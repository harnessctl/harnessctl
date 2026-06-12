import subprocess
from pathlib import Path


class OllamaPuller:
    def pull(self, model_name: str) -> bool:
        """Pull a model using Ollama CLI."""
        try:
            # We don't get a file path back from Ollama, it manages its own store
            subprocess.run(["ollama", "pull", model_name], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_local_path(self, model_name: str) -> Path:
        """Ollama managed models don't have a simple path we can point others to."""
        # This is a placeholder; for Ollama-native pulls, we usually let Ollama handle it
        return Path(f"ollama://{model_name}")
