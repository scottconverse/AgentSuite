"""Unit tests for kernel.artifacts."""
import json
import sys

import pytest


from agentsuite.kernel.artifacts import ArtifactWriter


def test_writer_creates_run_directory(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="2026-04-26-test")
    assert w.run_dir.exists()
    assert w.run_dir == tmp_path / "runs" / "2026-04-26-test"


def test_writer_writes_markdown_and_returns_ref(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    ref = w.write("brand-system.md", "# Brand System\n\nHello", kind="spec", stage="spec")
    assert ref.path.read_text(encoding="utf-8").startswith("# Brand System")
    assert ref.kind == "spec"
    assert ref.stage == "spec"
    assert len(ref.sha256) == 64


def test_writer_writes_json(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    ref = w.write_json("inputs_manifest.json", {"x": 1}, kind="data", stage="intake")
    loaded = json.loads(ref.path.read_text(encoding="utf-8"))
    assert loaded == {"x": 1}


def test_writer_overwrites_same_path_idempotent(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    r1 = w.write("a.md", "v1", kind="spec", stage="spec")
    r2 = w.write("a.md", "v2", kind="spec", stage="spec")
    assert r1.path == r2.path
    assert r2.path.read_text(encoding="utf-8") == "v2"
    assert r1.sha256 != r2.sha256


def test_writer_supports_subdirectories(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    ref = w.write("brief-template-library/landing-hero.md", "x", kind="template", stage="execute")
    assert ref.path.exists()
    assert "brief-template-library" in str(ref.path)


def test_writer_sha_stable_for_same_content(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    r1 = w.write("a.md", "same", kind="spec", stage="spec")
    r2 = w.write("b.md", "same", kind="spec", stage="spec")
    assert r1.sha256 == r2.sha256


def test_promote_copies_to_kernel_dir(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    w.write("brand-system.md", "promoted", kind="spec", stage="spec")
    promoted = w.promote(project_slug="patentforgelocal")
    assert any(p.name == "brand-system.md" for p in promoted)
    kernel_path = tmp_path / "_kernel" / "patentforgelocal" / "brand-system.md"
    assert kernel_path.read_text(encoding="utf-8") == "promoted"


def test_writer_rejects_path_traversal(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    with pytest.raises(ValueError, match="escapes run_dir"):
        w.write("../../etc/secret.txt", "bad", kind="spec", stage="spec")


def test_writer_rejects_deeply_nested_traversal(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    with pytest.raises(ValueError, match="escapes run_dir"):
        w.write("subdir/../../../../../../etc/passwd", "bad", kind="spec", stage="spec")


# Note: bare absolute paths like "/etc/passwd" resolve differently on Windows
# (treated as relative to current drive). The parametrize below covers POSIX behavior.
# The critical guard is the is_relative_to() check which works cross-platform.
@pytest.mark.parametrize("bad_path", [
    "../../etc/secret.txt",
    "subdir/../../../../../../etc/passwd",
    *(["/etc/passwd", "/absolute/path/file.txt"] if sys.platform != "win32" else []),
])
def test_resolve_safe_rejects_bad_paths(tmp_path, bad_path):
    """_resolve_safe raises ValueError for traversal and absolute-path attacks."""
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    with pytest.raises(ValueError, match="escapes run_dir"):
        w._resolve_safe(bad_path)


def test_resolve_safe_allows_legitimate_paths(tmp_path):
    """_resolve_safe returns the resolved path for safe relative paths."""
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    result = w._resolve_safe("subdir/file.md")
    assert result == (w.run_dir / "subdir" / "file.md").resolve()


def test_writer_allows_nested_paths(tmp_path):
    w = ArtifactWriter(output_root=tmp_path, run_id="r1")
    ref = w.write("a/b/c/file.md", "content", kind="spec", stage="spec")
    assert ref.path.exists()
    assert ref.path.read_text(encoding="utf-8") == "content"
