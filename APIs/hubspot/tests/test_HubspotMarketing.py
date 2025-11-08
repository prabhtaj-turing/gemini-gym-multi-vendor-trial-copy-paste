import os
from re import S
import unittest
import hubspot as HubspotMarketingAPI
from hubspot.SimulationEngine.db import DB, save_state, load_state
from hubspot.SimulationEngine.utils import (
    generate_hubspot_object_id,
)
import hashlib
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError
from hubspot.SimulationEngine.custom_errors import (
    InvalidSubscriptionIdTypeError,
    EmptySubscriptionIdError,
    SubscriptionNotFoundError,
    InvalidActiveParameterError,
    TemplateNotFoundError,
    InvalidTemplateIdTypeError,
    EmptyTemplateIdError,
    EmptyExternalEventIdError,
    EmptyAttendeeIdError,
    EmptyExternalAccountIdError,
    MarketingEventNotFoundError,
    EventAttendeesNotFoundError,
    AttendeeNotFoundError,
    InvalidExternalAccountIdError,
    TemplateNotValidError,
)


# ---------------------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------------------
class TestAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Clears the DB before each test."""
        DB.update(
            {
                "transactional_emails": {},
                "marketing_emails": {},
            }
        )

    def test_transactional_sendSingleEmail(self):
        # Test successful email sending
        result = HubspotMarketingAPI.TransactionalEmails.sendSingleEmail(
            message={
                "to": "test@example.com",
                "from": "sender@example.com",
                "subject": "Test",
                "htmlBody": "<p>Hello</p>",
            }
        )
        self.assertTrue(result["success"])
        self.assertIn(result["email_id"], DB["transactional_emails"])

        # Test missing required fields
        self.assert_error_behavior(
            HubspotMarketingAPI.TransactionalEmails.sendSingleEmail,
            expected_exception_type=ValueError,
            expected_message="Invalid message property: to",
            message={"from": "test@example.com"}
        )

        del DB["transactional_emails"]
        result = HubspotMarketingAPI.TransactionalEmails.sendSingleEmail(
            message={
                "to": "test@example.com",
                "from": "sender@example.com",
                "subject": "Test",
                "htmlBody": "<p>Hello</p>",
            }
        )
        self.assertTrue(result["success"])

    def test_transactional_sendSingleEmail_invalid_message(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.TransactionalEmails.sendSingleEmail,
            expected_exception_type=TypeError,
            expected_message="message must be a dictionary, but got int.",
            message=123
        )

    def test_marketing_create(self):
        result = HubspotMarketingAPI.MarketingEmails.create(name="Test Email")
        self.assertTrue(result["success"])
        self.assertTrue(result["email_id"])
        self.assertEqual(
            DB["marketing_emails"][result["email_id"]]["name"], "Test Email"
        )

    def test_marketing_create_invalid_name(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=ValueError,
            expected_message="Name must be a non-empty string.",
            name=1
        )

    def test_marketing_create_empty_name(self): 
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=ValueError,
            expected_message="Name must be a non-empty string.",
            name=""
        )

    def test_marketing_create_invalid_launch_date(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=ValueError,
            expected_message="Launch date must be in the format of YYYY-MM-DD.",
            launch_date="invalid_date",
            name="Test Email"
        )

    def test_marketing_create_invalid_sale_end_date(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=ValueError,
            expected_message="Sale end date must be in the format of YYYY-MM-DD.",
            sale_end_date="2 July 1006",
            name="Test Email"
        )

    def test_marketing_create_invalid_status(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="Status must be a string.",
            status=1,
            name="Test Email")

    def test_marketing_create_invalid_subject(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="Subject must be a string.",
            subject=99,
            name="Test Email")

    def test_marketing_create_invalid_htmlBody(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="HTML body must be a string.",
            htmlBody=99,
            name="Test Email")

    def test_marketing_create_invalid_discount_code(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="Discount code must be a string.",
            discount_code=99,
            name="Test Email")

    def test_marketing_create_invalid_isTransactional(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="isTransactional must be a boolean.",
            isTransactional="tru",
            name="Test Email")

    def test_marketing_create_all_fields(self):
        result = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email",
            subject="Test Subject",
            htmlBody="Test HTML Body",
            isTransactional=True,
            status="scheduled",
            discount_code="123456",
            expiration="2025-01-01",
            launch_date="2025-01-01",
            sale_end_date="2025-01-01",
            reward_points=100,
            access_code="123456")
        self.assertTrue(result["success"])
        self.assertEqual(DB["marketing_emails"][result["email_id"]]["name"], "Test Email")

    def test_marketing_create_invalid_expiration_date(self):
        """Test create with invalid expiration date format."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=ValueError,
            expected_message="Expiration must be in the format of YYYY-MM-DD.",
            name="Test Email",
            expiration="01/01/2025"
        )

    def test_marketing_create_invalid_expiration_type(self):
        """Test create with invalid expiration type."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="Expiration must be a string.",
            name="Test Email",
            expiration=2025
        )

    def test_marketing_create_invalid_reward_points_type(self):
        """Test create with invalid reward_points type."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="Reward points must be an integer.",
            name="Test Email",
            reward_points="100"
        )

    def test_marketing_create_invalid_access_code_type(self):
        """Test create with invalid access_code type."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.create,
            expected_exception_type=TypeError,
            expected_message="Access code must be a string.",
            name="Test Email",
            access_code=123456
        )

    def test_marketing_create_db_initialization(self):
        """Test create when marketing_emails key doesn't exist in DB."""
        # Remove marketing_emails from DB to test initialization
        if "marketing_emails" in DB:
            del DB["marketing_emails"]
        
        result = HubspotMarketingAPI.MarketingEmails.create(name="Test Email")
        self.assertTrue(result["success"])
        self.assertIn("marketing_emails", DB)
        self.assertIn(result["email_id"], DB["marketing_emails"])

    def test_marketing_create_with_only_required_fields(self):
        """Test create with only the required name field."""
        result = HubspotMarketingAPI.MarketingEmails.create(name="Minimal Email")
        self.assertTrue(result["success"])
        email_data = DB["marketing_emails"][result["email_id"]]
        self.assertEqual(email_data["name"], "Minimal Email")
        self.assertIsNone(email_data["subject"])
        self.assertIsNone(email_data["htmlBody"])
        self.assertFalse(email_data["isTransactional"])
        self.assertIsNone(email_data["status"])
        self.assertIsNone(email_data["discount_code"])
        self.assertIsNone(email_data["expiration"])
        self.assertIsNone(email_data["launch_date"])
        self.assertIsNone(email_data["sale_end_date"])
        self.assertIsNone(email_data["reward_points"])
        self.assertIsNone(email_data["access_code"])

    def test_marketing_create_with_boolean_false(self):
        """Test create with isTransactional set to False explicitly."""
        result = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email",
            isTransactional=False
        )
        self.assertTrue(result["success"])
        self.assertFalse(DB["marketing_emails"][result["email_id"]]["isTransactional"])

    def test_marketing_create_with_zero_reward_points(self):
        """Test create with reward_points set to 0."""
        result = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email",
            reward_points=0
        )
        self.assertTrue(result["success"])
        self.assertEqual(DB["marketing_emails"][result["email_id"]]["reward_points"], 0)

    def test_marketing_create_with_empty_strings(self):
        """Test create with empty string values for optional fields."""
        result = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email",
            subject="",
            htmlBody="",
            status="",
            discount_code="",
            access_code=""
        )
        self.assertTrue(result["success"])
        email_data = DB["marketing_emails"][result["email_id"]]
        self.assertEqual(email_data["subject"], "")
        self.assertEqual(email_data["htmlBody"], "")
        self.assertEqual(email_data["status"], "")
        self.assertEqual(email_data["discount_code"], "")
        self.assertEqual(email_data["access_code"], "")

    def test_marketing_create_with_valid_date_formats(self):
        """Test create with various valid date formats."""
        result = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email",
            expiration="2024-12-31",
            launch_date="2024-01-01",
            sale_end_date="2024-06-15"
        )
        self.assertTrue(result["success"])
        email_data = DB["marketing_emails"][result["email_id"]]
        self.assertEqual(email_data["expiration"], "2024-12-31")
        self.assertEqual(email_data["launch_date"], "2024-01-01")
        self.assertEqual(email_data["sale_end_date"], "2024-06-15")

    def test_marketing_create_return_structure(self):
        """Test that create returns the expected structure."""
        result = HubspotMarketingAPI.MarketingEmails.create(name="Test Email")
        self.assertIn("success", result)
        self.assertIn("message", result)
        self.assertIn("email_id", result)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Marketing email created successfully.")
        self.assertIsInstance(result["email_id"], str)
        self.assertTrue(len(result["email_id"]) > 0)

    def test_marketing_getById(self):
        result = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        email = HubspotMarketingAPI.MarketingEmails.getById(result["email_id"])
        self.assertEqual(email["name"], "Test Email")
        self.assertEqual(email["subject"], "Test Subject")

        # test non existant id
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.MarketingEmails.getById,
            expected_exception_type=TypeError,
            expected_message="email_id must be a string, but got int.",
            email_id=999,
        )

        # test invalid id type
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.MarketingEmails.getById,
            expected_exception_type=KeyError,
            expected_message="'Marketing email with id abc not found.'",
            email_id="abc",
        )

    def test_marketing_update(self):
        result = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = result["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.update(
            id, subject="Updated Subject"
        )
        self.assertTrue(result["success"])
        self.assertEqual(DB["marketing_emails"][id]["subject"], "Updated Subject")

    def test_marketing_update_invalid_input(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=ValueError,
            expected_message="Email ID is required.",
            email_id=None
        )

    def test_marketing_update_invalid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Email ID must be a string.",
            email_id=1
        )

    def test_marketing_update_invalid_launch_date(self):
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject", launch_date="2025-01-01"
        )
        id = email["email_id"]
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=ValueError,
            expected_message="Launch date must be in the format of YYYY-MM-DD.",
            email_id=id,
            launch_date="invalid_date"
        )

    def test_marketing_update_invalid_name(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Name must be a string.",
            email_id="1",
            name=1
        )

    def test_marketing_update_invalid_subject(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Subject must be a string.",
            email_id="1",
            subject=1
        )

    def test_marketing_update_invalid_htmlBody(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="HTML body must be a string.",
            email_id="1",
            htmlBody=1)

    def test_marketing_update_invalid_isTransactional(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="isTransactional must be a boolean.",
            email_id="1",
            isTransactional=1)

    def test_marketing_update_invalid_status(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Status must be a string.",
            email_id="1",
            status=1)

    def test_marketing_update_email_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=ValueError,
            expected_message="Marketing email with given ID not found.",
            email_id="1")

    def test_marketing_update_invalid_expiration_date(self):
        """Test update with invalid expiration date format."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = email["email_id"]
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=ValueError,
            expected_message="Expiration must be in the format of YYYY-MM-DD.",
            email_id=id,
            expiration="01/01/2025"
        )

    def test_marketing_update_invalid_expiration_type(self):
        """Test update with invalid expiration type."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = email["email_id"]
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Expiration must be a string.",
            email_id=id,
            expiration=2025
        )

    def test_marketing_update_invalid_sale_end_date(self):
        """Test update with invalid sale_end_date format."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = email["email_id"]
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=ValueError,
            expected_message="Sale end date must be in the format of YYYY-MM-DD.",
            email_id=id,
            sale_end_date="2 July 1006"
        )

    def test_marketing_update_invalid_sale_end_date_type(self):
        """Test update with invalid sale_end_date type."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = email["email_id"]
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Sale end date must be a string.",
            email_id=id,
            sale_end_date=2025
        )

    def test_marketing_update_invalid_reward_points_type(self):
        """Test update with invalid reward_points type."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = email["email_id"]
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Reward points must be an integer.",
            email_id=id,
            reward_points="100"
        )

    def test_marketing_update_invalid_access_code_type(self):
        """Test update with invalid access_code type."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = email["email_id"]
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=TypeError,
            expected_message="Access code must be a string.",
            email_id=id,
            access_code=123456
        )

    def test_marketing_update_multiple_fields(self):
        """Test update with multiple fields at once."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", subject="Test Subject"
        )
        id = email["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.update(
            id,
            name="Updated Name",
            subject="Updated Subject",
            htmlBody="Updated HTML Body",
            isTransactional=True,
            status="sent",
            discount_code="UPDATED123",
            expiration="2025-12-31",
            launch_date="2025-01-01",
            sale_end_date="2025-06-30",
            reward_points=500,
            access_code="VIP2025"
        )
        self.assertTrue(result["success"])
        email_data = DB["marketing_emails"][id]
        self.assertEqual(email_data["name"], "Updated Name")
        self.assertEqual(email_data["subject"], "Updated Subject")
        self.assertEqual(email_data["htmlBody"], "Updated HTML Body")
        self.assertTrue(email_data["isTransactional"])
        self.assertEqual(email_data["status"], "sent")
        self.assertEqual(email_data["discount_code"], "UPDATED123")
        self.assertEqual(email_data["expiration"], "2025-12-31")
        self.assertEqual(email_data["launch_date"], "2025-01-01")
        self.assertEqual(email_data["sale_end_date"], "2025-06-30")
        self.assertEqual(email_data["reward_points"], 500)
        self.assertEqual(email_data["access_code"], "VIP2025")

    def test_marketing_update_with_empty_strings(self):
        """Test update with empty string values."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email",
            subject="Original Subject",
            htmlBody="Original HTML",
            status="draft",
            discount_code="ORIGINAL123",
            access_code="ORIGINAL"
        )
        id = email["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.update(
            id,
            subject="",
            htmlBody="",
            status="",
            discount_code="",
            access_code=""
        )
        self.assertTrue(result["success"])
        email_data = DB["marketing_emails"][id]
        self.assertEqual(email_data["subject"], "")
        self.assertEqual(email_data["htmlBody"], "")
        self.assertEqual(email_data["status"], "")
        self.assertEqual(email_data["discount_code"], "")
        self.assertEqual(email_data["access_code"], "")

    def test_marketing_update_with_zero_reward_points(self):
        """Test update with reward_points set to 0."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", reward_points=100
        )
        id = email["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.update(id, reward_points=0)
        self.assertTrue(result["success"])
        self.assertEqual(DB["marketing_emails"][id]["reward_points"], 0)

    def test_marketing_update_with_boolean_false(self):
        """Test update with isTransactional set to False."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Email", isTransactional=True
        )
        id = email["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.update(id, isTransactional=False)
        self.assertTrue(result["success"])
        self.assertFalse(DB["marketing_emails"][id]["isTransactional"])

    def test_marketing_update_with_valid_date_formats(self):
        """Test update with various valid date formats."""
        email = HubspotMarketingAPI.MarketingEmails.create(name="Test Email")
        id = email["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.update(
            id,
            expiration="2024-12-31",
            launch_date="2024-01-01",
            sale_end_date="2024-06-15"
        )
        self.assertTrue(result["success"])
        email_data = DB["marketing_emails"][id]
        self.assertEqual(email_data["expiration"], "2024-12-31")
        self.assertEqual(email_data["launch_date"], "2024-01-01")
        self.assertEqual(email_data["sale_end_date"], "2024-06-15")

    def test_marketing_update_return_structure(self):
        """Test that update returns the expected structure."""
        email = HubspotMarketingAPI.MarketingEmails.create(name="Test Email")
        id = email["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.update(id, subject="Updated Subject")
        self.assertIn("success", result)
        self.assertIn("message", result)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Marketing email updated successfully.")

    def test_marketing_update_preserves_unmodified_fields(self):
        """Test that update preserves fields that are not being updated."""
        email = HubspotMarketingAPI.MarketingEmails.create(
            name="Original Name",
            subject="Original Subject",
            htmlBody="Original HTML",
            isTransactional=True,
            status="draft",
            discount_code="ORIGINAL123",
            expiration="2024-12-31",
            launch_date="2024-01-01",
            sale_end_date="2024-06-30",
            reward_points=100,
            access_code="ORIGINAL"
        )
        id = email["email_id"]
        
        # Update only the name
        result = HubspotMarketingAPI.MarketingEmails.update(id, name="Updated Name")
        self.assertTrue(result["success"])
        
        email_data = DB["marketing_emails"][id]
        self.assertEqual(email_data["name"], "Updated Name")
        # All other fields should remain unchanged
        self.assertEqual(email_data["subject"], "Original Subject")
        self.assertEqual(email_data["htmlBody"], "Original HTML")
        self.assertTrue(email_data["isTransactional"])
        self.assertEqual(email_data["status"], "draft")
        self.assertEqual(email_data["discount_code"], "ORIGINAL123")
        self.assertEqual(email_data["expiration"], "2024-12-31")
        self.assertEqual(email_data["launch_date"], "2024-01-01")
        self.assertEqual(email_data["sale_end_date"], "2024-06-30")
        self.assertEqual(email_data["reward_points"], 100)
        self.assertEqual(email_data["access_code"], "ORIGINAL")

    def test_marketing_update_db_missing_key(self):
        """Test update when marketing_emails key doesn't exist in DB."""
        # Remove marketing_emails from DB to test edge case
        if "marketing_emails" in DB:
            del DB["marketing_emails"]
        
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.update,
            expected_exception_type=ValueError,
            expected_message="Marketing email with given ID not found.",
            email_id="test_id"
        )

    def test_marketing_delete(self):
        result = HubspotMarketingAPI.MarketingEmails.create(name="Test Email")
        id = result["email_id"]
        result = HubspotMarketingAPI.MarketingEmails.delete(id)
        self.assertTrue(result["success"])
        self.assertNotIn(id, DB["marketing_emails"])

        
    def test_marketing_delete_invalid_id(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.delete,
            expected_exception_type=ValueError,
            expected_message="Marketing email with given email_id not found.",
            email_id="invalid_id"
        )

    def test_marketing_delete_none_id(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.delete,
            expected_exception_type=ValueError,
            expected_message="email_id is required",
            email_id=None
        )

    def test_marketing_delete_invalid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.delete,
            expected_exception_type=TypeError,
            expected_message="email_id must be a string",
            email_id=999
        )

    def test_marketing_clone(self):
        original = HubspotMarketingAPI.MarketingEmails.create(
            name="Original Email", subject="Original Subject"
        )
        result = HubspotMarketingAPI.MarketingEmails.clone(
            original["email_id"], name="Cloned Email"
        )
        result_id = result["email_id"]
        self.assertTrue(result["success"])
        self.assertEqual(DB["marketing_emails"][result_id]["name"], "Cloned Email")
        self.assertEqual(
            DB["marketing_emails"][result_id]["subject"], "Original Subject"
        )  # check subject remains

    def test_clone_invalid_id_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.clone,
            expected_exception_type=TypeError,
            expected_message="email_id must be a string",
            email_id=999,
            name="Cloned Email",
        )

    def test_clone_invalid_id_value(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.clone,
            expected_exception_type=ValueError,
            expected_message="Marketing email with given email_id not found.",
            email_id="999",
            name="Cloned Email",
        )

    def test_clone_invalid_name_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.clone,
            expected_exception_type=TypeError,
            expected_message="name must be a string",
            email_id="123",
            name=999,
        )

    def test_clone_invalid_name_value(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.clone,
            expected_exception_type=ValueError,
            expected_message="name is required",
            email_id="123",
            name=None,
        )

    def test_clone_invalid_id_none(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEmails.clone,
            expected_exception_type=ValueError,
            expected_message="email_id is required",
            email_id=None,
            name="Cloned Email",
        )

    def test_save_and_load_state(self):
        # Create some data
        result_1 = HubspotMarketingAPI.TransactionalEmails.sendSingleEmail(
            message={
                "to": "test@example.com",
                "from": "me@example.com",
                "subject": "test",
                "htmlBody": "body",
            }
        )
        result_2 = HubspotMarketingAPI.MarketingEmails.create(
            name="Test Marketing Email"
        )

        # Save the state
        save_state("test_state.json")

        # Clear the DB
        DB.update(
            {
                "transactional_emails": {},
                "marketing_emails": {},
            }
        )

        # Load the state
        load_state("test_state.json")

        # Check if data was restored correctly
        id = str(result_2["email_id"])
        self.assertIn(result_1["email_id"], DB["transactional_emails"])
        self.assertIn(id, DB["marketing_emails"])
        self.assertEqual(DB["marketing_emails"][id]["name"], "Test Marketing Email")

        # test load from invalid filepath
        load_state("invalid_file.json")  # File doesn't exist
        # Check that DB is still valid after FileNotFoundError
        self.assertIn("transactional_emails", DB)
        self.assertIn("marketing_emails", DB)

        # test save_state with invalid filepath
        with self.assertRaises(IOError) as context:
            save_state("/invalid/path/to/file.json")  # invalid path
        os.remove("test_state.json")


class TestSingleSendAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "transactional_emails": {},
                "email_templates": {},
                "contacts": {},
                "marketing_emails": {},
            }
        )  # Reset DB
        self.api = HubspotMarketingAPI.SingleSend
        # Pre-populate with a sample email template
        DB["email_templates"]["template_1"] = {
            "subject": "Welcome!",
            "body": "Hello, {name}!",
        }
        # Pre-populate with a sample contact
        DB["contacts"]["test@example.com"] = {
            "name": "Test User",
            "company": "Example Corp",
        }
        DB["contacts"]["test2@example.com"] = {"name": "Test User 2"}

    def test_sendSingleEmail_success(self):
        """Test successful email sending."""
        to = [{"email": "test@example.com"}]
        from_ = {"email": "sender@example.com", "name": "Sender"}
        message = {"to": to, "cc": None, "bcc": None, "from": from_, "replyTo": None}
        template = HubspotMarketingAPI.Templates.create_template(
            source="Trial Template"
        )
        template_id = template["id"]
        response = self.api.sendSingleEmail(
            template_id, message=message, customProperties={"city": "Boston"}
        )
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(DB["transactional_emails"]), 1)
        # Check for the transactional email ID in the response and DB
        txn_id = response["transactional_email_id"]
        self.assertIn(txn_id, DB["transactional_emails"])
        self.assertEqual(DB["transactional_emails"][txn_id]["template_id"], template_id)
        # Check that the message structure matches what's stored (with HubSpotEmailUser objects)
        stored_message = DB["transactional_emails"][txn_id]["message"]
        self.assertEqual(len(stored_message["to"]), 1)
        self.assertEqual(stored_message["to"][0].email, "test@example.com")
        self.assertEqual(stored_message["to"][0].name, None)
        self.assertEqual(stored_message["from"].email, "sender@example.com")
        self.assertEqual(stored_message["from"].name, "Sender")
        self.assertEqual(stored_message["cc"], None)
        self.assertEqual(stored_message["bcc"], None)
        self.assertEqual(stored_message["replyTo"], None)
        # Check if properties were merged correctly
        self.assertEqual(
            DB["transactional_emails"][txn_id]["properties"],
            {"name": "Test User", "company": "Example Corp", "city": "Boston"},
        )

    def test_sendSingleEmail_success_contact_properties(self):
        """Test successful email sending with contact and custom properties."""
        message = {
            "to": [{"email": "test@example.com"}],  # Contact exists
            "from": {"email": "sender@example.com", "name": "Sender"},
        }

        to = [{"email": "test@example.com"}]
        from_ = {"email": "sender@example.com", "name": "Sender"}
        # custom and contact props, contact props should take precedence
        template = HubspotMarketingAPI.Templates.create_template(
            source="Trial Template 1"
        )
        template_id = template["id"]
        response = self.api.sendSingleEmail(
            template_id,
            message=message,
            customProperties={"name": "Custom Name"},
            contactProperties={"name": "Contact Name"},
        )
        self.assertEqual(response["status"], "success")
        txn_id = response["transactional_email_id"]
        self.assertEqual(
            DB["transactional_emails"][txn_id]["properties"]["name"], "Contact Name"
        )  # contact name takes precedence

    def test_sendSingleEmail_success_multiple_recipients(self):
        """Test with multiple recipients, each having contact data."""
        message = {
            "to": [{"email": "test@example.com"}, {"email": "test2@example.com"}],
            "from": {"email": "sender@example.com"},
        }

        template = HubspotMarketingAPI.Templates.create_template(
            source="Trial Template 2"
        )
        template_id = template["id"]
        to = [{"email": "test@example.com"}, {"email": "test2@example.com"}]
        from_ = {"email": "sender@example.com", "name": "Sender"}
        response = self.api.sendSingleEmail(
            template_id, message=message, customProperties={"city": "Boston"}
        )
        self.assertEqual(response["status"], "success")
        self.assertEqual(
            len(DB["transactional_emails"]), 1
        )  # Still one send, but properties are correct
        txn_id = response["transactional_email_id"]
        # Verify properties (should be from the *first* contact if no recipient-specific handling)
        self.assertEqual(
            DB["transactional_emails"][txn_id]["properties"]["name"], "Test User 2"
        )
        self.assertEqual(
            DB["transactional_emails"][txn_id]["properties"]["city"], "Boston"
        )
        self.assertIn("company", DB["transactional_emails"][txn_id]["properties"])

    def test_sendSingleEmail_template_not_found(self):
        """Test sending email with a non-existent template ID."""
        message = {
            "to": [{"email": "test@example.com"}],
            "from": {"email": "sender@example.com"},
        }
        to = [{"email": "test@example.com"}]
        from_ = {"email": "sender@example.com", "name": "Sender"}
        
        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=TemplateNotFoundError,
            expected_message=f"Email template with ID invalid_template not found.",
            template_id="invalid_template",
            message=message,
        )

    def test_sendSingleEmail_invalid_input(self):
        """Test sending email with invalid input (missing 'to' field)."""
        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template 1"
        )
        template_id = template["id"]

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Field required',
            template_id=template_id,
            message={},
        )

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='String should have at least 1 character',
            template_id=template_id,
            message={"to": [{"email": ""}]},
        )

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message="Input should be a valid dictionary",
            template_id=template_id,
            message={"to": [{"email": "asd@asd.com"}], "from": "invalid"},
        )

    def test_sendSingleEmail_no_contact(self):
        """Test email sending when a contact doesn't exist in the DB."""
        message = {
            "to": [{"email": "nonexistent@example.com"}],  # This contact doesn't exist
            "from": {"email": "sender@example.com", "name": "Sender"},
        }
        to = [{"email": "nonexistent@example.com"}]
        from_ = {"email": "sender@example.com", "name": "Sender"}

        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template 2"
        )
        template_id = template["id"]
        response = self.api.sendSingleEmail(
            template_id, message=message, customProperties={"city": "Boston"}
        )
        self.assertEqual(response["status"], "success")
        txn_id = response["transactional_email_id"]
        # When there's no contact, custom properties should be used
        self.assertEqual(
            DB["transactional_emails"][txn_id]["properties"], {"city": "Boston"}
        )

    def test_sendSingleEmail_empty_contact_properties(self):
        """Test email sending when contact exist but has no properties"""
        DB["contacts"][
            "empty_contact@example.com"
        ] = {}  # add contact with no properties
        message = {
            "to": [{"email": "empty_contact@example.com"}],
            "from": {"email": "sender@example.com", "name": "Sender"},
        }

        to = [{"email": "empty_contact@example.com"}]
        from_ = {"email": "sender@example.com", "name": "Sender"}

        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template 3"
        )
        template_id = template["id"]
        response = self.api.sendSingleEmail(
            template_id, message=message, customProperties={"city": "Boston"}
        )
        self.assertEqual(response["status"], "success")
        txn_id = response["transactional_email_id"]
        # Only custom properties should be used
        self.assertEqual(
            DB["transactional_emails"][txn_id]["properties"], {"city": "Boston"}
        )

    def test_sendSingleEmail_contact_and_custom_properties_merge(self):
        """Test correct merging of contact and custom properties, contact properties overriding custom properties."""
        message = {
            "to": [{"email": "test@example.com"}],  # Contact exists for this email
            "from": {"email": "sender@example.com", "name": "Sender"},
        }

        to = [{"email": "test@example.com"}]
        from_ = {"email": "sender@example.com", "name": "Sender"}
        # Both customProperties and contactProperties are set, contact should take precedence
        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template 4"
        )
        template_id = template["id"]
        response = self.api.sendSingleEmail(
            template_id,
            message=message,
            customProperties={
                "city": "Boston",
                "name": "Should Not Appear",
            },  # Will be masked by contact prop
            contactProperties={"role": "Manager"},  # Additional contact prop
        )
        self.assertEqual(response["status"], "success")
        txn_id = response["transactional_email_id"]
        # Properties should be merged correctly, with contact props overriding custom props
        properties = DB["transactional_emails"][txn_id]["properties"]
        self.assertEqual(
            properties["name"], "Test User"
        )  # From contact, not custom prop
        self.assertEqual(properties["company"], "Example Corp")  # From contact
        self.assertEqual(properties["city"], "Boston")  # From custom prop
        self.assertEqual(properties["role"], "Manager")  # From contact prop override

    def test_sendSingleEmail_cc_bcc_replyTo(self):
        message = {
            "to": [{"email": "test@example.com"}],
            "from": {"email": "sender@example.com", "name": "Sender"},
            "cc": [{"email": "cc@example.com"}],
            "bcc": [{"email": "bcc@example.com"}],
            "replyTo": [{"email": "replyTo@example.com"}],
        }

        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template 5"
        )
        template_id = template["id"]
        response = self.api.sendSingleEmail(template_id, message=message)
        self.assertEqual(response["status"], "success")
        txn_id = response["transactional_email_id"]
        # Check CC, BCC, and replyTo with HubSpotEmailUser objects
        stored_message = DB["transactional_emails"][txn_id]["message"]
        self.assertEqual(len(stored_message["cc"]), 1)
        self.assertEqual(stored_message["cc"][0].email, "cc@example.com")
        self.assertEqual(stored_message["cc"][0].name, None)
        
        self.assertEqual(len(stored_message["bcc"]), 1)
        self.assertEqual(stored_message["bcc"][0].email, "bcc@example.com")
        self.assertEqual(stored_message["bcc"][0].name, None)
        
        self.assertEqual(len(stored_message["replyTo"]), 1)
        self.assertEqual(stored_message["replyTo"][0].email, "replyTo@example.com")
        self.assertEqual(stored_message["replyTo"][0].name, None)

        message["cc"] = [{"mailid": "cc2@example.com"}]

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Field required',
            template_id=template_id,
            message=message,
        )

        message["cc"] = [{"email": "cc2@example.com"}]
        message["bcc"] = [{"mailid": "bcc2@example.com"}]

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Field required',
            template_id=template_id,
            message=message,
        )

        message["bcc"] = [{"email": "bcc2@example.com"}]
        message["replyTo"] = [{"mailid": "replyTo2@example.com"}]

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Field required',
            template_id=template_id,
            message=message,
        )

        message["replyTo"] = [{"email": "replyTo2@example.com"}]
        del DB["templates"][template_id]
        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=TemplateNotFoundError,
            expected_message=f"Email template with ID {template_id} not found.",
            template_id=template_id,
            message=message,
        )

        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template 6", template_type=11
        )
        template_id = template["id"]
        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=TemplateNotValidError,
            expected_message=f"Template with ID {template_id} is not an email template.",
            template_id=template_id,
            message=message,
        )

    def test_sendSingleEmail_invalid_template_id(self):
        message = {
            "to": [{"email": "test@example.com"}],
            "from": {"email": "sender@example.com", "name": "Sender"},
        }
        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Input should be a valid string',
            template_id=123,
            message=message,
        )
        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Input should be a valid string',
            template_id=None,
            message=message,
        )

    def test_sendSingleEmail_invalid_message(self):
        template_id = "invalid_template"
        message = {
            "to": [{"email": "test@example.com"}],
            "from": {"email": "sender@example.com", "name": "Sender"},
        }
        self.assert_error_behavior( 
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Input should be a valid dictionary',
            template_id=template_id,
            message=None,
        )

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Input should be a valid dictionary',
            template_id=template_id,
            message=123,
        )

    def test_sendSingleEmail_invalid_custom_properties(self):
        # Create a valid template first
        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template for Custom Properties"
        )
        template_id = template["id"]
        
        message = {
            "to": [{"email": "test@example.com"}],
            "from": {"email": "sender@example.com", "name": "Sender"},
        }
        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Input should be a valid dictionary',
            template_id=template_id,
            message=message,
            customProperties=123,
        )

        # Original Pydantic model allows list values in customProperties - test success case
        result = self.api.sendSingleEmail(
            template_id=template_id,
            message=message,
            customProperties={
                'name': [123],
            },
        )
        self.assertEqual(result["status"], "success")


    def test_sendSingleEmail_invalid_contact_properties(self):
        # Create a valid template first
        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template for Contact Properties"
        )
        template_id = template["id"]
        
        message = {
            "to": [{"email": "test@example.com"}],
            "from": {"email": "sender@example.com", "name": "Sender"},
        }

        self.assert_error_behavior(
            func_to_call=self.api.sendSingleEmail,
            expected_exception_type=ValidationError,
            expected_message='Input should be a valid dictionary',
            template_id=template_id,
            message=message,
            contactProperties=123,
        )

        # Original Pydantic model allows list values in contactProperties - test success case
        result = self.api.sendSingleEmail(
            template_id=template_id,
            message=message,
            contactProperties={
                'name': [123],
            },
        )
        self.assertEqual(result["status"], "success")

    def test_sendSingleEmail_invalid_to(self):

        message = {
            "to": [{"email": "test@example.com"}],
            "from": {"email": "sender@example.com", "name": "Sender"},
            "cc": [{"email": "cc@example.com"}],
            "bcc": [{"email": "bcc@example.com"}],
            "replyTo": [{"email": "replyTo@example.com"}],
        }

        template = HubspotMarketingAPI.Templates.create_template(
            source="Test Template 5"
        )
        template_id = template["id"]

        message["to"] = []
        result = self.api.sendSingleEmail(
            template_id=template_id,
            message=message,
        )
        # Original Pydantic model allows empty 'to' lists - returns success
        self.assertEqual(result["status"], "success")

class TestCampaignsAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "campaigns": {
                    "a1b2c3d4-e5f6-4890-abcd-123456789abc": {
                        "id": "a1b2c3d4-e5f6-4890-abcd-123456789abc",
                        "name": "Campaign A",
                        "type": "EMAIL",
                        "createdAt": "2023-01-01T12:00:00Z",
                        "updatedAt": "2023-01-02T12:00:00Z",
                    },
                    "b2c3d4e5-f6a7-4901-bcde-234567890bcd": {
                        "id": "b2c3d4e5-f6a7-4901-bcde-234567890bcd",
                        "name": "Campaign B",
                        "type": "SOCIAL",
                        "createdAt": "2023-01-05T12:00:00Z",
                        "updatedAt": "2023-01-06T12:00:00Z",
                    },
                    "c3d4e5f6-a7b8-4012-cdef-345678901cde": {
                        "id": "c3d4e5f6-a7b8-4012-cdef-345678901cde",
                        "name": "Campaign C",
                        "type": "EMAIL",
                        "createdAt": "2023-01-10T12:00:00Z",
                        "updatedAt": "2023-01-11T12:00:00Z",
                    },
                }
            }
        )

    def test_get_campaigns_no_filters(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns()
        self.assertEqual(len(result["results"]), 3)
        self.assertEqual(result["total"], 3)
        self.assertIsNone(result["limit"])
        self.assertIsNone(result["offset"])

    def test_get_campaigns_limit(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(limit=1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["limit"], 1)
        self.assertIsNone(result["offset"])

    def test_get_campaigns_offset(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(offset=1)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["total"], 3)
        self.assertIsNone(result["limit"])
        self.assertEqual(result["offset"], 1)

    def test_get_campaigns_limit_and_offset(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(limit=1, offset=1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "b2c3d4e5-f6a7-4901-bcde-234567890bcd")
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["offset"], 1)

    def test_get_campaigns_id(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(id="a1b2c3d4-e5f6-4890-abcd-123456789abc")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "a1b2c3d4-e5f6-4890-abcd-123456789abc")

    def test_get_campaigns_name(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(name="Campaign B")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "b2c3d4e5-f6a7-4901-bcde-234567890bcd")

    def test_get_campaigns_type(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(type="EMAIL")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "a1b2c3d4-e5f6-4890-abcd-123456789abc")
        self.assertEqual(result["results"][1]["id"], "c3d4e5f6-a7b8-4012-cdef-345678901cde")

    def test_get_all_campaigns(self):
        """Test retrieving all campaigns without filters."""
        response = HubspotMarketingAPI.Campaigns.get_campaigns()
        self.assertEqual(response["total"], 3)
        self.assertEqual(len(response["results"]), 3)

    def test_get_campaigns_by_id(self):
        """Test retrieving campaign by id filter."""
        response = HubspotMarketingAPI.Campaigns.get_campaigns(id="b2c3d4e5-f6a7-4901-bcde-234567890bcd")
        self.assertEqual(response["total"], 1)
        self.assertEqual(response["results"][0]["name"], "Campaign B")

    def test_get_campaigns_by_name(self):
        """Test retrieving campaign by name filter."""
        response = HubspotMarketingAPI.Campaigns.get_campaigns(name="Campaign A")
        self.assertEqual(response["total"], 1)
        self.assertEqual(response["results"][0]["id"], "a1b2c3d4-e5f6-4890-abcd-123456789abc")

    def test_get_campaigns_by_type(self):
        """Test retrieving campaigns by type filter."""
        response = HubspotMarketingAPI.Campaigns.get_campaigns(type="EMAIL")
        self.assertEqual(response["total"], 2)
        campaign_names = [c["name"] for c in response["results"]]
        self.assertIn("Campaign A", campaign_names)
        self.assertIn("Campaign C", campaign_names)

    def test_get_campaigns_with_pagination(self):
        """Test pagination with limit and offset."""
        response = HubspotMarketingAPI.Campaigns.get_campaigns(limit=2)
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["limit"], 2)
        self.assertEqual(response["offset"], None)

        response = HubspotMarketingAPI.Campaigns.get_campaigns(offset=1)
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["offset"], 1)

        response = HubspotMarketingAPI.Campaigns.get_campaigns(limit=1, offset=1)
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["id"], "b2c3d4e5-f6a7-4901-bcde-234567890bcd")

    def test_get_campaigns_empty_result(self):
        """Test with filter resulting in empty list."""
        response = HubspotMarketingAPI.Campaigns.get_campaigns(
            name="Non Existent Campaign"
        )
        self.assertEqual(response["total"], 0)
        self.assertEqual(response["results"], [])

    def test_get_campaigns_no_filter(self):
        campaigns = HubspotMarketingAPI.Campaigns.get_campaigns()
        self.assertEqual(len(campaigns["results"]), 3)
        self.assertEqual(campaigns["total"], 3)
        self.assertIsNone(campaigns["limit"])
        self.assertIsNone(campaigns["offset"])

    def test_get_campaigns_with_limit(self):
        campaigns = HubspotMarketingAPI.Campaigns.get_campaigns(limit=2)
        self.assertEqual(len(campaigns["results"]), 2)
        self.assertEqual(campaigns["total"], 3)
        self.assertEqual(campaigns["limit"], 2)
        self.assertIsNone(campaigns["offset"])

    def test_get_campaigns_with_offset(self):
        campaigns = HubspotMarketingAPI.Campaigns.get_campaigns(offset=1)
        self.assertEqual(len(campaigns["results"]), 2)
        self.assertEqual(campaigns["total"], 3)
        self.assertIsNone(campaigns["limit"])
        self.assertEqual(campaigns["offset"], 1)

    def test_get_campaigns_with_limit_and_offset(self):
        campaigns = HubspotMarketingAPI.Campaigns.get_campaigns(limit=1, offset=1)
        self.assertEqual(len(campaigns["results"]), 1)
        self.assertEqual(campaigns["total"], 3)
        self.assertEqual(campaigns["limit"], 1)
        self.assertEqual(campaigns["offset"], 1)

    def test_get_campaigns_with_id_filter(self):
        campaigns = HubspotMarketingAPI.Campaigns.get_campaigns(id="b2c3d4e5-f6a7-4901-bcde-234567890bcd")
        self.assertEqual(len(campaigns["results"]), 1)
        self.assertEqual(campaigns["results"][0]["id"], "b2c3d4e5-f6a7-4901-bcde-234567890bcd")

    def test_get_campaigns_with_name_filter(self):
        campaigns = HubspotMarketingAPI.Campaigns.get_campaigns(name="Campaign A")
        self.assertEqual(len(campaigns["results"]), 1)
        self.assertEqual(campaigns["results"][0]["name"], "Campaign A")

    def test_get_campaigns_with_type_filter(self):
        campaigns = HubspotMarketingAPI.Campaigns.get_campaigns(type="EMAIL")
        self.assertEqual(len(campaigns["results"]), 2)
        self.assertTrue(all(c["type"] == "EMAIL" for c in campaigns["results"]))



    def test_get_campaign(self):
        campaign = HubspotMarketingAPI.Campaigns.get_campaign("a1b2c3d4-e5f6-4890-abcd-123456789abc")
        self.assertEqual(campaign["id"], "a1b2c3d4-e5f6-4890-abcd-123456789abc")
        self.assertEqual(campaign["name"], "Campaign A")

    def test_get_campaign_not_found(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaign,
            expected_exception_type=KeyError,
            expected_message="'Campaign with id 99999999-9999-9999-9999-999999999999 not found.'",
            campaign_id="99999999-9999-9999-9999-999999999999",
        )
    
    def test_get_campaign_invalid_id(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaign,
            expected_exception_type=TypeError,
            expected_message="campaign_id must be a string, but got int.",
            campaign_id=1,
        )

class TestArchiveCampaignAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "campaigns": {
                    "b1ba6c2d-8620-416a-aee7-a3347315311b": {
        "id": "b1ba6c2d-8620-416a-aee7-a3347315311b",
        "name": "Winter Holiday Sale",
        "slug": "winter-holiday-sale",
        "description": "Winter Holiday Sale",
        "start_year": 2024,
        "start_month": 5,
        "start_day": 24,
        "end_year": 2024,
        "end_month": 11,
        "end_day": 25,
        "theme": "Winter",
        "resource": "Winter Holiday Sale",
        "color_label": "Winter",
        "created_at": "2024-05-24T05:42:00"
      },
      "aedf35ed-8c02-4973-92b4-3c7c1ee83ddb": {
        "id": "aedf35ed-8c02-4973-92b4-3c7c1ee83ddb",
        "name": "Year-End Customer Appreciation",
        "slug": "year-end-customer-appreciation",
        "description": "Year-End Customer Appreciation",
        "start_year": 2024,
        "start_month": 3,
        "start_day": 23,
        "end_year": 2024,
        "end_month": 11,
        "end_day": 16,
        "theme": "Year-End",
        "resource": "Year-End Customer Appreciation",
        "color_label": "Year-End",
        "created_at": "2024-03-23T20:52:17"
            }
                }
            }
        )
    
    def test_archive_campaign(self):
        result = HubspotMarketingAPI.Campaigns.archive_campaign("b1ba6c2d-8620-416a-aee7-a3347315311b")
        self.assertTrue(result)
        self.assertTrue(DB["campaigns"]["b1ba6c2d-8620-416a-aee7-a3347315311b"]["is_archived"])

    def test_archive_campaign_invalid_id(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.archive_campaign,
            expected_exception_type=ValueError,
            expected_message="Campaign not found",
            campaign_id="b1ba6c2d-8620-416a-aee7-a3347315311c",
        )

    def test_get_campaigns_type__ne(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(type__ne="SOCIAL")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "b1ba6c2d-8620-416a-aee7-a3347315311b")
        self.assertEqual(result["results"][1]["id"], "aedf35ed-8c02-4973-92b4-3c7c1ee83ddb")   
    
    def test_get_campaigns_invalid_type(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="type must be a string, but got int.",
            type=1,
        )
    
    def test_get_campaigns_invalid_limit(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer, but got str.",
            limit="1",
        )
    def test_archive_campaign_invalid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.archive_campaign,
            expected_exception_type=TypeError,
            expected_message="Campaign ID must be a string",
            campaign_id=999,
        )

    def test_archive_campaign_invalid_uuid(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.archive_campaign,
            expected_exception_type=ValueError,
            expected_message="Campaign ID must be a valid UUID",
            campaign_id="b1ba6c2d",
        )

    def test_archive_campaign_no_campaign_id(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.archive_campaign,
            expected_exception_type=ValueError,
            expected_message="Campaign ID is required",
            campaign_id=None,
        )
    

    def test_get_campaigns_invalid_offset(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="offset must be an integer, but got str.",
            offset="1",
        )   
    
    def test_get_campaigns_invalid_created_at(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="created_at must be a string, but got int.",
            created_at=1,
        )
    
    def test_get_campaigns_invalid_created_at__gt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="created_at__gt must be a string, but got int.",
            created_at__gt=1,
        )
    
    def test_get_campaigns_invalid_created_at__gte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="created_at__gte must be a string, but got int.",
            created_at__gte=1,
        )
    
    def test_get_campaigns_invalid_created_at__lt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="created_at__lt must be a string, but got int.",
            created_at__lt=1,
        )
        
    def test_get_campaigns_invalid_created_at__lte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="created_at__lte must be a string, but got int.",
            created_at__lte=1,
        )
    
    def test_get_campaigns_invalid_updated_at(self):    
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="updated_at must be a string, but got int.",
            updated_at=1,
        )
    
    def test_get_campaigns_invalid_updated_at__gt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="updated_at__gt must be a string, but got int.",
            updated_at__gt=1,
        )
    
    def test_get_campaigns_invalid_updated_at__gte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="updated_at__gte must be a string, but got int.",
            updated_at__gte=1,
        )
    
    def test_get_campaigns_invalid_updated_at__lt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="updated_at__lt must be a string, but got int.",
            updated_at__lt=1,
        )
    
    def test_get_campaigns_invalid_updated_at__lte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="updated_at__lte must be a string, but got int.",
            updated_at__lte=1,
        )

    def test_get_campaigns_invalid_name(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="name must be a string, but got int.",
            name=1,
        )
    
    def test_get_campaigns_invalid_name__contains(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="name__contains must be a string, but got int.",
            name__contains=1,
        )
    
    def test_get_campaigns_invalid_name__icontains(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="name__icontains must be a string, but got int.",
            name__icontains=1,
        )   

    def test_get_campaigns_invalid_name__ne(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="name__ne must be a string, but got int.",
            name__ne=1,
        )
    
    def test_get_campaigns_invalid_id(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="id must be a string, but got int.",
            id=1,
        )
    
    def test_get_campaigns_invalid_id__ne(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="id__ne must be a string, but got int.",
            id__ne=1,
        )
    
    def test_get_campaigns_invalid_type__ne(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.get_campaigns,
            expected_exception_type=TypeError,
            expected_message="type__ne must be a string, but got int.",
            type__ne=1,
        )
    
    def test_get_campaigns_id_ne(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(id__ne="1")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "b1ba6c2d-8620-416a-aee7-a3347315311b")
        self.assertEqual(result["results"][1]["id"], "aedf35ed-8c02-4973-92b4-3c7c1ee83ddb")
    
    def test_get_campaigns_name_ne(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(name__ne="Campaign A")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "b1ba6c2d-8620-416a-aee7-a3347315311b")
        self.assertEqual(result["results"][1]["id"], "aedf35ed-8c02-4973-92b4-3c7c1ee83ddb")
    
    def test_get_campaigns_name_contains(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(name__contains="Winter")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "b1ba6c2d-8620-416a-aee7-a3347315311b")

    def test_get_campaigns_name_icontains(self):
        result = HubspotMarketingAPI.Campaigns.get_campaigns(name__icontains="winter")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "b1ba6c2d-8620-416a-aee7-a3347315311b")
    
class TestFormsAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "forms": {
                    "1": {
                        "id": "1",
                        "name": "Form A",
                        "submitText": "Submit A",
                        "fieldGroups": [],
                        "legalConsentOptions": {},
                        "createdAt": "2023-01-01T12:00:00Z",
                        "updatedAt": "2023-01-01T12:00:00Z",
                    },
                    "2": {
                        "id": "2",
                        "name": "Form B",
                        "submitText": "Submit B",
                        "fieldGroups": [],
                        "legalConsentOptions": {},
                        "createdAt": "2023-01-05T12:00:00Z",
                        "updatedAt": "2023-01-05T12:00:00Z",
                    },
                    "3": {
                        "id": "3",
                        "name": "Form C",
                        "submitText": "Submit C",
                        "fieldGroups": [],
                        "legalConsentOptions": {},
                        "createdAt": "2023-01-10T12:00:00Z",
                        "updatedAt": "2023-01-10T12:00:00Z",
                    },
                }
            }
        )

    def test_get_forms_no_filters(self):
        result = HubspotMarketingAPI.Forms.get_forms()
        self.assertEqual(len(result["results"]), 3)
        self.assertEqual(result["total"], 3)
        self.assertIsNone(result.get("paging"))

    def test_get_forms_limit(self):
        result = HubspotMarketingAPI.Forms.get_forms(limit=1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["total"], 3)
        self.assertIsNotNone(result.get("paging"))  # Should have paging info
        self.assertEqual(result["paging"]["next"]["after"], "1")

    def test_get_forms_after(self):
        result = HubspotMarketingAPI.Forms.get_forms(after="1")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["results"][0]["id"], "2")
        self.assertIsNone(result.get("paging"))

    def test_get_forms_after_and_limit(self):
        result = HubspotMarketingAPI.Forms.get_forms(after="1", limit=1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "2")
        self.assertEqual(result["total"], 3)
        self.assertIsNotNone(result.get("paging"))
        self.assertEqual(result["paging"]["next"]["after"], "2")

    def test_get_forms_after_not_found(self):
        # Test case where 'after' ID is not found
        result = HubspotMarketingAPI.Forms.get_forms(after="999")
        self.assertEqual(len(result["results"]), 0)
        self.assertEqual(result["total"], 3)  # Total should still be correct
        self.assertIsNone(result.get("paging"))

    def test_get_forms_created_at(self):
        result = HubspotMarketingAPI.Forms.get_forms(created_at="2023-01-05T12:00:00Z")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "2")

    def test_get_forms_created_at_gt(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            created_at__gt="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "3")

    def test_get_forms_created_at_gte(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            created_at__gte="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "2")
        self.assertEqual(result["results"][1]["id"], "3")

    def test_get_forms_created_at_lt(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            created_at__lt="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "1")

    def test_get_forms_created_at_lte(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            created_at__lte="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "1")
        self.assertEqual(result["results"][1]["id"], "2")

    def test_get_forms_updated_at(self):
        result = HubspotMarketingAPI.Forms.get_forms(updated_at="2023-01-05T12:00:00Z")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "2")

    def test_get_forms_updated_at_gt(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            updated_at__gt="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "3")

    def test_get_forms_updated_at_gte(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            updated_at__gte="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "2")
        self.assertEqual(result["results"][1]["id"], "3")

    def test_get_forms_updated_at_lt(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            updated_at__lt="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "1")

    def test_get_forms_updated_at_lte(self):
        result = HubspotMarketingAPI.Forms.get_forms(
            updated_at__lte="2023-01-05T12:00:00Z"
        )
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["id"], "1")
        self.assertEqual(result["results"][1]["id"], "2")

    def test_get_forms_name(self):
        result = HubspotMarketingAPI.Forms.get_forms(name="Form B")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "Form B")

    def test_get_forms_id(self):
        result = HubspotMarketingAPI.Forms.get_forms(id="2")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "2")
    
    def test_get_forms_invalid_after(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="after must be a string, but got int.",
            after=1,
        )
    
    def test_get_forms_invalid_limit(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer, but got str.",
            limit="1",
        )

    def test_get_forms_invalid_created_at(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="created_at must be a string, but got int.",
            created_at=1,
        )
    
    def test_get_forms_invalid_created_at__gt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="created_at__gt must be a string, but got int.",
            created_at__gt=1,
        )
    
    def test_get_forms_invalid_created_at__gte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="created_at__gte must be a string, but got int.",
            created_at__gte=1,
        )
    
    def test_get_forms_invalid_created_at__lt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="created_at__lt must be a string, but got int.",
            created_at__lt=1,
        )
    
    def test_get_forms_invalid_created_at__lte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="created_at__lte must be a string, but got int.",
            created_at__lte=1,
        )

    def test_get_forms_invalid_updated_at(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="updated_at must be a string, but got int.",
            updated_at=1,
        )

    def test_get_forms_invalid_updated_at__gt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="updated_at__gt must be a string, but got int.",
            updated_at__gt=1,
        )

    def test_get_forms_invalid_updated_at__gte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="updated_at__gte must be a string, but got int.",
            updated_at__gte=1,
        )

    def test_get_forms_invalid_updated_at__lt(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="updated_at__lt must be a string, but got int.",
            updated_at__lt=1,
        )
    
    def test_get_forms_invalid_updated_at__lte(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="updated_at__lte must be a string, but got int.",
            updated_at__lte=1,
        )

    def test_get_forms_invalid_name(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="name must be a string, but got int.",
            name=1,
        )
    
    def test_get_forms_invalid_id(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_forms,
            expected_exception_type=TypeError,
            expected_message="id must be a string, but got int.",
            id=1,
        )

    def test_get_form(self):
        form = HubspotMarketingAPI.Forms.get_form("1")
        self.assertEqual(form["id"], "1")
        self.assertEqual(form["name"], "Form A")

    def test_get_form_not_found(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_form,
            expected_exception_type=KeyError,
            expected_message="'Form with id 999 not found'",
            formId="999",
        )        
    
    def test_get_form_invalid_id(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Forms.get_form,
            expected_exception_type=TypeError,
            expected_message="formId must be a string, but got int.",
            formId=1,
        )


    def test_delete_form(self):
        HubspotMarketingAPI.Forms.delete_form("1")
        self.assertNotIn("1", DB["forms"])  # Check if removed from DB
        self.assertEqual(len(DB["forms"]), 2)

    def test_delete_form_invalid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.delete_form,
            expected_exception_type=TypeError,
            expected_message="formId must be a string",
            formId=999,
        )

    def test_delete_form_invalid_value(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.delete_form,
            expected_exception_type=ValueError,
            expected_message="formId is required",
            formId=None,
        )

    def test_delete_form_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.delete_form,
            expected_exception_type=ValueError,
            expected_message="Form with given ID not found.",
            formId="999",
        )


class TestUpdateFormAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "forms": {
                    "b1ba6c2d-8620-416a-aee7-a3347315311b": {
        "id": "b1ba6c2d-8620-416a-aee7-a3347315311b",
        "name": "Test Form",
        "submitText": "Submit Now",
        "fieldGroups": [
          {
            "groupType": "email",
            "richTextType": "text",
            "richText": "Test Rich Text",
            "fields": [
              {
                "fieldType": "email",
                "name": "email",
                "label": "Email",
                "required": True,
                "placeholder": "Enter your email",
                "defaultValue": "test@example.com",
                "options": ["Option 1", "Option 2"],
                "hidden": False
              }]
            }
        ],
        "legalConsentOptions": {
          "explicitConsentToProcess": {
            "communicationsCheckboxes": [
              {
                "subscriptionTypeId": 1,
                "label": "Email",
                "required": True
              }
            ],
            "communicationConsentText": "Test Communication Consent Text",
            "consentToProcessCheckboxLabel": "Test Consent To Process Checkbox Label",
            "consentToProcessFooterText": "Test Consent To Process Footer Text",
            "type": "explicit",
            "privacyText": "Test Privacy Text",
            "consentToProcessText": "Test Consent To Process Text"
          }
        },
        "createdAt": "2024-01-14T17:34:33",
        "updatedAt": "2024-06-24T05:19:38"
      }
                }
            }
        )

    def test_update_form_field_groups(self):
        updated_form = HubspotMarketingAPI.Forms.update_form(
            "b1ba6c2d-8620-416a-aee7-a3347315311b",
            fieldGroups=[
                {
                "groupType": "email",
                "richTextType": "text",
                "richText": "Test Rich Text",
                "fields": [{
                "fieldType": "email",
                "name": "email",
                "label": "Email",
                "required": True,
                "placeholder": "Enter your email",
                "defaultValue": "me@example.com",
                "options": ["Option 1", "Option 2"],
                "hidden": False
              }]}
            ]
        )
        self.assertEqual("me@example.com", DB["forms"]["b1ba6c2d-8620-416a-aee7-a3347315311b"]["fieldGroups"][0]["fields"][0]["defaultValue"])


    def test_update_form_name(self):
        updated_form = HubspotMarketingAPI.Forms.update_form(
            "b1ba6c2d-8620-416a-aee7-a3347315311b",
            name="Updated Form",
        )
        self.assertEqual("Updated Form", DB["forms"]["b1ba6c2d-8620-416a-aee7-a3347315311b"]["name"])

    def test_update_form_submit_text(self):
        updated_form = HubspotMarketingAPI.Forms.update_form(
            "b1ba6c2d-8620-416a-aee7-a3347315311b",
            submitText="Updated Submit Text",
        )
        self.assertEqual("Updated Submit Text", DB["forms"]["b1ba6c2d-8620-416a-aee7-a3347315311b"]["submitText"])

    def test_update_form_form_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.update_form,
            expected_exception_type=ValueError,
            expected_message="Form with given ID not found",
            formId="999",
            name="Updated Form",
        )

    def test_update_form_invalid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.update_form,
            expected_exception_type=TypeError,
            expected_message="name must be a string",
            formId="b1ba6c2d-8620-416a-aee7-a3347315311b",
            name=999,
        )

    def test_update_form_invalid_value(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.update_form,
            expected_exception_type=ValueError,
            expected_message="name cannot be empty or consist only of whitespace",
            formId="b1ba6c2d-8620-416a-aee7-a3347315311b",
            name="",
        )

    def test_update_form_invalid_formid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.update_form,
            expected_exception_type=TypeError,
            expected_message="formId must be a string",
            formId=999,
        )
        
    def test_update_form_invalid_field_groups_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.update_form,
            expected_exception_type=TypeError,
            expected_message="fieldGroups must be a list",
            formId="b1ba6c2d-8620-416a-aee7-a3347315311b",
            fieldGroups="invalid",
        )

    def test_update_form_invalid_field_groups_value(self):
        with self.assertRaises(ValidationError) as context:
            HubspotMarketingAPI.Forms.update_form(
                "b1ba6c2d-8620-416a-aee7-a3347315311b",
                fieldGroups=[{"groupType": "email", "richTextType": "text", "richText": "rich text", "fields": [{"name": "email", "label": "Email", "required": True, "placeholder": "Enter your email", "defaultValue": "me@example.com", "options": ["Option 1", "Option 2"], "hidden": False}]}]
            )

    def test_update_form_with_legal_consent_options(self):
        updated_form = HubspotMarketingAPI.Forms.update_form(
            "b1ba6c2d-8620-416a-aee7-a3347315311b",
            legalConsentOptions={
                "explicitConsentToProcess": {
            "communicationsCheckboxes": [
              {
                "subscriptionTypeId": 1,
                "label": "Email",
                "required": False
              }
            ],
            "communicationConsentText": "Test Communication Consent Text",
            "consentToProcessCheckboxLabel": "Test Consent To Process Checkbox Label",
            "consentToProcessFooterText": "Test Consent To Process Footer Text",
            "type": "explicit",
            "privacyText": "Test Privacy Text",
            "consentToProcessText": "Test Consent To Process Text"
          }
        
            },
        )
        self.assertEqual(False, DB["forms"]["b1ba6c2d-8620-416a-aee7-a3347315311b"]["legalConsentOptions"]["explicitConsentToProcess"]["communicationsCheckboxes"][0]["required"])
    
    def test_update_form_timestamp_format(self):
        """Test that the updatedAt timestamp is properly formatted as ISO 8601."""
        form_id = "b1ba6c2d-8620-416a-aee7-a3347315311b"
        
        # Update the form
        updated_form = HubspotMarketingAPI.Forms.update_form(
            form_id,
            name="Updated Form Name"
        )
        
        # Verify the timestamp format
        updated_at = updated_form["updatedAt"]
        self.assertTrue(
            updated_at.endswith("+00:00"),
            f"Timestamp should end with +00:00, got: {updated_at}"
        )
        self.assertFalse(
            updated_at.endswith("+00:00Z"),
            f"Timestamp should not have double Z suffix, got: {updated_at}"
        )
        
        # Verify it's a valid ISO 8601 format by checking it can be parsed
        from datetime import datetime
        try:
            # Try to parse the timestamp
            parsed_time = datetime.fromisoformat(updated_at)
            self.assertIsInstance(parsed_time, datetime)
        except ValueError as e:
            self.fail(f"Timestamp is not valid ISO 8601 format: {updated_at}, error: {e}")
    
    def test_update_form_legitimate_interest_preservation(self):
        """Test that legitimateInterest is preserved when updating other legal consent options."""
        form_id = "b1ba6c2d-8620-416a-aee7-a3347315311b"
        
        # Set up form with legitimateInterest
        DB["forms"][form_id]["legalConsentOptions"] = {
            "legitimateInterest": {
                "lawfulBasis": "Processing is necessary for the purposes of legitimate interests",
                "type": "legitimate_interest",
                "privacyText": "We process your data based on legitimate interests"
            },
            "explicitConsentToProcess": {
                "communicationsCheckboxes": [
                    {
                        "subscriptionTypeId": 1,
                        "label": "Email Marketing",
                        "required": True
                    }
                ],
                "communicationConsentText": "Original explicit consent text",
                "consentToProcessCheckboxLabel": "Original explicit label",
                "consentToProcessFooterText": "Original explicit footer",
                "type": "explicit",
                "privacyText": "Original explicit privacy text",
                "consentToProcessText": "Original explicit consent text"
            }
        }
        
        # Update only explicitConsentToProcess
        updated_form = HubspotMarketingAPI.Forms.update_form(
            form_id,
            legalConsentOptions={
                "explicitConsentToProcess": {
                    "communicationsCheckboxes": [
                        {
                            "subscriptionTypeId": 1,
                            "label": "Email Marketing",
                            "required": True
                        }
                    ],
                    "communicationConsentText": "Updated explicit consent text",  # Only this field is actually changed
                    "consentToProcessCheckboxLabel": "Original explicit label",  # Preserved from existing
                    "consentToProcessFooterText": "Original explicit footer",  # Preserved from existing
                    "type": "explicit",  # Preserved from existing
                    "privacyText": "Original explicit privacy text",  # Preserved from existing
                    "consentToProcessText": "Original explicit consent text"  # Preserved from existing
                }
            }
        )
        
        # Verify that legitimateInterest was preserved
        self.assertNotIn("legitimateInterest", updated_form["legalConsentOptions"])
        
        # Verify that explicitConsentToProcess was updated
        explicit_consent = updated_form["legalConsentOptions"]["explicitConsentToProcess"]
        self.assertEqual("Updated explicit consent text", explicit_consent["communicationConsentText"])


class TestFormGlobalEventsAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "subscription_definitions": [
                    {
                        "id": 1,
                        "name": "form.submission",
                        "description": "Form submission event",
                    }
                ],
                "subscriptions": {
                    "test-subscription-1": {
                        "id": "test-subscription-1",
                        "endpoint": "https://example.com/webhook1",
                        "subscriptionDetails": {},
                        "active": True,
                    },
                    "test-subscription-2": {
                        "id": "test-subscription-2",
                        "endpoint": "https://example.com/webhook2",
                        "subscriptionDetails": {},
                        "active": False,
                    },
                },
            }
        )

    def test_get_subscription_definitions(self):
        definitions = (
            HubspotMarketingAPI.FormGlobalEvents.get_subscription_definitions()
        )
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["name"], "form.submission")

    def test_create_subscription(self):
        new_subscription = HubspotMarketingAPI.FormGlobalEvents.create_subscription(
            endpoint="https://example.com/new",
            subscriptionDetails={"subscriptionType": "form.submission"},
        )
        id = new_subscription["id"]
        self.assertIn("id", new_subscription)
        self.assertEqual(new_subscription["endpoint"], "https://example.com/new")
        self.assertTrue(new_subscription["active"])
        self.assertEqual(len(DB["subscriptions"]), 3)  # Check if added
        self.assertEqual(DB["subscriptions"][id]["endpoint"], "https://example.com/new")

    def test_get_subscriptions(self):
        subscriptions = HubspotMarketingAPI.FormGlobalEvents.get_subscriptions()
        self.assertEqual(len(subscriptions), 2)
        self.assertEqual(subscriptions[0]["endpoint"], "https://example.com/webhook1")
        self.assertEqual(subscriptions[1]["endpoint"], "https://example.com/webhook2")

    def test_update_subscription(self):
        updated_subscription = HubspotMarketingAPI.FormGlobalEvents.update_subscription(
            "test-subscription-1", False
        )
        self.assertFalse(updated_subscription["active"])
        self.assertFalse(DB["subscriptions"]["test-subscription-1"]["active"])  # Check DB

        updated_subscription = HubspotMarketingAPI.FormGlobalEvents.update_subscription(
            "test-subscription-1", True
        )
        self.assertTrue(updated_subscription["active"])
        self.assertTrue(DB["subscriptions"]["test-subscription-1"]["active"])

    def test_update_subscription_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.update_subscription,
            expected_exception_type=SubscriptionNotFoundError,
            expected_message="Subscription with id 'non-existent-subscription' not found",
            subscriptionId="non-existent-subscription",
            active=True
        )

    def test_update_subscription_invalid_subscription_id_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.update_subscription,
            expected_exception_type=InvalidSubscriptionIdTypeError,
            expected_message="subscriptionId must be a string, got int",
            subscriptionId=123,
            active=True
        )

    def test_update_subscription_empty_string(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.update_subscription,
            expected_exception_type=EmptySubscriptionIdError,
            expected_message="subscriptionId cannot be empty or contain only whitespace",
            subscriptionId="",
            active=True
        )

    def test_update_subscription_whitespace_only(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.update_subscription,
            expected_exception_type=EmptySubscriptionIdError,
            expected_message="subscriptionId cannot be empty or contain only whitespace",
            subscriptionId="   ",
            active=True
        )

    def test_update_subscription_invalid_active_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.update_subscription,
            expected_exception_type=InvalidActiveParameterError,
            expected_message="active must be a boolean, got str",
            subscriptionId="test-subscription-1",
            active="true"
        )

    def test_update_subscription_none_subscription_id(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.update_subscription,
            expected_exception_type=InvalidSubscriptionIdTypeError,
            expected_message="subscriptionId must be a string, got NoneType",
            subscriptionId=None,
            active=True
        )

    def test_update_subscription_none_active(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.update_subscription,
            expected_exception_type=InvalidActiveParameterError,
            expected_message="active must be a boolean, got NoneType",
            subscriptionId="test-subscription-1",
            active=None
        )
    def test_delete_subscription(self):
        HubspotMarketingAPI.FormGlobalEvents.delete_subscription("test-subscription-1")
        self.assertEqual(len(DB["subscriptions"]), 1)
        self.assertNotIn("test-subscription-1", DB["subscriptions"])

    def test_delete_subscription_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.delete_subscription,
            expected_exception_type=SubscriptionNotFoundError,
            expected_message="Subscription with id 'non-existent-id' not found",
            subscriptionId="non-existent-id"
        )

    def test_delete_subscription_invalid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.delete_subscription,
            expected_exception_type=InvalidSubscriptionIdTypeError,
            expected_message="subscriptionId must be a string, got int",
            subscriptionId=123
        )

    def test_delete_subscription_empty_string(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.delete_subscription,
            expected_exception_type=EmptySubscriptionIdError,
            expected_message="subscriptionId cannot be empty or contain only whitespace",
            subscriptionId=""
        )

    def test_delete_subscription_whitespace_only(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.delete_subscription,
            expected_exception_type=EmptySubscriptionIdError,
            expected_message="subscriptionId cannot be empty or contain only whitespace",
            subscriptionId="   "
        )

    def test_delete_subscription_none_value(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.FormGlobalEvents.delete_subscription,
            expected_exception_type=InvalidSubscriptionIdTypeError,
            expected_message="subscriptionId must be a string, got NoneType",
            subscriptionId=None
        )


class TestMarketingEvents(BaseTestCaseWithErrorHandler):
    """Tests for the MarketingEvents class."""

    def setUp(self):
        """Set up the test environment."""
        DB.update(
            {
                "marketing_events": {},
                "attendees": {},
                "transactional_emails": {},
                "templates": {},
                "contacts": {},
                "marketing_emails": {},
                "campaigns": {},
                "forms": {},
                "subscription_definitions": [],
                "subscriptions": {},
            }
        )
        self.event_id = "event123"
        self.account_id = "account456"
        self.attendee_email = "test@example.com"
        self.attendee_id = hashlib.sha256(
            f"{self.event_id}-{self.attendee_email}".encode()
        ).hexdigest()[:8]

    def test_get_events(self):
        """Test getting all marketing events."""
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        events = HubspotMarketingAPI.MarketingEvents.get_events()
        self.assertEqual(len(events["results"]), 1)
        self.assertEqual(events["results"][0]["eventName"], "Test Event")

    def test_create_event(self):
        """Test creating a marketing event."""
        event = HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        self.assertEqual(event["eventName"], "Test Event")
        self.assertEqual(event["externalEventId"], self.event_id)
        self.assertEqual(event["externalAccountId"], self.account_id)
        self.assertIn(self.event_id, DB["marketing_events"])

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.create_event,
            EmptyExternalEventIdError,
            "External Event ID is required and must be a non-empty string.",
            externalEventId=None,
            externalAccountId=self.account_id,
            event_name="Test Event",
            event_type="Webinar",
            event_organizer="Organizer",
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.create_event,
            EmptyExternalAccountIdError,
            "External Account ID is required and must be a non-empty string.",
            externalEventId=self.event_id,
            externalAccountId=None,
            event_name="Test Event",
            event_type="Webinar",
            event_organizer="Organizer",
        )

    def test_get_event(self):
        """Test getting a marketing event."""
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        event = HubspotMarketingAPI.MarketingEvents.get_event(
            self.event_id, self.account_id
        )
        self.assertEqual(event["eventName"], "Test Event")

    def test_get_event_invalid_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=TypeError,
            expected_message="External Event ID must be a string.",
            externalEventId=123,
            externalAccountId=self.account_id
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=TypeError,
            expected_message="External Account ID must be a string.",
            externalEventId=self.event_id,
            externalAccountId=123,
        )

    def test_get_event_none_params(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID is required.",
            externalEventId=None,
            externalAccountId=self.account_id
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID is required.",
            externalEventId=self.event_id,
            externalAccountId=None,
        )

    def test_get_event_empty_string(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID cannot be empty.",
            externalEventId="",
            externalAccountId=self.account_id
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId="",
        )

    def test_get_event_invalid_value(self):
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=ValueError,
            expected_message="Event not found in DB.",
            externalEventId="nonexistent",
            externalAccountId=self.account_id
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_event,
            expected_exception_type=ValueError,
            expected_message="Event does not belong to the account.",
            externalEventId=self.event_id,
            externalAccountId="nonexistent"
        )

    def test_delete_event(self):
        """Test deleting a marketing event."""
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        HubspotMarketingAPI.MarketingEvents.delete_event(self.event_id, self.account_id)
        self.assertNotIn(self.event_id, DB["marketing_events"])

    def test_delete_event_invalid_event_id_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=TypeError,
            expected_message="External Event ID must be a string.",
            externalEventId=123,
            externalAccountId=self.account_id
        )

    def test_delete_event_invalid_account_id_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=TypeError,
            expected_message="External Account ID must be a string.",
            externalEventId=self.event_id,
            externalAccountId=123
        )

    def test_delete_event_invalid_event_id_empty(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID cannot be empty.",
            externalEventId="",
            externalAccountId=self.account_id
        )

    def test_delete_event_invalid_account_id_empty(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=""
        )

    def test_delete_event_invalid_event_id_none(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID is required.",
            externalEventId=None,
            externalAccountId=self.account_id
        )

    def test_delete_event_invalid_account_id_none(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID is required.",
            externalEventId=self.event_id,
            externalAccountId=None
        )

    def test_delete_event_event_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=ValueError,
            expected_message="Event not found in DB.",
            externalEventId="nonexistent",
            externalAccountId=self.account_id
        )

    def test_delete_event_event_not_found_in_account(self):
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_event,
            expected_exception_type=ValueError,
            expected_message="Event does not belong to the account.",
            externalEventId=self.event_id,
            externalAccountId="nonexistent"
        )


    def test_cancel_event(self):
        """Test canceling a marketing event."""
        DB.update({"marketing_events": {self.event_id: {
        "registrants": 100,
        "attendees": 50,
        "eventOrganizer": "Acme Corp",
        "eventUrl": "https://example.com/events/2",
        "eventType": "Trade Show",
        "noShows": 10,
        "cancellations": 5,
        "eventDescription": "Join us for Mobile World Congress to learn about Trade Show topics.",
        "eventName": "CES 2024",
        "eventCancelled": False,
        "customProperties": {
          "sourceId": "123-456-7890",
          "selectedByUser": True,
          "sourceLabel": "Trade Show",
          "source": "Trade Show",
          "updatedByUserId": 123,
          "persistenceTimestamp": 1714857600,
          "sourceMetadata": "Y29udHJvbHM6W10=",
          "dataSensitivity": "public",
          "unit": "number",
          "requestId": "123-456-7890",
          "isEncrypted": False,
          "name": "location",
          "useTimestampAsPersistenceTimestamp": True,
          "value": "Online",
          "selectedByUserTimestamp": 1714857600,
          "timestamp": 1714857600,
          "isLargeValue": False
        },
        "endDateTime": "2024-04-09T11:48:26",
        "startDateTime": "2024-02-03T20:21:10",
        "externalAccountId": self.account_id,
        "externalEventId": self.event_id,
        "id": self.event_id,
        "objectId": self.event_id,
        "createdAt": "2024-01-14T17:34:33",
        "updatedAt": "2024-06-24T05:19:38"
      }}})
        canceled_event = HubspotMarketingAPI.MarketingEvents.cancel_event(
            self.event_id, self.account_id
        )
        self.assertIsInstance(canceled_event, dict)
        self.assertIn("eventCancelled", canceled_event)
        self.assertIn("registrants", canceled_event)
        self.assertIn("attendees", canceled_event)
        self.assertIn("eventOrganizer", canceled_event)
        self.assertIn("eventUrl", canceled_event)
        self.assertIn("eventType", canceled_event)
        self.assertIn("noShows", canceled_event)
        self.assertIn("cancellations", canceled_event)
        self.assertEqual(canceled_event["eventCancelled"], True)

    def test_cancel_event_invalid_event_id_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for CancelMarketingEventRequest",
            externalEventId=123,
            externalAccountId=self.account_id
        )

    def test_cancel_event_invalid_account_id_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for CancelMarketingEventRequest",
            externalEventId=self.event_id,
            externalAccountId=123
        )
    
    def test_cancel_event_invalid_event_id_empty(self): 
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for CancelMarketingEventRequest",
            externalEventId="",
            externalAccountId=self.account_id
        )
    
    def test_cancel_event_invalid_account_id_empty(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for CancelMarketingEventRequest",
            externalEventId=self.event_id,
            externalAccountId=""
        )

    def test_cancel_event_invalid_event_id_none(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for CancelMarketingEventRequest",
            externalEventId=None,
            externalAccountId=self.account_id
        )

    def test_cancel_event_invalid_account_id_none(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for CancelMarketingEventRequest",
            externalEventId=self.event_id,
            externalAccountId=None
        )

    def test_cancel_event_event_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValueError,
            expected_message="Event not found in DB.",
            externalEventId="nonexistent",
            externalAccountId=self.account_id
        )

    def test_cancel_event_event_not_found_in_account(self):
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValueError,
            expected_message="Event does not belong to the account.",
            externalEventId=self.event_id,
            externalAccountId="nonexistent"
        )

    def test_cancel_event_event_already_canceled(self):
        DB.update({"marketing_events": {self.event_id: {
        "registrants": 100,
        "attendees": 50,
        "eventOrganizer": "Acme Corp",
        "eventUrl": "https://example.com/events/2",
        "eventType": "Trade Show",
        "noShows": 10,
        "cancellations": 5,
        "eventDescription": "Join us for Mobile World Congress to learn about Trade Show topics.",
        "eventName": "CES 2024",
        "eventCancelled": True,
        "customProperties": {
          "sourceId": "123-456-7890",
          "selectedByUser": True,
          "sourceLabel": "Trade Show",
          "source": "Trade Show",
          "updatedByUserId": 123,
          "persistenceTimestamp": 1714857600,
          "sourceMetadata": "Y29udHJvbHM6W10=",
          "dataSensitivity": "public",
          "unit": "number",
          "requestId": "123-456-7890",
          "isEncrypted": False,
          "name": "location",
          "useTimestampAsPersistenceTimestamp": True,
          "value": "Online",
          "selectedByUserTimestamp": 1714857600,
          "timestamp": 1714857600,
          "isLargeValue": False
        },
        "endDateTime": "2024-04-09T11:48:26",
        "startDateTime": "2024-02-03T20:21:10",
        "externalAccountId": self.account_id,
        "externalEventId": self.event_id,
        "id": self.event_id,
        "objectId": self.event_id,
        "createdAt": "2024-01-14T17:34:33",
        "updatedAt": "2024-06-24T05:19:38"
      }}})
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.cancel_event,
            expected_exception_type=ValueError,
            expected_message="Event is already canceled.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id
        )

    def test_create_or_update_attendee(self):
        """Test creating or updating an attendee."""
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        attendee = HubspotMarketingAPI.MarketingEvents.create_or_update_attendee(
            self.event_id,
            self.account_id,
            self.attendee_email,
            "2023-01-01T10:00:00Z",
            "2023-01-01T12:00:00Z",
        )
        self.assertEqual(attendee["email"], self.attendee_email)
        self.assertEqual(attendee["eventId"], self.event_id)
        self.assertIn(
            self.attendee_id, DB["marketing_events"][self.event_id]["attendees"]
        )

        attendee = HubspotMarketingAPI.MarketingEvents.create_or_update_attendee(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            email=self.attendee_email,
            joinedAt="2023-01-01T10:00:00Z",
            leftAt="2023-01-01T12:00:00Z",
        )
        self.assertEqual(attendee["email"], self.attendee_email)
        self.assertEqual(attendee["eventId"], self.event_id)
        self.assertIn(
            self.attendee_id, DB["marketing_events"][self.event_id]["attendees"]
        )

        # Test missing externalEventId - now raises exception
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.create_or_update_attendee,
            expected_exception_type=EmptyExternalEventIdError,
            expected_message="External Event ID is required and must be a non-empty string.",
            externalEventId=None,
            externalAccountId=self.account_id,
            email=self.attendee_email,
            joinedAt="2023-01-01T10:00:00Z",
            leftAt="2023-01-01T12:00:00Z",
        )

        # Test nonexistent event - now returns MarketingEventNotFoundError
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.create_or_update_attendee,
            expected_exception_type=MarketingEventNotFoundError,
            expected_message="Marketing event with ID 'nonexistent' not found.",
            externalEventId="nonexistent",
            externalAccountId=self.account_id,
            email=self.attendee_email,
            joinedAt="2023-01-01T10:00:00Z",
            leftAt="2023-01-01T12:00:00Z",
        )

        # Test invalid account ID - now raises exception
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.create_or_update_attendee,
            expected_exception_type=InvalidExternalAccountIdError,
            expected_message="External account ID 'nonexistent' does not match the event's account ID.",
            externalEventId=self.event_id,
            externalAccountId="nonexistent",
            email=self.attendee_email,
            joinedAt="2023-01-01T10:00:00Z",
            leftAt="2023-01-01T12:00:00Z",
        )

    def test_get_attendees(self):
        """Test getting attendees for a marketing event."""
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        # Create attendees in non-alphabetical order to test sorting
        HubspotMarketingAPI.MarketingEvents.create_or_update_attendee(
            self.event_id,
            self.account_id,
            "charlie@example.com",
            "2023-01-01T10:00:00Z",
            "2023-01-01T11:00:00Z",
        )
        HubspotMarketingAPI.MarketingEvents.create_or_update_attendee(
            self.event_id,
            self.account_id,
            "alpha@example.com",
            "2023-01-01T10:00:00Z",
            "2023-01-01T12:00:00Z",
        )
        HubspotMarketingAPI.MarketingEvents.create_or_update_attendee(
            self.event_id,
            self.account_id,
            "bravo@example.com",
            "2023-01-01T10:00:00Z",
            "2023-01-01T11:00:00Z",
        )

        attendees = HubspotMarketingAPI.MarketingEvents.get_attendees(self.event_id)
        
        # Verify the results are sorted alphabetically by email
        self.assertEqual(len(attendees["results"]), 3)
        self.assertEqual(attendees["results"][0]["email"], "alpha@example.com")
        self.assertEqual(attendees["results"][1]["email"], "bravo@example.com")
        self.assertEqual(attendees["results"][2]["email"], "charlie@example.com")

    def test_delete_attendee(self):
        """Test deleting an attendee for a marketing event."""
        # --- Success Case ---
        # Create an event and an attendee to be deleted.
        HubspotMarketingAPI.MarketingEvents.create_event(
            self.event_id, self.account_id, "Test Event", "Webinar", "Organizer"
        )
        attendee = HubspotMarketingAPI.MarketingEvents.create_or_update_attendee(
            self.event_id,
            self.account_id,
            self.attendee_email,
            "2023-01-01T10:00:00Z",
            "2023-01-01T12:00:00Z",
        )
        attendee_id_to_delete = attendee["attendeeId"]

        # Assert that the attendee exists before deletion.
        self.assertIn(attendee_id_to_delete, DB["marketing_events"][self.event_id]["attendees"])

        # Perform the deletion.
        HubspotMarketingAPI.MarketingEvents.delete_attendee(
            self.event_id, attendee_id_to_delete, self.account_id
        )

        # Assert that the attendee is no longer present.
        self.assertNotIn(attendee_id_to_delete, DB["marketing_events"][self.event_id]["attendees"])

        # Test missing externalAccountId
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for DeleteAttendeeRequest",
            externalEventId=self.event_id,
            attendeeId=attendee["attendeeId"],
            externalAccountId=None
        )

        # Test missing attendeeId
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for DeleteAttendeeRequest",
            externalEventId=self.event_id,
            attendeeId=None,
            externalAccountId=self.account_id
        )

        # Test nonexistent attendee
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            expected_exception_type=AttendeeNotFoundError,
            expected_message=f"Attendee with ID 'nonexistent' not found in marketing event '{self.event_id}'.",
            externalEventId=self.event_id,
            attendeeId="nonexistent",
            externalAccountId=self.account_id
        )

        # Test nonexistent event
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            expected_exception_type=MarketingEventNotFoundError,
            expected_message="Marketing event with ID 'nonexistent' not found.",
            externalEventId="nonexistent",
            attendeeId=attendee["attendeeId"],
            externalAccountId=self.account_id
        )

        # Test event with empty attendees section (no attendees)
        event = HubspotMarketingAPI.MarketingEvents.create_event(
            "event124", self.account_id, "Test Event", "Webinar", "Organizer"
        )
        # The new event should have an empty attendees section
        self.assertIn("attendees", DB["marketing_events"]["event124"])
        self.assertEqual(len(DB["marketing_events"]["event124"]["attendees"]), 0)
        
        # Test deleting from an event with no attendees (should raise AttendeeNotFoundError, not EventAttendeesNotFoundError)
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            expected_exception_type=AttendeeNotFoundError,
            expected_message="Attendee with ID 'any_attendee_id' not found in marketing event 'event124'.",
            externalEventId="event124",
            attendeeId="any_attendee_id",
            externalAccountId=self.account_id
        )

        # Create attendee again for next test
        attendee = HubspotMarketingAPI.MarketingEvents.create_or_update_attendee(
            self.event_id,
            self.account_id,
            self.attendee_email,
            "2023-01-01T10:00:00Z",
            "2023-01-01T12:00:00Z",
        )
        attendee_id = attendee["attendeeId"]

        # Test Empty/Invalid IDs
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            ValidationError,
            "1 validation error for DeleteAttendeeRequest",
            externalEventId="",
            attendeeId=attendee_id,
            externalAccountId=self.account_id,
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            ValidationError,
            "1 validation error for DeleteAttendeeRequest",
            externalEventId=self.event_id,
            attendeeId="",
            externalAccountId=self.account_id,
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            ValidationError,
            "1 validation error for DeleteAttendeeRequest",
            externalEventId=self.event_id,
            attendeeId=attendee_id,
            externalAccountId="",
        )

        # Test Not Found errors
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            MarketingEventNotFoundError,
            "Marketing event with ID 'nonexistent_event' not found.",
            externalEventId="nonexistent_event",
            attendeeId=attendee_id,
            externalAccountId=self.account_id,
        )
        
        # Test invalid account ID
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            InvalidExternalAccountIdError,
            "External account ID 'wrong_account' does not match the event's account ID.",
            externalEventId=self.event_id,
            attendeeId=attendee_id,
            externalAccountId="wrong_account",
        )

        # Test deleting a non-existent attendee
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            AttendeeNotFoundError,
            f"Attendee with ID 'nonexistent_attendee' not found in marketing event '{self.event_id}'.",
            externalEventId=self.event_id,
            attendeeId="nonexistent_attendee",
            externalAccountId=self.account_id,
        )

        # Test deleting when the event has no 'attendees' key
        event_no_attendees_id = "event_no_attendees"
        HubspotMarketingAPI.MarketingEvents.create_event(
            event_no_attendees_id, self.account_id, "Event Without Attendees", "Webinar", "Organizer"
        )
        # Manually remove the 'attendees' key to simulate the error condition
        if "attendees" in DB["marketing_events"][event_no_attendees_id]:
            del DB["marketing_events"][event_no_attendees_id]["attendees"]

        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.delete_attendee,
            EventAttendeesNotFoundError,
            f"No attendees section found for marketing event '{event_no_attendees_id}'.",
            externalEventId=event_no_attendees_id,
            attendeeId="any_attendee_id",
            externalAccountId=self.account_id,
        )

    def test_create_event_invalid_name(self):
        """Test creating an event with an invalid name."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.create_event,
            ValueError,
            "Field event_name cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name="",
            event_type="Webinar",
            event_organizer="Organizer",
        )

    def test_create_event_invalid_url(self):
        """Test creating an event with an invalid URL."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.create_event,
            ValidationError,
            "validation error",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name="Test Event",
            event_type="Webinar",
            event_organizer="Organizer",
            event_url="not-a-valid-url",
        )

    # def test_create_event_invalid_custom_property(self):
    #     """Test creating an event with invalid custom properties."""
    #     self.assert_error_behavior(
    #         HubspotMarketingAPI.MarketingEvents.create_event,
    #         ValidationError,
    #         "2 validation errors for CreateEventRequest",
    #         externalEventId=self.event_id,
    #         externalAccountId=self.account_id,
    #         event_name="Test Event",
    #         event_type="Webinar",
    #         event_organizer="Organizer",
    #         custom_properties=[{"invalid_key": "value"}],
    #     )

    def test_create_event_returns_all_fields(self):
        """Test that the created event contains all documented fields."""
        event = HubspotMarketingAPI.MarketingEvents.create_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name="Test Event",
            event_type="Webinar",
            event_organizer="Organizer",
        )
        self.assertIn("id", event)
        self.assertIn("createdAt", event)
        self.assertIn("updatedAt", event)
        self.assertEqual(event["registrants"], 0)
        self.assertIsInstance(event["attendees"], dict)
        self.assertFalse(event["eventCompleted"])


class TestCreateCampaignAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Setup method to prepare for each test."""
        DB.clear()
        DB.update(
            {
                "campaigns": {
                    
                    }
                }
        )

    def test_create_campaign(self):
        new_campaign = HubspotMarketingAPI.Campaigns.create_campaign(
            name="New Campaign"
        )
        self.assertEqual(new_campaign["name"], "New Campaign")
        self.assertIn(new_campaign["id"], DB["campaigns"])

    def test_create_campaign_invalid_name(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Name must be a string",
            name=1
        )

    def test_create_campaign_invalid_name_empty(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Name cannot be empty",
            name="  "
        )

    def test_create_campaign_invalid_name_none(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Name is required",
            name=None
        )
    
    def test_create_campaign_invalid_start_year(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Start year must be greater than 1900",
            name="New Campaign",
            start_year=1899
        )

    def test_create_campaign_invalid_start_year_negative(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Start year must be greater than 1900",
            name="New Campaign",
            start_year=-1   
        )

    def test_create_campaign_invalid_start_year(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Start year must be an integer",
            name="New Campaign",
            start_year="2024"
        )

    def test_create_campaign_invalid_start_day(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Start day must be between 1 and 31",
            name="New Campaign",
            start_day=32
        )

    def test_create_campaign_invalid_start_end_date(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Start date must be before end date",
            name="New Campaign",
            start_year=2024,
            start_month=1,
            start_day=1,
            end_year=2023,
            end_month=1,
            end_day=1
        )

    
    def test_create_campaign_invalid_start_month(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Start month must be between 1 and 12",
            name="New Campaign",
            start_month=13
        )

    def test_create_campaign_invalid_start_month_type(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Start month must be an integer",
            name="New Campaign",
            start_month="1"
        )

    def test_create_campaign_invalid_start_day_type(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Start day must be an integer",
            name="New Campaign",
            start_day="1"
        )

    def test_create_campaign_invalid_end_month_type(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="End month must be an integer",
            name="New Campaign",
            end_month="1"
        )

    def test_create_campaign_invalid_end_day_type(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="End day must be an integer",
            name="New Campaign",
            end_day="1"
        )

    def test_create_campaign_invalid_end_year(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="End year must be greater than 1900",
            name="New Campaign",
            end_year=1899
        )

    def test_create_campaign_invalid_end_year_negative(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="End year must be greater than 1900",
            name="New Campaign",
            end_year=-1
        )

    def test_create_campaign_without_slug(self):
        new_campaign = HubspotMarketingAPI.Campaigns.create_campaign(
            name="New Campaign",
            slug=None
        )
        self.assertIn(new_campaign["id"], DB["campaigns"])

    def test_create_campaign_with_slug(self):
        new_campaign = HubspotMarketingAPI.Campaigns.create_campaign(
            name="New Campaign",
            slug="new-campaign"
        )
        self.assertIn(new_campaign["id"], DB["campaigns"])
        self.assertEqual(new_campaign["slug"], "new-campaign")

    def test_create_campaign_invalid_slug(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Slug must be a string",
            name="New Campaign",
            slug=1   
        )

    def test_create_campaign_invalid_description(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Description must be a string",
            name="New Campaign",
            description=1   
        )

    def test_create_campaign_invalid_color_label(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Color label must be a string",
            name="New Campaign",
            color_label=1   
        )
    
    def test_create_campaign_invalid_theme(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Theme must be a string",
            name="New Campaign",
            theme=1   
        )

    def test_create_campaign_invalid_resource(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=TypeError,
            expected_message="Resource must be a string",
            name="New Campaign",
            resource=1   
        )

    def test_create_campaign_invalid_start_date(self):
        self.assert_error_behavior(
            func_to_call=HubspotMarketingAPI.Campaigns.create_campaign,
            expected_exception_type=ValueError,
            expected_message="Start date must be before end date",
            name="New Campaign",
            start_year=2024,
            start_month=1,
            start_day=1,
            end_year=2023,
            end_month=1,
            end_day=1
        )


class TestTemplatesAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        DB.clear()
        self.template_id = "1"

    def test_templates_create_template(self):
        new_template = HubspotMarketingAPI.Templates.create_template(
            category_id=1, folder="test_folder", template_type=2, source="test_source"
        )
        self.assertEqual(new_template["category_id"], 1)
        self.assertEqual(new_template["folder"], "test_folder")
        self.assertEqual(new_template["template_type"], 2)
        self.assertEqual(new_template["source"], "test_source")
        self.assertEqual(
            new_template["id"], str(generate_hubspot_object_id("test_source"))
        )
        self.assertEqual(len(DB["templates"]), 1)

    def test_templates_get_templates(self):
        result = HubspotMarketingAPI.Templates.create_template(
            category_id=1, folder="test_folder", template_type=2, source="test_source"
        )
        templates = HubspotMarketingAPI.Templates.get_templates()
        self.assertEqual(len(templates), 1)
        templates = HubspotMarketingAPI.Templates.get_templates(limit=0)
        self.assertEqual(len(templates), 0)
        templates = HubspotMarketingAPI.Templates.get_templates(id=result["id"])
        self.assertEqual(len(templates), 1)
        templates = HubspotMarketingAPI.Templates.get_templates(id="2")
        self.assertEqual(len(templates), 0)

        created = HubspotMarketingAPI.Templates.create_template(
            category_id=1,
            folder="test_folder",
            template_type=2,
            source="Test Template 7",
        )

        templates = HubspotMarketingAPI.Templates.get_templates(
            deleted_at="1719177600000"
        )
        self.assertEqual(len(templates), 0)

        templates = HubspotMarketingAPI.Templates.get_templates(
            is_available_for_new_content="True"
        )
        self.assertEqual(len(templates), 0)

        templates = HubspotMarketingAPI.Templates.get_templates(label="Test Template 7")
        self.assertEqual(len(templates), 0)

        templates = HubspotMarketingAPI.Templates.get_templates(path="/templates/")
        self.assertEqual(len(templates), 0)

    def test_template_by_id_get_template(self):
        result = HubspotMarketingAPI.Templates.create_template(
            category_id=1, folder="test_folder", template_type=2, source="test_source"
        )
        template = HubspotMarketingAPI.Templates.get_template_by_id(result["id"])
        self.assertEqual(template["id"], result["id"])

    def test_template_by_id_update_template(self):
        result = HubspotMarketingAPI.Templates.create_template(
            category_id=1, folder="test_folder", template_type=2, source="test_source"
        )
        updated_template = HubspotMarketingAPI.Templates.update_template_by_id(
            result["id"], folder="updated_folder"
        )
        self.assertEqual(updated_template["folder"], "updated_folder")

        self.assert_error_behavior(
            HubspotMarketingAPI.Templates.update_template_by_id,
            expected_exception_type=TemplateNotFoundError,
            expected_message="Template with id nonexistent not found.",
            template_id="nonexistent",
            folder="updated_folder"
        )

    def test_template_by_id_delete_template(self):
        result = HubspotMarketingAPI.Templates.create_template(
            category_id=1, folder="test_folder", template_type=2, source="test_source"
        )
        id = result["id"]
        HubspotMarketingAPI.Templates.delete_template_by_id(id)
        self.assertTrue("deleted_at" in DB["templates"][id])

    def test_template_by_id_restore_deleted_template(self):
        result = HubspotMarketingAPI.Templates.create_template(
            category_id=1, folder="test_folder", template_type=2, source="test_source"
        )
        HubspotMarketingAPI.Templates.delete_template_by_id(result["id"])
        restored_template = HubspotMarketingAPI.Templates.restore_deleted_template(
            result["id"]
        )
        self.assertEqual(restored_template["id"], result["id"])

        self.assert_error_behavior(
            HubspotMarketingAPI.Templates.restore_deleted_template,
            expected_exception_type=TemplateNotFoundError,
            expected_message="Template with id nonexistent not found.",
            template_id="nonexistent"
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.Templates.restore_deleted_template,
            expected_exception_type=InvalidTemplateIdTypeError,
            expected_message="template_id must be a string.",
            template_id=123
        )

        self.assert_error_behavior(
            HubspotMarketingAPI.Templates.restore_deleted_template,
            expected_exception_type=EmptyTemplateIdError,
            expected_message="template_id cannot be an empty string.",
            template_id="   "
        )

    def test_state_persistence(self):
        result = HubspotMarketingAPI.Templates.create_template(
            category_id=1, folder="test_folder", template_type=2, source="test_source"
        )
        save_state("test_state.json")
        DB.clear()
        load_state("test_state.json")
        self.assertEqual(len(DB["templates"]), 1)
        self.assertEqual(DB["templates"][result["id"]]["source"], "test_source")
        os.remove("test_state.json")

class TestCreateFormAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Setup method to prepare for each test."""
        DB.clear()
        DB.update(
            {
                "forms": {
                }
            }
        )

    def test_create_form(self):
        input_data = {
            "name": "Test Form",
            "submitText": "Submit Now",
            "fieldGroups": [
                        {
                            "groupType": "email",
                            "richTextType": "text",
                            "richText": "Test Rich Text",
                            "fields": [
                                {
                                    "fieldType": "email",
                                    "name": "email",
                                    "label": "Email",
                                    "required": True,
                                    "placeholder": "Enter your email",
                                    "defaultValue": "test@example.com",
                                    "options": ["Option 1", "Option 2"],
                                    "hidden": False
                                }
                            ]
                        }
                    ]
                }
           
        form = HubspotMarketingAPI.Forms.create_form(
            name="Test Form",
            submitText="Submit Now",
            fieldGroups=input_data["fieldGroups"],
        )
        self.assertEqual(form["name"], "Test Form")
        self.assertEqual(form["submitText"], "Submit Now")
        self.assertEqual(form["fieldGroups"], input_data["fieldGroups"])
        self.assertIn(form["id"], DB["forms"])

    def test_create_form_invalid_name(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValueError,
            expected_message="Name is required",
            name=None,
            submitText="Submit Now",
            fieldGroups=[],
        )
        
    def test_create_form_invalid_submit_text(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValueError,
            expected_message="Submit text is required",
            name="Test Form",
            submitText=None,
            fieldGroups=[],
        )

    def test_create_form_invalid_name_empty(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValueError,
            expected_message="Name cannot be empty",
            name="",
            submitText="Submit Now",
            fieldGroups=[],
        )
        
    def test_create_form_invalid_field_groups(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValueError,
            expected_message="Field groups are required",
            name="Test Form",
            submitText="Submit Now",
            fieldGroups=None,
        )

    def test_create_form_invalid_submit_text_empty(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValueError,
            expected_message="Submit text cannot be empty",
            name="Test Form",
            submitText="",
            fieldGroups=[],
        )
        
    def test_create_form_invalid_name_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=TypeError,
            expected_message="Name must be a string",
            name=999,
            submitText="Submit Now",
            fieldGroups=[],
        )

    def test_create_form_invalid_submit_text_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=TypeError,
            expected_message="Submit text must be a string",
            name="Test Form",
            submitText=999,
            fieldGroups=[],
        )

    def test_create_form_invalid_field_groups_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=TypeError,
            expected_message="Field groups must be a list",
            name="Test Form",
            submitText="Submit Now",
            fieldGroups=999,
        )

    def test_create_form_invalid_legal_consent_options_type(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=TypeError,
            expected_message="Legal consent options must be a dictionary",
            name="Test Form",
            submitText="Submit Now",
            fieldGroups=[],
            legalConsentOptions=999,
        )

    def test_create_form_invalid_field_groups_structure(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            name="Test Form",
            submitText="Submit Now",
            fieldGroups=[
            {
                "groupType": "email", 
                "richTextType": "text",
                "richText": "Test Rich Text",
                "fields": [
                    {
                        "fieldType": "email",
                    }
                ]
            }]
        )

    def test_create_form_invalid_legal_consent_options_structure(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            name="Test Form",
            submitText="Submit Now",
            fieldGroups=[
                {
                    "groupType": "email",
                    "richTextType": "text",
                    "richText": "Test Rich Text",
                    "fields": [
                        {
                            "fieldType": "email",
                            "name": "email",
                            "label": "Email",
                            "required": True,
                            "placeholder": "Enter your email",
                            "defaultValue": "test@example.com",
                            "options": ["Option 1", "Option 2"],
                            "hidden": False
                        }
                    ]
                }
            ],
            legalConsentOptions={
                "explicitConsentToProcess": {
                    "communicationsCheckboxes": [
            ]}}
        )

    def test_create_form_with_all_fields(self):
        input_data = {
            "name": "Test Form",
        "submitText": "Submit Now",
        "fieldGroups": [
          {
            "groupType": "email",
            "richTextType": "text",
            "richText": "Test Rich Text",
            "fields": [
              {
                "fieldType": "email",
                "name": "email",
                "label": "Email",
                "required": True,
                "placeholder": "Enter your email",
                "defaultValue": "test@example.com",
                "options": ["Option 1", "Option 2"],
                "hidden": False
              }]
            }
        ],
        "legalConsentOptions": {
          "explicitConsentToProcess": {
            "communicationsCheckboxes": [
              {
                "subscriptionTypeId": 1,
                "label": "Email",
                "required": True
              }
            ],
            "communicationConsentText": "Test Communication Consent Text",
            "consentToProcessCheckboxLabel": "Test Consent To Process Checkbox Label",
            "consentToProcessFooterText": "Test Consent To Process Footer Text",
            "type": "explicit",
            "privacyText": "Test Privacy Text",
            "consentToProcessText": "Test Consent To Process Text"
          }
        }}
        form = HubspotMarketingAPI.Forms.create_form(
            name=input_data["name"],
            submitText=input_data["submitText"],
            fieldGroups=input_data["fieldGroups"],
            legalConsentOptions=input_data["legalConsentOptions"]
       )
       
        self.assertIn(form["id"], DB["forms"])


        
        
      
class TestUpdateCampaignsAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "campaigns": {
                    "b1ba6c2d-8620-416a-aee7-a3347315311b": {
        "id": "b1ba6c2d-8620-416a-aee7-a3347315311b",
        "name": "Winter Holiday Sale",
        "slug": "winter-holiday-sale",
        "description": "Winter Holiday Sale",
        "start_year": 2024,
        "start_month": 5,
        "start_day": 24,
        "end_year": 2024,
        "end_month": 11,
        "end_day": 25,
        "theme": "Winter",
        "resource": "Winter Holiday Sale",
        "color_label": "Winter",
        "created_at": "2024-05-24T05:42:00"
      },
      "aedf35ed-8c02-4973-92b4-3c7c1ee83ddb": {
        "id": "aedf35ed-8c02-4973-92b4-3c7c1ee83ddb",
        "name": "Year-End Customer Appreciation",
        "slug": "year-end-customer-appreciation",
        "description": "Year-End Customer Appreciation",
        "start_year": 2024,
        "start_month": 3,
        "start_day": 23,
        "end_year": 2024,
        "end_month": 11,
        "end_day": 16,
        "theme": "Year-End",
        "resource": "Year-End Customer Appreciation",
        "color_label": "Year-End",
        "created_at": "2024-03-23T20:52:17"
      }
                }
            }
        )

    def test_update_campaign(self):
        updated_campaign = HubspotMarketingAPI.Campaigns.update_campaign(
            "b1ba6c2d-8620-416a-aee7-a3347315311b", name="Updated Campaign", description="Updated Description"
        )
        self.assertEqual(updated_campaign["name"], "Updated Campaign")
        self.assertEqual(updated_campaign["description"], "Updated Description")
        self.assertEqual(DB["campaigns"]["b1ba6c2d-8620-416a-aee7-a3347315311b"]["name"], "Updated Campaign")
        self.assertEqual(DB["campaigns"]["b1ba6c2d-8620-416a-aee7-a3347315311b"]["description"], "Updated Description")

    def test_update_campaign_invalid_name(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=TypeError,
            expected_message="Name must be a string",
            campaign_id="b1ba6c2d-8620-416a-aee7-a3347315311b",
            name=999,
        )

    def test_update_campaign_invalid_description(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=TypeError,
            expected_message="Description must be a string",
            campaign_id="b1ba6c2d-8620-416a-aee7-a3347315311b",
            description=999,
        )

    def test_update_campaign_invalid_start_year(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=TypeError,
            expected_message="Start year must be an integer",
            campaign_id="b1ba6c2d-8620-416a-aee7-a3347315311b",
            start_year="2024",
        )
        
    def test_update_campaign_invalid_start_date(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=ValueError,
            expected_message="Start date must be before end date",
            campaign_id="b1ba6c2d-8620-416a-aee7-a3347315311b",
            start_year=2024,
            start_month=1,
            end_year=2023)

    def test_update_campaign_invalid_campaign_id(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=TypeError,
            expected_message="Campaign ID must be a string",
            campaign_id=999,
        )

    def test_update_campaign_campaign_not_found(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=ValueError,
            expected_message="Campaign not found",
            campaign_id="b1ba6c2d-8620-416a-aee7-a3347315311c",
        )
        
    def test_update_campaign_no_campaign_id(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=ValueError,
            expected_message="Campaign ID is required",
            campaign_id=None,
        )

    def test_update_campaign_invalid_campaign_id_uuid(self):
        self.assert_error_behavior(
            HubspotMarketingAPI.Campaigns.update_campaign,
            expected_exception_type=ValueError,
            expected_message="Campaign ID must be a valid UUID",
            campaign_id="b1ba6c2d",
        )

class TestUpdateEvent(BaseTestCaseWithErrorHandler):
    """Comprehensive test class for the update_event method testing everything in minute detail."""

    def setUp(self):
        """Set up the test environment with a base event."""
        DB.update(
            {
                "marketing_events": {},
                "attendees": {},
                "transactional_emails": {},
                "templates": {},
                "contacts": {},
                "marketing_emails": {},
                "campaigns": {},
                "forms": {},
                "subscription_definitions": [],
                "subscriptions": {},
            }
        )
        self.event_id = "test_event_123"
        self.account_id = "test_account_456"
        self.other_account_id = "other_account_789"
        DB["marketing_events"][self.event_id] = {
        "registrants": 100,
        "attendees": 50,
        "eventOrganizer": "Test Organizer",
        "eventUrl": "https://example.com/events/2",
        "eventType": "Webinar",
        "noShows": 10,
        "cancellations": 5,
        "eventDescription": "Join us for Mobile World Congress to learn about Trade Show topics.",
        "eventName": "CES 2024",
        "eventCancelled": True,
        "eventCompleted": True,
        "customProperties": {
          "sourceId": "123-456-7890",
          "selectedByUser": True,
          "sourceLabel": "Webinar",
          "source": "Webinar",
          "updatedByUserId": 123,
          "persistenceTimestamp": 1714857600,
          "sourceMetadata": "Y29udHJvbHM6W10=",
          "dataSensitivity": "public",
          "unit": "number",
          "requestId": "123-456-7890",
          "isEncrypted": False,
          "name": "location",
          "useTimestampAsPersistenceTimestamp": True,
          "value": "Online",
          "selectedByUserTimestamp": 1714857600,
          "timestamp": 1714857600,
          "isLargeValue": False
        },
        "endDateTime": "2024-04-09T11:48:26",
        "startDateTime": "2024-02-03T20:21:10",
        "externalAccountId": self.account_id,
        "externalEventId": self.event_id,
        "id": self.event_id,
        "objectId": self.event_id,
        "createdAt": "2024-01-14T17:34:33",
        "updatedAt": "2024-06-24T05:19:38"
      }

    # ============================================================================
    # Required Parameters Validation Tests
    # ============================================================================

    def test_update_event_none_external_event_id(self):
        """Test that None externalEventId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID is required.",
            externalEventId=None,
            externalAccountId=self.account_id
        )

    def test_update_event_none_external_account_id(self):
        """Test that None externalAccountId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID is required.",
            externalEventId=self.event_id,
            externalAccountId=None
        )

    def test_update_event_invalid_type_external_event_id(self):
        """Test that non-string externalEventId raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="External Event ID must be a string.",
            externalEventId=123,
            externalAccountId=self.account_id
        )

    def test_update_event_invalid_type_external_account_id(self):
        """Test that non-string externalAccountId raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="External Account ID must be a string.",
            externalEventId=self.event_id,
            externalAccountId=456
        )

    def test_update_event_empty_external_event_id(self):
        """Test that empty externalEventId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID cannot be empty.",
            externalEventId="   ",
            externalAccountId=self.account_id
        )

    def test_update_event_empty_external_account_id(self):
        """Test that empty externalAccountId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId="   "
        )

    # ============================================================================
    # Event Existence and Ownership Validation Tests
    # ============================================================================

    def test_update_event_not_found(self):
        """Test that updating non-existent event raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event not found in DB.",
            externalEventId="nonexistent_event",
            externalAccountId=self.account_id
        )

    def test_update_event_wrong_account(self):
        """Test that updating event with wrong account ID raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event does not belong to the account.",
            externalEventId=self.event_id,
            externalAccountId=self.other_account_id
        )

    # ============================================================================
    # Registrants Parameter Validation Tests
    # ============================================================================

    def test_update_event_registrants_invalid_type(self):
        """Test that non-integer registrants raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Registrants must be an integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants="invalid"
        )

    def test_update_event_registrants_negative(self):
        """Test that negative registrants raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Registrants must be a positive integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=-1
        )

    def test_update_event_registrants_valid(self):
        """Test successful registrants update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=50
        )
        self.assertEqual(result["registrants"], 50)
        self.assertEqual(DB["marketing_events"][self.event_id]["registrants"], 50)

    # ============================================================================
    # Event Organizer Parameter Validation Tests
    # ============================================================================

    def test_update_event_organizer_invalid_type(self):
        """Test that non-string event_organizer raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event organizer must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_organizer=123
        )

    def test_update_event_organizer_empty(self):
        """Test that empty event_organizer raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event organizer cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_organizer="   "
        )

    def test_update_event_organizer_valid(self):
        """Test successful event_organizer update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_organizer="New Organizer"
        )
        self.assertEqual(result["eventOrganizer"], "New Organizer")

    # ============================================================================
    # Event URL Parameter Validation Tests
    # ============================================================================

    def test_update_event_url_invalid_type(self):
        """Test that non-string event_url raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event URL must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_url=123
        )

    def test_update_event_url_empty(self):
        """Test that empty event_url raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event URL cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_url="   "
        )

    def test_update_event_url_valid(self):
        """Test successful event_url update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_url="https://example.com/event"
        )
        self.assertEqual(result["eventUrl"], "https://example.com/event")

    # ============================================================================
    # Attendees Parameter Validation Tests
    # ============================================================================

    def test_update_event_attendees_invalid_type(self):
        """Test that non-integer attendees raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Attendees must be an integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            attendees="invalid"
        )

    def test_update_event_attendees_negative(self):
        """Test that negative attendees raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Attendees must be a positive integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            attendees=-1
        )

    def test_update_event_attendees_valid(self):
        """Test successful attendees update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            attendees=25
        )
        self.assertEqual(result["attendees"], 25)

    # ============================================================================
    # Event Type Parameter Validation Tests
    # ============================================================================

    def test_update_event_type_invalid_type(self):
        """Test that non-string event_type raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event type must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_type=123
        )

    def test_update_event_type_empty(self):
        """Test that empty event_type raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event type cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_type="   "
        )

    def test_update_event_type_valid(self):
        """Test successful event_type update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_type="Conference"
        )
        self.assertEqual(result["eventType"], "Conference")

    # ============================================================================
    # Event Completed Parameter Validation Tests
    # ============================================================================

    def test_update_event_completed_invalid_type(self):
        """Test that non-boolean event_completed raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event completed must be a boolean.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed="invalid"
        )

    def test_update_event_completed_valid(self):
        """Test successful event_completed update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed=True
        )
        self.assertEqual(result["eventCompleted"], True)

    # ============================================================================
    # Start Date Time Parameter Validation Tests
    # ============================================================================

    def test_update_event_start_date_invalid_type(self):
        """Test that non-string start_date_time raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Start date time must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time=123
        )

    def test_update_event_start_date_empty(self):
        """Test that empty start_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Start date time cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="   "
        )

    def test_update_event_start_date_invalid_format(self):
        """Test that invalid format start_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Start date time must be in valid format.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="invalid-date-format"
        )

    def test_update_event_start_date_valid(self):
        """Test successful start_date_time update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="2024-01-01T10:00:00"
        )
        self.assertEqual(result["startDateTime"], "2024-01-01T10:00:00")

    # ============================================================================
    # End Date Time Parameter Validation Tests
    # ============================================================================

    def test_update_event_end_date_invalid_type(self):
        """Test that non-string end_date_time raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="End date time must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            end_date_time=123
        )

    def test_update_event_end_date_empty(self):
        """Test that empty end_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="End date time cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            end_date_time="   "
        )

    def test_update_event_end_date_invalid_format(self):
        """Test that invalid format end_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="End date time must be in valid format.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            end_date_time="invalid-date-format"
        )

    def test_update_event_end_date_valid(self):
        """Test successful end_date_time update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="2024-01-01T10:00:00",
            end_date_time="2024-01-01T12:00:00"
        )
        self.assertEqual(result["endDateTime"], "2024-01-01T12:00:00")

    def test_update_event_start_after_end_date(self):
        """Test that start_date_time after end_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Start date time must be before end date time.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="2024-01-01T12:00:00",
            end_date_time="2024-01-01T10:00:00"
        )

    # ============================================================================
    # Event Description Parameter Validation Tests
    # ============================================================================

    def test_update_event_description_invalid_type(self):
        """Test that non-string event_description raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event description must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_description=123
        )

    def test_update_event_description_empty(self):
        """Test that empty event_description raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event description cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_description="   "
        )

    def test_update_event_description_valid(self):
        """Test successful event_description update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_description="Updated event description"
        )
        self.assertEqual(result["eventDescription"], "Updated event description")

    # ============================================================================
    # Event Name Parameter Validation Tests
    # ============================================================================

    def test_update_event_name_invalid_type(self):
        """Test that non-string event_name raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event name must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name=123
        )

    def test_update_event_name_empty(self):
        """Test that empty event_name raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event name cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name="   "
        )

    def test_update_event_name_valid(self):
        """Test successful event_name update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name="Updated Event Name"
        )
        self.assertEqual(result["eventName"], "Updated Event Name")

    # ============================================================================
    # No Shows Parameter Validation Tests
    # ============================================================================

    def test_update_event_no_shows_invalid_type(self):
        """Test that non-integer no_shows raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="No shows must be an integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            no_shows="invalid"
        )

    def test_update_event_no_shows_negative(self):
        """Test that negative no_shows raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="No shows must be a positive integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            no_shows=-1
        )

    def test_update_event_no_shows_event_not_completed(self):
        """Test that no_shows on incomplete event raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="No shows can only be set when the event is over.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed=False,
            no_shows=5
        )

    def test_update_event_no_shows_valid(self):
        """Test successful no_shows update on completed event."""
        # First mark event as completed
        HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed=True
        )
        
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            no_shows=5
        )
        self.assertEqual(result["noShows"], 5)

    # ============================================================================
    # Custom Properties Parameter Validation Tests
    # ============================================================================

    def test_update_event_custom_properties_invalid_type(self):
        """Test that non-dict custom_properties raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Custom properties must be a list.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            custom_properties="invalid"
        )

    def test_update_event_custom_properties_invalid_structure(self):
        """Test that invalid custom properties structure raises ValidationError."""
        # Test with invalid custom property structure
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            custom_properties=[{"invalid": "property"}]
        )

        # Test with valid custom property structure
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            custom_properties=[{
                "name": "location", 
                "value": "Online",
                "sourceId": "123",
                "selectedByUser": True,
                "sourceLabel": "Webinar",
                "source": "Webinar",
                "updatedByUserId": 123,
                "persistenceTimestamp": 1714857600,
                "sourceMetadata": "Y29udHJvbHM6W10=",
                "dataSensitivity": "public",
                "unit": "number",
                "requestId": "123-456-7890",
                "isEncrypted": False,
                "useTimestampAsPersistenceTimestamp": True,
                "selectedByUserTimestamp": 1714857600,
                "timestamp": 1714857600,
                "isLargeValue": False,
                "subscriptionDetails": {
                    "contact_id": "contact123",
                    "subscribed": True,
                    "opt_in_date": "2024-01-01T00:00:00Z"
                }
            }]
        )
        self.assertIn("customProperties", result)

    # ============================================================================
    # Comprehensive Success Tests
    # ============================================================================

    def test_update_event_all_parameters_success(self):
        """Test successful update with all valid parameters."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=100,
            event_name="Updated Test Event",
            event_type="Conference",
            start_date_time="2024-01-01T09:00:00",
            end_date_time="2024-01-01T17:00:00",
            event_organizer="Updated Organizer",
            event_description="Updated description",
            event_url="https://example.com/updated",
            attendees=75,
            event_completed=True,
            custom_properties=[{"name": "location", "value": "Online"}]
        )
        
        # Verify all fields were updated
        self.assertEqual(result["registrants"], 100)
        self.assertEqual(result["eventName"], "Updated Test Event")
        self.assertEqual(result["eventType"], "Conference")
        self.assertEqual(result["startDateTime"], "2024-01-01T09:00:00")
        self.assertEqual(result["endDateTime"], "2024-01-01T17:00:00")
        self.assertEqual(result["eventOrganizer"], "Updated Organizer")
        self.assertEqual(result["eventDescription"], "Updated description")
        self.assertEqual(result["eventUrl"], "https://example.com/updated")
        self.assertEqual(result["attendees"], 75)
        self.assertEqual(result["eventCompleted"], True)
        
        # Verify DB was updated
        db_event = DB["marketing_events"][self.event_id]
        self.assertEqual(db_event["registrants"], 100)
        self.assertEqual(db_event["eventName"], "Updated Test Event")
        self.assertEqual(db_event["eventType"], "Conference")

    def test_update_event_partial_update_success(self):
        """Test successful update with only some parameters."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=50,
            event_name="Partially Updated Event"
        )
        
        # Verify only specified fields were updated
        self.assertEqual(result["registrants"], 50)
        self.assertEqual(result["eventName"], "Partially Updated Event")
        # Original values should remain
        self.assertEqual(result["eventType"], "Webinar")
        self.assertEqual(result["eventOrganizer"], "Test Organizer")

    def test_update_event_zero_values_success(self):
        """Test successful update with zero values for integer fields."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=0,
            attendees=0
        )
        
        self.assertEqual(result["registrants"], 0)
        self.assertEqual(result["attendees"], 0)

    def test_update_event_updated_at_timestamp(self):
        """Test that updatedAt timestamp is updated on every update."""
        original_event = DB["marketing_events"][self.event_id].copy()
        
        # Update event
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=10
        )
        
        # Verify updatedAt was changed
        self.assertNotEqual(result["updatedAt"], original_event.get("updatedAt"))
        self.assertIn("updatedAt", result)

class TestGetEvents(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data for get_events tests."""
        DB['marketing_events'] = {
            "event1": {"id": "event1", "eventName": "Event 1", "createdAt": "2023-01-01T12:00:00Z"},
            "event2": {"id": "event2", "eventName": "Event 2", "createdAt": "2023-01-02T12:00:00Z"},
            "event3": {"id": "event3", "eventName": "Event 3", "createdAt": "2023-01-03T12:00:00Z"},
            "event4": {"id": "event4", "eventName": "Event 4", "createdAt": "2023-01-04T12:00:00Z"},
        }

    def test_get_events_no_filters(self):
        """Test getting all events without any filters."""
        response = HubspotMarketingAPI.MarketingEvents.get_events()
        self.assertEqual(len(response["results"]), 4)
        self.assertIsNone(response["paging"])

    def test_get_events_with_limit(self):
        """Test the limit parameter."""
        response = HubspotMarketingAPI.MarketingEvents.get_events(limit=2)
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["id"], "event1")
        self.assertIsNotNone(response["paging"])
        self.assertEqual(response["paging"]["next"]["after"], "event2")

    def test_get_events_with_after(self):
        """Test the after parameter for pagination."""
        response = HubspotMarketingAPI.MarketingEvents.get_events(after="event2")
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["id"], "event3")
        self.assertIsNone(response["paging"])

    def test_get_events_with_limit_and_after(self):
        """Test limit and after parameters together."""
        response = HubspotMarketingAPI.MarketingEvents.get_events(limit=1, after="event1")
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["id"], "event2")
        self.assertIsNotNone(response["paging"])

    def test_get_events_occurred_after(self):
        """Test filtering with occurredAfter."""
        response = HubspotMarketingAPI.MarketingEvents.get_events(occurredAfter="2023-01-02T12:00:00Z")
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["id"], "event3")

    def test_get_events_occurred_before(self):
        """Test filtering with occurredBefore."""
        response = HubspotMarketingAPI.MarketingEvents.get_events(occurredBefore="2023-01-03T12:00:00Z")
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["id"], "event1")

    def test_get_events_date_range(self):
        """Test filtering with both occurredAfter and occurredBefore."""
        response = HubspotMarketingAPI.MarketingEvents.get_events(
            occurredAfter="2023-01-01T12:00:00Z",
            occurredBefore="2023-01-04T12:00:00Z"
        )
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["id"], "event2")

    def test_get_events_invalid_limit(self):
        """Test with an invalid limit value."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_events,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            limit=200
        )

    def test_get_events_invalid_date_format(self):
        """Test with an invalid date format."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.get_events,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            occurredAfter="invalid-date"
        )

    def test_get_events_invalid_after_cursor(self):
        """Test with an invalid 'after' cursor."""
        response = HubspotMarketingAPI.MarketingEvents.get_events(after="invalid-cursor")
        self.assertEqual(len(response["results"]), 0)
        self.assertIsNone(response["paging"])

class TestUpdateEvent(BaseTestCaseWithErrorHandler):
    """Comprehensive test class for the update_event method testing everything in minute detail."""

    def setUp(self):
        """Set up the test environment with a base event."""
        DB.update(
            {
                "marketing_events": {},
                "attendees": {},
                "transactional_emails": {},
                "templates": {},
                "contacts": {},
                "marketing_emails": {},
                "campaigns": {},
                "forms": {},
                "subscription_definitions": [],
                "subscriptions": {},
            }
        )
        self.event_id = "test_event_123"
        self.account_id = "test_account_456"
        self.other_account_id = "other_account_789"
        DB["marketing_events"][self.event_id] = {
        "registrants": 100,
        "attendees": 50,
        "eventOrganizer": "Test Organizer",
        "eventUrl": "https://example.com/events/2",
        "eventType": "Webinar",
        "noShows": 10,
        "cancellations": 5,
        "eventDescription": "Join us for Mobile World Congress to learn about Trade Show topics.",
        "eventName": "CES 2024",
        "eventCancelled": True,
        "eventCompleted": True,
        "customProperties": {
          "sourceId": "123-456-7890",
          "selectedByUser": True,
          "sourceLabel": "Webinar",
          "source": "Webinar",
          "updatedByUserId": 123,
          "persistenceTimestamp": 1714857600,
          "sourceMetadata": "Y29udHJvbHM6W10=",
          "dataSensitivity": "public",
          "unit": "number",
          "requestId": "123-456-7890",
          "isEncrypted": False,
          "name": "location",
          "useTimestampAsPersistenceTimestamp": True,
          "value": "Online",
          "selectedByUserTimestamp": 1714857600,
          "timestamp": 1714857600,
          "isLargeValue": False
        },
        "endDateTime": "2024-04-09T11:48:26",
        "startDateTime": "2024-02-03T20:21:10",
        "externalAccountId": self.account_id,
        "externalEventId": self.event_id,
        "id": self.event_id,
        "objectId": self.event_id,
        "createdAt": "2024-01-14T17:34:33",
        "updatedAt": "2024-06-24T05:19:38"
      }

    # ============================================================================
    # Required Parameters Validation Tests
    # ============================================================================

    def test_update_event_none_external_event_id(self):
        """Test that None externalEventId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID is required.",
            externalEventId=None,
            externalAccountId=self.account_id
        )

    def test_update_event_none_external_account_id(self):
        """Test that None externalAccountId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID is required.",
            externalEventId=self.event_id,
            externalAccountId=None
        )

    def test_update_event_invalid_type_external_event_id(self):
        """Test that non-string externalEventId raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="External Event ID must be a string.",
            externalEventId=123,
            externalAccountId=self.account_id
        )

    def test_update_event_invalid_type_external_account_id(self):
        """Test that non-string externalAccountId raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="External Account ID must be a string.",
            externalEventId=self.event_id,
            externalAccountId=456
        )

    def test_update_event_empty_external_event_id(self):
        """Test that empty externalEventId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Event ID cannot be empty.",
            externalEventId="   ",
            externalAccountId=self.account_id
        )

    def test_update_event_empty_external_account_id(self):
        """Test that empty externalAccountId raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="External Account ID cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId="   "
        )

    # ============================================================================
    # Event Existence and Ownership Validation Tests
    # ============================================================================

    def test_update_event_not_found(self):
        """Test that updating non-existent event raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event not found in DB.",
            externalEventId="nonexistent_event",
            externalAccountId=self.account_id
        )

    def test_update_event_wrong_account(self):
        """Test that updating event with wrong account ID raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event does not belong to the account.",
            externalEventId=self.event_id,
            externalAccountId=self.other_account_id
        )

    # ============================================================================
    # Registrants Parameter Validation Tests
    # ============================================================================

    def test_update_event_registrants_invalid_type(self):
        """Test that non-integer registrants raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Registrants must be an integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants="invalid"
        )

    def test_update_event_registrants_negative(self):
        """Test that negative registrants raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Registrants must be a positive integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=-1
        )

    def test_update_event_registrants_valid(self):
        """Test successful registrants update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=50
        )
        self.assertEqual(result["registrants"], 50)
        self.assertEqual(DB["marketing_events"][self.event_id]["registrants"], 50)

    # ============================================================================
    # Event Organizer Parameter Validation Tests
    # ============================================================================

    def test_update_event_organizer_invalid_type(self):
        """Test that non-string event_organizer raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event organizer must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_organizer=123
        )

    def test_update_event_organizer_empty(self):
        """Test that empty event_organizer raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event organizer cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_organizer="   "
        )

    def test_update_event_organizer_valid(self):
        """Test successful event_organizer update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_organizer="New Organizer"
        )
        self.assertEqual(result["eventOrganizer"], "New Organizer")

    # ============================================================================
    # Event URL Parameter Validation Tests
    # ============================================================================

    def test_update_event_url_invalid_type(self):
        """Test that non-string event_url raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event URL must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_url=123
        )

    def test_update_event_url_empty(self):
        """Test that empty event_url raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event URL cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_url="   "
        )

    def test_update_event_url_valid(self):
        """Test successful event_url update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_url="https://example.com/event"
        )
        self.assertEqual(result["eventUrl"], "https://example.com/event")

    # ============================================================================
    # Attendees Parameter Validation Tests
    # ============================================================================

    def test_update_event_attendees_invalid_type(self):
        """Test that non-integer attendees raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Attendees must be an integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            attendees="invalid"
        )

    def test_update_event_attendees_negative(self):
        """Test that negative attendees raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Attendees must be a positive integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            attendees=-1
        )

    def test_update_event_attendees_valid(self):
        """Test successful attendees update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            attendees=25
        )
        self.assertEqual(result["attendees"], 25)

    # ============================================================================
    # Event Type Parameter Validation Tests
    # ============================================================================

    def test_update_event_type_invalid_type(self):
        """Test that non-string event_type raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event type must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_type=123
        )

    def test_update_event_type_empty(self):
        """Test that empty event_type raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event type cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_type="   "
        )

    def test_update_event_type_valid(self):
        """Test successful event_type update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_type="Conference"
        )
        self.assertEqual(result["eventType"], "Conference")

    # ============================================================================
    # Event Completed Parameter Validation Tests
    # ============================================================================

    def test_update_event_completed_invalid_type(self):
        """Test that non-boolean event_completed raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event completed must be a boolean.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed="invalid"
        )

    def test_update_event_completed_valid(self):
        """Test successful event_completed update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed=True
        )
        self.assertEqual(result["eventCompleted"], True)

    # ============================================================================
    # Start Date Time Parameter Validation Tests
    # ============================================================================

    def test_update_event_start_date_invalid_type(self):
        """Test that non-string start_date_time raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Start date time must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time=123
        )

    def test_update_event_start_date_empty(self):
        """Test that empty start_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Start date time cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="   "
        )

    def test_update_event_start_date_invalid_format(self):
        """Test that invalid format start_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Start date time must be in valid format.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="invalid-date-format"
        )

    def test_update_event_start_date_valid(self):
        """Test successful start_date_time update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="2024-01-01T10:00:00"
        )
        self.assertEqual(result["startDateTime"], "2024-01-01T10:00:00")

    # ============================================================================
    # End Date Time Parameter Validation Tests
    # ============================================================================

    def test_update_event_end_date_invalid_type(self):
        """Test that non-string end_date_time raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="End date time must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            end_date_time=123
        )

    def test_update_event_end_date_empty(self):
        """Test that empty end_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="End date time cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            end_date_time="   "
        )

    def test_update_event_end_date_invalid_format(self):
        """Test that invalid format end_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="End date time must be in valid format.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            end_date_time="invalid-date-format"
        )

    def test_update_event_end_date_valid(self):
        """Test successful end_date_time update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="2024-01-01T10:00:00",
            end_date_time="2024-01-01T12:00:00"
        )
        self.assertEqual(result["endDateTime"], "2024-01-01T12:00:00")

    def test_update_event_start_after_end_date(self):
        """Test that start_date_time after end_date_time raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Start date time must be before end date time.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            start_date_time="2024-01-01T12:00:00",
            end_date_time="2024-01-01T10:00:00"
        )

    # ============================================================================
    # Event Description Parameter Validation Tests
    # ============================================================================

    def test_update_event_description_invalid_type(self):
        """Test that non-string event_description raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event description must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_description=123
        )

    def test_update_event_description_empty(self):
        """Test that empty event_description raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event description cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_description="   "
        )

    def test_update_event_description_valid(self):
        """Test successful event_description update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_description="Updated event description"
        )
        self.assertEqual(result["eventDescription"], "Updated event description")

    # ============================================================================
    # Event Name Parameter Validation Tests
    # ============================================================================

    def test_update_event_name_invalid_type(self):
        """Test that non-string event_name raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Event name must be a string.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name=123
        )

    def test_update_event_name_empty(self):
        """Test that empty event_name raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="Event name cannot be empty.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name="   "
        )

    def test_update_event_name_valid(self):
        """Test successful event_name update."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_name="Updated Event Name"
        )
        self.assertEqual(result["eventName"], "Updated Event Name")

    # ============================================================================
    # No Shows Parameter Validation Tests
    # ============================================================================

    def test_update_event_no_shows_invalid_type(self):
        """Test that non-integer no_shows raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="No shows must be an integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            no_shows="invalid"
        )

    def test_update_event_no_shows_negative(self):
        """Test that negative no_shows raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="No shows must be a positive integer.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            no_shows=-1
        )

    def test_update_event_no_shows_event_not_completed(self):
        """Test that no_shows on incomplete event raises ValueError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValueError,
            expected_message="No shows can only be set when the event is over.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed=False,
            no_shows=5
        )

    def test_update_event_no_shows_valid(self):
        """Test successful no_shows update on completed event."""
        # First mark event as completed
        HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            event_completed=True
        )
        
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            no_shows=5
        )
        self.assertEqual(result["noShows"], 5)

    # ============================================================================
    # Custom Properties Parameter Validation Tests
    # ============================================================================

    def test_update_event_custom_properties_invalid_type(self):
        """Test that non-dict custom_properties raises TypeError."""
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=TypeError,
            expected_message="Custom properties must be a list.",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            custom_properties="invalid"
        )

    def test_update_event_custom_properties_invalid_structure(self):
        """Test that invalid custom properties structure raises ValidationError."""
        # Test with invalid custom property structure
        self.assert_error_behavior(
            HubspotMarketingAPI.MarketingEvents.update_event,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            custom_properties=[{"invalid": "property"}]
        )

        # Test with valid custom property structure
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            custom_properties=[{
                "name": "location", 
                "value": "Online",
                "sourceId": "123",
                "selectedByUser": True,
                "sourceLabel": "Webinar",
                "source": "Webinar",
                "updatedByUserId": 123,
                "persistenceTimestamp": 1714857600,
                "sourceMetadata": "Y29udHJvbHM6W10=",
                "dataSensitivity": "public",
                "unit": "number",
                "requestId": "123-456-7890",
                "isEncrypted": False,
                "useTimestampAsPersistenceTimestamp": True,
                "selectedByUserTimestamp": 1714857600,
                "timestamp": 1714857600,
                "isLargeValue": False,
                "subscriptionDetails": {
                    "contact_id": "contact123",
                    "subscribed": True,
                    "opt_in_date": "2024-01-01T00:00:00Z"
                }
            }]
        )
        self.assertIn("customProperties", result)

    # ============================================================================
    # Comprehensive Success Tests
    # ============================================================================

    def test_update_event_all_parameters_success(self):
        """Test successful update with all valid parameters."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=100,
            event_name="Updated Test Event",
            event_type="Conference",
            start_date_time="2024-01-01T09:00:00",
            end_date_time="2024-01-01T17:00:00",
            event_organizer="Updated Organizer",
            event_description="Updated description",
            event_url="https://example.com/updated",
            attendees=75,
            event_completed=True,
            custom_properties=[{
                "name": "location", 
                "value": "Online",
                "sourceId": "123",
                "selectedByUser": True,
                "sourceLabel": "Webinar",
                "source": "Webinar",
                "updatedByUserId": 123,
                "persistenceTimestamp": 1714857600,
                "sourceMetadata": "Y29udHJvbHM6W10=",
                "dataSensitivity": "public",
                "unit": "number",
                "requestId": "123-456-7890",
                "isEncrypted": False,
                "useTimestampAsPersistenceTimestamp": True,
                "selectedByUserTimestamp": 1714857600,
                "timestamp": 1714857600,
                "isLargeValue": False,
                "subscriptionDetails": {
                    "contact_id": "contact123",
                    "subscribed": True,
                    "opt_in_date": "2024-01-01T00:00:00Z"
                }
            }]
        )
        
        # Verify all fields were updated
        self.assertEqual(result["registrants"], 100)
        self.assertEqual(result["eventName"], "Updated Test Event")
        self.assertEqual(result["eventType"], "Conference")
        self.assertEqual(result["startDateTime"], "2024-01-01T09:00:00")
        self.assertEqual(result["endDateTime"], "2024-01-01T17:00:00")
        self.assertEqual(result["eventOrganizer"], "Updated Organizer")
        self.assertEqual(result["eventDescription"], "Updated description")
        self.assertEqual(result["eventUrl"], "https://example.com/updated")
        self.assertEqual(result["attendees"], 75)
        self.assertEqual(result["eventCompleted"], True)
        
        # Verify DB was updated
        db_event = DB["marketing_events"][self.event_id]
        self.assertEqual(db_event["registrants"], 100)
        self.assertEqual(db_event["eventName"], "Updated Test Event")
        self.assertEqual(db_event["eventType"], "Conference")

    def test_update_event_partial_update_success(self):
        """Test successful update with only some parameters."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=50,
            event_name="Partially Updated Event"
        )
        
        # Verify only specified fields were updated
        self.assertEqual(result["registrants"], 50)
        self.assertEqual(result["eventName"], "Partially Updated Event")
        # Original values should remain
        self.assertEqual(result["eventType"], "Webinar")
        self.assertEqual(result["eventOrganizer"], "Test Organizer")

    def test_update_event_zero_values_success(self):
        """Test successful update with zero values for integer fields."""
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=0,
            attendees=0
        )
        
        self.assertEqual(result["registrants"], 0)
        self.assertEqual(result["attendees"], 0)

    def test_update_event_updated_at_timestamp(self):
        """Test that updatedAt timestamp is updated on every update."""
        original_event = DB["marketing_events"][self.event_id].copy()
        
        # Update event
        result = HubspotMarketingAPI.MarketingEvents.update_event(
            externalEventId=self.event_id,
            externalAccountId=self.account_id,
            registrants=10
        )
        
        # Verify updatedAt was changed
        self.assertNotEqual(result["updatedAt"], original_event.get("updatedAt"))
        self.assertIn("updatedAt", result)




class TestFormsFieldTypeValidation(BaseTestCaseWithErrorHandler):
    """Test suite to verify fieldType validation in forms."""

    def setUp(self):
        """Clear the forms database before each test."""
        DB.update({
            "forms": {}
        })

    def test_create_form_with_email_fieldtype_should_succeed(self):
        """Test Case 1: If 'email' is passed as fieldType, it should succeed."""
        field_groups = [
            {
                "groupType": "default",
                "richTextType": "text",
                "richText": "Please provide your email",
                "fields": [
                    {
                        "fieldType": "email",
                        "name": "email_field",
                        "label": "Email Address",
                        "required": True,
                        "placeholder": "Enter your email",
                        "defaultValue": "",
                        "options": [],
                        "hidden": False
                    }
                ]
            }
        ]

        form = HubspotMarketingAPI.Forms.create_form(
            name="Email Form Test",
            submitText="Submit",
            fieldGroups=field_groups
        )

        # Assertions to verify success
        self.assertEqual(form["name"], "Email Form Test")
        self.assertEqual(form["submitText"], "Submit")
        self.assertEqual(form["fieldGroups"][0]["fields"][0]["fieldType"], "email")
        self.assertIn(form["id"], DB["forms"])

    def test_create_form_with_invalid_fieldtype_should_fail(self):
        """Test Case 2: Apart from valid fieldTypes, any invalid value should fail."""
        field_groups = [
            {
                "groupType": "default",
                "richTextType": "text",
                "richText": "Invalid field type test",
                "fields": [
                    {
                        "fieldType": "invalid_field_type",  # Invalid fieldType
                        "name": "test_field",
                        "label": "Test Field",
                        "required": True
                    }
                ]
            }
        ]

        # Assert that ValidationError is raised for invalid fieldType
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            name="Invalid FieldType Form",
            submitText="Submit",
            fieldGroups=field_groups
        )

    def test_create_form_with_multiple_values_in_fieldtype_should_fail(self):
        """Test Case 3: With multiple values like ('email', 'text') in fieldType, it should fail."""
        field_groups = [
            {
                "groupType": "default",
                "richTextType": "text",
                "richText": "Multiple values test",
                "fields": [
                    {
                        "fieldType": ("email", "text"),  # Multiple values as tuple
                        "name": "test_field",
                        "label": "Test Field",
                        "required": True
                    }
                ]
            }
        ]

        # Assert that ValidationError is raised for multiple values in fieldType
        self.assert_error_behavior(
            HubspotMarketingAPI.Forms.create_form,
            expected_exception_type=ValidationError,
            expected_message="validation error",
            name="Multiple FieldType Values Form",
            submitText="Submit",
            fieldGroups=field_groups
        )

    def test_create_form_iso8601_timestamp_format(self):
        """Test that created_at and updated_at timestamps are in valid ISO 8601 format with '+00:00' offset."""
        import re
        
        field_groups = [
            {
                "groupType": "default",
                "richTextType": "text",
                "richText": "Test Rich Text",
                "fields": [
                    {
                        "fieldType": "email",
                        "name": "email",
                        "label": "Email",
                        "required": True
                    }
                ]
            }
        ]
        
        form = HubspotMarketingAPI.Forms.create_form(
            name="ISO 8601 Test Form",
            submitText="Submit",
            fieldGroups=field_groups
        )
        
        # Verify timestamps exist
        self.assertIn("createdAt", form)
        self.assertIn("updatedAt", form)
        
        # Verify timestamps end with '+00:00' (not 'Z')
        self.assertTrue(form["createdAt"].endswith("+00:00"))
        self.assertTrue(form["updatedAt"].endswith("+00:00"))
        
        # Verify timestamps don't contain 'Z'
        self.assertNotIn("Z", form["createdAt"])
        self.assertNotIn("Z", form["updatedAt"])
        
        # Verify timestamps don't contain the malformed '+00:00Z' format
        self.assertNotIn("+00:00Z", form["createdAt"])
        self.assertNotIn("+00:00Z", form["updatedAt"])
        
        # Verify timestamps are valid ISO 8601 format
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$'
        self.assertRegex(form["createdAt"], iso8601_pattern, 
                        msg=f"createdAt is not valid ISO 8601 format: {form['createdAt']}")
        self.assertRegex(form["updatedAt"], iso8601_pattern,
                        msg=f"updatedAt is not valid ISO 8601 format: {form['updatedAt']}")
        
        # Verify initial timestamps are equal (should be when created)
        self.assertEqual(form["createdAt"], form["updatedAt"])


    def test_update_form_iso8601_timestamp_format(self):
        """Test that updated_at timestamp after update is in valid ISO 8601 format with '+00:00' offset."""
        import re
        
        # Create a form first
        field_groups = [
            {
                "groupType": "default",
                "richTextType": "text",
                "richText": "Original",
                "fields": [
                    {
                        "fieldType": "email",
                        "name": "email",
                        "label": "Email",
                        "required": True
                    }
                ]
            }
        ]
        
        form = HubspotMarketingAPI.Forms.create_form(
            name="Original Form",
            submitText="Submit",
            fieldGroups=field_groups
        )
        
        original_created_at = form["createdAt"]
        original_updated_at = form["updatedAt"]
        
        # Update the form
        new_field_groups = [
            {
                "groupType": "default",
                "richTextType": "text",
                "richText": "Updated",
                "fields": [
                    {
                        "fieldType": "email",
                        "name": "email",
                        "label": "Email Updated",
                        "required": True
                    }
                ]
            }
        ]
        
        updated_form = HubspotMarketingAPI.Forms.update_form(
            formId=form["id"],
            fieldGroups=new_field_groups
        )
        
        # Verify updated timestamp is different
        self.assertNotEqual(original_updated_at, updated_form["updatedAt"])
        
        # Verify created timestamp is unchanged
        self.assertEqual(original_created_at, updated_form["createdAt"])
        
        # Verify updated timestamp is valid ISO 8601 format with '+00:00'
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$'
        self.assertRegex(updated_form["updatedAt"], iso8601_pattern,
                        msg=f"updatedAt after update is not valid ISO 8601 format: {updated_form['updatedAt']}")
        
        # Verify updated timestamp doesn't contain the malformed '+00:00Z' format
        self.assertNotIn("+00:00Z", updated_form["updatedAt"])
        
        # Verify updated timestamp ends with '+00:00'
        self.assertTrue(updated_form["updatedAt"].endswith("+00:00"))