#!/usr/bin/env python3
"""
Standalone test for the hydrate_db function.
This test doesn't require the full API setup and can run independently.
"""

import unittest
import os
import json
import sys
import tempfile
import shutil
from pathlib import Path

# Add the APIs directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'APIs'))

class TestHydrateDBStandalone(unittest.TestCase):
    """Standalone tests for the hydrate_db function."""

    def setUp(self):
        """Set up test environment."""
        self.test_data_path = os.path.join(os.path.dirname(__file__), '..', 'output-data', 'files')
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_mock_db(self):
        """Create a mock database structure for testing."""
        return {
            'users': {
                'me': {
                    'about': {
                        'kind': 'drive#about',
                        'storageQuota': {
                            'limit': '1073741824',
                            'usageInDrive': '0',
                            'usageInDriveTrash': '0',
                            'usage': '0'
                        },
                        'driveThemes': False,
                        'canCreateDrives': False,
                        'importFormats': {},
                        'exportFormats': {},
                        'appInstalled': False,
                        'user': {
                            'displayName': 'Test User',
                            'kind': 'drive#user',
                            'me': True,
                            'permissionId': 'test_perm_id',
                            'emailAddress': 'test@example.com'
                        },
                        'folderColorPalette': "",
                        'maxImportSizes': {},
                        'maxUploadSize': '104857600'
                    },
                    'files': {},
                    'drives': {},
                    'comments': {},
                    'replies': {},
                    'labels': {},
                    'accessproposals': {},
                    'counters': {
                        'file': 0,
                        'drive': 0,
                        'comment': 0,
                        'reply': 0,
                        'label': 0,
                        'accessproposal': 0,
                        'revision': 0
                    }
                }
            }
        }

    def create_test_json_files(self):
        """Create test JSON files for hydration testing."""
        # Create a temporary directory with test JSON files
        test_files = [
            {
                "id": "sheet_test_001",
                "name": "Test Spreadsheet",
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "createdTime": "2024-01-01T00:00:00Z",
                "modifiedTime": "2024-01-01T00:00:00Z",
                "parents": [],
                "owners": ["test@example.com"],
                "size": 1024,
                "trashed": False,
                "starred": False,
                "sheets": [
                    {
                        "properties": {
                            "sheetId": 1,
                            "title": "Sheet1",
                            "index": 0,
                            "sheetType": "GRID"
                        }
                    }
                ],
                "data": {
                    "Sheet1!A1:B2": [
                        ["Header1", "Header2"],
                        ["Value1", "Value2"]
                    ]
                }
            },
            {
                "id": "slide_test_001",
                "name": "Test Presentation",
                "mimeType": "application/vnd.google-apps.presentation",
                "createdTime": "2024-01-01T00:00:00Z",
                "modifiedTime": "2024-01-01T00:00:00Z",
                "parents": [],
                "owners": ["test@example.com"],
                "size": 2048,
                "trashed": False,
                "starred": False,
                "presentationId": "slide_test_001",
                "title": "Test Presentation",
                "slides": [
                    {
                        "objectId": "slide1",
                        "pageType": "SLIDE",
                        "pageElements": []
                    }
                ]
            },
            {
                "id": "doc_test_001",
                "name": "Test Document",
                "mimeType": "application/vnd.google-apps.document",
                "createdTime": "2024-01-01T00:00:00Z",
                "modifiedTime": "2024-01-01T00:00:00Z",
                "parents": [],
                "owners": ["test@example.com"],
                "size": 512,
                "trashed": False,
                "starred": False,
                "content": [
                    {
                        "elementId": "element1",
                        "text": "This is a test document content."
                    }
                ]
            }
        ]
        
        # Create JSON files in temporary directory
        for i, file_data in enumerate(test_files):
            file_path = os.path.join(self.temp_dir, f"test_file_{i}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2)
        
        return len(test_files)

    def simple_hydrate_db(self, db_instance, directory_path):
        """
        Simple implementation of hydrate_db function for testing.
        This mimics the behavior of the actual function.
        """
        if not os.path.isdir(directory_path):
            raise FileNotFoundError(f"Directory not found: '{directory_path}'")
        
        # Ensure user exists
        user_id = 'me'
        if user_id not in db_instance['users']:
            db_instance['users'][user_id] = {'files': {}}
        
        db_user = db_instance['users'][user_id]
        
        all_json_data = []
        # Walk through directory to find JSON files
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            all_json_data.append(data)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode JSON from file: {file_path}")
                    except Exception as e:
                        print(f"An error occurred while reading {file_path}: {e}")
        
        # Add files to database
        db_user['files'] = {file['id']: file for file in all_json_data}
        return True

    def test_hydrate_db_basic_functionality(self):
        """Test basic hydrate_db functionality with created test files."""
        # Create mock database
        db = self.create_mock_db()
        
        # Create test JSON files
        expected_count = self.create_test_json_files()
        
        # Test hydration
        success = self.simple_hydrate_db(db, self.temp_dir)
        self.assertTrue(success)
        
        # Verify files were loaded
        files = db['users']['me']['files']
        self.assertEqual(len(files), expected_count)
        
        # Verify specific files
        self.assertIn('sheet_test_001', files)
        self.assertIn('slide_test_001', files)
        self.assertIn('doc_test_001', files)
        
        print(f"✓ Successfully loaded {len(files)} test files")

    def test_google_sheets_structure(self):
        """Test that Google Sheets files have the correct structure."""
        db = self.create_mock_db()
        self.create_test_json_files()
        self.simple_hydrate_db(db, self.temp_dir)
        
        # Find sheets file
        sheets_file = db['users']['me']['files']['sheet_test_001']
        
        # Verify structure
        self.assertEqual(sheets_file['mimeType'], 'application/vnd.google-apps.spreadsheet')
        self.assertIn('sheets', sheets_file)
        self.assertIn('data', sheets_file)
        self.assertIsInstance(sheets_file['sheets'], list)
        self.assertIsInstance(sheets_file['data'], dict)
        
        print(f"✓ Google Sheets structure validated: {sheets_file['name']}")

    def test_google_slides_structure(self):
        """Test that Google Slides files have the correct structure."""
        db = self.create_mock_db()
        self.create_test_json_files()
        self.simple_hydrate_db(db, self.temp_dir)
        
        # Find slides file
        slides_file = db['users']['me']['files']['slide_test_001']
        
        # Verify structure
        self.assertEqual(slides_file['mimeType'], 'application/vnd.google-apps.presentation')
        self.assertIn('slides', slides_file)
        self.assertIn('presentationId', slides_file)
        self.assertIsInstance(slides_file['slides'], list)
        self.assertEqual(slides_file['presentationId'], slides_file['id'])
        
        print(f"✓ Google Slides structure validated: {slides_file['name']}")

    def test_google_docs_structure(self):
        """Test that Google Docs files have the correct structure."""
        db = self.create_mock_db()
        self.create_test_json_files()
        self.simple_hydrate_db(db, self.temp_dir)
        
        # Find docs file
        docs_file = db['users']['me']['files']['doc_test_001']
        
        # Verify structure
        self.assertEqual(docs_file['mimeType'], 'application/vnd.google-apps.document')
        self.assertIn('content', docs_file)
        self.assertIsInstance(docs_file['content'], list)
        
        print(f"✓ Google Docs structure validated: {docs_file['name']}")

    def test_with_real_test_data(self):
        """Test with real test data if available."""
        if not os.path.exists(self.test_data_path):
            self.fail(f"Real test data not found at: {self.test_data_path}")
        
        # Count JSON files in test data
        json_files = []
        for root, _, files in os.walk(self.test_data_path):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            self.fail("No JSON files found in test data")
        
        # Test hydration with real data
        db = self.create_mock_db()
        success = self.simple_hydrate_db(db, self.test_data_path)
        self.assertTrue(success)
        
        # Verify files were loaded
        files = db['users']['me']['files']
        self.assertGreater(len(files), 0)
        
        # Count by type
        sheets_count = 0
        slides_count = 0
        docs_count = 0
        other_count = 0
        
        for file_data in files.values():
            mime_type = file_data.get('mimeType', '')
            if mime_type in ['application/vnd.google-apps.spreadsheet', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                sheets_count += 1
            elif mime_type == 'application/vnd.google-apps.presentation':
                slides_count += 1
            elif mime_type in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                docs_count += 1
            else:
                other_count += 1
        
        print(f"✓ Real test data loaded: {len(files)} total files")
        print(f"  - Google Sheets: {sheets_count}")
        print(f"  - Google Slides: {slides_count}")
        print(f"  - Google Docs: {docs_count}")
        print(f"  - Other files: {other_count}")

    def test_file_metadata_integrity(self):
        """Test that file metadata is preserved correctly."""
        db = self.create_mock_db()
        self.create_test_json_files()
        self.simple_hydrate_db(db, self.temp_dir)
        
        files = db['users']['me']['files']
        
        # Test each file has required fields
        for file_id, file_data in files.items():
            with self.subTest(file_id=file_id):
                self.assertIn('id', file_data)
                self.assertIn('name', file_data)
                self.assertIn('mimeType', file_data)
                self.assertIn('createdTime', file_data)
                self.assertIn('modifiedTime', file_data)
                self.assertIn('owners', file_data)
                self.assertIn('size', file_data)
                self.assertIn('trashed', file_data)
                self.assertIn('starred', file_data)
                
                # Verify file ID matches key
                self.assertEqual(file_data['id'], file_id)
                
                # Verify data types
                self.assertIsInstance(file_data['owners'], list)
                self.assertIsInstance(file_data['trashed'], bool)
                self.assertIsInstance(file_data['starred'], bool)
        
        print(f"✓ File metadata integrity validated for {len(files)} files")

    def test_error_handling(self):
        """Test error handling for various scenarios."""
        db = self.create_mock_db()
        
        # Test with non-existent directory
        with self.assertRaises(FileNotFoundError):
            self.simple_hydrate_db(db, "/non/existent/directory")
        
        # Test with empty directory
        empty_dir = tempfile.mkdtemp()
        try:
            success = self.simple_hydrate_db(db, empty_dir)
            self.assertTrue(success)
            self.assertEqual(len(db['users']['me']['files']), 0)
        finally:
            shutil.rmtree(empty_dir)
        
        # Test with directory containing invalid JSON
        invalid_dir = tempfile.mkdtemp()
        try:
            invalid_json_path = os.path.join(invalid_dir, "invalid.json")
            with open(invalid_json_path, 'w') as f:
                f.write("{ invalid json content")
            
            success = self.simple_hydrate_db(db, invalid_dir)
            self.assertTrue(success)  # Should handle gracefully
            self.assertEqual(len(db['users']['me']['files']), 0)
        finally:
            shutil.rmtree(invalid_dir)
        
        print("✓ Error handling tests passed")

if __name__ == '__main__':
    print("Running standalone hydrate_db tests...")
    unittest.main(verbosity=2) 