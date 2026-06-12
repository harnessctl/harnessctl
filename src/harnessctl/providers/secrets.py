import os
import re
from typing import Optional

# Matches exactly ${env:VAR_NAME}
ENV_PATTERN = re.compile(r"^\$\{env:([A-Z0-9_]+)\}$")


def parse_env_placeholder(value: str) -> Optional[str]:
    """
    Parses a string like '${env:VAR_NAME}' and returns 'VAR_NAME'.
    Returns None if the string does not match the pattern.
    """
    match = ENV_PATTERN.match(value)
    if match:
        return match.group(1)
    return None


def resolve_secret(value: str, warn_collector=None) -> str:
    """
    Resolves a secret placeholder to its environment variable value.
    If warn_collector is provided and the variable is missing, it adds a warning.
    If value is not a placeholder, returns it as-is.
    """
    var_name = parse_env_placeholder(value)
    if not var_name:
        return value

    resolved = os.getenv(var_name)
    if resolved is None:
        if warn_collector:
            warn_collector.add_warning(
                f"Environment variable '{var_name}' referenced but not set in current environment."
            )
        # We don't fail, we just return the placeholder so it can be passed through
        return value
    return resolved


def format_env_placeholder(var_name: str) -> str:
    """
    Formats a variable name into a placeholder string '${env:VAR_NAME}'.
    """
    return f"${{env:{var_name}}}"
