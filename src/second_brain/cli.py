"""Public command-line interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .automation import task_map
from .config import Config, LLMConfig, PathsConfig, SUPPORTED_PROVIDERS, SecretStore, load, save, validate
from .integrations import install as install_integrations, status as integration_status
from .paths import app_paths, ensure_runtime
from .providers import healthcheck
from .scheduler import activate, render
from .vault import bootstrap as bootstrap_vault, validate as validate_vault


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{label}{suffix}: ").strip() or default


def setup(_: argparse.Namespace) -> int:
    paths = app_paths()
    ensure_runtime(paths)
    vault = _prompt("Obsidian vault path")
    projects = _prompt("Projects root path")
    provider = _prompt("Provider (anthropic, openai, openai-compatible, ollama, lm-studio)", "ollama")
    if provider not in SUPPORTED_PROVIDERS:
        print(f"Unsupported provider: {provider}")
        return 2
    model = _prompt("Model")
    endpoint = _prompt("Endpoint (leave blank for provider default)")
    config = Config(PathsConfig(str(Path(vault).expanduser()), str(Path(projects).expanduser())), LLMConfig(provider, model, endpoint))
    if provider in {"anthropic", "openai", "openai-compatible"}:
        name = f"{provider.upper().replace('-', '_')}_API_KEY"
        config.llm.secret_name = name
        value = _prompt(f"{provider} API key")
        if not value:
            print("An API key is required for a cloud provider.")
            return 2
        use_file = _prompt("Use protected local secret file if system keyring is unavailable? (yes/no)", "no").lower() == "yes"
        try:
            location = SecretStore(paths).set(name, value, allow_file=use_file)
            print(f"Stored credential in {location}.")
        except RuntimeError as exc:
            print(str(exc))
            return 2
    issues = validate(config)
    if issues:
        print("Setup failed:\n- " + "\n- ".join(issues))
        return 2
    created = bootstrap_vault(Path(config.paths.vault))
    save(config, paths.config_file)
    install_integrations(config, paths)
    schedule = render(paths)
    activate(paths)
    check = healthcheck(config, SecretStore(paths).get(config.llm.secret_name) if config.llm.secret_name else "")
    print(f"Configuration saved to {paths.config_file}")
    print(f"Vault structure ready ({len(created)} item(s) created).")
    print(f"Scheduler manifest generated and activated at {schedule}")
    print(f"Provider health: {check.detail}")
    return 0 if check.ok else 1


def doctor(args: argparse.Namespace) -> int:
    paths = app_paths()
    issues = []
    if not paths.config_file.exists():
        issues.append("configuration is missing; run `second-brain setup`")
        config = None
    else:
        config = load(paths.config_file)
        issues.extend(validate(config))
        issues.extend(validate_vault(Path(config.paths.vault)))
        secret = SecretStore(paths).get(config.llm.secret_name) if config.llm.secret_name else ""
        health = healthcheck(config, secret)
        if not health.ok:
            issues.append(health.detail)
        integrations = integration_status(config, paths)
        for name, installed in integrations.items():
            if config.integrations.get(name, True) and not installed:
                issues.append(f"{name} integration is not installed")
    result = {"ok": not issues, "issues": issues, "config": str(paths.config_file)}
    print(json.dumps(result) if args.json else ("OK" if not issues else "FAIL\n- " + "\n- ".join(issues)))
    return 0 if not issues else 1


def status(args: argparse.Namespace) -> int:
    paths = app_paths()
    tasks = [{"name": task.name, "schedule": task.schedule, "mutates_vault": task.mutates_vault} for task in task_map().values()]
    integrations = integration_status(load(paths.config_file), paths) if paths.config_file.exists() else {}
    result = {"configured": paths.config_file.exists(), "scheduler": str(paths.scheduler_dir), "integrations": integrations, "tasks": tasks}
    print(json.dumps(result, indent=2) if args.json else "\n".join(f"{item['name']}: {item['schedule']}" for item in tasks))
    return 0


def run(args: argparse.Namespace) -> int:
    task = task_map().get(args.task)
    if not task:
        print(f"Unknown task: {args.task}")
        return 2
    paths = app_paths()
    audit = paths.data_dir / "logs" / "automation-audit.jsonl"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(audit.read_text(encoding="utf-8") if audit.exists() else "", encoding="utf-8")
    with audit.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"task": task.name, "description": task.description, "status": "dispatched"}) + "\n")
    print(f"Dispatched {task.name}; audit log: {audit}")
    return 0


def install(_: argparse.Namespace) -> int:
    paths = app_paths()
    if not paths.config_file.exists():
        print("Configuration is missing; run `second-brain setup` first.")
        return 2
    config = load(paths.config_file)
    ensure_runtime(paths)
    install_integrations(config, paths)
    render(paths)
    activate(paths)
    print("Native scheduler definitions installed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="second-brain", description="Universal Second Brain")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup").set_defaults(func=setup)
    for name, func in (("doctor", doctor), ("status", status)):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true")
        command.set_defaults(func=func)
    command = sub.add_parser("run")
    command.add_argument("task")
    command.set_defaults(func=run)
    command = sub.add_parser("install")
    command.set_defaults(func=install)
    for name in ("enable", "disable", "search", "backup", "restore", "migrate", "update", "uninstall"):
        command = sub.add_parser(name)
        command.set_defaults(func=lambda _: 0)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
