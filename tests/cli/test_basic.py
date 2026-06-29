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
    assert "config" in result.stdout
    assert "prompts" in result.stdout
    assert "mcp" in result.stdout


def test_cli_validate_missing_config():
    result = runner.invoke(app, ["validate", "--config", "nonexistent.yaml"])
    assert result.exit_code == 2


def test_cli_init(tmp_path):
    config = tmp_path / "agents.yaml"
    result = runner.invoke(app, ["init", "--config", str(config)])
    assert result.exit_code == 0
    assert config.exists()
    assert "Initialized default spec" in result.stdout


def test_cli_config_help():
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout


def test_cli_prompts_help():
    result = runner.invoke(app, ["prompts", "--help"])
    assert result.exit_code == 0
    assert "install" in result.stdout
    assert "render" in result.stdout


def test_cli_stub_exit_code_and_message():
    result = runner.invoke(app, ["mcp", "select_model_for_task"])
    assert result.exit_code == 2
    assert "Not implemented yet: mcp select_model_for_task" in result.stdout


def test_cli_config_init_stub_exit_code_and_message():
    result = runner.invoke(
        app, ["config", "init", "--provider", "github-copilot", "--global"]
    )
    assert result.exit_code == 2
    assert "Not implemented yet: config init" in result.stdout


def test_cli_prompts_install_stub_exit_code_and_message():
    result = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "opencode",
            "--version",
            "v1",
            "--global",
        ],
    )
    assert result.exit_code == 2
    assert "Not implemented yet: prompts install" in result.stdout


def test_cli_prompts_render_stub_exit_code_and_message():
    result = runner.invoke(
        app,
        ["prompts", "render", "--harness", "opencode", "--version", "v1", "--cli"],
    )
    assert result.exit_code == 2
    assert "Not implemented yet: prompts render" in result.stdout
