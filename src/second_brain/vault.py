"""Non-destructive Obsidian vault bootstrap and validation."""
from __future__ import annotations

from pathlib import Path


DIRECTORIES = (
    "00 Inbox/raw",
    "01 Projects",
    "wiki/architecture",
    "wiki/client-knowledge",
    "wiki/concepts",
    "wiki/connections",
    "wiki/design-systems",
    "wiki/mistakes",
    "wiki/project-templates",
    "wiki/qa",
    "wiki/shared-patterns",
    "wiki/skills",
    "wiki/tech-patterns",
)

FILES = {
    "wiki/_master-index.md": "# Knowledge Index\n\nThis file is maintained by Universal Second Brain.\n",
    "wiki/log.md": "# Knowledge Log\n",
    "wiki/skills/skills-catalog.json": "{\n  \"version\": 1,\n  \"skills\": []\n}\n",
    "00 Inbox/README.md": "# Inbox\n\nDrop unprocessed notes and source material here.\n",
    "01 Projects/README.md": "# Projects\n\nProject records are maintained by Universal Second Brain.\n",
}


def bootstrap(vault: Path) -> list[Path]:
    """Create only missing folders/files. Existing user content is untouched."""
    created: list[Path] = []
    for relative in DIRECTORIES:
        path = vault / relative
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
    for relative, content in FILES.items():
        path = vault / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            created.append(path)
    return created


def validate(vault: Path) -> list[str]:
    issues: list[str] = []
    for relative in DIRECTORIES:
        if not (vault / relative).is_dir():
            issues.append(f"missing vault directory: {relative}")
    for relative in FILES:
        if not (vault / relative).is_file():
            issues.append(f"missing vault file: {relative}")
    return issues
