"""Unified CLI argument parser and dispatcher for 04_orchestrator."""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from .config import load_campaign_config
from .launcher_pipeline import run_launcher_pipeline
from .pdca_pipeline import run_pdca_pipeline

logger = logging.getLogger("marketing_ops")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops",
        description="Marketing Ops Agent 統合CLIツール: 提案書・レポート・クリエイティブ・全体連携パイプラインを一元管理"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="実行するサブコマンド")

    # 1. pipeline (全体連携)
    parser_pipe = subparsers.add_parser("pipeline", help="マーケティング一括連携パイプラインを実行")
    parser_pipe.add_argument(
        "--mode", "-m",
        choices=["launch", "pdca"],
        required=True,
        help="実行モード: 'launch' (提案+初期クリエイティブ一括生成) または 'pdca' (レポート分析+改善クリエイティブ再生成)"
    )
    parser_pipe.add_argument(
        "--config", "-c",
        type=str,
        default=str(REPO_ROOT / "04_orchestrator" / "samples" / "sample_campaign_config.yaml"),
        help="案件設定ファイルパス (YAMLまたはJSON)"
    )
    parser_pipe.add_argument(
        "--data", "-d",
        type=str,
        default=str(REPO_ROOT / "02_report_automation" / "samples" / "sample_ad_performance.csv"),
        help="広告配信実績CSVファイルパス (pdcaモード時)"
    )
    parser_pipe.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="成果物出力ディレクトリ"
    )
    parser_pipe.add_argument(
        "--provider", "-p",
        choices=["auto", "gemini", "mock"],
        default=None,
        help="LLMプロバイダー (auto / gemini / mock)"
    )
    parser_pipe.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLMモデル名 (未指定時は最新エイリアス)"
    )

    # 2. proposal (単体スライド生成ラッパー)
    parser_prop = subparsers.add_parser("proposal", help="01_proposal_generator を単体実行")
    parser_prop.add_argument("--input", "-i", type=str, default=str(REPO_ROOT / "01_proposal_generator" / "samples" / "sample_brief.json"))
    parser_prop.add_argument("--output", "-o", type=str, default=str(REPO_ROOT / "01_proposal_generator" / "outputs" / "sample_proposal.pptx"))
    parser_prop.add_argument("--provider", "-p", default="auto")
    parser_prop.add_argument("--model", "-m", default=None)

    # 3. report (単体レポート生成ラッパー)
    parser_rep = subparsers.add_parser("report", help="02_report_automation を単体実行")
    parser_rep.add_argument("--input", "-i", type=str, default=str(REPO_ROOT / "02_report_automation" / "samples" / "sample_ad_performance.csv"))
    parser_rep.add_argument("--output", "-o", type=str, default=str(REPO_ROOT / "02_report_automation" / "outputs" / "weekly_report"))
    parser_rep.add_argument("--format", "-f", default="both", choices=["markdown", "html", "both"])
    parser_rep.add_argument("--provider", "-p", default="auto")
    parser_rep.add_argument("--model", "-m", default=None)

    # 4. creative (単体クリエイティブ生成ラッパー)
    parser_crt = subparsers.add_parser("creative", help="03_creative_pipeline を単体実行")
    parser_crt.add_argument("--input", "-i", type=str, default=str(REPO_ROOT / "03_creative_pipeline" / "samples" / "sample_creative_brief.json"))
    parser_crt.add_argument("--output-dir", "-o", type=str, default=str(REPO_ROOT / "03_creative_pipeline" / "outputs" / "campaign_latest"))
    parser_crt.add_argument("--variants", "-n", type=int, default=3)
    parser_crt.add_argument("--aspect-ratios", "-a", nargs="+", default=["1:1", "1.91:1"])
    parser_crt.add_argument("--provider", "-p", default="auto")
    parser_crt.add_argument("--model", "-m", default=None)

    return parser


def main(args_list=None):
    parser = build_parser()
    args = parser.parse_args(args_list)

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    if args.subcommand == "pipeline":
        try:
            config_path = Path(args.config)
            config = load_campaign_config(config_path) if config_path.exists() else None

            if args.mode == "launch":
                if not config:
                    logger.error("launchモードには有効な設定ファイル (--config) が必要です: %s", args.config)
                    sys.exit(1)
                out_dir = Path(args.output_dir) if args.output_dir else (REPO_ROOT / "04_orchestrator" / "outputs" / f"launch_{config.campaign_name.replace(' ', '_')}")
                run_launcher_pipeline(
                    config=config,
                    output_dir=out_dir,
                    provider=args.provider,
                    model=args.model
                )
            elif args.mode == "pdca":
                data_path = Path(args.data)
                out_dir = Path(args.output_dir) if args.output_dir else (REPO_ROOT / "04_orchestrator" / "outputs" / "pdca_latest")
                run_pdca_pipeline(
                    performance_csv=data_path,
                    config=config,
                    output_dir=out_dir,
                    provider=args.provider,
                    model=args.model
                )
        except Exception as e:
            logger.error("パイプライン実行中にエラーが発生しました: %s", e)
            sys.exit(1)

    elif args.subcommand == "proposal":
        cmd = [
            sys.executable,
            str(REPO_ROOT / "01_proposal_generator" / "scripts" / "generate_slides.py"),
            "--input", args.input,
            "--output", args.output,
            "--provider", args.provider
        ]
        if args.model:
            cmd.extend(["--model", args.model])
        res = subprocess.run(cmd)
        sys.exit(res.returncode)

    elif args.subcommand == "report":
        cmd = [
            sys.executable,
            str(REPO_ROOT / "02_report_automation" / "scripts" / "generate_report.py"),
            "--input", args.input,
            "--output", args.output,
            "--format", args.format,
            "--provider", args.provider
        ]
        if args.model:
            cmd.extend(["--model", args.model])
        res = subprocess.run(cmd)
        sys.exit(res.returncode)

    elif args.subcommand == "creative":
        cmd = [
            sys.executable,
            str(REPO_ROOT / "03_creative_pipeline" / "scripts" / "generate_creatives.py"),
            "--input", args.input,
            "--output-dir", args.output_dir,
            "--variants", str(args.variants),
            "--aspect-ratios", *args.aspect_ratios,
            "--provider", args.provider
        ]
        if args.model:
            cmd.extend(["--model", args.model])
        res = subprocess.run(cmd)
        sys.exit(res.returncode)
