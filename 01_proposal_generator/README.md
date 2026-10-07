# 01. Proposal Generator (提案スライド自動生成モジュール)

## 概要
クライアントの課題やヒアリング情報（企画メモ・ブリーフ）をもとに、LLM（Google AI Studio / Gemini、Claude、GPT-4o）がスライド構成案（アウトライン）を構造化データとして作成し、`python-pptx` を活用して PowerPoint（`.pptx`）スライドを自動生成するモジュールです。

## 主な機能
- **企画ブリーフの解析**: クライアント課題、商材特徴、ターゲット層、予算、KPI、施策方針の入力に対応
- **LLMによる構成案作成**:
  - **Google AI Studio (Gemini)**: 公式 `google-genai` SDK を用い、Pydantic モデルに準拠した Structured Outputs（ネイティブ構造化出力）で安定生成
  - **Anthropic API (Claude)** / **OpenAI API (GPT-4o)** もサポート
  - APIキー未設定時やオフライン時は高品質モックへ自動フォールバック
- **5枚構成のスライド出力**:
  1. `表紙 (cover)`: プロジェクト名・サブタイトル・宛先・提出者・日付
  2. `課題認識 (challenges)`: 現状のボトルネックと解くべき真の課題
  3. `ターゲット・訴求設計 (target_strategy)`: ペルソナとクリエイティブ訴求軸
  4. `配信シミュレーション (simulation)`: 予算配分と目標KPI・運用方針
  5. `スケジュール・体制 (schedule_team)`: 推進ロードマップと実行体制
- **重なり防止レイアウト**: 16:9 ワイド画面を採用し、文字数に応じたフォントサイズ動的縮小・行間余白調整により、タイトルや箇条書きカードの重なり・文字溢れを自動防止

## ディレクトリ構成
```text
01_proposal_generator/
├── README.md                  # 本ドキュメント
├── samples/
│   └── sample_brief.json      # テスト用企画メモサンプル
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydanticデータモデル (BriefInput, ProposalDeck等)
│   ├── llm_client.py          # LLM連携 (Gemini / Anthropic / OpenAI / Mock)
│   └── pptx_builder.py        # python-pptx によるスライド生成・レイアウト計算
├── scripts/
│   └── generate_slides.py     # CLI実行スクリプト
├── tests/
│   └── test_proposal_generator.py # 自動テストスイート (Pytest)
└── outputs/                   # 生成されたスライド出力先 (.pptx)
```

## 使い方・実行方法

### 1. 依存パッケージの準備
ルートディレクトリの `requirements.txt` に含まれるパッケージをインストールします。
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定 (任意)
Google AI Studio の無料APIキーまたは各LLMのAPIキーを設定してください。
```bash
# Google AI Studio (推奨 / 無料APIキー対応)
export GEMINI_API_KEY="your-gemini-api-key"

# または Anthropic / OpenAI
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```
※ APIキーが設定されていない場合でも、自動的にモック生成モードへフォールバックして動作確認が可能です。

### 3. スライド生成コマンドの実行

#### 基本実行（auto モード: Gemini -> Anthropic -> OpenAI -> Mock）
```bash
# 01_proposal_generator ディレクトリ配下から実行
python scripts/generate_slides.py --input samples/sample_brief.json --output outputs/sample_proposal.pptx

# またはリポジトリルートから実行
python 01_proposal_generator/scripts/generate_slides.py --input 01_proposal_generator/samples/sample_brief.json --output 01_proposal_generator/outputs/sample_proposal.pptx
```

#### Gemini API を明示指定して実行
```bash
python 01_proposal_generator/scripts/generate_slides.py \
  --input 01_proposal_generator/samples/sample_brief.json \
  --output 01_proposal_generator/outputs/sample_proposal.pptx \
  --provider gemini \
  --model gemini-2.0-flash
```

#### CLI オプション一覧
| オプション | 短縮 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `--input` | `-i` | `samples/sample_brief.json` | 入力ブリーフファイルのパス（JSONまたはMarkdown） |
| `--output` | `-o` | `outputs/sample_proposal.pptx` | 出力先PPTXファイルのパス |
| `--provider`| `-p` | `auto` | LLMプロバイダー (`auto`, `gemini`, `anthropic`, `openai`, `mock`) |
| `--model` | `-m` | 各プロバイダーデフォルト | 使用するモデル名（例: `gemini-2.0-flash`, `claude-3-5-sonnet-20241022`, `gpt-4o`） |
