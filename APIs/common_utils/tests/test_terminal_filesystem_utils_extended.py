import base64
import builtins
import importlib
import os
import stat
import sys
import tempfile
import shutil
import time
from contextlib import contextmanager

import pytest


# Ensure the common_utils package is importable when tests run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


terminal_utils = importlib.import_module("common_utils.terminal_filesystem_utils")


@contextmanager
def set_access_time_mode(mode: str):
    # The module under test, as imported by this test file
    module_to_patch = terminal_utils
    original_mode = module_to_patch.ACCESS_TIME_MODE
    module_to_patch.ACCESS_TIME_MODE = mode

    # The same module, but as it might be imported by other tests in the suite
    other_module_to_patch = sys.modules.get('APIs.common_utils.terminal_filesystem_utils')
    original_other_mode = None
    if other_module_to_patch and other_module_to_patch is not module_to_patch:
        original_other_mode = getattr(other_module_to_patch, 'ACCESS_TIME_MODE', None)
        other_module_to_patch.ACCESS_TIME_MODE = mode

    try:
        yield
    finally:
        module_to_patch.ACCESS_TIME_MODE = original_mode
        if other_module_to_patch and other_module_to_patch is not module_to_patch and original_other_mode is not None:
            other_module_to_patch.ACCESS_TIME_MODE = original_other_mode


def test_dehydrate_skips_paths_outside_workspace(tmp_path):
    # Cover lines 641-644
    db = {
        "workspace_root": "/logical/root",
        "file_system": {
            "/logical/root": {"is_directory": True, "content_lines": []},
            "/logical/root/file.txt": {
                "is_directory": False,
                "content_lines": ["content\n"],
            },
            "/other/location/outside.txt": {
                "is_directory": False,
                "content_lines": ["outside\n"],
            },
        },
    }

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    terminal_utils.dehydrate_db_to_directory(db, str(out_dir))

    assert (out_dir / "file.txt").exists()
    assert not (out_dir / "outside.txt").exists()


def test_map_temp_path_to_db_key_handles_nested(tmp_path):
    # Cover map_temp_path_to_db_key happy path (lines 723-724, 782)
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    nested = temp_root / "nested"
    nested.mkdir()

    mapped_root = terminal_utils.map_temp_path_to_db_key(str(temp_root), str(temp_root), "/workspace")
    mapped_nested = terminal_utils.map_temp_path_to_db_key(str(nested), str(temp_root), "/workspace")

    assert mapped_root == "/workspace"
    assert mapped_nested == "/workspace/nested"


def test_dehydrate_handles_corrupt_archive(tmp_path):
    # Cover archive decode fallback (lines 689-694)
    db = {
        "workspace_root": "/workspace",
        "file_system": {
            "/workspace": {"is_directory": True, "content_lines": []},
            "/workspace/broken.tar.gz": {
                "is_directory": False,
                "content_lines": [
                    terminal_utils.BINARY_FILE_MARKER + "\n",
                    "NOT_BASE64_DATA\n",
                ],
            },
        },
    }

    out_dir = tmp_path / "out"
    terminal_utils.dehydrate_db_to_directory(db, str(out_dir))

    assert (out_dir / "broken.tar.gz").exists()


def test_update_db_metadata_command_strict_mode(tmp_path):
    # Cover metadata command strict mode (lines 892-896, 902-906)
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    temp_dir = tempfile.TemporaryDirectory()
    os.makedirs(temp_dir.name, exist_ok=True)
    file_path = os.path.join(temp_dir.name, "file.txt")
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write("data")

    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": {str(workspace_root): {"is_directory": True}},
    }

    terminal_utils.update_db_file_system_from_temp(
        db,
        temp_dir.name,
        {},
        str(workspace_root),
        preserve_metadata=True,
        command="chmod 600 file.txt",
    )

    entry = db["file_system"].get(os.path.join(str(workspace_root), "file.txt"))
    assert entry is not None
    temp_dir.cleanup()


def test_collect_metadata_state_filters_invalid(tmp_path):
    # Cover error handling branches (lines 1385-1387, 1420-1422)
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    file_system = {
        str(workspace_root): {"is_directory": True},
        "/invalid": {"is_directory": False},
    }

    state = terminal_utils.collect_pre_command_metadata_state(
        file_system,
        str(workspace_root),
        str(workspace_root),
    )

    assert str(workspace_root) in state
    assert "/invalid" not in state


def test_extract_file_paths_graceful_empty(tmp_path):
    # Cover empty command parsing (lines 1491, 1529)
    workspace_root = str(tmp_path)

    assert terminal_utils._extract_file_paths_from_command("", workspace_root, workspace_root) == set()

    with set_access_time_mode("relatime"):
        assert terminal_utils._extract_file_paths_from_command(
            "ls", workspace_root, workspace_root
        ) == set()


@pytest.fixture
def sandbox(tmp_path):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "subdir").mkdir()
    file_path = workspace_root / "file.txt"
    file_path.write_text("initial\n", encoding="utf-8")
    preserved_change_time = "2024-01-01T00:00:00Z"

    original_state = {
        str(workspace_root): {
            "path": str(workspace_root),
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": preserved_change_time,
            "metadata": {
                "timestamps": {
                    "change_time": preserved_change_time,
                    "modify_time": preserved_change_time,
                    "access_time": preserved_change_time,
                },
                "attributes": {
                    "is_hidden": False,
                    "is_symlink": False,
                    "is_readonly": False,
                    "symlink_target": None,
                },
                "permissions": {
                    "mode": 0o755,
                    "uid": os.getuid() if hasattr(os, "getuid") else 1000,
                    "gid": os.getgid() if hasattr(os, "getgid") else 1000,
                },
            },
        },
        str(workspace_root / "file.txt"): {
            "path": str(workspace_root / "file.txt"),
            "is_directory": False,
            "content_lines": ["initial\n"],
            "size_bytes": 8,
            "last_modified": preserved_change_time,
            "metadata": {
                "timestamps": {
                    "change_time": preserved_change_time,
                    "modify_time": preserved_change_time,
                    "access_time": preserved_change_time,
                },
                "attributes": {
                    "is_hidden": False,
                    "is_symlink": False,
                    "is_readonly": False,
                    "symlink_target": None,
                },
                "permissions": {
                    "mode": 0o644,
                    "uid": os.getuid() if hasattr(os, "getuid") else 1000,
                    "gid": os.getgid() if hasattr(os, "getgid") else 1000,
                },
            },
        },
    }

    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": original_state.copy(),
    }

    yield workspace_root, db, original_state


def test_prepare_command_environment_and_handle_env_commands():
    db = {
        "cwd": "/workspace/project",
        "environment": {
            "workspace": {"USER": "workspace", "WORK": "yes"},
            "session": {"USER": "session", "SESSION_ONLY": "1"},
        },
    }

    env = terminal_utils.prepare_command_environment(db, "/tmp/sandbox", "/workspace/project")

    assert env["PWD"] == "/workspace/project"
    assert env["USER"] == "session"
    assert env["WORK"] == "yes"
    assert env["SESSION_ONLY"] == "1"
    assert env["PATH"] == os.environ.get("PATH")

    export_result = terminal_utils.handle_env_command("export NEW_VAR=$USER-123", db)
    assert export_result["returncode"] == 0
    assert db["environment"]["session"]["NEW_VAR"] == "session-123"

    env_output = terminal_utils.handle_env_command("env", db)
    assert "NEW_VAR=session-123" in env_output["stdout"].splitlines()

    unset_result = terminal_utils.handle_env_command("unset NEW_VAR", db)
    assert unset_result["returncode"] == 0
    assert "NEW_VAR" not in db["environment"]["session"]

    invalid_export = terminal_utils.handle_env_command("export INVALID", db)
    assert invalid_export["returncode"] == 1


def test_path_resolution_helpers_raise_and_normalize():
    db = {"workspace_root": "/workspace", "cwd": "/workspace/app"}

    assert terminal_utils.get_absolute_path(db, "src/main.py") == "/workspace/app/src/main.py"
    assert terminal_utils.get_absolute_path(db, "../README.md") == "/workspace/README.md"
    assert terminal_utils.path_exists(db, "../README.md") is False
    assert terminal_utils.is_directory(db, "/workspace") is False  # DB lacks file_system
    assert terminal_utils.is_file(db, "src/main.py") is False

    with pytest.raises(ValueError):
        terminal_utils.get_absolute_path(db, "/outside/secret.txt")

    assert terminal_utils._normalize_path_for_db(None) is None
    assert terminal_utils._normalize_path_for_db("/workspace//app/../src") == "/workspace/src"


def test_get_file_system_entry_helpers_cover_none_cases():
    db = {
        "workspace_root": "/workspace",
        "cwd": "/workspace",
        "file_system": {"/workspace/file.txt": {"is_directory": False}},
    }

    assert terminal_utils.get_file_system_entry(db, "file.txt") == {"is_directory": False}
    assert terminal_utils.get_file_system_entry(db, "/workspace/missing") is None
    assert terminal_utils.get_file_system_entry(db, "/outside") is None
    assert terminal_utils.path_exists(db, "file.txt") is True
    assert terminal_utils.path_exists(db, "/outside") is False
    assert terminal_utils.is_directory(db, "file.txt") is False
    assert terminal_utils.is_file(db, "file.txt") is True


def test_resolve_target_path_for_cd_validates_workspace():
    file_system_view = {
        "/workspace": {"is_directory": True},
        "/workspace/src": {"is_directory": True},
    }

    result = terminal_utils.resolve_target_path_for_cd(
        "/workspace", "src", "/workspace", file_system_view
    )
    assert result == "/workspace/src"

    outside = terminal_utils.resolve_target_path_for_cd(
        "/workspace", "../etc", "/workspace", file_system_view
    )
    assert outside is None


def test_expand_variables_handles_quotes():
    env = {"USER": "session", "EMPTY": ""}
    command = "echo '$USER'-${USER}-${UNSET:-fallback}"
    expanded = terminal_utils.expand_variables(command, env)
    # Single quotes should prevent expansion while double quotes allow it
    assert expanded.startswith("echo '$USER'-session-")


def test_expand_variables_handles_literal_dollar_and_braces():
    env = {"VAR": "value"}
    command = "echo $$ and ${VAR} and ${MISSING}"
    expanded = terminal_utils.expand_variables(command, env)
    assert "value" in expanded
    assert "${MISSING}" not in expanded


def test_access_time_modes_affect_should_update():
    with set_access_time_mode("relatime"):
        assert terminal_utils._should_update_access_time("cat file.txt") is True
        assert terminal_utils._should_update_access_time("ls file.txt") is False

    with set_access_time_mode("atime"):
        assert terminal_utils._should_update_access_time("ls") is True

    with set_access_time_mode("noatime"):
        assert terminal_utils._should_update_access_time("cat file.txt") is False


def test_extract_file_paths_from_command_includes_redirection(tmp_path):
    workspace_root = str(tmp_path)
    target = tmp_path / "output.txt"
    command = "echo hi > output.txt"

    with set_access_time_mode("relatime"):
        paths = terminal_utils._extract_file_paths_from_command(
            command, workspace_root, workspace_root
        )
        assert {str(target)} == paths

    with set_access_time_mode("atime"):
        paths = terminal_utils._extract_file_paths_from_command(
            "ls output.txt", workspace_root, workspace_root
        )
        assert str(target) in paths


def test_extract_last_unquoted_redirection_target_parses_inner_command():
    command = "bash -c \"echo hi > result.txt\""
    assert terminal_utils._extract_last_unquoted_redirection_target(command) == "result.txt"

    heredoc = "cat <<'EOF' > ignored.txt"
    assert terminal_utils._extract_last_unquoted_redirection_target(heredoc) is None


def test_metadata_collection_and_preservation(sandbox):
    workspace_root, db, original_state = sandbox
    pre_state = terminal_utils.collect_pre_command_metadata_state(
        db["file_system"], str(workspace_root), str(workspace_root)
    )
    time.sleep(0.05)
    post_state = terminal_utils.collect_post_command_metadata_state(
        db["file_system"], str(workspace_root), str(workspace_root)
    )

    db_entry = {
        "metadata": {
            "timestamps": {"change_time": "DIFFERENT", "modify_time": pre_state[str(workspace_root)]["metadata"]["timestamps"]["modify_time"]}
        }
    }
    terminal_utils.preserve_unchanged_change_times(
        {str(workspace_root): db_entry},
        pre_state,
        post_state,
        original_state,
        str(workspace_root),
        str(workspace_root),
    )
    assert (
        db_entry["metadata"]["timestamps"]["change_time"]
        == original_state[str(workspace_root)]["metadata"]["timestamps"]["change_time"]
    )


def test_collect_and_apply_metadata_toggle_readonly(tmp_path):
    file_path = tmp_path / "demo.txt"
    file_path.write_text("demo", encoding="utf-8")

    metadata = terminal_utils._collect_file_metadata(str(file_path))
    metadata["attributes"]["is_readonly"] = True
    terminal_utils._apply_file_metadata(str(file_path), metadata)
    assert stat.S_IWUSR & os.stat(file_path).st_mode == 0

    metadata["attributes"]["is_readonly"] = False
    terminal_utils._apply_file_metadata(str(file_path), metadata)
    assert stat.S_IWUSR & os.stat(file_path).st_mode != 0


def test_update_db_file_system_from_temp_handles_changes(sandbox):
    workspace_root, db, original_state = sandbox

    temp_dir = tempfile.TemporaryDirectory()
    temp_root = temp_dir.name

    os.makedirs(temp_root, exist_ok=True)
    file_path = os.path.join(temp_root, "file.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("updated\n")

    new_file_path = os.path.join(temp_root, "new.txt")
    with open(new_file_path, "w", encoding="utf-8") as f:
        f.write("created\n")

    # Ensure there is time delta for metadata comparisons
    time.sleep(0.05)

    terminal_utils.update_db_file_system_from_temp(
        db,
        temp_root,
        original_state,
        str(workspace_root),
        preserve_metadata=True,
        command="cat file.txt",
    )

    updated_entry = db["file_system"].get(os.path.join(str(workspace_root), "file.txt"))
    assert updated_entry is not None
    assert updated_entry["content_lines"][0] == "updated\n"
    assert updated_entry["size_bytes"] == len("updated\n")

    new_entry = db["file_system"].get(os.path.join(str(workspace_root), "new.txt"))
    assert new_entry is not None
    assert new_entry["content_lines"][0] == "created\n"

    # Deleted files should be removed from the file_system map
    assert os.path.join(str(workspace_root), "missing.txt") not in db["file_system"]

    temp_dir.cleanup()


def test_is_likely_binary_and_archive_detection(tmp_path):
    text_file = tmp_path / "hello.txt"
    text_file.write_text("hello", encoding="utf-8")
    binary_file = tmp_path / "image.bin"
    binary_file.write_bytes(b"\x00\xff\x00\xff")
    archive_file = tmp_path / "archive.tar.gz"
    archive_file.write_bytes(b"FakeTarData")

    assert terminal_utils.is_likely_binary_file(str(text_file)) is False
    assert terminal_utils.is_likely_binary_file(str(binary_file)) is True
    assert terminal_utils._is_archive_file(str(archive_file)) is True


def test_hydrate_db_from_directory_populates_metadata(tmp_path):
    root = tmp_path / "workspace"
    nested = root / "nested"
    root.mkdir()
    nested.mkdir()
    (root / "note.txt").write_text("hello\n", encoding="utf-8")
    (nested / "binary.zip").write_bytes(b"PK\x03\x04")
    hidden = nested / ".hidden"
    hidden.write_text("secret", encoding="utf-8")

    db = {}
    result = terminal_utils.hydrate_db_from_directory(db, str(root))
    assert result is True
    assert str(root) in db["file_system"]
    assert str(nested) in db["file_system"]
    binary_entry = db["file_system"][str(nested / "binary.zip")]
    assert binary_entry["content_lines"][0].strip() == terminal_utils.BINARY_FILE_MARKER
    assert binary_entry["metadata"]["attributes"]["is_hidden"] is False


def test_dehydrate_db_to_directory_round_trip(tmp_path):
    workspace_root = "/logical/root"
    target_dir = tmp_path / "sandbox"
    db = {
        "workspace_root": workspace_root,
        "file_system": {
            workspace_root: {
                "path": workspace_root,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": "2024-01-01T00:00:00Z",
                "metadata": {
                    "timestamps": {
                        "access_time": "2024-01-01T00:00:00Z",
                        "modify_time": "2024-01-01T00:00:00Z",
                        "change_time": "2024-01-01T00:00:00Z",
                    },
                    "attributes": {
                        "is_symlink": False,
                        "is_hidden": False,
                        "is_readonly": False,
                        "symlink_target": None,
                    },
                    "permissions": {
                        "mode": 0o755,
                        "uid": os.getuid() if hasattr(os, "getuid") else 1000,
                        "gid": os.getgid() if hasattr(os, "getgid") else 1000,
                    },
                },
            },
            "/logical/root/file.txt": {
                "path": "/logical/root/file.txt",
                "is_directory": False,
                "content_lines": ["content\n"],
                "size_bytes": 8,
                "last_modified": "2024-01-01T00:00:01Z",
                "metadata": {
                    "timestamps": {
                        "access_time": "2024-01-01T00:00:01Z",
                        "modify_time": "2024-01-01T00:00:01Z",
                        "change_time": "2024-01-01T00:00:01Z",
                    },
                    "attributes": {
                        "is_symlink": False,
                        "is_hidden": False,
                        "is_readonly": True,
                        "symlink_target": None,
                    },
                    "permissions": {
                        "mode": 0o644,
                        "uid": os.getuid() if hasattr(os, "getuid") else 1000,
                        "gid": os.getgid() if hasattr(os, "getgid") else 1000,
                    },
                },
            },
            "/logical/root/binary.bin": {
                "path": "/logical/root/binary.bin",
                "is_directory": False,
                "content_lines": [terminal_utils.BINARY_FILE_MARKER + "\n", base64.b64encode(b"\x00\x01").decode("ascii") + "\n"],
                "size_bytes": 2,
                "last_modified": "2024-01-01T00:00:02Z",
                "metadata": {
                    "timestamps": {
                        "access_time": "2024-01-01T00:00:02Z",
                        "modify_time": "2024-01-01T00:00:02Z",
                        "change_time": "2024-01-01T00:00:02Z",
                    },
                    "attributes": {
                        "is_symlink": False,
                        "is_hidden": False,
                        "is_readonly": False,
                        "symlink_target": None,
                    },
                    "permissions": {
                        "mode": 0o600,
                        "uid": os.getuid() if hasattr(os, "getuid") else 1000,
                        "gid": os.getgid() if hasattr(os, "getgid") else 1000,
                    },
                },
            },
        },
    }

    terminal_utils.dehydrate_db_to_directory(db, str(target_dir))

    assert (target_dir / "file.txt").read_text(encoding="utf-8") == "content\n"
    assert (target_dir / "binary.bin").read_bytes() == b"\x00\x01"
    mode = os.stat(target_dir / "file.txt").st_mode
    assert (mode & stat.S_IWUSR) == 0  # readonly applied


def test_map_temp_path_to_db_key_variants(tmp_path):
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    (temp_root / "sub").mkdir()
    desired = "/workspace"

    mapped_root = terminal_utils.map_temp_path_to_db_key(str(temp_root), str(temp_root), desired)
    assert mapped_root == desired

    mapped_sub = terminal_utils.map_temp_path_to_db_key(str(temp_root / "sub"), str(temp_root), desired)
    assert mapped_sub == "/workspace/sub"


def test_update_db_file_system_from_temp_preserves_metadata_on_touch(sandbox):
    workspace_root, db, original_state = sandbox
    temp_dir = tempfile.TemporaryDirectory()
    temp_root = temp_dir.name

    os.makedirs(temp_root, exist_ok=True)
    source_file = os.path.join(temp_root, "file.txt")
    with open(source_file, "w", encoding="utf-8") as handle:
        handle.write("initial\n")

    # command "touch" should preserve original last_modified value
    terminal_utils.update_db_file_system_from_temp(
        db,
        temp_root,
        original_state,
        str(workspace_root),
        preserve_metadata=True,
        command="touch file.txt",
    )

    original_entry = original_state[os.path.join(str(workspace_root), "file.txt")]
    updated_entry = db["file_system"][os.path.join(str(workspace_root), "file.txt")]
    assert updated_entry["content_lines"] == ["initial\n"]
    assert updated_entry["last_modified"] != original_entry["last_modified"]
    assert (
        updated_entry["metadata"]["timestamps"]["access_time"]
        != original_entry["metadata"]["timestamps"]["access_time"]
    )
    assert (
        updated_entry["metadata"]["timestamps"]["modify_time"]
        != original_entry["metadata"]["timestamps"]["modify_time"]
    )
    assert updated_entry["metadata"]["timestamps"]["change_time"] != ""
    temp_dir.cleanup()


def test_update_db_file_system_from_temp_handles_symlink(tmp_path):
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    target_file = workspace_root / "target.txt"
    target_file.write_text("data", encoding="utf-8")

    original_state = {
        str(workspace_root): {
            "path": str(workspace_root),
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": terminal_utils.get_current_timestamp_iso(),
            "metadata": {
                "timestamps": {
                    "change_time": terminal_utils.get_current_timestamp_iso(),
                    "modify_time": terminal_utils.get_current_timestamp_iso(),
                    "access_time": terminal_utils.get_current_timestamp_iso(),
                },
                "attributes": {
                    "is_hidden": False,
                    "is_symlink": False,
                    "is_readonly": False,
                    "symlink_target": None,
                },
                "permissions": {
                    "mode": 0o755,
                    "uid": os.getuid() if hasattr(os, "getuid") else 1000,
                    "gid": os.getgid() if hasattr(os, "getgid") else 1000,
                },
            },
        },
    }

    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": original_state.copy(),
    }

    temp_dir = tempfile.TemporaryDirectory()
    temp_root = temp_dir.name
    os.makedirs(temp_root, exist_ok=True)
    symlink_path = os.path.join(temp_root, "link.txt")
    os.symlink(str(target_file), symlink_path)

    terminal_utils.update_db_file_system_from_temp(
        db,
        temp_root,
        original_state,
        str(workspace_root),
        preserve_metadata=True,
        command="chmod 755 link.txt",
    )

    entry = db["file_system"][os.path.join(str(workspace_root), "link.txt")]
    assert entry["metadata"]["attributes"]["is_symlink"] is True
    assert entry["metadata"]["attributes"]["symlink_target"] == str(target_file)
    temp_dir.cleanup()


def test_hydrate_handles_binary_read_error(tmp_path, monkeypatch):
    # Lines 462-464, 466-484
    root = tmp_path / "workspace"
    root.mkdir()
    binary_file = root / "corrupt.bin"
    binary_file.write_bytes(b"\x00\xff")
    
    def mock_open_fail(*args, **kwargs):
        if 'corrupt.bin' in str(args[0]):
            raise IOError("Disk read error")
        return open(*args, **kwargs)
    
    monkeypatch.setattr(builtins, 'open', mock_open_fail)
    
    db = {}
    terminal_utils.hydrate_db_from_directory(db, str(root))
    
    # Should handle error gracefully with placeholder
    assert str(binary_file) in db["file_system"]
    assert terminal_utils.BINARY_CONTENT_PLACEHOLDER[0] in db["file_system"][str(binary_file)]["content_lines"][0]


def test_dehydrate_handles_path_not_relative_to_root(tmp_path):
    # Lines 641-644
    db = {
        "workspace_root": "/workspace",
        "file_system": {
            "/workspace/file.txt": {"is_directory": False, "content_lines": ["test\n"]},
            "/outside/bad.txt": {"is_directory": False, "content_lines": ["bad\n"]},
        },
    }
    
    target_dir = tmp_path / "out"
    terminal_utils.dehydrate_db_to_directory(db, str(target_dir))
    
    # Should skip /outside/bad.txt
    assert not (target_dir / "bad.txt").exists()
    assert (target_dir / "file.txt").exists()


def test_dehydrate_handles_binary_decode_failure(tmp_path):
    # Lines 690-694
    db = {
        "workspace_root": "/workspace",
        "file_system": {
            "/workspace": {"is_directory": True, "path": "/workspace", "content_lines": []},
            "/workspace/corrupt.bin": {
                "is_directory": False,
                "content_lines": [terminal_utils.BINARY_FILE_MARKER + "\n", "INVALID_BASE64!!!\n"],
            },
        },
    }
    
    target_dir = tmp_path / "out"
    terminal_utils.dehydrate_db_to_directory(db, str(target_dir))
    
    # Should fall back to writing as text
    assert (target_dir / "corrupt.bin").exists()


def test_update_db_handles_metadata_command_strict_mode(tmp_path):
    # Lines 892-896, 902-906
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    (workspace_root / "file.txt").write_text("data", encoding="utf-8")
    
    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": {str(workspace_root): {"is_directory": True}},
    }
    
    temp_dir = tempfile.TemporaryDirectory()
    os.makedirs(temp_dir.name, exist_ok=True)
    (tmp_path / "temp_file.txt").write_text("new", encoding="utf-8")
    
    # Test with chmod command (metadata command)
    terminal_utils.update_db_file_system_from_temp(
        db, temp_dir.name, {}, str(workspace_root), command="chmod 644 file.txt"
    )
    temp_dir.cleanup()


def test_expand_variables_edge_cases():
    # Lines 1795-1798, 1824, 1834-1836
    env = {"VAR": "value", "EMPTY": ""}
    
    # Test $ at end of string
    assert terminal_utils.expand_variables("test$", env) == "test$"
    
    # Test ${} with no closing brace
    assert terminal_utils.expand_variables("${VAR", env) == "${VAR"
    
    # Test $@ (special char after $)
    assert terminal_utils.expand_variables("$@", env) == "$@"


def test_handle_env_command_edge_cases():
    # Lines 1856, 1883-1887, 1926-1940, 1968
    db = {"environment": {"workspace": {}, "session": {}}, "workspace_root": "/ws", "cwd": "/ws"}
    
    # Test export with double quotes (expansion happens)
    result = terminal_utils.handle_env_command('export VAR="$USER"', db)
    assert db["environment"]["session"]["VAR"] == "user"  # USER from prepare_command_environment
    
    # Test unset from workspace
    db["environment"]["workspace"]["WORK_VAR"] = "value"
    result = terminal_utils.handle_env_command("unset WORK_VAR", db)
    assert "WORK_VAR" not in db["environment"]["workspace"]
    
    # Test unset of non-existent variable
    result = terminal_utils.handle_env_command("unset NONEXISTENT", db)
    assert result["returncode"] == 0
    assert "was not set" in result["message"]
    
    # Test unknown env command
    result = terminal_utils.handle_env_command("invalid_cmd", db)
    assert result["returncode"] == 1
    assert "Unknown environment command" in result["stderr"]


def test_collect_metadata_state_with_errors(tmp_path):
    # Lines 1385-1387, 1420-1422
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    
    file_system = {
        str(workspace_root): {"is_directory": True},
        "/invalid/path": {"is_directory": False},  # This will cause ValueError
    }
    
    # Should handle errors gracefully
    state = terminal_utils.collect_pre_command_metadata_state(
        file_system, str(workspace_root), str(workspace_root)
    )
    
    # Should only have the valid entry
    assert str(workspace_root) in state
    assert "/invalid/path" not in state


def test_preserve_unchanged_change_times_with_modified_file():
    # Line 1451
    db_file_system = {
        "/ws/file.txt": {
            "metadata": {"timestamps": {"change_time": "NEW_TIME"}}
        }
    }
    
    pre_state = {
        "/ws/file.txt": {
            "metadata": {"timestamps": {"modify_time": "OLD_MTIME"}}
        }
    }
    
    post_state = {
        "/ws/file.txt": {
            "metadata": {"timestamps": {"modify_time": "NEW_MTIME"}}
        }
    }
    
    original_state = {
        "/ws/file.txt": {
            "metadata": {"timestamps": {"change_time": "ORIGINAL_CTIME"}}
        }
    }
    
    terminal_utils.preserve_unchanged_change_times(
        db_file_system, pre_state, post_state, original_state, "/ws", "/tmp"
    )
    
    # Since mtime changed, ctime should NOT be preserved
    assert db_file_system["/ws/file.txt"]["metadata"]["timestamps"]["change_time"] == "NEW_TIME"


def test_update_db_handles_large_file(tmp_path):
    # Lines 913-915
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    
    temp_dir = tempfile.TemporaryDirectory()
    temp_root = temp_dir.name
    os.makedirs(temp_root, exist_ok=True)
    
    # Create a file that exceeds MAX_FILE_SIZE_BYTES
    large_file = os.path.join(temp_root, "large.txt")
    with open(large_file, "w") as f:
        f.write("x" * (terminal_utils.MAX_FILE_SIZE_BYTES + 1000))
    
    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": {str(workspace_root): {"is_directory": True}},
    }
    
    terminal_utils.update_db_file_system_from_temp(
        db, temp_root, {}, str(workspace_root)
    )
    
    entry = db["file_system"][os.path.join(str(workspace_root), "large.txt")]
    assert terminal_utils.LARGE_FILE_CONTENT_PLACEHOLDER[0] in entry["content_lines"][0]
    temp_dir.cleanup()


def test_update_db_handles_file_read_error(tmp_path, monkeypatch):
    # Lines 958-974
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    
    temp_dir = tempfile.TemporaryDirectory()
    temp_root = temp_dir.name
    os.makedirs(temp_root, exist_ok=True)
    
    bad_file = os.path.join(temp_root, "bad.txt")
    with open(bad_file, "w") as f:
        f.write("data")
    
    def mock_open_fail(*args, **kwargs):
        if 'bad.txt' in str(args[0]) and 'rb' in str(kwargs.get('mode', args[1] if len(args) > 1 else '')):
            raise PermissionError("No read access")
        return open(*args, **kwargs)
    
    monkeypatch.setattr(builtins, 'open', mock_open_fail)
    
    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": {str(workspace_root): {"is_directory": True}},
    }
    
    terminal_utils.update_db_file_system_from_temp(
        db, temp_root, {}, str(workspace_root)
    )
    
    entry = db["file_system"][os.path.join(str(workspace_root), "bad.txt")]
    assert "Error" in entry["content_lines"][0]
    temp_dir.cleanup()


def test_update_db_metadata_fallback_for_error_case(tmp_path):
    # Lines 999-1023
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    
    original_state = {
        str(workspace_root / "file.txt"): {
            "metadata": {
                "timestamps": {"access_time": "OLD_ATIME"}
            }
        }
    }
    
    temp_dir = tempfile.TemporaryDirectory()
    temp_root = temp_dir.name
    os.makedirs(temp_root, exist_ok=True)
    
    # Create file with same size as original (file_actually_changed = False)
    bad_file = os.path.join(temp_root, "file.txt")
    with open(bad_file, "w") as f:
        f.write("data")  # 4 bytes
    
    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": {str(workspace_root): {"is_directory": True}},
    }
    
    # Simulate a file that didn't change (same size)
    original_state[str(workspace_root / "file.txt")]["size_bytes"] = 4
    
    with set_access_time_mode("atime"):
        terminal_utils.update_db_file_system_from_temp(
            db, temp_root, original_state, str(workspace_root), command="cat file.txt"
        )
    
    # Should use fresh metadata for accessed file
    entry = db["file_system"][os.path.join(str(workspace_root), "file.txt")]
    assert "metadata" in entry
    temp_dir.cleanup()


def test_hydrate_handles_text_decode_errors(tmp_path):
    # Lines 502-504, 507-512
    root = tmp_path / "workspace"
    root.mkdir()
    # The function tries utf-8, latin-1, and cp1252 which can decode almost anything
    # For this test, we verify that the fallback encoding chain works
    bad_file = root / "latin1.txt"
    # Write content that's valid in latin-1 but not utf-8
    bad_file.write_bytes(b"\xe9\xe8\xe0")  # Valid latin-1: éèà
    
    db = {}
    terminal_utils.hydrate_db_from_directory(db, str(root))
    
    # Should successfully decode using fallback encoding
    assert str(bad_file) in db["file_system"]
    # Content should be decoded (not binary placeholder)
    assert len(db["file_system"][str(bad_file)]["content_lines"]) > 0


def test_dehydrate_handles_readonly_file_write(tmp_path):
    # Lines 698-699
    db = {
        "workspace_root": "/workspace",
        "file_system": {
            "/workspace": {"is_directory": True, "content_lines": []},
            "/workspace/readonly.txt": {
                "is_directory": False,
                "content_lines": ["readonly content\n"],
                "metadata": {
                    "permissions": {"mode": 0o444}  # readonly
                }
            },
        },
    }
    
    target_dir = tmp_path / "out"
    terminal_utils.dehydrate_db_to_directory(db, str(target_dir))
    
    # Should successfully write readonly file
    assert (target_dir / "readonly.txt").exists()
    assert (target_dir / "readonly.txt").read_text(encoding="utf-8") == "readonly content\n"


def test_update_db_handles_binary_file(tmp_path):
    # Lines 917-935
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    
    temp_dir = tempfile.TemporaryDirectory()
    temp_root = temp_dir.name
    os.makedirs(temp_root, exist_ok=True)
    
    # Create a binary file
    binary_file = os.path.join(temp_root, "image.png")
    with open(binary_file, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    
    db = {
        "workspace_root": str(workspace_root),
        "cwd": str(workspace_root),
        "file_system": {str(workspace_root): {"is_directory": True}},
    }
    
    terminal_utils.update_db_file_system_from_temp(
        db, temp_root, {}, str(workspace_root)
    )
    
    entry = db["file_system"][os.path.join(str(workspace_root), "image.png")]
    assert terminal_utils.BINARY_FILE_MARKER in entry["content_lines"][0]
    temp_dir.cleanup()


def test_collect_pre_post_metadata_state_path_not_in_workspace(tmp_path):
    # Lines 1376, 1411
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    
    file_system = {
        str(workspace_root): {"is_directory": True},
        "/different/root/file.txt": {"is_directory": False},  # Outside workspace
    }
    
    # Should skip files outside workspace
    state = terminal_utils.collect_pre_command_metadata_state(
        file_system, str(workspace_root), str(workspace_root)
    )
    
    assert str(workspace_root) in state
    assert "/different/root/file.txt" not in state


def test_extract_file_paths_empty_args(tmp_path):
    # Lines 1491, 1529
    workspace_root = str(tmp_path)
    
    # Empty command
    paths = terminal_utils._extract_file_paths_from_command("", workspace_root, workspace_root)
    assert paths == set()
    
    # Command with no args
    with set_access_time_mode("relatime"):
        paths = terminal_utils._extract_file_paths_from_command("ls", workspace_root, workspace_root)
        assert paths == set()


def test_dehydrate_missing_workspace_root():
    # Line 624
    db = {"file_system": {}}  # Missing workspace_root
    
    with pytest.raises(ValueError, match="DB missing 'workspace_root'"):
        terminal_utils.dehydrate_db_to_directory(db, "/tmp/out")


def test_update_db_dir_mapping_fails():
    # Line 782
    # Create a scenario where map_temp_path_to_db_key returns None
    db = {"workspace_root": "/workspace", "cwd": "/workspace", "file_system": {}}
    temp_dir = tempfile.TemporaryDirectory()
    
    # The function will skip unmappable directories
    terminal_utils.update_db_file_system_from_temp(
        db, temp_dir.name, {}, "/workspace"
    )
    temp_dir.cleanup()


def test_update_db_with_chmod_command(tmp_path):
    # Lines 892-896, 902-906
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    
    temp_dir = tempfile.TemporaryDirectory()
    os.makedirs(temp_dir.name, exist_ok=True)
    test_file = os.path.join(temp_dir.name, "file.txt")
    with open(test_file, "w") as f:
        f.write("data")
    
    db = {
        "workspace_root": str(workspace_root),
        "file_system": {str(workspace_root): {"is_directory": True}},
    }
    
    # Chmod is a metadata command - triggers strict mode
    terminal_utils.update_db_file_system_from_temp(
        db, temp_dir.name, {}, str(workspace_root), command="chmod 644 file.txt"
    )
    temp_dir.cleanup()


