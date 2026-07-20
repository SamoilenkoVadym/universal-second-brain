"""Generate inspectable platform scheduler manifests."""
from __future__ import annotations

import json
import os
import plistlib
import platform
import subprocess
from pathlib import Path

from .automation import TASKS
from .paths import AppPaths


def platform_name() -> str:
    return {"Darwin": "launchd", "Linux": "systemd", "Windows": "task-scheduler"}.get(platform.system(), "unsupported")


def render(paths: AppPaths) -> Path:
    target = paths.scheduler_dir / f"{platform_name()}.json"
    payload = {"platform": platform_name(), "command_prefix": "second-brain run", "tasks": [task.__dict__ for task in TASKS if "on-session" not in task.schedule and task.name != "backup"]}
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if platform_name() == "launchd":
        _render_launchd(paths, payload["tasks"])
    elif platform_name() == "systemd":
        _render_systemd(paths, payload["tasks"])
    elif platform_name() == "task-scheduler":
        _render_windows(paths, payload["tasks"])
    return target


def _render_launchd(paths: AppPaths, tasks: list[dict]) -> None:
    for task in tasks:
        name = task["name"]
        payload = {"Label": f"org.universal-second-brain.{name}", "ProgramArguments": ["second-brain", "run", name], "RunAtLoad": False, "StandardOutPath": str(paths.data_dir / "logs" / f"{name}.log"), "StandardErrorPath": str(paths.data_dir / "logs" / f"{name}.log")}
        with (paths.scheduler_dir / f"org.universal-second-brain.{name}.plist").open("wb") as handle:
            plistlib.dump(payload, handle)


def _render_systemd(paths: AppPaths, tasks: list[dict]) -> None:
    for task in tasks:
        name = task["name"]
        (paths.scheduler_dir / f"universal-second-brain-{name}.service").write_text(
            f"[Unit]\nDescription=Universal Second Brain: {name}\n\n[Service]\nType=oneshot\nExecStart=second-brain run {name}\n",
            encoding="utf-8",
        )
        (paths.scheduler_dir / f"universal-second-brain-{name}.timer").write_text(
            f"[Unit]\nDescription=Timer for Universal Second Brain: {name}\n\n[Timer]\nOnCalendar=*-*-* 09:00:00\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n",
            encoding="utf-8",
        )


def _render_windows(paths: AppPaths, tasks: list[dict]) -> None:
    for task in tasks:
        name = task["name"]
        (paths.scheduler_dir / f"UniversalSecondBrain-{name}.xml").write_text(
            f"<?xml version=\"1.0\"?><Task version=\"1.4\"><RegistrationInfo><Description>Universal Second Brain: {name}</Description></RegistrationInfo><Actions Context=\"Author\"><Exec><Command>second-brain</Command><Arguments>run {name}</Arguments></Exec></Actions></Task>",
            encoding="utf-8",
        )


def activate(paths: AppPaths) -> None:
    """Install generated definitions using the native user-level scheduler."""
    kind = platform_name()
    if kind == "launchd":
        agents = Path.home() / "Library" / "LaunchAgents"
        agents.mkdir(parents=True, exist_ok=True)
        for source in paths.scheduler_dir.glob("org.universal-second-brain.*.plist"):
            destination = agents / source.name
            destination.write_bytes(source.read_bytes())
            subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(destination)], check=False, capture_output=True)
    elif kind == "systemd":
        units = Path.home() / ".config/systemd/user"
        units.mkdir(parents=True, exist_ok=True)
        for source in paths.scheduler_dir.glob("universal-second-brain-*.*"):
            (units / source.name).write_bytes(source.read_bytes())
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
    elif kind == "task-scheduler":
        for source in paths.scheduler_dir.glob("UniversalSecondBrain-*.xml"):
            subprocess.run(["schtasks", "/Create", "/TN", source.stem, "/XML", str(source), "/F"], check=False, capture_output=True)
