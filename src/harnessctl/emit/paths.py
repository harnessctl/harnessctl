"""Path resolution helpers for harnessctl emitters."""

import os
import re
from pathlib import Path


_ENV_RE = re.compile(r"\$\{env:([^}]+)\}")


def resolve_path(path_template: str, project_dir: str | None = None) -> str:
    """Resolve a path template to an absolute path.

    Supports:
      - ``~`` expanded via :func:`os.path.expanduser`.
      - ``{project}`` expanded to *project_dir* (raises if not provided).
      - ``${env:VAR}`` expanded to the value of ``VAR`` in the environment
        (raises if unset).

    The result is always an absolute path.
    """
    resolved = path_template

    # Expand ~ first so subsequent steps work on an absolute-ish string.
    if "~" in resolved:
        resolved = os.path.expanduser(resolved)

    # Expand {project}
    if "{project}" in resolved:
        if project_dir is None:
            raise ValueError(
                f"Path template contains {{project}} but no project_dir was provided: {path_template!r}"
            )
        resolved = resolved.replace("{project}", str(project_dir))

    # Expand ${env:VAR}
    def _env_replacer(match: re.Match) -> str:  # type: ignore[type-arg]
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise ValueError(
                f"Environment variable {var_name!r} is not set (required by path template: {path_template!r})"
            )
        return value

    resolved = _ENV_RE.sub(_env_replacer, resolved)

    # Make absolute
    return str(Path(resolved).resolve())
