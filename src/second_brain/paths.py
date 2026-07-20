"""Cross-platform user configuration and runtime locations."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    config_dir: Path
    data_dir: Path

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.toml"

    @property
    def secrets_file(self) -> Path:
        return self.config_dir / "secrets.env"

    @property
    def integrations_dir(self) -> Path:
        return self.data_dir / "integrations"

    @property
    def scheduler_dir(self) -> Path:
        return self.data_dir / "scheduler"


def app_paths() -> AppPaths:
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        data = Path(os.environ.get("LOCALAPPDATA", root))
        return AppPaths(root / "UniversalSecondBrain", data / "UniversalSecondBrain")
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return AppPaths(config / "universal-second-brain", data / "universal-second-brain")


def ensure_runtime(paths: AppPaths) -> None:
    for path in (paths.config_dir, paths.data_dir, paths.data_dir / "logs", paths.data_dir / "index", paths.data_dir / "backups", paths.integrations_dir, paths.scheduler_dir):
        path.mkdir(parents=True, exist_ok=True)
