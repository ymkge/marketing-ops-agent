# Marketing Ops Agent (マーケティング業務自動化・コンテンツ運用改善 AIエージェント)

マーケティング業務の効率化・自動化およびコンテンツ運用の改善を支援するAIエージェント開発リポジトリ（モノレポ）です。  
LLM（Google AI Studio / Gemini、Claude、GPT-4o）やワークフロー自動化（n8n）、データ処理・ドキュメント自動生成ライブラリを活用し、**提案書作成**・**データレポーティング**・**クリエイティブ制作**の一連のプロセスを自動化・高度化します。

---

## 🚦 開発ステータス & ロードマップ

| モジュール / テーマ | 概要 | ステータス |
| :--- | :--- | :---: |
| **01. 提案スライド自動生成 (`01_proposal_generator`)** | 企画メモから5枚構成のPowerPoint（`.pptx`）スライド自動生成（Gemini無料API対応） | ✅ **実装完了** (v0.2.0) |
| **02. レポート自動化 (`02_report_automation`)** | 広告・アナリティクス実績データの自動集計・インサイト考察 | 📋 設計中 / 次期着手 |
| **03. クリエイティブ生成パイプライン (`03_creative_pipeline`)** | 広告コピー量産・画像生成API連携・n8nワークフロー | 📋 設計中 / 次期着手 |
| **開発ワークフロー規約 (`.agents/`)** | 計画書承認・自動テスト・内部レビュー・ウォークスルー規約 | ✅ **運用中** |

---

## 📁 ディレクトリ構成

```text
marketing-ops-agent/
├── README.md                      # プロジェクト全体ドキュメント（本ファイル）
├── .gitignore                     # Git除外設定 (Python, Node, .env, outputs/, tmp/)
├── .env.example                   # 環境変数テンプレート (LLM APIキー, n8n設定等)
├── requirements.txt               # Python共通依存パッケージ一覧
├── docker-compose.yml             # ローカル用 n8n 実行用 Docker Compose 設定
├── .agents/                       # AIエージェント開発規約・ワークフロー定義
│   ├── AGENTS.md                  # エージェント基本行動ルール
│   └── rules/
│       └── development_workflow.md # 開発・修正プロセスの厳格ルール
├── 01_proposal_generator/         # [Module 1] 提案スライド自動生成 (実装完了)
│   ├── README.md                  # モジュール詳細ドキュメント
│   ├── samples/
│   │   └── sample_brief.json      # テスト用企画ブリーフ（BtoB SaaS案件想定）
│   ├── src/
│   │   ├── models.py              # Pydanticデータモデル (BriefInput, ProposalDeck等)
│   │   ├── llm_client.py          # LLM連携 (Gemini / Anthropic / OpenAI / Mock)
│   │   └── pptx_builder.py        # python-pptx 描画ビルダー (16:9 カードレイアウト)
│   ├── scripts/
│   │   └── generate_slides.py     # CLI実行エントリーポイント
│   ├── tests/
│   │   └── test_proposal_generator.py # 自動テストスイート (Pytest 9件)
│   └── outputs/                   # 生成されたスライド成果物 (.pptx)
├── 02_report_automation/          # [Module 2] レポート自動化 (準備中)
│   └── README.md
└── 03_creative_pipeline/          # [Module 3] クリエイティブ生成パイプライン (準備中)
    └── README.md
```

---

## 🛠️ 環境構築手順

### 前提条件
- **Python**: 3.10 以上 (Python 3.12 推奨)
- **Docker / Docker Compose**: n8n のローカル実行に利用

### 1. リポジトリのクローン・準備
```bash
git clone <repository-url>
cd marketing-ops-agent
```

### 2. 環境変数の設定
`.env.example` をコピーして `.env` を作成し、必要なAPIキーを設定します。
```bash
cp .env.example .env
```
Google AI Studio の無料APIキーを利用する場合:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```
※ APIキーが未設定の場合でも、自動的に高品質モックへフォールバックしてローカル動作確認が可能です。

### 3. Python 仮想環境の構築 & パッケージ導入
```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境のアクティベート (macOS / Linux)
source .venv/bin/activate

# 依存パッケージのインストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. n8n ワークフローエンジンの起動 (任意)
クリエイティブパイプラインや外部連携で利用する n8n を起動します。
```bash
docker compose up -d
```
起動後、ブラウザで [http://localhost:5678](http://localhost:5678) にアクセスして初期設定を行えます。

---

## 🎯 実装済みモジュール紹介: `01_proposal_generator`

クライアントの課題やヒアリング情報（企画メモ・ブリーフ）をもとに、LLMが5枚構成のスライド骨子を構造化データとして策定し、`python-pptx` を用いて 16:9 ワイド画面の PowerPoint スライドを自動生成します。

### スライド構成（全5枚）
1. **`01. 表紙 (cover)`**: プロジェクト名、サブタイトル、クライアント名、提案者、日付、Confidential表記
2. **`02. 課題認識 (challenges)`**: 現状課題、根本要因、アプローチ方針の3カラムカード
3. **`03. ターゲット・訴求設計 (target_strategy)`**: ペルソナ定義、商材の差別化バリュー、クリエイティブ訴求軸
4. **`04. 配信シミュレーション (simulation)`**: 予算アロケーション、目標KPI試算、運用PDCA方針
5. **`05. スケジュール・体制 (schedule_team)`**: 12週ロードマップ、推進体制、定例報告スキーム

### 主な特長
- **Google AI Studio (Gemini) 対応**: 無料で利用可能な Gemini API (`gemini-2.0-flash` 等) による高速かつ高精度なスライド構造化出力（Structured Outputs）を標準サポート。
- **重なり防止・動的文字調整**: 座標と高さを分離計算したカード型レイアウト。文字数や箇条書きの行数に応じた自動フォントサイズ縮小・余白調整機能を備え、テキストボックス同士の重なりや文字溢れを防止。
- **高耐障害性フォールバック**: APIキー未設定時やネットワーク障害時でも、高品質なルールベースモック生成へ自動フォールバック。

### 実行方法

```bash
# 基本実行 (Gemini APIキーがあれば自動利用、なければモックへフォールバック)
python 01_proposal_generator/scripts/generate_slides.py \
  --input 01_proposal_generator/samples/sample_brief.json \
  --output 01_proposal_generator/outputs/sample_proposal.pptx

# Gemini API を明示指定して実行
python 01_proposal_generator/scripts/generate_slides.py \
  --input 01_proposal_generator/samples/sample_brief.json \
  --output 01_proposal_generator/outputs/sample_proposal.pptx \
  --provider gemini \
  --model gemini-2.0-flash
```

---

## 🧪 自動テストの実行

本プロジェクトではデグレ防止のため、ユニットテストおよびCLIエンドツーエンドテストを整備しています。

```bash
# 全自動テストの実行
pytest 01_proposal_generator/tests/ -v
```

**テスト項目一覧**:
- `test_brief_model_validation`: 企画メモ入力モデルのバリデーション検証
- `test_mock_deck_generation`: 5枚構成スライドモデルの整合性検証
- `test_pptx_builder_creates_valid_deck`: 16:9比率、破損のないPPTX生成、テキスト描画検証
- `test_cli_execution_with_mock`: CLIコマンドの正常系E2E実行テスト
- `test_cli_execution_with_invalid_input`: 異常系（存在しないファイルパス等）のエラーハンドリング検証

---

## 🛡️ 開発・修正ワークフロー規約 (`.agents/`)

本リポジトリでの機能開発および修正作業は、以下の4ステップを必ず遵守して進められます。

1. **実装計画書の提示とユーザー事前承認**:
   - 実装前に「ゴール」「対象ファイル」「デグレ・リスク情報」「テスト方針」を提示し、ユーザーの「OK」承認を得てからコード変更に着手する。
2. **機能実装 & 自動テスト（デグレ検証）**:
   - 実装と並行してテストを作成し、全テスト合格を確認する。
3. **サブエージェントによる内部レビュー & ブラッシュアップ**:
   - レビュー担当サブエージェントを召喚し、堅牢性・保守性・レイアウト等の観点からコードを改善する。
4. **ウォークスルーの作成・報告**:
   - 検証ログ・成果物・手順をまとめたレポートを提出する。
