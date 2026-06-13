import os
import json
from pathlib import Path
from typing import Dict, Optional


class SecretsManager:
    """
    Manages persistent authentication tokens in a central location.
    Storage: ~/.local/share/harnessctl/auth.json (following XDG spec)
    """

    def __init__(self):
        # Determine the base directory for auth storage
        if os.name == "nt":  # Windows
            base_dir = Path(os.environ.get("APPDATA", "~")).expanduser() / "harnessctl"
        else:  # Linux/macOS
            base_dir = (
                Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
                / "harnessctl"
            )

        self.auth_file = base_dir / "auth.json"
        self._ensure_dir()

    def _ensure_dir(self):
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        # Ensure private directory permissions on Unix
        if os.name != "nt":
            os.chmod(self.auth_file.parent, 0o700)

    def _load_all(self) -> Dict[str, str]:
        if not self.auth_file.exists():
            return {}
        try:
            with open(self.auth_file, "r") as f:
                data = json.load(f)
                # Flattening migration: if data is new format (provider: {token, type}), convert to flat (provider: token)
                updated = False
                for k, v in data.items():
                    if isinstance(v, dict) and "token" in v:
                        data[k] = v["token"]
                        updated = True
                if updated:
                    self._save_all(data)
                return data
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_all(self, secrets: Dict[str, str]):
        with open(self.auth_file, "w") as f:
            json.dump(secrets, f, indent=2)
        # Ensure private file permissions on Unix
        if os.name != "nt":
            os.chmod(self.auth_file, 0o600)

    def get_token(self, provider: str) -> Optional[str]:
        """
        Get token for a provider.
        Checks persistent storage first, then falls back to environment variables.
        """
        provider = provider.lower()

        # 1. Check persistent storage
        secrets = self._load_all()
        if provider in secrets:
            return secrets[provider]

        # 2. Fallback to common env vars
        env_map = {
            "github": "GITHUB_TOKEN",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
        }
        env_var = env_map.get(provider)
        if env_var:
            return os.getenv(env_var)

        return None

    def set_token(self, provider: str, token: str):
        """Save a token persistently for a provider."""
        provider = provider.lower()
        secrets = self._load_all()
        secrets[provider] = token
        self._save_all(secrets)

    def remove_token(self, provider: str):
        """Remove a token for a provider."""
        provider = provider.lower()
        secrets = self._load_all()
        if provider in secrets:
            del secrets[provider]
        self._save_all(secrets)

    def list_providers(self) -> Dict[str, bool]:
        """Returns a map of provider names to their authentication status."""
        secrets = self._load_all()
        # Common providers to always show
        base_providers = [
            "github",
            "openrouter",
            "openai",
            "anthropic",
            "google",
            "groq",
        ]
        result = {}
        for p in base_providers:
            result[p] = self.get_token(p) is not None

        # Add any other providers found in secrets
        for p in secrets:
            if p not in result:
                result[p] = True
        return result
