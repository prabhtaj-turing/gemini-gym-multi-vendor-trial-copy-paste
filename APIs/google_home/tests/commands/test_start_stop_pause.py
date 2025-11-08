import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home import run as gh_run, details as gh_details


class TestStartStopPause(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_vacuum(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("VACUUM", []).append(
            {
                "id": "vac-1",
                "names": ["Vacuum"],
                "types": ["VACUUM"],
                "traits": ["StartStop", "TransportControl"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "isStopped", "value": False},
                    {"name": "isPaused", "value": False},
                ],
            }
        )
        return "vac-1"

    def test_start_sets_not_stopped(self):
        did = self._add_vacuum()
        gh_run(devices=[did], op="start")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isStopped")
        self.assertFalse(st["value"])

    def test_stop_sets_stopped(self):
        did = self._add_vacuum()
        gh_run(devices=[did], op="stop")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isStopped")
        self.assertTrue(st["value"])

    def test_pause_sets_paused(self):
        did = self._add_vacuum()
        gh_run(devices=[did], op="pause")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isPaused")
        self.assertTrue(st["value"])

    def test_unpause_clears_paused(self):
        did = self._add_vacuum()
        gh_run(devices=[did], op="unpause")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isPaused")
        self.assertFalse(st["value"])
