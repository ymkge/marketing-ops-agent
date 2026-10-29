"""HTML catalog and CSV/JSON exporter for creative AB testing variants."""

import csv
import html
import json
import logging
from pathlib import Path
from typing import List, Optional

from .models import CreativeBatchResult, CreativeVariant

logger = logging.getLogger(__name__)


def _safe_csv_val(val: Optional[str]) -> str:
    """CSV Formula Injection (数式インジェクション) 対策"""
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


class CatalogBuilder:
    """クリエイティブバリエーションのHTMLカタログおよびCSV/JSON出力ビルダー"""

    def __init__(self, batch_result: CreativeBatchResult):
        self.result = batch_result
        self.brief = batch_result.brief
        self.variants = batch_result.variants

    def build_html(self, output_path: Path) -> str:
        """自己完結型 HTML カタログ（プレビュー・コピー一覧）を生成"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        p_name = html.escape(self.brief.product_name)
        cat_name = html.escape(self.brief.category)
        target = html.escape(self.brief.target_audience)
        created_at = html.escape(self.result.created_at)

        variants_html = ""
        for v in self.variants:
            v_id = html.escape(v.variant_id)
            approach = html.escape(v.approach_name)
            focus = html.escape(v.target_persona_focus)
            hypothesis = html.escape(v.hypothesis_reason)

            # 画像プレビューカード
            images_html = ""
            for img in v.generated_images:
                rel_path = Path(img.file_path).name  # HTMLと同じディレクトリまたは相対パス
                ar_label = html.escape(img.aspect_ratio)
                gen_type = html.escape(img.generator_type)
                images_html += f"""
                <div class="image-card">
                    <div class="image-header">
                        <span class="badge badge-ar">{ar_label}</span>
                        <span class="badge badge-tech">{gen_type}</span>
                        <span class="dims">{img.width}x{img.height}</span>
                    </div>
                    <div class="img-wrapper">
                        <img src="{html.escape(rel_path)}" alt="{approach} - {ar_label}" loading="lazy">
                    </div>
                    <div class="image-footer">
                        <a href="{html.escape(rel_path)}" download class="btn-download">画像をダウンロード</a>
                    </div>
                </div>
                """

            # コピー一覧 (Google, Meta, X)
            g = v.google_search
            m = v.meta
            x = v.x_twitter
            ip = v.image_prompt

            variants_html += f"""
            <section class="variant-section" id="{v_id}">
                <div class="variant-header">
                    <div class="variant-title-group">
                        <span class="variant-badge">{v_id}</span>
                        <h2>{approach}</h2>
                    </div>
                    <div class="variant-focus">
                        <strong>ターゲット焦点:</strong> {focus}
                    </div>
                </div>

                <div class="hypothesis-box">
                    <strong>💡 ABテスト仮説・狙い:</strong>
                    <p>{hypothesis}</p>
                </div>

                <div class="variant-grid">
                    <!-- 左カラム: バナー画像ギャラリー -->
                    <div class="column-visuals">
                        <h3>🎨 バナー画像ビジュアル</h3>
                        <div class="images-container">
                            {images_html}
                        </div>
                        <div class="prompt-box">
                            <h4>🤖 生成プロンプト (ImagePrompt)</h4>
                            <div class="prompt-item">
                                <span class="label">キャッチコピー:</span>
                                <code>{html.escape(ip.banner_catchphrase)}</code>
                            </div>
                            {f'<div class="prompt-item"><span class="label">サブコピー:</span> <code>{html.escape(ip.banner_subphrase)}</code></div>' if ip.banner_subphrase else ''}
                            <div class="prompt-item">
                                <span class="label">英語プロンプト (AI用):</span>
                                <pre>{html.escape(ip.prompt_en)}</pre>
                            </div>
                        </div>
                    </div>

                    <!-- 右カラム: チャネル別コピー -->
                    <div class="column-copies">
                        <h3>✍️ 広告配信用コピー</h3>

                        <!-- Google 検索広告 -->
                        <div class="copy-channel-card">
                            <div class="channel-title">
                                <span class="ch-badge ch-google">Google 検索広告</span>
                                <span class="ch-info">レスポンシブ検索広告 (RSA) 形式</span>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">見出し 1 ({len(g.headline_1)}/30字):</span>
                                <div class="copy-text">{html.escape(g.headline_1)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">見出し 2 ({len(g.headline_2)}/30字):</span>
                                <div class="copy-text">{html.escape(g.headline_2)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">見出し 3 ({len(g.headline_3)}/30字):</span>
                                <div class="copy-text">{html.escape(g.headline_3)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">説明文 1 ({len(g.description_1)}/90字):</span>
                                <div class="copy-text">{html.escape(g.description_1)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">説明文 2 ({len(g.description_2)}/90字):</span>
                                <div class="copy-text">{html.escape(g.description_2)}</div>
                            </div>
                        </div>

                        <!-- Meta 広告 -->
                        <div class="copy-channel-card">
                            <div class="channel-title">
                                <span class="ch-badge ch-meta">Meta (Facebook / Instagram) 広告</span>
                                <span class="ch-info">フィード・ストーリーズ推奨</span>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">メインテキスト ({len(m.primary_text)}/200字):</span>
                                <div class="copy-text pre-wrap">{html.escape(m.primary_text)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">見出し ({len(m.headline)}/40字):</span>
                                <div class="copy-text">{html.escape(m.headline)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">説明文 ({len(m.description)}/50字):</span>
                                <div class="copy-text">{html.escape(m.description)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">推奨CTAボタン:</span>
                                <span class="cta-pill">{html.escape(m.cta_type)}</span>
                            </div>
                        </div>

                        <!-- X 広告 -->
                        <div class="copy-channel-card">
                            <div class="channel-title">
                                <span class="ch-badge ch-x">X (Twitter) 広告</span>
                                <span class="ch-info">プロモポスト / カード</span>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">ポスト本文 ({len(x.post_text)}/140字):</span>
                                <div class="copy-text pre-wrap">{html.escape(x.post_text)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">カード見出し ({len(x.card_headline)}/40字):</span>
                                <div class="copy-text">{html.escape(x.card_headline)}</div>
                            </div>
                            <div class="copy-field">
                                <span class="copy-label">カードCTA:</span>
                                <span class="cta-pill">{html.escape(x.cta_type)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{p_name} - クリエイティブABテストカタログ</title>
    <style>
        :root {{
            --primary: #2563EB;
            --secondary: #1E40AF;
            --accent: #F59E0B;
            --bg-page: #F8FAFC;
            --bg-card: #FFFFFF;
            --text-main: #0F172A;
            --text-muted: #64748B;
            --border: #E2E8F0;
            --radius-lg: 16px;
            --radius-md: 10px;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Hiragino Sans", sans-serif;
            background-color: var(--bg-page);
            color: var(--text-main);
            line-height: 1.6;
            padding: 24px;
        }}
        .container {{ max-width: 1280px; margin: 0 auto; }}
        
        /* ヘッダー */
        header.header {{
            background: linear-gradient(135deg, #1E293B, #0F172A);
            color: #FFFFFF;
            padding: 36px 32px;
            border-radius: var(--radius-lg);
            margin-bottom: 32px;
            box-shadow: var(--shadow-lg);
        }}
        header h1 {{ font-size: 28px; margin-bottom: 8px; letter-spacing: -0.5px; }}
        header .meta-info {{
            display: flex; flex-wrap: wrap; gap: 16px; font-size: 14px; color: #CBD5E1; margin-top: 12px;
        }}
        header .meta-item {{ display: flex; align-items: center; gap: 6px; }}

        /* バリアントセクション */
        .variant-section {{
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            padding: 32px;
            margin-bottom: 36px;
        }}
        .variant-header {{
            display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;
            padding-bottom: 20px; border-bottom: 2px solid var(--border); margin-bottom: 20px;
        }}
        .variant-title-group {{ display: flex; align-items: center; gap: 12px; }}
        .variant-badge {{
            background: var(--primary); color: #fff; font-weight: 700; font-size: 16px;
            padding: 6px 14px; border-radius: 20px; letter-spacing: 0.5px;
        }}
        .variant-header h2 {{ font-size: 22px; font-weight: 700; color: var(--text-main); }}
        .variant-focus {{ font-size: 14px; color: var(--text-muted); background: #F1F5F9; padding: 6px 14px; border-radius: 8px; }}

        .hypothesis-box {{
            background: #EFF6FF; border-left: 4px solid var(--primary);
            padding: 16px 20px; border-radius: 0 8px 8px 0; margin-bottom: 24px; font-size: 14px; color: #1E3A8A;
        }}
        .hypothesis-box strong {{ display: block; margin-bottom: 4px; }}

        /* 2カラムレイアウト */
        .variant-grid {{
            display: grid; grid-template-columns: 1fr 1fr; gap: 32px;
        }}
        @media (max-width: 960px) {{
            .variant-grid {{ grid-template-columns: 1fr; }}
        }}

        /* 画像ギャラリー */
        .column-visuals h3, .column-copies h3 {{
            font-size: 18px; margin-bottom: 16px; color: var(--text-main); display: flex; align-items: center; gap: 8px;
        }}
        .images-container {{
            display: flex; flex-direction: column; gap: 20px; margin-bottom: 24px;
        }}
        .image-card {{
            background: #F8FAFC; border: 1px solid var(--border); border-radius: var(--radius-md); overflow: hidden;
        }}
        .image-header {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 14px; background: #FFFFFF; border-bottom: 1px solid var(--border); font-size: 12px;
        }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }}
        .badge-ar {{ background: #E0E7FF; color: #3730A3; }}
        .badge-tech {{ background: #FEF3C7; color: #92400E; }}
        .dims {{ color: var(--text-muted); }}
        .img-wrapper {{ width: 100%; text-align: center; background: #0F172A; }}
        .img-wrapper img {{
            max-width: 100%; height: auto; display: block; margin: 0 auto;
        }}
        .image-footer {{ padding: 8px 14px; text-align: right; background: #FFF; }}
        .btn-download {{
            font-size: 12px; color: var(--primary); text-decoration: none; font-weight: 600;
        }}
        .btn-download:hover {{ text-decoration: underline; }}

        /* プロンプトボックス */
        .prompt-box {{
            background: #F8FAFC; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 16px; font-size: 13px;
        }}
        .prompt-box h4 {{ font-size: 14px; margin-bottom: 10px; color: var(--text-main); }}
        .prompt-item {{ margin-bottom: 8px; }}
        .prompt-item .label {{ font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 2px; }}
        .prompt-item code {{ background: #FFF; border: 1px solid var(--border); padding: 3px 6px; border-radius: 4px; display: inline-block; }}
        .prompt-item pre {{
            background: #1E293B; color: #F8FAFC; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 12px; line-height: 1.4;
        }}

        /* コピーカード */
        .copy-channel-card {{
            background: #FFFFFF; border: 1px solid var(--border); border-radius: var(--radius-md);
            padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }}
        .channel-title {{
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #F1F5F9;
        }}
        .ch-badge {{
            padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px;
        }}
        .ch-google {{ background: #E8F0FE; color: #1A73E8; }}
        .ch-meta {{ background: #E7F3FF; color: #1877F2; }}
        .ch-x {{ background: #F3F4F6; color: #111827; }}
        .ch-info {{ font-size: 12px; color: var(--text-muted); }}

        .copy-field {{ margin-bottom: 12px; }}
        .copy-field:last-child {{ margin-bottom: 0; }}
        .copy-label {{ font-size: 12px; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 4px; }}
        .copy-text {{
            background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px 12px; border-radius: 6px; font-size: 14px; color: var(--text-main);
        }}
        .pre-wrap {{ white-space: pre-wrap; }}
        .cta-pill {{
            background: #FEF3C7; color: #92400E; font-weight: 700; font-size: 13px; padding: 4px 12px; border-radius: 14px; display: inline-block;
        }}

        footer {{ text-align: center; color: var(--text-muted); font-size: 13px; margin-top: 40px; padding: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>{p_name} 広告クリエイティブ ABテストカタログ</h1>
            <p>カテゴリ: {cat_name} | ターゲット: {target}</p>
            <div class="meta-info">
                <span class="meta-item">📅 生成日時: {created_at}</span>
                <span class="meta-item">🧪 バリエーション数: {len(self.variants)} パターン</span>
                <span class="meta-item">🖼️ 生成画像数: {self.result.total_images} 枚</span>
            </div>
        </header>

        {variants_html}

        <footer>
            Generated by Marketing Ops Agent (03_creative_pipeline) &bull; Confidential &copy; 2026
        </footer>
    </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("HTML カタログを出力しました: %s", output_path)
        return html_content

    def export_csv(self, output_path: Path):
        """広告運用管理用のCSVファイルを出力"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        for v in self.variants:
            # Google
            rows.append({
                "variant_id": _safe_csv_val(v.variant_id),
                "approach": _safe_csv_val(v.approach_name),
                "channel": "Google Search",
                "headline_1": _safe_csv_val(v.google_search.headline_1),
                "headline_2": _safe_csv_val(v.google_search.headline_2),
                "headline_3": _safe_csv_val(v.google_search.headline_3),
                "description_1": _safe_csv_val(v.google_search.description_1),
                "description_2": _safe_csv_val(v.google_search.description_2),
                "cta": "-",
                "image_catchphrase": _safe_csv_val(v.image_prompt.banner_catchphrase),
                "hypothesis": _safe_csv_val(v.hypothesis_reason)
            })
            # Meta
            rows.append({
                "variant_id": _safe_csv_val(v.variant_id),
                "approach": _safe_csv_val(v.approach_name),
                "channel": "Meta (FB/IG)",
                "headline_1": _safe_csv_val(v.meta.headline),
                "headline_2": "-",
                "headline_3": "-",
                "description_1": _safe_csv_val(v.meta.primary_text),
                "description_2": _safe_csv_val(v.meta.description),
                "cta": _safe_csv_val(v.meta.cta_type),
                "image_catchphrase": _safe_csv_val(v.image_prompt.banner_catchphrase),
                "hypothesis": _safe_csv_val(v.hypothesis_reason)
            })
            # X
            rows.append({
                "variant_id": _safe_csv_val(v.variant_id),
                "approach": _safe_csv_val(v.approach_name),
                "channel": "X (Twitter)",
                "headline_1": _safe_csv_val(v.x_twitter.card_headline),
                "headline_2": "-",
                "headline_3": "-",
                "description_1": _safe_csv_val(v.x_twitter.post_text),
                "description_2": "-",
                "cta": _safe_csv_val(v.x_twitter.cta_type),
                "image_catchphrase": _safe_csv_val(v.image_prompt.banner_catchphrase),
                "hypothesis": _safe_csv_val(v.hypothesis_reason)
            })

        fieldnames = [
            "variant_id", "approach", "channel", "headline_1", "headline_2", "headline_3",
            "description_1", "description_2", "cta", "image_catchphrase", "hypothesis"
        ]

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info("CSV エクスポート完了: %s", output_path)

    def export_json(self, output_path: Path):
        """全体のJSONファイルを出力"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.result.model_dump_json(indent=2))
        logger.info("JSON エクスポート完了: %s", output_path)
