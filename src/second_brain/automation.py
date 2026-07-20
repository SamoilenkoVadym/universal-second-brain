"""Single declarative inventory for every maintenance workflow."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    name: str
    command: str
    schedule: str
    mutates_vault: bool = False
    description: str = ""


TASKS = (
    Task("session-capture", "capture-session", "on-session-end", description="Capture agent session context"),
    Task("raw-flush", "flush", "on-session-end", description="Validate and flush raw session memory"),
    Task("enrichment", "enrich", "on-session-start", True, "Enrich projects, URLs, and session records"),
    Task("compile", "compile", "daily 21:00", True, "Compile knowledge into the vault"),
    Task("raw-inbox", "compile-raw", "every 5 minutes", True, "Process raw knowledge inbox"),
    Task("semantic-index", "embed-index", "after compile", False, "Refresh vector embeddings"),
    Task("obsidian-index", "obsidian-index", "daily 09:00", False, "Refresh Obsidian search index"),
    Task("wiki-index", "wiki-index", "after compile", True, "Refresh master wiki index"),
    Task("skills-harvest", "skills-harvest", "after session", True, "Harvest agent skills"),
    Task("skills-index", "skills-index", "after skills-harvest", True, "Refresh skills catalog"),
    Task("skills-provision", "skills-provision", "on-session-start", True, "Provision project skills"),
    Task("quality-gate", "quality-gate", "after compile", False, "Check knowledge quality"),
    Task("wiki-lint", "wiki-lint", "weekly Monday 10:00", False, "Lint vault links and metadata"),
    Task("dedupe", "dedupe", "daily 08:45", True, "Repair duplicate/conflict notes"),
    Task("compact-concepts", "compact-concepts", "monthly day 1 10:00", True, "Compact related concepts"),
    Task("debt-repair", "debt-repair", "weekly", True, "Repair knowledge debt"),
    Task("weekly-report", "report --weekly", "weekly Monday 09:00", True, "Write weekly report"),
    Task("monthly-report", "report --monthly", "monthly day 1 09:15", True, "Write monthly report"),
    Task("watchdog", "watchdog", "daily 09:30,18:30", False, "Alert on failed or stale automation"),
    Task("backup", "backup", "before mutation", False, "Snapshot vault before mutation"),
)


def task_map() -> dict[str, Task]:
    return {task.name: task for task in TASKS}
