"""Unit and integration tests for 04_orchestrator module."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

# 04_orchestrator を sys.path に追加
module_dir = Path(__file__).resolve().parent.parent
repo_root = module_dir.parent

if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# 他モジュールとの 'src' キャッシュ衝突をリセット
for mod in list(sys.modules.keys()):
    if mod == "src" or mod.startswith("src."):
        del sys.modules[mod]

from src.config import CampaignConfig, load_campaign_config
from src.launcher_pipeline import run_launcher_pipeline
from src.pdca_pipeline import run_pdca_pipeline


@pytest.fixture
def sample_config_yaml():
    return module_dir / "samples" / "sample_campaign_config.yaml"


@pytest.fixture
def sample_brief_json():
    return module_dir / "samples" / "sample_brief.json"


@pytest.fixture
def sample_performance_csv():
    return repo_root / "02_report_automation" / "samples" / "sample_ad_performance.csv"


def test_config_loader(sample_config_yaml, sample_brief_json):
    """YAMLおよびJSON設定ファイルのロードとデータモデル変換の検証"""
    # 1. YAMLロード
    cfg_yaml = load_campaign_config(sample_config_yaml)
    assert cfg_yaml.campaign_name == "CloudOps AI キャンペーン"
    assert cfg_yaml.client_name == "株式会社クラウドネクスト"
    assert cfg_yaml.brand_colors.primary == "#2563EB"

    # 変換メソッド
    brief_dict = cfg_yaml.to_brief_input_dict()
    assert brief_dict["client_name"] == "株式会社クラウドネクスト"
    assert "CloudOps AI" in brief_dict["project_name"]

    creative_dict = cfg_yaml.to_creative_brief_dict()
    assert creative_dict["product_name"] == "CloudOps AI"
    assert creative_dict["brand_colors"]["primary"] == "#2563EB"

    # 2. JSONロード
    cfg_json = load_campaign_config(sample_brief_json)
    assert cfg_json.campaign_name == "CloudOps AI キャンペーン"

    # 3. 不正HEXカラーのフォールバック
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write("campaign_name: 'Test'\nbrand_colors:\n  primary: 'invalid-hex'\n")
        tmp_name = f.name
    try:
        cfg_invalid = load_campaign_config(tmp_name)
        assert cfg_invalid.brand_colors.primary == "#2563EB"
    finally:
        os.remove(tmp_name)


def test_launcher_pipeline(sample_config_yaml):
    """新規立ち上げパイプラインの統合実行検証 (Proposal + Creatives)"""
    config = load_campaign_config(sample_config_yaml)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "launch_test"

        result = run_launcher_pipeline(
            config=config,
            output_dir=out_dir,
            provider="mock",
            variants_count=2,
            aspect_ratios=["1:1"]
        )

        assert result["campaign_name"] == config.campaign_name
        # 提案スライドPPTXの存在
        pptx_path = Path(result["outputs"]["proposal_pptx"])
        assert pptx_path.exists()
        assert pptx_path.stat().st_size > 0

        # クリエイティブ成果物の存在
        creatives_dir = Path(result["outputs"]["creatives_dir"])
        assert (creatives_dir / "creative_catalog.html").exists()
        assert (creatives_dir / "creative_copies.csv").exists()
        assert (creatives_dir / "Variant-A_1_1.png").exists()

        # サマリーJSONの存在
        assert (out_dir / "launch_summary.json").exists()


def test_pdca_pipeline(sample_performance_csv, sample_config_yaml):
    """PDCA運用改善パイプラインの統合実行検証 (Report -> Remedial Creatives)"""
    config = load_campaign_config(sample_config_yaml)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "pdca_test"

        result = run_pdca_pipeline(
            performance_csv=sample_performance_csv,
            config=config,
            output_dir=out_dir,
            provider="mock",
            remedial_variants_count=1
        )

        assert "performance_csv" in result
        # レポート出力の存在
        report_html = Path(result["outputs"]["report_html"])
        assert report_html.exists()
        assert report_html.stat().st_size > 0

        # 改善クリエイティブの存在
        remedial_dir = Path(result["outputs"]["remedial_creatives_dir"])
        assert (remedial_dir / "creative_catalog.html").exists()
        assert (remedial_dir / "Variant-A_1_1.png").exists()

        # サマリーJSONの存在
        assert (out_dir / "pdca_summary.json").exists()


def test_cli_execution_e2e(sample_config_yaml, sample_performance_csv):
    """ops.py CLI コマンドのE2Eサブプロセス実行検証"""
    cli_path = module_dir / "scripts" / "ops.py"

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. pipeline --mode launch
        launch_dir = Path(tmpdir) / "cli_launch"
        cmd_launch = [
            sys.executable,
            str(cli_path),
            "pipeline",
            "--mode", "launch",
            "--config", str(sample_config_yaml),
            "--output-dir", str(launch_dir),
            "--provider", "mock"
        ]
        res_launch = subprocess.run(cmd_launch, capture_output=True, text=True)
        assert res_launch.returncode == 0, f"Launch CLI error: {res_launch.stderr}"
        assert (launch_dir / "launch_summary.json").exists()

        # 2. pipeline --mode pdca
        pdca_dir = Path(tmpdir) / "cli_pdca"
        cmd_pdca = [
            sys.executable,
            str(cli_path),
            "pipeline",
            "--mode", "pdca",
            "--config", str(sample_config_yaml),
            "--data", str(sample_performance_csv),
            "--output-dir", str(pdca_dir),
            "--provider", "mock"
        ]
        res_pdca = subprocess.run(cmd_pdca, capture_output=True, text=True)
        assert res_pdca.returncode == 0, f"PDCA CLI error: {res_pdca.stderr}"
        assert (pdca_dir / "pdca_summary.json").exists()
