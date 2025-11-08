import json
import os
import sys
from pathlib import Path
from typing import List

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli.SimulationEngine import db as sim_db  # noqa: E402
from gemini_cli.SimulationEngine.file_utils import (  # noqa: E402
    _load_geminiignore_patterns,
    _is_ignored,
)
from gemini_cli import read_file  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError  # noqa: E402

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def reload_db():
    sim_db.DB.clear()
    with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
        sim_db.DB.update(json.load(fh))
    yield
    sim_db.DB.clear()


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


def _add_fs_entry(path_in_ws: str, *, is_dir: bool = False, lines: List[str] | None = None, size_bytes: int | None = None, extra: dict | None = None):  # noqa: ANN001
    root = sim_db.DB["workspace_root"]
    abs_path = os.path.join(root, path_in_ws.replace("/", os.sep))
    meta = {
        "path": abs_path,
        "is_directory": is_dir,
        "content_lines": [] if lines is None else lines,
        "size_bytes": size_bytes if size_bytes is not None else 0,
        "last_modified": "2025-07-09T00:00:00Z",
    }
    if extra:
        meta.update(extra)
    sim_db.DB["file_system"][abs_path] = meta
    return abs_path


# ---------------------------------------------------------------------------
# Tests for _load_geminiignore_patterns and _is_ignored
# ---------------------------------------------------------------------------


def test_load_patterns_parses_comments_and_blanks():
    _add_fs_entry(
        ".geminiignore",
        lines=["# comment\n", "\n", "*.log\n", "secret.*\n"],
    )
    patterns = _load_geminiignore_patterns(sim_db.DB["file_system"], sim_db.DB["workspace_root"])
    assert patterns == ["*.log", "secret.*"]


def test_is_ignored_matches_patterns():
    _add_fs_entry(
        ".geminiignore",
        lines=["secret.*\n", "*.log\n"],
    )
    root = sim_db.DB["workspace_root"]
    file_secret = os.path.join(root, "secret.txt")
    file_log = os.path.join(root, "debug.log")
    assert _is_ignored(file_secret, root, sim_db.DB["file_system"]) is True
    assert _is_ignored(file_log, root, sim_db.DB["file_system"]) is True
    file_ok = os.path.join(root, "readme.md")
    assert _is_ignored(file_ok, root, sim_db.DB["file_system"]) is False


def test_is_ignored_no_file():
    root = sim_db.DB["workspace_root"]
    file_path = os.path.join(root, "x.txt")
    assert _is_ignored(file_path, root, sim_db.DB["file_system"]) is False


def test_read_file_size_limit():
    # create huge file entry (size_bytes > 20MB)
    big_path = _add_fs_entry(
        "big.bin",
        lines=[],
        size_bytes=21 * 1024 * 1024,
        extra={"content_b64": ""},
    )
    with pytest.raises(ValueError):
        read_file(big_path) 