"""Data models for ad performance reporting, aggregation, and AI insights."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class RawAdRecord(BaseModel):
    """CSVまたはJSONから取得した単一の広告配信実績レコード"""
    date: str = Field(description="実績日付 (YYYY-MM-DD)")
    channel: str = Field(description="広告媒体 (Google Ads, Meta Ads 等)")
    campaign_name: str = Field(description="キャンペーン名")
    impressions: int = Field(ge=0, description="表示回数 (インプレッション)")
    clicks: int = Field(ge=0, description="クリック数")
    cost: float = Field(ge=0.0, description="消化コスト (円)")
    conversions: float = Field(ge=0.0, description="獲得数 (コンバージョン)")
    revenue: float = Field(default=0.0, ge=0.0, description="発生売上 (円)")


class MetricSummary(BaseModel):
    """主要KPIの集計サマリー"""
    cost: float = Field(description="総消化コスト (円)")
    impressions: int = Field(description="総インプレッション数")
    clicks: int = Field(description="総クリック数")
    conversions: float = Field(description="総コンバージョン数")
    revenue: float = Field(default=0.0, description="総売上 (円)")
    
    # ゼロ除算を考慮したオプショナル指標 (None時はレポート上で "-" 表記)
    ctr: Optional[float] = Field(default=None, description="クリック率 (CTR: %)")
    cpc: Optional[float] = Field(default=None, description="クリック単価 (CPC: 円)")
    cvr: Optional[float] = Field(default=None, description="コンバージョン率 (CVR: %)")
    cpa: Optional[float] = Field(default=None, description="顧客獲得単価 (CPA: 円)")
    roas: Optional[float] = Field(default=None, description="費用対効果 (ROAS: %)")


class ChannelSummary(BaseModel):
    """媒体別の集計パフォーマンス"""
    channel: str = Field(description="媒体名")
    metrics: MetricSummary = Field(description="媒体の集計指標")
    cost_share: float = Field(description="総費用に対するシェア率 (%)")
    conversion_share: float = Field(description="総CVに対するシェア率 (%)")


class DailyTrend(BaseModel):
    """日別の推移指標"""
    date: str = Field(description="日付 (YYYY-MM-DD)")
    cost: float = Field(description="消化コスト (円)")
    clicks: int = Field(description="クリック数")
    conversions: float = Field(description="コンバージョン数")
    cpa: Optional[float] = Field(default=None, description="日別CPA (円)")
    roas: Optional[float] = Field(default=None, description="日別ROAS (%)")


class AggregatedData(BaseModel):
    """pandasによってクレンジング・集計されたデータセット"""
    period_start: str = Field(description="集計開始日 (YYYY-MM-DD)")
    period_end: str = Field(description="集計終了日 (YYYY-MM-DD)")
    total: MetricSummary = Field(description="全体合算サマリー")
    by_channel: List[ChannelSummary] = Field(default_factory=list, description="媒体別集計リスト")
    daily_trends: List[DailyTrend] = Field(default_factory=list, description="日別推移リスト")


class ChannelEvaluation(BaseModel):
    """LLMによる媒体別要因分析"""
    channel: str = Field(description="媒体名")
    status: Literal["good", "warning", "neutral"] = Field(
        description="成果ステータス (good: 好調, warning: 要改善, neutral: 横ばい)"
    )
    comment: str = Field(description="評価コメントおよび要因分析")
    primary_driver: str = Field(description="成果を牽引・悪化させた主因 (例: リマーケティングの好調, 検索CPC高騰)")


class ActionItem(BaseModel):
    """LLMが提案する次週・次月の改善施策"""
    title: str = Field(description="施策タイトル")
    priority: Literal["High", "Medium", "Low"] = Field(description="施策優先度")
    target_channel: str = Field(description="対象媒体 (または 全体)")
    description: str = Field(description="施策の具体的アクション内容と期待効果")


class InsightAnalysis(BaseModel):
    """LLM (Gemini) が生成する定性的な考察・改善示唆"""
    executive_summary: str = Field(description="レポート全体の総括・経営陣向け要約 (2〜3文)")
    channel_evaluations: List[ChannelEvaluation] = Field(
        default_factory=list,
        description="各媒体の成果評価と要因分析"
    )
    key_findings: List[str] = Field(
        default_factory=list,
        description="データから読み取れる顕著な傾向・ボトルネック・成功パターン (3〜4項目)"
    )
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="推奨するネクストアクション一覧"
    )


class MarketingReport(BaseModel):
    """集計数値とAIインサイトを統合した完成レポートモデル"""
    report_title: str = Field(description="レポートタイトル")
    generated_at: str = Field(description="レポート生成日時")
    data: AggregatedData = Field(description="集計数値データ")
    insights: InsightAnalysis = Field(description="AI分析・インサイト考察")
