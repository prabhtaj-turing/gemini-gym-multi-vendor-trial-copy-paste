import pytest
from youtube.SimulationEngine.db import DB
from youtube.Videos import upload
from youtube.SimulationEngine.utils import generate_entity_id
import datetime
from pydantic import ValidationError

import unittest
from youtube.SimulationEngine.error_handling import get_package_error_mode
from pydantic import ValidationError



class BaseTestCaseWithErrorHandler(unittest.TestCase): # Or any TestCase subclass

    def assert_error_behavior(self,
                              func_to_call,
                              expected_exception_type, # The actual exception class, e.g., ValueError
                              expected_message,
                              # You can pass other specific key-value pairs expected
                              # in the dictionary (besides 'exceptionType' and 'message').
                              additional_expected_dict_fields=None,
                              *func_args, **func_kwargs):
        """
        Utility function to test error handling based on the global ERROR_MODE.

        Args:
            self: The TestCase instance.
            func_to_call: The function that might raise an error or return an error dict.
            expected_exception_type (type): The Python class of the exception (e.g., ValueError).
            expected_message (str): The expected error message.
            additional_expected_dict_fields (dict, optional): A dictionary of other
                key-value pairs expected in the error dictionary.
            *func_args: Positional arguments to pass to func_to_call.
            **func_kwargs: Keyword arguments to pass to func_to_call.
        """

        try:
            current_error_mode = get_package_error_mode()
        except NameError:
            self.fail("Global variable ERROR_MODE is not defined. Ensure it's in scope and set.")
            return # Stop further execution of this utility
        if current_error_mode == "raise":
            with self.assertRaises(expected_exception_type) as context:
                func_to_call(*func_args, **func_kwargs)
            if isinstance(context.exception, ValidationError):
                assert expected_message in str(context.exception)
            else:
                self.assertEqual(str(context.exception), expected_message)
        elif current_error_mode == "error_dict":
            result = func_to_call(*func_args, **func_kwargs)

            self.assertIsInstance(result, dict,
                                  f"Function should return a dictionary when ERROR_MODE is 'error_dict'. Got: {type(result)}")

            # Verify the 'exceptionType' field
            self.assertEqual(result.get("exceptionType"), expected_exception_type.__name__,
                             f"Error dictionary 'exceptionType' mismatch. Expected: '{expected_exception_type.__name__}', "
                             f"Got: '{result.get('exceptionType')}'")
            if expected_message:
                self.assertEqual(result.get("message"), expected_message,
                                f"Error dictionary 'message' mismatch. Expected: '{expected_message}', "
                                f"Got: '{result.get('message')}'")

            # Verify any other specified fields in the dictionary
            if additional_expected_dict_fields:
                for key, expected_value in additional_expected_dict_fields.items():
                    self.assertEqual(result.get(key), expected_value,
                                     f"Error dictionary field '{key}' mismatch. Expected: '{expected_value}', "
                                     f"Got: '{result.get(key)}'")
        else:
            self.fail(f"Invalid global ERROR_MODE value: '{current_error_mode}'. "
                      "Expected 'raise' or 'error_dict'.")
                      
class TestVideoUpload(BaseTestCaseWithErrorHandler):
    def setUp(self):
        DB.clear()
        DB["videos"] = {}
        DB["channels"] = {
            "UC_x5XG1OV2P6uZZ5FSM9Ttw": {
                    "forUsername": "Test Channel"
                }
            }
        DB["videoCategories"] = {
            "22": {}
        }


    def test_upload_video_success(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "22",
                "channelId": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "channelTitle": "Test Channel",
                "thumbnails": {
                    "default": {"url": "https://example.com/default.jpg", "width": 120, "height": 90},
                    "medium": {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
                    "high": {"url": "https://example.com/high.jpg", "width": 480, "height": 360}
                }
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        }

        response = upload(body)

        assert "id" in response
        video_id = response["id"]
        assert video_id in DB["videos"]

        stored_video = DB["videos"][video_id]
        assert stored_video["snippet"]["title"] == "Test Video"
        assert stored_video["status"]["privacyStatus"] == "public"
        assert "statistics" in stored_video
        assert stored_video["statistics"]["viewCount"] == 0
        assert "publishedAt" in stored_video["snippet"]

    def test_upload_video_missing_body(self):
        self.assert_error_behavior(upload, ValueError,
         "The 'body' parameter is required.", body=None)

    def test_upload_video_invalid_body_type(self):
        self.assert_error_behavior(upload, TypeError, "The 'body' parameter must be a dictionary.",
         body="not a dict")

    def test_upload_video_channel_not_found(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "22",
                "channelId": "invalid_channel",
                "channelTitle": "Test Channel",
                "thumbnails": {
                    "default": {"url": "https://example.com/default.jpg", "width": 120, "height": 90},
                    "medium": {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
                    "high": {"url": "https://example.com/high.jpg", "width": 480, "height": 360}
                }
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        }
        self.assert_error_behavior(upload, ValueError, "Channel not found", body=body)

    def test_upload_video_category_not_found(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "invalid_category",
                "channelId": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "channelTitle": "Test Channel",
                "thumbnails": {
                    "default": {"url": "https://example.com/default.jpg", "width": 120, "height": 90},
                    "medium": {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
                    "high": {"url": "https://example.com/high.jpg", "width": 480, "height": 360}
                }
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        }
        self.assert_error_behavior(upload, ValueError, "Category not found", body=body)

    def test_upload_video_channel_title_mismatch(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "22",
                "channelId": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "channelTitle": "Wrong Channel Title",
                "thumbnails": {
                    "default": {"url": "https://example.com/default.jpg", "width": 120, "height": 90},
                    "medium": {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
                    "high": {"url": "https://example.com/high.jpg", "width": 480, "height": 360}
                }
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        }
        self.assert_error_behavior(upload, ValueError, "Channel title does not match the channel title in the DB.", body=body)

    def test_upload_video_invalid_upload_status(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "22",
                "channelId": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "channelTitle": "Test Channel",
                "thumbnails": {
                    "default": {"url": "https://example.com/default.jpg", "width": 120, "height": 90},
                    "medium": {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
                    "high": {"url": "https://example.com/high.jpg", "width": 480, "height": 360}
                }
            },
            "status": {
                "uploadStatus": "invalid_status",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        }
        self.assert_error_behavior(upload, ValueError, "Invalid upload status", body=body)

    def test_upload_video_invalid_privacy_status(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "22",
                "channelId": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "channelTitle": "Test Channel",
                "thumbnails": {
                    "default": {"url": "https://example.com/default.jpg", "width": 120, "height": 90},
                    "medium": {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
                    "high": {"url": "https://example.com/high.jpg", "width": 480, "height": 360}
                }
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "invalid_status",
                "embeddable": True,
                "madeForKids": False
            }
        }
        self.assert_error_behavior(upload, ValueError, "Invalid privacy status", body=body)

    def test_upload_video_invalid_body_structure(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "22",
                "channelId": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "channelTitle": "Test Channel", 
            },
            "new_key": "new_value"
        }
        with self.assertRaises(ValidationError):
            upload(body)

    def test_upload_video_invalid_snippet_structure(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "wrong_key": "wrong_value"
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        }
        with self.assertRaises(ValidationError):
            upload(body)

    def test_upload_video_invalid_status_structure(self):
        body = {
            "snippet": {
                "title": "Test Video",
                "description": "This is a test video.",
                "tags": ["test", "video"],
                "categoryId": "22",
                "channelId": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "channelTitle": "Test Channel",
                "thumbnails": {
                    "default": {"url": "https://example.com/default.jpg", "width": 120, "height": 90},
                    "medium": {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
                    "high": {"url": "https://example.com/high.jpg", "width": 480, "height": 360}
                }
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": "incorrect_value",
                "madeForKids": False
            }
        }
        with self.assertRaises(ValidationError):
            upload(body)