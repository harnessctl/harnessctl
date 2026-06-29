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
    assert "Manage routing configuration and bootstrap workflows" in result.stdout
    assert "Manage harness-aware prompt bundles" in result.stdout
    assert (
        "MCP entrypoints for integration with external orchestrators" in result.stdout
    )


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

    init_help = runner.invoke(app, ["config", "init", "--help"])
    assert init_help.exit_code == 0
    assert "--provider" in init_help.stdout


def test_cli_prompts_help():
    result = runner.invoke(app, ["prompts", "--help"])
    assert result.exit_code == 0
    assert "install" in result.stdout
    assert "render" in result.stdout

    install_help = runner.invoke(app, ["prompts", "install", "--help"])
    assert install_help.exit_code == 0
    assert "--harness" in install_help.stdout

    render_help = runner.invoke(app, ["prompts", "render", "--help"])
    assert render_help.exit_code == 0
    assert "--harness" in render_help.stdout


def test_cli_mcp_select_model_requires_request_source():
    result = runner.invoke(app, ["mcp", "select_model_for_task"])
    assert result.exit_code == 2
    assert "exactly one of --request-json or --request-file" in result.stdout


def test_cli_config_init_command_executes(tmp_path):
    result = runner.invoke(
        app,
        ["config", "init", "--provider", "github-copilot", "--global"],
        env={"HARNESSCTL_HOME": str(tmp_path / "home")},
    )
    assert result.exit_code == 0
    assert "Initialized config" in result.stdout


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
