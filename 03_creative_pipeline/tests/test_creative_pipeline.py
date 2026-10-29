"""Unit and integration tests for 03_creative_pipeline module."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image
import pytest
from pydantic import ValidationError

# 03_creative_pipeline を sys.path に追加
module_dir = Path(__file__).resolve().parent.parent
if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

# 他モジュールとの 'src' キャッシュ衝突をリセット
for mod in list(sys.modules.keys()):
    if mod == "src" or mod.startswith("src."):
        del sys.modules[mod]

from src import copy_generator
from src.catalog_builder import CatalogBuilder
from src.copy_generator import (
    generate_creative_variants,
    generate_mock_variants,
    generate_variants_with_gemini,
    resolve_model,
)
from src.image_generator import generate_creative_images, generate_pillow_banner
from src.models import (
    AspectRatio,
    BrandColors,
    CreativeBatchResult,
    CreativeBrief,
    CreativeVariant,
    GoogleSearchCopy,
    ImagePrompt,
    MetaCopy,
    XCopy,
)


@pytest.fixture
def sample_brief():
    """テスト用基本ブリーフフィクスチャ"""
    return CreativeBrief(
        product_name="TestSaaS",
        category="BtoB クラウド運用",
        target_audience="情シス部門長、エンジニア",
        key_features=["24時間自動復旧", "マルチクラウド対応"],
        pain_points=["夜間アラート対応の負担", "属人化"],
        value_propositions=["運用工数70%削減", "即日導入"],
        brand_colors=BrandColors(
            primary="#2563EB",
            secondary="#1E40AF",
            accent="#F59E0B",
            background="#F8FAFC"
        ),
        forbidden_words=["絶対", "100%保証"],
        tone_and_manner="プロフェッショナル"
    )


def test_models_validation():
    """データモデルのバリデーションテスト"""
    # 正常系
    colors = BrandColors(primary="#FF0000", secondary="#00FF00")
    assert colors.primary == "#FF0000"

    # 不正なHEX（文字数だけ合っていて非16進数の場合も含む）はデフォルトにフォールバック
    invalid_colors = BrandColors(primary="invalid-hex", secondary="#gggggg", accent="#12345z")
    assert invalid_colors.primary == "#2563EB"
    assert invalid_colors.secondary == "#2563EB"
    assert invalid_colors.accent == "#2563EB"

    # アスペクト比の解像度
    assert AspectRatio.SQUARE_1_1.dimensions == (1080, 1080)
    assert AspectRatio.LANDSCAPE_191_1.dimensions == (1200, 628)
    assert AspectRatio.STORY_9_16.dimensions == (1080, 1920)

    # Google文字数制限超過バリデーション
    with pytest.raises(ValidationError):
        GoogleSearchCopy(
            headline_1="あ" * 31,  # 30文字上限
            headline_2="見出し2",
            headline_3="見出し3",
            description_1="説明文1",
            description_2="説明文2"
        )

    # X文字数制限超過バリデーション
    with pytest.raises(ValidationError):
        XCopy(
            post_text="あ" * 141,  # 140文字上限
            card_headline="カード見出し",
            cta_type="詳細"
        )


def test_mock_copy_generation(sample_brief):
    """ルールベース動的モック生成の検証"""
    variants = generate_mock_variants(sample_brief, num_variants=3)
    assert len(variants) == 3

    v_a = variants[0]
    assert v_a.variant_id == "Variant-A"
    assert "TestSaaS" in v_a.google_search.headline_1
    assert len(v_a.google_search.headline_1) <= 30
    assert len(v_a.google_search.description_1) <= 90
    assert len(v_a.meta.primary_text) <= 200
    assert len(v_a.x_twitter.post_text) <= 140
    assert v_a.image_prompt.banner_catchphrase is not None

    # 禁止ワード（"絶対", "100%保証"）が含まれていないことの検証
    for v in variants:
        for forbidden in sample_brief.forbidden_words:
            assert forbidden not in v.google_search.headline_1
            assert forbidden not in v.image_prompt.banner_catchphrase


def test_pillow_banner_generation(sample_brief):
    """Pillow によるローカル画像バナー生成の検証"""
    variants = generate_mock_variants(sample_brief, num_variants=1)
    variant = variants[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1:1 正方形
        img_square = generate_pillow_banner(variant, sample_brief, AspectRatio.SQUARE_1_1, tmp_path / "square.png")
        assert os.path.exists(img_square.file_path)
        with Image.open(img_square.file_path) as im:
            assert im.size == (1080, 1080)

        # 1.91:1 横長
        img_landscape = generate_pillow_banner(variant, sample_brief, AspectRatio.LANDSCAPE_191_1, tmp_path / "landscape.png")
        assert os.path.exists(img_landscape.file_path)
        with Image.open(img_landscape.file_path) as im:
            assert im.size == (1200, 628)

        # 9:16 縦長
        img_story = generate_pillow_banner(variant, sample_brief, AspectRatio.STORY_9_16, tmp_path / "story.png")
        assert os.path.exists(img_story.file_path)
        with Image.open(img_story.file_path) as im:
            assert im.size == (1080, 1920)


def test_catalog_builder_outputs(sample_brief):
    """HTML カタログおよび CSV/JSON エクスポートの検証"""
    variants = generate_mock_variants(sample_brief, num_variants=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # 画像生成
        for v in variants:
            v.generated_images = generate_creative_images(
                variant=v,
                brief=sample_brief,
                output_dir=tmp_path,
                aspect_ratios=[AspectRatio.SQUARE_1_1]
            )

        batch_result = CreativeBatchResult(
            campaign_name="Test Campaign",
            brief=sample_brief,
            variants=variants,
            total_images=2
        )

        builder = CatalogBuilder(batch_result)

        # HTML
        html_file = tmp_path / "catalog.html"
        html_content = builder.build_html(html_file)
        assert os.path.exists(html_file)
        assert "<!DOCTYPE html>" in html_content
        assert "TestSaaS" in html_content
        assert "Variant-A" in html_content
        assert "Variant-B" in html_content
        assert "Google 検索広告" in html_content

        # CSV
        csv_file = tmp_path / "copies.csv"
        # 1つ目の見出しに数式文字（+30%）を設定してエクスポート検証
        variants[0].google_search.headline_1 = "+30%の工数削減"
        builder.export_csv(csv_file)
        assert os.path.exists(csv_file)
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            csv_content = f.read()
            assert "'+30%の工数削減" in csv_content  # 先頭にシングルクォートが付与されること
            csv_lines = csv_content.splitlines()
            assert len(csv_lines) >= 7  # ヘッダー + 2バリアント x 3チャネル

        # JSON
        json_file = tmp_path / "batch.json"
        builder.export_json(json_file)
        assert os.path.exists(json_file)
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["campaign_name"] == "Test Campaign"
            assert len(data["variants"]) == 2


def test_resolve_model_empty_env(monkeypatch):
    """環境変数が空文字の場合でもデフォルト値が採用されることを検証"""
    monkeypatch.setenv("GEMINI_MODEL", "")
    assert resolve_model(None) == "gemini-flash-latest"
    monkeypatch.setenv("GEMINI_MODEL", "custom-model")
    assert resolve_model(None) == "custom-model"
    assert resolve_model("override-model") == "override-model"


def test_gemini_client_with_mocked_api(monkeypatch, sample_brief):
    """Gemini API 呼び出しのモック検証"""
    class FakeVariantList:
        def __init__(self):
            variants = generate_mock_variants(sample_brief, num_variants=1)
            self.variants = variants

    class FakeResponse:
        text = json.dumps({
            "variants": [
                {
                    "variant_id": "Variant-A",
                    "approach_name": "API生成アプローチ",
                    "target_persona_focus": "ペルソナ",
                    "google_search": {
                        "headline_1": "見出し1",
                        "headline_2": "見出し2",
                        "headline_3": "見出し3",
                        "description_1": "説明1",
                        "description_2": "説明2"
                    },
                    "meta": {
                        "primary_text": "メインテキスト",
                        "headline": "見出し",
                        "description": "説明",
                        "cta_type": "詳しくはこちら"
                    },
                    "x_twitter": {
                        "post_text": "ポストテキスト",
                        "card_headline": "カード見出し",
                        "cta_type": "今すぐチェック"
                    },
                    "image_prompt": {
                        "prompt_en": "test prompt",
                        "prompt_ja": "テストプロンプト",
                        "style": "3d",
                        "negative_prompt": "blurry",
                        "banner_catchphrase": "AI生成キャッチ",
                        "banner_subphrase": "サブコピー"
                    },
                    "generated_images": [],
                    "hypothesis_reason": "仮説理由"
                }
            ]
        })

    class FakeClient:
        def __init__(self):
            self.models = self

        def generate_content(self, model, contents, config):
            return FakeResponse()

    class FakeGenAIModule:
        Client = lambda **kwargs: FakeClient()
        types = type("types", (), {
            "GenerateContentConfig": lambda **kwargs: kwargs
        })

    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.setitem(sys.modules, "google", type("google", (), {}))
    monkeypatch.setitem(sys.modules, "google.genai", FakeGenAIModule)
    monkeypatch.setitem(sys.modules, "google.genai.types", FakeGenAIModule.types)

    variants = generate_variants_with_gemini(sample_brief, num_variants=1)
    assert len(variants) == 1
    assert variants[0].approach_name == "API生成アプローチ"


def test_gemini_503_failover(monkeypatch, sample_brief):
    """503高負荷時の代替モデル自動フェイルオーバーを検証"""
    calls = []

    class FakeResponse:
        text = json.dumps({
            "variants": [
                {
                    "variant_id": "Variant-A",
                    "approach_name": "フェイルオーバー後成功",
                    "target_persona_focus": "ペルソナ",
                    "google_search": {
                        "headline_1": "見出し1",
                        "headline_2": "見出し2",
                        "headline_3": "見出し3",
                        "description_1": "説明1",
                        "description_2": "説明2"
                    },
                    "meta": {
                        "primary_text": "メインテキスト",
                        "headline": "見出し",
                        "description": "説明",
                        "cta_type": "詳しくはこちら"
                    },
                    "x_twitter": {
                        "post_text": "ポストテキスト",
                        "card_headline": "カード見出し",
                        "cta_type": "今すぐチェック"
                    },
                    "image_prompt": {
                        "prompt_en": "test",
                        "prompt_ja": "test",
                        "style": "3d",
                        "banner_catchphrase": "フェイルオーバーキャッチ",
                        "banner_subphrase": "サブ"
                    },
                    "generated_images": [],
                    "hypothesis_reason": "フェイルオーバー仮説"
                }
            ]
        })

    class FakeClient:
        def __init__(self):
            self.models = self

        def generate_content(self, model, contents, config):
            calls.append(model)
            if model == "gemini-flash-latest":
                raise Exception("503 UNAVAILABLE: Model is overloaded")
            return FakeResponse()

    class FakeGenAIModule:
        Client = lambda **kwargs: FakeClient()
        types = type("types", (), {
            "GenerateContentConfig": lambda **kwargs: kwargs
        })

    monkeypatch.setattr(copy_generator, "resolve_model", lambda m: "gemini-flash-latest")
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.setitem(sys.modules, "google", type("google", (), {}))
    monkeypatch.setitem(sys.modules, "google.genai", FakeGenAIModule)
    monkeypatch.setitem(sys.modules, "google.genai.types", FakeGenAIModule.types)

    variants = generate_variants_with_gemini(sample_brief, num_variants=1)
    assert len(variants) == 1
    assert variants[0].approach_name == "フェイルオーバー後成功"
    assert calls == ["gemini-flash-latest", "gemini-flash-lite-latest"]


def test_cli_execution_with_mock():
    """CLI (generate_creatives.py) の E2E サブプロセス実行テスト"""
    sample_json = module_dir / "samples" / "sample_creative_brief.json"

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "cli_output"
        cmd = [
            sys.executable,
            str(module_dir / "scripts" / "generate_creatives.py"),
            "--input", str(sample_json),
            "--output-dir", str(out_dir),
            "--variants", "2",
            "--aspect-ratios", "1:1",
            "--provider", "mock",
            "--format", "all"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"CLI stderr: {result.stderr}"

        # 成果物の存在確認
        assert (out_dir / "creative_catalog.html").exists()
        assert (out_dir / "creative_copies.csv").exists()
        assert (out_dir / "creative_batch.json").exists()
        # 画像ファイル
        assert (out_dir / "Variant-A_1_1.png").exists()
        assert (out_dir / "Variant-B_1_1.png").exists()
