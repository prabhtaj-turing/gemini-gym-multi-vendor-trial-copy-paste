"""
Tests for the Apps module in Google Drive API.

This module provides tests for the get_app_details and list_installed_apps functions, covering input validation,
error handling, and core functionality.
"""
import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from gdrive.SimulationEngine.db import DB
from gdrive.SimulationEngine.utils import _ensure_user, _ensure_apps
from .. import (get_app_details, list_installed_apps)

class TestAppsGet(BaseTestCaseWithErrorHandler):
    """Test suite for the Apps.get function."""

    def setUp(self):
        """Set up a clean environment for each test."""
        # Reset DB before each test
        DB.clear()
        DB.update({
            "users": {
                "me": {
                    "about": {
                        "kind": "drive#about",
                        "storageQuota": {
                            "limit": "107374182400",
                            "usageInDrive": "0",
                            "usageInDriveTrash": "0",
                            "usage": "0",
                        },
                        "user": {"emailAddress": "me@example.com"},
                    },
                    "files": {},
                    "drives": {},
                    "comments": {},
                    "replies": {},
                    "labels": {},
                    "accessproposals": {},
                    "apps": {
                        "test_app_1": {
                            "kind": "drive#app",
                            "id": "test_app_1",
                            "name": "Test App 1",
                            "objectType": "file",
                            "supportsCreate": True,
                            "supportsImport": False,
                            "installed": True,
                            "authorized": True,
                            "useByDefault": False,
                            "productUrl": "https://example.com/app1",
                            "primaryMimeTypes": ["text/plain", "application/pdf"],
                            "secondaryMimeTypes": ["image/png"],
                            "primaryFileExtensions": ["txt", "pdf"],
                            "secondaryFileExtensions": ["png"],
                            "icons": [
                                {
                                    "category": "application",
                                    "iconUrl": "https://example.com/icon1.png",
                                    "size": 16
                                },
                                {
                                    "category": "document",
                                    "iconUrl": "https://example.com/icon2.png",
                                    "size": 32
                                }
                            ]
                        }
                    },
                    "channels": {},
                    "changes": {"startPageToken": "1", "changes": []},
                    "counters": {
                        "file": 0,
                        "drive": 0,
                        "comment": 0,
                        "reply": 0,
                        "label": 0,
                        "accessproposal": 0,
                        "revision": 0,
                        "change_token": 0,
                    },
                }
            }
        })
        # Ensure user and apps structure exists
        _ensure_user("me")
        _ensure_apps("me")

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()

    ##
    ## Success and Happy Path Tests
    ##

    def test_get_existing_app_success(self):
        """Test getting an existing app returns correct data."""
        result = get_app_details("test_app_1")
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "test_app_1")
        self.assertEqual(result["name"], "Test App 1")
        self.assertEqual(result["kind"], "drive#app")
        self.assertEqual(result["objectType"], "file")
        self.assertTrue(result["supportsCreate"])
        self.assertFalse(result["supportsImport"])
        self.assertTrue(result["installed"])
        self.assertTrue(result["authorized"])
        self.assertFalse(result["useByDefault"])
        self.assertEqual(result["productUrl"], "https://example.com/app1")
        self.assertEqual(result["primaryMimeTypes"], ["text/plain", "application/pdf"])
        self.assertEqual(result["secondaryMimeTypes"], ["image/png"])
        self.assertEqual(result["primaryFileExtensions"], ["txt", "pdf"])
        self.assertEqual(result["secondaryFileExtensions"], ["png"])
        self.assertEqual(len(result["icons"]), 2)
        self.assertEqual(result["icons"][0]["category"], "application")
        self.assertEqual(result["icons"][0]["iconUrl"], "https://example.com/icon1.png")
        self.assertEqual(result["icons"][0]["size"], 16)

    def test_get_nonexistent_app_returns_none(self):
        """Test getting a non-existent app returns None."""
        result = get_app_details("nonexistent_app")
        self.assertIsNone(result)

    def test_get_with_valid_string_variations(self):
        """Test getting apps with various valid string formats."""
        # Test with different valid app ID formats
        test_cases = ["app_123", "app-456", "app.789", "123456", "a"]
        
        for app_id in test_cases:
            # Add app to DB for testing
            DB["users"]["me"]["apps"][app_id] = {
                "id": app_id,
                "name": f"App {app_id}",
                "kind": "drive#app"
            }
            
            result = get_app_details(app_id)
            self.assertIsNotNone(result)
            self.assertEqual(result["id"], app_id)
            self.assertEqual(result["name"], f"App {app_id}")

    ##
    ## Input Validation Error Tests
    ##

    def test_get_with_none_appid_raises_typeerror(self):
        """Test that passing None as appId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_app_details,
            expected_exception_type=TypeError,
            expected_message="appId must be a string.",
            appId=None
        )

    def test_get_with_integer_appid_raises_typeerror(self):
        """Test that passing integer as appId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_app_details,
            expected_exception_type=TypeError,
            expected_message="appId must be a string.",
            appId=123
        )

    def test_get_with_list_appid_raises_typeerror(self):
        """Test that passing list as appId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_app_details,
            expected_exception_type=TypeError,
            expected_message="appId must be a string.",
            appId=["app1", "app2"]
        )

    def test_get_with_dict_appid_raises_typeerror(self):
        """Test that passing dict as appId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_app_details,
            expected_exception_type=TypeError,
            expected_message="appId must be a string.",
            appId={"id": "app1"}
        )

    def test_get_with_boolean_appid_raises_typeerror(self):
        """Test that passing boolean as appId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_app_details,
            expected_exception_type=TypeError,
            expected_message="appId must be a string.",
            appId=True
        )

    def test_get_with_float_appid_raises_typeerror(self):
        """Test that passing float as appId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_app_details,
            expected_exception_type=TypeError,
            expected_message="appId must be a string.",
            appId=3.14
        )

    def test_get_with_empty_string_raises_valueerror(self):
        """Test that passing empty string as appId raises ValueError."""
        self.assert_error_behavior(
            func_to_call=get_app_details,
            expected_exception_type=ValueError,
            expected_message="appId cannot be empty or contain only whitespace.",
            appId=""
        )

    def test_get_with_whitespace_string_raises_valueerror(self):
        """Test that passing whitespace-only string as appId raises ValueError."""
        test_cases = [" ", "  ", "\t", "\n", " \t \n "]
        
        for whitespace_appid in test_cases:
            self.assert_error_behavior(
                func_to_call=get_app_details,
                expected_exception_type=ValueError,
                expected_message="appId cannot be empty or contain only whitespace.",
                appId=whitespace_appid
            )

    ##
    ## Edge Cases and Database State Tests
    ##

    def test_get_with_empty_apps_db(self):
        """Test getting app when apps database is empty."""
        DB["users"]["me"]["apps"] = {}
        result = get_app_details("any_app")
        self.assertIsNone(result)

    def test_get_ensures_apps_structure_exists(self):
        """Test that the function ensures apps structure exists."""
        # Remove apps from user data
        del DB["users"]["me"]["apps"]
        
        # Function should create the structure and return None for non-existent app
        result = get_app_details("nonexistent_app")
        self.assertIsNone(result)
        
        # Verify apps structure was created
        self.assertIn("apps", DB["users"]["me"])
        self.assertIsInstance(DB["users"]["me"]["apps"], dict)

    def test_get_with_special_characters_in_appid(self):
        """Test getting apps with special characters in appId."""
        special_app_ids = [
            "app@example.com",
            "app+plus",
            "app_with_underscores",
            "app-with-dashes",
            "app.with.dots",
            "app:with:colons",
            "app|with|pipes",
            "app#with#hash"
        ]
        
        for app_id in special_app_ids:
            # Add app to DB
            DB["users"]["me"]["apps"][app_id] = {
                "id": app_id,
                "name": f"Special App {app_id}",
                "kind": "drive#app"
            }
            
            result = get_app_details(app_id)
            self.assertIsNotNone(result)
            self.assertEqual(result["id"], app_id)

    def test_get_app_with_minimal_fields(self):
        """Test getting an app with only minimal required fields."""
        minimal_app_id = "minimal_app"
        DB["users"]["me"]["apps"][minimal_app_id] = {
            "id": minimal_app_id,
            "kind": "drive#app"
        }
        
        result = get_app_details(minimal_app_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], minimal_app_id)
        self.assertEqual(result["kind"], "drive#app")

    def test_get_app_with_all_optional_fields(self):
        """Test getting an app with all possible fields populated."""
        complete_app_id = "complete_app"
        DB["users"]["me"]["apps"][complete_app_id] = {
            "kind": "drive#app",
            "id": complete_app_id,
            "name": "Complete Test App",
            "objectType": "file",
            "supportsCreate": True,
            "supportsImport": True,
            "installed": True,
            "authorized": True,
            "useByDefault": True,
            "productUrl": "https://example.com/complete",
            "primaryMimeTypes": ["text/plain", "application/pdf", "image/jpeg"],
            "secondaryMimeTypes": ["image/png", "text/html"],
            "primaryFileExtensions": ["txt", "pdf", "jpg"],
            "secondaryFileExtensions": ["png", "html"],
            "icons": [
                {
                    "category": "application",
                    "iconUrl": "https://example.com/icon1.png",
                    "size": 16
                },
                {
                    "category": "document", 
                    "iconUrl": "https://example.com/icon2.png",
                    "size": 32
                },
                {
                    "category": "shortcut",
                    "iconUrl": "https://example.com/icon3.png", 
                    "size": 64
                }
            ]
        }
        
        result = get_app_details(complete_app_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], complete_app_id)
        self.assertEqual(result["name"], "Complete Test App")
        self.assertEqual(result["objectType"], "file")
        self.assertTrue(result["supportsCreate"])
        self.assertTrue(result["supportsImport"])
        self.assertTrue(result["installed"])
        self.assertTrue(result["authorized"])
        self.assertTrue(result["useByDefault"])
        self.assertEqual(result["productUrl"], "https://example.com/complete")
        self.assertEqual(len(result["primaryMimeTypes"]), 3)
        self.assertEqual(len(result["secondaryMimeTypes"]), 2)
        self.assertEqual(len(result["primaryFileExtensions"]), 3)
        self.assertEqual(len(result["secondaryFileExtensions"]), 2)
        self.assertEqual(len(result["icons"]), 3)


class TestAppsList(BaseTestCaseWithErrorHandler):
    """Test suite for the Apps.list function."""

    def setUp(self):
        """Set up a clean environment for each test."""
        # Reset DB before each test
        DB.clear()
        DB.update({
            "users": {
                "me": {
                    "about": {
                        "kind": "drive#about",
                        "storageQuota": {
                            "limit": "107374182400",
                            "usageInDrive": "0",
                            "usageInDriveTrash": "0",
                            "usage": "0",
                        },
                        "user": {"emailAddress": "me@example.com"},
                    },
                    "files": {},
                    "drives": {},
                    "comments": {},
                    "replies": {},
                    "labels": {},
                    "accessproposals": {},
                    "apps": {
                        "text_editor": {
                            "kind": "drive#app",
                            "id": "text_editor",
                            "name": "Text Editor",
                            "primaryMimeTypes": ["text/plain", "text/html"],
                            "secondaryMimeTypes": ["application/rtf"],
                            "primaryFileExtensions": ["txt", "html"],
                            "secondaryFileExtensions": ["rtf"]
                        },
                        "pdf_viewer": {
                            "kind": "drive#app",
                            "id": "pdf_viewer",
                            "name": "PDF Viewer",
                            "primaryMimeTypes": ["application/pdf"],
                            "secondaryMimeTypes": [],
                            "primaryFileExtensions": ["pdf"],
                            "secondaryFileExtensions": []
                        },
                        "image_editor": {
                            "kind": "drive#app",
                            "id": "image_editor",
                            "name": "Image Editor",
                            "primaryMimeTypes": ["image/jpeg", "image/png"],
                            "secondaryMimeTypes": ["image/gif"],
                            "primaryFileExtensions": ["jpg", "jpeg", "png"],
                            "secondaryFileExtensions": ["gif"]
                        },
                        "office_suite": {
                            "kind": "drive#app",
                            "id": "office_suite",
                            "name": "Office Suite",
                            "primaryMimeTypes": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                            "secondaryMimeTypes": ["application/msword"],
                            "primaryFileExtensions": ["docx"],
                            "secondaryFileExtensions": ["doc"]
                        }
                    },
                    "channels": {},
                    "changes": {"startPageToken": "1", "changes": []},
                    "counters": {
                        "file": 0,
                        "drive": 0,
                        "comment": 0,
                        "reply": 0,
                        "label": 0,
                        "accessproposal": 0,
                        "revision": 0,
                        "change_token": 0,
                    },
                }
            }
        })
        # Ensure user and apps structure exists
        _ensure_user("me")
        _ensure_apps("me")

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()

    ##
    ## Success and Happy Path Tests
    ##

    def test_list_all_apps_no_filters(self):
        """Test listing all apps with no filters returns all apps."""
        result = list_installed_apps()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["kind"], "drive#appList")
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 4)
        
        # Verify all apps are present
        app_ids = {app["id"] for app in result["items"]}
        expected_ids = {"text_editor", "pdf_viewer", "image_editor", "office_suite"}
        self.assertEqual(app_ids, expected_ids)

    def test_list_apps_with_extension_filter(self):
        """Test filtering apps by file extensions."""
        result = list_installed_apps(appFilterExtensions="pdf")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "pdf_viewer")

    def test_list_apps_with_multiple_extension_filter(self):
        """Test filtering apps by multiple file extensions."""
        result = list_installed_apps(appFilterExtensions="txt,pdf")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 2)
        
        app_ids = {app["id"] for app in result["items"]}
        expected_ids = {"text_editor", "pdf_viewer"}
        self.assertEqual(app_ids, expected_ids)

    def test_list_apps_with_mime_type_filter(self):
        """Test filtering apps by MIME types."""
        result = list_installed_apps(appFilterMimeTypes="text/plain")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "text_editor")

    def test_list_apps_with_multiple_mime_type_filter(self):
        """Test filtering apps by multiple MIME types."""
        result = list_installed_apps(appFilterMimeTypes="text/plain,image/jpeg")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 2)
        
        app_ids = {app["id"] for app in result["items"]}
        expected_ids = {"text_editor", "image_editor"}
        self.assertEqual(app_ids, expected_ids)

    def test_list_apps_with_both_filters(self):
        """Test filtering apps by both extensions and MIME types."""
        result = list_installed_apps(appFilterExtensions="jpg", appFilterMimeTypes="image/jpeg")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "image_editor")

    def test_list_apps_case_insensitive_filtering(self):
        """Test that filtering is case insensitive."""
        result = list_installed_apps(appFilterExtensions="PDF", appFilterMimeTypes="APPLICATION/PDF")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "pdf_viewer")

    def test_list_apps_secondary_extensions_and_mimes(self):
        """Test filtering includes secondary extensions and MIME types."""
        result = list_installed_apps(appFilterExtensions="rtf")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "text_editor")

        result = list_installed_apps(appFilterMimeTypes="application/rtf")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "text_editor")

    def test_list_apps_no_matches(self):
        """Test filtering with no matches returns empty list."""
        result = list_installed_apps(appFilterExtensions="xyz")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 0)

        result = list_installed_apps(appFilterMimeTypes="application/xyz")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 0)

    def test_list_apps_with_language_code(self):
        """Test that languageCode parameter is accepted but doesn't affect results."""
        result_without = list_installed_apps()
        result_with = list_installed_apps(languageCode="en-US")
        
        self.assertEqual(result_without, result_with)

    ##
    ## Input Validation Error Tests
    ##

    def test_list_with_non_string_appfilterextensions_raises_typeerror(self):
        """Test that non-string appFilterExtensions raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=TypeError,
            expected_message="Argument 'appFilterExtensions' must be a string.",
            appFilterExtensions=123
        )

    def test_list_with_non_string_appfiltermimetypes_raises_typeerror(self):
        """Test that non-string appFilterMimeTypes raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=TypeError,
            expected_message="Argument 'appFilterMimeTypes' must be a string.",
            appFilterMimeTypes=["text/plain"]
        )

    def test_list_with_non_string_languagecode_raises_typeerror(self):
        """Test that non-string languageCode raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=TypeError,
            expected_message="Argument 'languageCode' must be a string.",
            languageCode=123
        )

    def test_list_with_empty_extension_in_filter_raises_valueerror(self):
        """Test that empty extension in filter raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=ValueError,
            expected_message="appFilterExtensions cannot contain empty extensions.",
            appFilterExtensions="pdf,,txt"
        )

    def test_list_with_invalid_extension_format_raises_valueerror(self):
        """Test that invalid extension format raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=ValueError,
            expected_message="Invalid file extension format: 'pdf@invalid'. Extensions must contain only alphanumeric characters, dots, hyphens, and underscores.",
            appFilterExtensions="pdf@invalid"
        )

    def test_list_with_empty_mime_type_in_filter_raises_valueerror(self):
        """Test that empty MIME type in filter raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=ValueError,
            expected_message="appFilterMimeTypes cannot contain empty MIME types.",
            appFilterMimeTypes="text/plain,,application/pdf"
        )

    def test_list_with_invalid_mime_type_format_raises_valueerror(self):
        """Test that invalid MIME type format raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=ValueError,
            expected_message="Invalid MIME type format: 'invalidmime'. MIME types must be in format 'type/subtype'.",
            appFilterMimeTypes="invalidmime"
        )

    def test_list_with_mime_type_multiple_slashes_raises_valueerror(self):
        """Test that MIME type with multiple slashes raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=ValueError,
            expected_message="Invalid MIME type format: 'text/plain/extra'. MIME types must be in format 'type/subtype'.",
            appFilterMimeTypes="text/plain/extra"
        )

    def test_list_with_mime_type_empty_parts_raises_valueerror(self):
        """Test that MIME type with empty parts raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=ValueError,
            expected_message="Invalid MIME type format: '/plain'. Both type and subtype must be non-empty.",
            appFilterMimeTypes="/plain"
        )

        self.assert_error_behavior(
            func_to_call=list_installed_apps,
            expected_exception_type=ValueError,
            expected_message="Invalid MIME type format: 'text/'. Both type and subtype must be non-empty.",
            appFilterMimeTypes="text/"
        )

    ##
    ## Edge Cases and Database State Tests
    ##

    def test_list_apps_with_empty_apps_db(self):
        """Test listing apps when apps database is empty."""
        DB["users"]["me"]["apps"] = {}
        result = list_installed_apps()
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 0)

    def test_list_apps_ensures_apps_structure_exists(self):
        """Test that the function ensures apps structure exists."""
        # Remove apps from user data
        del DB["users"]["me"]["apps"]
        
        # Function should create the structure and return empty list
        result = list_installed_apps()
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 0)
        
        # Verify apps structure was created
        self.assertIn("apps", DB["users"]["me"])
        self.assertIsInstance(DB["users"]["me"]["apps"], dict)

    def test_list_apps_with_missing_extension_fields(self):
        """Test filtering apps that don't have extension fields."""
        # Add app without extension fields
        DB["users"]["me"]["apps"]["minimal_app"] = {
            "kind": "drive#app",
            "id": "minimal_app",
            "name": "Minimal App"
        }
        
        result = list_installed_apps(appFilterExtensions="txt")
        
        # Should only return apps that have the requested extension
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "text_editor")

    def test_list_apps_with_missing_mime_type_fields(self):
        """Test filtering apps that don't have MIME type fields."""
        # Add app without MIME type fields
        DB["users"]["me"]["apps"]["minimal_app"] = {
            "kind": "drive#app",
            "id": "minimal_app",
            "name": "Minimal App"
        }
        
        result = list_installed_apps(appFilterMimeTypes="text/plain")
        
        # Should only return apps that have the requested MIME type
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "text_editor")

    def test_list_apps_with_whitespace_in_filters(self):
        """Test that whitespace in filters is handled correctly."""
        result = list_installed_apps(appFilterExtensions=" pdf , txt ")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 2)
        
        app_ids = {app["id"] for app in result["items"]}
        expected_ids = {"text_editor", "pdf_viewer"}
        self.assertEqual(app_ids, expected_ids)

    def test_list_apps_complex_filtering_scenario(self):
        """Test complex filtering scenario with both filters applied."""
        # This should find apps that support BOTH jpg extensions AND image/jpeg MIME type
        result = list_installed_apps(appFilterExtensions="jpg", appFilterMimeTypes="image/jpeg")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "image_editor")

    def test_list_apps_no_intersection_filters(self):
        """Test filtering where extension and MIME type filters have no intersection."""
        # Request PDF extension but text MIME type - should return no results
        result = list_installed_apps(appFilterExtensions="pdf", appFilterMimeTypes="text/plain")
        
        self.assertEqual(result["kind"], "drive#appList")
        self.assertEqual(len(result["items"]), 0)


if __name__ == "__main__":
    unittest.main() 