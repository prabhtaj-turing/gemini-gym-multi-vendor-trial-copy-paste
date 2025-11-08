import json
import os
from pathlib import Path

import pytest

from google_home.SimulationEngine import db as gh_db


ASSETS_DIR = Path(os.path.dirname(__file__)) / "assets"


@pytest.fixture(autouse=True)
def _reset_db_between_tests():
    original = json.loads(json.dumps(gh_db.DB))  # deep copy
    try:
        yield
    finally:
        gh_db.DB.clear()
        gh_db.DB.update(original)


def _load_state_in_place(path: Path) -> None:
    """Use module's load_state (it preserves identity)."""
    gh_db.load_state(str(path))


def _restore_default_data_in_place() -> None:
    gh_db.restore_default_data()


def test_load_state_from_assets_minimal():
    """
    Loading from an assets JSON should populate the in-memory DB using the pydantic model.
    """
    target = ASSETS_DIR / "google_home_db_minimal.json"
    assert target.exists(), f"Missing test asset: {target}"

    gh_db.DB.clear()
    _load_state_in_place(target)

    assert "structures" in gh_db.DB
    assert "TestHome" in gh_db.DB["structures"]
    devices = (
        gh_db.DB["structures"]["TestHome"]["rooms"]["Lab"]["devices"]["LIGHT"]
    )
    assert any(d["id"] == "light-asset" for d in devices)


def test_save_and_load_roundtrip(tmp_path: Path):
    """
    Saving to disk and loading back should preserve the DB contents.
    """
    # Prepare a tiny DB
    gh_db.DB.clear()
    gh_db.DB.update(
        {
            "structures": {
                "Home": {
                    "name": "Home",
                    "rooms": {
                        "Living": {
                            "name": "Living",
                            "devices": {
                                "LIGHT": [
                                    {
                                        "id": "L1",
                                        "names": ["Lamp"],
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff"],
                                        "room_name": "Living",
                                        "structure": "Home",
                                        "toggles_modes": [],
                                        "device_state": [
                                            {"name": "on", "value": False}
                                        ],
                                    }
                                ]
                            },
                        }
                    },
                }
            },
            "actions": [],
        }
    )

    save_path = tmp_path / "roundtrip_db.json"
    gh_db.save_state(str(save_path))

    # Mutate memory then load from file to prove it restores
    gh_db.DB.clear()
    _load_state_in_place(save_path)

    assert gh_db.DB["structures"]["Home"]["rooms"]["Living"]["devices"]["LIGHT"][0]["id"] == "L1"


def test_load_legacy_asset_is_backward_compatible():
    """
    Older DB files (e.g., without explicit actions) must still load.
    """
    legacy = ASSETS_DIR / "google_home_db_legacy.json"
    assert legacy.exists(), f"Missing test asset: {legacy}"

    gh_db.DB.clear()
    _load_state_in_place(legacy)

    # Basic shape and a known device id
    assert "structures" in gh_db.DB
    assert "LegacyHome" in gh_db.DB["structures"]
    light = gh_db.DB["structures"]["LegacyHome"]["rooms"]["Den"]["devices"]["LIGHT"][0]
    assert light["id"] == "legacy-light"


def test_restore_default_data_does_not_break_existing_files(tmp_path: Path):
    """
    Ensure our default-db loader still works and produces a loadable state to disk.
    """
    _restore_default_data_in_place()  # loads from DBs/GoogleHomeDefaultDB.json if available
    assert "structures" in gh_db.DB and len(gh_db.DB["structures"]) >= 1

    save_path = tmp_path / "default_dump.json"
    gh_db.save_state(str(save_path))

    # Load back and check a couple of top-level keys
    gh_db.DB.clear()
    gh_db.load_state(str(save_path))
    assert "structures" in gh_db.DB

