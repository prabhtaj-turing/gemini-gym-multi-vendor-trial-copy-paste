import unittest
import copy
from datetime import datetime, timezone
import uuid

from google_slides.presentations import batch_update_presentation, get_presentation
from google_slides.SimulationEngine import utils
from google_slides.SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_slides.SimulationEngine.db import DB
from google_slides.SimulationEngine import models
from google_slides.SimulationEngine.models import *
from google_slides.SimulationEngine.custom_errors import *


class TestBatchUpdatePredefinedLayouts(BaseTestCaseWithErrorHandler):
    """Test class for batch_update_presentation with various predefined layouts."""
    
    def setUp(self):
        """Set up test data for predefined layout testing."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.user_id = "me"
        self.presentation_id = "test_predefined_layouts_presentation"
        self.initial_revision_id = "rev_initial_predefined_layouts"
        self.default_master_id = "master_default_canonical_id"

        # Ensure user structure is initialized
        utils._ensure_user(self.user_id)

        # Create initial presentation data with multiple predefined layouts
        self.initial_presentation_data = {
            "presentationId": self.presentation_id,
            "title": "Predefined Layouts Test Presentation",
            "slides": [
                {
                    "objectId": "slide_initial_uuid",
                    "pageType": "SLIDE",
                    "slideProperties": {
                        "layoutObjectId": "layout_blank_canonical_id",
                        "masterObjectId": self.default_master_id,
                        "isSkipped": False
                    },
                    "notesPage": {
                        "objectId": "notes_page_initial_uuid",
                        "pageType": "NOTES_PAGE",
                        "notesPageProperties": {"speakerNotesObjectId": "speaker_notes_initial_uuid"},
                        "pageElements": []
                    },
                    "pageElements": []
                }
            ],
            "masters": [
                {
                    "objectId": self.default_master_id,
                    "pageType": "MASTER",
                    "pageElements": [],
                    "masterProperties": {
                        "displayName": "Default Master"
                    }
                }
            ],
            "layouts": [
                {
                    "objectId": "layout_blank_canonical_id",
                    "pageType": "LAYOUT",
                    "layoutProperties": {
                        "masterObjectId": self.default_master_id,
                        "name": "BLANK",
                        "displayName": "Blank Layout"
                    },
                    "pageElements": []
                },
                {
                    "objectId": "layout_title_canonical_id",
                    "pageType": "LAYOUT",
                    "layoutProperties": {
                        "masterObjectId": self.default_master_id,
                        "name": "TITLE",
                        "displayName": "Title Layout"
                    },
                    "pageElements": [
                        {
                            "objectId": "title_placeholder_uuid",
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "placeholder": {"type": "TITLE", "index": 0}
                            }
                        }
                    ]
                },
                {
                    "objectId": "layout_title_and_body_canonical_id",
                    "pageType": "LAYOUT",
                    "layoutProperties": {
                        "masterObjectId": self.default_master_id,
                        "name": "TITLE_AND_BODY",
                        "displayName": "Title and Body Layout"
                    },
                    "pageElements": [
                        {
                            "objectId": "title_placeholder_uuid",
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "placeholder": {"type": "TITLE", "index": 0}
                            }
                        },
                        {
                            "objectId": "body_placeholder_uuid",
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "placeholder": {"type": "BODY", "index": 0}
                            }
                        }
                    ]
                },
                {
                    "objectId": "layout_section_header_canonical_id",
                    "pageType": "LAYOUT",
                    "layoutProperties": {
                        "masterObjectId": self.default_master_id,
                        "name": "SECTION_HEADER",
                        "displayName": "Section Header Layout"
                    },
                    "pageElements": []
                },
                {
                    "objectId": "layout_big_number_canonical_id",
                    "pageType": "LAYOUT",
                    "layoutProperties": {
                        "masterObjectId": self.default_master_id,
                        "name": "BIG_NUMBER",
                        "displayName": "Big Number Layout"
                    },
                    "pageElements": []
                }
            ],
            "notesMaster": {
                "objectId": "notes_master_uuid",
                "pageType": "NOTES_MASTER",
                "pageElements": []
            },
            "pageSize": {"width": {"magnitude": 7200000, "unit": "EMU"}, "height": {"magnitude": 4050000, "unit": "EMU"}},
            "locale": "en_US",
            "revisionId": self.initial_revision_id
        }

        # Use the proper utility function to create the presentation file
        utils._ensure_presentation_file(self.initial_presentation_data, self.user_id)

    def tearDown(self):
        """Restore original database state."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_create_slide_with_blank_layout(self):
        """Test creating a slide with BLANK predefined layout."""
        
        requests = [
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                    "objectId": "blank_slide"
                }
            }
        ]

        response = batch_update_presentation(
            presentationId=self.presentation_id,
            requests=requests
        )

        # Validate response structure
        self.assertIn('presentationId', response)
        self.assertIn('replies', response)
        self.assertIn('writeControl', response)
        
        self.assertEqual(response['presentationId'], self.presentation_id)
        self.assertEqual(len(response['replies']), 1)
        
        # Validate slide creation reply
        reply = response['replies'][0]
        self.assertIn('createSlide', reply)
        self.assertEqual(reply['createSlide']['objectId'], "blank_slide")

        # Verify the presentation was updated in the database
        updated_presentation = get_presentation(presentationId=self.presentation_id)
        self.assertEqual(len(updated_presentation['slides']), 2)  # 1 initial + 1 new slide

    def test_create_slide_with_title_layout(self):
        """Test creating a slide with TITLE predefined layout."""
        
        requests = [
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "TITLE"},
                    "objectId": "title_slide"
                }
            }
        ]

        response = batch_update_presentation(
            presentationId=self.presentation_id,
            requests=requests
        )

        # Validate response
        self.assertEqual(len(response['replies']), 1)
        reply = response['replies'][0]
        self.assertIn('createSlide', reply)
        self.assertEqual(reply['createSlide']['objectId'], "title_slide")

        # Verify slide was created
        updated_presentation = get_presentation(presentationId=self.presentation_id)
        self.assertEqual(len(updated_presentation['slides']), 2)

    def test_create_slide_with_title_and_body_layout(self):
        """Test creating a slide with TITLE_AND_BODY predefined layout."""
        
        requests = [
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "objectId": "title_body_slide"
                }
            }
        ]

        response = batch_update_presentation(
            presentationId=self.presentation_id,
            requests=requests
        )

        # Validate response
        self.assertEqual(len(response['replies']), 1)
        reply = response['replies'][0]
        self.assertIn('createSlide', reply)
        self.assertEqual(reply['createSlide']['objectId'], "title_body_slide")

        # Verify slide was created
        updated_presentation = get_presentation(presentationId=self.presentation_id)
        self.assertEqual(len(updated_presentation['slides']), 2)

    def test_create_multiple_slides_with_different_layouts(self):
        """Test creating multiple slides with different predefined layouts in one batch."""
        
        requests = [
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                    "objectId": "slide_blank"
                }
            },
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "TITLE"},
                    "objectId": "slide_title"
                }
            },
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "objectId": "slide_title_body"
                }
            },
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "SECTION_HEADER"},
                    "objectId": "slide_section_header"
                }
            },
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "BIG_NUMBER"},
                    "objectId": "slide_big_number"
                }
            }
        ]

        response = batch_update_presentation(
            presentationId=self.presentation_id,
            requests=requests
        )

        # Validate response structure
        self.assertEqual(len(response['replies']), 5)
        
        # Validate each slide creation reply
        expected_slide_ids = ["slide_blank", "slide_title", "slide_title_body", "slide_section_header", "slide_big_number"]
        for i, expected_id in enumerate(expected_slide_ids):
            reply = response['replies'][i]
            self.assertIn('createSlide', reply)
            self.assertEqual(reply['createSlide']['objectId'], expected_id)

        # Verify all slides were created
        updated_presentation = get_presentation(presentationId=self.presentation_id)
        self.assertEqual(len(updated_presentation['slides']), 6)  # 1 initial + 5 new slides

    def test_create_slide_with_invalid_predefined_layout(self):
        """Test creating a slide with an invalid predefined layout should raise an error."""
        
        requests = [
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "INVALID_LAYOUT"},
                    "objectId": "invalid_slide"
                }
            }
        ]

        # This should raise an error because the layout doesn't exist in the presentation
        with self.assertRaises(Exception) as context:
            batch_update_presentation(
                presentationId=self.presentation_id,
                requests=requests
            )
        
        # Verify the error message mentions the invalid layout
        error_message = str(context.exception)
        self.assertIn("INVALID_LAYOUT", error_message)

    def test_create_slide_with_predefined_layout_and_placeholder_mappings(self):
        """Test creating a slide with predefined layout and placeholder mappings."""
        
        requests = [
            {
                "createSlide": {
                    "placeholderIdMappings": [
                        {
                            "layoutPlaceholder": {"type": "TITLE", "index": 0},
                            "objectId": "custom_title"
                        },
                        {
                            "layoutPlaceholder": {"type": "BODY", "index": 0},
                            "objectId": "custom_body"
                        }
                    ],
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "objectId": "custom_mapped_slide"
                }
            }
        ]

        response = batch_update_presentation(
            presentationId=self.presentation_id,
            requests=requests
        )

        # Validate response
        self.assertEqual(len(response['replies']), 1)
        
        # Validate slide creation
        slide_reply = response['replies'][0]
        self.assertIn('createSlide', slide_reply)
        self.assertEqual(slide_reply['createSlide']['objectId'], "custom_mapped_slide")
        
        # Verify slide was created
        updated_presentation = get_presentation(presentationId=self.presentation_id)
        self.assertEqual(len(updated_presentation['slides']), 2)

    def test_create_slide_with_insertion_index(self):
        """Test creating a slide with specific insertion index."""
        
        requests = [
            {
                "createSlide": {
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                    "objectId": "inserted_slide",
                    "insertionIndex": 0  # Insert at the beginning
                }
            }
        ]

        response = batch_update_presentation(
            presentationId=self.presentation_id,
            requests=requests
        )

        # Validate response
        self.assertEqual(len(response['replies']), 1)
        reply = response['replies'][0]
        self.assertIn('createSlide', reply)
        self.assertEqual(reply['createSlide']['objectId'], "inserted_slide")

        # Verify slide was created at the correct position
        updated_presentation = get_presentation(presentationId=self.presentation_id)
        self.assertEqual(len(updated_presentation['slides']), 2)
        # The new slide should be at index 0 (first position)
        self.assertEqual(updated_presentation['slides'][0]['objectId'], "inserted_slide")

if __name__ == '__main__':
    unittest.main()
