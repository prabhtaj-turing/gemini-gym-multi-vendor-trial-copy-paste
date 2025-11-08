import unittest
import time
import psutil
import os
import gc
import tempfile
import threading
import concurrent.futures
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from .. import (
    create_meeting_space,
    get_meeting_space_details,
    list_conference_records,
    list_conference_participants,
    get_conference_participant,
)


class TestGoogleMeetPerformance(BaseTestCaseWithErrorHandler):
    """Performance tests for Google Meet API operations."""

    def setUp(self):
        """Set up test environment with performance monitoring."""
        super().setUp()
        self.process = psutil.Process(os.getpid())

        # Set up test data
        self.test_space_id = "test_space_perf"
        DB['spaces'][self.test_space_id] = {
            "name": f"spaces/{self.test_space_id}",
            "meetingUri": f"https://meet.google.com/{self.test_space_id}",
            "meetingCode": self.test_space_id,
            "accessType": "OPEN"
        }

        self.test_conference_id = "test_conference_perf"
        DB['conferenceRecords'][self.test_conference_id] = {
            "name": f"conferenceRecords/{self.test_conference_id}",
            "space": f"spaces/{self.test_space_id}",
            "state": "ACTIVE"
        }

        self.test_participant_id = "test_participant_perf"
        DB['participants'][self.test_participant_id] = {
            "name": f"conferenceRecords/{self.test_conference_id}/participants/{self.test_participant_id}",
        }

    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()

    def test_memory_usage_space_operations(self):
        """Test memory usage during multiple space operations."""
        initial_memory = self.process.memory_info().rss

        # Perform multiple space operations
        for i in range(50):
            space_name = f"spaces/mem_test_space_{i}"
            space_content = {
                "meetingCode": f"perf-test-code-{i}",
                "meetingUri": f"https://meet.google.com/perf-test-code-{i}",
                "accessType": "OPEN"
            }
            create_meeting_space(space_name=space_name, space_content=space_content)
            get_meeting_space_details(name=space_name)

        gc.collect()

        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory

        self.assertLess(memory_increase, 5 * 1024 * 1024,
                       f"Memory increase {memory_increase / 1024 / 1024:.2f}MB exceeds 5MB limit")

    def test_create_space_response_time(self):
        """Test space creation response time."""
        start_time = time.time()
        space_content = {
            "meetingCode": "new-space-code",
            "meetingUri": "https://meet.google.com/new-space-code",
            "accessType": "OPEN"
        }
        result = create_meeting_space(space_name="spaces/new_space", space_content=space_content)
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 0.5,
                       f"Space creation took {execution_time:.3f}s, should be < 0.5s")
        self.assertIn('message', result)

    def test_list_conferences_performance(self):
        """Test listing conference records performance with large datasets."""
        for i in range(100):
            conf_id = f"conf_{i}"
            DB['conferenceRecords'][conf_id] = {"name": f"conferenceRecords/{conf_id}"}

        start_time = time.time()
        result = list_conference_records(pageSize=50)
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 1.0,
                       f"List conferences took {execution_time:.3f}s, should be < 1.0s")
        self.assertEqual(len(result['conferenceRecords']), 50)

    def test_concurrent_space_creation(self):
        """Test performance under concurrent load."""
        def create_space_worker(i):
            space_content = {
                "meetingCode": f"concurrent-space-code-{i}",
                "meetingUri": f"https://meet.google.com/concurrent-space-code-{i}",
                "accessType": "OPEN"
            }
            return create_meeting_space(space_name=f"spaces/concurrent_space_{i}", space_content=space_content)

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_space_worker, i) for i in range(20)]
            results = [future.result() for future in futures]

        execution_time = time.time() - start_time

        self.assertLess(execution_time, 5.0,
                       f"Concurrent operations took {execution_time:.3f}s, should be < 5.0s")
        self.assertTrue(all('message' in result for result in results))

    def test_mixed_operations_performance(self):
        """Test performance with mixed operations simulating real usage."""
        start_time = time.time()

        for i in range(10):
            space_name = f"spaces/mixed_space_{i}"
            space_content = {
                "meetingCode": f"mixed-space-code-{i}",
                "meetingUri": f"https://meet.google.com/mixed-space-code-{i}",
                "accessType": "OPEN"
            }
            space = create_meeting_space(space_name=space_name, space_content=space_content)
            get_meeting_space_details(name=space_name)
            list_conference_records(pageSize=10)
            list_conference_participants(parent=f"conferenceRecords/{self.test_conference_id}")

        execution_time = time.time() - start_time

        self.assertLess(execution_time, 5.0,
                       f"Mixed operations took {execution_time:.3f}s, should be < 5.0s")


if __name__ == '__main__':
    unittest.main()
