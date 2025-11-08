import unittest
import pytest
from pydantic import ValidationError
from ..SimulationEngine.models import (
    MessageUpdateModel,
    MessageContentModel,
    MessagePayloadModel
)


class TestTimestampValidation(unittest.TestCase):
    """Test cases for timestamp validation in Gmail API models."""
    
    def test_valid_millisecond_timestamp(self):
        """Test that valid millisecond timestamps are accepted."""
        # Valid 13-digit millisecond timestamp (year 2024)
        valid_timestamp = "1705123456789"
        
        # Test MessageUpdateModel
        model = MessageUpdateModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
        
        # Test MessageContentModel
        model = MessageContentModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
        
        # Test MessagePayloadModel
        model = MessagePayloadModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
    
    def test_valid_millisecond_timestamp_old_date(self):
        """Test that valid millisecond timestamps for old dates are accepted."""
        # Valid 13-digit millisecond timestamp (year 2001)
        valid_timestamp = "1000000000000"
        
        # Test MessageUpdateModel
        model = MessageUpdateModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
        
        # Test MessageContentModel
        model = MessageContentModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
        
        # Test MessagePayloadModel
        model = MessagePayloadModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
    
    def test_valid_millisecond_timestamp_future_date(self):
        """Test that valid millisecond timestamps for future dates are accepted."""
        # Valid 13-digit millisecond timestamp (year 2030)
        valid_timestamp = "1893456000000"
        
        # Test MessageUpdateModel
        model = MessageUpdateModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
        
        # Test MessageContentModel
        model = MessageContentModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
        
        # Test MessagePayloadModel
        model = MessagePayloadModel(internalDate=valid_timestamp)
        self.assertEqual(model.internalDate, valid_timestamp)
    
    def test_seconds_timestamp_rejected(self):
        """Test that second-based timestamps are rejected with appropriate error message."""
        # Invalid 10-digit second timestamp (year 2024)
        invalid_timestamp = "1705123456"
        expected_error = f"internalDate '{invalid_timestamp}' appears to be in seconds, but must be in milliseconds. Expected a 13-digit timestamp (e.g., 1705123456789), got 10 digits."
        
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate=invalid_timestamp)
        self.assertIn(expected_error, str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate=invalid_timestamp)
        self.assertIn(expected_error, str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate=invalid_timestamp)
        self.assertIn(expected_error, str(cm.exception))
    
    def test_seconds_timestamp_old_date(self):
        """Test that old second-based timestamps are rejected."""
        # Invalid 10-digit second timestamp (year 2000)
        invalid_timestamp = "946684800"
        expected_error = f"internalDate '{invalid_timestamp}' appears to be in seconds, but must be in milliseconds. Expected a 13-digit timestamp (e.g., 1705123456789), got 9 digits."
        
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate=invalid_timestamp)
        self.assertIn(expected_error, str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate=invalid_timestamp)
        self.assertIn(expected_error, str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate=invalid_timestamp)
        self.assertIn(expected_error, str(cm.exception))
    
    def test_none_timestamp_accepted(self):
        """Test that None timestamps are accepted."""
        # Test MessageUpdateModel
        model = MessageUpdateModel(internalDate=None)
        self.assertIsNone(model.internalDate)
        
        # Test MessageContentModel
        model = MessageContentModel(internalDate=None)
        self.assertIsNone(model.internalDate)
        
        # Test MessagePayloadModel
        model = MessagePayloadModel(internalDate=None)
        self.assertIsNone(model.internalDate)
    
    def test_empty_string_timestamp_rejected(self):
        """Test that empty string timestamps are rejected."""
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate="")
        self.assertIn("internalDate '' must be a valid numeric timestamp in milliseconds", str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate="")
        self.assertIn("internalDate '' must be a valid numeric timestamp in milliseconds", str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate="")
        self.assertIn("internalDate '' must be a valid numeric timestamp in milliseconds", str(cm.exception))
    
    def test_non_numeric_string_rejected(self):
        """Test that non-numeric string timestamps are rejected."""
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate="not_a_number")
        self.assertIn("internalDate 'not_a_number' must be a valid numeric timestamp in milliseconds", str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate="not_a_number")
        self.assertIn("internalDate 'not_a_number' must be a valid numeric timestamp in milliseconds", str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate="not_a_number")
        self.assertIn("internalDate 'not_a_number' must be a valid numeric timestamp in milliseconds", str(cm.exception))
    
    def test_float_timestamp_accepted(self):
        """Test that float timestamps are accepted."""
        # Valid 13-digit millisecond timestamp as float
        valid_timestamp = 1705123456789.0
        
        # Test MessageUpdateModel
        model = MessageUpdateModel(internalDate=str(valid_timestamp))
        self.assertEqual(model.internalDate, str(valid_timestamp))
        
        # Test MessageContentModel
        model = MessageContentModel(internalDate=str(valid_timestamp))
        self.assertEqual(model.internalDate, str(valid_timestamp))
        
        # Test MessagePayloadModel
        model = MessagePayloadModel(internalDate=str(valid_timestamp))
        self.assertEqual(model.internalDate, str(valid_timestamp))
    
    def test_edge_case_threshold_timestamp(self):
        """Test edge case around the threshold value."""
        # Just below threshold (should be rejected)
        below_threshold = "999999999999"  # 13 digits but below 1000000000000
        expected_error = f"internalDate '{below_threshold}' appears to be in seconds, but must be in milliseconds. Expected a 13-digit timestamp (e.g., 1705123456789), got 12 digits."
        
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate=below_threshold)
        self.assertIn(expected_error, str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate=below_threshold)
        self.assertIn(expected_error, str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate=below_threshold)
        self.assertIn(expected_error, str(cm.exception))
        
        # Just at threshold (should be accepted)
        at_threshold = "1000000000000"
        
        # Test MessageUpdateModel
        model = MessageUpdateModel(internalDate=at_threshold)
        self.assertEqual(model.internalDate, at_threshold)
        
        # Test MessageContentModel
        model = MessageContentModel(internalDate=at_threshold)
        self.assertEqual(model.internalDate, at_threshold)
        
        # Test MessagePayloadModel
        model = MessagePayloadModel(internalDate=at_threshold)
        self.assertEqual(model.internalDate, at_threshold)
    
    def test_very_large_timestamp_accepted(self):
        """Test that very large millisecond timestamps are accepted."""
        # Very large 13-digit millisecond timestamp (year 2100+)
        large_timestamp = "4102444800000"
        
        # Test MessageUpdateModel
        model = MessageUpdateModel(internalDate=large_timestamp)
        self.assertEqual(model.internalDate, large_timestamp)
        
        # Test MessageContentModel
        model = MessageContentModel(internalDate=large_timestamp)
        self.assertEqual(model.internalDate, large_timestamp)
        
        # Test MessagePayloadModel
        model = MessagePayloadModel(internalDate=large_timestamp)
        self.assertEqual(model.internalDate, large_timestamp)
    
    def test_whitespace_string_rejected(self):
        """Test that whitespace-only string timestamps are rejected."""
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate="   ")
        self.assertIn("internalDate '   ' must be a valid numeric timestamp in milliseconds", str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate="   ")
        self.assertIn("internalDate '   ' must be a valid numeric timestamp in milliseconds", str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate="   ")
        self.assertIn("internalDate '   ' must be a valid numeric timestamp in milliseconds", str(cm.exception))
    
    def test_negative_timestamp_rejected(self):
        """Test that negative timestamps are rejected."""
        # Negative timestamp
        negative_timestamp = "-1705123456789"
        
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate=negative_timestamp)
        self.assertIn("internalDate '-1705123456789' appears to be in seconds, but must be in milliseconds", str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate=negative_timestamp)
        self.assertIn("internalDate '-1705123456789' appears to be in seconds, but must be in milliseconds", str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate=negative_timestamp)
        self.assertIn("internalDate '-1705123456789' appears to be in seconds, but must be in milliseconds", str(cm.exception))
    
    def test_zero_timestamp_rejected(self):
        """Test that zero timestamp is rejected."""
        # Zero timestamp
        zero_timestamp = "0"
        
        # Test MessageUpdateModel
        with self.assertRaises(ValidationError) as cm:
            MessageUpdateModel(internalDate=zero_timestamp)
        self.assertIn("internalDate '0' appears to be in seconds, but must be in milliseconds", str(cm.exception))
        
        # Test MessageContentModel
        with self.assertRaises(ValidationError) as cm:
            MessageContentModel(internalDate=zero_timestamp)
        self.assertIn("internalDate '0' appears to be in seconds, but must be in milliseconds", str(cm.exception))
        
        # Test MessagePayloadModel
        with self.assertRaises(ValidationError) as cm:
            MessagePayloadModel(internalDate=zero_timestamp)
        self.assertIn("internalDate '0' appears to be in seconds, but must be in milliseconds", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
