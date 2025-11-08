from datetime import datetime
import uuid 

from google_slides.SimulationEngine.utils import _ensure_user 
from google_slides.SimulationEngine.custom_errors import InvalidInputError
from google_slides.SimulationEngine.custom_errors import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_slides.SimulationEngine.models import CreatePresentationRequest, Size, Dimension, PageModel, PageType
from google_slides.SimulationEngine.db import DB
from .. import create_presentation

class TestCreatePresentation(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self.DB = DB
        self.DB.clear()
        self.user_id = "me"
        
        # Initialize counters if tests depend on specific starting values for non-UUID counters
        # Ensure the user and their counters dictionary exist before trying to access specific counters
        if 'users' not in self.DB or self.user_id not in self.DB['users'] or 'counters' not in self.DB['users'][self.user_id]:
            _ensure_user(self.user_id)
        else: 
            if 'counters' not in self.DB['users'][self.user_id]:
                 # _ensure_user would have created this, but as a safeguard if user existed partially:
                self.DB['users'][self.user_id]['counters'] = {} 
            
            default_counters_for_test_logic = ['presentation', 'slide', 'pageElement', 'revision']
            for counter_name in default_counters_for_test_logic:
                 if counter_name not in self.DB['users'][self.user_id]['counters']:
                     self.DB['users'][self.user_id]['counters'][counter_name] = 0

    def _validate_uuid(self, id_string, id_name):
        try:
            uuid.UUID(str(id_string)) 
        except ValueError:
            self.fail(f"{id_name} '{id_string}' is not a valid UUID.")

    def _assert_successful_creation(self, response, expected_data=None):
        """Assert that a presentation was created successfully."""
        self.assertIsInstance(response, dict, "Response should be a dictionary.")

        # Validate presentationId
        self.assertIn("presentationId", response)
        self.assertIsInstance(response["presentationId"], str)
        
        # If a custom presentationId was provided, it should match exactly
        # If auto-generated, it should be a valid UUID
        if expected_data and expected_data.get("presentationId"):
            self.assertEqual(response["presentationId"], expected_data["presentationId"])
        else:
            # Auto-generated ID should be a valid UUID
            self._validate_uuid(response["presentationId"], "presentationId")

        # Title should match expected or be None
        self.assertIn("title", response)
        if expected_data and expected_data.get("title"):
            self.assertEqual(response["title"], expected_data["title"])

        # Page size should match expected or be None
        self.assertIn("pageSize", response)
        if expected_data and expected_data.get("pageSize"):
            self.assertIsInstance(response["pageSize"], dict)
        else:
            self.assertIsNone(response["pageSize"])

        # Slides should be a list
        self.assertIn("slides", response)
        self.assertIsInstance(response["slides"], list)

        # Masters should be a list
        self.assertIn("masters", response)
        self.assertIsInstance(response["masters"], list)

        # Layouts should be a list
        self.assertIn("layouts", response)
        self.assertIsInstance(response["layouts"], list)

        # notesMaster should match expected or be None
        self.assertIn("notesMaster", response)

        # locale should match expected or be None
        self.assertIn("locale", response)
        if expected_data and expected_data.get("locale"):
            self.assertEqual(response["locale"], expected_data["locale"])

        # revisionId should be a valid UUID
        self.assertIn("revisionId", response)
        self.assertIsInstance(response["revisionId"], str)
        self._validate_uuid(response["revisionId"], "revisionId")

        # Check DB structure
        presentation_id = response["presentationId"]
        self.assertIn(self.user_id, self.DB.get('users', {}), f"User '{self.user_id}' not found in DB.")
        user_data = self.DB['users'][self.user_id]
        self.assertIn('files', user_data, f"User '{self.user_id}' does not have 'files' entry in DB.")
        self.assertIn(presentation_id, user_data['files'], "Presentation not found in user's files in DB.")
        db_presentation_file = user_data['files'][presentation_id]

        self.assertEqual(db_presentation_file.get("id"), presentation_id)
        self.assertEqual(db_presentation_file.get("mimeType"), "application/vnd.google-apps.presentation")

        for time_field in ["createdTime", "modifiedTime"]:
            self.assertIn(time_field, db_presentation_file)
            self.assertIsInstance(db_presentation_file[time_field], str)
            try:
                datetime.fromisoformat(db_presentation_file[time_field].replace("Z", "+00:00"))
            except ValueError:
                self.fail(f"{time_field} '{db_presentation_file[time_field]}' is not a valid ISO 8601 Z-offset timestamp string.")

    # Basic creation tests
    def test_create_presentation_with_only_title(self):
        """Test creating presentation with only title provided."""
        request = {"title": "My First Presentation"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], "My First Presentation")
        self.assertEqual(response["slides"], [])
        self.assertEqual(response["masters"], [])
        self.assertEqual(response["layouts"], [])
        self.assertIsNone(response["pageSize"])
        self.assertIsNone(response["notesMaster"])
        self.assertIsNone(response["locale"])

    def test_create_presentation_with_provided_id(self):
        """Test creating presentation with a specific presentationId."""
        custom_id = "my-custom-presentation-id"
        request = {"presentationId": custom_id, "title": "Custom ID Presentation"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["presentationId"], custom_id)
        self.assertEqual(response["title"], "Custom ID Presentation")

    def test_create_presentation_with_page_size(self):
        """Test creating presentation with custom page size."""
        page_size = {
            "width": {"magnitude": 800.0, "unit": "PT"},
            "height": {"magnitude": 600.0, "unit": "PT"}
        }
        request = {"title": "Custom Size Presentation", "pageSize": page_size}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], "Custom Size Presentation")
        self.assertIsNotNone(response["pageSize"])
        self.assertEqual(response["pageSize"]["width"]["magnitude"], 800.0)
        self.assertEqual(response["pageSize"]["width"]["unit"], "PT")
        self.assertEqual(response["pageSize"]["height"]["magnitude"], 600.0)
        self.assertEqual(response["pageSize"]["height"]["unit"], "PT")

    def test_create_presentation_with_locale(self):
        """Test creating presentation with custom locale."""
        request = {"title": "Localized Presentation", "locale": "fr-FR"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], "Localized Presentation")
        self.assertEqual(response["locale"], "fr-FR")

    def test_create_presentation_minimal_title_only(self):
        """Test creating presentation with minimal data - just one character title."""
        request = {"title": "A"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], "A")

    def test_create_presentation_all_fields_none_except_title(self):
        """Test creating presentation where only title is provided, all others explicit None."""
        request = {"title": "Only Title"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], "Only Title")

    def test_create_presentation_with_special_chars_in_title(self):
        """Test creating presentation with special characters in title."""
        title = "Presentation: Test with !@#$%^&*()_+-=[]{};':\",./<>? and unicode 🚀"
        request = {"title": title}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], title)

    def test_create_presentation_with_max_length_title(self):
        """Test creating presentation with maximum allowed title length."""
        title = "a" * 1000  # Max length as defined in CreatePresentationRequest
        request = {"title": title}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], title)

    def test_create_presentation_title_with_leading_trailing_spaces(self):
        """Test creating presentation with title having leading/trailing spaces."""
        title_with_spaces = "   My Presentation with Spaces   "
        request = {"title": title_with_spaces}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], title_with_spaces)

    def test_create_multiple_presentations_success(self):
        """Test creating multiple presentations with unique IDs."""
        # First presentation
        request1 = {"title": "Presentation One"}
        response1 = create_presentation(request1)
        self._assert_successful_creation(response1, request1)
        presentation_id1 = response1["presentationId"]

        # Second presentation
        request2 = {"title": "Presentation Two"}
        response2 = create_presentation(request2)
        self._assert_successful_creation(response2, request2)
        presentation_id2 = response2["presentationId"]

        # Ensure IDs are different
        self.assertNotEqual(presentation_id1, presentation_id2, "Presentation IDs should be unique.")
        self.assertIn(presentation_id1, self.DB['users'][self.user_id]['files'])
        self.assertIn(presentation_id2, self.DB['users'][self.user_id]['files'])

    # Error handling tests
    def test_create_presentation_invalid_request_type(self):
        """Test creating presentation with invalid request type."""
        self.assert_error_behavior(
            func_to_call=create_presentation,
            expected_exception_type=InvalidInputError,
            expected_message="Request must be a dictionary.",
            request="invalid_request"
        )

    def test_create_presentation_no_fields_provided(self):
        """Test creating presentation with no fields provided (should fail validation)."""
        self.assert_error_behavior(
            func_to_call=create_presentation,
            expected_exception_type=InvalidInputError,
            expected_message="At least one field must be provided in the create presentation request.",
            request={}
        )

    def test_create_presentation_title_too_long(self):
        """Test creating presentation with title exceeding maximum length."""
        with self.assertRaises(InvalidInputError) as context:
            create_presentation({"title": "a" * 1001})
        self.assertIn("Request validation", str(context.exception))
       

    def test_create_presentation_empty_title(self):
        """Test creating presentation with empty title."""
        with self.assertRaises(InvalidInputError) as context:
            create_presentation({"title": ""})
        self.assertIn("Request validation failed", str(context.exception))

    def test_create_presentation_with_duplicate_id(self):
        """Test creating presentation with duplicate presentationId."""
        custom_id = "duplicate-id"
        
        # First presentation with custom ID
        request1 = {"presentationId": custom_id, "title": "First Presentation"}
        response1 = create_presentation(request1)
        self._assert_successful_creation(response1, request1)
        
        # Second presentation with same ID should fail
        request2 = {"presentationId": custom_id, "title": "Second Presentation"}
        self.assert_error_behavior(
            func_to_call=create_presentation,
            expected_exception_type=InvalidInputError,
            expected_message=f"A presentation with ID '{custom_id}' already exists.",
            request=request2
        )

    def test_create_presentation_revisionId_ignored(self):
        """Test that revisionId in request is ignored (output-only field)."""
        ignored_revision_id = "ignored-revision"
        request = {"title": "Test Presentation", "revisionId": ignored_revision_id}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        
        # The returned revisionId should be different (generated, not the provided one)
        self.assertNotEqual(response["revisionId"], ignored_revision_id)
        self._validate_uuid(response["revisionId"], "revisionId")

    def test_create_presentation_with_only_locale(self):
        """Test creating presentation with only locale provided."""
        request = {"locale": "en-US"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["locale"], "en-US")
        self.assertIsNone(response["title"])

    def test_create_presentation_with_only_page_size(self):
        """Test creating presentation with only page size provided."""
        page_size = {
            "width": {"magnitude": 1024.0, "unit": "PT"},
            "height": {"magnitude": 768.0, "unit": "PT"}
        }
        request = {"pageSize": page_size}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertIsNotNone(response["pageSize"])
        self.assertIsNone(response["title"])

    def test_create_presentation_with_only_presentation_id(self):
        """Test creating presentation with only presentationId provided."""
        custom_id = "only-id-provided"
        request = {"presentationId": custom_id}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["presentationId"], custom_id)
        self.assertIsNone(response["title"])

    def test_create_presentation_complex_combination(self):
        """Test creating presentation with multiple fields provided."""
        custom_id = "complex-presentation"
        page_size = {
            "width": {"magnitude": 1920.0, "unit": "PT"},
            "height": {"magnitude": 1080.0, "unit": "PT"}
        }
        request = {
            "presentationId": custom_id,
            "title": "Complex Presentation",
            "pageSize": page_size,
            "locale": "es-ES",
            "slides": [],  # Empty lists are valid
            "masters": [],
            "layouts": []
        }
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["presentationId"], custom_id)
        self.assertEqual(response["title"], "Complex Presentation")
        self.assertEqual(response["locale"], "es-ES")
        self.assertIsNotNone(response["pageSize"])
        self.assertEqual(response["slides"], [])
        self.assertEqual(response["masters"], [])
        self.assertEqual(response["layouts"], [])

    def test_create_presentation_with_all_new_page_element_types(self):
        """Test that new page element types work correctly in the models."""
        # This test ensures our new models (Image, Video, Table, etc.) are properly integrated
        from google_slides.SimulationEngine.models import Image, Video, Table, TableRow, Line, WordArt, SpeakerSpotlight
        
        # Test that we can create instances of the new models
        image = Image(contentUrl="https://example.com/image.jpg")
        video = Video(url="https://youtube.com/watch?v=123", source="YOUTUBE")
        table = Table(rows=2, columns=3)
        line = Line(lineType="STRAIGHT_CONNECTOR_1", lineCategory="STRAIGHT")
        word_art = WordArt(renderedText="Hello World")
        speaker_spotlight = SpeakerSpotlight()
        
        # These objects should be creatable without errors
        self.assertEqual(image.contentUrl, "https://example.com/image.jpg")
        self.assertEqual(video.source, "YOUTUBE")
        self.assertEqual(table.rows, 2)
        self.assertEqual(line.lineCategory, "STRAIGHT")
        self.assertEqual(word_art.renderedText, "Hello World")
        self.assertIsNotNone(speaker_spotlight)

        # Test create presentation with title to ensure everything still works
        request = {"title": "Model Integration Test"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], "Model Integration Test")

    def test_create_presentation_model_validation_failure(self):
        """Test creating presentation when PresentationModel validation fails."""
        import unittest.mock
        
        request = {"title": "Model Validation Failure Test"}
        
        # Mock PresentationModel to raise a validation error
        with unittest.mock.patch('google_slides.presentations.PresentationModel', 
                                 side_effect=ValueError("Model validation failed")):
            self.assert_error_behavior(
                func_to_call=create_presentation,
                expected_exception_type=InvalidInputError,
                expected_message="Failed to create presentation model: Model validation failed",
                request=request
            )

    def test_create_presentation_with_mock_ensure_file_failure(self):
        """Test creating presentation when _ensure_presentation_file fails."""
        import unittest.mock
        
        request = {"title": "File Storage Failure Test"}
        
        # Mock _ensure_presentation_file to raise an exception
        with unittest.mock.patch('google_slides.SimulationEngine.utils._ensure_presentation_file', 
                                 side_effect=Exception("Storage failure")):
            self.assert_error_behavior(
                func_to_call=create_presentation,
                expected_exception_type=InvalidInputError,
                expected_message="Failed to store presentation: Storage failure",
                request=request
            )

    def test_create_presentation_with_dict_input_original_use_case(self):
        """Test creating presentation with dictionary input - the original use case that was failing."""
        request = {"title": "Integration Test Presentation"}
        response = create_presentation(request)
        self._assert_successful_creation(response, request)
        self.assertEqual(response["title"], "Integration Test Presentation")
        self.assertEqual(response["slides"], [])
        self.assertEqual(response["masters"], [])
        self.assertEqual(response["layouts"], [])
        self.assertIsNone(response["pageSize"])
        self.assertIsNone(response["notesMaster"])
        self.assertIsNone(response["locale"])