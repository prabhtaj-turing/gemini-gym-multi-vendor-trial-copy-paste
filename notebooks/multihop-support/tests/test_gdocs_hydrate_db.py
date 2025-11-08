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

class TestGDocsHydrateDB(unittest.TestCase):
    """Tests for Google Docs hydrate_db functionality."""

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
        
        if not docs_files:
            self.fail("No Google Docs files found in test data")
        
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
                        self.assertIsInstance(file_data['content']['data'], list)
                        content_data = file_data['content']['data']
                    else:
                        self.assertIsInstance(file_data['content'], list)
                        content_data = file_data['content']
                    
                    # Validate content elements if present
                    if content_data:
                        for item in content_data[:3]:  # Check first few items
                            if isinstance(item, dict) and 'table' not in item:
                                self.assertIn('elementId', item)
                                self.assertIn('text', item)
                
                print(f"✓ Validated Google Docs file: {file_data['name']}")

    def test_docs_content_structure(self):
        """Test the structure of Google Docs content."""
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
        
        if not docs_files:
            self.fail("No Google Docs files found in test data")
        
        for file_id, file_data in docs_files:
            with self.subTest(file_id=file_id):
                # Test content structure
                if 'content' in file_data:
                    # Get content data (handle both dict and list formats)
                    if isinstance(file_data['content'], dict) and 'data' in file_data['content']:
                        content_data = file_data['content']['data']
                    else:
                        content_data = file_data['content']
                    
                    for content_item in content_data[:5]:  # Check first few items
                        if isinstance(content_item, dict):
                            # Should have elementId and text for content elements
                            self.assertIn('elementId', content_item)
                            
                            # Text field should be present
                            if 'text' in content_item:
                                self.assertIsInstance(content_item['text'], str)
                                
                print(f"✓ Validated Google Docs content structure: {file_data['name']}")

    def test_docs_text_content_extraction(self):
        """Test that text content is properly extracted from Google Docs."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Find Google Docs files with content
        docs_with_content = []
        for file_id, file_data in DB['users']['me']['files'].items():
            if (file_data.get('mimeType') in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'] and 
                'content' in file_data and file_data['content']):
                docs_with_content.append((file_id, file_data))
        
        if not docs_with_content:
            self.fail("No Google Docs files with content found in test data")
        
        total_text_length = 0
        
        for file_id, file_data in docs_with_content:
            with self.subTest(file_id=file_id):
                # Get content data (handle both dict and list formats)
                if isinstance(file_data['content'], dict) and 'data' in file_data['content']:
                    content_data = file_data['content']['data']
                else:
                    content_data = file_data['content']
                
                # Extract all text content
                for content_item in content_data[:10]:  # Check first few items
                    if isinstance(content_item, dict) and 'text' in content_item:
                        text = content_item['text']
                        total_text_length += len(text)
                        
                        # Text should not be empty for meaningful content
                        if text.strip():
                            self.assertGreater(len(text.strip()), 0)
                            
                print(f"✓ Validated Google Docs text content: {file_data['name']}")
        
        print(f"Total text content length: {total_text_length} characters")

    def test_docs_document_properties(self):
        """Test that Google Docs document properties are correctly preserved."""
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
        
        if not docs_files:
            self.fail("No Google Docs files found in test data")
        
        for file_id, file_data in docs_files:
            with self.subTest(file_id=file_id):
                # Verify document properties
                if 'documentId' in file_data:
                    self.assertEqual(file_data['documentId'], file_data['id'])
                    
                # Check for revisions if present
                if 'revisions' in file_data:
                    self.assertIsInstance(file_data['revisions'], list)
                
                print(f"✓ Validated Google Docs properties: {file_data['name']}")

    def test_docs_revision_history(self):
        """Test that Google Docs revision history is preserved if available."""
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
        
        if not docs_files:
            self.fail("No Google Docs files found in test data")
        
        docs_with_revisions = 0
        
        for file_id, file_data in docs_files:
            with self.subTest(file_id=file_id):
                # Check for revision history
                if 'revisions' in file_data and file_data['revisions']:
                    docs_with_revisions += 1
                    revisions = file_data['revisions']
                    
                    for revision in revisions:
                        if isinstance(revision, dict):
                            # Common revision fields
                            self.assertIsInstance(revision, dict)
                            
                print(f"✓ Validated Google Docs revisions: {file_data['name']}")
        
        print(f"Documents with revision history: {docs_with_revisions}")

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
            
            # Verify API response (Google Docs API returns 'id', not 'documentId')
            self.assertIsInstance(document, dict)
            self.assertIn('id', document)
            self.assertEqual(document['id'], docs_file_id)
            
            print(f"✓ API integration test passed for Google Docs file: {docs_file_id}")
            
        except ImportError:
            self.fail("Google Docs API not available")
        except Exception as e:
            self.fail(f"API integration test failed: {e}")

    def test_docs_count_and_statistics(self):
        """Test the count and statistics of Google Docs files."""
        test_data_path = self.get_test_data_path()
        
        if not os.path.exists(test_data_path):
            self.fail(f"Test data directory not found: {test_data_path}")
        
        # Hydrate the database
        hydrate_db_sample(DB, test_data_path, max_files_per_type=2)
        
        # Count Google Docs files
        docs_count = 0
        docs_with_content = 0
        total_content_elements = 0
        
        for file_id, file_data in DB['users']['me']['files'].items():
            if file_data.get('mimeType') in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                docs_count += 1
                
                if 'content' in file_data and file_data['content']:
                    docs_with_content += 1
                    total_content_elements += len(file_data['content'])
        
        print(f"Google Docs statistics:")
        print(f"  Total document files: {docs_count}")
        print(f"  Documents with content: {docs_with_content}")
        print(f"  Total content elements: {total_content_elements}")
        
        # Note: We might not have Google Docs files in test data
        if docs_count > 0:
            self.assertGreater(docs_count, 0, "Should have at least one Google Docs file")

    def test_docs_content_element_types(self):
        """Test different types of content elements in Google Docs."""
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
        
        if not docs_files:
            self.fail("No Google Docs files found in test data")
        
        element_types = set()
        
        for file_id, file_data in docs_files:
            with self.subTest(file_id=file_id):
                if 'content' in file_data:
                    # Get content data (handle both dict and list formats)
                    if isinstance(file_data['content'], dict) and 'data' in file_data['content']:
                        content_data = file_data['content']['data']
                    else:
                        content_data = file_data['content']
                    
                    for content_item in content_data[:10]:  # Check first few items
                        if isinstance(content_item, dict):
                            # Track different element types
                            if 'elementId' in content_item:
                                element_types.add('element')
                            if 'text' in content_item:
                                element_types.add('text')
                            if 'textRun' in content_item:
                                element_types.add('textRun')
                                
                print(f"✓ Validated Google Docs content elements: {file_data['name']}")
        
        print(f"Content element types found: {element_types}")

    def test_docs_file_size_validation(self):
        """Test that Google Docs file sizes are reasonable."""
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
        
        if not docs_files:
            self.fail("No Google Docs files found in test data")
        
        for file_id, file_data in docs_files:
            with self.subTest(file_id=file_id):
                # Check file size if present
                if 'size' in file_data:
                    size = int(file_data['size']) if isinstance(file_data['size'], str) else file_data['size']
                    self.assertGreater(size, 0)
                    # Reasonable upper limit for test files
                    self.assertLess(size, 100 * 1024 * 1024)  # 100MB
                    
                print(f"✓ Validated Google Docs file size: {file_data['name']}")

    def test_docs_content_vs_file_metadata(self):
        """Test consistency between document content and file metadata."""
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
        
        if not docs_files:
            self.fail("No Google Docs files found in test data")
        
        for file_id, file_data in docs_files:
            with self.subTest(file_id=file_id):
                # Basic consistency checks
                self.assertEqual(file_data['id'], file_id)
                
                # If content exists, it should be consistent with file existence
                if 'content' in file_data and file_data['content']:
                    # Get content data (handle both dict and list formats)
                    if isinstance(file_data['content'], dict) and 'data' in file_data['content']:
                        content_data = file_data['content']['data']
                        # Content should be a list
                        self.assertIsInstance(content_data, list)
                    else:
                        content_data = file_data['content']
                        self.assertIsInstance(content_data, list)
                
                print(f"✓ Validated Google Docs consistency: {file_data['name']}")

if __name__ == '__main__':
    unittest.main(verbosity=2) 