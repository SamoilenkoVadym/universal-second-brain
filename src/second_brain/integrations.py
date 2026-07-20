"""Install idempotent integrations into the actual AI-client locations."""
from __future__ import annotations

import json
from pathlib import Path

from .config import Config
from .paths import AppPaths

MARKER_START = "<!-- universal-second-brain:start -->"
MARKER_END = "<!-- universal-second-brain:end -->"
HOOK_MARKER = "# universal-second-brain"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Cannot update malformed JSON: {path}") from exc


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _hook(command: str, timeout: int = 120) -> dict:
    return {"hooks": [{"type": "command", "command": f"{command} {HOOK_MARKER}", "timeout": timeout}]}


def _merge_hooks(path: Path, hooks: dict[str, list[dict]]) -> None:
    payload = _read_json(path)
    root = payload.setdefault("hooks", {})
    for event, definitions in hooks.items():
        existing = root.setdefault(event, [])
        existing[:] = [item for item in existing if HOOK_MARKER not in json.dumps(item)]
        existing.extend(definitions)
    _write_json(path, payload)


def _replace_marked_block(path: Path, body: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"{MARKER_START}\n{body.rstrip()}\n{MARKER_END}\n"
    if MARKER_START in current and MARKER_END in current:
        before, _, tail = current.partition(MARKER_START)
        _, _, after = tail.partition(MARKER_END)
        current = before.rstrip() + "\n\n" + block + after.lstrip("\n")
    else:
        current = current.rstrip() + ("\n\n" if current.strip() else "") + block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(current, encoding="utf-8")


def _enable_codex_hooks(config_path: Path) -> None:
    current = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    if "[features]" in current:
        if "hooks" not in current.split("[features]", 1)[1].split("[", 1)[0]:
            current = current.replace("[features]", "[features]\nhooks = true", 1)
    else:
        current = current.rstrip() + "\n\n[features]\nhooks = true\n"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(current, encoding="utf-8")


def install(config: Config, paths: AppPaths, home: Path | None = None) -> dict[str, str]:
    """Install client hooks/rules; safe to run repeatedly without duplicates."""
    home = home or Path.home()
    project_root = Path(config.paths.projects_root).expanduser()
    installed: dict[str, str] = {}
    if config.integrations.get("claude_code", True):
        target = home / ".claude" / "settings.json"
        _merge_hooks(target, {
            "SessionStart": [_hook("second-brain run enrichment", 120)],
            "SessionEnd": [_hook("second-brain run session-capture", 120), _hook("second-brain run raw-flush", 600)],
        })
        installed["claude_code"] = str(target)
    if config.integrations.get("codex", True):
        hooks = home / ".codex" / "hooks.json"
        _merge_hooks(hooks, {
            "SessionStart": [_hook("second-brain run enrichment", 120)],
            "Stop": [_hook("second-brain run session-capture", 120), _hook("second-brain run raw-flush", 600)],
        })
        _enable_codex_hooks(home / ".codex" / "config.toml")
        _replace_marked_block(project_root / "AGENTS.md", "# Universal Second Brain\n\nBefore substantive work, run `second-brain search --query \"<user task>\"`.\nUse the configured Obsidian vault as the knowledge source of truth.")
        installed["codex"] = str(hooks)
    if config.integrations.get("cursor", True):
        target = project_root / ".cursor" / "rules" / "universal-second-brain.mdc"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("---\ndescription: Universal Second Brain context protocol\nalwaysApply: true\n---\n\nBefore substantive work, run `second-brain search --query \"<user task>\"`.\n", encoding="utf-8")
        installed["cursor"] = str(target)
    manifest = paths.integrations_dir / "installed.json"
    _write_json(manifest, installed)
    return installed


def status(config: Config, paths: AppPaths, home: Path | None = None) -> dict[str, bool]:
    home = home or Path.home()
    projects = Path(config.paths.projects_root).expanduser()
    return {
        "claude_code": (home / ".claude" / "settings.json").exists() and HOOK_MARKER in (home / ".claude" / "settings.json").read_text(encoding="utf-8"),
        "codex": (home / ".codex" / "hooks.json").exists() and HOOK_MARKER in (home / ".codex" / "hooks.json").read_text(encoding="utf-8") and (projects / "AGENTS.md").exists(),
        "cursor": (projects / ".cursor" / "rules" / "universal-second-brain.mdc").exists(),
    }
