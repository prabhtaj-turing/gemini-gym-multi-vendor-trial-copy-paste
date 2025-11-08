"""
db.py – central bootstrap for the MySQL-simulation engine.

* Instantiates a persistent `DuckDBManager`.
* Loads a JSON snapshot of attachments + aliases.
* If the snapshot and on-disk *.duckdb* files diverge, prints a warning
  and rewrites the JSON so they are back in sync.

Public API kept intact:
    - DB               : in-memory dict mirroring the JSON
    - save_state(path) : dump DB to disk
    - load_state(path) : overwrite DB from disk and re-apply error-sim
"""

from __future__ import annotations

import json
import os
import warnings
from typing import Optional
import atexit

from mysql.SimulationEngine.duckdb_manager import DuckDBManager

# --------------------------------------------------------------------------- #
#  Paths & manager                                                            #
# --------------------------------------------------------------------------- #

MAIN_DB_URL = "main_db.duckdb"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DB_DIR = os.path.join(BASE_DIR, "SampleDBs")

SIMULATION_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR))),
    "DBs",
    "MySqlDefaultDB.json",
)

db_manager = DuckDBManager(
    main_url=MAIN_DB_URL,
    database_directory=SAMPLE_DB_DIR,
    simulation_state_path=SIMULATION_DEFAULT_DB_PATH,
)

atexit.register(db_manager.close_main_connection)

# --------------------------------------------------------------------------- #
#  Helper – read & validate JSON snapshot                                     #
# --------------------------------------------------------------------------- #


def _load_json(path: str) -> dict:
    """Return a *valid* snapshot dict; never raises on corrupt/missing file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _scan_duckdb_files() -> dict[str, str]:
    """Return {alias: rel_path} for every *.duckdb in SAMPLE_DB_DIR."""
    mapping = {}
    for fname in os.listdir(SAMPLE_DB_DIR):
        if not fname.endswith(".duckdb"):
            continue
        user_alias = os.path.splitext(fname)[0]
        rel_path = fname
        mapping[user_alias] = rel_path
    return mapping


def _sync_snapshot(snapshot: dict) -> dict:
    """
    Ensure `snapshot["attached"][alias]["path"]` matches the files that
    actually exist in SAMPLE_DB_DIR.  If not, patch & warn.
    """
    current_files = _scan_duckdb_files()
    snap_attached = snapshot.get("attached", {})

    snap_files = {a: info.get("path") for a, info in snap_attached.items()}
    if snap_files == current_files:
        return snapshot  # already in sync

    warnings.warn("Simulation JSON was out of sync with DB folder – fixing.")
    new_attached = {}
    for alias, rel in current_files.items():
        new_attached[alias] = {
            "sanitized": db_manager._sanitize_for_duckdb_alias_and_filename(alias),
            "path": rel,
        }
    snapshot["attached"] = new_attached
    snapshot.setdefault("current", db_manager._main_db_alias)
    snapshot.setdefault("primary_internal_name", db_manager._main_db_alias)

    # Write back immediately
    os.makedirs(os.path.dirname(SIMULATION_DEFAULT_DB_PATH), exist_ok=True)
    with open(SIMULATION_DEFAULT_DB_PATH, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2)

    return snapshot


# --------------------------------------------------------------------------- #
#  In-memory representation exposed as `DB`                                   #
# --------------------------------------------------------------------------- #

DB: dict = _sync_snapshot(_load_json(SIMULATION_DEFAULT_DB_PATH))

# --------------------------------------------------------------------------- #
#  Convenience save/load wrappers (public API)                                #
# --------------------------------------------------------------------------- #


def save_state(filepath: str) -> None:
    """Serialize the *current* DB dict to `filepath`."""
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(DB, fh, indent=2)


def load_state(
    filepath: str,
    error_config_path: str = "./error_config.json",
    error_definitions_path: str = "./error_definitions.json",
) -> None:
    """
    Replace in-memory DB with the contents of `filepath`.
    """
    global DB
    with open(filepath, "r", encoding="utf-8") as fh:
        new_data = json.load(fh)
        DB.clear()
        DB.update(new_data)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
