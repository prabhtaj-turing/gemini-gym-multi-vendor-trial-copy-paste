import pytest
import copy
import os
from unittest.mock import patch
from contextlib import contextmanager
from APIs.cursor.cursorAPI import grep_search
from APIs.cursor.SimulationEngine.db import DB as GlobalDBSource
from APIs.cursor.SimulationEngine.custom_errors import InvalidInputError

@contextmanager
def patch_all_db_locations(mock_db):
    """Context manager to patch all DB locations needed for workspace validation."""
    with patch("APIs.cursor.cursorAPI.DB", mock_db), \
         patch("APIs.cursor.SimulationEngine.utils.DB", mock_db), \
         patch("APIs.cursor.SimulationEngine.db.DB", mock_db), \
         patch("APIs.cursor.DB", mock_db):
        yield

@pytest.fixture
def mock_db():
    pristine_db_state = copy.deepcopy(GlobalDBSource)
    db_for_test = copy.deepcopy(pristine_db_state)
    
    # Ensure workspace is properly hydrated for testing
    ws_root = "/test_ws"
    db_for_test["workspace_root"] = ws_root
    db_for_test["cwd"] = ws_root
    db_for_test["file_system"] = {}
    
    # Add root directory
    db_for_test["file_system"][ws_root] = {
        "path": ws_root,
        "is_directory": True,
        "size_bytes": 0,
        "last_modified": "T_DIR",
    }

    # Populate with some initial files
    db_for_test["file_system"].update({
        "/ws/main.py": {
            "path": "/ws/main.py",
            "is_directory": False,
            "content_lines": ["import flask", "app = flask.Flask(__name__)", "app.run()"],
        },
        "/ws/utils.py": {
            "path": "/ws/utils.py",
            "is_directory": False,
            "content_lines": ["def helper_function():", "    return 'helper'"],
        },
        "/ws/config.txt": {
            "path": "/ws/config.txt",
            "is_directory": False,
            "content_lines": ["HOST=localhost", "PORT=8080"],
        },
    })
    
    yield db_for_test
    
    # Teardown: Restore the original DB state
    GlobalDBSource.clear()
    GlobalDBSource.update(pristine_db_state)

def _add_file_with_content(db, path, content_lines):
    dir_name = os.path.dirname(path)
    if dir_name:
        current_path = ""
        root = db.get("workspace_root", "/")
        parts = dir_name.replace(root, "").strip("/").split("/")
        current_path = root
        if root not in db["file_system"]:
            _add_dir(db, root)
        for part in parts:
            if not part:
                continue
            if current_path == "/" and not part.startswith("/"):
                current_path = "/" + part
            elif current_path.endswith("/") and part.startswith("/"):
                current_path = current_path + part[1:]
            elif not current_path.endswith("/") and not part.startswith("/"):
                current_path = current_path + "/" + part
            else:
                current_path = current_path + part
            current_path = os.path.normpath(current_path)
            if current_path not in db["file_system"]:
                _add_dir(db, current_path)
    db["file_system"][path] = {
        "path": path,
        "is_directory": False,
        "content_lines": content_lines,
        "size_bytes": sum(len(line.encode("utf-8")) for line in content_lines),
        "last_modified": "T_FILE",
    }

def _add_dir(db, path):
    if path not in db["file_system"]:
        db["file_system"][path] = {
            "path": path,
            "is_directory": True,
            "size_bytes": 0,
            "last_modified": "T_DIR",
        }

def _assert_match(match_dict, expected_path, expected_line_num, expected_content):
    assert match_dict.get("file_path") == expected_path
    assert match_dict.get("line_number") == expected_line_num
    assert match_dict.get("line_content") == expected_content

def test_basic_match(mock_db):
    path = "/test_ws/file.txt"
    content = ["Hello world\n", "This is line two\n", "Another Hello\n"]
    _add_file_with_content(mock_db, path, content)
    with patch_all_db_locations(mock_db):
        results = grep_search(query="Hello")
    assert len(results) == 2
    _assert_match(results[0], path, 1, "Hello world")
    _assert_match(results[1], path, 3, "Another Hello")

def test_multiple_files(mock_db):
    path1 = "/test_ws/one.py"
    content1 = ["import sys\n", "print('TARGET')\n"]
    path2 = "/test_ws/two.txt"
    content2 = ["This TARGET is important\n", "No match here\n"]
    _add_file_with_content(mock_db, path1, content1)
    _add_file_with_content(mock_db, path2, content2)
    with patch_all_db_locations(mock_db):
        results = grep_search(query="TARGET")
    assert len(results) == 2
    # Order depends on sorted path iteration
    _assert_match(results[0], path1, 2, "print('TARGET')")
    _assert_match(results[1], path2, 1, "This TARGET is important")

def test_case_sensitive_default(mock_db):
    path = "/test_ws/case.txt"
    content = ["MatchThis\n", "matchthis\n", "MATCHTHIS\n"]
    _add_file_with_content(mock_db, path, content)
    with patch_all_db_locations(mock_db):
        results = grep_search(query="MatchThis")
    assert len(results) == 1
    _assert_match(results[0], path, 1, "MatchThis")

def test_case_insensitive_match(mock_db):
    path = "/test_ws/case.txt"
    content = ["MatchThis\n", "matchthis\n", "MATCHTHIS\n"]
    _add_file_with_content(mock_db, path, content)
    with patch_all_db_locations(mock_db):
        results = grep_search(query="MatchThis", case_sensitive=False)
    assert len(results) == 3
    _assert_match(results[0], path, 1, "MatchThis")
    _assert_match(results[1], path, 2, "matchthis")
    _assert_match(results[2], path, 3, "MATCHTHIS")

def test_regex_metacharacters(mock_db):
    path = "/test_ws/regex.txt"
    content = ["start middle end\n", "abc\n", "a.c\n", "1.0\n"]
    _add_file_with_content(mock_db, path, content)

    # Test '.' (any character) - Should match 'abc' (line 2) and 'a.c' (line 3)
    with patch_all_db_locations(mock_db):
        results_dot = grep_search(query="a.c")
    assert len(results_dot) == 2, "Regex 'a.c' should match two lines"
    # Verify the specific matches found (order depends on line iteration)
    _assert_match(results_dot[0], path, 2, "abc")
    _assert_match(results_dot[1], path, 3, "a.c")

    # Test '^' (start anchor)
    with patch_all_db_locations(mock_db):
        results_start = grep_search(query="^start")
    assert len(results_start) == 1, "Regex '^start' should match one line"
    _assert_match(results_start[0], path, 1, "start middle end")

    # Test '$' (end anchor)
    with patch_all_db_locations(mock_db):
        results_end = grep_search(query="end$")
    assert len(results_end) == 1, "Regex 'end$' should match one line"
    _assert_match(results_end[0], path, 1, "start middle end")

    # Test escaped literal dot using a raw string for the pattern
    with patch_all_db_locations(mock_db):
        results_escaped = grep_search(query=r"1\.0")
    assert len(results_escaped) == 1, "Regex '1\\.0' should match one line"
    _assert_match(results_escaped[0], path, 4, "1.0")

def test_no_match(mock_db):
    path = "/test_ws/data.log"
    content = ["Log entry one\n", "Another entry\n"]
    _add_file_with_content(mock_db, path, content)
    with patch_all_db_locations(mock_db):
        results = grep_search(query="non_existent_pattern")
    assert results == []

def test_invalid_regex_query(mock_db):
    path = "/test_ws/data.log"
    content = ["Some content\n"]
    _add_file_with_content(mock_db, path, content)
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        with patch_all_db_locations(mock_db):
            grep_search(query="[invalidRegex")  # Unbalanced bracket

def test_empty_query(mock_db):
    path = "/test_ws/data.log"
    content = ["Some content\n"]
    _add_file_with_content(mock_db, path, content)
    with patch_all_db_locations(mock_db):
        results = grep_search(query="")
    assert results == []

def test_skip_directories(mock_db):
    _add_dir(mock_db, "/test_ws/a_directory")
    mock_db["file_system"]["/test_ws/a_directory"]["content_lines"] = [
        "This should not be searched\n"
    ]  # Add content just in case
    _add_file_with_content(mock_db, "/test_ws/a_file.txt", ["Search this instead\n"])
    with patch_all_db_locations(mock_db):
        results = grep_search(query="Search")
    assert len(results) == 1
    _assert_match(results[0], "/test_ws/a_file.txt", 1, "Search this instead")

def test_include_pattern_filter(mock_db):
    _add_file_with_content(mock_db, "/test_ws/include_me.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/ignore_me.txt", ["match_target\n"])
    _add_file_with_content(
        mock_db, "/test_ws/scripts/include_me_too.py", ["match_target\n"]
    )
    with patch_all_db_locations(mock_db):
        results = grep_search(query="match_target", include_pattern="*.py")
    assert len(results) == 2
    assert all(r["file_path"].endswith(".py") for r in results)
    assert [r["file_path"] for r in results] == [
        "/test_ws/include_me.py", "/test_ws/scripts/include_me_too.py"
    ]

def test_exclude_pattern_filter(mock_db):
    _add_file_with_content(mock_db, "/test_ws/search_me.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/temp/exclude_me.log", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/exclude_me_also.log", ["match_target\n"])
    with patch_all_db_locations(mock_db):
        results = grep_search(query="match_target", exclude_pattern="*.log")
    assert len(results) == 1
    _assert_match(results[0], "/test_ws/search_me.py", 1, "match_target")

def test_include_exclude_interaction(mock_db):
    _add_file_with_content(mock_db, "/test_ws/src/main.py", ["target\n"])
    _add_file_with_content(
        mock_db, "/test_ws/src/test_main.py", ["target\n"]
    )  # Included by *.py, excluded by test_*
    _add_file_with_content(
        mock_db, "/test_ws/src/config.yaml", ["target\n"]
    )  # Not included
    with patch_all_db_locations(mock_db):
        results = grep_search(
            query="target", include_pattern="*.py", exclude_pattern="test_*.py"
        )
    assert len(results) == 1
    _assert_match(results[0], "/test_ws/src/main.py", 1, "target")

def test_result_capping_at_50(mock_db):
    path = "/test_ws/many_matches.txt"
    content = [f"Match line {i}\n" for i in range(100)]  # 100 lines that match
    _add_file_with_content(mock_db, path, content)
    with patch_all_db_locations(mock_db):
        results = grep_search(query="Match line")
    assert len(results) == 50
    # Check the first and last item expected within the cap
    _assert_match(results[0], path, 1, "Match line 0")
    _assert_match(results[49], path, 50, "Match line 49")

def test_empty_file_content(mock_db):
    _add_file_with_content(mock_db, "/test_ws/empty.txt", [])
    with patch_all_db_locations(mock_db):
        results = grep_search(query="anything")
    assert results == []

def test_invalid_query_type_raises_error(mock_db):
    with pytest.raises(InvalidInputError):
        with patch_all_db_locations(mock_db):
            grep_search(query=123)

def test_invalid_explanation_type_raises_error(mock_db):
    with pytest.raises(InvalidInputError):
        with patch_all_db_locations(mock_db):
            grep_search(query="test", explanation=[])

def test_invalid_case_sensitive_type_raises_error(mock_db):
    with pytest.raises(InvalidInputError):
        with patch_all_db_locations(mock_db):
            grep_search(query="test", case_sensitive="true")

def test_invalid_include_pattern_type_raises_error(mock_db):
    with pytest.raises(InvalidInputError):
        with patch_all_db_locations(mock_db):
            grep_search(query="test", include_pattern=123)

def test_invalid_exclude_pattern_type_raises_error(mock_db):
    with pytest.raises(InvalidInputError):
        with patch_all_db_locations(mock_db):
            grep_search(query="test", exclude_pattern=False)

def test_basic_search(mock_db):
    with patch_all_db_locations(mock_db):
        results = grep_search(query="flask")
    assert len(results) == 2
    assert results[0]["file_path"] == "/ws/main.py"
    assert results[0]["line_number"] == 1
    assert results[1]["file_path"] == "/ws/main.py"
    assert results[1]["line_number"] == 2

def test_case_insensitive_search(mock_db):
    with patch_all_db_locations(mock_db):
        results = grep_search(query="HOST", case_sensitive=False)
    assert len(results) == 1
    assert results[0]["file_path"] == "/ws/config.txt"

def test_include_pattern(mock_db):
    with patch_all_db_locations(mock_db):
        results = grep_search(query="import", include_pattern="*.py")
    assert len(results) == 1
    assert results[0]["file_path"] == "/ws/main.py"

def test_exclude_pattern(mock_db):
    with patch_all_db_locations(mock_db):
        results = grep_search(query=".", exclude_pattern="*.txt")
    assert len(results) == 5

def test_no_matches(mock_db):
    with patch_all_db_locations(mock_db):
        results = grep_search(query="nonexistent_string")
    assert len(results) == 0

def test_glob_pattern_with_relative_path(mock_db):
    """Verify glob pattern matching works with relative paths from cwd."""
    mock_db["cwd"] = "/test_ws/project"
    _add_file_with_content(mock_db, "/test_ws/project/src/main.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/project/lib/helper.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/project/src/data.txt", ["match_target\n"])
    with patch_all_db_locations(mock_db):
        results = grep_search(query="match_target", include_pattern="src/main.py")
    assert len(results) == 1
    assert results[0]["file_path"] == "/test_ws/project/src/main.py"

def test_glob_pattern_with_wildcard_relative_path(mock_db):
    """Verify glob pattern matching works with relative paths and wildcards."""
    mock_db["cwd"] = "/test_ws/project"
    _add_file_with_content(mock_db, "/test_ws/project/src/main.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/project/src/utils.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/project/lib/helper.py", ["match_target\n"])
    with patch_all_db_locations(mock_db):
        results = grep_search(query="match_target", include_pattern="src/*.py")
    assert len(results) == 2
    assert [r["file_path"] for r in results] == [
        "/test_ws/project/src/main.py", "/test_ws/project/src/utils.py"
    ]

def test_exclude_glob_pattern_with_relative_path(mock_db):
    """Verify exclude glob pattern matching works with relative paths."""
    mock_db["cwd"] = "/test_ws/project"
    _add_file_with_content(mock_db, "/test_ws/project/src/main.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/project/src/utils.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/project/lib/helper.py", ["match_target\n"])
    with patch_all_db_locations(mock_db):
        results = grep_search(query="match_target", include_pattern="**/*.py", exclude_pattern="src/utils.py")
    assert len(results) == 2
    assert sorted([r["file_path"] for r in results]) == [
        "/test_ws/project/lib/helper.py",
        "/test_ws/project/src/main.py"
    ]

def test_glob_pattern_with_absolute_path(mock_db):
    """Verify glob pattern matching works with absolute paths."""
    mock_db["cwd"] = "/test_ws/project"
    _add_file_with_content(mock_db, "/test_ws/project/src/main.py", ["match_target\n"])
    _add_file_with_content(mock_db, "/test_ws/project/lib/helper.py", ["match_target\n"])
    with patch_all_db_locations(mock_db):
        results = grep_search(query="match_target", include_pattern="/test_ws/project/src/main.py")
    assert len(results) == 1
    assert results[0]["file_path"] == "/test_ws/project/src/main.py"


if __name__ == "__main__":
    pytest.main()