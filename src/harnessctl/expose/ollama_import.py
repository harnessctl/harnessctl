import os
import subprocess
from typing import Optional
from pathlib import Path


def create_modelfile(
    model_path: Path, model_name: str, cache_dir: Optional[Path] = None
) -> Path:
    """Generate a Modelfile for importing a GGUF into Ollama."""
    if cache_dir is None:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            cache_dir = Path(xdg_data) / "harnessctl" / "models"
        else:
            cache_dir = Path.home() / ".local" / "share" / "harnessctl" / "models"

    ollama_dir = cache_dir / "ollama" / model_name
    ollama_dir.mkdir(parents=True, exist_ok=True)

    modelfile_path = ollama_dir / "Modelfile"
    content = f"""FROM {model_path.absolute()}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
"""
    with open(modelfile_path, "w") as f:
        f.write(content)

    return modelfile_path


def import_to_ollama(modelfile_path: Path, model_name: str) -> bool:
    """Run 'ollama create' to import the model."""
    try:
        subprocess.run(
            ["ollama", "create", model_name, "-f", str(modelfile_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
