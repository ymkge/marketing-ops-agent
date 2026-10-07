#!/usr/bin/env python3
"""CLI script to generate proposal PowerPoint slides from brief input."""

import argparse
import json
import os
import sys
from pathlib import Path

# モジュールインポート用のパス設定（01_proposal_generator ディレクトリまたはリポジトリルートからの実行に対応）
current_file = Path(__file__).resolve()
module_dir = current_file.parent.parent
if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

from src.models import BriefInput
from src.llm_client import generate_proposal_deck
from src.pptx_builder import ProposalPptxBuilder


def parse_args():
    parser = argparse.ArgumentParser(
        description="企画メモやブリーフ情報から提案スライド(.pptx)を自動生成するツール"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=str(module_dir / "samples" / "sample_brief.json"),
        help="企画メモ入力ファイル（JSONまたはMarkdown形式、デフォルト: samples/sample_brief.json）"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=str(module_dir / "outputs" / "sample_proposal.pptx"),
        help="生成するPPTXファイルの出力先パス（デフォルト: outputs/sample_proposal.pptx）"
    )
    parser.add_argument(
        "--provider", "-p",
        type=str,
        choices=["auto", "gemini", "anthropic", "openai", "mock"],
        default="auto",
        help="LLMプロバイダー指定 (auto / gemini / anthropic / openai / mock, デフォルト: auto)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="使用するモデル名（例: gemini-2.0-flash, claude-3-5-sonnet-20241022, gpt-4o など）"
    )
    return parser.parse_args()


def load_brief_data(input_path: str) -> BriefInput:
    """入力ファイルからBriefInputオブジェクトを生成"""
    path = Path(input_path)
    if not path.exists():
        # カレントディレクトリからの相対パスで存在しない場合、module_dirからの相対パスを試行
        alt_path = module_dir / input_path
        if alt_path.exists():
            path = alt_path
        else:
            raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if path.suffix.lower() == ".json":
        data = json.loads(content)
        return BriefInput.model_validate(data)
    else:
        # Markdownやテキストファイルの場合のシンプルなパース
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return BriefInput(
            client_name="提案先クライアント",
            project_name=lines[0].replace("#", "").strip() if lines else "新規マーケティング施策提案",
            strategy=lines[1:10] if len(lines) > 1 else ["課題解決型プロモーションの推進"]
        )


def main():
    args = parse_args()

    print("=" * 60)
    print("🚀 Marketing Ops Agent: 提案スライド自動生成パイプライン")
    print("=" * 60)
    print(f"📄 入力ブリーフ: {args.input}")
    print(f"📊 出力先パス  : {args.output}")
    print(f"🤖 LLMモード   : {args.provider}")

    # 1. ブリーフ入力データの読み込み
    try:
        brief = load_brief_data(args.input)
        print(f"✅ ブリーフ読み込み完了: {brief.client_name} / {brief.project_name}")
    except Exception as e:
        print(f"❌ 入力ブリーフの読み込みに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. 構成案の生成 (LLM または モック)
    print("\n🧠 スライド構成・ストーリーラインを構築中...")
    try:
        deck = generate_proposal_deck(brief, provider=args.provider, model_name=args.model)
        print(f"✅ スライド骨子作成完了: 全 {len(deck.slides)} スライド")
        for i, s in enumerate(deck.slides, 1):
            print(f"   [{i}] {s.slide_type:15s} : {s.title}")
    except Exception as e:
        print(f"❌ スライド構成案の生成に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. PowerPoint スライド生成
    print(f"\n🎨 PowerPoint スライド（.pptx）をビルド中...")
    try:
        output_path = Path(args.output)
        if not output_path.is_absolute() and not str(args.output).startswith("outputs/"):
            # 相対パスの場合はモジュールディレクトリ基準を考慮
            pass
        builder = ProposalPptxBuilder(deck)
        saved_path = builder.build(str(output_path))
        print(f"✨ 提案スライド生成が完了しました！")
        print(f"📁 出力ファイル: {os.path.abspath(saved_path)}")
        print("=" * 60)
    except Exception as e:
        print(f"❌ PowerPointファイルの生成に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
