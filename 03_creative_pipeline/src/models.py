"""Pydantic data models for 03_creative_pipeline."""

import re
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

HEX_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


class AspectRatio(str, Enum):
    """バナー画像のアスペクト比"""
    SQUARE_1_1 = "1:1"          # 1080x1080 (Instagram / Facebook Feed, X)
    LANDSCAPE_191_1 = "1.91:1"  # 1200x628 (Facebook / Meta Feed, Google Display, X Summary)
    STORY_9_16 = "9:16"         # 1080x1920 (Instagram Stories, Reels, TikTok)

    @property
    def dimensions(self) -> tuple[int, int]:
        """推奨解像度 (width, height) を返す"""
        if self == AspectRatio.SQUARE_1_1:
            return (1080, 1080)
        elif self == AspectRatio.LANDSCAPE_191_1:
            return (1200, 628)
        elif self == AspectRatio.STORY_9_16:
            return (1080, 1920)
        return (1080, 1080)


class AdChannel(str, Enum):
    """広告配信チャネル"""
    GOOGLE_SEARCH = "google_search"
    META = "meta"
    X_TWITTER = "x_twitter"


class BrandColors(BaseModel):
    """ブランドカラー設定（HEXカラーコード）"""
    primary: str = Field(default="#2563EB", description="プライマリカラー（メイン）")
    secondary: str = Field(default="#1E40AF", description="セカンダリカラー")
    accent: str = Field(default="#F59E0B", description="アクセントカラー（CTA等）")
    background: str = Field(default="#F8FAFC", description="背景ベースカラー")

    @field_validator("primary", "secondary", "accent", "background")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        v = v.strip()
        if not HEX_REGEX.match(v):
            return "#2563EB"
        return v


class CreativeBrief(BaseModel):
    """クリエイティブ生成用ブリーフ（商材・ターゲット・訴求情報）"""
    product_name: str = Field(..., min_length=1, description="商材・サービス名")
    category: str = Field(..., min_length=1, description="カテゴリ・業種")
    target_audience: str = Field(..., min_length=1, description="ターゲットペルソナ")
    key_features: List[str] = Field(default_factory=list, description="主要な機能・特徴")
    pain_points: List[str] = Field(default_factory=list, description="顧客の抱える課題・ペイン")
    value_propositions: List[str] = Field(default_factory=list, description="提供価値・ベネフィット")
    brand_colors: BrandColors = Field(default_factory=BrandColors, description="ブランドカラー")
    forbidden_words: List[str] = Field(default_factory=list, description="使用禁止キーワード")
    tone_and_manner: Optional[str] = Field(default="プロフェッショナル、信頼感、明快", description="トーン＆マナー")


class GoogleSearchCopy(BaseModel):
    """Google検索広告向けコピー（規定文字数準拠）"""
    headline_1: str = Field(..., max_length=30, description="見出し1 (30文字以内)")
    headline_2: str = Field(..., max_length=30, description="見出し2 (30文字以内)")
    headline_3: str = Field(..., max_length=30, description="見出し3 (30文字以内)")
    description_1: str = Field(..., max_length=90, description="説明文1 (90文字以内)")
    description_2: str = Field(..., max_length=90, description="説明文2 (90文字以内)")


class MetaCopy(BaseModel):
    """Meta (FB/IG) 広告向けコピー"""
    primary_text: str = Field(..., max_length=200, description="メインテキスト (推奨125文字以内)")
    headline: str = Field(..., max_length=40, description="見出し (40文字以内)")
    description: str = Field(..., max_length=50, description="ニュースフィードリンク説明文 (50文字以内)")
    cta_type: str = Field(default="詳しくはこちら", description="CTAボタン文言")


class XCopy(BaseModel):
    """X (旧Twitter) 広告向けコピー"""
    post_text: str = Field(..., max_length=140, description="ポスト本文 (140文字以内)")
    card_headline: str = Field(..., max_length=40, description="ウェブサイトカード見出し (40文字以内)")
    cta_type: str = Field(default="今すぐチェック", description="カードCTA")


class ImagePrompt(BaseModel):
    """画像生成モデル（Imagen 3 / DALL-E 3等）向けプロンプト定義"""
    prompt_en: str = Field(..., description="画像生成AI向け詳細英語プロンプト")
    prompt_ja: str = Field(..., description="日本語プロンプト解説・意図")
    style: str = Field(default="modern minimal 3D tech illustration", description="ビジュアルスタイル")
    negative_prompt: Optional[str] = Field(
        default="blurry, distorted, low quality, messy text, cluttered",
        description="ネガティブプロンプト"
    )
    banner_catchphrase: str = Field(..., max_length=30, description="画像内に合成するメインキャッチコピー (30文字以内)")
    banner_subphrase: Optional[str] = Field(default=None, max_length=50, description="画像内サブコピー (50文字以内)")


class GeneratedImage(BaseModel):
    """生成された画像素材メタデータ"""
    aspect_ratio: str = Field(..., description="アスペクト比 ('1:1', '1.91:1', '9:16')")
    file_path: str = Field(..., description="画像保存パス（相対または絶対パス）")
    width: int = Field(..., description="画像横幅 (px)")
    height: int = Field(..., description="画像縦幅 (px)")
    generator_type: str = Field(..., description="生成エンジン ('pillow_banner', 'imagen3', etc.)")


class CreativeVariant(BaseModel):
    """1つの訴求軸に対するクリエイティブバリエーション（ABテストの1パターン）"""
    variant_id: str = Field(..., description="バリアント記号 (例: 'Variant-A', 'Variant-B')")
    approach_name: str = Field(..., description="訴求軸アプローチ名 (例: '時短・効率化訴求', '安心・リスク回避訴求')")
    target_persona_focus: str = Field(..., description="このバリアントが特に狙うターゲット")
    google_search: GoogleSearchCopy = Field(..., description="Google検索広告コピー")
    meta: MetaCopy = Field(..., description="Meta広告コピー")
    x_twitter: XCopy = Field(..., description="X広告コピー")
    image_prompt: ImagePrompt = Field(..., description="画像生成プロンプト")
    generated_images: List[GeneratedImage] = Field(default_factory=list, description="生成された画像一覧")
    hypothesis_reason: str = Field(..., description="このバリエーションの仮説・効果想定")


class CreativeBatchResult(BaseModel):
    """クリエイティブ生成パイプライン全体のバッチ出力結果"""
    campaign_name: str = Field(..., description="キャンペーン名 / 商材名")
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"), description="生成日時")
    brief: CreativeBrief = Field(..., description="入力ブリーフ")
    variants: List[CreativeVariant] = Field(default_factory=list, description="生成されたバリアント一覧")
    total_images: int = Field(default=0, description="生成画像総数")
