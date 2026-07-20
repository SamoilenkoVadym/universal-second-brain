from second_brain.vault import DIRECTORIES, FILES, bootstrap, validate


def test_bootstrap_creates_the_complete_obsidian_layout_without_overwriting(tmp_path):
    existing = tmp_path / "wiki" / "log.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("keep this", encoding="utf-8")
    bootstrap(tmp_path)
    assert not validate(tmp_path)
    assert existing.read_text(encoding="utf-8") == "keep this"
    for item in DIRECTORIES:
        assert (tmp_path / item).is_dir()
    for item in FILES:
        assert (tmp_path / item).is_file()
