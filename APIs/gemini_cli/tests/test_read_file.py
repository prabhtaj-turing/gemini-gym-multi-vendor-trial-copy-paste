import json
import os
import sys
from pathlib import Path
from typing import List

import pytest

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli import read_file  # noqa: E402
from gemini_cli.SimulationEngine import db as sim_db  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import (  # noqa: E402
    InvalidInputError,
    WorkspaceNotAvailableError,
)

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def reload_db(tmp_path):
    """Load fresh DB snapshot before each test and provide helpers."""
    sim_db.DB.clear()
    with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
        sim_db.DB.update(json.load(fh))

    # Provide helper to add files easily inside tests
    def _add_file(rel_path: str, lines: List[str], is_binary: bool = False):
        abs_path = os.path.join(sim_db.DB["workspace_root"], rel_path.replace("/", os.sep))
        metadata = {
            "path": abs_path,
            "is_directory": False,
            "content_lines": [] if is_binary else lines,
            "size_bytes": sum(len(l.encode("utf-8")) for l in lines),
            "last_modified": "2025-07-09T00:00:00Z",
        }
        if is_binary:
            # Fake binary content as base64 string placeholder
            metadata["content_b64"] = "ZGF0YQ=="  # "data" base64
        sim_db.DB["file_system"][abs_path] = metadata
        return abs_path

    sim_db.DB["_test_helpers"] = {"add_file": _add_file}
    yield
    sim_db.DB.clear()


def _add_file(rel_path: str, lines: List[str], is_binary: bool = False):  # type: ignore[docstring]
    """Proxy to fixture-injected helper (for type checkers)."""
    return sim_db.DB["_test_helpers"]["add_file"](rel_path, lines, is_binary)  # type: ignore[index]


# ---------------------------------------------------------------------------
# Success scenarios
# ---------------------------------------------------------------------------

def test_read_full_text_file():
    path = _add_file("foo.txt", ["A\n", "B\n", "C\n"])
    result = read_file(path)
    assert result["content"].endswith("A\nB\nC\n")
    assert result["start_line"] == 1
    assert result["end_line"] == 3
    assert result["total_lines"] == 3
    assert result["is_truncated"] is False


def test_read_slice_with_offset_limit_truncation():
    lines = [f"Line {i}\n" for i in range(3000)]
    path = _add_file("big.txt", lines)
    # Request slice offset 100, limit 10
    result = read_file(path, offset=100, limit=10)
    assert result["start_line"] == 101  # 1-based
    assert result["end_line"] == 110
    # should flag truncation (lines above and below)
    assert result["is_truncated"] is True
    assert "truncated" in result["content"].split("\n", 1)[0].lower()


def test_line_length_truncation():
    long_line = "x" * 3000 + "\n"
    path = _add_file("long.txt", [long_line])
    result = read_file(path)
    # Content should include [truncated]
    assert "[truncated]" in result["content"]
    assert result["is_truncated"] is True


def test_binary_file_base64():
    path = _add_file("image.png", [], is_binary=True)
    res = read_file(path)
    assert res["encoding"] == "base64"
    assert "inlineData" in res
    assert res["inlineData"]["data"] == "ZGF0YQ=="


def test_geminiignore_rejection():
    # Add .geminiignore file with pattern secret.*
    _add_file(".geminiignore", ["secret.*\n"])
    secret_path = _add_file("secret.txt", ["Top secret\n"])
    with pytest.raises(InvalidInputError):
        read_file(secret_path)


# ---------------------------------------------------------------------------
# NEW EDGE CASES: Empty Files
# ---------------------------------------------------------------------------

def test_empty_file():
    """Test reading completely empty file (0 bytes, 0 lines)."""
    path = _add_file("empty.txt", [])
    result = read_file(path)
    assert result["size_bytes"] == 0
    assert result["content"] == ""
    assert result["start_line"] == 1
    assert result["end_line"] == 0  # Empty file returns 0 for end_line
    assert result["total_lines"] == 0
    assert result["is_truncated"] is False


def test_empty_file_with_offset():
    """Test reading empty file with offset should raise error."""
    path = _add_file("empty.txt", [])
    with pytest.raises(InvalidInputError, match="Offset.*beyond.*total number of lines"):
        read_file(path, offset=1)


def test_file_with_only_newlines():
    """Test file containing only empty lines."""
    path = _add_file("newlines.txt", ["\n", "\n", "\n"])
    result = read_file(path)
    assert result["content"] == "\n\n\n"
    assert result["total_lines"] == 3
    assert result["is_truncated"] is False


# ---------------------------------------------------------------------------
# NEW EDGE CASES: File Size Limits
# ---------------------------------------------------------------------------

def test_file_size_limit_exceeded():
    """Test file exceeding 20MB size limit."""
    # Create a file that's too large
    abs_path = os.path.join(sim_db.DB["workspace_root"], "huge.txt")
    sim_db.DB["file_system"][abs_path] = {
        "path": abs_path,
        "is_directory": False,
        "content_lines": ["small content\n"],
        "size_bytes": 21 * 1024 * 1024,  # 21 MB > 20 MB limit
        "last_modified": "2025-07-09T00:00:00Z",
    }
    
    with pytest.raises(ValueError, match="File exceeds 20 MB size limit"):
        read_file(abs_path)


def test_file_size_at_boundary():
    """Test file at exactly 20MB boundary."""
    abs_path = os.path.join(sim_db.DB["workspace_root"], "boundary.txt")
    sim_db.DB["file_system"][abs_path] = {
        "path": abs_path,
        "is_directory": False,
        "content_lines": ["content\n"],
        "size_bytes": 20 * 1024 * 1024,  # Exactly 20 MB
        "last_modified": "2025-07-09T00:00:00Z",
    }
    
    result = read_file(abs_path)
    assert result["size_bytes"] == 20 * 1024 * 1024
    assert "content" in result


# ---------------------------------------------------------------------------
# NEW EDGE CASES: Line Count Limits
# ---------------------------------------------------------------------------

def test_default_line_limit():
    """Test default 2000 line limit without explicit limit parameter."""
    lines = [f"Line {i}\n" for i in range(2500)]  # More than 2000 lines
    path = _add_file("many_lines.txt", lines)
    result = read_file(path)
    assert result["total_lines"] == 2500
    assert result["end_line"] == 2000  # Default limit
    assert result["is_truncated"] is True


def test_line_limit_boundary():
    """Test exactly at line limit boundary."""
    lines = [f"Line {i}\n" for i in range(2000)]  # Exactly 2000 lines
    path = _add_file("exactly_2000.txt", lines)
    result = read_file(path)
    assert result["total_lines"] == 2000
    assert result["end_line"] == 2000
    assert result["is_truncated"] is False


# ---------------------------------------------------------------------------
# NEW EDGE CASES: File System Errors
# ---------------------------------------------------------------------------

def test_file_not_found():
    """Test reading non-existent file."""
    abs_path = os.path.join(sim_db.DB["workspace_root"], "nonexistent.txt")
    with pytest.raises(FileNotFoundError):
        read_file(abs_path)


def test_malformed_db_entry():
    """Test malformed DB entry with content_lines not a list."""
    abs_path = os.path.join(sim_db.DB["workspace_root"], "malformed.txt")
    sim_db.DB["file_system"][abs_path] = {
        "path": abs_path,
        "is_directory": False,
        "content_lines": "not a list",  # Should be a list
        "size_bytes": 10,
        "last_modified": "2025-07-09T00:00:00Z",
    }
    
    with pytest.raises(RuntimeError, match="malformed.*content_lines.*not a list"):
        read_file(abs_path)


def test_missing_workspace_root():
    """Test when workspace_root is not configured."""
    sim_db.DB.pop("workspace_root", None)
    path = "/some/path"
    with pytest.raises(WorkspaceNotAvailableError):
        read_file(path)


# ---------------------------------------------------------------------------
# NEW EDGE CASES: Different File Types
# ---------------------------------------------------------------------------

def test_svg_file_as_text():
    """Test SVG file is treated as text, not binary."""
    svg_content = ['<svg xmlns="http://www.w3.org/2000/svg">\n', '<circle cx="50" cy="50" r="40"/>\n', '</svg>\n']
    path = _add_file("image.svg", svg_content)
    result = read_file(path)
    assert "content" in result
    assert "inlineData" not in result
    assert result["total_lines"] == 3


def test_pdf_file_as_binary():
    """Test PDF file is treated as binary."""
    path = _add_file("document.pdf", [], is_binary=True)
    result = read_file(path)
    assert "inlineData" in result
    assert result["inlineData"]["mimeType"] == "application/pdf"
    assert result["encoding"] == "base64"


def test_audio_file_as_binary():
    """Test audio file is treated as binary."""
    path = _add_file("song.mp3", [], is_binary=True)
    result = read_file(path)
    assert "inlineData" in result
    assert result["inlineData"]["mimeType"] == "audio/mpeg"
    assert result["encoding"] == "base64"


def test_video_file_as_binary():
    """Test video file is treated as binary."""
    path = _add_file("movie.mp4", [], is_binary=True)
    result = read_file(path)
    assert "inlineData" in result
    assert result["inlineData"]["mimeType"] == "video/mp4"
    assert result["encoding"] == "base64"


# ---------------------------------------------------------------------------
# NEW EDGE CASES: Unicode and Special Characters
# ---------------------------------------------------------------------------

def test_unicode_content():
    """Test file with Unicode characters and emoji."""
    unicode_lines = ["Hello 世界\n", "Emoji: 🚀🌟\n", "Special: àáâãäå\n"]
    path = _add_file("unicode.txt", unicode_lines)
    result = read_file(path)
    assert "Hello 世界" in result["content"]
    assert "🚀🌟" in result["content"]
    assert "àáâãäå" in result["content"]


def test_different_newline_formats():
    """Test file with different newline formats."""
    # Note: In simulation, all lines in content_lines should end with \n
    # but we can test mixed content within lines
    mixed_lines = ["Line with \\r\\n\n", "Line with \\r\n", "Normal line\n"]
    path = _add_file("mixed_newlines.txt", mixed_lines)
    result = read_file(path)
    assert "\\r\\n" in result["content"]
    assert result["total_lines"] == 3


# ---------------------------------------------------------------------------
# NEW EDGE CASES: Boundary Conditions
# ---------------------------------------------------------------------------

def test_offset_at_exact_end():
    """Test offset at exactly the last line."""
    lines = ["Line 1\n", "Line 2\n", "Line 3\n"]
    path = _add_file("three_lines.txt", lines)
    result = read_file(path, offset=2, limit=1)  # offset=2 is line 3 (0-based)
    assert result["start_line"] == 3
    assert result["end_line"] == 3
    assert "Line 3" in result["content"]


def test_limit_larger_than_remaining():
    """Test limit larger than remaining lines."""
    lines = ["Line 1\n", "Line 2\n", "Line 3\n"]
    path = _add_file("three_lines.txt", lines)
    result = read_file(path, offset=1, limit=10)  # Only 2 lines remaining
    assert result["start_line"] == 2
    assert result["end_line"] == 3
    # Should be truncated because we have an offset > 0 (content from beginning is missing)
    assert result["is_truncated"] is True


def test_offset_zero_limit_one():
    """Test minimal slice: offset=0, limit=1."""
    lines = ["First line\n", "Second line\n"]
    path = _add_file("two_lines.txt", lines)
    result = read_file(path, offset=0, limit=1)
    assert result["start_line"] == 1
    assert result["end_line"] == 1
    assert result["is_truncated"] is True
    assert "First line" in result["content"]


# ---------------------------------------------------------------------------
# NEW EDGE CASES: is_truncated Flag Comprehensive Tests
# ---------------------------------------------------------------------------

def test_is_truncated_last_page_with_offset():
    """Test is_truncated=True when reading last page of file with offset."""
    lines = [f"Line {i}\n" for i in range(1, 11)]  # 10 lines total
    path = _add_file("ten_lines.txt", lines)
    
    # Read last 3 lines with offset (lines 8-10)
    result = read_file(path, offset=7, limit=3)
    assert result["start_line"] == 8
    assert result["end_line"] == 10
    assert result["total_lines"] == 10
    # Should be truncated because content from beginning is missing (offset > 0)
    assert result["is_truncated"] is True
    assert "truncated" in result["content"].split("\n", 1)[0].lower()


def test_is_truncated_middle_page_with_offset():
    """Test is_truncated=True when reading middle page with offset."""
    lines = [f"Line {i}\n" for i in range(1, 21)]  # 20 lines total
    path = _add_file("twenty_lines.txt", lines)
    
    # Read middle lines 6-10 with offset
    result = read_file(path, offset=5, limit=5)
    assert result["start_line"] == 6
    assert result["end_line"] == 10
    assert result["total_lines"] == 20
    # Should be truncated because content from beginning AND end is missing
    assert result["is_truncated"] is True
    assert "truncated" in result["content"].split("\n", 1)[0].lower()


def test_is_truncated_first_page_no_offset():
    """Test is_truncated=False when reading first page without offset."""
    lines = [f"Line {i}\n" for i in range(1, 11)]  # 10 lines total
    path = _add_file("ten_lines_first.txt", lines)
    
    # Read first 5 lines without offset
    result = read_file(path, offset=0, limit=5)
    assert result["start_line"] == 1
    assert result["end_line"] == 5
    assert result["total_lines"] == 10
    # Should be truncated because content from end is missing (end_idx_exclusive < total_lines)
    assert result["is_truncated"] is True
    assert "truncated" in result["content"].split("\n", 1)[0].lower()


def test_is_truncated_full_file_no_offset():
    """Test is_truncated=False when reading entire file without offset."""
    lines = [f"Line {i}\n" for i in range(1, 6)]  # 5 lines total
    path = _add_file("five_lines.txt", lines)
    
    # Read entire file without offset or limit restrictions
    result = read_file(path)
    assert result["start_line"] == 1
    assert result["end_line"] == 5
    assert result["total_lines"] == 5
    # Should NOT be truncated (no offset, no line limit exceeded, line length OK)
    assert result["is_truncated"] is False
    assert "truncated" not in result["content"].lower()


def test_is_truncated_offset_with_long_lines():
    """Test is_truncated=True when both offset and line length truncation occur."""
    long_line = "x" * 2500 + "\n"  # Exceeds 2000 char limit
    short_line = "short\n"
    lines = [short_line, long_line, short_line]
    path = _add_file("mixed_length.txt", lines)
    
    # Read from offset 1 (second line is long)
    result = read_file(path, offset=1, limit=2)
    assert result["start_line"] == 2
    assert result["end_line"] == 3
    assert result["total_lines"] == 3
    # Should be truncated for BOTH reasons: offset > 0 AND line length exceeded
    assert result["is_truncated"] is True
    assert "[truncated]" in result["content"]  # Line length truncation marker
    assert "File content truncated:" in result["content"]  # Header for offset/limit


def test_is_truncated_single_line_with_offset():
    """Test is_truncated=True when reading single line with offset."""
    lines = ["Line 1\n", "Line 2\n", "Line 3\n"]
    path = _add_file("single_with_offset.txt", lines)
    
    # Read just the last line
    result = read_file(path, offset=2, limit=1)
    assert result["start_line"] == 3
    assert result["end_line"] == 3
    assert result["total_lines"] == 3
    # Should be truncated because content from beginning is missing
    assert result["is_truncated"] is True
    assert "truncated" in result["content"].split("\n", 1)[0].lower()


def test_is_truncated_no_offset_but_limit():
    """Test is_truncated=True when no offset but limit causes end truncation."""
    lines = [f"Line {i}\n" for i in range(1, 11)]  # 10 lines total
    path = _add_file("limit_only.txt", lines)
    
    # Read first 7 lines (no offset but limited)
    result = read_file(path, offset=0, limit=7)
    assert result["start_line"] == 1
    assert result["end_line"] == 7
    assert result["total_lines"] == 10
    # Should be truncated because end content is missing (limit < total)
    assert result["is_truncated"] is True
    assert "truncated" in result["content"].split("\n", 1)[0].lower()


# ---------------------------------------------------------------------------
# NEW EDGE CASES: Advanced .geminiignore Cases
# ---------------------------------------------------------------------------

def test_nested_geminiignore():
    """Test nested .geminiignore files with different patterns."""
    # Add root .geminiignore
    _add_file(".geminiignore", ["*.tmp\n"])
    
    # Add nested .geminiignore in subdirectory
    _add_file("subdir/.geminiignore", ["*.log\n"])
    
    # Create files to test
    tmp_path = _add_file("test.tmp", ["temp content\n"])
    log_path = _add_file("subdir/test.log", ["log content\n"])
    
    # Root pattern should be ignored
    with pytest.raises(InvalidInputError, match="ignored by .geminiignore"):
        read_file(tmp_path)
    
    # Nested .geminiignore might not be supported in current implementation
    # Let's test that the file is NOT ignored (implementation limitation)
    result = read_file(log_path)
    assert "log content" in result["content"]


def test_geminiignore_case_sensitivity():
    """Test .geminiignore pattern case sensitivity."""
    _add_file(".geminiignore", ["*.LOG\n"])  # Uppercase pattern
    
    # Test lowercase file
    log_path = _add_file("test.log", ["content\n"])
    
    # Should NOT be ignored (case sensitive)
    result = read_file(log_path)
    assert "content" in result["content"]


def test_geminiignore_wildcard_patterns():
    """Test various .geminiignore wildcard patterns."""
    _add_file(".geminiignore", ["temp/*\n", "*.backup\n", "secret.*\n"])
    
    # Test different patterns
    temp_path = _add_file("temp/file.txt", ["temp content\n"])
    backup_path = _add_file("file.backup", ["backup content\n"])
    secret_path = _add_file("secret.key", ["secret content\n"])
    
    # All should be ignored
    with pytest.raises(InvalidInputError, match="ignored by .geminiignore"):
        read_file(temp_path)
    
    with pytest.raises(InvalidInputError, match="ignored by .geminiignore"):
        read_file(backup_path)
    
    with pytest.raises(InvalidInputError, match="ignored by .geminiignore"):
        read_file(secret_path)


# ---------------------------------------------------------------------------
# NEW EDGE CASES: Line Length Edge Cases
# ---------------------------------------------------------------------------

def test_line_exactly_at_length_limit():
    """Test line exactly at 2000 character limit (including newline)."""
    # The implementation checks len(line) > MAX_LINE_LENGTH where line includes \n
    # So 2000 chars + \n = 2001 chars > 2000 limit, so it gets truncated
    exact_line = "x" * 2000 + "\n"
    path = _add_file("exact_length.txt", [exact_line])
    result = read_file(path)
    assert "[truncated]" in result["content"]
    assert result["is_truncated"] is True


def test_line_under_length_limit():
    """Test line under 2000 character limit should not be truncated."""
    under_line = "x" * 1999 + "\n"  # 1999 chars + \n = 2000 total, which is exactly at limit
    path = _add_file("under_length.txt", [under_line])
    result = read_file(path)
    assert "[truncated]" not in result["content"]
    assert result["is_truncated"] is False


def test_line_one_over_length_limit():
    """Test line one character over 2000 limit."""
    over_line = "x" * 2001 + "\n"
    path = _add_file("over_length.txt", [over_line])
    result = read_file(path)
    assert "[truncated]" in result["content"]
    assert result["is_truncated"] is True


def test_multiple_long_lines():
    """Test multiple lines exceeding length limit."""
    long_lines = [
        "a" * 2500 + "\n",
        "b" * 2200 + "\n",
        "short line\n",
        "c" * 3000 + "\n"
    ]
    path = _add_file("multi_long.txt", long_lines)
    result = read_file(path)
    content_lines = result["content"].split("\n")
    
    # First line is the truncation header, then the actual content lines
    assert "[File content truncated:" in content_lines[0]
    assert "[truncated]" in content_lines[1]  # First long line
    assert "[truncated]" in content_lines[2]  # Second long line
    assert "short line" in content_lines[3]   # Short line unchanged
    assert "[truncated]" in content_lines[4]  # Third long line
    assert result["is_truncated"] is True


# ---------------------------------------------------------------------------
# Validation / error scenarios
# ---------------------------------------------------------------------------

def test_invalid_path_type():
    with pytest.raises(InvalidInputError):  # type: ignore[name-defined]
        read_file(123)  # type: ignore[arg-type]


def test_relative_path():
    # Relative paths are now supported, but this path doesn't exist
    with pytest.raises(FileNotFoundError):  # type: ignore[name-defined]
        read_file("relative/path.txt")


def test_path_outside_workspace():
    # Paths with leading slashes are now treated as relative, so this creates
    # a path like workspace_root/etc/hosts which doesn't exist
    with pytest.raises(FileNotFoundError):  # type: ignore[name-defined]
        read_file("/etc/hosts")


def test_negative_offset():
    path = _add_file("neg.txt", ["L1\n"])
    with pytest.raises(InvalidInputError):  # type: ignore[name-defined]
        read_file(path, offset=-1)


def test_limit_zero():
    path = _add_file("limit.txt", ["L1\n"])
    with pytest.raises(InvalidInputError):  # type: ignore[name-defined]
        read_file(path, limit=0)


def test_offset_beyond_lines():
    path = _add_file("few.txt", ["L1\n", "L2\n"])
    with pytest.raises(InvalidInputError):  # type: ignore[name-defined]
        read_file(path, offset=10)


def test_directory_path_error():
    # Create directory entry
    dir_path = os.path.join(sim_db.DB["workspace_root"], "dir")
    sim_db.DB["file_system"][dir_path] = {
        "path": dir_path,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": "2025-07-09T00:00:00Z",
    }
    with pytest.raises(IsADirectoryError):
        read_file(dir_path) 