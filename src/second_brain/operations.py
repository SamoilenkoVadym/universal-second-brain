"""Safe local vault operations used by the public CLI and automations."""
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .automation import Task
from .config import Config
from .paths import AppPaths


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _markdown_files(vault: Path) -> list[Path]:
    return sorted(path for path in vault.rglob("*.md") if ".obsidian" not in path.parts)


def build_index(vault: Path, paths: AppPaths) -> Path:
    """Create a portable lexical index without copying vault content elsewhere."""
    documents = []
    for path in _markdown_files(vault):
        text = path.read_text(encoding="utf-8", errors="replace")
        documents.append({
            "path": str(path.relative_to(vault)),
            "title": next((line.removeprefix("# ").strip() for line in text.splitlines() if line.startswith("# ")), path.stem),
            "excerpt": " ".join(text.split())[:500],
            "modified": path.stat().st_mtime_ns,
        })
    target = paths.data_dir / "index" / "vault-index.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"created_at": _now(), "documents": documents}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def search(vault: Path, paths: AppPaths, query: str, limit: int = 10) -> list[dict]:
    index = paths.data_dir / "index" / "vault-index.json"
    if not index.exists():
        build_index(vault, paths)
    payload = json.loads(index.read_text(encoding="utf-8"))
    tokens = [token.casefold() for token in re.findall(r"[\w-]+", query) if len(token) > 1]
    scored = []
    for document in payload["documents"]:
        haystack = f"{document['title']} {document['path']} {document['excerpt']}".casefold()
        score = sum(haystack.count(token) for token in tokens)
        if score:
            scored.append({**document, "score": score})
    return sorted(scored, key=lambda item: (-item["score"], item["path"]))[:limit]


def backup(vault: Path, paths: AppPaths) -> Path:
    target = paths.data_dir / "backups" / f"vault-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in vault.rglob("*"):
            if path.is_file() and ".obsidian/workspace" not in str(path):
                archive.write(path, path.relative_to(vault))
    return target


def restore(archive_path: Path, vault: Path) -> int:
    """Restore a backup while refusing absolute and traversal archive members."""
    restored = 0
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            relative = PurePosixPath(member.filename)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe archive path: {member.filename}")
            if member.is_dir():
                continue
            destination = vault.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, destination.open("wb") as output:
                output.write(source.read())
            restored += 1
    return restored


def execute(task: Task, config: Config, paths: AppPaths) -> dict:
    vault = Path(config.paths.vault)
    result: dict[str, object] = {"task": task.name, "at": _now(), "status": "completed"}
    if task.name in {"semantic-index", "obsidian-index", "wiki-index"}:
        result["index"] = str(build_index(vault, paths))
    elif task.name in {"weekly-report", "monthly-report"}:
        reports = paths.data_dir / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        report = reports / f"{task.name}-{datetime.now().strftime('%Y%m%d')}.md"
        report.write_text(f"# {task.description}\n\nGenerated: {_now()}\n\nRun `second-brain search` to explore the current knowledge index.\n", encoding="utf-8")
        result["report"] = str(report)
    else:
        result["detail"] = "Lifecycle event recorded; provider-backed enrichment and compilation are not enabled in this release."
    audit = paths.data_dir / "logs" / "automation-audit.jsonl"
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    return result
