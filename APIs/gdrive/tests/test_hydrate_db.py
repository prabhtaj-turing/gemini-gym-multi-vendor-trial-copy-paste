import unittest
from unittest.mock import patch, mock_open
import os
import sys
import base64
import hashlib
from datetime import datetime, timedelta, UTC
import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler

from gdrive.SimulationEngine.utils import hydrate_db
from ..SimulationEngine.db import DB

class TestHydrateDB(BaseTestCaseWithErrorHandler):
    """An extensive, state-based test suite for the hydrate_db function."""

    def setUp(self):
        """Reset DB to a clean state before each test."""
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
                            'displayName': '',
                            'kind': 'drive#user',
                            'me': True,
                            'permissionId': '',
                            'emailAddress': ''
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

    def test_hydrate_db_success(self):
        """Test that hydrate_db successfully hydrates the DB."""
        hydrate_db(DB, "APIs/gdrive/tests/json_data")

        self.assertEqual(DB['users']['me']['files']['pres_0923c170852bab81d481db7e870d6bee']['name'], 'Acme Proposal')
        self.assertEqual(DB['users']['me']['files']['file_be5ace206a68ed26ff09b4166377f6d4']['name'], 'Doe v. Smith Trial Prep Sheet.docx')
        self.assertEqual(DB['users']['me']['files']['file_6a0dd6dfdfa6825886d1e6cba2f71365']['name'], 'Empty_text_file.txt')
        self.assertEqual(DB['users']['me']['files']['file_59701ddfc443cb0d970f41e8932af8ee']['name'], 'Example_doc.docx')
        self.assertEqual(DB['users']['me']['files']['file_a8d36c3d87c2294fce78a7b7c77bedd9']['name'], 'Example_text_file.txt')
        self.assertEqual(DB['users']['me']['files']['sheet_daec2563e73d777c681e8cf7aab4813b']['name'], 'Production Costs - Waxahatchee')
        self.assertEqual(DB['users']['me']['files']['file_a3a6c8bd450f40b7f75e09b0e22fdce2']['name'], 'Example_file_in_subfolder.txt')
    
    def test_google_docs_can_get_from_hydrated_db(self):
        from APIs.google_docs import get_document
        documentId = 'file_be5ace206a68ed26ff09b4166377f6d4'
        hydrate_db(DB, "APIs/gdrive/tests/json_data")

        document_from_get = get_document(documentId=documentId, userId='me')
        document_from_db = DB['users']['me']['files'][documentId]
        
        self.assertEqual(document_from_get['id'], document_from_db['id'])
        self.assertEqual(document_from_get['name'], document_from_db['name'])
        self.assertEqual(document_from_get['mimeType'], document_from_db['mimeType'])
        self.assertEqual(document_from_get['createdTime'], document_from_db['createdTime'])
        self.assertEqual(document_from_get['modifiedTime'], document_from_db['modifiedTime'])
        self.assertEqual(document_from_get['trashed'], document_from_db['trashed'])
        self.assertEqual(document_from_get['starred'], document_from_db['starred'])
        self.assertEqual(document_from_get['parents'], document_from_db['parents'])
        self.assertEqual(document_from_get['owners'], document_from_db['owners'])
        self.assertEqual(document_from_get['size'], document_from_db['size'])
        self.assertEqual(document_from_get['permissions'], document_from_db['permissions'])
        self.assertEqual(document_from_get['content'], document_from_db['content'])
        self.assertEqual(document_from_get['revisions'], document_from_db['revisions'])
    
    def test_google_sheets_can_get_from_hydrated_db(self):
        from APIs.google_sheets import get_spreadsheet
        spreadsheet_id = 'sheet_daec2563e73d777c681e8cf7aab4813b'
        hydrate_db(DB, "APIs/gdrive/tests/json_data")

        spreadsheet_from_get = get_spreadsheet(spreadsheet_id=spreadsheet_id, includeGridData=True)
        spreadsheet_from_db = DB['users']['me']['files'][spreadsheet_id]
        
        self.assertEqual(spreadsheet_from_get['id'], spreadsheet_from_db['id'])
        self.assertEqual(spreadsheet_from_get['properties']['title'], spreadsheet_from_db['name'])
        self.assertEqual(spreadsheet_from_get['sheets'], spreadsheet_from_db['sheets'])
        self.assertEqual(spreadsheet_from_get['data'], spreadsheet_from_db['data'])
    
    def test_google_slides_can_get_from_hydrated_db(self):
        from APIs.google_slides import get_presentation
        presentationId = 'pres_0923c170852bab81d481db7e870d6bee'
        hydrate_db(DB, "APIs/gdrive/tests/json_data")

        presentation_from_get = get_presentation(presentationId=presentationId)
        presentation_from_db = DB['users']['me']['files'][presentationId]

        self.assertEqual(presentation_from_get['presentationId'], presentation_from_db['presentationId'])
        self.assertEqual(presentation_from_get['title'], presentation_from_db['title'])
        self.assertEqual(presentation_from_get['pageSize'], presentation_from_db['pageSize'])
        self.assertEqual(len(presentation_from_get['slides']), len(presentation_from_db['slides']))
        objectId_from_get = [presentation_from_get['slides'][i]['objectId'] for i in range(len(presentation_from_get['slides']))]
        objectId_from_db = [presentation_from_db['slides'][i]['objectId'] for i in range(len(presentation_from_db['slides']))]
        for objectId in objectId_from_get:
            self.assertIn(objectId, objectId_from_db)

    '''
    def test_google_drive_can_get_from_hydrated_db(self):
        from APIs.gdrive import get_file_metadata_or_content
        file_id = 'file_a8d36c3d87c2294fce78a7b7c77bedd9'
        hydrate_db(DB, "APIs/gdrive/tests/json_data")

        file_from_get = get_file_metadata_or_content(file_id=file_id, userId='me')
        file_from_db = DB['users']['me']['files'][file_id]
        
        print("file_from_get")
        print(file_from_get)
        print()
        print("file_from_db")
        print(file_from_db)
        print()

        self.assertEqual(file_from_get['id'], file_from_db['id'])
        self.assertEqual(file_from_get['name'], file_from_db['name'])
        self.assertEqual(file_from_get['mimeType'], file_from_db['mimeType'])
    '''

    def test_binary_files_loaded_in_hydrate_db(self):
        """Test that binary files (PDF and images) are correctly loaded during hydration."""
        hydrate_db(DB, "APIs/gdrive/tests/json_data")
        
        # Check that binary files are loaded into the database
        files = DB['users']['me']['files']
        
        # Look for our test files
        pdf_file = None
        jpg_file = None
        
        for file_id, file_data in files.items():
            if file_data['name'] == 'test_document.pdf':
                pdf_file = file_data
            elif file_data['name'] == 'test_image.jpg':
                jpg_file = file_data
        
        # Verify PDF file was loaded
        self.assertIsNotNone(pdf_file, "PDF file should be loaded in hydrate_db")
        self.assertEqual(pdf_file['mimeType'], 'application/pdf')
        self.assertIn('content', pdf_file)
        self.assertIsNotNone(pdf_file['content'])
        
        # Verify the content is base64 encoded
        self.assertIsInstance(pdf_file['content'], dict)
        self.assertIn('data', pdf_file['content'])
        self.assertEqual(pdf_file['content']['encoding'], 'base64')
        try:
            decoded_content = base64.b64decode(pdf_file['content']['data'])
            self.assertGreater(len(decoded_content), 0)
            # PDF files start with %PDF
            self.assertTrue(decoded_content.startswith(b'%PDF'))
        except Exception as e:
            self.fail(f"PDF content should be valid base64: {e}")
        
        # Verify JPG file was loaded
        self.assertIsNotNone(jpg_file, "JPG file should be loaded in hydrate_db")
        self.assertEqual(jpg_file['mimeType'], 'image/jpeg')
        self.assertIn('content', jpg_file)
        self.assertIsNotNone(jpg_file['content'])
        
        # Verify the content is base64 encoded
        self.assertIsInstance(jpg_file['content'], dict)
        self.assertIn('data', jpg_file['content'])
        self.assertEqual(jpg_file['content']['encoding'], 'base64')
        try:
            decoded_content = base64.b64decode(jpg_file['content']['data'])
            self.assertGreater(len(decoded_content), 0)
            # JPEG files start with FF D8 FF
            self.assertTrue(decoded_content.startswith(b'\xff\xd8\xff'))
        except Exception as e:
            self.fail(f"JPG content should be valid base64: {e}")

    def test_binary_files_have_correct_metadata(self):
        """Test that binary files have correct metadata after hydration."""
        hydrate_db(DB, "APIs/gdrive/tests/json_data")
        
        files = DB['users']['me']['files']
        
        # Find our test files
        pdf_file = None
        jpg_file = None
        
        for file_id, file_data in files.items():
            if file_data['name'] == 'test_document.pdf':
                pdf_file = file_data
            elif file_data['name'] == 'test_image.jpg':
                jpg_file = file_data
        
        # Verify PDF metadata
        self.assertIsNotNone(pdf_file)
        self.assertEqual(pdf_file['name'], 'test_document.pdf')
        self.assertEqual(pdf_file['mimeType'], 'application/pdf')
        self.assertIn('id', pdf_file)
        self.assertIn('size', pdf_file)
        self.assertIn('createdTime', pdf_file)
        self.assertIn('modifiedTime', pdf_file)
        self.assertIn('parents', pdf_file)
        self.assertIn('owners', pdf_file)
        self.assertFalse(pdf_file.get('trashed', False))
        
        # Verify JPG metadata
        self.assertIsNotNone(jpg_file)
        self.assertEqual(jpg_file['name'], 'test_image.jpg')
        self.assertEqual(jpg_file['mimeType'], 'image/jpeg')
        self.assertIn('id', jpg_file)
        self.assertIn('size', jpg_file)
        self.assertIn('createdTime', jpg_file)
        self.assertIn('modifiedTime', jpg_file)
        self.assertIn('parents', jpg_file)
        self.assertIn('owners', jpg_file)
        self.assertFalse(jpg_file.get('trashed', False))

    def test_binary_files_size_calculation(self):
        """Test that binary files have correct size calculation."""
        hydrate_db(DB, "APIs/gdrive/tests/json_data")
        
        files = DB['users']['me']['files']
        
        # Find our test files
        pdf_file = None
        jpg_file = None
        
        for file_id, file_data in files.items():
            if file_data['name'] == 'test_document.pdf':
                pdf_file = file_data
            elif file_data['name'] == 'test_image.jpg':
                jpg_file = file_data
        
        # Verify sizes match actual file sizes
        self.assertIsNotNone(pdf_file)
        self.assertIsNotNone(jpg_file)
        
        # Get actual file sizes
        pdf_path = os.path.join("APIs/gdrive/tests/json_data", "test_document.pdf")
        jpg_path = os.path.join("APIs/gdrive/tests/json_data", "test_image.jpg")
        
        if os.path.exists(pdf_path):
            actual_pdf_size = os.path.getsize(pdf_path)
            self.assertEqual(int(pdf_file['size']), actual_pdf_size)
        
        if os.path.exists(jpg_path):
            actual_jpg_size = os.path.getsize(jpg_path)
            self.assertEqual(int(jpg_file['size']), actual_jpg_size)

    def test_binary_files_conversion_back_to_original(self):
        """Test that binary files can be converted back to their original format using gdrive utilities."""
        import tempfile
        import filecmp
        from ..SimulationEngine.file_utils import base64_to_file, DriveFileProcessor
        
        hydrate_db(DB, "APIs/gdrive/tests/json_data")
        
        files = DB['users']['me']['files']
        
        # Find our test files
        pdf_file = None
        jpg_file = None
        
        for file_id, file_data in files.items():
            if file_data['name'] == 'test_document.pdf':
                pdf_file = file_data
            elif file_data['name'] == 'test_image.jpg':
                jpg_file = file_data
        
        self.assertIsNotNone(pdf_file)
        self.assertIsNotNone(jpg_file)
        
        # Test PDF conversion back to file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF back to file using base64_to_file utility
            output_pdf_path = os.path.join(temp_dir, "converted_test_document.pdf")
            base64_to_file(pdf_file['content']['data'], output_pdf_path)
            
            # Verify the converted file exists and has correct size
            self.assertTrue(os.path.exists(output_pdf_path))
            converted_size = os.path.getsize(output_pdf_path)
            self.assertEqual(converted_size, int(pdf_file['size']))
            
            # Verify the file is a valid PDF
            with open(output_pdf_path, 'rb') as f:
                pdf_header = f.read(4)
                self.assertEqual(pdf_header, b'%PDF')
            
            # Compare with original file if it exists
            original_pdf_path = os.path.join("APIs/gdrive/tests/json_data", "test_document.pdf")
            if os.path.exists(original_pdf_path):
                self.assertTrue(filecmp.cmp(original_pdf_path, output_pdf_path, shallow=False))
            
            # Test JPG conversion back to file
            output_jpg_path = os.path.join(temp_dir, "converted_test_image.jpg")
            base64_to_file(jpg_file['content']['data'], output_jpg_path)
            
            # Verify the converted file exists and has correct size
            self.assertTrue(os.path.exists(output_jpg_path))
            converted_size = os.path.getsize(output_jpg_path)
            self.assertEqual(converted_size, int(jpg_file['size']))
            
            # Verify the file is a valid JPEG
            with open(output_jpg_path, 'rb') as f:
                jpg_header = f.read(3)
                self.assertEqual(jpg_header, b'\xff\xd8\xff')
            
            # Compare with original file if it exists
            original_jpg_path = os.path.join("APIs/gdrive/tests/json_data", "test_image.jpg")
            if os.path.exists(original_jpg_path):
                self.assertTrue(filecmp.cmp(original_jpg_path, output_jpg_path, shallow=False))

    def test_binary_files_processor_decode_functionality(self):
        """Test that DriveFileProcessor can properly decode base64 content back to bytes."""
        from ..SimulationEngine.file_utils import DriveFileProcessor
        
        hydrate_db(DB, "APIs/gdrive/tests/json_data")
        
        files = DB['users']['me']['files']
        processor = DriveFileProcessor()
        
        # Find our test files
        pdf_file = None
        jpg_file = None
        
        for file_id, file_data in files.items():
            if file_data['name'] == 'test_document.pdf':
                pdf_file = file_data
            elif file_data['name'] == 'test_image.jpg':
                jpg_file = file_data
        
        self.assertIsNotNone(pdf_file)
        self.assertIsNotNone(jpg_file)

        # Test PDF decoding using DriveFileProcessor
        pdf_decoded = processor.decode_base64_to_file(pdf_file['content'])
        self.assertIsInstance(pdf_decoded, str)
        self.assertGreater(len(pdf_decoded), 0)
        self.assertEqual(len(pdf_decoded), int(pdf_file['size']))
        self.assertTrue(pdf_decoded.startswith('%PDF'))
        
        # Test JPG decoding using DriveFileProcessor
        jpg_decoded = processor.decode_base64_to_file(jpg_file['content'])
        self.assertIsInstance(jpg_decoded, str)
        self.assertGreater(len(jpg_decoded), 0)
        print("jpg_decoded")
        print(jpg_decoded[:20])
        self.assertTrue(jpg_decoded.startswith("b'\\xff\\xd8\\xff"))

    def test_binary_files_checksum_validation(self):
        """Test that binary files have correct checksums and can be validated."""
        import hashlib
        from ..SimulationEngine.file_utils import DriveFileProcessor
        
        hydrate_db(DB, "APIs/gdrive/tests/json_data")
        
        files = DB['users']['me']['files']
        processor = DriveFileProcessor()
        
        # Find our test files
        pdf_file = None
        jpg_file = None
        
        for file_id, file_data in files.items():
            if file_data['name'] == 'test_document.pdf':
                pdf_file = file_data
            elif file_data['name'] == 'test_image.jpg':
                jpg_file = file_data
        
        self.assertIsNotNone(pdf_file)
        self.assertIsNotNone(jpg_file)
        
        # Test PDF checksum validation
        pdf_decoded = processor.decode_base64_to_file(pdf_file['content'])
        expected_checksum = pdf_file['content']['checksum']
        
        # Extract the hash from the checksum (format: "sha256:hash")
        if expected_checksum.startswith('sha256:'):
            expected_hash = expected_checksum[7:]  # Remove "sha256:" prefix
            actual_hash = hashlib.sha256(pdf_decoded.encode('utf-8')).hexdigest()
            self.assertEqual(actual_hash, expected_hash)
    
    def test_hydrate_db_has_revision_with_content(self):
        """Test that hydrate_db has revision with content."""
        hydrate_db(DB, "APIs/gdrive/tests/json_data")
        
        files = DB['users']['me']['files']
        for _, file_data in files.items():
            if 'revisions' in file_data:
                for revision in file_data['revisions']:
                    self.assertIn('content', revision)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
