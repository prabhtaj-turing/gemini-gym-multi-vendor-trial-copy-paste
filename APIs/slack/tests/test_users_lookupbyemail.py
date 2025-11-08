from unittest.mock import patch

from ..SimulationEngine.custom_errors import InvalidEmailFormatError, UserNotFoundError, EmptyEmailError
from common_utils.custom_errors import InvalidEmailError
from .. import lookup_user_by_email
from common_utils.base_case import BaseTestCaseWithErrorHandler

DB = {}

class TestLookupUserByEmail(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state before each test, particularly the mock DB."""
        global DB  # We are modifying the global DB defined in the "Refactored Function" section
        self.original_db_users = DB.get("users", {}).copy()  # Store original users

        # Setup mock DB data for tests
        test_users_data = {
            "user123": {
                "id": "user123",
                "profile": {"email": "test.user@example.com", "name": "Test User One"}
            },
            "user456": {
                "id": "user456",
                "profile": {"email": "another.email@sub.example.org", "name": "Test User Two"}
            }
        }
        DB["users"] = test_users_data

    def tearDown(self):
        """Restore original DB state after each test."""
        global DB
        DB["users"] = self.original_db_users  # Restore original users

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_valid_email_user_found(self, mock_db):
        """Test with a valid email that exists in the mock DB."""
        email_to_find = "test.user@example.com"
        result = lookup_user_by_email(email=email_to_find)
        self.assertTrue(result.get("ok"))
        self.assertIn("user", result)
        self.assertEqual(result["user"]["profile"]["email"], email_to_find)
        self.assertEqual(result["user"]["id"], "user123")

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_valid_email_user_not_found(self, mock_db):
        """Test with a valid email that does not exist in the mock DB."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=UserNotFoundError,
            expected_message="User with email not found",
            email="nonexistent@example.com"
        )

    def test_invalid_email_type_integer(self):
        """Test that providing an integer for email raises TypeError."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=TypeError,
            expected_message="email must be a string.",
            email=12345
        )

    def test_invalid_email_type_none(self):
        """Test that providing None for email raises TypeError."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=TypeError,
            expected_message="email must be a string.",
            email=None
        )

    def test_empty_email_string(self):
        """Test that an empty email string raises ValueError."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=EmptyEmailError,
            expected_message="email cannot be empty.",
            email=""
        )

    def test_invalid_email_format_no_at_symbol(self):
        """Test email format validation: missing '@' symbol."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailFormatError,
            expected_message="Argument 'email' has an invalid format. It must contain a local part and a domain part separated by '@'.",
            email="testexample.com"
        )

    def test_invalid_email_format_empty_local_part(self):
        """Test email format validation: empty local part."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailFormatError,
            expected_message="Argument 'email' has an invalid format. It must contain a local part and a domain part separated by '@'.",
            email="@example.com"
        )

    def test_invalid_email_format_empty_domain_part(self):
        """Test email format validation: empty domain part."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailFormatError,
            expected_message="Argument 'email' has an invalid format. It must contain a local part and a domain part separated by '@'.",
            email="test@"
        )

    def test_invalid_email_format_no_dot_in_domain(self):
        """Test email format validation: missing '.' in domain part."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailFormatError,
            expected_message="Argument 'email' has an invalid format. The domain part must contain '.'.",
            email="test@examplecom"
        )

    def test_invalid_email_format_empty_tld(self):
        """Test email format validation: domain ends with a dot (empty TLD)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailFormatError,
            expected_message="Argument 'email' has an invalid format. The top-level domain cannot be empty.",
            email="test@example."
        )

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_valid_email_with_subdomain(self, mock_db):
        """Test a valid email with a subdomain successfully finds user."""
        email_to_find = "another.email@sub.example.org"
        result = lookup_user_by_email(email=email_to_find)
        self.assertTrue(result.get("ok"))
        self.assertIn("user", result)
        self.assertEqual(result["user"]["profile"]["email"], email_to_find)
        self.assertEqual(result["user"]["id"], "user456")

    def test_invalid_email_local_part_starts_with_dot(self):
        """Test email validation: local part starts with a dot (triggers InvalidEmailError from validate_email_util)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailError,
            expected_message="Invalid email value '.test@example.com' for field 'email'",
            email=".test@example.com"
        )

    def test_invalid_email_local_part_ends_with_dot(self):
        """Test email validation: local part ends with a dot (triggers InvalidEmailError from validate_email_util)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailError,
            expected_message="Invalid email value 'test.@example.com' for field 'email'",
            email="test.@example.com"
        )

    def test_invalid_email_local_part_consecutive_dots(self):
        """Test email validation: consecutive dots in local part (triggers InvalidEmailError from validate_email_util)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailError,
            expected_message="Invalid email value 'test..email@example.com' for field 'email'",
            email="test..email@example.com"
        )

    def test_invalid_email_domain_starts_with_hyphen(self):
        """Test email validation: domain starts with hyphen (triggers InvalidEmailError from validate_email_util)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailError,
            expected_message="Invalid email value 'test@-example.com' for field 'email'",
            email="test@-example.com"
        )

    def test_invalid_email_domain_ends_with_hyphen(self):
        """Test email validation: domain ends with hyphen (triggers InvalidEmailError from validate_email_util)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailError,
            expected_message="Invalid email value 'test@example.com-' for field 'email'",
            email="test@example.com-"
        )

    def test_invalid_email_domain_consecutive_dots(self):
        """Test email validation: consecutive dots in domain (triggers InvalidEmailError from validate_email_util)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailError,
            expected_message="Invalid email value 'test@example..com' for field 'email'",
            email="test@example..com"
        )

    def test_invalid_email_multiple_at_symbols(self):
        """Test email validation: multiple '@' symbols (caught by manual validation, raises InvalidEmailFormatError)."""
        self.assert_error_behavior(
            func_to_call=lookup_user_by_email,
            expected_exception_type=InvalidEmailFormatError,
            expected_message="Argument 'email' has an invalid format. It must contain a local part and a domain part separated by '@'.",
            email="test@email@example.com"
        )
