import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tiktok.SimulationEngine.db import DB
from tiktok.SimulationEngine.utils import (
    _add_business_account,
    _update_business_account,
    _delete_business_account
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestTikTokUtils(BaseTestCaseWithErrorHandler):
    """Test cases for TikTok API utility functions."""
    
    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()
        # Clear DB to ensure clean state for each test
        DB.clear()
    
    def test_add_business_account_success(self):
        """Test successful addition of a business account."""
        business_id = "test_account_1"
        account_data = {
            "username": "test_user",
            "display_name": "Test User",
            "profile": {
                "bio": "Test bio",
                "followers_count": 1000,
                "following_count": 100,
                "website": "https://test.com"
            },
            "analytics": {
                "total_likes": 5000,
                "total_views": 100000,
                "engagement_rate": 0.05
            },
            "settings": {
                "notifications_enabled": True,
                "ads_enabled": False,
                "language": "en"
            }
        }
        
        _add_business_account(business_id, account_data)
        
        # Verify account was added correctly
        self.assertIn(business_id, DB)
        self.assertEqual(DB[business_id], account_data)
        self.assertEqual(DB[business_id]["username"], "test_user")
        self.assertEqual(DB[business_id]["display_name"], "Test User")
    
    def test_add_business_account_minimal_data(self):
        """Test adding a business account with minimal required data."""
        business_id = "minimal_account"
        account_data = {
            "username": "minimal_user",
            "display_name": "Minimal User"
        }
        
        _add_business_account(business_id, account_data)
        
        self.assertIn(business_id, DB)
        self.assertEqual(DB[business_id], account_data)
    
    def test_add_business_account_overwrites_existing(self):
        """Test that adding an account with existing ID overwrites the previous data."""
        business_id = "overwrite_test"
        
        # Add first account
        original_data = {
            "username": "original_user",
            "display_name": "Original User"
        }
        _add_business_account(business_id, original_data)
        self.assertEqual(DB[business_id]["username"], "original_user")
        
        # Add account with same ID (should overwrite)
        new_data = {
            "username": "new_user",
            "display_name": "New User",
            "profile": {"bio": "New bio"}
        }
        _add_business_account(business_id, new_data)
        
        self.assertEqual(DB[business_id], new_data)
        self.assertEqual(DB[business_id]["username"], "new_user")
        # Verify original data is completely replaced
        self.assertNotEqual(DB[business_id], original_data)
    
    def test_add_business_account_empty_data(self):
        """Test adding a business account with empty data."""
        business_id = "empty_account"
        account_data = {}
        
        _add_business_account(business_id, account_data)
        
        self.assertIn(business_id, DB)
        self.assertEqual(DB[business_id], {})
    
    def test_add_multiple_business_accounts(self):
        """Test adding multiple business accounts."""
        accounts = {
            "account_1": {"username": "user1", "display_name": "User 1"},
            "account_2": {"username": "user2", "display_name": "User 2"},
            "account_3": {"username": "user3", "display_name": "User 3"}
        }
        
        for business_id, account_data in accounts.items():
            _add_business_account(business_id, account_data)
        
        # Verify all accounts were added
        self.assertEqual(len(DB), 3)
        for business_id, expected_data in accounts.items():
            self.assertIn(business_id, DB)
            self.assertEqual(DB[business_id], expected_data)
    
    def test_update_business_account_success(self):
        """Test successful update of an existing business account."""
        business_id = "update_test"
        
        # First add an account
        original_data = {
            "username": "original_user",
            "display_name": "Original User",
            "profile": {"bio": "Original bio", "followers_count": 1000}
        }
        _add_business_account(business_id, original_data)
        
        # Update the account
        updated_data = {
            "username": "updated_user",
            "display_name": "Updated User",
            "profile": {
                "bio": "Updated bio", 
                "followers_count": 2000,
                "following_count": 500
            },
            "analytics": {
                "total_likes": 10000,
                "total_views": 200000,
                "engagement_rate": 0.05
            }
        }
        
        _update_business_account(business_id, updated_data)
        
        # Verify the account was updated
        self.assertEqual(DB[business_id], updated_data)
        self.assertEqual(DB[business_id]["username"], "updated_user")
        self.assertEqual(DB[business_id]["profile"]["followers_count"], 2000)
    
    def test_update_business_account_not_found(self):
        """Test updating a non-existent business account raises ValueError."""
        business_id = "non_existent_account"
        account_data = {"username": "test_user", "display_name": "Test User"}
        
        with self.assertRaises(ValueError) as context:
            _update_business_account(business_id, account_data)
        
        self.assertIn("Business account with id 'non_existent_account' not found", str(context.exception))
        # Verify DB remains empty
        self.assertEqual(len(DB), 0)
    
    def test_update_business_account_partial_update(self):
        """Test updating with partial data completely replaces the account."""
        business_id = "partial_update_test"
        
        # Add account with full data
        original_data = {
            "username": "original_user",
            "display_name": "Original User",
            "profile": {"bio": "Original bio", "followers_count": 1000},
            "analytics": {"total_likes": 5000, "total_views": 100000}
        }
        _add_business_account(business_id, original_data)
        
        # Update with partial data (should completely replace)
        partial_data = {
            "username": "updated_user",
            "display_name": "Updated User"
        }
        _update_business_account(business_id, partial_data)
        
        # Verify the account is completely replaced, not merged
        self.assertEqual(DB[business_id], partial_data)
        self.assertNotIn("profile", DB[business_id])
        self.assertNotIn("analytics", DB[business_id])
    
    def test_delete_business_account_success(self):
        """Test successful deletion of a business account."""
        business_id = "delete_test"
        account_data = {
            "username": "delete_user",
            "display_name": "Delete User"
        }
        
        # Add account first
        _add_business_account(business_id, account_data)
        self.assertIn(business_id, DB)
        
        # Delete the account
        _delete_business_account(business_id)
        
        # Verify account was deleted
        self.assertNotIn(business_id, DB)
        self.assertEqual(len(DB), 0)
    
    def test_delete_business_account_not_found(self):
        """Test deleting a non-existent business account raises ValueError."""
        business_id = "non_existent_account"
        
        with self.assertRaises(ValueError) as context:
            _delete_business_account(business_id)
        
        self.assertIn("Business account with id 'non_existent_account' not found", str(context.exception))
    
    def test_delete_business_account_from_multiple(self):
        """Test deleting one account from multiple accounts."""
        accounts = {
            "account_1": {"username": "user1", "display_name": "User 1"},
            "account_2": {"username": "user2", "display_name": "User 2"},
            "account_3": {"username": "user3", "display_name": "User 3"}
        }
        
        # Add multiple accounts
        for business_id, account_data in accounts.items():
            _add_business_account(business_id, account_data)
        
        self.assertEqual(len(DB), 3)
        
        # Delete one account
        _delete_business_account("account_2")
        
        # Verify only the target account was deleted
        self.assertEqual(len(DB), 2)
        self.assertNotIn("account_2", DB)
        self.assertIn("account_1", DB)
        self.assertIn("account_3", DB)
        self.assertEqual(DB["account_1"]["username"], "user1")
        self.assertEqual(DB["account_3"]["username"], "user3")
    
    def test_delete_already_deleted_account(self):
        """Test deleting an account that was already deleted."""
        business_id = "already_deleted"
        account_data = {"username": "test_user", "display_name": "Test User"}
        
        # Add and delete account
        _add_business_account(business_id, account_data)
        _delete_business_account(business_id)
        
        # Try to delete again
        with self.assertRaises(ValueError) as context:
            _delete_business_account(business_id)
        
        self.assertIn("Business account with id 'already_deleted' not found", str(context.exception))
    
    def test_crud_operations_sequence(self):
        """Test a complete CRUD sequence (Create, Read, Update, Delete)."""
        business_id = "crud_test"
        
        # CREATE: Add account
        create_data = {
            "username": "crud_user",
            "display_name": "CRUD User",
            "profile": {"bio": "Initial bio", "followers_count": 100}
        }
        _add_business_account(business_id, create_data)
        
        # READ: Verify account exists
        self.assertIn(business_id, DB)
        self.assertEqual(DB[business_id], create_data)
        
        # UPDATE: Modify account
        update_data = {
            "username": "crud_user_updated",
            "display_name": "CRUD User Updated",
            "profile": {"bio": "Updated bio", "followers_count": 500},
            "analytics": {"total_likes": 1000, "total_views": 20000}
        }
        _update_business_account(business_id, update_data)
        
        # READ: Verify update
        self.assertEqual(DB[business_id], update_data)
        self.assertEqual(DB[business_id]["username"], "crud_user_updated")
        
        # DELETE: Remove account
        _delete_business_account(business_id)
        
        # READ: Verify deletion
        self.assertNotIn(business_id, DB)
        self.assertEqual(len(DB), 0)
    
    def test_business_id_edge_cases(self):
        """Test edge cases for business_id parameter."""
        test_cases = [
            ("normal_id", {"username": "normal", "display_name": "Normal"}),
            ("id_with_numbers_123", {"username": "numbers", "display_name": "Numbers"}),
            ("id-with-dashes", {"username": "dashes", "display_name": "Dashes"}),
            ("id_with_underscores", {"username": "underscores", "display_name": "Underscores"}),
            ("MixedCaseId", {"username": "mixed", "display_name": "Mixed Case"}),
            ("", {"username": "empty_id", "display_name": "Empty ID"}),  # Empty string ID
        ]
        
        for business_id, account_data in test_cases:
            _add_business_account(business_id, account_data)
            self.assertIn(business_id, DB)
            self.assertEqual(DB[business_id], account_data)
        
        # Test all accounts are present
        self.assertEqual(len(DB), len(test_cases))
    
    def test_account_data_types(self):
        """Test different data types in account_data."""
        business_id = "data_types_test"
        
        # Test with various data types
        complex_data = {
            "username": "complex_user",
            "display_name": "Complex User",
            "profile": {
                "bio": "Bio with unicode: 🎵 and émojis",
                "followers_count": 1234567,
                "following_count": 0,  # Zero value
                "website": "https://example.com/path?param=value",
                "verified": True,  # Boolean
                "tags": ["tag1", "tag2", "tag3"],  # List
                "metadata": {  # Nested dict
                    "creation_date": "2024-01-01",
                    "last_login": None  # None value
                }
            },
            "analytics": {
                "total_likes": 999999999,  # Large number
                "total_views": 1.5e6,  # Scientific notation
                "engagement_rate": 0.0523  # Float
            }
        }
        
        _add_business_account(business_id, complex_data)
        
        # Verify all data types are preserved
        self.assertEqual(DB[business_id], complex_data)
        self.assertIsInstance(DB[business_id]["profile"]["verified"], bool)
        self.assertIsInstance(DB[business_id]["profile"]["tags"], list)
        self.assertIsInstance(DB[business_id]["analytics"]["engagement_rate"], float)
        self.assertIsNone(DB[business_id]["profile"]["metadata"]["last_login"])
    
    def test_concurrent_operations_simulation(self):
        """Test rapid successive operations (simulating concurrent access)."""
        base_id = "concurrent_test"
        
        # Rapid add/update/delete operations
        for i in range(10):
            business_id = f"{base_id}_{i}"
            
            # Add
            account_data = {
                "username": f"user_{i}",
                "display_name": f"User {i}"
            }
            _add_business_account(business_id, account_data)
            self.assertIn(business_id, DB)
            
            # Update
            updated_data = {
                "username": f"updated_user_{i}",
                "display_name": f"Updated User {i}",
                "profile": {"followers_count": i * 100}
            }
            _update_business_account(business_id, updated_data)
            self.assertEqual(DB[business_id]["username"], f"updated_user_{i}")
            
            # Delete every other account
            if i % 2 == 0:
                _delete_business_account(business_id)
                self.assertNotIn(business_id, DB)
        
        # Verify final state
        remaining_accounts = [key for key in DB.keys() if key.startswith(base_id)]
        self.assertEqual(len(remaining_accounts), 5)  # Should have 5 odd-numbered accounts left
    
    def test_error_messages_accuracy(self):
        """Test that error messages contain accurate information."""
        test_ids = ["test_account_1", "another_test", "special-chars_123"]
        
        for business_id in test_ids:
            # Test update error message
            with self.assertRaises(ValueError) as context:
                _update_business_account(business_id, {"username": "test"})
            
            self.assertIn(f"Business account with id '{business_id}' not found", str(context.exception))
            
            # Test delete error message
            with self.assertRaises(ValueError) as context:
                _delete_business_account(business_id)
            
            self.assertIn(f"Business account with id '{business_id}' not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
