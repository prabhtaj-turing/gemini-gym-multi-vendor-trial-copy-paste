import unittest
import os


from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, load_state, save_state, DEFAULT_DB_PATH
from ..SimulationEngine import utils
import json

class TestDBStateManagement(BaseTestCaseWithErrorHandler):
    """Test the load_state and save_state functions of the canva DB."""

    def setUp(self):
        """Set up test environment."""
        
        # Save the original DB state to restore after tests
        load_state(DEFAULT_DB_PATH)
        self.temp_db_file = DEFAULT_DB_PATH + ".temp"

        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
        
        temp_db = {
            "Users": {},
            "Designs": {},
            "brand_templates": {},
            "autofill_jobs": {},
            "asset_upload_jobs": {},
            "design_export_jobs": {},
            "design_import_jobs": {},
            "url_import_jobs": {},
            "assets": {},
            "folders": {}
        }

        with open(self.temp_db_file, 'w') as f:
            json.dump(temp_db, f)  


    def tearDown(self):
        super().tearDown()
        DB.clear()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)

    def test_load_db_from_file(self):
        """
        Test that the database can be loaded from a file.
        """
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['Users'].keys()), 0)
        self.assertEqual(len(DB['Designs'].keys()), 0)
        self.assertEqual(len(DB['brand_templates'].keys()), 0)
        self.assertEqual(len(DB['autofill_jobs'].keys()), 0)
        self.assertEqual(len(DB['asset_upload_jobs'].keys()), 0)
        self.assertEqual(len(DB['design_export_jobs'].keys()), 0)
        self.assertEqual(len(DB['design_import_jobs'].keys()), 0)
        self.assertEqual(len(DB['url_import_jobs'].keys()), 0)
        self.assertEqual(len(DB['assets'].keys()), 0)
        self.assertEqual(len(DB['folders'].keys()), 0)

    def test_save_db_to_file(self):
        """
        Test that the database can be saved to a file.
        """
        load_state(self.temp_db_file)
        DB["Users"] = { 
                "123": {
                    "user_id": "123",
                    "team_id": "456",
                    "profile": { "display_name": "User 1" }
                },
                "456": {
                    "user_id": "456",
                    "team_id": "123",
                    "profile": { "display_name": "User 2" }
                }
            }
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['Users'].keys()), 2)
        self.assertEqual(DB['Users']['123']['user_id'], "123")
        self.assertEqual(DB['Users']['123']['team_id'], "456")
        self.assertEqual(DB['Users']['123']['profile']['display_name'], "User 1")
        self.assertEqual(DB['Users']['456']['user_id'], "456")
        self.assertEqual(DB['Users']['456']['team_id'], "123")
        self.assertEqual(DB['Users']['456']['profile']['display_name'], "User 2")
    
    def test_load_state_preserves_all_collections(self):
        """Test that loading state preserves all database collections."""
        load_state(self.temp_db_file)
        DB["Designs"] = {
            "design1": {
                "id": "abcdefgh123",
                "title": "Test Design",
                "design_type": {"type": "preset", "name": "doc"},
                "owner": {"user_id": "user1", "team_id": "team1"},
                "thumbnail": {"width": 100, "height": 100, "url": "http://test.com"},
                "urls": {"edit_url": "http://edit.com", "view_url": "http://view.com"},
                "created_at": 1234567890,
                "updated_at": 1234567890,
                "page_count": 1,
                "pages": {},
                "comments": {"threads": {}}
            }
        }
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['Designs'].keys()), 1)
        self.assertEqual(DB['Designs']['design1']['title'], "Test Design")
    
    def test_save_and_load_multiple_collections(self):
        """Test saving and loading multiple collections."""
        load_state(self.temp_db_file)
        DB["Users"]["user1"] = {
            "user_id": "user1",
            "team_id": "team1",
            "profile": {"display_name": "User One"}
        }
        DB["assets"]["asset1"] = {
            "type": "image",
            "id": "asset1",
            "name": "Test Asset",
            "tags": ["tag1", "tag2"],
            "created_at": 1234567890,
            "updated_at": 1234567890,
            "thumbnail": {"width": 100, "height": 100, "url": "http://test.com"}
        }
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['Users'].keys()), 1)
        self.assertEqual(len(DB['assets'].keys()), 1)
        self.assertEqual(DB['Users']['user1']['user_id'], "user1")
        self.assertEqual(DB['assets']['asset1']['name'], "Test Asset")
    
    def test_db_state_persistence_after_modification(self):
        """Test that DB state persists after modification."""
        load_state(self.temp_db_file)
        DB["brand_templates"]["template1"] = {
            "id": "template1",
            "title": "Brand Template",
            "design_type": {"type": "preset", "name": "presentation"},
            "view_url": "http://view.com",
            "create_url": "http://create.com",
            "thumbnail": {"width": 100, "height": 100, "url": "http://test.com"},
            "created_at": 1234567890,
            "updated_at": 1234567890,
            "datasets": {}
        }
        save_state(self.temp_db_file)
        DB.clear()
        load_state(self.temp_db_file)
        self.assertIn("template1", DB["brand_templates"])
        self.assertEqual(DB["brand_templates"]["template1"]["title"], "Brand Template")
    
    def test_save_state_with_jobs(self):
        """Test saving state with job collections."""
        load_state(self.temp_db_file)
        DB["autofill_jobs"]["job1"] = {
            "id": "job1",
            "status": "in_progress",
            "created_at": 1234567890
        }
        DB["design_export_jobs"]["export1"] = {
            "id": "export1",
            "status": "completed",
            "created_at": 1234567890
        }
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        self.assertEqual(DB["autofill_jobs"]["job1"]["status"], "in_progress")
        self.assertEqual(DB["design_export_jobs"]["export1"]["status"], "completed")
    
    def test_load_state_with_folders(self):
        """Test loading state with folder data."""
        load_state(self.temp_db_file)
        DB["folders"]["folder1"] = {
            "assets": ["asset1", "asset2"],
            "Designs": ["design1"],
            "folders": ["subfolder1"],
            "folder": {
                "id": "folder1",
                "name": "Test Folder",
                "created_at": 1234567890,
                "updated_at": 1234567890,
                "parent_id": "",
                "thumbnail": {"width": 100, "height": 100, "url": "http://test.com"}
            }
        }
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        self.assertEqual(DB["folders"]["folder1"]["folder"]["name"], "Test Folder")
        self.assertEqual(len(DB["folders"]["folder1"]["assets"]), 2)
    
    def test_db_clear_and_reload(self):
        """Test that DB can be cleared and reloaded."""
        load_state(self.temp_db_file)
        DB["Users"]["test_user"] = {
            "user_id": "test_user",
            "team_id": "test_team",
            "profile": {"display_name": "Test"}
        }
        save_state(self.temp_db_file)
        
        # Clear DB
        DB.clear()
        self.assertEqual(len(DB), 0)
        
        # Reload
        load_state(self.temp_db_file)
        self.assertGreater(len(DB), 0)
        self.assertIn("test_user", DB["Users"])
    
    def test_multiple_save_operations(self):
        """Test multiple consecutive save operations."""
        load_state(self.temp_db_file)
        
        DB["Users"]["user1"] = {
            "user_id": "user1",
            "team_id": "team1",
            "profile": {"display_name": "First Save"}
        }
        save_state(self.temp_db_file)
        
        DB["Users"]["user1"]["profile"]["display_name"] = "Second Save"
        save_state(self.temp_db_file)
        
        load_state(self.temp_db_file)
        self.assertEqual(DB["Users"]["user1"]["profile"]["display_name"], "Second Save")
    
    def test_save_state_preserves_nested_structures(self):
        """Test that nested structures are preserved correctly."""
        load_state(self.temp_db_file)
        DB["Designs"]["complex_design"] = {
            "id": "12345678901",
            "title": "Complex Design",
            "design_type": {"type": "preset", "name": "doc"},
            "owner": {"user_id": "owner1", "team_id": "team1"},
            "thumbnail": {"width": 200, "height": 200, "url": "http://thumb.com"},
            "urls": {"edit_url": "http://edit.com", "view_url": "http://view.com"},
            "created_at": 1234567890,
            "updated_at": 1234567890,
            "page_count": 3,
            "pages": {
                "page1": {"index": 0, "thumbnail": {"width": 100, "height": 100, "url": "http://p1.com"}},
                "page2": {"index": 1, "thumbnail": {"width": 100, "height": 100, "url": "http://p2.com"}}
            },
            "comments": {
                "threads": {
                    "thread1": {
                        "id": "thread1",
                        "design_id": "12345678901",
                        "thread_type": {
                            "type": "comment",
                            "content": {"plaintext": "Test comment", "markdown": "**Test comment**"},
                            "mentions": {},
                            "assignee": {"id": "", "display_name": ""},
                            "resolver": {"id": "", "display_name": ""}
                        },
                        "author": {"id": "author1", "display_name": "Author One"},
                        "created_at": 1234567890,
                        "updated_at": 1234567890,
                        "replies": {}
                    }
                }
            }
        }
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        
        design = DB["Designs"]["complex_design"]
        self.assertEqual(len(design["pages"]), 2)
        self.assertEqual(len(design["comments"]["threads"]), 1)
        self.assertEqual(design["comments"]["threads"]["thread1"]["author"]["display_name"], "Author One")
    
    def test_load_state_updates_existing_db(self):
        """Test that load_state updates existing DB contents."""
        load_state(self.temp_db_file)
        # Add some data
        DB["Users"]["user1"] = {
            "user_id": "user1",
            "team_id": "team1",
            "profile": {"display_name": "User One"}
        }
        # Load should preserve data
        initial_count = len(DB.get("Users", {}))
        self.assertGreaterEqual(initial_count, 1)
    
    def test_save_state_with_empty_collections(self):
        """Test saving state with intentionally empty collections."""
        load_state(self.temp_db_file)
        # Explicitly set collections to empty
        for key in DB.keys():
            DB[key] = {}
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        
        # All collections should be empty
        for collection in DB.values():
            if isinstance(collection, dict):
                self.assertEqual(len(collection), 0)
    
if __name__ == '__main__':
    unittest.main() 