# 02. Report Automation (レポート自動化モジュール)

## 概要
広告媒体（Google広告、Meta広告等）やWebアナリティクスの実績データ（CSV/JSON）を集計・クレンジングし、Google AI Studio（Gemini API）の Structured Outputs を用いて、要因分析・考察・改善アクション付きの定例マーケティングレポート（Markdown / 自己完結型HTML）を自動出力するモジュールです。

## 主な機能
- **高精度なデータ集計・クレンジング (`DataProcessor`)**:
  - `pandas` による加重平均KPI計算（CTR, CPC, CVR, CPA, ROAS）
  - ゼロ除算・欠損値（NaN, Inf）の自動安全化（`None` / `"-"` への正規化）
  - 全体サマリー、媒体別シェア、日別トレンドの3層集計
- **LLMによる自動インサイト考察 (`InsightAnalyzer`)**:
  - Google GenAI SDK（Gemini 3.8 Flash）によるネイティブ Structured Outputs
  - 集計済みサマリーテーブルのみをコンテキストに投入し、トークン削減とハルシネーション（計算ミス）を完全排除
  - APIキー未設定時・オフライン時も、実データ数値に完全連動した動的モック分析へ自動フォールバック
- **マルチフォーマット出力 (`ReportBuilder`)**:
  - **Markdown形式**: GitHub、Notion、Slack 等へそのまま貼り付け可能
  - **自己完結型 HTML形式**: インラインCSS設計、KPIサマリーカード、CSS横棒グラフ、印刷/PDF保存対応

## ディレクトリ構成
```text
02_report_automation/
├── README.md                      # 本ドキュメント
├── samples/
│   └── sample_ad_performance.csv  # 複数媒体（Google/Meta）の配信実績サンプルデータ
├── src/
│   ├── __init__.py
│   ├── models.py                  # Pydanticデータモデル (RawAdRecord, AggregatedData, InsightAnalysis等)
│   ├── data_processor.py          # pandasによるデータ集計・加重平均KPI計算・ゼロ除算ガード
│   ├── insight_analyzer.py        # Gemini API による要因分析・改善インサイト生成
│   └── report_builder.py          # Markdown & 自己完結型HTMLレポート生成ビルダー
├── scripts/
│   └── generate_report.py         # CLI実行スクリプト
├── tests/
│   └── test_report_automation.py  # 自動テストスイート (Pytest 11件)
└── outputs/                       # 生成されたレポート成果物 (.md / .html)
```

## 使い方・実行方法

### 1. 依存パッケージの準備
ルートディレクトリの `requirements.txt` に含まれるパッケージをインストールします。
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定 (任意)
Google AI Studio の無料APIキーを設定してください。
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```
※ APIキーが設定されていない場合でも、自動的に動的モック生成モードへフォールバックして動作確認が可能です。

### 3. レポート生成コマンドの実行

#### 基本実行（Markdown & HTML の両方を出力）
```bash
# 02_report_automation ディレクトリ配下から実行
python scripts/generate_report.py --input samples/sample_ad_performance.csv --output outputs/weekly_report

# またはリポジトリルートから実行
python 02_report_automation/scripts/generate_report.py \
  --input 02_report_automation/samples/sample_ad_performance.csv \
  --output 02_report_automation/outputs/weekly_report
```

#### Gemini API を明示指定して実行
```bash
python 02_report_automation/scripts/generate_report.py \
  --input 02_report_automation/samples/sample_ad_performance.csv \
  --output 02_report_automation/outputs/weekly_report \
  --provider gemini \
  --model gemini-flash-latest
```

#### CLI オプション一覧
| オプション | 短縮 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `--input` | `-i` | `samples/sample_ad_performance.csv` | 入力実績データファイル (CSVまたはJSON) |
| `--output` | `-o` | `outputs/weekly_report` | 出力ファイルパス（ベース名） |
| `--format` | `-f` | `both` | 出力形式 (`markdown`, `html`, `both`) |
| `--provider`| `-p` | `auto` | LLMプロバイダー (`auto`, `gemini`, `mock`) |
| `--model` | `-m` | `gemini-flash-latest` | Gemini モデル名（未指定時は環境変数 GEMINI_MODEL または gemini-flash-latest） |
| `--title` | `-t` | `週次マーケティング広告成果分析レポート` | レポートタイトル |
