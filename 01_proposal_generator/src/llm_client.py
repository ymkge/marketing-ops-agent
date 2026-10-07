"""LLM Client for structuring proposal deck from brief input."""

import json
import logging
import os
from typing import Optional
from datetime import datetime

from .models import BriefInput, ProposalDeck, SlideContent, ContentBlock

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """あなたは大手総合広告代理店およびマーケティングコンサルティングファームのシニアプランナーです。
クライアントの課題・商材特性・ターゲット・予算・KPI等の企画メモ（Brief）を分析し、
経営層およびマーケティング責任者が一目で納得できる、説得力ある5枚構成のプレゼンテーションスライド骨子を作成してください。

構成は以下の厳密な5枚構成とします:
1. 表紙 (cover): 提案タイトル、サブタイトル、クライアント名
2. 課題認識 (challenges): 現状認識、主要ボトルネック、本施策が解くべき真の課題
3. ターゲット・訴求設計 (target_strategy): ペルソナ定義、訴求メッセージ軸、差別化アプローチ
4. 配信シミュレーション (simulation): 予算配分、媒体別想定KPI、獲得コスト（CPA等）試算
5. スケジュール・体制 (schedule_team): フェーズ別ロードマップ、推進体制・役割分担

出力は必ず指定されたJSONフォーマット（ProposalDeckスキーマに完全準拠）で返してください。
余計な前置きやマークダウンの補足は含めず、純粋なJSONのみを出力してください。
"""


def generate_mock_deck(brief: BriefInput) -> ProposalDeck:
    """APIキーがない場合やローカル検証用のモック構成データを生成"""
    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    slides = [
        # 1. 表紙
        SlideContent(
            slide_type="cover",
            title=brief.project_name,
            lead_sentence=f"{brief.target_service or 'マーケティング施策'} 成長最大化に向けた総合プロモーション提案",
            blocks=[
                ContentBlock(
                    heading="クライアント",
                    bullet_points=[brief.client_name]
                ),
                ContentBlock(
                    heading="提案者",
                    bullet_points=[brief.team_structure or "マーケティングソリューションチーム"]
                )
            ],
            footer_note="Confidential - 社外秘"
        ),
        # 2. 課題認識
        SlideContent(
            slide_type="challenges",
            title="現状のマーケティング課題とボトルネック認識",
            lead_sentence="既存チャネルの成長鈍化と差別化訴求の不足により、見込み顧客の獲得効率が低下傾向にあります。",
            blocks=[
                ContentBlock(
                    heading="直面している課題",
                    bullet_points=brief.client_challenges if brief.client_challenges else [
                        "自然流入およびオーガニック成長の頭打ち",
                        "競合サービスとの差別化要素の浸透不足",
                        "商談獲得数・パイプライン不足"
                    ]
                ),
                ContentBlock(
                    heading="課題の根本要因",
                    bullet_points=[
                        "顕在層へのリーチ偏重による潜在層の未開拓",
                        "機能的便益（Feature）に偏った広告メッセージによる共感不足",
                        "検討段階に応じたコンテンツ動線・受け皿の不足"
                    ]
                ),
                ContentBlock(
                    heading="解決へのアプローチ方針",
                    bullet_points=[
                        "課題解決型コンテンツを軸とした潜在・準顕在層の惹きつけ",
                        "ターゲット別ペルソナに最適化した訴求軸のマルチ展開",
                        "認知からリード獲得、商談創出までの一貫したファネル設計"
                    ]
                )
            ],
            footer_note="※ヒアリング内容および競合環境調査に基づく初期分析"
        ),
        # 3. ターゲット・訴求設計
        SlideContent(
            slide_type="target_strategy",
            title="ターゲット選定と訴求メッセージ設計",
            lead_sentence="意思決定関与者を明確に定義し、ペルソナごとの業務課題に直結した価値訴求を展開します。",
            blocks=[
                ContentBlock(
                    heading="コアターゲット層",
                    bullet_points=brief.target_audience if brief.target_audience else [
                        "中堅・大手企業のDX推進部門長および経営企画責任者",
                        "業務属人化とコスト削減に直結する改革リーダー"
                    ]
                ),
                ContentBlock(
                    heading="商材のコアバリュー・差別化要素",
                    bullet_points=brief.product_features if brief.product_features else [
                        "最短即日で導入可能なノーコード自動化基盤",
                        "業界特化型AIエージェントによる高精度な実務代行",
                        "主要業務システムとの柔軟なシームレス連携"
                    ]
                ),
                ContentBlock(
                    heading="クリエイティブ訴求軸",
                    bullet_points=[
                        "【時短・効率訴求】「月間40時間の残業をAIエージェントが削減」",
                        "【安心・実績訴求】「既存システムと即日連携。失敗しないDX基盤」",
                        "【課題解決訴求】「属人化業務からチームを解放する新基準」"
                    ]
                )
            ],
            footer_note="※媒体特性（SNS/検索/動画）に応じて最適なバナー・コピーを出し分け"
        ),
        # 4. 配信シミュレーション
        SlideContent(
            slide_type="simulation",
            title="メディアプランニング＆配信効果シミュレーション",
            lead_sentence=f"予算（{brief.budget or '適正配分'}）に基づき、リード獲得単価を最適化するハイブリッド配信を設計します。",
            blocks=[
                ContentBlock(
                    heading="予算アロケーション方針",
                    bullet_points=[
                        "Meta（FB/IG）広告 [50%]: 課題訴求ホワイトペーパーによる安価なリード獲得",
                        "Google検索広告 [35%]: 顕在ニーズの高い指名・関連キーワード刈り取り",
                        "リマーケティング・検証 [15%]: 離脱層の再エンゲージメントおよび検証枠"
                    ]
                ),
                ContentBlock(
                    heading="目標KPI・試算数値",
                    bullet_points=brief.kpis if brief.kpis else [
                        "想定月間リード獲得数: 250件以上",
                        "目標CPA: 20,000円以内",
                        "有効商談創出数: 60件 / 月（商談化率 24%想定）"
                    ]
                ),
                ContentBlock(
                    heading="最適化・PDCA運用方針",
                    bullet_points=[
                        "週次でのクリエイティブ疲弊度モニタリングと新規バナー投入",
                        "CPAと商談化率の相関分析による配信セグメント毎の入札調整",
                        "LP/フォーム離脱率改善のためのEFO（入力補助）施策連携"
                    ]
                )
            ],
            footer_note="※過去の同業種ベンチマーク実績を基に算出した試算値です"
        ),
        # 5. スケジュール・体制
        SlideContent(
            slide_type="schedule_team",
            title="推進ロードマップとプロジェクト実行体制",
            lead_sentence="キックオフから最速2週間で配信開始し、高速なPDCAサイクルを回す推進体制を構築します。",
            blocks=[
                ContentBlock(
                    heading="フェーズ別ロードマップ",
                    bullet_points=[
                        "Phase 1（W1〜W2）: 要件定義・タグ設計・クリエイティブ制作・初期入稿",
                        "Phase 2（W3〜W6）: 配信開始・初期データ収集・初期クリエイティブABテスト",
                        "Phase 3（W7〜W12）: 獲得効率の最大化・高成果セグメントへの予算集中投下"
                    ]
                ),
                ContentBlock(
                    heading="推進体制・役割分担",
                    bullet_points=[
                        f"全体統括 / 窓口: {brief.team_structure or '専任アカウントマネージャー'}",
                        "広告運用・分析: 運用コンサルタント（デイリー入札最適化・週次報告）",
                        "制作・検証: クリエイティブディレクター（新規訴求制作・コピー改善）"
                    ]
                ),
                ContentBlock(
                    heading="定例コミュニケーション方針",
                    bullet_points=[
                        "週次定例ミーティング（進捗報告・次週施策方針合意）",
                        "日次ダッシュボード共有（成果のリアルタイム可視化）",
                        "月次総括レポーティング（詳細要因分析と翌月プラン見直し）"
                    ]
                )
            ],
            footer_note="※スケジュール期間: " + (brief.timeline or "3ヶ月集中配信")
        )
    ]
    
    return ProposalDeck(
        client_name=brief.client_name,
        proposal_title=brief.project_name,
        proposal_subtitle=f"{brief.target_service or 'マーケティング推進'} 施策提案書",
        presentation_date=today_str,
        presenter_info=brief.team_structure or "マーケティングOps推進チーム",
        slides=slides
    )


def generate_deck_with_anthropic(brief: BriefInput, model_name: str = "claude-3-5-sonnet-20241022") -> ProposalDeck:
    """Anthropic API を呼び出して ProposalDeck を生成"""
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic パッケージがインストールされていません。pip install anthropic を実行してください。")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("環境変数 ANTHROPIC_API_KEY が設定されていません。")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    schema = ProposalDeck.model_json_schema()
    
    prompt = f"""以下の企画メモ（Brief）をもとに、ProposalDeckスキーマに完全準拠したスライド構成JSONを作成してください。

企画メモ（Brief）:
{brief.model_dump_json(indent=2)}

必要なスライド構成:
1. cover（表紙）
2. challenges（課題認識）
3. target_strategy（ターゲット・訴求設計）
4. simulation（配信シミュレーション）
5. schedule_team（スケジュール・体制）

返答は以下のJSONスキーマに従い、JSONコードブロック（```json ... ```）または生JSON形式で返してください。
スキーマ:
{json.dumps(schema, ensure_ascii=False, indent=2)}
"""

    response = client.messages.create(
        model=model_name,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    content_text = response.content[0].text.strip()
    
    if "```json" in content_text:
        content_text = content_text.split("```json")[1].split("```")[0].strip()
    elif "```" in content_text:
        content_text = content_text.split("```")[1].split("```")[0].strip()
        
    deck_dict = json.loads(content_text)
    return ProposalDeck.model_validate(deck_dict)


def generate_deck_with_openai(brief: BriefInput, model_name: str = "gpt-4o") -> ProposalDeck:
    """OpenAI API を呼び出して ProposalDeck を生成"""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai パッケージがインストールされていません。pip install openai を実行してください。")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("環境変数 OPENAI_API_KEY が設定されていません。")
    
    client = OpenAI(api_key=api_key)
    
    # Structured Outputs (beta.chat.completions.parse)
    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"以下の企画メモから5枚構成の提案スライド骨子を作成してください:\n\n{brief.model_dump_json(indent=2)}"
            }
        ],
        response_format=ProposalDeck,
        temperature=0.7
    )
    
    return completion.choices[0].message.parsed


def generate_deck_with_gemini(brief: BriefInput, model_name: str = "gemini-2.0-flash") -> ProposalDeck:
    """Google GenAI SDK (Gemini API) を呼び出して ProposalDeck を生成"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai パッケージがインストールされていません。pip install google-genai を実行してください。")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("環境変数 GEMINI_API_KEY または GOOGLE_API_KEY が設定されていません。")

    client = genai.Client(api_key=api_key)

    prompt = f"""以下の企画メモ（Brief）をもとに、5枚構成の提案スライド骨子を作成してください:

企画メモ:
{brief.model_dump_json(indent=2)}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ProposalDeck,
            temperature=0.7,
        )
    )

    response_text = response.text.strip()
    deck_dict = json.loads(response_text)
    return ProposalDeck.model_validate(deck_dict)


def generate_proposal_deck(
    brief: BriefInput,
    provider: str = "auto",
    model_name: Optional[str] = None
) -> ProposalDeck:
    """プロバイダー指定または環境変数自動判定に基づいてスライド構成を生成"""
    valid_providers = {"auto", "gemini", "anthropic", "openai", "mock"}
    provider_key = provider.lower()
    if provider_key not in valid_providers:
        raise ValueError(f"未対応のプロバイダーです: '{provider}'. 対応プロバイダー: {sorted(list(valid_providers))}")

    if provider_key == "mock":
        return generate_mock_deck(brief)
    
    # プロバイダーが明示されている場合
    if provider_key == "gemini":
        return generate_deck_with_gemini(brief, model_name or "gemini-2.0-flash")
    elif provider_key == "anthropic":
        return generate_deck_with_anthropic(brief, model_name or "claude-3-5-sonnet-20241022")
    elif provider_key == "openai":
        return generate_deck_with_openai(brief, model_name or "gpt-4o")
    
    # auto の場合: 優先順位 Gemini -> Anthropic -> OpenAI -> Mock
    # auto モード時は、プロバイダー間のモデル名衝突を防ぐため個別デフォルトを利用
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        try:
            return generate_deck_with_gemini(brief, model_name or "gemini-2.0-flash")
        except Exception as e:
            logger.warning("Gemini APIの呼び出しに失敗しました (%s)。他プロバイダーまたはモックへフォールバックします。", e)

    if anthropic_key:
        try:
            return generate_deck_with_anthropic(brief, "claude-3-5-sonnet-20241022")
        except Exception as e:
            logger.warning("Anthropic APIの呼び出しに失敗しました (%s)。OpenAIまたはモックへフォールバックします。", e)
    
    if openai_key:
        try:
            return generate_deck_with_openai(brief, "gpt-4o")
        except Exception as e:
            logger.warning("OpenAI APIの呼び出しに失敗しました (%s)。モック生成へフォールバックします。", e)
            
    logger.info("APIキーが未設定またはAPIエラーのため、ルールベース高品質モック生成を実行します。")
    return generate_mock_deck(brief)
