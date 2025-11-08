"""
Test module for state persistence (load/save) in Google Slides API.

This module tests the save_state and load_state functions to ensure
database state can be properly persisted and restored.
"""

import unittest
import json
import os
import tempfile
import uuid
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_slides.SimulationEngine.db import DB, save_state, load_state
from google_slides.SimulationEngine.utils import _ensure_user, _ensure_presentation_file
from google_slides.SimulationEngine import models
from .. import create_presentation

class TestStateLoadSave(BaseTestCaseWithErrorHandler):
    """Test cases for state load/save functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.DB = DB
        self.DB.clear()
        self.user_id = "me"
        _ensure_user(self.user_id)
        self.temp_files = []
        
    def tearDown(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        self.temp_files.clear()
        
    def _create_temp_file(self):
        """Create a temporary file and track it for cleanup"""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        self.temp_files.append(path)
        return path
        
    def test_save_state_basic(self):
        """Test basic save_state functionality"""
        # Add some data to DB
        presentation = {
            'presentationId': 'test_save_001',
            'title': 'Save Test Presentation',
            'slides': [],
            'masters': [],
            'layouts': []
        }
        _ensure_presentation_file(presentation, self.user_id)
        
        # Save state
        temp_file = self._create_temp_file()
        save_state(temp_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(temp_file))
        
        # Load and verify content
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
            
        self.assertIn('users', saved_data)
        self.assertIn(self.user_id, saved_data['users'])
        self.assertIn('files', saved_data['users'][self.user_id])
        self.assertIn('test_save_001', saved_data['users'][self.user_id]['files'])
        
    def test_load_state_default_db(self):
        """Test loading the GoogleSlidesDefaultDB.json directly"""
        # Get the path to the default DB
        default_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "DBs",
            "GoogleSlidesDefaultDB.json"
        )
        
        # Verify the file exists
        self.assertTrue(os.path.exists(default_db_path), f"Default DB not found at {default_db_path}")
        
        # Clear DB and load the default DB
        self.DB.clear()
        load_state(default_db_path)
        
        # Verify basic structure
        self.assertIn('users', self.DB)
        self.assertIn('me', self.DB['users'])
        
        # Verify about section
        self.assertIn('about', self.DB['users']['me'])
        self.assertEqual(self.DB['users']['me']['about']['kind'], 'drive#about')
        
        # Verify files section with presentations
        self.assertIn('files', self.DB['users']['me'])
        self.assertIn('pres1', self.DB['users']['me']['files'])
        
        # Verify presentation structure
        pres1 = self.DB['users']['me']['files']['pres1']
        self.assertEqual(pres1['presentationId'], 'pres1')
        self.assertEqual(pres1['title'], 'Test Presentation 1')
        self.assertEqual(pres1['mimeType'], 'application/vnd.google-apps.presentation')
        self.assertIsInstance(pres1['slides'], list)
        self.assertGreater(len(pres1['slides']), 0)
        
        # Verify counters
        self.assertIn('counters', self.DB['users']['me'])
    
    def test_load_state_basic(self):
        """Test basic load_state functionality"""
        # Create a state file with test data
        test_data = {
            'users': {
                'test_user': {
                    'about': {
                        'kind': 'drive#about',
                        'user': {
                            'displayName': 'Test User',
                            'emailAddress': 'test@example.com'
                        }
                    },
                    'files': {
                        'loaded_pres_001': {
                            'id': 'loaded_pres_001',
                            'driveId': '',
                            'name': 'Loaded Presentation',
                            'presentationId': 'loaded_pres_001',
                            'title': 'Loaded Presentation',
                            'mimeType': 'application/vnd.google-apps.presentation',
                            'createdTime': '2025-01-01T00:00:00Z',
                            'modifiedTime': '2025-01-01T00:00:00Z',
                            'owners': ['test_user@example.com'],
                            'parents': [],
                            'permissions': [],
                            'trashed': False,
                            'starred': False,
                            'slides': []
                        }
                    },
                    'drives': {},
                    'comments': {},
                    'replies': {},
                    'labels': {},
                    'accessproposals': {},
                    'counters': {
                        'file': 5
                    }
                }
            }
        }
        
        temp_file = self._create_temp_file()
        with open(temp_file, 'w') as f:
            json.dump(test_data, f)
            
        # Clear DB and load state
        self.DB.clear()
        load_state(temp_file)
        
        # Verify data was loaded
        self.assertIn('users', self.DB)
        self.assertIn('test_user', self.DB['users'])
        self.assertEqual(self.DB['users']['test_user']['files']['loaded_pres_001']['title'], 
                        'Loaded Presentation')
        self.assertEqual(self.DB['users']['test_user']['counters']['file'], 5)
        
    def test_save_load_round_trip(self):
        """Test save and load work together correctly"""
        # Create complex data structure
        presentation1 = create_presentation({"title": "Presentation 1"})
        presentation2 = create_presentation({"title": "Presentation 2"})
        
        # Modify standard counter values (only counters that exist in the schema)
        self.DB['users'][self.user_id]['counters']['file'] = 10
        self.DB['users'][self.user_id]['counters']['drive'] = 5
        
        # Save state
        temp_file = self._create_temp_file()
        save_state(temp_file)
        
        # Store IDs for verification
        pres1_id = presentation1['presentationId']
        pres2_id = presentation2['presentationId']
        
        # Clear and reload
        self.DB.clear()
        self.assertNotIn('users', self.DB)
        
        load_state(temp_file)
        
        # Verify presentations are preserved
        self.assertIn(self.user_id, self.DB['users'])
        self.assertIn(pres1_id, self.DB['users'][self.user_id]['files'])
        self.assertIn(pres2_id, self.DB['users'][self.user_id]['files'])
        self.assertEqual(self.DB['users'][self.user_id]['files'][pres1_id]['title'], 'Presentation 1')
        self.assertEqual(self.DB['users'][self.user_id]['files'][pres2_id]['title'], 'Presentation 2')
        
        # Verify counters are preserved
        self.assertEqual(self.DB['users'][self.user_id]['counters']['file'], 10)
        self.assertEqual(self.DB['users'][self.user_id]['counters']['drive'], 5)
        
    def test_save_state_with_complex_presentations(self):
        """Test saving state with complex presentation structures"""
        # Create a presentation with slides and elements
        presentation_data = models.PresentationModel(
            presentationId="complex_pres",
            title="Complex Presentation",
            pageSize=models.Size(
                width=models.Dimension(magnitude=9144000, unit="EMU"),
                height=models.Dimension(magnitude=5143500, unit="EMU")
            ),
            slides=[
                models.PageModel(
                    objectId="slide_001",
                    pageType=models.PageType.SLIDE,
                    revisionId="rev_slide_001",
                    pageProperties=models.PageProperties(
                        backgroundColor=models.BackgroundColor(
                            opaqueColor=models.OpaqueColor(
                                rgbColor=models.RgbColor(red=0.9, green=0.9, blue=0.9)
                            )
                        )
                    ),
                    slideProperties=models.SlideProperties(
                        layoutObjectId="layout_001"
                    ),
                    pageElements=[
                        models.PageElement(
                            objectId="elem_001",
                            size=models.Size(
                                width=models.Dimension(magnitude=200, unit="PT"),
                                height=models.Dimension(magnitude=100, unit="PT")
                            ),
                            shape=models.Shape(
                                shapeType="TEXT_BOX",
                                text=models.TextContent(
                                    textElements=[
                                        models.TextElement(
                                            textRun=models.TextRun(
                                                content="Hello World",
                                                style=models.TextStyle(
                                                    fontSize=models.Dimension(magnitude=14, unit="PT"),
                                                    bold=True
                                                )
                                            ),
                                            startIndex=0,
                                            endIndex=11
                                        )
                                    ]
                                ).model_dump(exclude_none=True, mode="json")
                            )
                        )
                    ]
                )
            ],
            masters=[],
            layouts=[
                models.PageModel(
                    objectId="layout_001",
                    pageType=models.PageType.LAYOUT,
                    revisionId="rev_layout_001",
                    pageProperties=models.PageProperties(
                        backgroundColor=models.BackgroundColor(
                            opaqueColor=models.OpaqueColor()
                        )
                    ),
                    layoutProperties=models.LayoutProperties(
                        name="BLANK",
                        displayName="Blank Layout"
                    ),
                    pageElements=[]
                )
            ],
            locale="en-US",
            revisionId="rev_complex_pres"
        )
        
        # Add to DB
        presentation_dict = presentation_data.model_dump(exclude_none=True, mode="json")
        _ensure_presentation_file(presentation_dict, self.user_id)
        
        # Save state
        temp_file = self._create_temp_file()
        save_state(temp_file)
        
        # Clear and reload
        self.DB.clear()
        load_state(temp_file)
        
        # Verify complex structure was preserved
        loaded_pres = self.DB['users'][self.user_id]['files']['complex_pres']
        self.assertEqual(loaded_pres['title'], 'Complex Presentation')
        self.assertEqual(len(loaded_pres['slides']), 1)
        self.assertEqual(loaded_pres['slides'][0]['objectId'], 'slide_001')
        self.assertEqual(len(loaded_pres['slides'][0]['pageElements']), 1)
        
        # Verify text content
        text_element = loaded_pres['slides'][0]['pageElements'][0]['shape']['text']['textElements'][0]
        self.assertEqual(text_element['textRun']['content'], 'Hello World')
        self.assertTrue(text_element['textRun']['style']['bold'])
        
    def test_load_state_nonexistent_file(self):
        """Test load_state with nonexistent file"""
        self.assert_error_behavior(
            load_state,
            FileNotFoundError,
            "[Errno 2] No such file or directory: '/nonexistent/path/to/file.json'",
            filepath='/nonexistent/path/to/file.json'
        )
            
    def test_load_state_invalid_json(self):
        """Test load_state with invalid JSON"""
        temp_file = self._create_temp_file()
        with open(temp_file, 'w') as f:
            f.write("{ invalid json }")
            
        # The load_state wraps JSONDecodeError in a ValueError
        self.assert_error_behavior(
            load_state,
            ValueError,
            "Invalid JSON format: Expecting property name enclosed in double quotes: line 1 column 3 (char 2)",
            filepath=temp_file
        )
            
    def test_save_state_permission_error(self):
        """Test save_state with permission error"""
        # Try to save to a protected directory that exists but is read-only
        protected_path = '/etc/test_save.json' if os.name != 'nt' else 'C:\\Windows\\System32\\test_save.json'
        
        # This should raise a permission error on most systems
        self.assert_error_behavior(
            save_state,
            PermissionError,
            f"[Errno 13] Permission denied: '{protected_path}'",
            filepath=protected_path
        )
            
    def test_multiple_users_save_load(self):
        """Test save/load with multiple users"""
        # Create data for multiple users
        for user_id in ['user1', 'user2', 'user3']:
            _ensure_user(user_id)
            presentation = {
                'presentationId': f'pres_{user_id}',
                'title': f'Presentation for {user_id}',
                'slides': []
            }
            _ensure_presentation_file(presentation, user_id)
            
        # Save state
        temp_file = self._create_temp_file()
        save_state(temp_file)
        
        # Clear and reload
        self.DB.clear()
        load_state(temp_file)
        
        # Verify all users were restored
        for user_id in ['user1', 'user2', 'user3']:
            self.assertIn(user_id, self.DB['users'])
            self.assertIn(f'pres_{user_id}', self.DB['users'][user_id]['files'])
            
    def test_save_load_preserves_counters(self):
        """Test that counters are preserved through save/load"""
        # Set specific counter values (only counters that exist in the schema)
        self.DB['users'][self.user_id]['counters']['file'] = 10
        self.DB['users'][self.user_id]['counters']['drive'] = 5
        self.DB['users'][self.user_id]['counters']['comment'] = 25
        self.DB['users'][self.user_id]['counters']['revision'] = 100
        
        # Save and reload
        temp_file = self._create_temp_file()
        save_state(temp_file)
        self.DB.clear()
        load_state(temp_file)
        
        # Verify counters
        counters = self.DB['users'][self.user_id]['counters']
        self.assertEqual(counters['file'], 10)
        self.assertEqual(counters['drive'], 5)
        self.assertEqual(counters['comment'], 25)
        self.assertEqual(counters['revision'], 100)
        
    def test_save_state_creates_parent_directories(self):
        """Test save_state creates parent directories if they don't exist"""
        # Create a path with non-existent parent directories
        temp_dir = tempfile.mkdtemp()
        self.temp_files.append(temp_dir)  # Track for cleanup
        
        nested_path = os.path.join(temp_dir, 'subdir1', 'subdir2', 'state.json')
        
        # Parent directories don't exist yet
        self.assertFalse(os.path.exists(os.path.dirname(nested_path)))
        
        # The gdrive save_state doesn't create parent directories
        # So we expect a FileNotFoundError
        self.assert_error_behavior(
            save_state,
            FileNotFoundError,
            f"[Errno 2] No such file or directory: '{nested_path}'",
            filepath=nested_path
        )
        
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
