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

class TestGSheetsHydrateDB(unittest.TestCase):
    """Tests for Google Sheets hydrate_db functionality."""

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

    def test_sheets_data_structure(self):
        """Test the structure of Google Sheets data."""
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
        
        if not sheets_files:
            self.fail("No Google Sheets files found in test data")
        
        for file_id, file_data in sheets_files:
            with self.subTest(file_id=file_id):
                # Test sheets structure
                if 'sheets' in file_data:
                    for sheet in file_data['sheets']:
                        self.assertIn('properties', sheet)
                        properties = sheet['properties']
                        self.assertIn('title', properties)
                        self.assertIn('sheetId', properties)
                        
                # Test data structure
                if 'data' in file_data:
                    for sheet_range, sheet_data in file_data['data'].items():
                        self.assertIsInstance(sheet_data, list)
                        if sheet_data:  # If there's data
                            self.assertIsInstance(sheet_data[0], list)  # First row should be a list
                            
                print(f"✓ Validated Google Sheets data structure: {file_data['name']}")

    def test_sheets_properties_validation(self):
        """Test that Google Sheets properties are correctly preserved."""
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
        
        if not sheets_files:
            self.fail("No Google Sheets files found in test data")
        
        for file_id, file_data in sheets_files:
            with self.subTest(file_id=file_id):
                # Verify spreadsheet properties
                if 'properties' in file_data:
                    properties = file_data['properties']
                    if 'title' in properties:
                        self.assertIsInstance(properties['title'], str)
                    if 'locale' in properties:
                        self.assertIsInstance(properties['locale'], str)
                    if 'timeZone' in properties:
                        self.assertIsInstance(properties['timeZone'], str)
                
                print(f"✓ Validated Google Sheets properties: {file_data['name']}")

    def test_sheets_data_content(self):
        """Test that Google Sheets data content is properly loaded."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find Google Sheets files with data
        sheets_with_data = []
        for file_id, file_data in DB['users']['me']['files'].items():
            if (file_data.get('mimeType') in ['application/vnd.google-apps.spreadsheet', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] and 
                'data' in file_data and file_data['data']):
                sheets_with_data.append((file_id, file_data))
        
        if not sheets_with_data:
            self.fail("No Google Sheets files with data found in test data")
        
        for file_id, file_data in sheets_with_data:
            with self.subTest(file_id=file_id):
                data = file_data['data']
                
                # Verify each sheet range has valid data
                for sheet_range, sheet_data in data.items():
                    self.assertIsInstance(sheet_range, str)
                    self.assertIsInstance(sheet_data, list)
                    
                    if sheet_data:  # If there's data
                        # First row should be a list
                        self.assertIsInstance(sheet_data[0], list)
                        
                        # All rows should have the same structure
                        for row in sheet_data:
                            self.assertIsInstance(row, list)
                            
                print(f"✓ Validated Google Sheets data content: {file_data['name']}")

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
            from google_sheets import get_spreadsheet
            spreadsheet = get_spreadsheet(spreadsheet_id=sheets_file_id, includeGridData=True)
            
            # Verify API response
            self.assertIsInstance(spreadsheet, dict)
            self.assertIn('id', spreadsheet)
            self.assertEqual(spreadsheet['id'], sheets_file_id)
            
            print(f"✓ API integration test passed for Google Sheets file: {sheets_file_id}")
            
        except ImportError:
            self.fail("Google Sheets API not available")
        except Exception as e:
            self.fail(f"API integration test failed: {e}")

    def test_sheets_count_and_distribution(self):
        """Test the count and distribution of Google Sheets files."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Count Google Sheets files
        sheets_count = 0
        sheets_with_data = 0
        sheets_with_multiple_sheets = 0
        
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.spreadsheet', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                sheets_count += 1
                
                if 'data' in file_data and file_data['data']:
                    sheets_with_data += 1
                    
                if 'sheets' in file_data and len(file_data['sheets']) > 1:
                    sheets_with_multiple_sheets += 1
        
        print(f"Google Sheets statistics:")
        print(f"  Total sheets files: {sheets_count}")
        print(f"  Sheets with data: {sheets_with_data}")
        print(f"  Sheets with multiple tabs: {sheets_with_multiple_sheets}")
        
        # Should have at least one sheets file
        self.assertGreater(sheets_count, 0, "Should have at least one Google Sheets file")

    def test_sheets_file_size_validation(self):
        """Test that Google Sheets file sizes are reasonable."""
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
        
        if not sheets_files:
            self.fail("No Google Sheets files found in test data")
        
        for file_id, file_data in sheets_files:
            with self.subTest(file_id=file_id):
                # Verify size field exists and is reasonable
                if 'size' in file_data:
                    size = file_data['size']
                    if isinstance(size, str):
                        size = int(size)
                    self.assertGreaterEqual(size, 0, "File size should be non-negative")
                    
                print(f"✓ Validated Google Sheets file size: {file_data['name']}")

if __name__ == '__main__':
    unittest.main(verbosity=2) 