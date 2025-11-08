import json
import os
import sys
from pathlib import Path

import pytest

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli.SimulationEngine import db as sim_db  # noqa: E402
from gemini_cli.SimulationEngine.utils import resolve_workspace_path  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError  # noqa: E402


DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def reload_db():
    """Load fresh DB snapshot before each test."""
    sim_db.DB.clear()
    with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
        sim_db.DB.update(json.load(fh))
    yield
    sim_db.DB.clear()


def test_resolve_slash_maps_to_workspace_root():
    root = sim_db.DB["workspace_root"]
    resolved = resolve_workspace_path("/", root)
    assert os.path.normpath(resolved) == os.path.normpath(root)


def test_resolve_absolute_within_workspace_returns_same():
    root = sim_db.DB["workspace_root"]
    # Take a known child path from default DB
    child = os.path.join(root, "src")
    resolved = resolve_workspace_path(child, root)
    assert os.path.normpath(resolved) == os.path.normpath(child)


def test_resolve_absolute_outside_workspace_treated_as_relative():
    """Test that absolute paths outside workspace are treated as relative (like cursor)."""
    root = sim_db.DB["workspace_root"]
    outside = "/etc"
    resolved = resolve_workspace_path(outside, root)
    # Absolute path outside workspace gets treated as relative
    expected = os.path.normpath(os.path.join(root, "etc"))
    assert resolved == expected


def test_resolve_relative_returns_joined_path():
    """Test that relative paths are joined with workspace root."""
    root = sim_db.DB["workspace_root"]
    relative = "some/relative/path"
    resolved = resolve_workspace_path(relative, root)
    expected = os.path.normpath(os.path.join(root, relative))
    assert resolved == expected


def test_resolve_empty_string_maps_to_workspace_root():
    """Test that empty string maps to workspace root."""
    root = sim_db.DB["workspace_root"]
    resolved = resolve_workspace_path("", root)
    assert os.path.normpath(resolved) == os.path.normpath(root)


def test_resolve_dot_maps_to_workspace_root():
    """Test that '.' maps to workspace root."""
    root = sim_db.DB["workspace_root"]
    resolved = resolve_workspace_path(".", root)
    assert os.path.normpath(resolved) == os.path.normpath(root)


def test_resolve_leading_slash_stripped():
    """Test that leading slashes are stripped for relative path processing."""
    root = sim_db.DB["workspace_root"]
    resolved = resolve_workspace_path("/src/test", root)
    expected = os.path.normpath(os.path.join(root, "src/test"))
    assert resolved == expected


def test_resolve_multiple_slashes_handled():
    """Test that multiple leading slashes are handled correctly."""
    root = sim_db.DB["workspace_root"]
    resolved = resolve_workspace_path("///", root)
    assert os.path.normpath(resolved) == os.path.normpath(root)


def test_resolve_invalid_inputs_raise():
    root = sim_db.DB["workspace_root"]
    with pytest.raises(InvalidInputError):
        resolve_workspace_path(None, root)  # Changed from "" to None since empty string is now valid
    with pytest.raises(InvalidInputError):
        resolve_workspace_path("/", "")
    with pytest.raises(InvalidInputError):
        resolve_workspace_path("/", "not/abs")


def test_resolve_relative_subdirectory():
    """Test resolving relative paths to subdirectories."""
    root = sim_db.DB["workspace_root"]
    resolved = resolve_workspace_path("Scripts/test.py", root)
    expected = os.path.normpath(os.path.join(root, "Scripts/test.py"))
    assert resolved == expected


def test_resolve_path_traversal_attempts():
    """Test that path traversal attempts are resolved (but will be caught by validation later)."""
    root = sim_db.DB["workspace_root"]
    resolved = resolve_workspace_path("../../etc", root)
    expected = os.path.normpath(os.path.join(root, "../../etc"))
    assert resolved == expected

