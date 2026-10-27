"""Insight analyzer using Gemini API with Structured Outputs and dynamic mock fallback."""

import json
import logging
import os
from typing import Optional

from .models import AggregatedData, InsightAnalysis, ChannelEvaluation, ActionItem

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """あなたは大手デジタルマーケティングエージェンシーのシニアデータアナリストです。
提供された広告配信実績の集計データ（全体KPI、媒体別内訳、日別トレンド）を綿密に分析し、
マーケティング責任者や経営陣が次の意思決定を即座に下せる「定例マーケティングレポートの考察（InsightAnalysis）」を作成してください。

分析の指針:
1. 全体総括 (executive_summary): 予算消化に対する目標達成状況、全体のCPA・ROAS動向を2〜3文で簡潔にまとめる。
2. 媒体別評価 (channel_evaluations): 各媒体（Google, Meta等）の勝因・ボトルネック（CTR, CPC, CVR, CPAの観点）を深掘りする。
3. 重要インサイト (key_findings): 数値の乖離や曜日トレンド、媒体間の獲得効率の差など重要な発見を3〜4項目箇条書きにする。
4. 改善施策 (action_items): 翌週・翌月に実施すべき具体的でインパクトの大きいアクションを優先度（High/Medium/Low）をつけて提示する。

必ず InsightAnalysis スキーマに完全準拠したJSONを出力してください。
"""


def _build_summary_prompt(data: AggregatedData) -> str:
    """集計結果からプロンプト用テキストテーブルを生成（トークン消費の極小化）"""
    total = data.total
    lines = [
        f"# 集計対象期間: {data.period_start} 〜 {data.period_end}",
        "",
        "## 全体パフォーマンス:",
        f"- 総コスト: ¥{total.cost:,.0f}",
        f"- 総インプレッション: {total.impressions:,}",
        f"- 総クリック数: {total.clicks:,} (CTR: {total.ctr or '-'}%)",
        f"- 平均CPC: ¥{total.cpc or '-'}",
        f"- 総コンバージョン: {total.conversions:,.0f} (CVR: {total.cvr or '-'}%)",
        f"- 全体平均CPA: ¥{total.cpa or '-'}",
        f"- 総売上: ¥{total.revenue:,.0f} (ROAS: {total.roas or '-'}%)",
        "",
        "## 媒体別パフォーマンス内訳:"
    ]

    for ch in data.by_channel:
        m = ch.metrics
        lines.append(
            f"### 【{ch.channel}】 (費用シェア: {ch.cost_share:.1f}%, CVシェア: {ch.conversion_share:.1f}%)\n"
            f"- コスト: ¥{m.cost:,.0f} | CV: {m.conversions:,.0f} | CPA: ¥{m.cpa or '-'} | "
            f"CTR: {m.ctr or '-'}% | CPC: ¥{m.cpc or '-'} | CVR: {m.cvr or '-'}% | ROAS: {m.roas or '-'}%"
        )

    lines.append("\n## 日別推移サマリー:")
    for d in data.daily_trends:
        lines.append(
            f"- {d.date}: コスト ¥{d.cost:,.0f}, クリック {d.clicks}, CV {d.conversions}, CPA ¥{d.cpa or '-'}, ROAS {d.roas or '-'}%"
        )

    return "\n".join(lines)


def generate_mock_insights(data: AggregatedData) -> InsightAnalysis:
    """実データの集計数値と連動した高品質な動的モックインサイトを生成"""
    total = data.total
    by_channel = data.by_channel

    # 最低CPA媒体（最優秀）と最高CPA媒体（改善対象）を特定
    valid_cpa_channels = [ch for ch in by_channel if ch.metrics.cpa is not None and ch.metrics.conversions > 0]
    best_channel = min(valid_cpa_channels, key=lambda x: x.metrics.cpa) if valid_cpa_channels else (by_channel[0] if by_channel else None)
    worst_channel = max(valid_cpa_channels, key=lambda x: x.metrics.cpa) if valid_cpa_channels else None

    # 総括の作成
    exec_summary = (
        f"当期間（{data.period_start}〜{data.period_end}）の総広告費は¥{total.cost:,.0f}、総獲得件数は{total.conversions:,.0f}件（平均CPA ¥{total.cpa:,.0f}）となりました。"
    )
    if total.roas:
        exec_summary += f" 総売上¥{total.revenue:,.0f}に対しROAS {total.roas:.1f}%を達成し、費用対効果は堅調に推移しています。"

    # 媒体別評価
    evaluations = []
    for ch in by_channel:
        m = ch.metrics
        if best_channel and ch.channel == best_channel.channel:
            status = "good"
            comment = f"CPA ¥{m.cpa or 0:,.0f}と最も高効率でCVを獲得。CVR {m.cvr or 0:.2f}%と高く、コンバージョン獲得の主力エンジンとなっています。"
            driver = "ブランド指名キーワードおよび高確度オーディエンスの刈り取り成功"
        elif worst_channel and ch.channel == worst_channel.channel:
            status = "warning"
            comment = f"費用シェア{ch.cost_share:.1f}%を占める一方、CPAが¥{m.cpa or 0:,.0f}と高騰。クリック単価（CPC ¥{m.cpc or 0:,.0f}）の抑制またはLP離脱改善が急務です。"
            driver = "獲得初期段階の潜在層リーチ偏重およびクリエイティブ疲弊"
        else:
            status = "neutral"
            comment = f"消化コスト¥{m.cost:,.0f}、CPA ¥{m.cpa or 0:,.0f}で安定推移。継続的なクリエイティブ検証を推奨します。"
            driver = "ターゲットセグメント配信の適正化"

        evaluations.append(
            ChannelEvaluation(
                channel=ch.channel,
                status=status,
                comment=comment,
                primary_driver=driver
            )
        )

    # 重要インサイト
    findings = [
        f"全体獲得件数{total.conversions:,.0f}件のうち、{best_channel.channel if best_channel else '主要媒体'}が全体の{best_channel.conversion_share if best_channel else 0:.1f}%を牽引。",
        f"全体CTRは{total.ctr or 0:.2f}%、平均CPCは¥{total.cpc or 0:,.0f}であり、想定許容単価内でリード流入を確保。",
        "日別推移において平日後半にかけて商談化リードのCV数が増加する傾向を確認。"
    ]

    # アクションアイテム
    action_items = [
        ActionItem(
            title=f"{best_channel.channel if best_channel else '主力媒体'}への予算シフトと配信強化",
            priority="High",
            target_channel=best_channel.channel if best_channel else "全体",
            description=f"高効率（CPA ¥{best_channel.metrics.cpa if best_channel else 0:,.0f}）を維持しているため、週次予算配分を15%増額し、獲得件数の最大化を図る。"
        ),
        ActionItem(
            title="クリエイティブのリフレッシュと訴求軸ABテスト",
            priority="Medium",
            target_channel=worst_channel.channel if worst_channel else "全体",
            description="CTR低下とCPA高騰の兆候が見られるキャンペーンに対し、新規ホワイトペーパー訴求バナーを投入してリフレッシュを実施する。"
        ),
        ActionItem(
            title="コンバージョン導線（LP/入力フォーム）のEFO改善",
            priority="Low",
            target_channel="全体",
            description="モバイル流入からのフォーム離脱率を改善するため、必須項目の整理と自動入力補完を適用する。"
        )
    ]

    return InsightAnalysis(
        executive_summary=exec_summary,
        channel_evaluations=evaluations,
        key_findings=findings,
        action_items=action_items
    )


def generate_insights_with_gemini(
    data: AggregatedData,
    model_name: str = "gemini-3.8-flash"
) -> InsightAnalysis:
    """Google GenAI SDK (Gemini API) による構造化インサイト生成"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai パッケージがインストールされていません。pip install google-genai を実行してください。")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("環境変数 GEMINI_API_KEY または GOOGLE_API_KEY が設定されていません。")

    client = genai.Client(api_key=api_key)

    summary_text = _build_summary_prompt(data)
    prompt = f"以下の広告配信集計データから、InsightAnalysisスキーマに準拠した要因分析・考察を作成してください:\n\n{summary_text}"

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=InsightAnalysis,
            temperature=0.7,
        )
    )

    response_text = response.text.strip()
    analysis_dict = json.loads(response_text)
    return InsightAnalysis.model_validate(analysis_dict)


def generate_insights(
    data: AggregatedData,
    provider: str = "auto",
    model_name: Optional[str] = None
) -> InsightAnalysis:
    """プロバイダー指定または自動判定によるインサイト生成"""
    valid_providers = {"auto", "gemini", "mock"}
    provider_key = provider.lower()
    if provider_key not in valid_providers:
        raise ValueError(f"未対応のプロバイダーです: '{provider}'. 対応プロバイダー: {sorted(list(valid_providers))}")

    if provider_key == "mock":
        return generate_mock_insights(data)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if provider_key == "gemini":
        return generate_insights_with_gemini(data, model_name or "gemini-3.8-flash")

    # auto の場合: Gemini -> Mock
    if gemini_key:
        try:
            return generate_insights_with_gemini(data, model_name or "gemini-3.8-flash")
        except Exception as e:
            logger.warning("Gemini APIの呼び出しに失敗しました (%s)。動的モックへフォールバックします。", e)

    logger.info("APIキー未設定またはエラーのため、動的モック生成を実行します。")
    return generate_mock_insights(data)
