import json
import os
import sys
from pathlib import Path

import pytest

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli import list_directory  # noqa: E402
from gemini_cli.SimulationEngine import db as sim_db  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import (
    InvalidInputError,
    WorkspaceNotAvailableError,
)  # noqa: E402

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def reload_db(tmp_path):
    """Load fresh DB snapshot before each test."""
    sim_db.DB.clear()
    with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
        sim_db.DB.update(json.load(fh))
    yield
    sim_db.DB.clear()


def test_root_listing():
    root = sim_db.DB["workspace_root"]
    items = list_directory(root)
    names = [i["name"] for i in items]
    
    # Check expected files
    assert "README.md" in names
    assert ".gitignore" in names
    assert ".geminiignore" in names
    assert "package.json" in names
    
    # Check expected directories
    assert "src" in names
    assert "docs" in names
    assert "tests" in names
    assert ".gemini" in names
    
    # Check that we have the expected number of items (4 files + 4 directories = 8 total)
    assert len(items) == 8
    
    # Verify mix of files and directories
    files = [item for item in items if not item["is_directory"]]
    directories = [item for item in items if item["is_directory"]]
    assert len(files) == 4  # .gitignore, .geminiignore, README.md, package.json
    assert len(directories) == 4  # src, docs, tests, .gemini


def test_ignore_pattern():
    root = sim_db.DB["workspace_root"]
    items = list_directory(root, ignore=["*.md"])
    assert all(not n["name"].endswith(".md") for n in items)


def test_invalid_path_type():
    with pytest.raises(InvalidInputError):  # type: ignore[name-defined]
        list_directory(123)  # type: ignore[arg-type]


def test_relative_path():
    # Relative paths are now supported, but this path doesn't exist
    with pytest.raises(FileNotFoundError):  # type: ignore[name-defined]
        list_directory("relative/path")


def test_path_outside_workspace():
    # Paths with leading slashes are now treated as relative, so this creates
    # a path like workspace_root/etc which doesn't exist
    with pytest.raises(FileNotFoundError):  # type: ignore[name-defined]
        list_directory("/etc")


def test_ignore_not_list():
    root = sim_db.DB["workspace_root"]
    with pytest.raises(InvalidInputError):  # type: ignore[name-defined]
        list_directory(root, ignore="*.md")  # type: ignore[arg-type]


def test_ignore_contains_non_string():
    root = sim_db.DB["workspace_root"]
    with pytest.raises(InvalidInputError):  # type: ignore[name-defined]
        list_directory(root, ignore=[123])  # type: ignore[list-item] 


def test_directories_first_sort_order_at_root():
    root = sim_db.DB["workspace_root"]
    items = list_directory(root)
    # Directories should come first, then files
    kinds = [item["is_directory"] for item in items]
    # Once we hit a False (file), there should be no more True values afterwards
    seen_file = False
    for is_dir in kinds:
        if not is_dir:
            seen_file = True
        else:
            assert not seen_file, "Directories must precede files in the listing"


def test_list_subdirectory_src_contents_and_sorting():
    root = sim_db.DB["workspace_root"]
    src_path = os.path.join(root, "src")
    items = list_directory(src_path)
    names = [i["name"] for i in items]
    assert names == sorted(names, key=str.lower)
    assert names == ["main.py", "utils.py"]
    assert all(not i["is_directory"] for i in items)


def test_list_subdirectory_docs_with_ignore_md():
    root = sim_db.DB["workspace_root"]
    docs_path = os.path.join(root, "docs")
    items = list_directory(docs_path, ignore=["*.md"])
    assert items == []


def test_returned_item_structure_and_values():
    root = sim_db.DB["workspace_root"]
    items = list_directory(root)
    # Find README.md item and validate fields
    readme = next(i for i in items if i["name"] == "README.md")
    assert set(readme.keys()) == {"name", "path", "is_directory", "size", "modifiedTime"}
    assert readme["path"].endswith("/README.md")
    assert readme["is_directory"] is False
    assert isinstance(readme["size"], int) and readme["size"] > 0
    assert isinstance(readme["modifiedTime"], str)


def test_list_directory_on_file_raises_not_a_directory():
    root = sim_db.DB["workspace_root"]
    file_path = os.path.join(root, "README.md")
    with pytest.raises(NotADirectoryError):
        list_directory(file_path)


def test_list_directory_missing_path_raises_file_not_found():
    root = sim_db.DB["workspace_root"]
    missing = os.path.join(root, "no_such_dir")
    with pytest.raises(FileNotFoundError):
        list_directory(missing)


def test_ignore_multiple_patterns():
    root = sim_db.DB["workspace_root"]
    items = list_directory(root, ignore=["*.md", ".gemini"])
    names = [i["name"] for i in items]
    assert "README.md" not in names
    assert ".gemini" not in names


def test_ignore_default_none_equivalence():
    root = sim_db.DB["workspace_root"]
    items_default = list_directory(root)
    items_none = list_directory(root, ignore=None)
    # Compare by names and kinds to avoid timestamp fluctuations
    default_sig = [(i["name"], i["is_directory"]) for i in items_default]
    none_sig = [(i["name"], i["is_directory"]) for i in items_none]
    assert default_sig == none_sig


def test_workspace_not_available_error():
    # Simulate missing workspace_root
    sim_db.DB["workspace_root"] = ""
    with pytest.raises(WorkspaceNotAvailableError):  # type: ignore[name-defined]
        list_directory("/")


def test_slash_path_maps_to_workspace_root():
    """Passing "/" should be treated as the workspace root directory.

    This currently fails because the implementation rejects "/" as outside the
    workspace root. After the fix, it should list the same items as the root.
    """
    root = sim_db.DB["workspace_root"]

    # Baseline listing at the actual workspace root
    expected_items = list_directory(root)
    expected_names = [i["name"] for i in expected_items]

    # Listing using "/" should match baseline
    slash_items = list_directory("/")
    slash_names = [i["name"] for i in slash_items]

    assert slash_names == expected_names


def test_slash_path_with_empty_ignore_list_behaves_like_root():
    """Passing "/" with ignore=[] should behave like listing the root with ignore=None.

    This guards the edge case reported in tooling where ignore was provided as
    an empty list. After the fix, both calls should succeed and match.
    """
    root = sim_db.DB["workspace_root"]

    baseline = list_directory(root, ignore=None)
    baseline_names = [i["name"] for i in baseline]

    slash_with_empty_ignore = list_directory("/", ignore=[])
    slash_names = [i["name"] for i in slash_with_empty_ignore]

    assert slash_names == baseline_names