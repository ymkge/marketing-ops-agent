# 03. Creative Pipeline (クリエイティブ自動生成パイプラインモジュール)

広告クリエイティブ（広告見出し、説明文、SNS投稿文、バナー画像素材）の量産およびABテスト設計を自動化・高度化するパイプラインモジュールです。

商材ブリーフ（ターゲットペルソナ、特徴、ペイン、提供価値）を入力として、**訴求軸別の広告コピー（Google検索・Meta・X）**、**AI画像生成プロンプト**、**バナー画像（Pillow完全ローカル合成 / Google Imagen 3）**、**ABテスト比較用HTMLカタログ / CSV** をワンストップで生成します。

---

## 🚀 主な機能

1. **マルチチャネル広告コピー自動量産**:
   - **Google 検索広告 (RSA)**: 見出し（全角30文字以内 x 3）/ 説明文（全角90文字以内 x 2）
   - **Meta (FB/IG) 広告**: メインテキスト（200文字以内）/ 見出し（40文字以内）/ 説明文（50文字以内）/ 推奨CTA
   - **X (Twitter) 広告**: ポスト本文（140文字以内）/ カード見出し（40文字以内）/ CTA
   - 禁止キーワード（`forbidden_words`）の自動サニタイズ機能
2. **AI画像プロンプト最適化**:
   - Google Imagen 3 / Midjourney 等に向けた英語プロンプト、スタイル指定、ネガティブプロンプト、画像内キャッチコピーの自動抽出
3. **バナー画像生成（ハイブリッド対応）**:
   - **Pillow 完全ローカル合成**: 外部API不要・オフラインで動作。ブランドカラーに基づくグラデーション背景、カードデザイン、テキスト折り返し、バッジ、CTAボタンを自動描画。
   - **Google Imagen 3 API 連携**: `google-genai` SDK を通じた高品質画像素材の生成
   - 複数アスペクト比対応: `1:1` (1080x1080), `1.91:1` (1200x628), `9:16` (1080x1920)
4. **ABテスト比較用 HTML カタログ & CSV/JSON エクスポート**:
   - 各バリエーション（A/B/C...）の画像とコピーを横並びで比較・確認できるレスポンシブWebカタログ（CSS内蔵・自己完結型）
   - 広告管理画面やスプレッドシートへそのままインポート可能な UTF-8 BOM付き CSV エクスポート
5. **n8n ワークフロー連携**:
   - Webhook受信 → クリエイティブ生成 → Slack通知・レビューまでを自動化するワークフロー定義（`workflows/creative_generation_n8n.json`）を同梱

---

## 📁 ディレクトリ構成

```text
03_creative_pipeline/
├── README.md                      # 本ドキュメント
├── samples/
│   └── sample_creative_brief.json # テスト用入力ブリーフ（BtoB SaaS案件想定）
├── src/
│   ├── __init__.py
│   ├── models.py                  # Pydanticデータモデル (CreativeBrief, CreativeVariant等)
│   ├── copy_generator.py          # Gemini Structured Outputs & 動的モック生成
│   ├── image_generator.py         # Pillowバナー合成 & Imagen 3 APIクライアント
│   └── catalog_builder.py         # HTMLカタログ & CSV/JSONエクスポート
├── scripts/
│   └── generate_creatives.py      # CLI実行エントリーポイント
├── tests/
│   ├── __init__.py
│   └── test_creative_pipeline.py  # 自動テストスイート (単体・Pillow・CLI検証)
├── workflows/
│   └── creative_generation_n8n.json # n8n 連携ワークフロー定義
└── outputs/                       # 生成成果物保存先（画像, HTML, CSV, JSON）
```

---

## 🛠️ クイックスタート & 実行方法

### 1. 依存ライブラリの確認
```bash
pip install -r requirements.txt
```
（`Pillow>=10.0.0`, `pydantic>=2.10.0`, `google-genai>=1.0.0` が利用されます）

### 2. 環境変数の設定（任意）
Google AI Studio の Gemini API を利用する場合（未設定時は動的モックが自動適用されます）：
```bash
export GEMINI_API_KEY="your-gemini-api-key"
# モデル名を明示したい場合（未指定時は最新エイリアス: gemini-flash-latest）
export GEMINI_MODEL="gemini-flash-latest"
```

### 3. CLI からの実行

#### 基本実行（デフォルト: 3バリエーション、1:1 と 1.91:1 の画像を生成）
```bash
python 03_creative_pipeline/scripts/generate_creatives.py
```

#### 引数によるカスタム実行
```bash
python 03_creative_pipeline/scripts/generate_creatives.py \
  --input 03_creative_pipeline/samples/sample_creative_brief.json \
  --output-dir 03_creative_pipeline/outputs/campaign_202610 \
  --variants 3 \
  --aspect-ratios 1:1 1.91:1 9:16 \
  --provider auto \
  --format all
```

### 4. CLI 主要オプション一覧

| オプション | 短縮 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `--input` | `-i` | `samples/sample_creative_brief.json` | 入力ブリーフJSONファイルのパス |
| `--output-dir` | `-o` | `outputs/campaign_latest` | 成果物の出力先ディレクトリ |
| `--variants` | `-n` | `3` | 生成するABテストバリエーション数 |
| `--aspect-ratios` | `-a` | `1:1 1.91:1` | 生成する画像のアスペクト比 (`1:1`, `1.91:1`, `9:16`) |
| `--provider` | `-p` | `auto` | コピー生成プロバイダー (`auto`, `gemini`, `mock`) |
| `--model` | `-m` | `None` (環境変数または最新汎用エイリアス) | Geminiモデル名 (`gemini-flash-latest` 等) |
| `--use-imagen` | - | `False` | Google Imagen 3 APIによる画像生成を試行 |
| `--format` | `-f` | `all` | 出力形式 (`all`, `html`, `csv`, `json`) |

---

## 🧪 自動テストの実行

```bash
pytest 03_creative_pipeline/tests/ -v
```
Pydanticバリデーション、動的モック、Pillowバナー生成（1:1, 1.91:1, 9:16）、HTML/CSV/JSON出力、Geminiモック、503自動フェイルオーバー、CLI実行テストの全8件がパスします。
