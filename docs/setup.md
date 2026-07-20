# Setup Guide

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for the recommended installation path
- An existing Obsidian vault and a directory containing your projects
- At least one supported LLM option: Anthropic, OpenAI, an OpenAI-compatible API, Ollama, or LM Studio

For local models, start Ollama or LM Studio before running setup. Cloud providers require an API key.

## Install

Clone the repository and install the CLI:

```bash
git clone https://github.com/SamoilenkoVadym/universal-second-brain.git
cd universal-second-brain
uv tool install .
```

For development instead of a global tool installation:

```bash
uv sync --extra dev
uv run second-brain setup
```

## Configure

Run the interactive setup wizard:

```bash
second-brain setup
```

The wizard asks for your Obsidian vault, project root, provider/model/endpoint, and—when required—a cloud API key. It only offers local file-based secret storage when the OS credential store is unavailable and you explicitly approve it.

## Verify

```bash
second-brain doctor
second-brain status --json
```

`doctor` checks the vault structure, provider health, and each enabled AI-client integration.

## AI client integrations

| Client | Installed location | Behavior |
| --- | --- | --- |
| Claude Code | `~/.claude/settings.json` | Runs enrichment when a session starts and captures/flushes knowledge when it ends. |
| Codex | `~/.codex/hooks.json` and `~/.codex/config.toml` | Enables hooks, runs the same lifecycle actions, and adds a managed context protocol to `<projects-root>/AGENTS.md`. |
| Cursor | `<projects-root>/.cursor/rules/universal-second-brain.mdc` | Adds a persistent context/search instruction for projects under the selected root. |

Restart Claude Code and Codex after setup so they reload their hook configuration.

## Vault layout

Setup creates only missing items and never overwrites existing notes:

```text
00 Inbox/raw/
01 Projects/
wiki/
  architecture/              client-knowledge/       concepts/
  connections/               design-systems/         mistakes/
  project-templates/         qa/                     shared-patterns/
  skills/                    tech-patterns/
  _master-index.md           log.md
```

## Updating or repairing an installation

Run setup again after changing folders, provider details, or integrations. The operation is idempotent.

```bash
second-brain setup
second-brain install
second-brain doctor
```

## Security

Do not commit generated runtime configuration or a local `secrets.env` file. The project `.gitignore` excludes common secret and runtime files, but always review `git status` before pushing changes.
