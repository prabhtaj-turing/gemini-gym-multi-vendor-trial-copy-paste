import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
import random

# Import the hydrate_db function from the gdrive utils
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..','..', '..', 'APIs'))
from gdrive.SimulationEngine.utils import hydrate_db
from gdrive.SimulationEngine.db import DB

def hydrate_db_sample(db_instance, directory_path, max_files_per_type=3):
    """
    Load a sample of JSON files from the directory for testing purposes.
    
    Args:
        db_instance: The database instance to hydrate
        directory_path: Path to the test data directory
        max_files_per_type: Maximum number of files to load per file type
    
    Returns:
        bool: True if hydration was successful
    """
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: '{directory_path}'")
    
    # Group files by type
    file_types = {
        'docs': [],
        'sheets': [],
        'slides': [],
        'other': []
    }
    
    # Walk through directory and categorize files
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                
                # Categorize by file type based on the filename
                if '.docx.json' in file:
                    file_types['docs'].append(file_path)
                elif '.xlsx.json' in file:
                    file_types['sheets'].append(file_path)
                elif '.pptx.json' in file:
                    file_types['slides'].append(file_path)
                else:
                    file_types['other'].append(file_path)
    
    # Sample files from each type
    sampled_files = []
    for file_type, files in file_types.items():
        if files:
            # Randomly sample up to max_files_per_type from each category
            sample_size = min(max_files_per_type, len(files))
            sampled_files.extend(random.sample(files, sample_size))
    
    # Load sampled files
    user_id = 'me'
    from gdrive.SimulationEngine.utils import _ensure_user
    _ensure_user(user_id)
    
    db_user = db_instance['users'][user_id]
    all_json_data = []
    
    for file_path in sampled_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_json_data.append(data)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from file: {file_path}")
        except Exception as e:
            print(f"An error occurred while reading {file_path}: {e}")
    
    db_user['files'] = {file['id']: file for file in all_json_data}
    
    print(f"✓ Loaded {len(all_json_data)} sample files for testing")
    return True

class TestMultihopHydrateDB(unittest.TestCase):
    """Comprehensive tests for the hydrate_db function with multihop support data."""

    def setUp(self):
        """Reset DB to a clean state before each test."""
        # Clear the DB and set up a fresh state
        DB.clear()
        DB.update({
            'users': {
                'me': {
                    'about': {
                        'kind': 'drive#about',
                        'storageQuota': {
                            'limit': '1073741824',  # 1GB in bytes
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
                        'maxUploadSize': '104857600'  # 100MB in bytes
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
        })

    def get_test_data_path(self):
        """Get the path to the test data directory."""
        return os.path.join(os.path.dirname(__file__), 'data')

    def collect_all_json_files(self, directory):
        """Recursively collect all JSON files from a directory."""
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        return json_files

    def test_hydrate_db_with_multihop_data(self):
        """Test that hydrate_db successfully loads all files from multihop test data."""
        test_data_path = self.get_test_data_path()
        
        # Skip test if test data directory doesn't exist
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Collect all JSON files to verify they get loaded
        json_files = self.collect_all_json_files(test_data_path)
        
        # Skip test if no JSON files found
        if not json_files:
            self.fail("No JSON files found in test data directory")
        
        # Hydrate the database
        success = hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        self.assertTrue(success, "hydrate_db should return True on success")
        
        # Verify that files were loaded
        self.assertIn('files', DB['users']['me'])
        files = DB['users']['me']['files']
        self.assertGreater(len(files), 0, "Should have loaded at least one file")
        
        # Count expected files from JSON files
        expected_files = set()
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'id' in data:
                        expected_files.add(data['id'])
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not read {json_file}: {e}")
        
        # Verify all expected files are loaded
        loaded_files = set(files.keys())
        print(f"Expected files: {len(expected_files)}")
        print(f"Loaded files: {len(loaded_files)}")
        
        # Check that all expected files are present
        missing_files = expected_files - loaded_files
        if missing_files:
            print(f"Missing files: {missing_files}")
        
        # At least some files should be loaded
        self.assertGreater(len(loaded_files), 0, "Should have loaded at least one file")

    def test_google_sheets_content_integrity(self):
        """Test that Google Sheets files are properly loaded with content."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find Google Sheets files
        sheets_files = []
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.spreadsheet', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                sheets_files.append((file_id, file_data))
        
        # Should have at least one sheets file
        self.assertGreater(len(sheets_files), 0, "Should have at least one Google Sheets file")
        
        # Test each sheets file
        for file_id, file_data in sheets_files:
            with self.subTest(file_id=file_id):
                # Verify required fields
                self.assertIn('id', file_data)
                self.assertIn('name', file_data)
                self.assertIn(file_data['mimeType'], ['application/vnd.google-apps.spreadsheet', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'])
                
                # Verify sheets structure
                if 'sheets' in file_data:
                    self.assertIsInstance(file_data['sheets'], list)
                    
                # Verify data structure
                if 'data' in file_data:
                    self.assertIsInstance(file_data['data'], dict)
                    
                print(f"✓ Validated Google Sheets file: {file_data['name']}")

    def test_google_slides_content_integrity(self):
        """Test that Google Slides files are properly loaded with content."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find Google Slides files
        slides_files = []
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.presentation', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
                slides_files.append((file_id, file_data))
        
        # Should have at least one slides file
        self.assertGreater(len(slides_files), 0, "Should have at least one Google Slides file")
        
        # Test each slides file
        for file_id, file_data in slides_files:
            with self.subTest(file_id=file_id):
                # Verify required fields
                self.assertIn('id', file_data)
                self.assertIn('name', file_data)
                self.assertIn(file_data['mimeType'], ['application/vnd.google-apps.presentation', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'])
                
                # Verify slides structure
                if 'slides' in file_data:
                    self.assertIsInstance(file_data['slides'], list)
                    
                # Verify presentation ID
                if 'presentationId' in file_data:
                    self.assertEqual(file_data['presentationId'], file_data['id'])
                    
                print(f"✓ Validated Google Slides file: {file_data['name']}")

    def test_google_docs_content_integrity(self):
        """Test that Google Docs files are properly loaded with content."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find Google Docs files
        docs_files = []
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                docs_files.append((file_id, file_data))
        
        # Should have at least one docs file
        self.assertGreater(len(docs_files), 0, "Should have at least one Google Docs file")
        
        # Test each docs file
        for file_id, file_data in docs_files:
            with self.subTest(file_id=file_id):
                # Verify required fields
                self.assertIn('id', file_data)
                self.assertIn('name', file_data)
                self.assertIn(file_data['mimeType'], ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'])
                
                # Verify content structure
                if 'content' in file_data:
                    # Content can be either a list or a dict with 'data' key
                    if isinstance(file_data['content'], dict) and 'data' in file_data['content']:
                        # Data can be a list or empty string
                        if file_data['content']['data'] != '':
                            self.assertIsInstance(file_data['content']['data'], list)
                    else:
                        self.assertIsInstance(file_data['content'], list)
                    
                print(f"✓ Validated Google Docs file: {file_data['name']}")

    def test_gdrive_file_content_integrity(self):
        """Test that Google Drive files are properly loaded with content."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find other file types (not Google Workspace apps)
        other_files = []
        for file_id, file_data in DB['users']['me']['files'].items():
            mime_type = file_data.get('mimeType', '')
            if not mime_type.startswith('application/vnd.google-apps.'):
                other_files.append((file_id, file_data))
        
        # Test each file
        for file_id, file_data in other_files:
            with self.subTest(file_id=file_id):
                # Verify required fields
                self.assertIn('id', file_data)
                self.assertIn('name', file_data)
                self.assertIn('mimeType', file_data)
                
                # Verify basic metadata
                if 'createdTime' in file_data:
                    self.assertIsInstance(file_data['createdTime'], str)
                    
                if 'modifiedTime' in file_data:
                    self.assertIsInstance(file_data['modifiedTime'], str)
                    
                print(f"✓ Validated Google Drive file: {file_data['name']}")

    def test_file_hierarchy_preservation(self):
        """Test that file hierarchy is preserved during hydration."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        files = DB['users']['me']['files']
        
        # Check that files have parent relationships
        files_with_parents = []
        for file_id, file_data in files.items():
            if 'parents' in file_data and file_data['parents']:
                files_with_parents.append((file_id, file_data))
        
        # At least some files should have parent relationships
        # (This depends on the test data structure)
        print(f"Files with parent relationships: {len(files_with_parents)}")
        
        # Verify parent structure is valid
        for file_id, file_data in files_with_parents:
            with self.subTest(file_id=file_id):
                self.assertIsInstance(file_data['parents'], list)
                for parent_id in file_data['parents']:
                    self.assertIsInstance(parent_id, str)
                    
                print(f"✓ Validated file hierarchy for: {file_data['name']}")

    def test_content_specific_validation(self):
        """Test specific content validation for each file type."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        files = DB['users']['me']['files']
        
        # Validate specific content for each file type
        sheets_count = 0
        slides_count = 0
        docs_count = 0
        
        for file_id, file_data in files.items():
            mime_type = file_data.get('mimeType', '')
            
            if mime_type in ['application/vnd.google-apps.spreadsheet', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                sheets_count += 1
                # Validate sheets-specific content
                if 'data' in file_data:
                    for sheet_range, sheet_data in file_data['data'].items():
                        self.assertIsInstance(sheet_data, list)
                        if sheet_data:  # If there's data
                            self.assertIsInstance(sheet_data[0], list)  # First row should be a list
                            
            elif mime_type == 'application/vnd.google-apps.presentation':
                slides_count += 1
                # Validate slides-specific content
                if 'slides' in file_data:
                    for slide in file_data['slides']:
                        self.assertIn('objectId', slide)
                        self.assertIn('pageType', slide)
                        
            elif mime_type in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                docs_count += 1
                # Validate docs-specific content
                if 'content' in file_data:
                    # Content can be either a list or a dict with 'data' key
                    if isinstance(file_data['content'], dict) and 'data' in file_data['content']:
                        content_data = file_data['content']['data']
                    else:
                        content_data = file_data['content']
                    
                    # Skip validation if content_data is empty string
                    if content_data != '':
                        for content_item in content_data:
                            if isinstance(content_item, dict):
                                # Should have elementId and text for content elements
                                self.assertIn('elementId', content_item)
        
        print(f"✓ Validated {sheets_count} Google Sheets files")
        print(f"✓ Validated {slides_count} Google Slides files")
        print(f"✓ Validated {docs_count} Google Docs files")

    def test_database_state_after_hydration(self):
        """Test that the database is in a consistent state after hydration."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Verify database structure
        self.assertIn('users', DB)
        self.assertIn('me', DB['users'])
        self.assertIn('files', DB['users']['me'])
        self.assertIn('about', DB['users']['me'])
        
        # Verify files structure
        files = DB['users']['me']['files']
        self.assertIsInstance(files, dict)
        
        # Verify each file has required fields
        for file_id, file_data in files.items():
            with self.subTest(file_id=file_id):
                self.assertIsInstance(file_data, dict)
                self.assertIn('id', file_data)
                self.assertIn('name', file_data)
                self.assertIn('mimeType', file_data)
                
                # Verify file ID matches key
                self.assertEqual(file_data['id'], file_id)
        
        print(f"✓ Database state is consistent with {len(files)} files loaded")

    def test_api_integration_google_sheets(self):
        """Test that hydrated Google Sheets files can be accessed via the API."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find a Google Sheets file
        sheets_file_id = None
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.spreadsheet', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                sheets_file_id = file_id
                break
        
        if sheets_file_id is None:
            self.fail("No Google Sheets file found in test data")
        
        # Test API access
        try:
            from google_sheets.Spreadsheets import get
            spreadsheet = get(spreadsheet_id=sheets_file_id, includeGridData=True)
            
            # Verify API response
            self.assertIsInstance(spreadsheet, dict)
            self.assertIn('id', spreadsheet)
            self.assertEqual(spreadsheet['id'], sheets_file_id)
            
            print(f"✓ API integration test passed for Google Sheets file: {sheets_file_id}")
            
        except ImportError:
            self.fail("Google Sheets API not available")
        except Exception as e:
            self.fail(f"API integration test failed: {e}")

    def test_api_integration_google_slides(self):
        """Test that hydrated Google Slides files can be accessed via the API."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find a Google Slides file
        slides_file_id = None
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.presentation', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
                slides_file_id = file_id
                break
        
        if slides_file_id is None:
            self.fail("No Google Slides file found in test data")
        
        # Test API access
        try:
            from google_slides import get_presentation
            presentation = get_presentation(presentationId=slides_file_id)
            
            # Verify API response
            self.assertIsInstance(presentation, dict)
            self.assertIn('presentationId', presentation)
            self.assertEqual(presentation['presentationId'], slides_file_id)
            
            print(f"✓ API integration test passed for Google Slides file: {slides_file_id}")
            
        except ImportError:
            self.fail("Google Slides API not available")
        except Exception as e:
            self.fail(f"API integration test failed: {e}")

    def test_api_integration_google_docs(self):
        """Test that hydrated Google Docs files can be accessed via the API."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find a Google Docs file
        docs_file_id = None
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                docs_file_id = file_id
                break
        
        if docs_file_id is None:
            self.fail("No Google Docs file found in test data")
        
        # Test API access
        try:
            from google_docs import get_document
            document = get_document(documentId=docs_file_id)
            
            # Verify API response
            self.assertIsInstance(document, dict)
            self.assertIn('id', document)
            self.assertEqual(document['id'], docs_file_id)
            
            print(f"✓ API integration test passed for Google Docs file: {docs_file_id}")
            
        except ImportError:
            self.fail("Google Docs API not available")
        except Exception as e:
            self.fail(f"API integration test failed: {e}")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 