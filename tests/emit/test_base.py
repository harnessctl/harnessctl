"""Tests for harnessctl.emit.base."""

from pathlib import Path

import pytest

from harnessctl.emit.base import (
    Emitter,
    FileChangedError,
    GENERATED_MARKER,
)


class ConcreteEmitter(Emitter):
    """Minimal concrete emitter for testing base helpers."""

    def emit_file(self, target_path: str, content: str, mode: str) -> None:
        path = Path(target_path)
        full_content = self._prepend_marker(content)

        if mode == "dry-run":
            return

        if mode == "diff":
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if existing == full_content:
                    return
                diff = self._unified_diff(existing, full_content, target_path)
                raise FileChangedError(target_path, diff)
            return

        if mode == "check":
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if existing != full_content:
                    diff = self._unified_diff(existing, full_content, target_path)
                    raise FileChangedError(target_path, diff)
            else:
                raise FileChangedError(
                    target_path, f"File {target_path!r} does not exist."
                )
            return

        if mode == "write":
            self._backup_if_needed(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write(path, full_content)
            return

        raise ValueError(f"Unknown mode: {mode!r}")


class TestPrependMarker:
    def test_marker_prepended(self) -> None:
        result = Emitter._prepend_marker("hello")
        assert result.startswith(GENERATED_MARKER)
        assert "hello" in result


class TestHasMarker:
    def test_contains_marker(self) -> None:
        assert Emitter._has_marker(f"{GENERATED_MARKER}\ncontent")

    def test_missing_marker(self) -> None:
        assert not Emitter._has_marker("user content")


class TestAtomicWrite:
    def test_creates_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"
        Emitter._atomic_write(target, "atomic content")
        assert target.read_text(encoding="utf-8") == "atomic content"

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"
        target.write_text("old")
        Emitter._atomic_write(target, "new")
        assert target.read_text(encoding="utf-8") == "new"


class TestBackupIfNeeded:
    def test_no_backup_when_file_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "missing.txt"
        Emitter._backup_if_needed(target)
        assert not target.exists()

    def test_backup_user_file(self, tmp_path: Path) -> None:
        target = tmp_path / "user.txt"
        target.write_text("user content")
        Emitter._backup_if_needed(target)
        bak = tmp_path / "user.txt.bak"
        assert bak.exists()
        assert bak.read_text(encoding="utf-8") == "user content"
        assert not target.exists()

    def test_no_backup_for_generated_file(self, tmp_path: Path) -> None:
        target = tmp_path / "gen.txt"
        target.write_text(f"{GENERATED_MARKER}\ngenerated")
        Emitter._backup_if_needed(target)
        assert not (tmp_path / "gen.txt.bak").exists()
        assert target.exists()


class TestUnifiedDiff:
    def test_diff_output(self) -> None:
        diff = Emitter._unified_diff("a\n", "b\n", "/tmp/f")
        assert "--- /tmp/f" in diff
        assert "+++ /tmp/f" in diff
        assert "-a" in diff
        assert "+b" in diff


class TestConcreteEmitterModes:
    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        target = tmp_path / "dry.txt"
        emitter = ConcreteEmitter()
        emitter.emit_file(str(target), "content", "dry-run")
        assert not target.exists()

    def test_write_creates_file_with_marker(self, tmp_path: Path) -> None:
        target = tmp_path / "write.txt"
        emitter = ConcreteEmitter()
        emitter.emit_file(str(target), "content", "write")
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert text.startswith(GENERATED_MARKER)
        assert "content" in text

    def test_write_backs_up_user_file(self, tmp_path: Path) -> None:
        target = tmp_path / "existing.txt"
        target.write_text("user content")
        emitter = ConcreteEmitter()
        emitter.emit_file(str(target), "new content", "write")
        bak = tmp_path / "existing.txt.bak"
        assert bak.exists()
        assert bak.read_text(encoding="utf-8") == "user content"
        assert target.read_text(encoding="utf-8").startswith(GENERATED_MARKER)

    def test_write_does_not_backup_generated_file(self, tmp_path: Path) -> None:
        target = tmp_path / "existing.txt"
        target.write_text(f"{GENERATED_MARKER}\nold generated")
        emitter = ConcreteEmitter()
        emitter.emit_file(str(target), "new generated", "write")
        assert not (tmp_path / "existing.txt.bak").exists()
        assert target.read_text(encoding="utf-8").startswith(GENERATED_MARKER)

    def test_check_raises_when_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "missing.txt"
        emitter = ConcreteEmitter()
        with pytest.raises(FileChangedError, match="does not exist"):
            emitter.emit_file(str(target), "content", "check")

    def test_check_raises_when_drift(self, tmp_path: Path) -> None:
        target = tmp_path / "drift.txt"
        target.write_text(f"{GENERATED_MARKER}\nold")
        emitter = ConcreteEmitter()
        with pytest.raises(FileChangedError, match="---"):
            emitter.emit_file(str(target), "new", "check")

    def test_check_passes_when_unchanged(self, tmp_path: Path) -> None:
        target = tmp_path / "same.txt"
        emitter = ConcreteEmitter()
        emitter.emit_file(str(target), "same", "write")
        # Should not raise
        emitter.emit_file(str(target), "same", "check")

    def test_diff_raises_when_drift(self, tmp_path: Path) -> None:
        target = tmp_path / "diff.txt"
        target.write_text("old")
        emitter = ConcreteEmitter()
        with pytest.raises(FileChangedError, match="---"):
            emitter.emit_file(str(target), "new", "diff")

    def test_diff_passes_when_same(self, tmp_path: Path) -> None:
        target = tmp_path / "same.txt"
        emitter = ConcreteEmitter()
        emitter.emit_file(str(target), "same", "write")
        # Should not raise because on-disk matches generated content.
        emitter.emit_file(str(target), "same", "diff")

    def test_unknown_mode_raises(self, tmp_path: Path) -> None:
        emitter = ConcreteEmitter()
        with pytest.raises(ValueError, match="Unknown mode"):
            emitter.emit_file(str(tmp_path / "x"), "c", "nope")
