from second_brain.paths import AppPaths, ensure_runtime
from second_brain.scheduler import render


def test_scheduler_manifest_contains_index_jobs(tmp_path):
    paths = AppPaths(tmp_path / "config", tmp_path / "data")
    ensure_runtime(paths)
    manifest = render(paths)
    assert "semantic-index" in manifest.read_text()
