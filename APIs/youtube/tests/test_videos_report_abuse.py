import unittest
from unittest.mock import patch
from youtube.Videos import report_abuse
from youtube.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

import datetime


class TestVideosReportAbuse(BaseTestCaseWithErrorHandler):
    """Test cases for the Videos.report_abuse function."""

    def setUp(self):
        """Reset the database before each test."""
        DB.clear()
        DB.update({
            "videos": {
                "video1": {
                    "id": "video1",
                    "snippet": {
                        "title": "Test Video 1",
                        "description": "A test video for abuse reporting",
                        "channelTitle": "Test Channel"
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "50",
                        "dislikeCount": "5"
                    }
                },
                "video2": {
                    "id": "video2",
                    "snippet": {
                        "title": "Test Video 2",
                        "description": "Another test video",
                        "channelTitle": "Another Channel"
                    },
                    "statistics": {
                        "viewCount": "500",
                        "likeCount": "25",
                        "dislikeCount": "2"
                    }
                }
            }
        })

    def test_report_abuse_success_basic(self):
        """Test successful abuse report with minimal required parameters."""
        result = report_abuse(
            video_id="video1",
            reason_id="spam"
        )
        
        self.assertEqual(result["success"], True)
        self.assertIn("abuse_reports", DB)
        self.assertEqual(len(DB["abuse_reports"]), 1)
        
        report = DB["abuse_reports"][0]
        self.assertEqual(report["video_id"], "video1")
        self.assertEqual(report["reason_id"], "spam")
        self.assertIsNone(report["on_behalf_of_content_owner"])
        self.assertIsNone(report["secondary_reason_id"])
        self.assertIsNone(report["comments"])
        self.assertIsNone(report["language"])
        self.assertIn("timestamp", report)

    def test_report_abuse_success_with_all_parameters(self):
        """Test successful abuse report with all parameters."""
        result = report_abuse(
            video_id="video2",
            reason_id="violence",
            on_behalf_of_content_owner="content_owner_123",
            secondary_reason_id="graphic_violence",
            comments="This video contains inappropriate content",
            language="en"
        )
        
        self.assertEqual(result["success"], True)
        self.assertIn("abuse_reports", DB)
        self.assertEqual(len(DB["abuse_reports"]), 1)
        
        report = DB["abuse_reports"][0]
        self.assertEqual(report["video_id"], "video2")
        self.assertEqual(report["reason_id"], "violence")
        self.assertEqual(report["on_behalf_of_content_owner"], "content_owner_123")
        self.assertEqual(report["secondary_reason_id"], "graphic_violence")
        self.assertEqual(report["comments"], "This video contains inappropriate content")
        self.assertEqual(report["language"], "en")
        self.assertIn("timestamp", report)

    def test_report_abuse_multiple_reports(self):
        """Test multiple abuse reports for the same video."""
        # First report
        result1 = report_abuse(
            video_id="video1",
            reason_id="spam"
        )
        self.assertEqual(result1["success"], True)
        
        # Second report
        result2 = report_abuse(
            video_id="video1",
            reason_id="violence",
            comments="Second report"
        )
        self.assertEqual(result2["success"], True)
        
        self.assertEqual(len(DB["abuse_reports"]), 2)
        
        # Check both reports are stored
        reports = DB["abuse_reports"]
        self.assertEqual(reports[0]["reason_id"], "spam")
        self.assertEqual(reports[1]["reason_id"], "violence")
        self.assertEqual(reports[1]["comments"], "Second report")

    def test_report_abuse_video_not_found(self):
        """Test reporting abuse for a non-existent video."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=ValueError,
            expected_message="Video not found",
            video_id="nonexistent_video",
            reason_id="spam"
        )

    def test_report_abuse_missing_video_id(self):
        """Test that missing video_id raises ValueError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=ValueError,
            expected_message="video_id is required",
            video_id="",
            reason_id="spam"
        )

    def test_report_abuse_none_video_id(self):
        """Test that None video_id raises ValueError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=ValueError,
            expected_message="video_id is required",
            video_id=None,
            reason_id="spam"
        )

    def test_report_abuse_invalid_video_id_type(self):
        """Test that non-string video_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=TypeError,
            expected_message="video_id must be a string",
            video_id=123,
            reason_id="spam"
        )

    def test_report_abuse_missing_reason_id(self):
        """Test that missing reason_id raises ValueError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=ValueError,
            expected_message="reason_id is required",
            video_id="video1",
            reason_id=""
        )

    def test_report_abuse_none_reason_id(self):
        """Test that None reason_id raises ValueError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=ValueError,
            expected_message="reason_id is required",
            video_id="video1",
            reason_id=None
        )

    def test_report_abuse_invalid_reason_id_type(self):
        """Test that non-string reason_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=TypeError,
            expected_message="reason_id must be a string",
            video_id="video1",
            reason_id=123
        )

    def test_report_abuse_invalid_on_behalf_of_content_owner_type(self):
        """Test that non-string on_behalf_of_content_owner raises TypeError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=TypeError,
            expected_message="on_behalf_of_content_owner must be a string",
            video_id="video1",
            reason_id="spam",
            on_behalf_of_content_owner=123
        )

    def test_report_abuse_invalid_secondary_reason_id_type(self):
        """Test that non-string secondary_reason_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=TypeError,
            expected_message="secondary_reason_id must be a string",
            video_id="video1",
            reason_id="spam",
            secondary_reason_id=123
        )

    def test_report_abuse_invalid_comments_type(self):
        """Test that non-string comments raises TypeError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=TypeError,
            expected_message="comments must be a string",
            video_id="video1",
            reason_id="spam",
            comments=123
        )

    def test_report_abuse_invalid_language_type(self):
        """Test that non-string language raises TypeError."""
        self.assert_error_behavior(
            func_to_call=report_abuse,
            expected_exception_type=TypeError,
            expected_message="language must be a string",
            video_id="video1",
            reason_id="spam",
            language=123
        )

    def test_report_abuse_timestamp_format(self):
        """Test that the timestamp is properly formatted."""
        result = report_abuse(
            video_id="video1",
            reason_id="spam"
        )
        
        self.assertEqual(result["success"], True)
        report = DB["abuse_reports"][0]
        
        # Check timestamp format (ISO format ending with Z)
        timestamp = report["timestamp"]
        self.assertIsInstance(timestamp, str)
        self.assertTrue(timestamp.endswith("Z"))
        
        # Verify it's a valid ISO timestamp
        try:
            datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")

    def test_report_abuse_preserves_existing_reports(self):
        """Test that new reports don't overwrite existing ones."""
        # Add an existing report
        DB["abuse_reports"] = [{
            "video_id": "video2",
            "reason_id": "existing_reason",
            "timestamp": "2023-01-01T00:00:00Z"
        }]
        
        # Add a new report
        result = report_abuse(
            video_id="video1",
            reason_id="new_reason"
        )
        
        self.assertEqual(result["success"], True)
        self.assertEqual(len(DB["abuse_reports"]), 2)
        
        # Check that both reports exist
        reports = DB["abuse_reports"]
        existing_report = next(r for r in reports if r["reason_id"] == "existing_reason")
        new_report = next(r for r in reports if r["reason_id"] == "new_reason")
        
        self.assertEqual(existing_report["video_id"], "video2")
        self.assertEqual(new_report["video_id"], "video1")

    def test_report_abuse_with_special_characters(self):
        """Test abuse report with special characters in parameters."""
        result = report_abuse(
            video_id="video1",
            reason_id="spam",
            comments="Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            language="en-US"
        )
        
        self.assertEqual(result["success"], True)
        report = DB["abuse_reports"][0]
        self.assertEqual(report["comments"], "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?")
        self.assertEqual(report["language"], "en-US")

    def test_report_abuse_empty_string_optional_params(self):
        """Test abuse report with empty strings for optional parameters."""
        result = report_abuse(
            video_id="video1",
            reason_id="spam",
            on_behalf_of_content_owner="",
            secondary_reason_id="",
            comments="",
            language=""
        )
        
        self.assertEqual(result["success"], True)
        report = DB["abuse_reports"][0]
        self.assertEqual(report["on_behalf_of_content_owner"], "")
        self.assertEqual(report["secondary_reason_id"], "")
        self.assertEqual(report["comments"], "")
        self.assertEqual(report["language"], "")


if __name__ == "__main__":
    unittest.main() 