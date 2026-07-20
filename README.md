# Universal Second Brain

A cross-platform, provider-neutral second-brain runtime for an Obsidian vault.

It keeps configuration, indexes, logs, backups, and credentials outside the vault; lets each user choose cloud or local AI; and installs native automations for macOS, Linux, or Windows.

## Quick start

```bash
uv tool install .
second-brain setup
second-brain doctor
second-brain status
```

`setup` asks for an Obsidian vault, projects root, AI provider/model, and optional Telegram notifications. It writes a portable TOML configuration, verifies the selected provider, creates runtime directories, generates agent integrations, and prepares native scheduler definitions.

It also bootstraps a non-destructive vault layout: `00 Inbox/raw`, `01 Projects`, and the complete `wiki/` knowledge taxonomy. Existing notes are never replaced.

For a complete walkthrough, provider notes, client integrations, and troubleshooting, see the [Setup Guide](docs/setup.md).

## What setup installs

- Native scheduler definitions for macOS, Linux, or Windows.
- Claude Code lifecycle hooks in `~/.claude/settings.json`.
- Codex lifecycle hooks in `~/.codex/hooks.json`, the required feature flag, and an `AGENTS.md` protocol in the selected projects root.
- A Cursor rule in the selected projects root.

All integration changes are idempotent: rerunning setup replaces only the blocks managed by Universal Second Brain and preserves unrelated user settings.

## Supported providers

- Anthropic
- OpenAI
- Any OpenAI-compatible cloud endpoint
- Ollama
- LM Studio

Cloud API keys are stored in the operating system credential store when the optional `keyring` dependency is installed. Otherwise setup requires explicit confirmation before writing a local secrets file with owner-only permissions.

## Automation coverage

The registry includes session capture, raw flush, enrichment, compilation, semantic and Obsidian indexing, skill harvesting/provisioning, quality gates, linting, duplicate repair, reports, watchdogs, backups, and notifications. Each task has an explicit schedule and safety classification.

See [docs/operations.md](docs/operations.md) for commands, integrations, and migration notes.

## License and contributions

This project is licensed under the [GNU Affero General Public License v3.0 or later](LICENSE). If you distribute a modified version or operate a modified version for users over a network, you must make the corresponding source code available under the same license.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the required change description and publication policy.
