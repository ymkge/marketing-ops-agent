# Marketing Ops Agent (マーケティング業務自動化・コンテンツ運用改善 AIエージェント)

マーケティング業務の効率化・自動化およびコンテンツ運用の改善を支援するAIエージェント開発リポジトリ（モノレポ）です。  
LLM（Google AI Studio / Gemini、Claude、GPT-4o）やワークフロー自動化（n8n）、データ処理・ドキュメント自動生成ライブラリを活用し、**提案書作成**・**データレポーティング**・**クリエイティブ制作**・**運用PDCAループ**の一連のプロセスを自動化・高度化します。

---

## 🚦 開発ステータス & ロードマップ

全4大主要テーマのモジュール実装・自動テスト・内部レビューが完了し、`main` ブランチに統合されています。

| モジュール / テーマ | 概要 | ステータス |
| :--- | :--- | :---: |
| **[01. 提案スライド自動生成](01_proposal_generator/README.md) (`01_proposal_generator`)** | 企画メモから5枚構成のPowerPoint（`.pptx`）スライド自動生成（Gemini無料API対応） | ✅ **実装完了** (v0.2.0) |
| **[02. レポート自動化](02_report_automation/README.md) (`02_report_automation`)** | 広告実績データの自動集計・要因分析・定例レポート（MD/HTML）出力（Gemini無料API対応） | ✅ **実装完了** (v0.1.0) |
| **[03. クリエイティブ生成パイプライン](03_creative_pipeline/README.md) (`03_creative_pipeline`)** | 広告コピー量産・バナー画像合成（Pillow/Imagen 3）・ABテストカタログ・n8nワークフロー | ✅ **実装完了** (v0.1.0) |
| **[04. 統合運用オーケストレーター](04_orchestrator/README.md) (`04_orchestrator`)** | 新規案件一括立ち上げ・PDCA改善クリエイティブ再生成・統合CLI (`ops.py`) | ✅ **実装完了** (v0.1.0) |
| **[開発ワークフロー規約](.agents/rules/development_workflow.md) (`.agents/`)** | 計画書承認・自動テスト・内部レビュー・ウォークスルー規約 | ✅ **運用中** |

---

## 🚀 クイックスタート: 最速で動かす

> 💡 **初回セットアップ**: 先に [🛠️ 環境構築手順](#%EF%B8%8F-環境構築手順) を完了してください。APIキー未設定時でも、自動的に高品質モックで即座に動作します。

統合CLI（`ops.py`）を使用することで、ワンコマンドで実務パイプラインを実行できます。

### 1. 新規案件の一括立ち上げ（提案スライド + 初期クリエイティブ群）
```bash
python 04_orchestrator/scripts/ops.py pipeline --mode launch --output-dir 04_orchestrator/outputs/sample_launch
```
👉 `04_orchestrator/outputs/sample_launch/` に以下が即時生成されます：
- 提案書スライド: `CloudOps AI キャンペーン_proposal.pptx`
- クリエイティブHTMLカタログ: `creatives/creative_catalog.html`
- バナー画像素材: `creatives/*.png` (1:1, 1.91:1)
- 広告コピー一覧: `creatives/creative_copies.csv`

### 2. PDCA運用改善（実績レポーティング + 課題テコ入れクリエイティブ再生成）
```bash
python 04_orchestrator/scripts/ops.py pipeline --mode pdca --output-dir 04_orchestrator/outputs/sample_pdca
```
👉 `04_orchestrator/outputs/sample_pdca/` に以下が即時生成されます：
- 定例広告配信レポート: `performance_report.html`, `performance_report.md`
- 課題テコ入れ改善用クリエイティブカタログ: `remedial_creatives/creative_catalog.html`
- 改善バナー画像素材: `remedial_creatives/*.png`

---

## 📁 ディレクトリ構成

```text
marketing-ops-agent/
├── README.md                      # プロジェクト全体ドキュメント（本ファイル）
├── .gitignore                     # Git除外設定 (Python, Node, .env, outputs/, tmp/)
├── .env.example                   # 環境変数テンプレート (LLM APIキー, モデル設定等)
├── requirements.txt               # Python共通依存パッケージ一覧
├── docker-compose.yml             # ローカル用 n8n 実行用 Docker Compose 設定
├── .agents/                       # AIエージェント開発規約・ワークフロー定義
│   ├── AGENTS.md                  # エージェント基本行動ルール
│   └── rules/
│       └── development_workflow.md # 開発・修正プロセスの厳格ルール
├── 01_proposal_generator/         # [Module 1] 提案スライド自動生成
│   ├── README.md                  # モジュール詳細ドキュメント
│   ├── samples/                   # テスト用企画ブリーフ（JSON）
│   ├── src/                       # Pydanticモデル, Gemini連携, pptx_builder
│   ├── scripts/generate_slides.py # 単体CLIエントリーポイント
│   └── tests/                     # 自動テストスイート (9件)
├── 02_report_automation/          # [Module 2] レポート自動化
│   ├── README.md                  # モジュール詳細ドキュメント
│   ├── samples/                   # 広告配信実績データ (CSV)
│   ├── src/                       # 加重平均プロセッサ, Geminiインサイト分析, report_builder
│   ├── scripts/generate_report.py # 単体CLIエントリーポイント
│   └── tests/                     # 自動テストスイート (13件)
├── 03_creative_pipeline/          # [Module 3] クリエイティブ生成パイプライン
│   ├── README.md                  # モジュール詳細ドキュメント
│   ├── samples/                   # クリエイティブブリーフ (JSON)
│   ├── src/                       # コピー生成, Pillowバナー合成, カタログビルダー
│   ├── scripts/generate_creatives.py # 単体CLIエントリーポイント
│   ├── workflows/                 # n8n 連携ワークフロー定義 (JSON)
│   └── tests/                     # 自動テストスイート (8件)
└── 04_orchestrator/               # [Module 4] 統合運用オーケストレーター
    ├── README.md                  # モジュール詳細ドキュメント
    ├── samples/                   # 統合案件設定ファイル (YAML/JSON)
    ├── src/                       # 設定ローダー, launchパイプライン, pdcaパイプライン, 統合CLI
    ├── scripts/ops.py             # 統合CLI実行エントリーポイント
    ├── workflows/                 # 全体統合 n8n ワークフロー定義 (JSON)
    └── tests/                     # 自動テストスイート (4件)
```

---

## 🛠️ 環境構築手順

### 前提条件
- **Python**: 3.10 以上 (Python 3.12 推奨)
- **Docker / Docker Compose**: n8n のローカル実行に利用（任意）

### 1. リポジトリのクローン・準備
```bash
git clone https://github.com/ymkge/marketing-ops-agent.git
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
# 推奨汎用最新モデルエイリアス（デフォルト: gemini-flash-latest）
export GEMINI_MODEL="gemini-flash-latest"
```
※ APIキーが未設定の場合でも、自動的に動的モック・完全ローカル画像合成（Pillow）へフォールバックして動作確認が可能です。

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

## 🎯 各モジュールの詳細と実行方法

### 1. 提案スライド自動生成 ([01_proposal_generator](01_proposal_generator/README.md))
クライアントの課題やヒアリング情報（企画メモ・ブリーフ）をもとに、LLMが5枚構成のスライド骨子を策定し、`python-pptx` を用いて 16:9 ワイド画面の PowerPoint スライドを自動生成します。

- **構成**: 表紙、課題認識（3カラム）、ターゲット・訴求設計、配信シミュレーション、スケジュール・体制
- **単体実行**:
  ```bash
  python 01_proposal_generator/scripts/generate_slides.py \
    --input 01_proposal_generator/samples/sample_brief.json \
    --output 01_proposal_generator/outputs/sample_proposal.pptx
  ```

### 2. レポート自動化 ([02_report_automation](02_report_automation/README.md))
広告媒体（Google広告、Meta広告等）の配信実績データ（CSV）を加重平均集計し、Gemini API による要因分析・改善インサイトを付与した定例レポート（Markdown / 自己完結型HTML）を自動出力します。

- **特長**: 単純平均を排した正確な加重平均集計、Gemini 503混雑時の自動フェイルオーバー、XSS完全エスケープ
- **単体実行**:
  ```bash
  python 02_report_automation/scripts/generate_report.py \
    --input 02_report_automation/samples/sample_ad_performance.csv \
    --output 02_report_automation/outputs/weekly_report
  ```

### 3. クリエイティブ生成パイプライン ([03_creative_pipeline](03_creative_pipeline/README.md))
商材ブリーフから、媒体別コピー量産（Google RSA / Meta / X）、AI画像プロンプト最適化、Pillowによるバナー画像合成（1:1, 1.91:1, 9:16）、ABテスト比較用HTMLカタログを出力します。

- **特長**: 各媒体の文字数制限を厳格に管理、禁止キーワード自動サニタイズ、Excel数式インジェクション防止
- **単体実行**:
  ```bash
  python 03_creative_pipeline/scripts/generate_creatives.py \
    --input 03_creative_pipeline/samples/sample_creative_brief.json \
    --output-dir 03_creative_pipeline/outputs/sample_campaign
  ```

### 4. 統合運用オーケストレーター ([04_orchestrator](04_orchestrator/README.md))
単体モジュール群を束ね、共通設定ファイル（`marketing_ops.yaml`）から新規立ち上げパイプライン（スライド+初期クリエイティブ一式）や、PDCA運用改善パイプライン（レポート+改善クリエイティブ再生成）を一気通貫で実行します。

- **統合CLIショートカット**:
  ```bash
  # 統合パイプラインの実行
  python 04_orchestrator/scripts/ops.py pipeline --mode launch --output-dir 04_orchestrator/outputs/sample_launch
  python 04_orchestrator/scripts/ops.py pipeline --mode pdca --output-dir 04_orchestrator/outputs/sample_pdca

  # 各モジュールの単体呼び出し
  python 04_orchestrator/scripts/ops.py proposal
  python 04_orchestrator/scripts/ops.py report
  python 04_orchestrator/scripts/ops.py creative
  ```

---

## 🧪 自動テストの実行

本プロジェクトではデグレ防止と品質保証のため、全モジュールにユニットテストおよびCLIエンドツーエンドテストを整備しています（**全34テスト完全合格**）。

```bash
# 全モジュールの自動テストを一括実行
pytest -v

# モジュール個別実行
pytest 01_proposal_generator/tests/ -v
pytest 02_report_automation/tests/ -v
pytest 03_creative_pipeline/tests/ -v
pytest 04_orchestrator/tests/ -v
```

---

## 🛡️ 開発・修正ワークフロー規約 (`.agents/`)

本リポジトリでの機能開発および修正作業は、以下の4ステップを必ず遵守して進められます。

1. **実装計画書の提示とユーザー事前承認**:
   - 実装前に「ゴール」「対象ファイル」「デグレ・リスク情報」「テスト方針」を提示し、ユーザーの「OK」承認を得てからコード変更に着手する。
2. **機能実装 & 自動テスト（デグレ検証）**:
   - 実装と並行してテストを作成し、全テスト合格を確認する。
3. **サブエージェントによる内部レビュー & ブラッシュアップ**:
   - レビュー担当サブエージェントを召喚し、堅牢性・セキュリティ・保守性の観点からコードを改善する。
4. **ウォークスルーの作成・報告**:
   - 検証ログ・成果物・手順をまとめたレポートを提出する。
