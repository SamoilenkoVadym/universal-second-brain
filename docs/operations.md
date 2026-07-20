# Operations

## Commands

`setup`, `doctor`, `status`, `install`, `enable`, `disable`, `search`, `run`, `backup`, `restore`, `migrate`, `update`, and `uninstall` are public CLI commands. `doctor` and `status` accept `--json`.

## Agent integrations

`second-brain install` writes an integration manifest under the runtime data directory. Claude Code receives hook commands, while Codex and Cursor receive English context/search instructions. The scheduler runs maintenance independently of an agent client.

## Safety

Mutation-class tasks create an audit entry and a vault snapshot before execution. Git commits and pushes are never enabled by default.

## Migration

Run `second-brain migrate --from-legacy <path>` to inspect a legacy installation. The command is dry-run by default and must be confirmed before copying configuration or state.
