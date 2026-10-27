#!/usr/bin/env python3
"""CLI script to generate marketing performance reports from ad data."""

import argparse
from datetime import datetime
import os
import sys
from pathlib import Path

# モジュールインポート用パス設定
current_file = Path(__file__).resolve()
module_dir = current_file.parent.parent
if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

from src.data_processor import DataProcessor
from src.insight_analyzer import generate_insights
from src.models import MarketingReport
from src.report_builder import ReportBuilder


def parse_args():
    parser = argparse.ArgumentParser(
        description="広告配信実績データ（CSV/JSON）からKPI集計とAIインサイト考察付きレポートを自動生成するツール"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=str(module_dir / "samples" / "sample_ad_performance.csv"),
        help="広告実績データ入力ファイル (CSVまたはJSON, デフォルト: samples/sample_ad_performance.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=str(module_dir / "outputs" / "weekly_report"),
        help="出力ファイルパス（拡張子なし指定時は format に応じた拡張子を付与）"
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["markdown", "html", "both"],
        default="both",
        help="レポート出力形式 (markdown / html / both, デフォルト: both)"
    )
    parser.add_argument(
        "--provider", "-p",
        type=str,
        choices=["auto", "gemini", "mock"],
        default="auto",
        help="LLMプロバイダー (auto / gemini / mock, デフォルト: auto)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Gemini モデル名 (未指定時は環境変数 GEMINI_MODEL または最新汎用エイリアス: gemini-flash-latest, gemini-flash-lite-latest)"
    )
    parser.add_argument(
        "--title", "-t",
        type=str,
        default="週次マーケティング広告成果分析レポート",
        help="レポートタイトル"
    )
    return parser.parse_args()


def resolve_input_path(input_path_str: str) -> Path:
    """カレントディレクトリおよびモジュールディレクトリからの相対パス解決"""
    p = Path(input_path_str)
    if p.exists():
        return p
    alt_p = module_dir / input_path_str
    if alt_p.exists():
        return alt_p
    raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path_str}")


def main():
    args = parse_args()

    print("=" * 65)
    print("📊 Marketing Ops Agent: レポート自動化パイプライン (テーマ2)")
    print("=" * 65)
    print(f"📄 入力データ  : {args.input}")
    print(f"📁 出力先ベース: {args.output}")
    print(f"🎨 出力フォーマット: {args.format}")
    print(f"🤖 LLMモード   : {args.provider} ({args.model or 'auto-resolve'})")

    # 1. データ集計 (pandas)
    try:
        input_file = resolve_input_path(args.input)
        print(f"\n[1/3] データを集計・クレンジング中...")
        processor = DataProcessor(input_file)
        aggregated_data = processor.process()
        tot = aggregated_data.total
        print(f"  ✅ 集計完了: 期間 {aggregated_data.period_start} 〜 {aggregated_data.period_end}")
        print(f"  • 総コスト: ¥{tot.cost:,.0f} | CV: {tot.conversions:,.0f} | CPA: ¥{tot.cpa or 0:,.0f} | ROAS: {tot.roas or 0:.1f}%")
        print(f"  • 対象媒体: {', '.join([c.channel for c in aggregated_data.by_channel])}")
    except Exception as e:
        print(f"❌ データの集計に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. AIインサイト・要因分析の生成
    try:
        print(f"\n[2/3] AIインサイト・要因分析を生成中...")
        insights = generate_insights(
            data=aggregated_data,
            provider=args.provider,
            model_name=args.model
        )
        print(f"  ✅ インサイト生成完了: 要因分析 {len(insights.channel_evaluations)}件, アクション {len(insights.action_items)}件")
    except Exception as e:
        print(f"❌ インサイト生成に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. レポート出力
    try:
        print(f"\n[3/3] レポートをレンダリング・出力中...")
        now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        marketing_report = MarketingReport(
            report_title=args.title,
            generated_at=now_str,
            data=aggregated_data,
            insights=insights
        )
        builder = ReportBuilder(marketing_report)

        base_out = Path(args.output)
        if not base_out.is_absolute():
            # 相対パスの解決
            pass

        # 拡張子処理
        out_str = str(args.output)
        if out_str.endswith(".md") or out_str.endswith(".html"):
            stem_out = out_str.rsplit(".", 1)[0]
        else:
            stem_out = out_str

        generated_files = []
        if args.format in ("markdown", "both"):
            md_path = f"{stem_out}.md"
            builder.build_markdown(md_path)
            generated_files.append(os.path.abspath(md_path))

        if args.format in ("html", "both"):
            html_path = f"{stem_out}.html"
            builder.build_html(html_path)
            generated_files.append(os.path.abspath(html_path))

        print(f"✨ レポート生成が完了しました！")
        for fpath in generated_files:
            print(f"  📁 出力ファイル: {fpath}")
        print("=" * 65)

    except Exception as e:
        print(f"❌ レポート出力に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
