from pydantic import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler # Assuming this is provided per prompt.
from .. import create_user
from ..SimulationEngine.db import DB


class TestCreateUser(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state before each test by clearing the mock DB's users."""
        DB["users"] = {} # Ensures tests are isolated regarding DB state

    def test_valid_input_creates_user(self):
        """Test createUser with valid userId and profile, checking DB state and return value."""
        user_id = "testuser1"
        profile_data = {"emailAddress": "test@example.com", "displayName": "Test User"}
        
        result = create_user(userId=user_id, profile=profile_data) # Use the alias

        self.assertIsInstance(result, dict)
        self.assertEqual(result["profile"]["emailAddress"], "test@example.com")
        self.assertIn(user_id, DB["users"])
        self.assertEqual(DB["users"][user_id]["profile"]["emailAddress"], "test@example.com")
        # Verify that extra fields from input profile are not in DB's profile structure
        self.assertNotIn("displayName", DB["users"][user_id]["profile"])

    def test_invalid_userid_type_raises_typeerror(self):
        """Test createUser with a non-string userId (e.g., int) raises TypeError."""
        profile_data = {"emailAddress": "test@example.com"}
        self.assert_error_behavior(
            func_to_call=create_user,
            expected_exception_type=TypeError,
            expected_message=r"userId must be a string, got int",
            userId=123, # Invalid type for userId
            profile=profile_data
        )

    def test_none_userid_raises_typeerror(self):
        """Test createUser with None as userId raises TypeError."""
        profile_data = {"emailAddress": "test@example.com"}
        self.assert_error_behavior(
            func_to_call=create_user,
            expected_exception_type=TypeError,
            expected_message=r"userId must be a string, got NoneType",
            userId=None, # userId is None
            profile=profile_data
        )

    def test_profile_missing_email_raises_validationerror(self):
        """Test createUser with profile missing the mandatory 'emailAddress' key raises ValidationError."""
        user_id = "testuser2"
        profile_data = {"displayName": "Another User"} # 'emailAddress' is missing
        
        # Pydantic v2 error message for a required field:
        self.assert_error_behavior(
            func_to_call=create_user,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for ProfileInputModel\nemailAddress\n  Field required [type=missing, input_value={'displayName': 'Another User'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
            userId=user_id,
            profile=profile_data
        )

    def test_profile_email_wrong_type_raises_validationerror(self):
        """Test createUser with 'emailAddress' of an incorrect type (e.g., int) raises ValidationError."""
        user_id = "testuser3"
        profile_data = {"emailAddress": 12345} # 'emailAddress' is an int, not string
        
        # Pydantic v2 error message for EmailStr when input is not a string:
        self.assert_error_behavior(
            func_to_call=create_user,
            expected_exception_type=ValidationError,
            expected_message='1 validation error for ProfileInputModel\nemailAddress\n  Input should be a valid string [type=string_type, input_value=12345, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type',
            userId=user_id,
            profile=profile_data
        )

    def test_profile_email_invalid_format_raises_validationerror(self):
        """Test createUser with 'emailAddress' as a string but not in a valid email format raises ValidationError."""
        user_id = "testuser4"
        profile_data = {"emailAddress": "not-a-valid-email"} # String, but invalid email format
        
        # Pydantic v2 error message for EmailStr when string is not a valid email:
        self.assert_error_behavior(
            func_to_call=create_user,
            expected_exception_type=ValidationError,
            expected_message="value is not a valid email address: An email address must have an @-sign.",
            userId=user_id,
            profile=profile_data
        )

    def test_profile_not_a_dict_raises_typeerror(self):
        """Test createUser if 'profile' is not a dictionary (e.g., a list) raises TypeError."""
        user_id = "testuser5"
        # The `**profile` in `ProfileInputModel(**profile)` causes this TypeError before Pydantic validation.
        self.assert_error_behavior(
            func_to_call=create_user,
            expected_exception_type=TypeError,
            expected_message="profile must be a dict", # Python's error for **non_mapping
            userId=user_id,
            profile=["this", "is", "a", "list"] # 'profile' is a list
        )

    def test_profile_is_none_raises_typeerror(self):
        """Test createUser if 'profile' is None raises TypeError."""
        user_id = "testuser6"
        # Similar to the list case, `**None` raises TypeError.
        self.assert_error_behavior(
            func_to_call=create_user,
            expected_exception_type=TypeError,
            expected_message="profile must be a dict",
            userId=user_id,
            profile=None # 'profile' is None
        )
        
    def test_profile_with_extra_fields_is_valid(self):
        """Test createUser with a profile including extra, unmodelled fields is accepted (extra fields are ignored)."""
        user_id = "testuser7"
        profile_data = {
            "emailAddress": "extra@example.com",
            "displayName": "Extra Fields User", # This field is not in ProfileInputModel
            "age": 30                           # This field is also not in ProfileInputModel
        }
        result = create_user(userId=user_id, profile=profile_data)
        self.assertEqual(result["profile"]["emailAddress"], "extra@example.com")
        self.assertIn(user_id, DB["users"])
        # Verify that Pydantic's default behavior (extra='ignore') means extra fields
        # are not part of the validated model and thus not used to populate DB["users"][user_id]["profile"]
        # beyond 'emailAddress'.
        self.assertNotIn("displayName", DB["users"][user_id]["profile"])
        self.assertNotIn("age", DB["users"][user_id]["profile"])
        self.assertEqual(DB["users"][user_id]["profile"]["messagesTotal"], 0) # Check a default value

    def test_userid_already_exists_overwrites_entry(self):
        """Test that calling createUser with an existing userId overwrites the previous user entry."""
        user_id = "existinguser"
        initial_profile_data = {"emailAddress": "initial@example.com"}
        create_user(userId=user_id, profile=initial_profile_data) # First call to create the user

        # Verify initial creation
        self.assertEqual(DB["users"][user_id]["profile"]["emailAddress"], "initial@example.com")

        new_profile_data = {"emailAddress": "updated@example.com"}
        result = create_user(userId=user_id, profile=new_profile_data) # Second call with same userId

        # Verify overwrite
        self.assertEqual(DB["users"][user_id]["profile"]["emailAddress"], "updated@example.com")
        self.assertEqual(result["profile"]["emailAddress"], "updated@example.com")
        
        # Ensure only one entry for this user_id exists, confirming overwrite behavior.
        self.assertEqual(len(DB["users"]), 1, "DB should contain only one user entry after overwrite.")

