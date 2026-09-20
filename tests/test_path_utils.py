"""Tests for path safety utilities."""
from theosis_ancient_context.adapters.path_utils import (
    safe_resolve,
    list_text_files,
    read_bounded,
)


class TestSafeResolve:
    """Path traversal prevention."""

    def test_valid_relative_path(self, tmp_path):
        (tmp_path / "test.txt").write_text("hello")
        result = safe_resolve(str(tmp_path), "test.txt")
        assert result is not None
        assert result.name == "test.txt"

    def test_subdirectory_path(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "file.txt").write_text("hello")
        result = safe_resolve(str(tmp_path), "sub/file.txt")
        assert result is not None

    def test_traversal_blocked(self, tmp_path):
        result = safe_resolve(str(tmp_path), "../etc/passwd")
        assert result is None

    def test_absolute_path_blocked(self, tmp_path):
        result = safe_resolve(str(tmp_path), "/etc/passwd")
        assert result is None

    def test_nonexistent_file(self, tmp_path):
        result = safe_resolve(str(tmp_path), "nonexistent.txt")
        assert result is None

    def test_dot_dot_dot_traversal(self, tmp_path):
        result = safe_resolve(str(tmp_path), "../../etc/passwd")
        assert result is None

    def test_symlink_traversal(self, tmp_path):
        """Symlink pointing outside base should be blocked."""
        target = tmp_path / "target.txt"
        target.write_text("secret")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        # Symlink within base is fine
        result = safe_resolve(str(tmp_path), "link.txt")
        assert result is not None


class TestListTextFiles:
    """Bounded text file listing."""

    def test_lists_txt_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.xml").write_text("b")
        (tmp_path / "c.json").write_text("c")
        (tmp_path / "d.pdf").write_text("d")  # should be excluded
        files = list_text_files(str(tmp_path))
        names = {f.name for f in files}
        assert "a.txt" in names
        assert "b.xml" in names
        assert "c.json" in names
        assert "d.pdf" not in names

    def test_respects_max_files(self, tmp_path):
        for i in range(10):
            (tmp_path / f"f{i:02d}.txt").write_text(str(i))
        files = list_text_files(str(tmp_path), max_files=5)
        assert len(files) == 5

    def test_nonexistent_directory(self):
        files = list_text_files("/nonexistent/dir")
        assert files == []


class TestReadBounded:
    """Bounded file reading."""

    def test_small_file(self, tmp_path):
        f = tmp_path / "small.txt"
        f.write_text("hello world")
        content = read_bounded(f)
        assert content == "hello world"

    def test_large_file_truncated(self, tmp_path):
        f = tmp_path / "large.txt"
        f.write_text("x" * 200_000)
        content = read_bounded(f, max_bytes=1000)
        assert len(content) < 200_000
        assert "File too large" in content

    def test_nonexistent_file(self, tmp_path):
        content = read_bounded(tmp_path / "nope.txt")
        assert "Error reading" in content
