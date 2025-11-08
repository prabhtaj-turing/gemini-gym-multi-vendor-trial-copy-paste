import json
import os
import sys
import unittest
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tiktok.SimulationEngine.db import DB
from tiktok.SimulationEngine.utils import _add_business_account, _update_business_account
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestTikTokDBValidation(BaseTestCaseWithErrorHandler):
    """Test cases for TikTok API database structure validation."""
    
    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()
        # Clear and reset DB to known state (business accounts are top-level keys)
        DB.clear()
    
    def _validate_business_account_structure(self, account_data: Dict[str, Any]) -> List[str]:
        """
        Validate the structure of a business account entry.
        
        Args:
            account_data: The account data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required top-level fields
        required_fields = ["username", "display_name"]
        for field in required_fields:
            if field not in account_data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(account_data[field], str):
                errors.append(f"Field '{field}' must be a string")
            elif not account_data[field].strip():
                errors.append(f"Field '{field}' cannot be empty")
        
        # Optional but structured fields
        if "profile" in account_data:
            profile_errors = self._validate_profile_structure(account_data["profile"])
            errors.extend([f"profile.{error}" for error in profile_errors])
        
        if "analytics" in account_data:
            analytics_errors = self._validate_analytics_structure(account_data["analytics"])
            errors.extend([f"analytics.{error}" for error in analytics_errors])
        
        if "settings" in account_data:
            settings_errors = self._validate_settings_structure(account_data["settings"])
            errors.extend([f"settings.{error}" for error in settings_errors])
        
        return errors
    
    def _validate_profile_structure(self, profile_data: Dict[str, Any]) -> List[str]:
        """Validate profile structure."""
        errors = []
        
        if not isinstance(profile_data, dict):
            return ["profile must be a dictionary"]
        
        # Bio validation
        if "bio" in profile_data:
            if not isinstance(profile_data["bio"], str):
                errors.append("bio must be a string")
        
        # Followers count validation
        if "followers_count" in profile_data:
            if not isinstance(profile_data["followers_count"], int) or profile_data["followers_count"] < 0:
                errors.append("followers_count must be a non-negative integer")
        
        # Following count validation
        if "following_count" in profile_data:
            if not isinstance(profile_data["following_count"], int) or profile_data["following_count"] < 0:
                errors.append("following_count must be a non-negative integer")
        
        # Website validation
        if "website" in profile_data:
            if not isinstance(profile_data["website"], str):
                errors.append("website must be a string")
            elif profile_data["website"] and not (profile_data["website"].startswith("http://") or profile_data["website"].startswith("https://")):
                errors.append("website must be a valid URL starting with http:// or https://")
        
        return errors
    
    def _validate_analytics_structure(self, analytics_data: Dict[str, Any]) -> List[str]:
        """Validate analytics structure."""
        errors = []
        
        if not isinstance(analytics_data, dict):
            return ["analytics must be a dictionary"]
        
        # Numeric fields validation
        numeric_fields = ["total_likes", "total_views"]
        for field in numeric_fields:
            if field in analytics_data:
                if not isinstance(analytics_data[field], int) or analytics_data[field] < 0:
                    errors.append(f"{field} must be a non-negative integer")
        
        # Engagement rate validation
        if "engagement_rate" in analytics_data:
            rate = analytics_data["engagement_rate"]
            if not isinstance(rate, (int, float)) or rate < 0 or rate > 1:
                errors.append("engagement_rate must be a number between 0 and 1")
        
        return errors
    
    def _validate_settings_structure(self, settings_data: Dict[str, Any]) -> List[str]:
        """Validate settings structure."""
        errors = []
        
        if not isinstance(settings_data, dict):
            return ["settings must be a dictionary"]
        
        # Boolean fields validation
        boolean_fields = ["notifications_enabled", "ads_enabled"]
        for field in boolean_fields:
            if field in settings_data:
                if not isinstance(settings_data[field], bool):
                    errors.append(f"{field} must be a boolean")
        
        # Language validation
        if "language" in settings_data:
            if not isinstance(settings_data["language"], str):
                errors.append("language must be a string")
            elif len(settings_data["language"]) < 2:
                errors.append("language must be at least 2 characters long")
        
        return errors
    
    def test_default_db_structure(self):
        """Test that the default database structure matches TikTok format."""
        # In TikTok structure, business accounts are stored as top-level keys
        # This test verifies the DB can handle this structure correctly
        
        # Add a test business account in TikTok format
        test_account = {
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
        
        DB["test_account_1"] = test_account
        
        # Verify the account was stored correctly
        self.assertIn("test_account_1", DB)
        self.assertEqual(DB["test_account_1"]["username"], "test_user")
        self.assertIsInstance(DB["test_account_1"], dict)
    
    def test_valid_business_account_structure(self):
        """Test validation of valid business account structures."""
        valid_account = {
            "username": "test_user",
            "display_name": "Test User",
            "profile": {
                "bio": "Test bio",
                "followers_count": 1000,
                "following_count": 500,
                "website": "https://example.com"
            },
            "analytics": {
                "total_likes": 50000,
                "total_views": 1000000,
                "engagement_rate": 0.05
            },
            "settings": {
                "notifications_enabled": True,
                "ads_enabled": False,
                "language": "en"
            }
        }
        
        errors = self._validate_business_account_structure(valid_account)
        self.assertEqual(errors, [], f"Valid account structure failed validation: {errors}")
    
    def test_minimal_valid_business_account(self):
        """Test validation of minimal valid business account."""
        minimal_account = {
            "username": "minimal_user",
            "display_name": "Minimal User"
        }
        
        errors = self._validate_business_account_structure(minimal_account)
        self.assertEqual(errors, [], f"Minimal valid account failed validation: {errors}")
    
    def test_business_account_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        # Missing username
        account_missing_username = {
            "display_name": "Test User"
        }
        errors = self._validate_business_account_structure(account_missing_username)
        self.assertIn("Missing required field: username", errors)
        
        # Missing display_name
        account_missing_display_name = {
            "username": "test_user"
        }
        errors = self._validate_business_account_structure(account_missing_display_name)
        self.assertIn("Missing required field: display_name", errors)
        
        # Missing both
        empty_account = {}
        errors = self._validate_business_account_structure(empty_account)
        self.assertIn("Missing required field: username", errors)
        self.assertIn("Missing required field: display_name", errors)
    
    def test_business_account_invalid_field_types(self):
        """Test validation fails for invalid field types."""
        # Non-string username
        account_invalid_username = {
            "username": 123,
            "display_name": "Test User"
        }
        errors = self._validate_business_account_structure(account_invalid_username)
        self.assertIn("Field 'username' must be a string", errors)
        
        # Non-string display_name
        account_invalid_display_name = {
            "username": "test_user",
            "display_name": ["Test", "User"]
        }
        errors = self._validate_business_account_structure(account_invalid_display_name)
        self.assertIn("Field 'display_name' must be a string", errors)
    
    def test_business_account_empty_required_fields(self):
        """Test validation fails for empty required fields."""
        account_empty_username = {
            "username": "   ",
            "display_name": "Test User"
        }
        errors = self._validate_business_account_structure(account_empty_username)
        self.assertIn("Field 'username' cannot be empty", errors)
        
        account_empty_display_name = {
            "username": "test_user",
            "display_name": ""
        }
        errors = self._validate_business_account_structure(account_empty_display_name)
        self.assertIn("Field 'display_name' cannot be empty", errors)
    
    def test_profile_structure_validation(self):
        """Test profile structure validation."""
        # Valid profile
        valid_profile = {
            "bio": "Test bio",
            "followers_count": 1000,
            "following_count": 500,
            "website": "https://example.com"
        }
        errors = self._validate_profile_structure(valid_profile)
        self.assertEqual(errors, [])
        
        # Invalid bio type
        invalid_bio = {
            "bio": 123,
            "followers_count": 1000
        }
        errors = self._validate_profile_structure(invalid_bio)
        self.assertIn("bio must be a string", errors)
        
        # Invalid followers_count (negative)
        invalid_followers = {
            "bio": "Test bio",
            "followers_count": -100
        }
        errors = self._validate_profile_structure(invalid_followers)
        self.assertIn("followers_count must be a non-negative integer", errors)
        
        # Invalid website format
        invalid_website = {
            "bio": "Test bio",
            "website": "not-a-url"
        }
        errors = self._validate_profile_structure(invalid_website)
        self.assertIn("website must be a valid URL starting with http:// or https://", errors)
    
    def test_analytics_structure_validation(self):
        """Test analytics structure validation."""
        # Valid analytics
        valid_analytics = {
            "total_likes": 50000,
            "total_views": 1000000,
            "engagement_rate": 0.05
        }
        errors = self._validate_analytics_structure(valid_analytics)
        self.assertEqual(errors, [])
        
        # Invalid total_likes (negative)
        invalid_likes = {
            "total_likes": -100
        }
        errors = self._validate_analytics_structure(invalid_likes)
        self.assertIn("total_likes must be a non-negative integer", errors)
        
        # Invalid engagement_rate (> 1)
        invalid_engagement = {
            "engagement_rate": 1.5
        }
        errors = self._validate_analytics_structure(invalid_engagement)
        self.assertIn("engagement_rate must be a number between 0 and 1", errors)
        
        # Invalid engagement_rate (negative)
        negative_engagement = {
            "engagement_rate": -0.1
        }
        errors = self._validate_analytics_structure(negative_engagement)
        self.assertIn("engagement_rate must be a number between 0 and 1", errors)
    
    def test_settings_structure_validation(self):
        """Test settings structure validation."""
        # Valid settings
        valid_settings = {
            "notifications_enabled": True,
            "ads_enabled": False,
            "language": "en"
        }
        errors = self._validate_settings_structure(valid_settings)
        self.assertEqual(errors, [])
        
        # Invalid notifications_enabled type
        invalid_notifications = {
            "notifications_enabled": "true"
        }
        errors = self._validate_settings_structure(invalid_notifications)
        self.assertIn("notifications_enabled must be a boolean", errors)
        
        # Invalid language (too short)
        invalid_language = {
            "language": "e"
        }
        errors = self._validate_settings_structure(invalid_language)
        self.assertIn("language must be at least 2 characters long", errors)
    
    def test_nested_structure_validation(self):
        """Test validation of nested structures in business accounts."""
        account_with_invalid_nested = {
            "username": "test_user",
            "display_name": "Test User",
            "profile": "not a dict",  # Should be dict
            "analytics": {
                "total_likes": "not a number"  # Should be number
            },
            "settings": {
                "notifications_enabled": "not a boolean"  # Should be boolean
            }
        }
        
        errors = self._validate_business_account_structure(account_with_invalid_nested)
        
        # Check that nested validation errors are properly prefixed
        self.assertTrue(any("profile.profile must be a dictionary" in error for error in errors))
        self.assertTrue(any("analytics.total_likes must be a non-negative integer" in error for error in errors))
        self.assertTrue(any("settings.notifications_enabled must be a boolean" in error for error in errors))
    
    def test_default_db_data_from_file(self):
        """Test that default database file contains valid data structure."""
        # Load the default database file
        default_db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "DBs", "TikTokDefaultDB.json")
        
        if os.path.exists(default_db_path):
            with open(default_db_path, 'r') as f:
                default_data = json.load(f)
            
            # Validate each business account in the default data
            for account_id, account_data in default_data.items():
                errors = self._validate_business_account_structure(account_data)
                self.assertEqual(errors, [], f"Default account '{account_id}' has validation errors: {errors}")
    
    def test_db_operations_maintain_structure(self):
        """Test that database operations maintain proper structure."""
        # Test _add_business_account with TikTok structure
        valid_account = {
            "username": "new_user",
            "display_name": "New User",
            "profile": {
                "bio": "New bio", 
                "followers_count": 100,
                "following_count": 50,
                "website": "https://newuser.com"
            },
            "analytics": {
                "total_likes": 1000,
                "total_views": 20000,
                "engagement_rate": 0.05
            },
            "settings": {
                "notifications_enabled": True,
                "ads_enabled": False,
                "language": "en"
            }
        }
        
        _add_business_account("new_account", valid_account)
        
        # Validate the added account
        errors = self._validate_business_account_structure(DB["new_account"])
        self.assertEqual(errors, [], f"Added account has validation errors: {errors}")
    
    def test_edge_case_field_values(self):
        """Test validation with edge case field values."""
        # Zero values (should be valid)
        zero_values_account = {
            "username": "zero_user",
            "display_name": "Zero User",
            "profile": {
                "followers_count": 0,
                "following_count": 0
            },
            "analytics": {
                "total_likes": 0,
                "total_views": 0,
                "engagement_rate": 0.0
            }
        }
        
        errors = self._validate_business_account_structure(zero_values_account)
        self.assertEqual(errors, [], f"Zero values account failed validation: {errors}")
        
        # Maximum engagement rate (should be valid)
        max_engagement_account = {
            "username": "max_user",
            "display_name": "Max User",
            "analytics": {
                "engagement_rate": 1.0
            }
        }
        
        errors = self._validate_business_account_structure(max_engagement_account)
        self.assertEqual(errors, [], f"Max engagement rate account failed validation: {errors}")
    
    def test_unicode_and_special_characters(self):
        """Test validation with unicode and special characters."""
        unicode_account = {
            "username": "unicode_user_🎵",
            "display_name": "Unicode User 测试",
            "profile": {
                "bio": "Bio with unicode: 🌟 and émojis",
                "website": "https://example.com/path?param=value&other=true"
            }
        }
        
        errors = self._validate_business_account_structure(unicode_account)
        self.assertEqual(errors, [], f"Unicode account failed validation: {errors}")
    
    def test_large_numeric_values(self):
        """Test validation with large numeric values."""
        large_values_account = {
            "username": "viral_user",
            "display_name": "Viral User",
            "profile": {
                "followers_count": 999999999,
                "following_count": 10000
            },
            "analytics": {
                "total_likes": 2147483647,  # Max int32
                "total_views": 999999999999,  # Large number
                "engagement_rate": 0.999999
            }
        }
        
        errors = self._validate_business_account_structure(large_values_account)
        self.assertEqual(errors, [], f"Large values account failed validation: {errors}")
    
    def test_video_structure_validation(self):
        """Test basic video structure validation."""
        # Test that videos can be stored as top-level entries in TikTok format
        DB["test_video"] = {
            "title": "Test Video",
            "duration": 30,
            "tags": ["test", "demo"],
            "type": "video"  # Add type to distinguish from business accounts
        }
        
        self.assertIn("test_video", DB)
        self.assertEqual(DB["test_video"]["title"], "Test Video")
    
    def test_publish_status_structure_validation(self):
        """Test basic publish status structure validation."""
        # Test that publish status can be stored as top-level entries in TikTok format
        DB["test_publish"] = {
            "status": "published",
            "timestamp": "2024-01-01T00:00:00Z",
            "share_id": "abc123",
            "type": "publish_status"  # Add type to distinguish from business accounts
        }
        
        self.assertIn("test_publish", DB)
        self.assertEqual(DB["test_publish"]["status"], "published")
    
    def test_complex_validation_scenario(self):
        """Test validation of complex, realistic account data."""
        complex_account = {
            "username": "travel_blogger_2024",
            "display_name": "Travel Adventures 🌍",
            "profile": {
                "bio": "Exploring the world one video at a time! 📸✈️\n#travel #adventure #wanderlust",
                "followers_count": 1234567,
                "following_count": 892,
                "website": "https://travel-blog.example.com/my-journey?utm_source=tiktok"
            },
            "analytics": {
                "total_likes": 9876543,
                "total_views": 87654321,
                "engagement_rate": 0.0823
            },
            "settings": {
                "notifications_enabled": True,
                "ads_enabled": True,
                "language": "en-US"
            }
        }
        
        errors = self._validate_business_account_structure(complex_account)
        self.assertEqual(errors, [], f"Complex realistic account failed validation: {errors}")


if __name__ == "__main__":
    unittest.main()
