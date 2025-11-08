"""
Comprehensive test cases for the fixed issues in batch_update_presentation function.

This module tests:
1. Index field requirement in layoutPlaceholder
2. TITLE_AND_BODY predefined layout support
3. Proper request structure validation
4. Backend behavior with predefined layouts
"""

import unittest
import copy
from APIs.google_slides.presentations import batch_update_presentation
from APIs.google_slides.SimulationEngine.db import DB
from APIs.google_slides.SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestBatchUpdateFixes(BaseTestCaseWithErrorHandler):
    """Test cases for the fixed issues in batch_update_presentation."""
    
    def setUp(self):
        """Set up test data before each test."""
        self.maxDiff = None
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        # Create a test presentation with proper structure
        self.presentation_id = "pres1"
        self.user_id = "me"
        
        # Initialize user and presentation following existing test patterns
        DB.update({
            "users": {
                self.user_id: {
                    "about": {
                        "kind": "drive#about",
                        "storageQuota": {
                            "limit": "0",
                            "usageInDrive": "0",
                            "usageInDriveTrash": "0",
                            "usage": "0"
                        },
                        "driveThemes": False,
                        "canCreateDrives": False,
                        "importFormats": {},
                        "exportFormats": {},
                        "appInstalled": False,
                        "user": {
                            "displayName": "",
                            "kind": "drive#user",
                            "me": True,
                            "permissionId": "",
                            "emailAddress": ""
                        },
                        "folderColorPalette": "",
                        "maxImportSizes": {},
                        "maxUploadSize": "0"
                    },
                    "files": {
                        self.presentation_id: {
                            "id": self.presentation_id,
                            "driveId": "My-Drive-ID",
                            "name": "Test Presentation 1",
                            "mimeType": "application/vnd.google-apps.presentation",
                            "createdTime": "2025-03-01T10:00:00Z",
                            "modifiedTime": "2025-03-10T10:00:00Z",
                            "trashed": False,
                            "starred": False,
                            "parents": ["drive-1"],
                            "owners": ["john.doe@gmail.com"],
                            "size": "102400",
                            "permissions": [
                                {
                                    "kind": "drive#permission",
                                    "id": "anyoneWithLink",
                                    "type": "anyone",
                                    "role": "reader"
                                }
                            ],
                            "presentationId": self.presentation_id,
                            "title": "Test Presentation",
                            "slides": [],
                            "layouts": [],
                            "masters": [],
                            "pageSize": {
                                "width": {"magnitude": 720, "unit": "PT"},
                                "height": {"magnitude": 405, "unit": "PT"}
                            },
                            "revisionId": "1"
                        }
                    }
                }
            }
        })
        
    def tearDown(self):
        """Restore original DB state after each test."""
        global DB
        DB.clear()
        DB.update(self._original_DB_state)
    
    def test_layout_placeholder_index_field_valid(self):
        """Test that index field works correctly when provided."""
        # Test case 2: Valid index field should work
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_with_index",
                    "placeholderIdMappings": [{
                        "objectId": "placeholder_test",
                        "layoutPlaceholder": {
                            "type": "TITLE",
                            "index": 0
                        }
                    }]
                }
            }]
        )
        self.assertIsNotNone(result)
        self.assertIn("createSlide", result["replies"][0])
    
    def test_title_and_body_predefined_layout_works(self):
        """Test that TITLE_AND_BODY predefined layout works correctly."""
        # Test case 3: TITLE_AND_BODY should work even without existing layout
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_title_body",
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE_AND_BODY"
                    }
                }
            }]
        )
        
        # Verify the slide was created
        self.assertIsNotNone(result)
        self.assertIn("createSlide", result["replies"][0])
        
        # Verify the layout was created automatically
        presentation = DB['users']['me']['files']['pres1']
        layouts = presentation.get('layouts', [])
        
        # Should have at least one layout with TITLE_AND_BODY name
        title_body_layouts = [
            layout for layout in layouts 
            if layout.get('layoutProperties', {}).get('name') == 'TITLE_AND_BODY'
        ]
        self.assertGreater(len(title_body_layouts), 0, 
                            "TITLE_AND_BODY layout should be created automatically")
        
        # Verify the slide uses the correct layout
        slides = presentation.get('slides', [])
        test_slide = next((s for s in slides if s['objectId'] == 'test_slide_title_body'), None)
        self.assertIsNotNone(test_slide, "Test slide should be created")
        self.assertIn('slideProperties', test_slide)
        self.assertIn('layoutObjectId', test_slide['slideProperties'])
    
    def test_title_predefined_layout_works(self):
        """Test that TITLE predefined layout works correctly."""
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_title",
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE"
                    }
                }
            }]
        )
        
        self.assertIsNotNone(result)
        self.assertIn("createSlide", result["replies"][0])
        
        # Verify the layout was created
        presentation = DB['users']['me']['files']['pres1']
        layouts = presentation.get('layouts', [])
        
        title_layouts = [
            layout for layout in layouts 
            if layout.get('layoutProperties', {}).get('name') == 'TITLE'
        ]
        self.assertGreater(len(title_layouts), 0, 
                            "TITLE layout should be created automatically")
    
    def test_blank_predefined_layout_works(self):
        """Test that BLANK predefined layout works correctly."""
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_blank",
                    "slideLayoutReference": {
                        "predefinedLayout": "BLANK"
                    }
                }
            }]
        )
        
        self.assertIsNotNone(result)
        self.assertIn("createSlide", result["replies"][0])
    
    def test_proper_request_structure_validation(self):
        """Test that proper request structure is validated correctly."""
        # Test case 4: Proper separate requests should work
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[
                {
                    "createSlide": {
                        "objectId": "proper_slide_id"
                    }
                },
                {
                    "createShape": {
                        "objectId": "proper_shape_id",
                        "shapeType": "TEXT_BOX",
                        "elementProperties": {
                            "pageObjectId": "proper_slide_id",
                            "size": {
                                "width": {"magnitude": 200, "unit": "PT"},
                                "height": {"magnitude": 100, "unit": "PT"}
                            }
                        }
                    }
                },
                {
                    "insertText": {
                        "objectId": "proper_shape_id",
                        "text": "Proper text insertion"
                    }
                }
            ]
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result["replies"]), 3)
        self.assertIn("createSlide", result["replies"][0])
        self.assertIn("createShape", result["replies"][1])
        self.assertIn("insertText", result["replies"][2])
    
    def test_title_and_body_layout_has_correct_placeholders(self):
        """Test that TITLE_AND_BODY layout has correct placeholders."""
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_placeholders",
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE_AND_BODY"
                    }
                }
            }]
        )
        
        # Find the created layout
        presentation = DB['users']['me']['files']['pres1']
        layouts = presentation.get('layouts', [])
        
        title_body_layout = next(
            (layout for layout in layouts 
             if layout.get('layoutProperties', {}).get('name') == 'TITLE_AND_BODY'),
            None
        )
        
        self.assertIsNotNone(title_body_layout, "TITLE_AND_BODY layout should exist")
        
        # Check that it has the correct placeholders
        page_elements = title_body_layout.get('pageElements', [])
        self.assertEqual(len(page_elements), 2, "TITLE_AND_BODY should have 2 placeholders")
        
        # Check for title placeholder
        title_placeholder = next(
            (elem for elem in page_elements 
             if elem.get('placeholder', {}).get('type') == 'TITLE'),
            None
        )
        self.assertIsNotNone(title_placeholder, "Should have TITLE placeholder")
        self.assertEqual(title_placeholder['placeholder']['index'], 0)
        
        # Check for body placeholder
        body_placeholder = next(
            (elem for elem in page_elements 
             if elem.get('placeholder', {}).get('type') == 'BODY'),
            None
        )
        self.assertIsNotNone(body_placeholder, "Should have BODY placeholder")
        self.assertEqual(body_placeholder['placeholder']['index'], 0)
    
    def test_title_layout_has_correct_placeholders(self):
        """Test that TITLE layout has correct placeholders."""
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_title_only",
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE"
                    }
                }
            }]
        )
        
        # Find the created layout
        presentation = DB['users']['me']['files']['pres1']
        layouts = presentation.get('layouts', [])
        
        title_layout = next(
            (layout for layout in layouts 
             if layout.get('layoutProperties', {}).get('name') == 'TITLE'),
            None
        )
        
        self.assertIsNotNone(title_layout, "TITLE layout should exist")
        
        # Check that it has only title placeholder
        page_elements = title_layout.get('pageElements', [])
        self.assertEqual(len(page_elements), 1, "TITLE should have 1 placeholder")
        
        # Check for title placeholder
        title_placeholder = page_elements[0]
        self.assertEqual(title_placeholder.get('placeholder', {}).get('type'), 'TITLE')
        self.assertEqual(title_placeholder['placeholder']['index'], 0)
    
    def test_blank_layout_has_no_placeholders(self):
        """Test that BLANK layout has no placeholders."""
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_blank_only",
                    "slideLayoutReference": {
                        "predefinedLayout": "BLANK"
                    }
                }
            }]
        )
        
        # Find the created layout
        presentation = DB['users']['me']['files']['pres1']
        layouts = presentation.get('layouts', [])
        
        blank_layout = next(
            (layout for layout in layouts 
             if layout.get('layoutProperties', {}).get('name') == 'BLANK'),
            None
        )
        
        self.assertIsNotNone(blank_layout, "BLANK layout should exist")
        
        # Check that it has no placeholders
        page_elements = blank_layout.get('pageElements', [])
        self.assertEqual(len(page_elements), 0, "BLANK should have no placeholders")
    
    def test_multiple_predefined_layouts_work(self):
        """Test that multiple predefined layouts can be created."""
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[
                {
                    "createSlide": {
                        "objectId": "slide_title_body",
                        "slideLayoutReference": {
                            "predefinedLayout": "TITLE_AND_BODY"
                        }
                    }
                },
                {
                    "createSlide": {
                        "objectId": "slide_title",
                        "slideLayoutReference": {
                            "predefinedLayout": "TITLE"
                        }
                    }
                },
                {
                    "createSlide": {
                        "objectId": "slide_blank",
                        "slideLayoutReference": {
                            "predefinedLayout": "BLANK"
                        }
                    }
                }
            ]
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result["replies"]), 3)
        
        # Verify all layouts were created
        presentation = DB['users']['me']['files']['pres1']
        layouts = presentation.get('layouts', [])
        
        layout_names = [layout.get('layoutProperties', {}).get('name') for layout in layouts]
        self.assertIn('TITLE_AND_BODY', layout_names)
        self.assertIn('TITLE', layout_names)
        self.assertIn('BLANK', layout_names)
    
    def test_existing_layout_takes_precedence(self):
        """Test that existing layouts take precedence over auto-creation."""
        # First, manually add a TITLE_AND_BODY layout
        presentation = DB['users']['me']['files']['pres1']
        presentation['layouts'].append({
            'objectId': 'existing_title_body_layout',
            'pageType': 'LAYOUT',
            'revisionId': 'rev_existing',
            'layoutProperties': {
                'name': 'TITLE_AND_BODY',
                'displayName': 'Existing Title and Body'
            },
            'pageElements': [],
            'pageProperties': {
                'backgroundColor': {
                    'opaqueColor': {
                        'rgbColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}
                    }
                }
            }
        })

        # Now create a slide with TITLE_AND_BODY - should use existing layout
        result = batch_update_presentation(
            presentationId="pres1",
            requests=[{
                "createSlide": {
                    "objectId": "test_slide_existing_layout",
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE_AND_BODY"
                    }
                }
            }]
        )
        
        # Re-fetch the presentation after the update (batch_update replaces the entire object)
        presentation = DB['users']['me']['files']['pres1']
        
        # Verify the slide uses the existing layout
        slides = presentation.get('slides', [])
        test_slide = next((s for s in slides if s['objectId'] == 'test_slide_existing_layout'), None)
        self.assertIsNotNone(test_slide)
        self.assertEqual(test_slide['slideProperties']['layoutObjectId'], 'existing_title_body_layout')
        
        # Verify no duplicate layout was created
        title_body_layouts = [
            layout for layout in presentation['layouts']
            if layout.get('layoutProperties', {}).get('name') == 'TITLE_AND_BODY'
        ]
        self.assertEqual(len(title_body_layouts), 1, "Should not create duplicate layouts")


if __name__ == '__main__':
    unittest.main()
