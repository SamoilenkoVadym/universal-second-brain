"""Portable TOML configuration and secret references."""
from __future__ import annotations

import os
import stat
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .paths import AppPaths


SUPPORTED_PROVIDERS = {"anthropic", "openai", "openai-compatible", "ollama", "lm-studio"}


@dataclass
class PathsConfig:
    vault: str
    projects_root: str


@dataclass
class LLMConfig:
    provider: str
    model: str
    endpoint: str = ""
    fallback_provider: str = ""
    fallback_model: str = ""
    secret_name: str = ""


@dataclass
class Config:
    paths: PathsConfig
    llm: LLMConfig
    automation: dict[str, bool] = field(default_factory=dict)
    integrations: dict[str, bool] = field(default_factory=lambda: {"claude_code": True, "codex": True, "cursor": True})
    notifications: dict[str, str | bool] = field(default_factory=lambda: {"local": True, "telegram": False})
    safety: dict[str, bool] = field(default_factory=lambda: {"backup_before_mutation": True, "git_push": False})


def validate(config: Config) -> list[str]:
    issues: list[str] = []
    if config.llm.provider not in SUPPORTED_PROVIDERS:
        issues.append(f"unsupported provider: {config.llm.provider}")
    if not config.paths.vault or not Path(config.paths.vault).expanduser().is_dir():
        issues.append("vault path does not exist or is not a directory")
    if not config.paths.projects_root or not Path(config.paths.projects_root).expanduser().is_dir():
        issues.append("projects root does not exist or is not a directory")
    if not config.llm.model:
        issues.append("model is required")
    return issues


def load(path: Path) -> Config:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config(
        paths=PathsConfig(**raw["paths"]),
        llm=LLMConfig(**raw["llm"]),
        automation=raw.get("automation", {}),
        integrations=raw.get("integrations", {}),
        notifications=raw.get("notifications", {}),
        safety=raw.get("safety", {}),
    )


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def save(config: Config, path: Path) -> None:
    data = asdict(config)
    parts: list[str] = []
    for section in ("paths", "llm", "automation", "integrations", "notifications", "safety"):
        parts.append(f"[{section}]")
        parts.extend(f"{key} = {_toml_value(value)}" for key, value in data[section].items())
        parts.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


class SecretStore:
    """Uses keyring when available; file storage is an explicit fallback."""
    service = "universal-second-brain"

    def __init__(self, paths: AppPaths):
        self.paths = paths

    def set(self, name: str, value: str, allow_file: bool = False) -> str:
        try:
            import keyring  # type: ignore
            keyring.set_password(self.service, name, value)
            return "keyring"
        except ImportError:
            if not allow_file:
                raise RuntimeError("keyring is unavailable; rerun with explicit local secret storage confirmation")
        self.paths.secrets_file.write_text(f"{name}={value}\n", encoding="utf-8")
        self.paths.secrets_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return "file"

    def get(self, name: str) -> str:
        try:
            import keyring  # type: ignore
            return keyring.get_password(self.service, name) or ""
        except ImportError:
            pass
        if not self.paths.secrets_file.exists():
            return ""
        for line in self.paths.secrets_file.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key == name:
                return value
        return os.environ.get(name, "")
