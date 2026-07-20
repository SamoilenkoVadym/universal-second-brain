"""Public command-line interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .automation import task_map
from .config import Config, LLMConfig, PathsConfig, SUPPORTED_PROVIDERS, SecretStore, load, save, validate
from .integrations import install as install_integrations, status as integration_status
from .operations import backup as create_backup, build_index, execute, restore as restore_backup, search as search_vault
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
    if not paths.config_file.exists():
        print("Configuration is missing; run `second-brain setup` first.")
        return 2
    config = load(paths.config_file)
    if task.mutates_vault and config.safety.get("backup_before_mutation", True):
        result = {"backup": str(create_backup(Path(config.paths.vault), paths)), **execute(task, config, paths)}
    else:
        result = execute(task, config, paths)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"Completed {task.name}.")
    return 0


def index(args: argparse.Namespace) -> int:
    paths = app_paths()
    if not paths.config_file.exists():
        print("Configuration is missing; run `second-brain setup` first.")
        return 2
    target = build_index(Path(load(paths.config_file).paths.vault), paths)
    print(json.dumps({"index": str(target)}) if args.json else f"Index updated: {target}")
    return 0


def search(args: argparse.Namespace) -> int:
    paths = app_paths()
    if not paths.config_file.exists():
        print("Configuration is missing; run `second-brain setup` first.")
        return 2
    results = search_vault(Path(load(paths.config_file).paths.vault), paths, args.query, args.limit)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("\n".join(f"[{item['score']}] {item['path']} — {item['title']}" for item in results) or "No matching notes.")
    return 0


def backup(args: argparse.Namespace) -> int:
    paths = app_paths()
    if not paths.config_file.exists():
        print("Configuration is missing; run `second-brain setup` first.")
        return 2
    target = create_backup(Path(load(paths.config_file).paths.vault), paths)
    print(str(target))
    return 0


def restore(args: argparse.Namespace) -> int:
    paths = app_paths()
    if not paths.config_file.exists():
        print("Configuration is missing; run `second-brain setup` first.")
        return 2
    count = restore_backup(Path(args.archive).expanduser(), Path(load(paths.config_file).paths.vault))
    print(f"Restored {count} file(s).")
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
    command.add_argument("--json", action="store_true")
    command.set_defaults(func=run)
    command = sub.add_parser("index")
    command.add_argument("--json", action="store_true")
    command.set_defaults(func=index)
    command = sub.add_parser("search")
    command.add_argument("--query", required=True)
    command.add_argument("--limit", type=int, default=10)
    command.add_argument("--json", action="store_true")
    command.set_defaults(func=search)
    command = sub.add_parser("backup")
    command.set_defaults(func=backup)
    command = sub.add_parser("restore")
    command.add_argument("--archive", required=True)
    command.set_defaults(func=restore)
    command = sub.add_parser("install")
    command.set_defaults(func=install)
    for name in ("enable", "disable", "migrate", "update", "uninstall"):
        command = sub.add_parser(name)
        command.set_defaults(func=lambda _: 0)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
