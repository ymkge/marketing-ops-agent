"""Launcher pipeline: generates both proposal deck and creative assets in one workflow."""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import CampaignConfig

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_launcher_pipeline(
    config: CampaignConfig,
    output_dir: Path,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    variants_count: int = 3,
    aspect_ratios: Optional[List[str]] = None
) -> Dict[str, Any]:
    """新規案件立ち上げパイプライン: 提案スライドと初期クリエイティブ一式を一括生成"""
    output_dir.mkdir(parents=True, exist_ok=True)
    provider = provider or config.default_provider or "auto"
    model = model or config.default_model
    aspect_ratios = aspect_ratios or ["1:1", "1.91:1"]

    logger.info("=== [Launcher Pipeline] 新規案件立ち上げ一括生成開始 ===")
    logger.info("対象キャンペーン: %s (クライアント: %s)", config.campaign_name, config.client_name)
    logger.info("出力先ディレクトリ: %s", output_dir)

    results: Dict[str, Any] = {
        "campaign_name": config.campaign_name,
        "client_name": config.client_name,
        "provider": provider,
        "model": model,
        "outputs": {}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # ----------------------------------------------------
        # 1. 提案スライド (01_proposal_generator) の生成
        # ----------------------------------------------------
        logger.info("[1/2] 提案書スライド (01_proposal_generator) を生成中...")
        brief_data = config.to_brief_input_dict()
        brief_json_path = tmp_path / "proposal_brief.json"
        with open(brief_json_path, "w", encoding="utf-8") as f:
            json.dump(brief_data, f, ensure_ascii=False, indent=2)

        proposal_output_path = output_dir / f"{config.campaign_name}_proposal.pptx"
        proposal_cmd = [
            sys.executable,
            str(REPO_ROOT / "01_proposal_generator" / "scripts" / "generate_slides.py"),
            "--input", str(brief_json_path),
            "--output", str(proposal_output_path),
            "--provider", provider
        ]
        if model:
            proposal_cmd.extend(["--model", model])

        logger.info("実行コマンド: %s", " ".join(proposal_cmd))
        try:
            proc_prop = subprocess.run(proposal_cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired as e:
            logger.error("提案スライド生成がタイムアウトしました (300秒)")
            raise RuntimeError("Proposal generator timed out") from e

        if proc_prop.returncode != 0:
            logger.error("提案スライド生成に失敗しました: %s", proc_prop.stderr)
            raise RuntimeError(f"Proposal generator failed: {proc_prop.stderr}")
        
        logger.info("✅ 提案スライド生成完了: %s", proposal_output_path)
        results["outputs"]["proposal_pptx"] = str(proposal_output_path)

        # ----------------------------------------------------
        # 2. 初期クリエイティブ (03_creative_pipeline) の生成
        # ----------------------------------------------------
        logger.info("[2/2] 初期クリエイティブ群 (03_creative_pipeline) を生成中...")
        creative_data = config.to_creative_brief_dict()
        creative_json_path = tmp_path / "creative_brief.json"
        with open(creative_json_path, "w", encoding="utf-8") as f:
            json.dump(creative_data, f, ensure_ascii=False, indent=2)

        creative_output_dir = output_dir / "creatives"
        creative_cmd = [
            sys.executable,
            str(REPO_ROOT / "03_creative_pipeline" / "scripts" / "generate_creatives.py"),
            "--input", str(creative_json_path),
            "--output-dir", str(creative_output_dir),
            "--variants", str(variants_count),
            "--aspect-ratios", *aspect_ratios,
            "--provider", provider,
            "--format", "all"
        ]
        if model:
            creative_cmd.extend(["--model", model])

        logger.info("実行コマンド: %s", " ".join(creative_cmd))
        try:
            proc_creat = subprocess.run(creative_cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired as e:
            logger.error("クリエイティブ生成がタイムアウトしました (300秒)")
            raise RuntimeError("Creative pipeline timed out") from e

        if proc_creat.returncode != 0:
            logger.error("クリエイティブ生成に失敗しました: %s", proc_creat.stderr)
            raise RuntimeError(f"Creative pipeline failed: {proc_creat.stderr}")

        logger.info("✅ 初期クリエイティブ生成完了: %s", creative_output_dir)
        results["outputs"]["creatives_dir"] = str(creative_output_dir)
        results["outputs"]["creative_catalog_html"] = str(creative_output_dir / "creative_catalog.html")
        results["outputs"]["creative_copies_csv"] = str(creative_output_dir / "creative_copies.csv")

    # ----------------------------------------------------
    # 3. 立ち上げサマリー JSON の保存
    # ----------------------------------------------------
    summary_path = output_dir / "launch_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info("=== [Launcher Pipeline] 全工程が正常に完了しました ===")
    logger.info("サマリーファイル: %s", summary_path)
    return results
