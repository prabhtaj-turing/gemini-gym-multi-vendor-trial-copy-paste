"""
Test cases for security validation in Google Calendar API.
Tests the fix for Issue #659: Path traversal and command injection vulnerabilities.
"""

import pytest
from pydantic import ValidationError
from google_calendar.SimulationEngine.models import CalendarListResourceInput


class TestCalendarListResourceInputSecurity:
    """Test security validation for CalendarListResourceInput model."""

    def test_valid_id_and_timezone(self):
        """Test that valid inputs pass validation."""
        valid_data = {
            "id": "test-calendar-123",
            "summary": "Test Calendar",
            "timeZone": "America/New_York"
        }
        
        # Should not raise any exception
        model = CalendarListResourceInput(**valid_data)
        assert model.id == "test-calendar-123"
        assert model.timeZone == "America/New_York"

    def test_id_path_traversal_attack(self):
        """Test that path traversal patterns in id are rejected."""
        malicious_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/../etc/passwd",
            "\\..\\windows\\system32",
            "..%2fetc%2fpasswd",
            "..%5cwindows%5csystem32",
            "%2e%2e%2fetc%2fpasswd",
            "%2e%2e%5cwindows%5csystem32",
            "....//etc/passwd",
            "....\\\\windows\\\\system32",
        ]
        
        for malicious_id in malicious_ids:
            with pytest.raises(ValidationError) as exc_info:
                CalendarListResourceInput(id=malicious_id)
            
            error_message = str(exc_info.value)
            assert "path traversal pattern" in error_message

    def test_id_dangerous_characters(self):
        """Test that dangerous characters in id are rejected."""
        dangerous_chars = ['<', '>', '|', '&', ';', '`', '$', '(', ')', '{', '}']
        
        for char in dangerous_chars:
            malicious_id = f"test{char}calendar"
            with pytest.raises(ValidationError) as exc_info:
                CalendarListResourceInput(id=malicious_id)
            
            error_message = str(exc_info.value)
            assert "dangerous character" in error_message

    def test_id_too_long(self):
        """Test that overly long ids are rejected."""
        long_id = "a" * 256  # 256 characters, exceeds limit of 255
        
        with pytest.raises(ValidationError) as exc_info:
            CalendarListResourceInput(id=long_id)
        
        error_message = str(exc_info.value)
        assert "too long" in error_message

    def test_id_empty_or_none(self):
        """Test that empty or None ids are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarListResourceInput(id="")
        
        error_message = str(exc_info.value)
        assert "cannot be empty" in error_message

        with pytest.raises(ValidationError) as exc_info:
            CalendarListResourceInput(id="   ")
        
        error_message = str(exc_info.value)
        assert "cannot be empty" in error_message

    def test_timezone_command_injection_attack(self):
        """Test that command injection patterns in timeZone are rejected."""
        malicious_timezones = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& echo 'hacked'",
            "`whoami`",
            "$(id)",
            "${USER}",
            "|| echo 'hacked'",
            "&& rm -rf /",
            "< /etc/passwd",
            "> /tmp/hacked",
            "\\; rm -rf /",
        ]
        
        for malicious_tz in malicious_timezones:
            with pytest.raises(ValidationError) as exc_info:
                CalendarListResourceInput(id="test", timeZone=malicious_tz)
            
            error_message = str(exc_info.value)
            assert "Invalid IANA time zone" in error_message

    def test_timezone_invalid_format(self):
        """Test that invalid timezone formats are rejected."""
        invalid_timezones = [
            "America/New York",  # Space not allowed
            "America/New-York",  # Hyphen not allowed
            "America/New.York",  # Dot not allowed
            "America/New_York123",  # Numbers not allowed
            "America/New_York@",  # Special characters not allowed
        ]
        
        for invalid_tz in invalid_timezones:
            with pytest.raises(ValidationError) as exc_info:
                CalendarListResourceInput(id="test", timeZone=invalid_tz)
            
            error_message = str(exc_info.value)
            assert "Invalid IANA time zone" in error_message

    def test_timezone_empty_string(self):
        """Test that empty timezone strings are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarListResourceInput(id="test", timeZone="")
        
        error_message = str(exc_info.value)
        assert "cannot be empty if provided" in error_message

        with pytest.raises(ValidationError) as exc_info:
            CalendarListResourceInput(id="test", timeZone="   ")
        
        error_message = str(exc_info.value)
        assert "cannot be empty if provided" in error_message

    def test_timezone_none_allowed(self):
        """Test that None timezone is allowed (will default to UTC)."""
        model = CalendarListResourceInput(id="test", timeZone=None)
        assert model.timeZone is None

    def test_valid_timezone_formats(self):
        """Test that valid timezone formats are accepted."""
        valid_timezones = [
            "UTC",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
            "Pacific/Honolulu",
            "America/Los_Angeles",
            "Europe/Paris",
        ]
        
        for valid_tz in valid_timezones:
            model = CalendarListResourceInput(id="test", timeZone=valid_tz)
            assert model.timeZone == valid_tz

    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed from inputs."""
        model = CalendarListResourceInput(
            id="  test-calendar  ",
            timeZone="  America/New_York  "
        )
        assert model.id == "test-calendar"
        assert model.timeZone == "America/New_York"
