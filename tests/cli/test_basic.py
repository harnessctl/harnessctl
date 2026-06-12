from typer.testing import CliRunner
from harnessctl.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "harnessctl 0.1.0" in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "harnessctl: Manage AI harness configurations and agents" in result.stdout


def test_cli_validate_missing_config():
    result = runner.invoke(app, ["validate", "--config", "nonexistent.yaml"])
    assert result.exit_code == 2


def test_cli_init(tmp_path):
    config = tmp_path / "agents.yaml"
    result = runner.invoke(app, ["init", "--config", str(config)])
    assert result.exit_code == 0
    assert config.exists()
    assert "Initialized default spec" in result.stdout
