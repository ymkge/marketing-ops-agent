# 04. Marketing Ops Orchestrator (統合運用オーケストレーター)

マーケティング業務のライフサイクル（**新規提案・立ち上げ** ➔ **配信運用・レポーティング** ➔ **改善クリエイティブ再生成のPDCAループ**）を一元管理・自動実行するオーケストレーション基盤です。

これまで構築した3つの単体モジュール：
1. `01_proposal_generator`（提案スライド自動生成）
2. `02_report_automation`（広告レポート集計 & 考察文自動生成）
3. `03_creative_pipeline`（クリエイティブ量産 & バナー合成 & ABテストカタログ）

を1つの統合CLIコマンド（`ops.py`）から横断的に呼び出し、マーケティング運用の実務フローをシームレスに自動化します。

---

## 🚀 主な機能と連携シナリオ

### 1. 新規案件立ち上げパイプライン (`pipeline --mode launch`)
- 共通案件設定（`marketing_ops.yaml`）を1つ用意するだけで、
  - クライアント提案用 5枚構成 PowerPoint（`.pptx`）
  - 配信準備用広告コピー（Google/Meta/X）
  - バナー画像（1:1 正方形, 1.91:1 横長）
  - ABテスト比較用 HTML カタログ & CSV
  を一括同時生成します。

### 2. PDCA運用改善パイプライン (`pipeline --mode pdca`)
- 広告配信実績データ（CSV）を読み込み、
  1. 定例広告レポート（HTML / Markdown）の集計・要因分析
  2. レポート考察文からボトルネック要因（例: 「CTR低下」「クリエイティブ疲弊」）を自動抽出
  3. テコ入れ改善用の新規クリエイティブバリエーションを自動再生成
  を一気通貫で実行します。

### 3. 統合 CLI (`scripts/ops.py`) による一元管理
- 単一のエントリーポイントから個別モジュールの単体実行および全体パイプライン連携を自在に操作可能です。

### 4. n8n 統合ワークフロー定義
- Webhookトリガーから案件立ち上げおよびPDCA改善をSlack連携付きで自動実行するワークフロー定義（`workflows/full_marketing_cycle_n8n.json`）を同梱しています。

---

## 📁 ディレクトリ構成

```text
04_orchestrator/
├── README.md                      # 本ドキュメント
├── samples/
│   ├── sample_campaign_config.yaml # 統合案件設定ファイル（ブランド・KPI設定）
│   └── sample_brief.json          # 共通企画ブリーフ（JSON版）
├── src/
│   ├── __init__.py
│   ├── config.py                  # 設定ローダー & データモデル変換
│   ├── launcher_pipeline.py       # 新規立ち上げ一括連携（提案+クリエイティブ）
│   ├── pdca_pipeline.py           # PDCA改善一括連携（レポート+改善クリエイティブ）
│   └── cli.py                     # 統合CLIパーサー・ディスパッチャー
├── scripts/
│   └── ops.py                     # 統合CLIエントリーポイント
├── tests/
│   └── test_orchestrator.py       # 自動テストスイート（全4件）
└── workflows/
    └── full_marketing_cycle_n8n.json # 全体統合 n8n ワークフロー定義
```

---

## 🛠️ CLI 実行リファレンス

### 1. 新規案件立ち上げパイプラインの実行
```bash
python 04_orchestrator/scripts/ops.py pipeline \
  --mode launch \
  --config 04_orchestrator/samples/sample_campaign_config.yaml \
  --output-dir 04_orchestrator/outputs/campaign_launch \
  --provider auto
```
**生成される成果物**:
- `campaign_launch/[案件名]_proposal.pptx`: 提案書スライド
- `campaign_launch/creatives/creative_catalog.html`: クリエイティブHTMLカタログ
- `campaign_launch/creatives/creative_copies.csv`: 広告コピーCSV
- `campaign_launch/creatives/*.png`: バナー画像素材
- `campaign_launch/launch_summary.json`: 立ち上げサマリーメタデータ

---

### 2. PDCA運用改善パイプラインの実行
```bash
python 04_orchestrator/scripts/ops.py pipeline \
  --mode pdca \
  --config 04_orchestrator/samples/sample_campaign_config.yaml \
  --data 02_report_automation/samples/sample_ad_performance.csv \
  --output-dir 04_orchestrator/outputs/campaign_pdca \
  --provider auto
```
**生成される成果物**:
- `campaign_pdca/performance_report.html`: 広告配信レポート（HTML）
- `campaign_pdca/performance_report.md`: 広告配信レポート（Markdown）
- `campaign_pdca/remedial_creatives/creative_catalog.html`: 課題テコ入れ改善用クリエイティブカタログ
- `campaign_pdca/remedial_creatives/*.png`: 改善バナー画像
- `campaign_pdca/pdca_summary.json`: PDCAサマリーメタデータ

---

### 3. 個別モジュールの単体呼び出し（ショートカット）

```bash
# 提案スライド単体生成
python 04_orchestrator/scripts/ops.py proposal --input 01_proposal_generator/samples/sample_brief.json

# レポート単体生成
python 04_orchestrator/scripts/ops.py report --input 02_report_automation/samples/sample_ad_performance.csv

# クリエイティブ単体生成
python 04_orchestrator/scripts/ops.py creative --input 03_creative_pipeline/samples/sample_creative_brief.json
```

---

## 🧪 自動テストの実行

```bash
pytest 04_orchestrator/tests/ -v
```
設定ローダー、Launchパイプライン、PDCAパイプライン、CLI E2Eサブプロセス実行の全4テストがパスします。
