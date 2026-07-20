import json

from second_brain.config import Config, LLMConfig, PathsConfig
from second_brain.integrations import install, status
from second_brain.paths import AppPaths, ensure_runtime


def test_installs_real_client_hooks_and_is_idempotent(tmp_path):
    home = tmp_path / "home"
    projects = tmp_path / "projects"
    projects.mkdir()
    claude = home / ".claude"
    claude.mkdir(parents=True)
    (claude / "settings.json").write_text(json.dumps({"hooks": {"Stop": [{"hooks": [{"command": "keep-me"}]}]}}))
    paths = AppPaths(tmp_path / "config", tmp_path / "data")
    ensure_runtime(paths)
    config = Config(PathsConfig(str(tmp_path), str(projects)), LLMConfig("ollama", "llama3"))
    install(config, paths, home)
    install(config, paths, home)
    settings = json.loads((claude / "settings.json").read_text())
    assert settings["hooks"]["Stop"][0]["hooks"][0]["command"] == "keep-me"
    assert len(settings["hooks"]["SessionStart"]) == 1
    assert status(config, paths, home) == {"claude_code": True, "codex": True, "cursor": True}
