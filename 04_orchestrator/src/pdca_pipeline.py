"""PDCA pipeline: generates performance report and automatically produces remedial creatives."""

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import CampaignConfig

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_pdca_pipeline(
    performance_csv: Path,
    config: Optional[CampaignConfig] = None,
    output_dir: Optional[Path] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    remedial_variants_count: int = 2
) -> Dict[str, Any]:
    """PDCA運用改善パイプライン: 実績レポーティングから改善クリエイティブ再生成までを自動連動"""
    if not performance_csv.exists():
        raise FileNotFoundError(f"広告実績CSVが見つかりません: {performance_csv}")

    output_dir = output_dir or (REPO_ROOT / "04_orchestrator" / "outputs" / "pdca_latest")
    output_dir.mkdir(parents=True, exist_ok=True)

    provider = provider or (config.default_provider if config else "auto")
    model = model or (config.default_model if config else None)

    logger.info("=== [PDCA Pipeline] 運用レポーティング & 改善クリエイティブ生成開始 ===")
    logger.info("実績データCSV: %s", performance_csv)
    logger.info("出力先ディレクトリ: %s", output_dir)

    results: Dict[str, Any] = {
        "performance_csv": str(performance_csv),
        "provider": provider,
        "model": model,
        "outputs": {}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # ----------------------------------------------------
        # 1. 広告レポート (02_report_automation) の生成
        # ----------------------------------------------------
        logger.info("[1/2] 広告配信実績レポート (02_report_automation) を集計・分析中...")
        report_base = output_dir / "performance_report"
        report_cmd = [
            sys.executable,
            str(REPO_ROOT / "02_report_automation" / "scripts" / "generate_report.py"),
            "--input", str(performance_csv),
            "--output", str(report_base),
            "--format", "both",
            "--provider", provider
        ]
        if model:
            report_cmd.extend(["--model", model])

        logger.info("実行コマンド: %s", " ".join(report_cmd))
        try:
            proc_rep = subprocess.run(report_cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired as e:
            logger.error("レポート集計がタイムアウトしました (300秒)")
            raise RuntimeError("Report automation timed out") from e

        if proc_rep.returncode != 0:
            logger.error("レポート生成に失敗しました: %s", proc_rep.stderr)
            raise RuntimeError(f"Report automation failed: {proc_rep.stderr}")

        report_md_path = output_dir / "performance_report.md"
        report_html_path = output_dir / "performance_report.html"
        logger.info("✅ レポート生成完了: %s, %s", report_md_path, report_html_path)
        results["outputs"]["report_md"] = str(report_md_path)
        results["outputs"]["report_html"] = str(report_html_path)

        # ----------------------------------------------------
        # 2. レポート考察から改善課題を抽出し、テコ入れブリーフを構築
        # ----------------------------------------------------
        logger.info("レポートから課題と推奨アクションを抽出中...")
        report_text = ""
        if report_md_path.exists():
            with open(report_md_path, "r", encoding="utf-8") as f:
                report_text = f.read()

        # 課題抽出 (アクションアイテムの抽出)
        extracted_actions: List[str] = []
        for line in report_text.splitlines():
            if line.strip().startswith("- **[") or line.strip().startswith("- **"):
                clean_line = re.sub(r"[\*\#\-]", "", line).strip()
                if clean_line:
                    extracted_actions.append(clean_line[:80])

        if not extracted_actions:
            extracted_actions = [
                "CTR低下およびCPA高騰キャンペーンへの新規クリエイティブ投入",
                "高効率チャネルへの予算シフトと訴求ABテスト"
            ]

        logger.info("抽出された改善施策: %s", extracted_actions)
        results["extracted_actions"] = extracted_actions

        # ----------------------------------------------------
        # 3. 改善用クリエイティブ (03_creative_pipeline) の再生成
        # ----------------------------------------------------
        logger.info("[2/2] 課題テコ入れ用の改善クリエイティブ (03_creative_pipeline) を生成中...")
        
        p_name = config.target_service if config else "運用中サービス"
        p_category = config.category if config else "Webプロモーション"
        p_target = config.target_audience if config else "既存検討層および潜在見込み顧客"
        
        remedial_brief = {
            "product_name": p_name,
            "category": p_category,
            "target_audience": f"{p_target} (CTR低下・離脱防止フォーカス)",
            "key_features": config.product_features if config else ["成果改善に向けた新機能", "迅速なサポート"],
            "pain_points": extracted_actions,
            "value_propositions": [
                "改善施策直結の具体ベネフィット訴求",
                "導入障壁を払拭する安心・即効性メッセージ"
            ],
            "brand_colors": {
                "primary": config.brand_colors.primary if config else "#2563EB",
                "secondary": config.brand_colors.secondary if config else "#1E40AF",
                "accent": config.brand_colors.accent if config else "#F59E0B",
                "background": config.brand_colors.background if config else "#F8FAFC"
            },
            "forbidden_words": config.forbidden_words if config else ["絶対", "100%"],
            "tone_and_manner": config.tone_and_manner if config else "明快、信頼感、アクション喚起"
        }

        remedial_json_path = tmp_path / "remedial_brief.json"
        with open(remedial_json_path, "w", encoding="utf-8") as f:
            json.dump(remedial_brief, f, ensure_ascii=False, indent=2)

        remedial_output_dir = output_dir / "remedial_creatives"
        creative_cmd = [
            sys.executable,
            str(REPO_ROOT / "03_creative_pipeline" / "scripts" / "generate_creatives.py"),
            "--input", str(remedial_json_path),
            "--output-dir", str(remedial_output_dir),
            "--variants", str(remedial_variants_count),
            "--aspect-ratios", "1:1", "1.91:1",
            "--provider", provider,
            "--format", "all"
        ]
        if model:
            creative_cmd.extend(["--model", model])

        logger.info("実行コマンド: %s", " ".join(creative_cmd))
        try:
            proc_creat = subprocess.run(creative_cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired as e:
            logger.error("改善クリエイティブ生成がタイムアウトしました (300秒)")
            raise RuntimeError("Remedial creative pipeline timed out") from e

        if proc_creat.returncode != 0:
            logger.error("改善クリエイティブ生成に失敗しました: %s", proc_creat.stderr)
            raise RuntimeError(f"Remedial creative pipeline failed: {proc_creat.stderr}")

        logger.info("✅ 改善クリエイティブ生成完了: %s", remedial_output_dir)
        results["outputs"]["remedial_creatives_dir"] = str(remedial_output_dir)
        results["outputs"]["remedial_catalog_html"] = str(remedial_output_dir / "creative_catalog.html")
        results["outputs"]["remedial_copies_csv"] = str(remedial_output_dir / "creative_copies.csv")

    # ----------------------------------------------------
    # 4. PDCA サマリー JSON の保存
    # ----------------------------------------------------
    summary_path = output_dir / "pdca_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info("=== [PDCA Pipeline] 全工程が正常に完了しました ===")
    logger.info("サマリーファイル: %s", summary_path)
    return results
