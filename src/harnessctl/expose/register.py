import yaml
from pathlib import Path
from typing import List, Optional


def register_model(
    model_name: str,
    source: str,
    via: List[str],
    path: Path,
    spec_path: Optional[Path] = None,
) -> None:
    """Register a pulled model in models.yaml fragment."""
    if spec_path is None:
        # Default to models.yaml in the current working directory or default location
        spec_path = Path("models.yaml")

    data = {"models": []}
    if spec_path.exists():
        with open(spec_path, "r") as f:
            existing_data = yaml.safe_load(f)
            if existing_data and "models" in existing_data:
                data = existing_data

    # Check if already exists
    entry_index = -1
    for i, model in enumerate(data["models"]):
        if model.get("name") == model_name:
            entry_index = i
            break

    new_entry = {
        "name": model_name,
        "source": source,
        "via": via,
        "path": str(path.absolute()),
    }

    if entry_index >= 0:
        data["models"][entry_index] = new_entry
    else:
        data["models"].append(new_entry)

    with open(spec_path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
