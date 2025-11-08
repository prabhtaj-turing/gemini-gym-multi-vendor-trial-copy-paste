"""
Test suite for get_logs functionality in the Supabase API simulation.
"""
import copy
import unittest
from datetime import datetime, timezone, timedelta

from supabase.SimulationEngine import custom_errors
from supabase.SimulationEngine.db import DB
from supabase.SimulationEngine.models import LogEntry, LogLevel, ProjectLogs
from supabase.logs import get_logs
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Initial DB state for get_logs function tests
GET_LOGS_INITIAL_DB_STATE = {
    "organizations": [
        {
            "id": "org_abc123",
            "name": "Acme Corp",
            "created_at": "2023-01-15T10:00:00Z",
            "subscription_plan": {
                "id": "plan_pro",
                "name": "Pro Plan",
                "price": 25.00,
                "currency": "USD",
                "features": [
                    "unlimited_projects",
                    "priority_support",
                    "daily_backups",
                    "branching_enabled"
                ]
            }
        }
    ],
    "projects": [
        {
            "id": "proj_1a2b3c",
            "name": "Acme CRM",
            "organization_id": "org_abc123",
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2023-02-01T09:15:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_no_logs",
            "name": "No Logs Project",
            "organization_id": "org_abc123",
            "region": "us-west-2",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2023-03-01T10:00:00Z",
            "version": "PostgreSQL 15"
        }
    ],
    "logs": {}
}


class TestGetLogs(BaseTestCaseWithErrorHandler):
    """
    Test suite for the get_logs function.
    """
    
    def validate_log_entries(self, logs):
        """Validate that logs conform to LogEntry model structure."""
        self.assertIsInstance(logs, list)
        for log in logs:
            # This will raise ValidationError if structure is incorrect
            LogEntry(**log)

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(GET_LOGS_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Set up test state before each test."""
        # Reset logs for each test
        current_time = datetime.now(timezone.utc)
        thirty_seconds_ago = current_time - timedelta(seconds=30)
        two_minutes_ago = current_time - timedelta(minutes=2)
        
        DB['logs'] = {
            "proj_1a2b3c": {
                "api": [
                    {
                        "timestamp": thirty_seconds_ago.isoformat().replace('+00:00', 'Z'),
                        "level": "INFO",
                        "message": "API request: GET /rest/v1/users",
                        "metadata": {"request_id": "req_12345", "ip_address": "192.168.1.100"}
                    },
                    {
                        "timestamp": two_minutes_ago.isoformat().replace('+00:00', 'Z'),
                        "level": "WARN",
                        "message": "Old API request",
                        "metadata": {"request_id": "req_old"}
                    }
                ],
                "postgres": [
                    {
                        "timestamp": thirty_seconds_ago.isoformat().replace('+00:00', 'Z'),
                        "level": "DEBUG",
                        "message": "DB connection established",
                        "metadata": {}
                    }
                ],
                "edge-function": []  # Empty service logs
            },
            "proj_no_logs": {}  # Project with no log services
        }

    def test_get_logs_success_recent_logs(self):
        """Test successful retrieval of logs within the last minute."""
        logs = get_logs(project_id='proj_1a2b3c', service='api')
        
        # Validate structure using LogEntry model
        self.validate_log_entries(logs)
        
        # Should return only the recent log entry
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['level'], 'INFO')
        self.assertEqual(logs[0]['message'], 'API request: GET /rest/v1/users')
        self.assertEqual(logs[0]['metadata']['request_id'], 'req_12345')

    def test_get_logs_success_multiple_services(self):
        """Test retrieving logs from different services."""
        # Test API logs
        api_logs = get_logs(project_id='proj_1a2b3c', service='api')
        self.validate_log_entries(api_logs)
        self.assertEqual(len(api_logs), 1)
        self.assertEqual(api_logs[0]['message'], 'API request: GET /rest/v1/users')
        
        # Test postgres logs
        postgres_logs = get_logs(project_id='proj_1a2b3c', service='postgres')
        self.validate_log_entries(postgres_logs)
        self.assertEqual(len(postgres_logs), 1)
        self.assertEqual(postgres_logs[0]['message'], 'DB connection established')

    def test_get_logs_filters_old_logs(self):
        """Test that logs older than 1 minute are filtered out."""
        # Add a mix of old and new logs
        current_time = datetime.now(timezone.utc)
        DB['logs']['proj_1a2b3c']['api'] = [
            {
                "timestamp": (current_time - timedelta(seconds=30)).isoformat().replace('+00:00', 'Z'),
                "level": "INFO",
                "message": "Recent log",
                "metadata": {}
            },
            {
                "timestamp": (current_time - timedelta(minutes=2)).isoformat().replace('+00:00', 'Z'),
                "level": "WARN",
                "message": "Old log",
                "metadata": {}
            },
            {
                "timestamp": (current_time - timedelta(seconds=59)).isoformat().replace('+00:00', 'Z'),
                "level": "DEBUG",
                "message": "Just within range",
                "metadata": {}
            }
        ]
        
        logs = get_logs(project_id='proj_1a2b3c', service='api')
        
        # Validate structure using LogEntry model
        self.validate_log_entries(logs)
        
        # Should return only logs within last minute
        self.assertEqual(len(logs), 2)
        messages = [log['message'] for log in logs]
        self.assertIn('Recent log', messages)
        self.assertIn('Just within range', messages)
        self.assertNotIn('Old log', messages)

    def test_get_logs_empty_service_logs_raises_error(self):
        """Test that empty service logs raise LogsNotAvailableError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.LogsNotAvailableError,
            expected_message="No logs found for service 'edge-function' within the last minute. Logs older than 1 minute are not available.",
            project_id='proj_1a2b3c',
            service='edge-function'
        )

    def test_get_logs_service_not_configured_raises_error(self):
        """Test that unconfigured service raises LogsNotAvailableError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.LogsNotAvailableError,
            expected_message="Logs for service 'auth' are not available for project 'proj_1a2b3c'.",
            project_id='proj_1a2b3c',
            service='auth'
        )

    def test_get_logs_project_with_no_logs_raises_error(self):
        """Test that project with no logs configuration raises LogsNotAvailableError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.LogsNotAvailableError,
            expected_message="Logs for service 'api' are not available for project 'proj_no_logs'.",
            project_id='proj_no_logs',
            service='api'
        )

    def test_get_logs_all_logs_too_old_raises_error(self):
        """Test that all logs being too old raises LogsNotAvailableError."""
        # Set all logs to be older than 1 minute
        current_time = datetime.now(timezone.utc)
        DB['logs']['proj_1a2b3c']['api'] = [
            {
                "timestamp": (current_time - timedelta(minutes=2)).isoformat().replace('+00:00', 'Z'),
                "level": "INFO",
                "message": "Old log 1",
                "metadata": {}
            },
            {
                "timestamp": (current_time - timedelta(minutes=5)).isoformat().replace('+00:00', 'Z'),
                "level": "WARN",
                "message": "Old log 2",
                "metadata": {}
            }
        ]
        
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.LogsNotAvailableError,
            expected_message="No logs found for service 'api' within the last minute. Logs older than 1 minute are not available.",
            project_id='proj_1a2b3c',
            service='api'
        )

    def test_get_logs_invalid_timestamps_are_skipped(self):
        """Test that logs with invalid timestamps are skipped."""
        current_time = datetime.now(timezone.utc)
        DB['logs']['proj_1a2b3c']['api'] = [
            {
                "timestamp": "invalid-timestamp",
                "level": "ERROR",
                "message": "Log with invalid timestamp",
                "metadata": {}
            },
            {
                "timestamp": (current_time - timedelta(seconds=30)).isoformat().replace('+00:00', 'Z'),
                "level": "INFO",
                "message": "Valid log",
                "metadata": {}
            },
            {
                # Missing timestamp
                "level": "WARN",
                "message": "Log without timestamp",
                "metadata": {}
            }
        ]
        
        logs = get_logs(project_id='proj_1a2b3c', service='api')
        
        # Validate structure using LogEntry model
        self.validate_log_entries(logs)
        
        # Should return only the valid log
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['message'], 'Valid log')

    # Validation error tests
    def test_get_logs_empty_project_id_raises_validation_error(self):
        """Test that empty project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'project_id' parameter cannot be null or empty.",
            project_id='',
            service='api'
        )

    def test_get_logs_whitespace_project_id_raises_validation_error(self):
        """Test that whitespace-only project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'project_id' parameter cannot be null or empty.",
            project_id='   ',
            service='api'
        )

    def test_get_logs_none_project_id_raises_validation_error(self):
        """Test that None project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'project_id' parameter cannot be null or empty.",
            project_id=None,
            service='api'
        )

    def test_get_logs_integer_project_id_raises_validation_error(self):
        """Test that integer project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'project_id' parameter must be a string.",
            project_id=123,
            service='api'
        )

    def test_get_logs_empty_service_raises_validation_error(self):
        """Test that empty service raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'service' parameter is required.",
            project_id='proj_1a2b3c',
            service=''
        )

    def test_get_logs_none_service_raises_validation_error(self):
        """Test that None service raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'service' parameter is required.",
            project_id='proj_1a2b3c',
            service=None
        )

    def test_get_logs_integer_service_raises_validation_error(self):
        """Test that integer service raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'service' parameter must be a string.",
            project_id='proj_1a2b3c',
            service=123
        )

    def test_get_logs_invalid_service_type_raises_validation_error(self):
        """Test that invalid service type raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid service type 'invalid-service'. Must be one of: api, branch-action, postgres, edge-function, auth, storage, realtime",
            project_id='proj_1a2b3c',
            service='invalid-service'
        )

    def test_get_logs_project_not_found_raises_error(self):
        """Test that non-existent project raises NotFoundError."""
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Project with id 'non_existent_project' not found.",
            project_id='non_existent_project',
            service='api'
        )

    def test_get_logs_all_valid_service_types(self):
        """Test that all valid service types are accepted."""
        valid_services = ['api', 'branch-action', 'postgres', 'edge-function', 'auth', 'storage', 'realtime']
        
        # Set up logs for all services
        current_time = datetime.now(timezone.utc)
        for service in valid_services:
            DB['logs']['proj_1a2b3c'][service] = [
                {
                    "timestamp": (current_time - timedelta(seconds=30)).isoformat().replace('+00:00', 'Z'),
                    "level": "INFO",
                    "message": f"Log for {service}",
                    "metadata": {}
                }
            ]
        
        # Test each service
        for service in valid_services:
            logs = get_logs(project_id='proj_1a2b3c', service=service)
            self.validate_log_entries(logs)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]['message'], f"Log for {service}")

    def test_get_logs_preserves_metadata_structure(self):
        """Test that log metadata is preserved correctly."""
        current_time = datetime.now(timezone.utc)
        DB['logs']['proj_1a2b3c']['api'] = [
            {
                "timestamp": (current_time - timedelta(seconds=15)).isoformat().replace('+00:00', 'Z'),
                "level": "ERROR",
                "message": "Complex metadata test",
                "metadata": {
                    "request_id": "req_complex",
                    "user_id": "user_123",
                    "nested": {
                        "key1": "value1",
                        "key2": 42
                    },
                    "array": [1, 2, 3]
                }
            }
        ]
        
        logs = get_logs(project_id='proj_1a2b3c', service='api')
        
        # Validate structure using LogEntry model
        self.validate_log_entries(logs)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['metadata']['request_id'], 'req_complex')
        self.assertEqual(logs[0]['metadata']['nested']['key1'], 'value1')
        self.assertEqual(logs[0]['metadata']['array'], [1, 2, 3])

    def test_get_logs_edge_case_exactly_one_minute_old(self):
        """Test edge case where log is exactly 1 minute old."""
        current_time = datetime.now(timezone.utc)
        DB['logs']['proj_1a2b3c']['api'] = [
            {
                "timestamp": (current_time - timedelta(minutes=1)).isoformat().replace('+00:00', 'Z'),
                "level": "INFO",
                "message": "Exactly 1 minute old",
                "metadata": {}
            }
        ]
        
        # This should raise error as the log is not within the last minute (>= one_minute_ago excludes exactly 1 minute)
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.LogsNotAvailableError,
            expected_message="No logs found for service 'api' within the last minute. Logs older than 1 minute are not available.",
            project_id='proj_1a2b3c',
            service='api'
        )

    def test_get_logs_malformed_db_structure_no_logs_key(self):
        """Test that missing 'logs' key in DB raises LogsNotAvailableError."""
        # Temporarily remove logs from DB
        logs_backup = DB.pop('logs', None)
        try:
            self.assert_error_behavior(
                func_to_call=get_logs,
                expected_exception_type=custom_errors.LogsNotAvailableError,
                expected_message="Logs for service 'api' are not available for project 'proj_1a2b3c'.",
                project_id='proj_1a2b3c',
                service='api'
            )
        finally:
            if logs_backup is not None:
                DB['logs'] = logs_backup

    def test_get_logs_malformed_db_structure_logs_not_dict(self):
        """Test that malformed 'logs' structure raises LogsNotAvailableError."""
        # Temporarily set logs to non-dict
        logs_backup = DB.get('logs')
        DB['logs'] = "not a dict"
        try:
            self.assert_error_behavior(
                func_to_call=get_logs,
                expected_exception_type=custom_errors.LogsNotAvailableError,
                expected_message="Logs for service 'api' are not available for project 'proj_1a2b3c'.",
                project_id='proj_1a2b3c',
                service='api'
            )
        finally:
            DB['logs'] = logs_backup

    def test_get_logs_malformed_project_logs_not_dict(self):
        """Test that malformed project logs structure raises LogsNotAvailableError."""
        # Set project logs to non-dict
        DB['logs']['proj_1a2b3c'] = "not a dict"
        
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.LogsNotAvailableError,
            expected_message="Logs for service 'api' are not available for project 'proj_1a2b3c'.",
            project_id='proj_1a2b3c',
            service='api'
        )

    def test_get_logs_malformed_service_logs_not_list(self):
        """Test that malformed service logs structure raises LogsNotAvailableError."""
        # Set service logs to non-list
        DB['logs']['proj_1a2b3c']['api'] = "not a list"
        
        self.assert_error_behavior(
            func_to_call=get_logs,
            expected_exception_type=custom_errors.LogsNotAvailableError,
            expected_message="Logs for service 'api' are not available for project 'proj_1a2b3c'.",
            project_id='proj_1a2b3c',
            service='api'
        )

    def test_get_logs_handles_malformed_log_entries(self):
        """Test that malformed log entries are skipped gracefully."""
        current_time = datetime.now(timezone.utc)
        DB['logs']['proj_1a2b3c']['api'] = [
            "not a dict",  # Malformed entry
            {
                "timestamp": (current_time - timedelta(seconds=30)).isoformat().replace('+00:00', 'Z'),
                "level": "INFO",
                "message": "Valid log",
                "metadata": {}
            },
            {"no_timestamp": "missing timestamp field"},  # Missing timestamp
            {
                "timestamp": 123,  # Non-string timestamp
                "level": "ERROR",
                "message": "Invalid timestamp type",
                "metadata": {}
            }
        ]
        
        logs = get_logs(project_id='proj_1a2b3c', service='api')
        
        # Validate structure using LogEntry model
        self.validate_log_entries(logs)
        
        # Should return only the valid log
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['message'], 'Valid log')

    def test_get_logs_handles_naive_datetime_timestamps(self):
        """Test that naive datetime timestamps are handled correctly."""
        current_time = datetime.now(timezone.utc)
        naive_time = current_time.replace(tzinfo=None) - timedelta(seconds=30)
        
        DB['logs']['proj_1a2b3c']['api'] = [
            {
                "timestamp": naive_time.isoformat(),  # Naive datetime
                "level": "INFO",
                "message": "Log with naive timestamp",
                "metadata": {}
            }
        ]
        
        logs = get_logs(project_id='proj_1a2b3c', service='api')
        
        # Validate structure using LogEntry model
        self.validate_log_entries(logs)
        
        # Should handle naive timestamp by assuming UTC
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['message'], 'Log with naive timestamp')


if __name__ == '__main__':
    unittest.main()