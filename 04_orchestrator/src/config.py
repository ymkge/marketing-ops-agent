"""Campaign configuration loader and data converter for 04_orchestrator."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator
import yaml

logger = logging.getLogger(__name__)

HEX_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

DEFAULT_COLORS = {
    "primary": "#2563EB",
    "secondary": "#1E40AF",
    "accent": "#F59E0B",
    "background": "#F8FAFC"
}


class BrandColorConfig(BaseModel):
    """ブランドカラー設定"""
    primary: str = Field(default="#2563EB", description="プライマリカラー")
    secondary: str = Field(default="#1E40AF", description="セカンダリカラー")
    accent: str = Field(default="#F59E0B", description="アクセントカラー")
    background: str = Field(default="#F8FAFC", description="背景色")

    @field_validator("primary", "secondary", "accent", "background")
    @classmethod
    def validate_hex(cls, v: str, info: ValidationInfo) -> str:
        v = v.strip()
        if not HEX_REGEX.match(v):
            return DEFAULT_COLORS.get(info.field_name, "#2563EB")
        return v


class CampaignConfig(BaseModel):
    """マーケティング統合案件設定（提案・レポート・クリエイティブ共通）"""
    campaign_name: str = Field(..., min_length=1, description="キャンペーン名 / 案件名")
    client_name: str = Field(default="クライアント企業", description="クライアント企業名")
    target_service: Optional[str] = Field(default=None, description="対象商材・サービス名")
    category: str = Field(default="BtoB SaaS", description="商材カテゴリ・業種")
    target_audience: str = Field(default="意思決定責任者・実務リーダー", description="ターゲットペルソナ")
    
    # 課題と特徴
    client_challenges: List[str] = Field(default_factory=list, description="顧客の抱える課題")
    product_features: List[str] = Field(default_factory=list, description="商材の特徴・機能")
    value_propositions: List[str] = Field(default_factory=list, description="提供価値・ベネフィット")
    
    # 運用・提案パラメータ
    budget: Optional[str] = Field(default="月額100万円〜", description="想定予算")
    timeline: Optional[str] = Field(default="3ヶ月集中運用", description="配信・提案スケジュール")
    kpis: List[str] = Field(default_factory=list, description="目標KPI")
    team_structure: Optional[str] = Field(default="マーケティングOpsチーム", description="推進体制")
    
    # ブランド・表現ガイドライン
    brand_colors: BrandColorConfig = Field(default_factory=BrandColorConfig, description="ブランドカラー設定")
    forbidden_words: List[str] = Field(default_factory=list, description="禁止キーワード")
    tone_and_manner: str = Field(default="プロフェッショナル、信頼感、明快", description="トーン＆マナー")
    
    # 実行プロバイダー設定
    default_provider: str = Field(default="auto", description="デフォルトLLMプロバイダー (auto/gemini/mock)")
    default_model: Optional[str] = Field(default=None, description="LLMモデル名 (未指定時は汎用最新)")

    def to_brief_input_dict(self) -> Dict[str, Any]:
        """01_proposal_generator の BriefInput に適合する辞書を生成"""
        p_name = self.target_service or self.campaign_name
        return {
            "client_name": self.client_name,
            "project_name": f"{self.campaign_name} プロモーション提案",
            "target_service": p_name,
            "client_challenges": self.client_challenges or ["業務の属人化と運用コストの増大"],
            "target_audience": [self.target_audience],
            "product_features": self.product_features or ["最新AIによる自律運用", "即日導入可能な柔軟性"],
            "budget": self.budget,
            "timeline": self.timeline,
            "kpis": self.kpis or ["想定リード獲得数: 月間100件以上", "目標CPA: 15,000円以内"],
            "team_structure": self.team_structure
        }

    def to_creative_brief_dict(self) -> Dict[str, Any]:
        """03_creative_pipeline の CreativeBrief に適合する辞書を生成"""
        p_name = self.target_service or self.campaign_name
        return {
            "product_name": p_name,
            "category": self.category,
            "target_audience": self.target_audience,
            "key_features": self.product_features or ["最新AIによる自動化", "導入即日から利用可能"],
            "pain_points": self.client_challenges or ["日々の運用負担とチーム疲弊"],
            "value_propositions": self.value_propositions or ["工数大幅削減とROI向上"],
            "brand_colors": {
                "primary": self.brand_colors.primary,
                "secondary": self.brand_colors.secondary,
                "accent": self.brand_colors.accent,
                "background": self.brand_colors.background
            },
            "forbidden_words": self.forbidden_words,
            "tone_and_manner": self.tone_and_manner
        }


def load_campaign_config(config_path: str | Path) -> CampaignConfig:
    """YAML または JSON ファイルから CampaignConfig をロード"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # YAML / JSON 読み込み
    try:
        data = yaml.safe_load(content)
    except Exception:
        data = json.loads(content)

    if not isinstance(data, dict):
        raise ValueError(f"設定ファイルのルートはマッピング（辞書）形式である必要があります: {config_path}")

    return CampaignConfig.model_validate(data)
