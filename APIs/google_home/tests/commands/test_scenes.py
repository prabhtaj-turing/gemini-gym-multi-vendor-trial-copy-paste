import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home import run as gh_run


class TestScenes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_scene(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("SCENE", []).append(
            {
                "id": "scene-1",
                "names": ["Movie Night"],
                "types": ["SCENE"],
                "traits": ["Scene"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [],
            }
        )
        return "scene-1"

    def test_activate_scene_stateless_success(self):
        did = self._add_scene()
        res = gh_run(devices=[did], op="activate_scene")  # type: ignore
        self.assertEqual(res[0]["result"], "SUCCESS")

    def test_deactivate_scene_stateless_success(self):
        did = self._add_scene()
        res = gh_run(devices=[did], op="deactivate_scene")  # type: ignore
        self.assertEqual(res[0]["result"], "SUCCESS")


