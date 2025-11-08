import os
import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from common_utils.authentication_manager import AuthenticationManager, get_auth_manager
from authentication.authentication_service import (
    authenticate_service,
    deauthenticate_service,
    is_service_authenticated,
    list_authenticated_services,
    reset_all_authentication,
    create_authenticated_function,
)
from authentication.SimulationEngine.custom_errors import (
    ValidationError,
    AuthenticationError,
)


class TestAuthenticationService(BaseTestCaseWithErrorHandler):
    """Class-based tests for authentication service runtime functions."""

    def setUp(self):
        # Ensure auth enforcement is disabled for predictable tests
        self._prev_auth_env = os.environ.get("AUTH_ENFORCEMENT")
        os.environ["AUTH_ENFORCEMENT"] = "FALSE"
        # Reset manager to defaults between tests
        AuthenticationManager.rollback_config()
        # Start from a clean service config map in each test
        get_auth_manager().service_configs = {}

    def tearDown(self):
        # Restore env and reset manager
        if self._prev_auth_env is None:
            os.environ.pop("AUTH_ENFORCEMENT", None)
        else:
            os.environ["AUTH_ENFORCEMENT"] = self._prev_auth_env
        AuthenticationManager.rollback_config()

    # --- authenticate_service ---

    def test_authenticate_service_success(self):
        auth_manager = get_auth_manager()
        # Configure an existing service from DB
        auth_manager.service_configs["airline"] = {
            "authentication_enabled": True,
            "excluded_functions": [],
            "is_authenticated": False,
        }

        result = authenticate_service("airline")

        self.assertEqual(result["service"], "airline")
        self.assertTrue(result["authenticated"]) 
        self.assertIn("authenticated successfully", result["message"]) 
        self.assertTrue(auth_manager.is_service_authenticated("airline"))

    def test_authenticate_service_invalid_name_empty_string(self):
        """Test authenticate_service with empty string."""
        self.assert_error_behavior(
            authenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=""
        )

    def test_authenticate_service_invalid_name_type_none(self):
        """Test authenticate_service with None as service_name."""
        self.assert_error_behavior(
            authenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=None
        )

    def test_authenticate_service_invalid_name_type_int(self):
        """Test authenticate_service with integer as service_name."""
        self.assert_error_behavior(
            authenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=123
        )

    def test_authenticate_service_invalid_name_type_float(self):
        """Test authenticate_service with float as service_name."""
        self.assert_error_behavior(
            authenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=123.45
        )

    def test_authenticate_service_invalid_name_type_list(self):
        """Test authenticate_service with list as service_name."""
        self.assert_error_behavior(
            authenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=["service"]
        )

    def test_authenticate_service_invalid_name_type_dict(self):
        """Test authenticate_service with dict as service_name."""
        self.assert_error_behavior(
            authenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name={"name": "service"}
        )

    def test_authenticate_service_invalid_name_type_bool(self):
        """Test authenticate_service with boolean as service_name."""
        self.assert_error_behavior(
            authenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=True
        )

    def test_authenticate_service_whitespace_only_name(self):
        """Test authenticate_service with whitespace-only service_name."""
        # Whitespace-only strings pass validation but fail service lookup
        self.assert_error_behavior(
            authenticate_service,
            AuthenticationError,
            "Service '   ' not found",
            service_name="   "
        )

    # --- deauthenticate_service ---

    def test_deauthenticate_service_success(self):
        auth_manager = get_auth_manager()
        auth_manager.service_configs["airline"] = {
            "authentication_enabled": True,
            "excluded_functions": [],
            "is_authenticated": True,
        }

        result = deauthenticate_service("airline")

        self.assertEqual(result["service"], "airline")
        self.assertFalse(result["authenticated"]) 
        self.assertIn("deauthenticated successfully", result["message"]) 
        self.assertFalse(auth_manager.is_service_authenticated("airline"))

    def test_deauthenticate_service_invalid_name_empty_string(self):
        """Test deauthenticate_service with empty string."""
        self.assert_error_behavior(
            deauthenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=""
        )

    def test_deauthenticate_service_invalid_name_type_none(self):
        """Test deauthenticate_service with None as service_name."""
        self.assert_error_behavior(
            deauthenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=None
        )

    def test_deauthenticate_service_invalid_name_type_int(self):
        """Test deauthenticate_service with integer as service_name."""
        self.assert_error_behavior(
            deauthenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=456
        )

    def test_deauthenticate_service_invalid_name_type_float(self):
        """Test deauthenticate_service with float as service_name."""
        self.assert_error_behavior(
            deauthenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=78.9
        )

    def test_deauthenticate_service_invalid_name_type_list(self):
        """Test deauthenticate_service with list as service_name."""
        self.assert_error_behavior(
            deauthenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name=["gmail"]
        )

    def test_deauthenticate_service_invalid_name_type_dict(self):
        """Test deauthenticate_service with dict as service_name."""
        self.assert_error_behavior(
            deauthenticate_service,
            ValidationError,
            "Service name must be a non-empty string",
            service_name={"service": "gmail"}
        )

    def test_deauthenticate_service_whitespace_only_name(self):
        """Test deauthenticate_service with whitespace-only service_name."""
        # Whitespace-only strings pass validation and deauth succeeds gracefully
        result = deauthenticate_service("\t\n  ")
        self.assertIsInstance(result, dict)

    # --- is_service_authenticated ---

    def test_is_service_authenticated_service_not_in_db(self):
        self.assertFalse(is_service_authenticated("totally_unknown_service"))

    def test_is_service_authenticated_when_auth_disabled(self):
        auth_manager = get_auth_manager()
        # Existing service with auth disabled should always return True
        auth_manager.service_configs["airline"] = {
            "authentication_enabled": False,
            "excluded_functions": [],
            "is_authenticated": False,
        }
        self.assertTrue(is_service_authenticated("airline"))

    def test_is_service_authenticated_when_auth_enabled_and_not_authenticated(self):
        auth_manager = get_auth_manager()
        auth_manager.service_configs["airline"] = {
            "authentication_enabled": True,
            "excluded_functions": [],
            "is_authenticated": False,
        }
        self.assertFalse(is_service_authenticated("airline"))

    def test_is_service_authenticated_when_auth_enabled_and_authenticated(self):
        auth_manager = get_auth_manager()
        auth_manager.service_configs["airline"] = {
            "authentication_enabled": True,
            "excluded_functions": [],
            "is_authenticated": True,
        }
        self.assertTrue(is_service_authenticated("airline"))

    # --- list_authenticated_services ---

    def test_list_authenticated_services(self):
        auth_manager = get_auth_manager()
        auth_manager.service_configs.update(
            {
                "airline": {
                    "authentication_enabled": True,
                    "excluded_functions": [],
                    "is_authenticated": True,
                },
                "gmail": {
                    "authentication_enabled": True,
                    "excluded_functions": [],
                    "is_authenticated": True,
                },
                "slack": {
                    "authentication_enabled": True,
                    "excluded_functions": [],
                    "is_authenticated": False,
                },
            }
        )

        result = list_authenticated_services()
        services = set(result.get("authenticated_services", []))

        self.assertIn("airline", services)
        self.assertIn("gmail", services)
        self.assertNotIn("slack", services)
        self.assertEqual(result.get("count"), 2)

    # --- reset_all_authentication ---

    def test_reset_all_authentication(self):
        auth_manager = get_auth_manager()
        auth_manager.service_configs.update(
            {
                "airline": {
                    "authentication_enabled": True,
                    "excluded_functions": [],
                    "is_authenticated": True,
                },
                "gmail": {
                    "authentication_enabled": True,
                    "excluded_functions": [],
                    "is_authenticated": True,
                },
            }
        )

        result = reset_all_authentication()

        self.assertTrue(result.get("success"))
        self.assertIn("deauthenticated", result.get("message", ""))
        self.assertFalse(auth_manager.is_service_authenticated("airline"))
        self.assertFalse(auth_manager.is_service_authenticated("gmail"))

    # --- create_authenticated_function ---

    def test_create_authenticated_function_enforces_auth(self):
        auth_manager = get_auth_manager()
        auth_manager.service_configs["airline"] = {
            "authentication_enabled": True,
            "excluded_functions": [],
            "is_authenticated": False,
        }

        def sample_func(x: int, y: int) -> int:
            return x + y

        wrapped = create_authenticated_function(sample_func, "airline")

        self.assert_error_behavior(
            wrapped,
            AuthenticationError,
            "Service 'airline' is not authenticated. Please authenticate using authenticate_service('airline') before using this API.",
            1, 2
        )

        # Authenticate and call again
        authenticate_service("airline")
        self.assertEqual(wrapped(3, 4), 7)

        # Deauthenticate and ensure it fails again
        deauthenticate_service("airline")
        self.assert_error_behavior(
            wrapped,
            AuthenticationError,
            "Service 'airline' is not authenticated. Please authenticate using authenticate_service('airline') before using this API.",
            5, 6
        )

    def test_create_authenticated_function_invalid_func_none(self):
        """Test create_authenticated_function with None as func parameter."""
        # The function doesn't validate input types, so this will create a wrapper
        # but when called, it will fail during the authentication check or function call
        wrapped = create_authenticated_function(None, "airline") 
        # When called, it should fail (either during auth check or function call)
        self.assert_error_behavior(
            wrapped,
            TypeError,
            "'NoneType' object is not callable"
        )

    def test_create_authenticated_function_invalid_service_name_none(self):
        """Test create_authenticated_function with None as service_name."""
        def dummy_func():
            return "test"
            
        # This will likely fail during authentication check, not parameter validation
        wrapped = create_authenticated_function(dummy_func, None)
        
        # When called, should fail due to invalid service name  
        self.assert_error_behavior(
            wrapped,
            AuthenticationError,
            "Service 'None' is not authenticated. Please authenticate using authenticate_service('None') before using this API."
        )

    def test_create_authenticated_function_invalid_service_name_type_int(self):
        """Test create_authenticated_function with integer as service_name."""
        def dummy_func():
            return "test"
            
        # This will likely fail during authentication check
        wrapped = create_authenticated_function(dummy_func, 123)
        
        self.assert_error_behavior(
            wrapped,
            AuthenticationError,
            "Service '123' is not authenticated. Please authenticate using authenticate_service('123') before using this API."
        )

    def test_create_authenticated_function_invalid_service_name_type_list(self):
        """Test create_authenticated_function with list as service_name."""
        def dummy_func():
            return "test"
            
        wrapped = create_authenticated_function(dummy_func, ["airline"])
        
        self.assert_error_behavior(
            wrapped,
            TypeError,
            "unhashable type: 'list'"
        )

    # --- Additional Edge Cases and Special Scenarios ---
    def test_authenticate_service_nonexistent_service(self):
        """Test authenticate_service with non-existent service."""
        self.assert_error_behavior(
            authenticate_service,
            AuthenticationError,
            "Service 'nonexistent_service' not found",
            service_name="nonexistent_service"
        )

    def test_authenticate_service_authentication_failure(self):
        """Test authenticate_service when auth manager fails to set authentication."""
        from unittest.mock import patch, MagicMock
        
        # Mock auth manager to simulate authentication failure
        mock_auth_manager = MagicMock()
        mock_auth_manager.set_service_authenticated.return_value = False  # Simulate failure
        
        with patch('authentication.authentication_service.get_auth_manager', return_value=mock_auth_manager):
            self.assert_error_behavior(
                authenticate_service,
                AuthenticationError,
                "Failed to authenticate service 'airline'",
                service_name="airline"
            )

    def test_deauthenticate_service_save_failure_still_succeeds(self):
        """Test deauthenticate_service when save fails but still returns success."""
        from unittest.mock import patch, MagicMock
        
        # Mock auth manager to simulate save failure during deauthentication
        mock_auth_manager = MagicMock()
        mock_auth_manager.set_service_authenticated.return_value = False  # Simulate save failure
        
        with patch('authentication.authentication_service.get_auth_manager', return_value=mock_auth_manager):
            # Should still succeed even if save failed, as in-memory state is updated
            result = deauthenticate_service("airline")
            
            # Verify success despite save failure
            self.assertIsInstance(result, dict)
            self.assertEqual(result["service"], "airline")
            self.assertFalse(result["authenticated"])
            self.assertIn("deauthenticated successfully", result["message"])

    def test_deauthenticate_service_nonexistent_service(self):
        """Test deauthenticate_service with non-existent service."""
        # Should succeed even for non-existent services (graceful handling)
        result = deauthenticate_service("nonexistent_service")
        self.assertEqual(result["service"], "nonexistent_service")
        self.assertFalse(result["authenticated"])
        self.assertIn("deauthenticated successfully", result["message"])



if __name__ == "__main__":
    unittest.main()
