"""Tests for path traversal protection in laap.tools.file_safety.

Regression coverage for the prefix-match bypass where ``str.startswith``
 was used to enforce the allowed-directory sandbox. The check now uses
``Path.is_relative_to`` (Python 3.9+) plus a normcase-aware boundary
comparison so that sibling directories sharing a name prefix
(e.g. ``/allowed`` vs ``/allowed_secret``) cannot escape the sandbox.
"""
import os
from pathlib import Path

import pytest

from laap.tools.file_safety import (
    resolve_safe_path,
    safe_read,
    safe_write,
    _is_path_within,
)


# ── _is_path_within unit checks ──────────────────────────────────────────────

class TestIsPathWithin:
    def test_same_directory_is_within(self, tmp_path):
        assert _is_path_within(tmp_path, tmp_path) is True

    def test_nested_file_is_within(self, tmp_path):
        nested = tmp_path / "sub" / "file.txt"
        assert _is_path_within(nested, tmp_path) is True

    def test_prefix_sibling_is_not_within(self, tmp_path):
        """The core regression: /allowed must NOT match /allowed_secret."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        sibling = tmp_path / "allowed_secret"
        sibling.mkdir()
        victim = sibling / "file.txt"
        assert _is_path_within(victim, allowed) is False
        assert _is_path_within(sibling, allowed) is False

    def test_parent_is_not_within_child(self, tmp_path):
        child = tmp_path / "child"
        child.mkdir()
        # tmp_path is the parent of child; parent is NOT within child
        assert _is_path_within(tmp_path, child) is False

    def test_dotdot_traversal_rejected(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        # Build a path that climbs out of `allowed`
        escape = allowed / ".." / ".." / "etc" / "passwd"
        assert _is_path_within(escape, allowed) is False


# ── resolve_safe_path sandbox enforcement ────────────────────────────────────

class TestResolveSafePath:
    def test_legitimate_path_allowed(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        (allowed / "file.txt").write_text("ok")
        resolved, err = resolve_safe_path(
            str(allowed / "file.txt"), allowed_dirs={allowed}
        )
        assert err == ""
        assert resolved is not None
        assert resolved == (allowed / "file.txt").resolve()

    def test_prefix_sibling_bypass_rejected(self, tmp_path):
        """Attack: allowed_dir_secret shares prefix with allowed_dir.

        With the old ``str.startswith`` check this would be accepted,
        leaking files outside the sandbox.
        """
        allowed = tmp_path / "allowed_dir"
        allowed.mkdir()
        secret = tmp_path / "allowed_dir_secret"
        secret.mkdir()
        victim = secret / "secret.txt"
        victim.write_text("top secret")

        resolved, err = resolve_safe_path(
            str(victim), allowed_dirs={allowed}
        )
        assert resolved is None
        assert "outside allowed directories" in err

    def test_dotdot_escape_rejected(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "passwd").write_text("root:x:0:0")

        # /allowed/../../outside/passwd — but anchored at tmp_path
        escape = allowed / ".." / "outside" / "passwd"
        resolved, err = resolve_safe_path(str(escape), allowed_dirs={allowed})
        assert resolved is None
        assert "outside allowed directories" in err

    def test_dotdot_to_system_path_rejected(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        # Climb well above tmp_path; resolve() collapses the `..`
        escape = allowed / ".." / ".." / ".." / ".." / ".." / "etc" / "passwd"
        resolved, err = resolve_safe_path(str(escape), allowed_dirs={allowed})
        assert resolved is None
        assert "outside allowed directories" in err

    def test_subdirectory_path_allowed(self, tmp_path):
        allowed = tmp_path / "allowed"
        (allowed / "deep" / "nest").mkdir(parents=True)
        target = allowed / "deep" / "nest" / "file.txt"
        target.write_text("nested")
        resolved, err = resolve_safe_path(str(target), allowed_dirs={allowed})
        assert err == ""
        assert resolved == target.resolve()

    def test_trailing_separator_normalized(self, tmp_path):
        """allowed dir stored with trailing sep must still match."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        allowed_with_sep = Path(str(allowed) + os.sep)
        target = allowed / "file.txt"
        target.write_text("x")
        resolved, err = resolve_safe_path(
            str(target), allowed_dirs={allowed_with_sep}
        )
        assert err == ""
        assert resolved is not None

    def test_empty_allowed_dirs_allows_anything(self, tmp_path):
        """No sandbox configured → any resolvable path is accepted."""
        target = tmp_path / "free.txt"
        target.write_text("x")
        resolved, err = resolve_safe_path(str(target), allowed_dirs=set())
        assert err == ""
        assert resolved == target.resolve()

    def test_none_allowed_dirs_uses_global_default(self, tmp_path, monkeypatch):
        """When allowed_dirs is None, the global default is consulted."""
        from laap.tools import file_safety as fs
        monkeypatch.setattr(fs, "_DEFAULT_ALLOWED_DIRS", set())
        target = tmp_path / "anywhere.txt"
        target.write_text("x")
        # Empty global default → no restriction
        resolved, err = resolve_safe_path(str(target), allowed_dirs=None)
        assert err == ""
        assert resolved == target.resolve()

    def test_relative_path_resolved_against_cwd(self, tmp_path, monkeypatch):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        (allowed / "rel.txt").write_text("x")
        # chdir into allowed and reference a relative file
        monkeypatch.chdir(allowed)
        resolved, err = resolve_safe_path("rel.txt", allowed_dirs={allowed})
        assert err == ""
        assert resolved == (allowed / "rel.txt").resolve()

    def test_empty_string_path_handled(self, tmp_path, monkeypatch):
        """An empty path resolves to cwd; it must not crash.

        With cwd inside the allowed dir it is accepted; with cwd outside
        it is rejected. Either way the function returns a clean tuple.
        """
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        monkeypatch.chdir(allowed)
        resolved, err = resolve_safe_path("", allowed_dirs={allowed})
        assert err == ""
        assert resolved == allowed.resolve()


# ── Windows-specific case-insensitivity ──────────────────────────────────────

@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows case-insensitive path semantics",
)
class TestWindowsCaseSensitivity:
    def test_case_insensitive_match(self, tmp_path):
        allowed = tmp_path / "Allowed"
        allowed.mkdir()
        target = allowed / "File.txt"
        target.write_text("x")
        # Reference the dir with different casing
        resolved, err = resolve_safe_path(
            str(allowed / "FILE.TXT"), allowed_dirs={Path(str(allowed).upper())}
        )
        assert err == ""
        assert resolved is not None

    def test_drive_letter_case_difference(self, tmp_path):
        # tmp_path typically under C:\... ; ensure drive letter case-insensitive
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        target = allowed / "f.txt"
        target.write_text("x")
        # Flip drive letter case if present
        allowed_str = str(allowed)
        if len(allowed_str) >= 2 and allowed_str[1] == ":":
            flipped = allowed_str[0].swapcase() + allowed_str[1:]
            resolved, err = resolve_safe_path(
                str(target), allowed_dirs={Path(flipped)}
            )
            assert err == "", f"Drive letter case should not matter: {err}"
            assert resolved is not None


# ── Symlink-based escape ─────────────────────────────────────────────────────

class TestSymlinkEscape:
    def test_symlink_pointing_outside_rejected(self, tmp_path):
        """A symlink inside the sandbox pointing outside must be rejected.

        Path.resolve() follows the link, so the resolved real path lands
        outside the allowed dir and is blocked by the traversal check.
        """
        if os.name == "nt" and not hasattr(os, "symlink"):
            pytest.skip("symlinks not available on this Windows build")
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("leaked")

        link = allowed / "link.txt"
        try:
            os.symlink(outside / "secret.txt", link)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlink")

        resolved, err = resolve_safe_path(str(link), allowed_dirs={allowed})
        assert resolved is None
        assert "outside allowed directories" in err

    def test_symlink_pointing_inside_allowed(self, tmp_path):
        if os.name == "nt" and not hasattr(os, "symlink"):
            pytest.skip("symlinks not available on this Windows build")
        allowed = tmp_path / "allowed"
        (allowed / "data").mkdir(parents=True)
        (allowed / "data" / "real.txt").write_text("ok")

        link = allowed / "link.txt"
        try:
            os.symlink(allowed / "data" / "real.txt", link)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlink")

        resolved, err = resolve_safe_path(str(link), allowed_dirs={allowed})
        assert err == ""
        assert resolved is not None

    def test_symlink_dir_pointing_outside_rejected(self, tmp_path):
        if os.name == "nt" and not hasattr(os, "symlink"):
            pytest.skip("symlinks not available on this Windows build")
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("leaked")

        link_dir = allowed / "escape"
        try:
            os.symlink(outside, link_dir)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlink")

        target = link_dir / "secret.txt"
        resolved, err = resolve_safe_path(str(target), allowed_dirs={allowed})
        assert resolved is None
        assert "outside allowed directories" in err


# ── Integration with safe_read / safe_write ─────────────────────────────────

class TestSafeOpsEnforceSandbox:
    def test_safe_read_blocks_escape(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        secret = tmp_path / "allowed_secret"
        secret.mkdir()
        (secret / "f.txt").write_text("nope")

        content, err = safe_read(
            str(secret / "f.txt"), allowed_dirs={allowed}
        )
        assert content is None
        assert "outside allowed directories" in err

    def test_safe_read_allows_inside(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        (allowed / "f.txt").write_text("hello")

        content, err = safe_read(
            str(allowed / "f.txt"), allowed_dirs={allowed}
        )
        assert err == ""
        assert content == "hello"

    def test_safe_write_blocks_escape(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        secret = tmp_path / "allowed_secret"
        secret.mkdir()

        ok, err = safe_write(
            str(secret / "f.txt"), "payload", allowed_dirs={allowed}
        )
        assert ok is False
        assert "outside allowed directories" in err
        # Ensure nothing was written
        assert not (secret / "f.txt").exists()

    def test_safe_write_allows_inside(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        ok, err = safe_write(
            str(allowed / "f.txt"), "payload", allowed_dirs={allowed},
            create_backup=False,
        )
        assert ok is True
        assert (allowed / "f.txt").read_text() == "payload"
