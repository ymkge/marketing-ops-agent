"""Copy and image prompt generator using Gemini Structured Outputs and dynamic mock fallbacks."""

import json
import logging
import os
import re
from typing import List, Optional
from pydantic import BaseModel

from .models import (
    CreativeBrief,
    CreativeVariant,
    GoogleSearchCopy,
    ImagePrompt,
    MetaCopy,
    XCopy,
)

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
ALT_GEMINI_MODEL = "gemini-flash-lite-latest"

SYSTEM_PROMPT = """あなたは大手広告代理店のトップコピーライター兼クリエイティブディレクターです。
提供された商材情報・ターゲット・ペイン・提供価値（CreativeBrief）を綿密に分析し、
ABテスト用の異なる訴求アプローチ（例: 「業務効率化・コスト削減」「不安・リスク解消」「手軽さ・即効性」など）を持つ
広告クリエイティブバリエーションを生成してください。

各バリエーションについて以下の要件を厳密に満たしてください:
1. Google検索広告:
   - headline_1, headline_2, headline_3: それぞれ全角30文字以内。クリック率を高める具体的な数字やキーワードを含める。
   - description_1, description_2: それぞれ全角90文字以内。具体的なベネフィットとCTAを含める。
2. Meta広告:
   - primary_text: 200文字以内（推奨125文字前後）。ペルソナへの問いかけと導入のメリット。
   - headline: 40文字以内。
   - description: 50文字以内。
   - cta_type: ボタン表記（例: 「詳しくはこちら」「資料をダウンロード」など）。
3. X (旧Twitter) 広告:
   - post_text: 140文字以内。タイムラインで目を引くフックと共感。
   - card_headline: 40文字以内。
   - cta_type: 簡潔な誘導アクション。
4. 画像生成プロンプト (ImagePrompt):
   - prompt_en: 画像生成モデル（Imagen 3/Midjourney）向けの高品質な英語プロンプト。背景、被写体、ライティング、カラースキームを指定。
   - prompt_ja: 日本語での意図説明。
   - banner_catchphrase: バナー画像中央に大きく載せるキャッチコピー（全角20文字以内）。
   - banner_subphrase: 補助サブコピー（全角35文字以内）。
5. 禁止ワード (forbidden_words) は一切使用しないでください。
"""


def resolve_model(model_name: Optional[str] = None) -> str:
    """指定引数、環境変数、汎用デフォルトエイリアスの順でモデル名を解決"""
    if model_name:
        return model_name
    return os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL


def _sanitize_copy(text: str, forbidden_words: List[str]) -> str:
    """禁止ワードが含まれている場合はマスク・除外"""
    sanitized = text
    for word in forbidden_words:
        if word and word in sanitized:
            sanitized = sanitized.replace(word, "")
    return sanitized


def _sanitize_variant(v: CreativeVariant, forbidden_words: List[str]) -> CreativeVariant:
    """バリアント内の全テキストフィールドから禁止ワードをサニタイズ"""
    if not forbidden_words:
        return v
    # Google
    v.google_search.headline_1 = _sanitize_copy(v.google_search.headline_1, forbidden_words)
    v.google_search.headline_2 = _sanitize_copy(v.google_search.headline_2, forbidden_words)
    v.google_search.headline_3 = _sanitize_copy(v.google_search.headline_3, forbidden_words)
    v.google_search.description_1 = _sanitize_copy(v.google_search.description_1, forbidden_words)
    v.google_search.description_2 = _sanitize_copy(v.google_search.description_2, forbidden_words)
    # Meta
    v.meta.primary_text = _sanitize_copy(v.meta.primary_text, forbidden_words)
    v.meta.headline = _sanitize_copy(v.meta.headline, forbidden_words)
    v.meta.description = _sanitize_copy(v.meta.description, forbidden_words)
    # X
    v.x_twitter.post_text = _sanitize_copy(v.x_twitter.post_text, forbidden_words)
    v.x_twitter.card_headline = _sanitize_copy(v.x_twitter.card_headline, forbidden_words)
    # Image prompt
    v.image_prompt.banner_catchphrase = _sanitize_copy(v.image_prompt.banner_catchphrase, forbidden_words)
    if v.image_prompt.banner_subphrase:
        v.image_prompt.banner_subphrase = _sanitize_copy(v.image_prompt.banner_subphrase, forbidden_words)
    return v


def generate_mock_variants(brief: CreativeBrief, num_variants: int = 3) -> List[CreativeVariant]:
    """APIキー未設定時またはローカル実行用の高品質ルールベースモック生成"""
    p_name = brief.product_name
    features = brief.key_features if brief.key_features else ["高い業務効率化", "安心のサポート体制"]
    pains = brief.pain_points if brief.pain_points else ["業務の属人化とコスト負担"]
    values = brief.value_propositions if brief.value_propositions else ["業務工数を大幅削減"]

    approaches = [
        {
            "id": "Variant-A",
            "approach": "時短・工数削減訴求",
            "focus": "日々の運用負担に悩む実務責任者・リーダー",
            "headline_prefix": "作業時間を最大70%削減",
            "hook": f"まだ手作業で消耗していませんか？{p_name}なら自動化を実現。",
            "catchphrase": "もう夜間アラートで起きない。",
            "subphrase": "自律型AIがインフラ運用を即日自動化",
            "prompt_en": "A modern clean minimal 3D illustration of an engineer smiling peacefully at night while an autonomous AI system manages cloud servers smoothly, soft futuristic blue lighting, high quality render",
            "prompt_ja": "夜間アラートから解放されたエンジニアと静かに稼働する自律型AIクラウド基盤",
            "hypothesis": "日々の負担軽減と工数削減数値を前面に出すことで、現場リーダーの共感とクリックを最大化する。"
        },
        {
            "id": "Variant-B",
            "approach": "安心・リスク回避訴求",
            "focus": "障害リスクやセキュリティを最重要視する経営層・情シス部門長",
            "headline_prefix": "障害復旧までの時間をゼロへ",
            "hook": f"予期せぬインフラ障害から事業を守る。{p_name}が一次切り分けを自律代行。",
            "catchphrase": "クラウド障害、最短1分で初動完了。",
            "subphrase": "マルチクラウドの運用属人化を完全解消",
            "prompt_en": "An isometric 3D visualization of a secure glowing shield protecting multi-cloud architecture logos AWS GCP Azure, enterprise grade, professional deep navy blue and gold accents, crisp 8k",
            "prompt_ja": "マルチクラウドを守る堅牢なAIシールドと安定したインフラ基盤の信頼感",
            "hypothesis": "リスク低減と事業継続性を訴求し、決裁権を持つマネジメント層の資料請求CVRを高める。"
        },
        {
            "id": "Variant-C",
            "approach": "手軽さ・即日導入訴求",
            "focus": "リソース不足で大掛かりな導入ができない中小・中堅スタートアップ",
            "headline_prefix": "最短即日連携・月額10万円〜",
            "hook": f"エージェントレスで即日稼働開始。{p_name}で今日からスモールスタート。",
            "catchphrase": "初期費用0円、即日スタート。",
            "subphrase": "既存システムに手を加えずノーコード連携",
            "prompt_en": "A sleek modern laptop dashboard showing a one-click integration progress bar reaching 100 percent in seconds, bright vibrant colors, tech startup aesthetic, octane render",
            "prompt_ja": "ワンクリックで即座に連携が完了するダッシュボード画面とスピード感",
            "hypothesis": "導入ハードルの低さと初期費用の手軽さを提示し、検討初期段階のリード獲得単価（CPA）を引き下げる。"
        }
    ]

    variants: List[CreativeVariant] = []
    for i in range(min(num_variants, len(approaches))):
        app = approaches[i]

        google_copy = GoogleSearchCopy(
            headline_1=_sanitize_copy(f"【公式】{p_name} - {app['headline_prefix']}"[:30], brief.forbidden_words),
            headline_2=_sanitize_copy(f"{app['approach']}で課題解決"[:30], brief.forbidden_words),
            headline_3=_sanitize_copy(f"{p_name}導入事例公開中"[:30], brief.forbidden_words),
            description_1=_sanitize_copy(f"{app['hook']} {features[0]}"[:90], brief.forbidden_words),
            description_2=_sanitize_copy(f"{values[0]}。まずは無料デモ・資料請求で効果をご体感ください。"[:90], brief.forbidden_words)
        )

        meta_copy = MetaCopy(
            primary_text=_sanitize_copy(f"【{app['approach']}】\n{app['hook']}\n\n■ 主なポイント:\n・{features[0]}\n・{values[0]}\n今すぐ詳細資料をご覧ください。"[:200], brief.forbidden_words),
            headline=_sanitize_copy(f"{p_name} | {app['headline_prefix']}"[:40], brief.forbidden_words),
            description=_sanitize_copy(f"{brief.target_audience}向け導入ガイド無料進呈中"[:50], brief.forbidden_words),
            cta_type="詳しくはこちら"
        )

        x_copy = XCopy(
            post_text=_sanitize_copy(f"＼{brief.target_audience}必見／\n{app['hook']}\n\n{features[0]}で業務を変革しませんか？\n詳細はこちら👇"[:140], brief.forbidden_words),
            card_headline=_sanitize_copy(f"{p_name} - {app['headline_prefix']}"[:40], brief.forbidden_words),
            cta_type="今すぐチェック"
        )

        img_prompt = ImagePrompt(
            prompt_en=app["prompt_en"],
            prompt_ja=app["prompt_ja"],
            style="modern minimal 3D tech illustration",
            negative_prompt="blurry, distorted, low quality, messy text, cluttered",
            banner_catchphrase=_sanitize_copy(app["catchphrase"][:30], brief.forbidden_words),
            banner_subphrase=_sanitize_copy(app["subphrase"][:50], brief.forbidden_words)
        )

        variant = CreativeVariant(
            variant_id=app["id"],
            approach_name=app["approach"],
            target_persona_focus=app["focus"],
            google_search=google_copy,
            meta=meta_copy,
            x_twitter=x_copy,
            image_prompt=img_prompt,
            generated_images=[],
            hypothesis_reason=app["hypothesis"]
        )
        variants.append(variant)

    return variants


def generate_variants_with_gemini(
    brief: CreativeBrief,
    num_variants: int = 3,
    model_name: Optional[str] = None
) -> List[CreativeVariant]:
    """Gemini API (google-genai SDK) による構造化コピー＆プロンプト生成"""
    resolved_model = resolve_model(model_name)
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai パッケージがインストールされていません。pip install google-genai を実行してください。")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("環境変数 GEMINI_API_KEY または GOOGLE_API_KEY が設定されていません。")

    client = genai.Client(api_key=api_key)

    # Structured Outputs 用のラッパーモデル
    class GeminiVariantList(BaseModel):
        variants: List[CreativeVariant]

    prompt = f"""以下の企画ブリーフ情報をもとに、ABテスト用の広告クリエイティブバリエーションをちょうど {num_variants} パターン生成してください。

ブリーフ内容:
{brief.model_dump_json(indent=2)}

各バリエーションの variant_id は 'Variant-A', 'Variant-B', 'Variant-C'... としてください。
各チャネルの文字数制限（Google headline: 30字以内, desc: 90字以内 / Meta headline: 40字以内 / X post: 140字以内）を厳密に守ってください。
禁止ワードリスト: {brief.forbidden_words}
"""

    models_to_try = [resolved_model]
    alt_model = ALT_GEMINI_MODEL if resolved_model != ALT_GEMINI_MODEL else DEFAULT_GEMINI_MODEL
    if alt_model not in models_to_try:
        models_to_try.append(alt_model)

    last_error = None
    for target_model in models_to_try:
        try:
            logger.info("Gemini API (%s) でクリエイティブバリエーションを生成中...", target_model)
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=GeminiVariantList,
                    temperature=0.7,
                )
            )
            response_text = response.text.strip()
            parsed_data = json.loads(response_text)
            batch = GeminiVariantList.model_validate(parsed_data)
            
            # 禁止ワードの事後サニタイズ（全コピーフィールド）
            for i in range(len(batch.variants)):
                batch.variants[i] = _sanitize_variant(batch.variants[i], brief.forbidden_words)

            return batch.variants
        except Exception as e:
            last_error = e
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                logger.warning("モデル %s が高負荷(503)のため、代替モデル %s へフェイルオーバーします: %s", target_model, alt_model, e)
                continue
            raise e

    if last_error:
        raise last_error

    return generate_mock_variants(brief, num_variants)


def generate_creative_variants(
    brief: CreativeBrief,
    num_variants: int = 3,
    provider: str = "auto",
    model_name: Optional[str] = None
) -> List[CreativeVariant]:
    """プロバイダー判定に基づいてクリエイティブバリエーションを生成"""
    provider_key = provider.lower()
    if provider_key == "mock":
        return generate_mock_variants(brief, num_variants)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if provider_key == "gemini" or (provider_key == "auto" and api_key):
        try:
            return generate_variants_with_gemini(brief, num_variants, model_name)
        except Exception as e:
            logger.warning("Gemini API 呼び出しに失敗したため、動的モックへフォールバックします: %s", e)
            return generate_mock_variants(brief, num_variants)

    logger.info("APIキー未設定またはプロバイダー指定なしのため、動的モック生成を使用します。")
    return generate_mock_variants(brief, num_variants)
