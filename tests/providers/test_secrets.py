import os
from unittest.mock import patch

from harnessctl.providers.secrets import (
    parse_env_placeholder,
    resolve_secret,
    format_env_placeholder,
)


class MockWarningCollector:
    def __init__(self):
        self.warnings = []

    def add_warning(self, msg: str):
        self.warnings.append(msg)


def test_parse_env_placeholder():
    assert parse_env_placeholder("${env:FOO_BAR}") == "FOO_BAR"
    assert parse_env_placeholder("${env:KEY123}") == "KEY123"
    assert parse_env_placeholder("just_a_string") is None
    assert parse_env_placeholder("${not_env:FOO}") is None


@patch.dict(os.environ, {"MY_SECRET": "secret_value"})
def test_resolve_secret_success():
    assert resolve_secret("${env:MY_SECRET}") == "secret_value"


@patch.dict(os.environ, {}, clear=True)
def test_resolve_secret_missing_warns():
    collector = MockWarningCollector()
    result = resolve_secret("${env:MISSING_VAR}", warn_collector=collector)
    # Should pass through the placeholder
    assert result == "${env:MISSING_VAR}"
    assert len(collector.warnings) == 1
    assert "MISSING_VAR" in collector.warnings[0]


def test_resolve_secret_not_placeholder():
    assert resolve_secret("plain_text") == "plain_text"


def test_format_env_placeholder():
    assert format_env_placeholder("TEST_VAR") == "${env:TEST_VAR}"
