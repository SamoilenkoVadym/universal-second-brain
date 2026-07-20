from second_brain.config import Config, LLMConfig, PathsConfig, save, load


def test_config_roundtrip(tmp_path):
    config = Config(PathsConfig(str(tmp_path), str(tmp_path)), LLMConfig("ollama", "llama3"))
    path = tmp_path / "config.toml"
    save(config, path)
    loaded = load(path)
    assert loaded.llm.provider == "ollama"
    assert loaded.paths.vault == str(tmp_path)
