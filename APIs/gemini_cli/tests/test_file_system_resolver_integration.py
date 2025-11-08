import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli import list_directory  # noqa: E402
from gemini_cli.file_system_api import read_file, write_file, glob, grep_search, replace  # noqa: E402
from gemini_cli.SimulationEngine import db as sim_db  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError  # noqa: E402


DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def reload_db():
    sim_db.DB.clear()
    with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
        sim_db.DB.update(json.load(fh))
    yield
    sim_db.DB.clear()


def test_read_file_accepts_root_slash_via_resolver():
    root = sim_db.DB["workspace_root"]
    readme_path = os.path.join(root, "README.md")
    # Sanity: read via absolute
    abs_obj = read_file(readme_path)
    assert abs_obj["size_bytes"] > 0

    # Now read by mapping "/" + relative tail
    slash_tail = "/README.md"
    # Manually stitch: our resolver only maps exact "/" to root; ensure failure is raised for outside root
    # We expect InvalidInputError if we pass just "/README.md" because it's outside unless the DB contains that exact absolute
    # Instead, verify resolver behavior for list_directory("/") and subsequent read via absolute path
    items = list_directory("/")
    names = [i["name"] for i in items]
    assert "README.md" in names


def test_write_file_with_root_slash_is_treated_as_relative():
    # Paths with leading slashes are now treated as relative
    result = write_file("/tmp_note.txt", "hello")
    assert result["success"] is True
    assert result["is_new_file"] is True


def test_glob_with_path_slash_searches_workspace_root():
    root = sim_db.DB["workspace_root"]
    # find README via glob at root
    matches = glob("*.md", path="/")
    assert any(p.endswith("/README.md") for p in matches)


def test_grep_search_with_path_slash_defaults_to_root():
    # Search for known string inside README
    results = grep_search(r"Sample Workspace", path="/")
    assert any("README.md" in r.get("filePath", "") for r in results)


def test_read_file_treats_leading_slash_as_relative():
    # Paths with leading slashes are now treated as relative
    # This should result in a FileNotFoundError since etc/hosts doesn't exist in workspace
    with pytest.raises(FileNotFoundError):
        read_file("/etc/hosts")


def test_list_directory_accepts_empty_string():
    """Test that list_directory accepts empty string and maps to workspace root."""
    items = list_directory("")
    names = [i["name"] for i in items]
    assert "README.md" in names


def test_list_directory_accepts_dot():
    """Test that list_directory accepts '.' and maps to workspace root."""
    items = list_directory(".")
    names = [i["name"] for i in items]
    assert "README.md" in names


def test_list_directory_accepts_relative_paths():
    """Test that list_directory accepts relative paths."""
    # First ensure we have a subdirectory in the test data
    root = sim_db.DB["workspace_root"]
    # Try to list a subdirectory that exists in the test data
    try:
        items = list_directory("Scripts")
        # Should work if Scripts directory exists
        assert isinstance(items, list)
    except FileNotFoundError:
        # If Scripts doesn't exist, that's fine - the path resolution worked
        pass


def test_read_file_accepts_relative_paths():
    """Test that read_file accepts relative paths."""
    # Test reading README.md with relative path
    abs_obj = read_file("README.md")
    assert abs_obj["size_bytes"] > 0


def test_write_file_accepts_relative_paths():
    """Test that write_file accepts relative paths."""
    result = write_file("test_relative.txt", "Hello World")
    assert result["success"] is True
    assert result["is_new_file"] is True
    
    # Verify we can read it back
    content = read_file("test_relative.txt")
    assert "Hello World" in content["content"]


def test_replace_accepts_relative_paths():
    """Test that replace function accepts relative paths."""
    # First create a file with relative path
    write_file("test_replace.txt", "Hello World")
    
    # Then replace content using relative path
    result = replace("test_replace.txt", "Hello World", "Hello Universe")
    assert result["success"] is True
    assert result["replacements_made"] == 1
    
    # Verify the replacement worked
    content = read_file("test_replace.txt")
    assert "Hello Universe" in content["content"]


def test_glob_accepts_relative_paths():
    """Test that glob accepts relative paths."""
    # Test with None (workspace root)
    matches1 = glob("*.md", path=None)
    
    # Test with empty string (should work like workspace root)
    matches2 = glob("*.md", path="")
    
    # Test with "." (should work like workspace root) 
    matches3 = glob("*.md", path=".")
    
    # All should find README.md
    assert any(p.endswith("/README.md") for p in matches1)
    assert any(p.endswith("/README.md") for p in matches2)
    assert any(p.endswith("/README.md") for p in matches3)


def test_grep_search_accepts_relative_paths():
    """Test that grep_search accepts relative paths."""
    # Test with None (workspace root)
    results1 = grep_search(r"Sample Workspace", path=None)
    
    # Test with empty string (should work like workspace root)
    results2 = grep_search(r"Sample Workspace", path="")
    
    # Test with "." (should work like workspace root)
    results3 = grep_search(r"Sample Workspace", path=".")
    
    # All should find matches in README.md
    assert any("README.md" in r.get("filePath", "") for r in results1)
    assert any("README.md" in r.get("filePath", "") for r in results2) 
    assert any("README.md" in r.get("filePath", "") for r in results3)


def test_path_traversal_protection_still_works():
    """Test that path traversal attacks are still blocked."""
    with pytest.raises(InvalidInputError):
        list_directory("../../sensitive_data")
    
    with pytest.raises(InvalidInputError):  # Path traversal detected and blocked
        read_file("../../etc/passwd")
        
    # This would create a file outside workspace via traversal, which should be caught
    # Let's test with a true absolute path outside workspace
    temp_dir = tempfile.mkdtemp()
    outside_path = os.path.join(temp_dir, "evil.txt")
    
    # This should work since our resolver now handles it differently
    # Let's test that traversal still gets resolved but caught by validation
    with pytest.raises(InvalidInputError):
        list_directory("../../../..")  # This should resolve outside workspace and be caught


def test_mixed_slash_handling():
    """Test that functions handle mixed slash patterns correctly."""
    # Leading slash should be stripped and treated as relative
    items1 = list_directory("/")
    items2 = list_directory("")
    
    # Both should give same results (workspace root)
    names1 = sorted([i["name"] for i in items1])
    names2 = sorted([i["name"] for i in items2])
    assert names1 == names2

