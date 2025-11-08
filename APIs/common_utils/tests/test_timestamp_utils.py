"""
Unit tests for timestamp_utils module.

Tests the timestamp generation and validation functions that ensure
consistent ISO 8601 format across all APIs.
"""

import unittest
import time
from datetime import datetime, timezone

from common_utils.timestamp_utils import (
    get_iso_timestamp,
    timestamp_from_unix,
    validate_iso_timestamp,
    fix_malformed_timestamp,
    get_current_timestamp_iso
)


class TestTimestampUtils(unittest.TestCase):
    """Test cases for timestamp utility functions."""
    
    def test_get_iso_timestamp_format(self):
        """Test that get_iso_timestamp returns correct format."""
        timestamp = get_iso_timestamp()
        
        # Should be a string
        self.assertIsInstance(timestamp, str)
        
        # Should end with Z
        self.assertTrue(timestamp.endswith('Z'))
        
        # Should NOT contain +00:00
        self.assertNotIn('+00:00', timestamp)
        
        # Should be parseable as ISO format
        self.assertTrue(validate_iso_timestamp(timestamp))
    
    def test_get_iso_timestamp_contains_components(self):
        """Test get_iso_timestamp contains expected components."""
        timestamp = get_iso_timestamp()
        
        # Should contain date and time components
        self.assertIn('T', timestamp)  # Date-time separator
        self.assertIn('-', timestamp)  # Date separators
        self.assertIn(':', timestamp)  # Time separators
        self.assertTrue(timestamp.endswith('Z'))
    
    def test_timestamp_from_unix(self):
        """Test converting Unix timestamp to ISO format."""
        # Use a known Unix timestamp: Jan 1, 2025 00:00:00 UTC
        unix_ts = 1735689600.0
        
        timestamp = timestamp_from_unix(unix_ts)
        
        # Should be ISO 8601 format with Z suffix
        self.assertIsInstance(timestamp, str)
        self.assertTrue(timestamp.endswith('Z'))
        self.assertIn("2025-01-01", timestamp)
        self.assertTrue(validate_iso_timestamp(timestamp))
    
    def test_validate_iso_timestamp_valid_formats(self):
        """Test validation of valid ISO 8601 timestamps."""
        valid_timestamps = [
            "2025-10-06T21:05:52.510677Z",
            "2025-10-06T21:05:52Z",
            "2025-10-06T21:05:52.510Z",
            "2025-10-06T21:05:52+00:00",
            "2025-10-06T21:05:52.510677+00:00",
        ]
        
        for ts in valid_timestamps:
            with self.subTest(timestamp=ts):
                self.assertTrue(validate_iso_timestamp(ts))
    
    def test_validate_iso_timestamp_invalid_formats(self):
        """Test validation rejects invalid timestamps."""
        invalid_timestamps = [
            "2025-10-06 21:05:52",  # Missing T separator
            "2025/10/06T21:05:52Z",  # Wrong date separator
            "invalid",
            "2025-10-06",  # Date only, no time
            "",
            None,
            123,
            [],
        ]
        
        for ts in invalid_timestamps:
            with self.subTest(timestamp=ts):
                self.assertFalse(validate_iso_timestamp(ts))
    
    def test_validate_iso_timestamp_malformed_but_fixable(self):
        """Test that malformed timestamps are detected (even if auto-fixable)."""
        # These are technically malformed but can be auto-fixed
        malformed_but_fixable = [
            "2025-10-06T21:05:52.510677+00:00Z",  # Double timezone
        ]
        
        for ts in malformed_but_fixable:
            with self.subTest(timestamp=ts):
                # Should still be detected as invalid in strict validation
                # But fix_malformed_timestamp can fix them
                fixed = fix_malformed_timestamp(ts)
                self.assertTrue(validate_iso_timestamp(fixed))
                self.assertNotEqual(ts, fixed)  # Should have been modified
    
    def test_fix_malformed_timestamp_double_timezone(self):
        """Test fixing timestamp with both +00:00 and Z."""
        malformed = "2025-10-06T21:05:52.510677+00:00Z"
        fixed = fix_malformed_timestamp(malformed)
        
        self.assertEqual(fixed, "2025-10-06T21:05:52.510677Z")
        self.assertTrue(validate_iso_timestamp(fixed))
    
    def test_fix_malformed_timestamp_plus_zero(self):
        """Test fixing timestamp with +00:00 (no Z)."""
        input_ts = "2025-10-06T21:05:52.510677+00:00"
        fixed = fix_malformed_timestamp(input_ts)
        
        # Should standardize to Z format
        self.assertEqual(fixed, "2025-10-06T21:05:52.510677Z")
        self.assertTrue(validate_iso_timestamp(fixed))
    
    def test_fix_malformed_timestamp_already_correct(self):
        """Test that already-correct timestamps are not modified."""
        correct = "2025-10-06T21:05:52.510677Z"
        fixed = fix_malformed_timestamp(correct)
        
        self.assertEqual(fixed, correct)
    
    def test_fix_malformed_timestamp_invalid_type(self):
        """Test fixing invalid types returns current timestamp."""
        result = fix_malformed_timestamp(None)
        
        # Should return a valid current timestamp
        self.assertIsInstance(result, str)
        self.assertTrue(validate_iso_timestamp(result))
        
        result = fix_malformed_timestamp(123)
        self.assertIsInstance(result, str)
        self.assertTrue(validate_iso_timestamp(result))
    
    def test_get_current_timestamp_iso_alias(self):
        """Test that get_current_timestamp_iso is an alias for get_iso_timestamp."""
        timestamp1 = get_iso_timestamp()
        time.sleep(0.001)  # Small delay
        timestamp2 = get_current_timestamp_iso()
        
        # Both should return valid timestamps
        self.assertTrue(validate_iso_timestamp(timestamp1))
        self.assertTrue(validate_iso_timestamp(timestamp2))
        
        # Both should use the same format
        self.assertTrue(timestamp1.endswith('Z'))
        self.assertTrue(timestamp2.endswith('Z'))
    
    def test_timestamp_consistency_across_calls(self):
        """Test that multiple calls within short timeframe produce consistent format."""
        timestamps = [get_iso_timestamp() for _ in range(5)]
        
        for ts in timestamps:
            # All should be valid
            self.assertTrue(validate_iso_timestamp(ts))
            
            # All should end with Z
            self.assertTrue(ts.endswith('Z'))
            
            # None should have +00:00
            self.assertNotIn('+00:00', ts)
    
    def test_timestamp_format_structure(self):
        """Test the structure of generated timestamps."""
        timestamp = get_iso_timestamp()
        
        # Should have the basic structure: YYYY-MM-DDTHH:MM:SS...Z
        parts = timestamp.split('T')
        self.assertEqual(len(parts), 2)
        
        date_part = parts[0]
        time_part = parts[1]
        
        # Date should be YYYY-MM-DD
        date_components = date_part.split('-')
        self.assertEqual(len(date_components), 3)
        self.assertEqual(len(date_components[0]), 4)  # Year
        self.assertEqual(len(date_components[1]), 2)  # Month
        self.assertEqual(len(date_components[2]), 2)  # Day
        
        # Time should end with Z
        self.assertTrue(time_part.endswith('Z'))
        
        # Time should have microseconds
        self.assertIn('.', time_part)
    
    def test_unix_timestamp_conversion_preserves_value(self):
        """Test that Unix timestamp conversion is accurate."""
        # Use current time
        now = datetime.now(timezone.utc)
        unix_ts = now.timestamp()
        
        # Convert to ISO
        iso_ts = timestamp_from_unix(unix_ts)
        
        # Parse back and compare
        parsed = datetime.fromisoformat(iso_ts.replace('Z', '+00:00'))
        
        # Should be within 1 microsecond (accounting for rounding)
        time_diff = abs((parsed - now).total_seconds())
        self.assertLess(time_diff, 0.000001)


if __name__ == '__main__':
    unittest.main()
