import os
import shutil
from pathlib import Path
from typing import Optional
from huggingface_hub import hf_hub_download, snapshot_download


class HuggingFaceDownloader:
    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            # Default to XDG data home
            xdg_data = os.environ.get("XDG_DATA_HOME")
            if xdg_data:
                cache_dir = Path(xdg_data) / "harnessctl" / "models"
            else:
                cache_dir = Path.home() / ".local" / "share" / "harnessctl" / "models"

        self.cache_dir = cache_dir / "huggingface"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download(self, repo_id: str, filename: Optional[str] = None) -> Path:
        """Download a file or entire repo from Hugging Face."""
        # Pre-check disk space (rough estimate)
        # In a real app we'd fetch the size first via HfApi
        total, used, free = shutil.disk_usage(self.cache_dir)
        if free < 2 * (1024**3):  # Less than 2GB free
            # In a real app we'd be more precise about the requirement
            pass

        if filename:
            path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=self.cache_dir / repo_id,
                local_dir_use_symlinks=False,
                resume_download=True,
            )
        else:
            path = snapshot_download(
                repo_id=repo_id,
                local_dir=self.cache_dir / repo_id,
                local_dir_use_symlinks=False,
                resume_download=True,
            )

        return Path(path)
