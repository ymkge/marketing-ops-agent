"""Data models for proposal brief and generated slide deck structure."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class BriefInput(BaseModel):
    """企画メモ・ヒアリングシートの入力モデル"""
    client_name: str = Field(description="クライアント企業名")
    project_name: str = Field(description="プロジェクト名・施策名")
    target_service: Optional[str] = Field(default=None, description="対象商材・サービス名")
    client_challenges: List[str] = Field(default_factory=list, description="クライアントの現状課題")
    product_features: List[str] = Field(default_factory=list, description="商材の特徴・強み")
    target_audience: List[str] = Field(default_factory=list, description="ターゲット層・ペルソナ")
    budget: Optional[str] = Field(default=None, description="配信予算・費用感")
    kpis: List[str] = Field(default_factory=list, description="目標KPI（CPA, リード数等）")
    strategy: List[str] = Field(default_factory=list, description="施策方針・アプローチ")
    timeline: Optional[str] = Field(default=None, description="スケジュール期間")
    team_structure: Optional[str] = Field(default=None, description="推進体制")


class ContentBlock(BaseModel):
    """スライド内のコンテンツブロック（カード/カラム相当）"""
    heading: str = Field(description="ブロックの見出し・カテゴリタイトル")
    bullet_points: List[str] = Field(
        default_factory=list,
        description="箇条書きの内容（要点・数値・説明文）"
    )


class SlideContent(BaseModel):
    """単一スライドの構造化データ"""
    slide_type: Literal[
        "cover",                 # 表紙
        "challenges",            # 課題認識
        "target_strategy",       # ターゲット・訴求設計
        "simulation",            # 配信シミュレーション
        "schedule_team"          # スケジュール・体制
    ] = Field(description="スライド種別")
    
    title: str = Field(description="スライドの大見出し・タイトル")
    lead_sentence: Optional[str] = Field(
        default=None,
        description="スライドのキーメッセージ・リード文（要約1〜2行）"
    )
    blocks: List[ContentBlock] = Field(
        default_factory=list,
        description="スライド本文の構成ブロック（2〜3個のカード形式）"
    )
    footer_note: Optional[str] = Field(
        default=None,
        description="スライド下部の注記・前提条件など"
    )


class ProposalDeck(BaseModel):
    """全5枚のスライド構成データ"""
    client_name: str = Field(description="クライアント名")
    proposal_title: str = Field(description="提案書メインタイトル")
    proposal_subtitle: Optional[str] = Field(default=None, description="提案書サブタイトル")
    presentation_date: Optional[str] = Field(default=None, description="提出日・日付")
    presenter_info: Optional[str] = Field(default=None, description="提案者・チーム名")
    slides: List[SlideContent] = Field(
        description="全5枚のスライド（表紙、課題認識、ターゲット・訴求設計、配信シミュレーション、スケジュール・体制）"
    )
