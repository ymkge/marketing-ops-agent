"""Unit and integration tests for 02_report_automation module."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# 02_report_automation を sys.path に追加し、モジュールキャッシュ衝突を防止
module_dir = Path(__file__).resolve().parent.parent
if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

# 他モジュールとの 'src' キャッシュ衝突をリセット
for mod in list(sys.modules.keys()):
    if mod == "src" or mod.startswith("src."):
        del sys.modules[mod]

from src.data_processor import DataProcessor, calculate_metrics, _safe_div
from src.insight_analyzer import generate_mock_insights, generate_insights, generate_insights_with_gemini, resolve_model
from src.models import AggregatedData, MarketingReport, InsightAnalysis
from src.report_builder import ReportBuilder


@pytest.fixture
def sample_csv_path():
    """テスト用サンプルCSVパス"""
    return module_dir / "samples" / "sample_ad_performance.csv"


def test_safe_div_calculations():
    """安全な除算ユーティリティの検証（ゼロ除算・NaN・Inf対策）"""
    assert _safe_div(100, 20) == 5.0
    assert _safe_div(1, 3, multiplier=100.0) == 33.33
    assert _safe_div(100, 0) is None
    assert _safe_div(None, 10) is None
    assert _safe_div(10, None) is None


def test_calculate_metrics_weighted_average():
    """KPI集計ロジックの検証（合算後除算の加重平均を担保）"""
    # cost=100,000, imp=10,000, clicks=500, cv=25, rev=300,000
    m = calculate_metrics(cost=100000, imp=10000, clicks=500, cv=25, rev=300000)
    assert m.cost == 100000.0
    assert m.impressions == 10000
    assert m.clicks == 500
    assert m.conversions == 25.0
    assert m.revenue == 300000.0
    assert m.ctr == 5.0        # (500 / 10,000) * 100
    assert m.cpc == 200.0      # 100,000 / 500
    assert m.cvr == 5.0        # (25 / 500) * 100
    assert m.cpa == 4000.0     # 100,000 / 25
    assert m.roas == 300.0     # (300,000 / 100,000) * 100


def test_data_processor_with_sample_csv(sample_csv_path):
    """サンプルCSVを用いたデータ集計の総合検証"""
    processor = DataProcessor(sample_csv_path)
    data = processor.process()

    assert isinstance(data, AggregatedData)
    assert data.period_start == "2026-10-01"
    assert data.period_end == "2026-10-07"
    assert data.total.cost > 0
    assert data.total.conversions > 0
    assert data.total.cpa is not None
    assert len(data.by_channel) == 2  # Google Ads, Meta Ads
    assert len(data.daily_trends) == 7

    # 媒体別シェアの合計が約100%になること
    total_cost_share = sum(ch.cost_share for ch in data.by_channel)
    assert abs(total_cost_share - 100.0) < 0.1


def test_edge_case_zero_conversions_and_clicks():
    """clicks=0 や conversions=0 の行を含むエッジケースでもゼロ除算なく処理できること"""
    df_edge = pd.DataFrame([
        {"date": "2026-10-01", "channel": "TestCh", "campaign_name": "Camp1", "impressions": 100, "clicks": 0, "cost": 1000, "conversions": 0, "revenue": 0},
        {"date": "2026-10-02", "channel": "TestCh", "campaign_name": "Camp1", "impressions": 0, "clicks": 0, "cost": 0, "conversions": 0, "revenue": 0}
    ])
    processor = DataProcessor(df_edge)
    data = processor.process()

    assert data.total.clicks == 0
    assert data.total.conversions == 0
    assert data.total.cpa is None
    assert data.total.cpc is None
    assert data.total.cvr is None
    assert data.total.ctr == 0.0 or data.total.ctr is None


def test_single_channel_dataset():
    """単一媒体のみのデータセットでも正常に動作すること"""
    df_single = pd.DataFrame([
        {"date": "2026-10-01", "channel": "Google Ads", "campaign_name": "C1", "impressions": 500, "clicks": 50, "cost": 10000, "conversions": 5, "revenue": 20000}
    ])
    processor = DataProcessor(df_single)
    data = processor.process()

    assert len(data.by_channel) == 1
    assert data.by_channel[0].channel == "Google Ads"
    assert data.by_channel[0].cost_share == 100.0


def test_missing_required_columns():
    """必須カラム欠落時に ValueError が発生すること"""
    df_invalid = pd.DataFrame([{"date": "2026-10-01", "clicks": 10}])
    with pytest.raises(ValueError, match="必須カラムが不足"):
        DataProcessor(df_invalid)


def test_empty_file_handling():
    """空ファイル指定時に ValueError が発生すること"""
    with tempfile.NamedTemporaryFile(suffix=".csv") as f:
        with pytest.raises(ValueError, match="データファイルが空"):
            DataProcessor(f.name)


def test_dynamic_mock_insights(sample_csv_path):
    """実集計データと連動した動的モックインサイトの検証"""
    processor = DataProcessor(sample_csv_path)
    data = processor.process()
    insights = generate_mock_insights(data)

    assert isinstance(insights, InsightAnalysis)
    assert len(insights.channel_evaluations) == len(data.by_channel)
    assert len(insights.key_findings) >= 3
    assert len(insights.action_items) >= 2
    assert "当期間" in insights.executive_summary


def test_gemini_client_with_mocked_api(sample_csv_path, monkeypatch):
    """Gemini API をモックして InsightAnalysis が生成されることを検証"""
    from unittest.mock import MagicMock

    monkeypatch.setenv("GEMINI_API_KEY", "dummy_gemini_key")

    processor = DataProcessor(sample_csv_path)
    data = processor.process()
    mock_insights = generate_mock_insights(data)

    mock_response = MagicMock()
    mock_response.text = mock_insights.model_dump_json()

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    monkeypatch.setattr("google.genai.Client", lambda api_key: mock_client)

    result_insights = generate_insights_with_gemini(data)
    assert isinstance(result_insights, InsightAnalysis)
    assert len(result_insights.channel_evaluations) == len(data.by_channel)


def test_report_builder_markdown_and_html(sample_csv_path):
    """Markdown および 自己完結型 HTML レポートが正しく生成されることを検証"""
    processor = DataProcessor(sample_csv_path)
    data = processor.process()
    insights = generate_mock_insights(data)

    report = MarketingReport(
        report_title="テスト週次マーケティングレポート",
        generated_at="2026年10月27日 12:00",
        data=data,
        insights=insights
    )
    builder = ReportBuilder(report)

    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = os.path.join(tmpdir, "test_report.md")
        html_file = os.path.join(tmpdir, "test_report.html")

        builder.build_markdown(md_file)
        builder.build_html(html_file)

        assert os.path.exists(md_file)
        assert os.path.exists(html_file)

        # Markdown 検証
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()
        assert "# テスト週次マーケティングレポート" in md_content
        assert "Google Ads" in md_content
        assert "Meta Ads" in md_content
        assert "推奨改善アクション" in md_content

        # HTML 検証
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        assert "<!DOCTYPE html>" in html_content
        assert "kpi-card" in html_content
        assert "Google Ads" in html_content


def test_cli_execution_with_mock(sample_csv_path):
    """generate_report.py の CLI 実行テスト (E2E)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_base = os.path.join(tmpdir, "e2e_report")
        cmd = [
            sys.executable,
            str(module_dir / "scripts" / "generate_report.py"),
            "--input", str(sample_csv_path),
            "--output", out_base,
            "--format", "both",
            "--provider", "mock"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"CLI error: {result.stderr}"
        assert os.path.exists(f"{out_base}.md")
        assert os.path.exists(f"{out_base}.html")
        assert os.path.getsize(f"{out_base}.html") > 0


def test_resolve_model_empty_env(monkeypatch):
    """環境変数が空文字の場合でもデフォルト値が採用されることを検証"""
    monkeypatch.setenv("GEMINI_MODEL", "")
    assert resolve_model(None) == "gemini-flash-latest"
    monkeypatch.setenv("GEMINI_MODEL", "custom-model")
    assert resolve_model(None) == "custom-model"
    assert resolve_model("override-model") == "override-model"


def test_gemini_503_failover(monkeypatch, sample_csv_path):
    """Gemini APIで503高負荷が発生した際に、代替モデルへ自動フェイルオーバーすることを検証"""
    processor = DataProcessor(sample_csv_path)
    agg_data = processor.process()

    class FakeClient:
        def __init__(self):
            self.models = self
            self.calls = []

        def generate_content(self, model, contents, config):
            self.calls.append(model)
            if model == "gemini-flash-latest":
                raise Exception("503 UNAVAILABLE: Model is experiencing high demand")
            
            # 2回目の試行で成功するフェイクレスポンス
            class FakeResponse:
                text = json.dumps({
                    "executive_summary": "フェイルオーバー後のサマリー",
                    "channel_evaluations": [],
                    "key_findings": ["Finding 1"],
                    "action_items": []
                })
            return FakeResponse()

    fake_client = FakeClient()

    class FakeGenAIModule:
        Client = lambda **kwargs: fake_client
        types = type("types", (), {
            "GenerateContentConfig": lambda **kwargs: kwargs
        })

    monkeypatch.setattr("src.insight_analyzer.resolve_model", lambda m: "gemini-flash-latest")
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.setitem(sys.modules, "google", type("google", (), {}))
    monkeypatch.setitem(sys.modules, "google.genai", FakeGenAIModule)
    monkeypatch.setitem(sys.modules, "google.genai.types", FakeGenAIModule.types)

    insights = generate_insights_with_gemini(agg_data, model_name=None)
    assert insights.executive_summary == "フェイルオーバー後のサマリー"
    assert fake_client.calls == ["gemini-flash-latest", "gemini-flash-lite-latest"]
