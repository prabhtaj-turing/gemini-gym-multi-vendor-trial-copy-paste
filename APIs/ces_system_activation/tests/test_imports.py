import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
import importlib


class TestImports(BaseTestCaseWithErrorHandler):
    """
    Test suite for validating the ces_system_activation package imports and basic functionality.
    """

    def test_import_ces_package(self):
        """
        Test that the ces package can be imported successfully.
        """
        try:
            import APIs.ces_system_activation
        except ImportError:
            self.fail("Failed to import APIs.ces package")

    def test_import_public_functions(self):
        """
        Test that the public functions can be imported successfully.
        """
        try:
            from APIs.ces_system_activation import get_activation_visit_details
            from APIs.ces_system_activation import find_available_technician_appointment_slots
            from APIs.ces_system_activation import reschedule_technician_visit
            from APIs.ces_system_activation import schedule_new_technician_visit
            from APIs.ces_system_activation import flag_technician_visit_issue
            from APIs.ces_system_activation import trigger_service_activation
            from APIs.ces_system_activation import get_service_activation_status
            from APIs.ces_system_activation import send_customer_notification
            from APIs.ces_system_activation import search_order_details
            from APIs.ces_system_activation import search_activation_guides
            from APIs.ces_system_activation import escalate
            from APIs.ces_system_activation import fail
            from APIs.ces_system_activation import cancel

        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")

    def test_import_function_callable(self):
        """
        Test that the public functions are callable.
        """
        try:
            from APIs.ces_system_activation import (
                get_activation_visit_details,
                find_available_technician_appointment_slots,
                reschedule_technician_visit,
                schedule_new_technician_visit,
                flag_technician_visit_issue,
                trigger_service_activation,
                get_service_activation_status,
                send_customer_notification,
                search_order_details,
                search_activation_guides,
                escalate,
                fail,
                cancel
            )

            assert callable(get_activation_visit_details)
            assert callable(find_available_technician_appointment_slots)
            assert callable(reschedule_technician_visit)
            assert callable(schedule_new_technician_visit)
            assert callable(flag_technician_visit_issue)
            assert callable(trigger_service_activation)
            assert callable(get_service_activation_status)
            assert callable(send_customer_notification)
            assert callable(search_order_details)
            assert callable(search_activation_guides)
            assert callable(escalate)
            assert callable(fail)
            assert callable(cancel)

        except Exception as e:
            self.fail(f"Failed to verify function callability: {e}")

    def test_import_simulation_engine_modules(self):
        """
        Test that the simulation engine can be imported successfully.
        """
        try:
            importlib.import_module("APIs.ces_system_activation.SimulationEngine.models")
            importlib.import_module("APIs.ces_system_activation.SimulationEngine.db")
            importlib.import_module("APIs.ces_system_activation.SimulationEngine.custom_errors")
            importlib.import_module("APIs.ces_system_activation.SimulationEngine.utils")
        except Exception as e:
            self.fail(f"Failed to import simulation engine: {e}")

    def test_simulation_engine_module_usability(self):
        """
        Test that the simulation engine modules can be used successfully.
        """
        try:
            from APIs.ces_system_activation.SimulationEngine.models import (
                TechnicianVisitDetails,
                AppointmentAvailability,
                AvailableAppointmentSlot,
                FlaggedIssueConfirmation,
                ServiceActivationAttempt,
                NotificationResult,
                DataStoreQueryResult,
                SourceSnippet
            )
            from APIs.ces_system_activation.SimulationEngine.db import DB, save_state, load_state
            from APIs.ces_system_activation.SimulationEngine.utils import query_order_details_infobot, query_activation_guides_infobot

            assert type(DB) == dict
            # These are dataclasses, not BaseModel
            assert hasattr(TechnicianVisitDetails, '__pydantic_fields__')
            assert hasattr(AppointmentAvailability, '__pydantic_fields__')
            assert hasattr(AvailableAppointmentSlot, '__pydantic_fields__')
            assert hasattr(FlaggedIssueConfirmation, '__pydantic_fields__')
            assert hasattr(ServiceActivationAttempt, '__pydantic_fields__')
            assert hasattr(NotificationResult, '__pydantic_fields__')
            assert hasattr(DataStoreQueryResult, '__pydantic_fields__')
            assert hasattr(SourceSnippet, '__pydantic_fields__')

            assert callable(save_state)
            assert callable(load_state)
            assert callable(query_order_details_infobot)
            assert callable(query_activation_guides_infobot)

        except Exception as e:
            self.fail(f"Failed to use simulation engine modules: {e}")

    def test_function_map_integrity(self):
        """
        Test that the function map contains all expected functions.
        """
        from APIs.ces_system_activation import _function_map
        
        expected_functions = [
            "get_activation_visit_details",
            "find_available_technician_appointment_slots",
            "reschedule_technician_visit",
            "schedule_new_technician_visit",
            "flag_technician_visit_issue",
            "trigger_service_activation",
            "get_service_activation_status",
            "send_customer_notification",
            "search_order_details",
            "search_activation_guides",
            "escalate",
            "fail",
            "cancel"
        ]

        for func_name in expected_functions:
            self.assertIn(func_name, _function_map, f"Function {func_name} not found in function map")

if __name__ == '__main__':
    unittest.main()