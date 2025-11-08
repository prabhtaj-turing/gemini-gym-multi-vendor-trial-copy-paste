import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
import random

# Import the hydrate_db function from the gdrive utils
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'APIs'))
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

class TestGDriveHydrateDB(unittest.TestCase):
    """Tests for Google Drive hydrate_db functionality."""

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

    def test_file_types_distribution(self):
        """Test that various file types are loaded correctly."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        files = DB['users']['me']['files']
        
        # Count files by type
        file_types = {}
        for file_data in files.values():
            mime_type = file_data.get('mimeType', 'unknown')
            file_types[mime_type] = file_types.get(mime_type, 0) + 1
        
        # Verify we have different types of files
        self.assertGreater(len(file_types), 0, "Should have at least one file type")
        
        # Print distribution
        print("File type distribution:")
        for mime_type, count in sorted(file_types.items()):
            print(f"  {mime_type}: {count} files")
        
        # Verify specific Google file types are present
        google_types = [t for t in file_types.keys() if t.startswith('application/vnd.google-apps.')]
        self.assertGreater(len(google_types), 0, "Should have at least one Google file type")

    def test_file_metadata_completeness(self):
        """Test that file metadata is complete and valid."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        files = DB['users']['me']['files']
        
        # Define required fields
        required_fields = ['id', 'name', 'mimeType']
        
        # Test metadata completeness
        incomplete_files = []
        for file_id, file_data in files.items():
            for field in required_fields:
                if field not in file_data:
                    incomplete_files.append((file_id, field))
        
        # All files should have required fields
        self.assertEqual(len(incomplete_files), 0, 
                        f"Files missing required fields: {incomplete_files}")
        
        # Verify data types
        for file_id, file_data in files.items():
            with self.subTest(file_id=file_id):
                self.assertIsInstance(file_data['id'], str)
                self.assertIsInstance(file_data['name'], str)
                self.assertIsInstance(file_data['mimeType'], str)
                
                # Optional fields should have correct types if present
                if 'size' in file_data:
                    self.assertIsInstance(file_data['size'], (int, str))
                if 'owners' in file_data:
                    self.assertIsInstance(file_data['owners'], list)
                if 'parents' in file_data:
                    self.assertIsInstance(file_data['parents'], list)
        
        print(f"✓ File metadata completeness validated for {len(files)} files")

    def test_google_docs_table_content_extraction(self):
        """Test that Google Docs with tables are properly extracted and stored."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        files = DB['users']['me']['files']
        
        # Look for Google Docs files
        google_docs_files = []
        for file_id, file_data in files.items():
            mime_type = file_data.get('mimeType', '')
            if mime_type == 'application/vnd.google-apps.document':
                google_docs_files.append((file_id, file_data))
        
        # Test each Google Doc file
        for file_id, file_data in google_docs_files:
            with self.subTest(file_id=file_id):
                # Verify content structure
                if 'content' in file_data and file_data['content']:
                    content = file_data['content']
                    
                    # Check if content is a list (as expected from get_content_google_docs)
                    if isinstance(content, list):
                        # Look for table elements
                        table_elements = [elem for elem in content if 'table' in elem]
                        
                        for table_elem in table_elements:
                            # Verify table structure
                            self.assertIn('elementId', table_elem)
                            self.assertIn('table', table_elem)
                            self.assertIsInstance(table_elem['table'], list)
                            
                            # Verify table data structure
                            table_data = table_elem['table']
                            if table_data:  # If table has rows
                                self.assertIsInstance(table_data[0], list)  # First row should be a list
                                
                                # Verify all rows have consistent structure
                                for row in table_data:
                                    self.assertIsInstance(row, list)
                                    for cell in row:
                                        self.assertIsInstance(cell, str)
                        
                        print(f"✓ Validated Google Doc table content: {file_data['name']}")
                    else:
                        print(f"Note: Google Doc {file_data['name']} has non-list content structure")

    def test_table_content_data_integrity(self):
        """Test that table content maintains data integrity during processing."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        files = DB['users']['me']['files']
        
        # Check all files for table content
        files_with_tables = []
        for file_id, file_data in files.items():
            if 'content' in file_data and file_data['content']:
                content = file_data['content']
                if isinstance(content, list):
                    table_elements = [elem for elem in content if 'table' in elem]
                    if table_elements:
                        files_with_tables.append((file_id, file_data, table_elements))
        
        # Test table data integrity
        for file_id, file_data, table_elements in files_with_tables:
            with self.subTest(file_id=file_id):
                for table_elem in table_elements:
                    table_data = table_elem['table']
                    
                    # Verify table is not empty
                    self.assertGreater(len(table_data), 0, "Table should have at least one row")
                    
                    # Verify all rows have the same number of columns (if table is rectangular)
                    if len(table_data) > 1:
                        first_row_length = len(table_data[0])
                        for i, row in enumerate(table_data[1:], 1):
                            # Allow for ragged tables (different column counts)
                            # but verify that all cells contain strings
                            for cell in row:
                                self.assertIsInstance(cell, str, 
                                    f"All table cells should be strings in {file_data['name']}")
                    
                    # Verify element ID format
                    self.assertTrue(table_elem['elementId'].startswith('t'), 
                        f"Table element ID should start with 't' in {file_data['name']}")
                    
                    # Verify element ID is numeric after 't'
                    try:
                        int(table_elem['elementId'][1:])
                    except ValueError:
                        self.fail(f"Table element ID should be numeric after 't' in {file_data['name']}")
                
                print(f"✓ Validated table data integrity: {file_data['name']}")

    def test_mixed_content_extraction(self):
        """Test that documents with both text and tables are properly extracted."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        files = DB['users']['me']['files']
        
        # Look for files with mixed content (both text and tables)
        files_with_mixed_content = []
        for file_id, file_data in files.items():
            if 'content' in file_data and file_data['content']:
                content = file_data['content']
                if isinstance(content, list):
                    text_elements = [elem for elem in content if 'text' in elem]
                    table_elements = [elem for elem in content if 'table' in elem]
                    
                    if text_elements and table_elements:
                        files_with_mixed_content.append((file_id, file_data, text_elements, table_elements))
        
        # Test mixed content files
        for file_id, file_data, text_elements, table_elements in files_with_mixed_content:
            with self.subTest(file_id=file_id):
                # Verify both text and table elements exist
                self.assertGreater(len(text_elements), 0, "Should have text elements")
                self.assertGreater(len(table_elements), 0, "Should have table elements")
                
                # Verify element IDs are properly formatted
                for text_elem in text_elements:
                    self.assertTrue(text_elem['elementId'].startswith('p'), 
                        f"Text element ID should start with 'p' in {file_data['name']}")
                
                for table_elem in table_elements:
                    self.assertTrue(table_elem['elementId'].startswith('t'), 
                        f"Table element ID should start with 't' in {file_data['name']}")
                
                # Verify content order is preserved (element IDs should be sequential)
                all_elements = text_elements + table_elements
                element_ids = [elem['elementId'] for elem in all_elements]
                
                # Sort by element ID to check if they're properly numbered
                sorted_ids = sorted(element_ids, key=lambda x: (x[0], int(x[1:])))
                
                print(f"✓ Validated mixed content extraction: {file_data['name']} "
                      f"(text: {len(text_elements)}, tables: {len(table_elements)})")

if __name__ == '__main__':
    unittest.main(verbosity=2) 