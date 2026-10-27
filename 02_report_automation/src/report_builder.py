"""Report builder for generating Markdown and Standalone HTML reports."""

import html
import os
from pathlib import Path
from .models import MarketingReport, AggregatedData, InsightAnalysis


class ReportBuilder:
    """MarketingReportモデルからMarkdownおよびHTMLレポートを出力するビルダー"""

    def __init__(self, report: MarketingReport):
        self.report = report
        self.data = report.data
        self.insights = report.insights

    def build_markdown(self, output_path: str) -> str:
        """Markdown形式のレポートファイルを生成"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        content = self._render_markdown()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def build_html(self, output_path: str) -> str:
        """自己完結型（インラインCSS）HTMLレポートファイルを生成"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        content = self._render_html()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def _render_markdown(self) -> str:
        t = self.data.total
        lines = [
            f"# {self.report.report_title}",
            f"> 生成日時: {self.report.generated_at} | 集計期間: {self.data.period_start} 〜 {self.data.period_end}",
            "",
            "---",
            "",
            "## 1. エグゼクティブ・サマリー (AI総括)",
            self.insights.executive_summary,
            "",
            "---",
            "",
            "## 2. 全体KPIサマリー",
            "| 指標 | 実績値 | 指標 | 実績値 |",
            "| :--- | :--- | :--- | :--- |",
            f"| **総消化コスト** | ¥{t.cost:,.0f} | **総獲得数 (CV)** | {t.conversions:,.0f} 件 |",
            f"| **総インプレッション** | {t.impressions:,} 回 | **獲得単価 (CPA)** | ¥{t.cpa or 0:,.0f} |",
            f"| **総クリック数** | {t.clicks:,} 回 | **総売上金額** | ¥{t.revenue:,.0f} |",
            f"| **クリック率 (CTR)** | {t.ctr or 0:.2f}% | **費用対効果 (ROAS)** | {t.roas or 0:.1f}% |",
            f"| **クリック単価 (CPC)** | ¥{t.cpc or 0:,.0f} | **コンバージョン率 (CVR)** | {t.cvr or 0:.2f}% |",
            "",
            "---",
            "",
            "## 3. 媒体別パフォーマンス詳細",
            "| 媒体名 | 費用 (シェア) | CV数 (シェア) | CPA | CTR | CPC | CVR | ROAS |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for ch in self.data.by_channel:
            m = ch.metrics
            lines.append(
                f"| **{ch.channel}** | ¥{m.cost:,.0f} ({ch.cost_share:.1f}%) | {m.conversions:,.0f} ({ch.conversion_share:.1f}%) | "
                f"¥{m.cpa or 0:,.0f} | {m.ctr or 0:.2f}% | ¥{m.cpc or 0:,.0f} | {m.cvr or 0:.2f}% | {m.roas or 0:.1f}% |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 4. 媒体別要因分析 & 評価",
        ])

        for ev in self.insights.channel_evaluations:
            badge = "🟢 好調" if ev.status == "good" else ("🔴 要改善" if ev.status == "warning" else "⚪️ 順調")
            lines.extend([
                f"### {badge} {ev.channel}",
                f"- **評価・要因分析**: {ev.comment}",
                f"- **主因**: {ev.primary_driver}",
                ""
            ])

        lines.extend([
            "---",
            "",
            "## 5. 主要な発見・ボトルネック (Key Findings)",
        ])
        for finding in self.insights.key_findings:
            lines.append(f"- {finding}")

        lines.extend([
            "",
            "---",
            "",
            "## 6. 推奨改善アクション (Next Actions)",
            "| 優先度 | 対象媒体 | 施策タイトル | 施策概要 |",
            "| :---: | :--- | :--- | :--- |"
        ])
        for act in self.insights.action_items:
            p_badge = f"**[{act.priority}]**"
            lines.append(f"| {p_badge} | {act.target_channel} | {act.title} | {act.description} |")

        return "\n".join(lines) + "\n"

    def _render_html(self) -> str:
        t = self.data.total
        title = self.report.report_title

        channel_rows = ""
        for ch in self.data.by_channel:
            m = ch.metrics
            ch_name = html.escape(ch.channel)
            channel_rows += f"""
            <tr>
                <td><strong>{ch_name}</strong></td>
                <td>¥{m.cost:,.0f} <span class="share-pill">{ch.cost_share:.1f}%</span></td>
                <td>{m.conversions:,.0f} <span class="share-pill">{ch.conversion_share:.1f}%</span></td>
                <td class="highlight-val">¥{m.cpa or 0:,.0f}</td>
                <td>{m.ctr or 0:.2f}%</td>
                <td>¥{m.cpc or 0:,.0f}</td>
                <td>{m.cvr or 0:.2f}%</td>
                <td>{m.roas or 0:.1f}%</td>
            </tr>
            """

        eval_cards = ""
        for ev in self.insights.channel_evaluations:
            status_class = f"status-{ev.status}"
            status_label = "好調" if ev.status == "good" else ("要改善" if ev.status == "warning" else "順調")
            ch_name = html.escape(ev.channel)
            comment_text = html.escape(ev.comment)
            driver_text = html.escape(ev.primary_driver)
            eval_cards += f"""
            <div class="eval-card {status_class}">
                <div class="eval-header">
                    <h4>{ch_name}</h4>
                    <span class="badge {status_class}">{status_label}</span>
                </div>
                <p class="eval-comment">{comment_text}</p>
                <div class="eval-driver"><strong>主因:</strong> {driver_text}</div>
            </div>
            """

        findings_list = "".join(f"<li>{html.escape(f)}</li>" for f in self.insights.key_findings)

        action_rows = ""
        for act in self.insights.action_items:
            p_class = f"priority-{act.priority.lower()}"
            tgt_ch = html.escape(act.target_channel)
            act_title = html.escape(act.title)
            act_desc = html.escape(act.description)
            action_rows += f"""
            <tr>
                <td><span class="badge {p_class}">{act.priority}</span></td>
                <td><strong>{tgt_ch}</strong></td>
                <td><strong>{act_title}</strong></td>
                <td>{act_desc}</td>
            </tr>
            """

        # CSS横棒グラフ用バー
        share_bars = ""
        for ch in self.data.by_channel:
            ch_name = html.escape(ch.channel)
            share_bars += f"""
            <div class="bar-group">
                <div class="bar-label">{ch_name} ({ch.cost_share:.1f}%)</div>
                <div class="bar-track">
                    <div class="bar-fill" style="width: {ch.cost_share}%;"></div>
                </div>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
    :root {{
        --primary: #1e293b;
        --accent: #2563eb;
        --accent-light: #eff6ff;
        --bg-gray: #f8fafc;
        --border: #e2e8f0;
        --text: #334155;
        --text-muted: #64748b;
        --good: #10b981;
        --good-bg: #ecfdf5;
        --warning: #ef4444;
        --warning-bg: #fef2f2;
        --neutral: #3b82f6;
        --neutral-bg: #eff6ff;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        line-height: 1.6;
        color: var(--text);
        background: #f1f5f9;
        margin: 0;
        padding: 30px 15px;
    }}
    .container {{
        max-width: 1040px;
        margin: 0 auto;
        background: #ffffff;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    }}
    header {{
        border-bottom: 2px solid var(--border);
        padding-bottom: 20px;
        margin-bottom: 30px;
    }}
    h1 {{
        color: var(--primary);
        font-size: 26px;
        margin: 0 0 10px 0;
    }}
    .meta {{
        color: var(--text-muted);
        font-size: 13px;
    }}
    h2 {{
        color: var(--primary);
        font-size: 19px;
        border-left: 4px solid var(--accent);
        padding-left: 12px;
        margin: 35px 0 15px 0;
    }}
    .exec-summary {{
        background: var(--accent-light);
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 18px 22px;
        font-size: 15px;
        font-weight: 500;
        color: #1e3a8a;
    }}
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin-bottom: 25px;
    }}
    .kpi-card {{
        background: var(--bg-gray);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }}
    .kpi-title {{
        font-size: 12px;
        color: var(--text-muted);
        margin-bottom: 6px;
    }}
    .kpi-val {{
        font-size: 22px;
        font-weight: 700;
        color: var(--primary);
    }}
    .kpi-sub {{
        font-size: 12px;
        color: var(--accent);
        margin-top: 4px;
        font-weight: 600;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0 25px 0;
        font-size: 13.5px;
    }}
    th, td {{
        padding: 10px 14px;
        text-align: left;
        border-bottom: 1px solid var(--border);
    }}
    th {{
        background: var(--bg-gray);
        color: var(--primary);
        font-weight: 600;
    }}
    .highlight-val {{
        font-weight: 700;
        color: #0f172a;
    }}
    .share-pill {{
        display: inline-block;
        font-size: 11px;
        background: #e2e8f0;
        padding: 1px 6px;
        border-radius: 10px;
        color: #475569;
        margin-left: 4px;
    }}
    .eval-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 15px;
        margin: 15px 0;
    }}
    .eval-card {{
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 16px;
        background: #ffffff;
    }}
    .eval-card.status-good {{ border-left: 4px solid var(--good); }}
    .eval-card.status-warning {{ border-left: 4px solid var(--warning); }}
    .eval-card.status-neutral {{ border-left: 4px solid var(--neutral); }}
    .eval-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    .eval-header h4 {{ margin: 0; font-size: 16px; color: var(--primary); }}
    .badge {{
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }}
    .badge.status-good {{ background: var(--good-bg); color: var(--good); }}
    .badge.status-warning {{ background: var(--warning-bg); color: var(--warning); }}
    .badge.status-neutral {{ background: var(--neutral-bg); color: var(--neutral); }}
    .badge.priority-high {{ background: #fee2e2; color: #dc2626; }}
    .badge.priority-medium {{ background: #fef3c7; color: #d97706; }}
    .badge.priority-low {{ background: #e0e7ff; color: #4338ca; }}
    .eval-comment {{ font-size: 13.5px; margin: 0 0 10px 0; }}
    .eval-driver {{ font-size: 12px; color: var(--text-muted); background: var(--bg-gray); padding: 6px 10px; border-radius: 4px; }}
    .bar-group {{ margin-bottom: 10px; }}
    .bar-label {{ font-size: 12px; margin-bottom: 3px; font-weight: 600; }}
    .bar-track {{ height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: var(--accent); }}
    ul {{ padding-left: 20px; font-size: 14px; }}
    li {{ margin-bottom: 8px; }}
    @media print {{
        body {{ background: #ffffff; padding: 0; }}
        .container {{ box-shadow: none; padding: 0; max-width: 100%; }}
        .exec-summary {{ border: 1px solid #ccc; }}
    }}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>{title}</h1>
        <div class="meta">集計期間: {self.data.period_start} 〜 {self.data.period_end} ｜ レポート生成日時: {self.report.generated_at}</div>
    </header>

    <h2>1. エグゼクティブ・サマリー (AI総括)</h2>
    <div class="exec-summary">
        {self.insights.executive_summary}
    </div>

    <h2>2. 全体KPIサマリー</h2>
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-title">総消化コスト</div>
            <div class="kpi-val">¥{t.cost:,.0f}</div>
            <div class="kpi-sub">予算進捗: 順調</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">総獲得数 (CV)</div>
            <div class="kpi-val">{t.conversions:,.0f}</div>
            <div class="kpi-sub">CVR: {t.cvr or 0:.2f}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">平均CPA</div>
            <div class="kpi-val">¥{t.cpa or 0:,.0f}</div>
            <div class="kpi-sub">獲得単価</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">総売上 (ROAS)</div>
            <div class="kpi-val">¥{t.revenue:,.0f}</div>
            <div class="kpi-sub">ROAS: {t.roas or 0:.1f}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">総クリック (CTR)</div>
            <div class="kpi-val">{t.clicks:,}</div>
            <div class="kpi-sub">CTR: {t.ctr or 0:.2f}% | CPC: ¥{t.cpc or 0:,.0f}</div>
        </div>
    </div>

    <h2>3. 媒体別パフォーマンス詳細</h2>
    <div style="margin-bottom: 15px;">
        <div style="font-size: 13px; font-weight: 600; margin-bottom: 6px;">費用シェア内訳:</div>
        {share_bars}
    </div>
    <table>
        <thead>
            <tr>
                <th>媒体名</th>
                <th>費用 (シェア)</th>
                <th>CV数 (シェア)</th>
                <th>CPA</th>
                <th>CTR</th>
                <th>CPC</th>
                <th>CVR</th>
                <th>ROAS</th>
            </tr>
        </thead>
        <tbody>
            {channel_rows}
        </tbody>
    </table>

    <h2>4. 媒体別要因分析 & 評価</h2>
    <div class="eval-grid">
        {eval_cards}
    </div>

    <h2>5. 主要な発見・ボトルネック (Key Findings)</h2>
    <ul>
        {findings_list}
    </ul>

    <h2>6. 推奨改善アクション (Next Actions)</h2>
    <table>
        <thead>
            <tr>
                <th style="width: 80px;">優先度</th>
                <th style="width: 140px;">対象媒体</th>
                <th style="width: 220px;">施策タイトル</th>
                <th>施策概要</th>
            </tr>
        </thead>
        <tbody>
            {action_rows}
        </tbody>
    </table>
</div>
</body>
</html>
"""
