import pytest
from copilot.SimulationEngine import db


@pytest.fixture
def sample_db(monkeypatch):
    """
    Patch the global DB in db.py with a controlled fixture.
    """
    fake_db = {
        "workspace_root": "/content/workspace",
        "cwd": "/content/workspace",
        "file_system": {
            "/content/workspace": {
                "path": "/content/workspace",
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 123,
                "last_modified": "2025-08-18T22:23:06.864178Z",
                "metadata": {
                    "permissions": {"mode": 493, "uid": 0, "gid": 0},
                    "timestamps": {
                        "access_time": "2025-08-18T22:23:21.788178Z",
                        "modify_time": "2025-08-18T22:23:06.864178Z",
                        "change_time": "2025-08-18T22:23:06.864178Z"
                    }
                },
            },
            "/content/workspace/file1.txt": {
                "path": "/content/workspace/file1.txt",
                "is_directory": False,
                "content_lines": ["hello", "world"],
                "size_bytes": 456,
                "last_modified": "2025-08-18T22:24:00.000000Z",
                "metadata": {
                    "attributes": {"is_hidden": False},
                    "timestamps": {
                        "access_time": "2025-08-18T22:24:21.788178Z",
                        "modify_time": "2025-08-18T22:24:00.000000Z",
                        "change_time": "2025-08-18T22:24:00.000000Z"
                    }
                },
            },
            "/content/workspace/file2.log": {
                "path": "/content/workspace/file2.log",
                "is_directory": False,
                "content_lines": ["log entry"],
                "size_bytes": 789,
                "last_modified": "2025-08-18T22:25:00.000000Z",
                "metadata": {
                    "attributes": {"is_hidden": True},
                    "timestamps": {
                        "access_time": "2025-08-18T22:25:21.788178Z",
                        "modify_time": "2025-08-18T22:25:00.000000Z",
                        "change_time": "2025-08-18T22:25:00.000000Z"
                    }
                },
            },
            "/content/workspace/binary_file.bin": {
                "path": "/content/workspace/binary_file.bin",
                "is_directory": False,
                "content_lines": ["# BINARY_ARCHIVE_BASE64_ENCODED\n", "AAAAAA"],
                "size_bytes": 123,
                "last_modified": "2025-08-18T22:26:00.000000Z",
                "metadata": {
                    "attributes": {"is_hidden": False},
                    "timestamps": {
                        "access_time": "2025-08-18T22:26:21.788178Z",
                        "modify_time": "2025-08-18T22:26:00.000000Z",
                        "change_time": "2025-08-18T22:26:00.000000Z"
                    }
                },
            },
        },
    }

    monkeypatch.setattr(db, "DB", fake_db)
    return fake_db


def test_minified_state_removes_only_timestamps(sample_db):
    result = db.get_minified_state()

    fs = result["file_system"]

    for entry in fs.values():
        # "timestamps" must be gone from metadata, but metadata and other fields remain
        if "metadata" in entry:
            assert "timestamps" not in entry["metadata"]
            # Other metadata subfields (like permissions/attributes) should remain
            for k in entry["metadata"]:
                assert k != "timestamps"
        # Other fields must remain intact
        assert "path" in entry
        assert "is_directory" in entry
        assert "content_lines" in entry
        assert "metadata" in entry


def test_minified_state_does_not_mutate_original_db(sample_db):
    result = db.get_minified_state()

    assert result["file_system"]["/content/workspace/binary_file.bin"]["content_lines"] == ["# BINARY_ARCHIVE_BASE64_ENCODED\n"]

    orig_entry = sample_db["file_system"]["/content/workspace/file1.txt"]
    assert "metadata" in orig_entry
    assert "timestamps" in orig_entry["metadata"]

    minified_entry = result["file_system"]["/content/workspace/file1.txt"]
    assert "metadata" in minified_entry
    assert "timestamps" not in minified_entry["metadata"]
    # Other metadata subfields should remain
    assert "attributes" in minified_entry["metadata"]


def test_multiple_files_preserved_data_integrity(sample_db):
    result = db.get_minified_state()

    fs = result["file_system"]

    # Ensure each file still has its content lines and path
    assert fs["/content/workspace/file1.txt"]["content_lines"] == ["hello", "world"]
    assert fs["/content/workspace/file2.log"]["content_lines"] == ["log entry"]

    # Paths remain correct
    assert fs["/content/workspace/file1.txt"]["path"].endswith("file1.txt")
    assert fs["/content/workspace/file2.log"]["path"].endswith("file2.log")