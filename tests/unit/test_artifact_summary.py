"""Unit tests for _artifact_summary CLI helper."""
from agentsuite.cli import _artifact_summary


class TestArtifactSummary:
    def test_empty_when_dir_missing(self, tmp_path):
        assert _artifact_summary(tmp_path / "nonexistent") == ""

    def test_lists_user_facing_files(self, tmp_path):
        (tmp_path / "brief.md").write_text("x" * 1024)
        (tmp_path / "spec.md").write_text("y" * 2048)
        result = _artifact_summary(tmp_path)
        assert "brief.md" in result
        assert "spec.md" in result

    def test_excludes_internal_files(self, tmp_path):
        (tmp_path / "_state.json").write_text("{}")
        (tmp_path / "_meta.json").write_text("{}")
        (tmp_path / "brief.md").write_text("hello")
        result = _artifact_summary(tmp_path)
        assert "_state.json" not in result
        assert "_meta.json" not in result
        assert "brief.md" in result

    def test_empty_when_only_internal_files(self, tmp_path):
        (tmp_path / "_state.json").write_text("{}")
        assert _artifact_summary(tmp_path) == ""

    def test_caps_at_max_shown(self, tmp_path):
        for i in range(10):
            (tmp_path / f"artifact_{i}.md").write_text("x")
        result = _artifact_summary(tmp_path, max_shown=6)
        assert "(+ 4 more" in result

    def test_shows_size_in_kb(self, tmp_path):
        (tmp_path / "brief.md").write_text("x" * 2048)
        result = _artifact_summary(tmp_path)
        assert "KB" in result

    def test_no_overflow_line_when_at_limit(self, tmp_path):
        for i in range(3):
            (tmp_path / f"artifact_{i}.md").write_text("x")
        result = _artifact_summary(tmp_path, max_shown=6)
        assert "(+" not in result
