#!/usr/bin/env python3
"""CLI script to generate creative copy, banner images, and AB testing catalog."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# モジュール検索パスにリポジトリルートおよびカレントモジュールを追加
current_dir = Path(__file__).resolve().parent
module_dir = current_dir.parent
if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

from src.catalog_builder import CatalogBuilder
from src.copy_generator import generate_creative_variants
from src.image_generator import generate_creative_images
from src.models import (
    AspectRatio,
    CreativeBatchResult,
    CreativeBrief,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("generate_creatives")


def parse_args():
    parser = argparse.ArgumentParser(
        description="広告クリエイティブ自動生成パイプライン: コピー量産、バナー画像合成、ABテストカタログ作成"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=str(module_dir / "samples" / "sample_creative_brief.json"),
        help="企画ブリーフJSONファイルパス (デフォルト: samples/sample_creative_brief.json)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=str(module_dir / "outputs" / "campaign_latest"),
        help="成果物出力ディレクトリ (デフォルト: outputs/campaign_latest)"
    )
    parser.add_argument(
        "--variants", "-n",
        type=int,
        default=3,
        help="生成するABテストバリエーション数 (デフォルト: 3)"
    )
    parser.add_argument(
        "--aspect-ratios", "-a",
        nargs="+",
        choices=["1:1", "1.91:1", "9:16"],
        default=["1:1", "1.91:1"],
        help="生成するバナー画像のアスペクト比 (デフォルト: 1:1 1.91:1)"
    )
    parser.add_argument(
        "--provider", "-p",
        type=str,
        choices=["auto", "gemini", "mock"],
        default="auto",
        help="コピー生成プロバイダー (auto / gemini / mock, デフォルト: auto)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Gemini モデル名 (未指定時は環境変数 GEMINI_MODEL または最新汎用エイリアス: gemini-flash-latest)"
    )
    parser.add_argument(
        "--use-imagen",
        action="store_true",
        default=False,
        help="Google Imagen 3 APIによる画像生成を試行 (デフォルト: False, Pillowによるローカルバナー合成)"
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["all", "html", "csv", "json"],
        default="all",
        help="出力フォーマット (all / html / csv / json, デフォルト: all)"
    )
    return parser.parse_args()


def load_brief(input_path: str) -> CreativeBrief:
    """入力JSONファイルからCreativeBriefをロード"""
    path = Path(input_path)
    if not path.exists():
        alt_path = module_dir / input_path
        if alt_path.exists():
            path = alt_path
        else:
            raise FileNotFoundError(f"入力ブリーフファイルが見つかりません: {input_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return CreativeBrief.model_validate(data)


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== クリエイティブ生成パイプライン開始 ===")
    logger.info("入力ファイル: %s", args.input)
    logger.info("出力先: %s", output_dir)
    logger.info("プロバイダー: %s (モデル: %s)", args.provider, args.model or "default")

    # 1. ブリーフ読み込み
    try:
        brief = load_brief(args.input)
        logger.info("商材ブリーフ読み込み完了: %s (%s)", brief.product_name, brief.category)
    except Exception as e:
        logger.error("ブリーフの読み込みに失敗しました: %s", e)
        sys.exit(1)

    # 2. コピー＆プロンプト生成
    logger.info("広告コピー＆プロンプトを生成中 (%d パターン)...", args.variants)
    variants = generate_creative_variants(
        brief=brief,
        num_variants=args.variants,
        provider=args.provider,
        model_name=args.model
    )
    logger.info("コピー生成完了: %d 件のバリエーション", len(variants))

    # 3. アスペクト比のパース
    selected_ratios = [AspectRatio(ar_str) for ar_str in args.aspect_ratios]

    # 4. バナー画像生成
    total_images = 0
    logger.info("バナー画像を生成中 (対象比率: %s)...", [r.value for r in selected_ratios])
    for v in variants:
        generated = generate_creative_images(
            variant=v,
            brief=brief,
            output_dir=output_dir,
            aspect_ratios=selected_ratios,
            use_api=args.use_imagen
        )
        v.generated_images = generated
        total_images += len(generated)

    # 5. バッチ結果の集計
    batch_result = CreativeBatchResult(
        campaign_name=brief.product_name,
        brief=brief,
        variants=variants,
        total_images=total_images
    )

    # 6. カタログ & エクスポート出力
    builder = CatalogBuilder(batch_result)
    
    if args.format in ("all", "html"):
        html_path = output_dir / "creative_catalog.html"
        builder.build_html(html_path)
        logger.info("HTML カタログ生成: %s", html_path)

    if args.format in ("all", "csv"):
        csv_path = output_dir / "creative_copies.csv"
        builder.export_csv(csv_path)
        logger.info("CSV コピー一覧生成: %s", csv_path)

    if args.format in ("all", "json"):
        json_path = output_dir / "creative_batch.json"
        builder.export_json(json_path)
        logger.info("JSON メタデータ生成: %s", json_path)

    logger.info("=== クリエイティブ生成パイプライン完了 ===")
    logger.info("生成成果物: %s", output_dir)


if __name__ == "__main__":
    main()
