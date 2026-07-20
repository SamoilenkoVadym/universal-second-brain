from second_brain.operations import backup, build_index, restore, search
from second_brain.paths import AppPaths, ensure_runtime


def test_index_search_backup_and_restore(tmp_path):
    vault = tmp_path / "vault"
    note = vault / "wiki" / "concepts" / "memory.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Memory\n\nSemantic knowledge retrieval.", encoding="utf-8")
    paths = AppPaths(tmp_path / "config", tmp_path / "data")
    ensure_runtime(paths)
    build_index(vault, paths)
    assert search(vault, paths, "semantic retrieval")[0]["path"] == "wiki/concepts/memory.md"
    archive = backup(vault, paths)
    note.unlink()
    assert restore(archive, vault) == 1
    assert note.exists()
