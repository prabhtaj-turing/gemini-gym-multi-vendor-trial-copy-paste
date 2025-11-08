import unittest
import time
import psutil
import os
import gc
import concurrent.futures

from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_home.SimulationEngine.db import DB
from google_home.devices_api import devices
from google_home.get_devices_api import get_devices
from google_home.run_api import run
from google_home.mutate_api import mutate
from google_home.view_schedules_api import view_schedules
from google_home.cancel_schedules_api import cancel_schedules
from google_home.SimulationEngine.custom_errors import NoSchedulesFoundError


class TestGoogleHomePerformance(BaseTestCaseWithErrorHandler):
    """Performance tests for Google Home API operations."""

    def setUp(self):
        super().setUp()
        self.process = psutil.Process(os.getpid())

        # Minimal seed
        DB.clear()
        DB.update({
            "structures": {
                "Home": {
                    "name": "Home",
                    "rooms": {
                        "Living": {
                            "name": "Living",
                            "devices": {
                                "LIGHT": [
                                    {
                                        "id": "light-perf-0",
                                        "names": ["Perf Lamp 0"],
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff", "Brightness", "ViewSchedules"],
                                        "room_name": "Living",
                                        "structure": "Home",
                                        "toggles_modes": [],
                                        "device_state": [
                                            {"name": "on", "value": False},
                                            {"name": "brightness", "value": 0.5},
                                            {"name": "schedules", "value": []},
                                        ],
                                    }
                                ]
                            },
                        }
                    },
                }
            },
            "actions": [],
        })

    def tearDown(self):
        super().tearDown()
        DB.clear()

    def test_memory_usage_device_operations(self):
        """Test memory usage during multiple device operations."""
        initial_memory = self.process.memory_info().rss

        for _ in range(50):
            devices()
            get_devices(include_state=True)

        gc.collect()
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory

        self.assertLess(
            memory_increase,
            8 * 1024 * 1024,
            f"Memory increase {memory_increase / 1024 / 1024:.2f}MB exceeds 8MB limit",
        )

    def test_run_response_time(self):
        """Test command execution response time."""
        start_time = time.time()
        result = run(devices=["light-perf-0"], op="on")
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 0.5, f"run() took {execution_time:.3f}s, should be < 0.5s")
        self.assertEqual(result[0]["result"], "SUCCESS")

    def test_list_devices_performance_large_dataset(self):
        """Test listing performance with a larger dataset."""
        # Add additional 500 lights
        lights = DB["structures"]["Home"]["rooms"]["Living"]["devices"]["LIGHT"]
        for i in range(1, 501):
            lights.append({
                "id": f"light-perf-{i}",
                "names": [f"Perf Lamp {i}"],
                "types": ["LIGHT"],
                "traits": ["OnOff"],
                "room_name": "Living",
                "structure": "Home",
                "toggles_modes": [],
                "device_state": [{"name": "on", "value": False}],
            })

        start_time = time.time()
        result = get_devices(include_state=False)
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 1.5, f"get_devices() took {execution_time:.3f}s, should be < 1.5s")
        self.assertGreaterEqual(len(result["devices"]), 501)

    def test_concurrent_mutations(self):
        """Test performance under concurrent load of run() operations."""
        # Ensure some devices exist
        lights = DB["structures"]["Home"]["rooms"]["Living"]["devices"]["LIGHT"]
        for i in range(501, 521):
            lights.append({
                "id": f"light-perf-{i}",
                "names": [f"Perf Lamp {i}"],
                "types": ["LIGHT"],
                "traits": ["OnOff"],
                "room_name": "Living",
                "structure": "Home",
                "toggles_modes": [],
                "device_state": [{"name": "on", "value": False}],
            })

        def toggle_worker(i):
            return run(devices=[f"light-perf-{i}"], op="toggle_on_off")

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(toggle_worker, i) for i in range(501, 521)]
            results = [f.result() for f in futures]
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 5.0, f"Concurrent run() took {execution_time:.3f}s, should be < 5.0s")
        self.assertTrue(all(r[0]["result"] == "SUCCESS" for r in results))

    def test_mixed_operations_performance(self):
        """Test performance with mixed operations simulating real usage."""
        start_time = time.time()

        for i in range(10):
            devices()
            get_devices(include_state=(i % 2 == 0))
            run(devices=["light-perf-0"], op=("on" if i % 2 == 0 else "off"))
            view_schedules()
            try:
                cancel_schedules()
            except NoSchedulesFoundError:
                # Acceptable when there are no schedules present
                pass
            mutate(devices=["light-perf-0"], traits=["OnOff"], commands=["toggle_on_off"], values=[])

        execution_time = time.time() - start_time
        self.assertLess(execution_time, 5.0, f"Mixed operations took {execution_time:.3f}s, should be < 5.0s")


if __name__ == "__main__":
    unittest.main()


