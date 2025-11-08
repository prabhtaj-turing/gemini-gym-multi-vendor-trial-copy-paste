"""
Comprehensive test cases for port_generic_reminder_db function.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add the APIs path to sys.path for imports
ROOT = Path(__file__).resolve().parents[3]
APIS_PATH = ROOT / "APIs"
SCRIPTS_PATH = ROOT / "Scripts" / "porting"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))

# Import after path setup
from port_reminders import port_generic_reminder_db  # noqa: E402


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def default_db_with_data():
    """Default database with actual data (based on GenericRemindersDefaultDB.json)."""
    return {
        "reminders": {
            "reminder_1": {
                "id": "reminder_1",
                "title": "Team standup meeting",
                "description": "Daily team standup to discuss progress and blockers",
                "start_date": "2024-12-16",
                "time_of_day": "09:30:00",
                "am_pm_or_unknown": "AM",
                "end_date": None,
                "repeat_every_n": 1,
                "repeat_interval_unit": "DAY",
                "days_of_week": [
                    "MONDAY",
                    "TUESDAY",
                    "WEDNESDAY",
                    "THURSDAY",
                    "FRIDAY",
                ],
                "weeks_of_month": None,
                "days_of_month": None,
                "occurrence_count": None,
                "completed": False,
                "deleted": False,
                "created_at": "2024-12-15T14:30:00.000Z",
                "updated_at": "2024-12-15T14:30:00.000Z",
                "schedule": "December 16, 2024 at 09:30 AM (repeats daily)",
                "uri": "reminder://reminder_1",
            },
            "reminder_2": {
                "id": "reminder_2",
                "title": "Take medication",
                "description": "Take daily vitamins",
                "start_date": "2024-12-15",
                "time_of_day": "08:00:00",
                "am_pm_or_unknown": "AM",
                "end_date": None,
                "repeat_every_n": 1,
                "repeat_interval_unit": "DAY",
                "days_of_week": None,
                "weeks_of_month": None,
                "days_of_month": None,
                "occurrence_count": None,
                "completed": False,
                "deleted": False,
                "created_at": "2024-12-15T10:15:00.000Z",
                "updated_at": "2024-12-15T10:15:00.000Z",
                "schedule": "December 15, 2024 at 08:00 AM (repeats daily)",
                "uri": "reminder://reminder_2",
            },
        },
        "operations": {
            "operation_1": {
                "id": "operation_1",
                "operation_type": "create",
                "reminder_id": "reminder_1",
                "original_data": None,
                "timestamp": "2024-12-15T14:30:00.000Z",
            }
        },
        "counters": {"reminder": 2, "operation": 1},
    }


@pytest.fixture
def mock_default_db(default_db_with_data):
    """Mock the default DB file loading with realistic data."""
    return mock_open(read_data=json.dumps(default_db_with_data))


@pytest.fixture
def valid_reminder():
    """Valid reminder data for testing."""
    return {
        "id": "test_reminder",
        "title": "Test Reminder",
        "description": "Test description",
        "start_date": "2024-01-01",
        "time_of_day": "10:30:00",
        "am_pm_or_unknown": "AM",
        "end_date": None,
        "repeat_every_n": 0,
        "repeat_interval_unit": None,
        "days_of_week": None,
        "weeks_of_month": None,
        "days_of_month": None,
        "occurrence_count": None,
        "completed": False,
        "deleted": False,
        "created_at": "2024-01-01T10:30:00.000Z",
        "updated_at": "2024-01-01T10:30:00.000Z",
        "schedule": "January 01, 2024 at 10:30 AM",
        "uri": "reminder://test_reminder",
    }


# ============================================================================
# KEY MERGING LOGIC TESTS
# ============================================================================


@pytest.mark.key_merging
def test_source_has_all_keys_from_default(mock_default_db):
    """Source DB has all keys from default DB (complete merge)."""
    source_json = json.dumps(
        {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                }
            },
            "operations": {
                "test_operation": {
                    "id": "test_operation",
                    "operation_type": "create",
                    "reminder_id": "test_reminder",
                    "original_data": None,
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            },
            "counters": {"reminder": 1, "operation": 1},
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)

        # Account for URI patching
        expected_reminder = {
            "id": "test_reminder",
            "title": "Test",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "schedule": "Test schedule",
            "uri": "reminder://test_reminder",
        }
        assert result["reminders"] == {"test_reminder": expected_reminder}
        assert result["operations"]["test_operation"]["operation_type"] == "create"
        assert result["counters"] == {"reminder": 1, "operation": 1}


@pytest.mark.key_merging
def test_source_has_partial_keys_from_default(mock_default_db, default_db_with_data):
    """Source DB has partial keys from default DB (partial merge)."""
    # Source only has reminders, missing operations and counters
    source_json = json.dumps(
        {
            "reminders": {
                "new_reminder": {
                    "id": "new_reminder",
                    "title": "New Reminder",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "New schedule",
                }
            }
            # Missing operations and counters - these will be cleared
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)

        # Source reminders should be present (with URI patching)
        expected_reminder = {
            "id": "new_reminder",
            "title": "New Reminder",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "schedule": "New schedule",
            "uri": "reminder://new_reminder",
        }
        assert result["reminders"] == {"new_reminder": expected_reminder}

        # Missing keys should be cleared (list/dict become empty)
        assert result["operations"] == {}  # Dict cleared because missing in source
        assert result["counters"] == {}  # Dict cleared because missing in source


@pytest.mark.key_merging
def test_source_has_no_keys_from_default(mock_default_db, default_db_with_data):
    """Source DB has no keys from default DB (empty source)."""
    source_json = "{}"

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)
        # When source is empty, default data gets cleared
        assert result["reminders"] == {}
        assert result["operations"] == {}
        assert result["counters"] == {}


@pytest.mark.key_merging
def test_source_has_additional_keys_not_in_default(mock_default_db):
    """Source DB has additional keys not in default DB (extra keys ignored)."""
    source_json = json.dumps(
        {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                }
            },
            "extra_key": "should be ignored",
            "another_extra": {"nested": "data"},
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)
        assert "extra_key" not in result
        assert "another_extra" not in result
        assert "reminders" in result


@pytest.mark.key_merging
def test_source_has_same_keys_but_different_values(default_db_with_data):
    """Source DB has same keys but different values (values overwritten)."""
    # Source data that will overwrite default values
    source_json = json.dumps(
        {
            "reminders": {
                "reminder_1": {
                    "id": "reminder_1",
                    "title": "Overwritten Meeting Title",  # Different from default
                    "description": "New description",
                    "start_date": "2025-01-01",  # Different date
                    "time_of_day": "10:00:00",  # Different time
                    "am_pm_or_unknown": "PM",  # Different AM/PM
                    "created_at": "2024-12-15T14:30:00.000Z",
                    "updated_at": "2024-12-15T14:30:00.000Z",
                    "schedule": "New schedule",
                    "uri": "reminder://reminder_1",
                }
            },
            "operations": {
                "operation_1": {
                    "id": "operation_1",
                    "operation_type": "modify",  # Different from default "create"
                    "reminder_id": "reminder_1",
                    "original_data": {"some": "data"},  # Different from default null
                    "timestamp": "2025-01-01T00:00:00.000Z",  # Different timestamp
                }
            },
            "counters": {"reminder": 999, "operation": 888},  # Different from default
        }
    )

    with patch("builtins.open", mock_open(read_data=json.dumps(default_db_with_data))):
        result = port_generic_reminder_db(source_json)

        # Verify values were overwritten from source
        assert result["reminders"]["reminder_1"]["title"] == "Overwritten Meeting Title"
        assert result["reminders"]["reminder_1"]["start_date"] == "2025-01-01"
        assert result["reminders"]["reminder_1"]["time_of_day"] == "10:00:00"
        assert result["reminders"]["reminder_1"]["am_pm_or_unknown"] == "PM"

        assert result["operations"]["operation_1"]["operation_type"] == "modify"
        assert result["operations"]["operation_1"]["original_data"] == {"some": "data"}

        assert result["counters"]["reminder"] == 999
        assert result["counters"]["operation"] == 888

        # Note: reminder_2 from default is NOT preserved because
        # the entire reminders dict from source replaces the default
        assert "reminder_2" not in result["reminders"]


# ============================================================================
# URI PATCHING TESTS
# ============================================================================


@pytest.mark.uri_patching
def test_reminder_missing_uri_gets_patched(mock_default_db):
    """Reminder missing URI gets patched with reminder://{rid}."""
    source_json = json.dumps(
        {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    # Missing URI
                }
            }
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)
        assert result["reminders"]["test_reminder"]["uri"] == "reminder://test_reminder"


@pytest.mark.uri_patching
def test_reminder_with_existing_uri_keeps_original(mock_default_db):
    """Reminder with existing URI keeps original URI."""
    source_json = json.dumps(
        {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "uri": "custom://test_reminder",
                }
            }
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)
        assert result["reminders"]["test_reminder"]["uri"] == "custom://test_reminder"


@pytest.mark.uri_patching
def test_multiple_reminders_with_missing_uris_all_get_patched(mock_default_db):
    """Multiple reminders with missing URIs all get patched."""
    source_json = json.dumps(
        {
            "reminders": {
                "reminder_1": {
                    "id": "reminder_1",
                    "title": "Test 1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule 1",
                },
                "reminder_2": {
                    "id": "reminder_2",
                    "title": "Test 2",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule 2",
                },
            }
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)
        assert result["reminders"]["reminder_1"]["uri"] == "reminder://reminder_1"
        assert result["reminders"]["reminder_2"]["uri"] == "reminder://reminder_2"


@pytest.mark.uri_patching
def test_mixed_reminders_some_with_uri_some_without(mock_default_db):
    """Mixed reminders (some with URI, some without)."""
    source_json = json.dumps(
        {
            "reminders": {
                "reminder_1": {
                    "id": "reminder_1",
                    "title": "Test 1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule 1",
                    "uri": "custom://reminder_1",
                },
                "reminder_2": {
                    "id": "reminder_2",
                    "title": "Test 2",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule 2",
                },
            }
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)
        assert result["reminders"]["reminder_1"]["uri"] == "custom://reminder_1"
        assert result["reminders"]["reminder_2"]["uri"] == "reminder://reminder_2"


# ============================================================================
# COMPREHENSIVE DATE FORMAT VALIDATION TESTS
# ============================================================================

@pytest.mark.date_validation
def test_start_date_valid_formats(mock_default_db):
    """Test valid YYYY-MM-DD date formats."""
    valid_dates = [
        "2024-01-01",
        "2024-12-31", 
        "2023-02-28",  # Non-leap year
        "2024-02-29",  # Leap year
        "2024-06-15",
        "1999-01-01",  # Past date
        "2099-12-31",  # Future date
    ]
    
    for valid_date in valid_dates:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "start_date": valid_date,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["start_date"] == valid_date


@pytest.mark.date_validation
def test_start_date_invalid_formats(mock_default_db):
    """Test invalid date formats that should fail."""
    invalid_dates = [
        "01/01/2024",      # MM/DD/YYYY
        "01/31/2024",      # MM/DD/YYYY
        "2024/01/01",      # YYYY/MM/DD
        "2024/31/01",      # YYYY/DD/MM
        "31/01/2024",      # DD/MM/YYYY
        "31/12/2024",      # DD/MM/YYYY
        "2024-30-01",      # YYYY-DD-MM (invalid day)
        "2024-13-01",      # Invalid month
        "2024-01-32",      # Invalid day
        "2024-02-30",      # Invalid day for February
        "2023-02-29",      # Invalid leap day for non-leap year
        "24-01-01",        # YY-MM-DD
        "2024-1-1",        # Missing leading zeros
        "2024-01",         # Missing day
        "01-01",           # Missing year
        "2024",            # Only year
        "invalid-date",    # Completely invalid
        "2024-01-01T10:30:00",  # DateTime instead of date
        "",                 # Empty string
        "null",            # String null
        "undefined",       # String undefined
    ]
    
    for invalid_date in invalid_dates:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "start_date": invalid_date,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.date_validation
def test_end_date_valid_formats(mock_default_db):
    """Test valid end date formats."""
    valid_dates = [
        "2024-01-01",
        "2024-12-31",
        "2025-06-15",
    ]
    
    for valid_date in valid_dates:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "end_date": valid_date,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["end_date"] == valid_date


@pytest.mark.date_validation
def test_end_date_invalid_formats(mock_default_db):
    """Test invalid end date formats."""
    invalid_dates = [
        "01/01/2024",
        "2024/01/01", 
        "invalid-date",
        "2024-13-01",
        "2024-01-32",
    ]
    
    for invalid_date in invalid_dates:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "end_date": invalid_date,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.date_validation
def test_date_range_validation(mock_default_db):
    """Test date range validation - end date must be >= start date."""
    # Valid date ranges
    valid_ranges = [
        ("2024-01-01", "2024-01-01"),  # Same date
        ("2024-01-01", "2024-01-02"),  # Next day
        ("2024-01-01", "2024-12-31"),  # Same year
        ("2024-01-01", "2025-01-01"),  # Next year
    ]
    
    for start_date, end_date in valid_ranges:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "start_date": start_date,
                    "end_date": end_date,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["start_date"] == start_date
            assert result["reminders"]["test_reminder"]["end_date"] == end_date
    
    # Invalid date ranges (end before start)
    invalid_ranges = [
        ("2024-01-02", "2024-01-01"),  # Previous day
        ("2024-12-31", "2024-01-01"),  # Previous month
        ("2025-01-01", "2024-01-01"),  # Previous year
    ]
    
    for start_date, end_date in invalid_ranges:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "start_date": start_date,
                    "end_date": end_date,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)



# ============================================================================
# COMPREHENSIVE TIME FORMAT VALIDATION TESTS
# ============================================================================

@pytest.mark.time_validation
def test_time_valid_formats(mock_default_db):
    """Test valid HH:MM:SS time formats."""
    valid_times = [
        "00:00:00",  # Midnight
        "12:00:00",  # Noon
        "23:59:59",  # End of day
        "01:30:45",  # Random valid time
        "10:30:00",  # Morning time
        "15:45:30",  # Afternoon time
        "09:05:01",  # Single digit minutes/seconds
        "8:05:01",   # Single digit hour (should be valid)
        "08:5:01",   # Single digit minute (should be valid)
        "08:05:1",   # Single digit second (should be valid)
    ]
    
    for valid_time in valid_times:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "time_of_day": valid_time,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["time_of_day"] == valid_time


@pytest.mark.time_validation
def test_time_invalid_formats(mock_default_db):
    """Test invalid time formats that should fail."""
    invalid_times = [
        "10:30",         # Missing seconds (HH:MM)
        "10",            # Only hour
        "10:30:60",      # Invalid seconds (60)
        "10:60:30",      # Invalid minutes (60)
        "24:00:00",      # Invalid hour (24)
        "25:30:00",      # Invalid hour (25)
        "10:30:00 AM",  # With AM/PM suffix
        "10:30:00 PM",  # With AM/PM suffix
        "10-30-00",      # Wrong separator
        "10.30.00",      # Wrong separator
        "10 30 00",      # Space separator
        "10:30:00.123",  # With milliseconds
        "invalid-time",  # Completely invalid
        "noon",          # Text time
        "midnight",      # Text time
        "10:30:00Z",     # With timezone
        "10:30:00+05:30", # With timezone offset
        "T10:30:00",     # ISO format prefix
        "2024-01-01T10:30:00", # Full datetime
        "",              # Empty string
        "null",          # String null
        "undefined",     # String undefined
        "ab:cd:ef",      # Non-numeric
        "10:ab:30",      # Mixed numeric/non-numeric
        "10:30:ab",      # Mixed numeric/non-numeric
        "1:2:3",         # Too short (missing leading zeros might be invalid)
    ]
    
    for invalid_time in invalid_times:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "time_of_day": invalid_time,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.time_validation
def test_time_boundary_values(mock_default_db):
    """Test time boundary values."""
    boundary_times = [
        ("00:00:00", True),   # Start of day
        ("23:59:59", True),   # End of day
        ("12:00:00", True),   # Noon
        ("24:00:00", False),  # Invalid - should be 00:00:00
        ("23:60:00", False),  # Invalid minutes
        ("23:59:60", False),  # Invalid seconds
        ("-1:00:00", False),  # Negative hour
        ("00:-1:00", False),  # Negative minute
        ("00:00:-1", False),  # Negative second
    ]
    
    for time_value, should_pass in boundary_times:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "time_of_day": time_value,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            if should_pass:
                result = port_generic_reminder_db(source_json)
                assert result["reminders"]["test_reminder"]["time_of_day"] == time_value
            else:
                with pytest.raises(
                    ValueError, match="Validation failed for reminder test_reminder"
                ):
                    port_generic_reminder_db(source_json)


# ============================================================================
# COMPREHENSIVE AM/PM/UNKNOWN VALIDATION TESTS
# ============================================================================

@pytest.mark.am_pm_validation
def test_am_pm_valid_values(mock_default_db):
    """Test valid AM/PM/UNKNOWN values (case-sensitive)."""
    valid_values = ["AM", "PM", "UNKNOWN"]
    
    for valid_value in valid_values:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "am_pm_or_unknown": valid_value,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["am_pm_or_unknown"] == valid_value


@pytest.mark.am_pm_validation
def test_am_pm_invalid_values(mock_default_db):
    """Test invalid AM/PM values that should fail (case-sensitive)."""
    invalid_values = [
        "am",           # Lowercase
        "pm",           # Lowercase
        "unknown",      # Lowercase
        "Am",           # Mixed case
        "Pm",           # Mixed case
        "Unknown",      # Mixed case
        "AM ",          # With trailing space
        " AM",          # With leading space
        " AM ",         # With spaces
        "A.M.",         # With periods
        "P.M.",         # With periods
        "a.m.",         # Lowercase with periods
        "p.m.",         # Lowercase with periods
        "MORNING",      # Alternative text
        "EVENING",      # Alternative text
        "NOON",         # Alternative text
        "MIDNIGHT",     # Alternative text
        "12AM",         # Combined format
        "12PM",         # Combined format
        "INVALID",      # Completely invalid
        "NULL",         # Null string
        "UNDEFINED",    # Undefined string
        "",             # Empty string
        "0",            # Numeric
        "1",            # Numeric
        "true",         # Boolean string
        "false",        # Boolean string
        "yes",          # Boolean-like string
        "no",           # Boolean-like string
    ]
    
    for invalid_value in invalid_values:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "am_pm_or_unknown": invalid_value,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.am_pm_validation  
def test_am_pm_case_sensitivity(mock_default_db):
    """Test that AM/PM validation is strictly case-sensitive."""
    # Test each valid value with various case combinations
    test_cases = [
        ("AM", True),
        ("am", False),
        ("Am", False),
        ("aM", False),
        ("PM", True),
        ("pm", False),
        ("Pm", False),
        ("pM", False),
        ("UNKNOWN", True),
        ("unknown", False),
        ("Unknown", False),
        ("UnKnOwN", False),
    ]
    
    for value, should_pass in test_cases:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "am_pm_or_unknown": value,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            if should_pass:
                result = port_generic_reminder_db(source_json)
                assert result["reminders"]["test_reminder"]["am_pm_or_unknown"] == value
            else:
                with pytest.raises(
                    ValueError, match="Validation failed for reminder test_reminder"
                ):
                    port_generic_reminder_db(source_json)


# ============================================================================
# COMPREHENSIVE REPEAT FREQUENCY AND INTERVAL VALIDATION TESTS
# ============================================================================

@pytest.mark.repeat_validation
def test_repeat_every_n_valid_values(mock_default_db):
    """Test valid repeat_every_n values (non-negative integers)."""
    valid_values = [0, 1, 2, 5, 10, 50, 100, 365, 1000]
    
    for valid_value in valid_values:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "repeat_every_n": valid_value,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["repeat_every_n"] == valid_value


@pytest.mark.repeat_validation
def test_repeat_every_n_invalid_values(mock_default_db):
    """Test invalid repeat_every_n values (negative or non-integer)."""
    invalid_values = [
        -1,              # Negative
        -10,             # Negative
        -100,            # Large negative
        "1",             # String number
        "not-a-number",  # String
        1.5,             # Float
        -1.5,            # Negative float
        None,            # None (but this might be handled as null)
        [],              # List
        {},              # Dict
        True,            # Boolean
        False,           # Boolean
    ]
    
    for invalid_value in invalid_values:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "repeat_every_n": invalid_value,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.repeat_validation
def test_repeat_interval_unit_valid_values(mock_default_db):
    """Test valid repeat_interval_unit values (case-insensitive)."""
    # Test all valid units in different cases
    valid_units = [
        "MINUTE", "minute", "Minute", "MINUTE",
        "HOUR", "hour", "Hour", "HOUR",
        "DAY", "day", "Day", "DAY",
        "WEEK", "week", "Week", "WEEK", 
        "MONTH", "month", "Month", "MONTH",
        "YEAR", "year", "Year", "YEAR",
    ]
    
    for valid_unit in valid_units:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "repeat_interval_unit": valid_unit,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["repeat_interval_unit"] == valid_unit


@pytest.mark.repeat_validation
def test_repeat_interval_unit_invalid_values(mock_default_db):
    """Test invalid repeat_interval_unit values."""
    invalid_units = [
        "INVALID",       # Completely invalid
        "SECOND",        # Not supported
        "SECONDS",       # Plural form
        "MINUTES",       # Plural form
        "HOURS",         # Plural form
        "DAYS",          # Plural form
        "WEEKS",         # Plural form
        "MONTHS",        # Plural form
        "YEARS",         # Plural form
        "MIN",           # Abbreviation
        "HR",            # Abbreviation
        "WK",            # Abbreviation
        "MO",            # Abbreviation
        "YR",            # Abbreviation
        "D",             # Single letter
        "H",             # Single letter
        "M",             # Single letter (ambiguous)
        "Y",             # Single letter
        "DAILY",         # Alternative format
        "WEEKLY",        # Alternative format
        "MONTHLY",       # Alternative format
        "YEARLY",        # Alternative format
        "ANNUALLY",      # Alternative format
        "QUARTERLY",     # Not supported
        "BIWEEKLY",      # Not supported
        "FORTNIGHTLY",   # Not supported
        "",              # Empty string
        "null",          # String null
        "undefined",     # String undefined
        "1",             # Numeric string
        123,             # Number
        [],              # List
        {},              # Dict
        True,            # Boolean
        False,           # Boolean
    ]
    
    for invalid_unit in invalid_units:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "repeat_interval_unit": invalid_unit,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.repeat_validation
def test_repeat_consistency_validation(mock_default_db):
    """Test consistency validation between repeat_every_n and repeat_interval_unit."""
    # Valid combinations
    valid_combinations = [
        (0, None),        # No repeat
        (1, "DAY"),       # Daily
        (2, "WEEK"),      # Bi-weekly
        (3, "MONTH"),     # Every 3 months
        (1, "YEAR"),      # Yearly
        (15, "MINUTE"),   # Every 15 minutes
        (4, "HOUR"),      # Every 4 hours
    ]
    
    for repeat_n, repeat_unit in valid_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "repeat_every_n": repeat_n,
                    "repeat_interval_unit": repeat_unit,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["repeat_every_n"] == repeat_n
            assert result["reminders"]["test_reminder"]["repeat_interval_unit"] == repeat_unit
    
    # Invalid combinations (repeat_every_n > 0 without repeat_interval_unit)
    invalid_combinations = [
        (1, None),        # Repeat without unit
        (5, None),        # Repeat without unit
        (10, None),       # Repeat without unit
    ]
    
    for repeat_n, repeat_unit in invalid_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "repeat_every_n": repeat_n,
                    "repeat_interval_unit": repeat_unit,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


# ============================================================================
# COMPREHENSIVE DAYS OF WEEK VALIDATION TESTS
# ============================================================================

@pytest.mark.days_of_week_validation
def test_days_of_week_valid_values(mock_default_db):
    """Test valid weekday names (case-insensitive)."""
    # Test individual days in different cases
    valid_days_cases = [
        ["SUNDAY"], ["sunday"], ["Sunday"], ["SuNdAy"],
        ["MONDAY"], ["monday"], ["Monday"], ["MoNdAy"],
        ["TUESDAY"], ["tuesday"], ["Tuesday"], ["TuEsDaY"],
        ["WEDNESDAY"], ["wednesday"], ["Wednesday"], ["WeDnEsDaY"],
        ["THURSDAY"], ["thursday"], ["Thursday"], ["ThUrSdAy"],
        ["FRIDAY"], ["friday"], ["Friday"], ["FrIdAy"],
        ["SATURDAY"], ["saturday"], ["Saturday"], ["SaTuRdAy"],
    ]
    
    for valid_days in valid_days_cases:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_week": valid_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["days_of_week"] == valid_days


@pytest.mark.days_of_week_validation
def test_days_of_week_multiple_valid(mock_default_db):
    """Test multiple valid weekday combinations."""
    valid_combinations = [
        ["MONDAY", "TUESDAY"],
        ["MONDAY", "WEDNESDAY", "FRIDAY"],
        ["SATURDAY", "SUNDAY"],  # Weekend
        ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],  # Weekdays
        ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"],  # All days
        ["monday", "tuesday", "wednesday"],  # Lowercase
        ["Monday", "Tuesday", "Wednesday"],  # Title case
        ["MONDAY", "tuesday", "Wednesday"],  # Mixed case
    ]
    
    for valid_combination in valid_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_week": valid_combination,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["days_of_week"] == valid_combination


@pytest.mark.days_of_week_validation
def test_days_of_week_invalid_values(mock_default_db):
    """Test invalid weekday names."""
    invalid_day_combinations = [
        ["INVALID"],          # Completely invalid
        ["WEEKDAY"],          # Not a specific day
        ["WEEKEND"],          # Not a specific day
        ["MON"],              # Abbreviation
        ["TUE"],              # Abbreviation
        ["WED"],              # Abbreviation
        ["THU"],              # Abbreviation
        ["FRI"],              # Abbreviation
        ["SAT"],              # Abbreviation
        ["SUN"],              # Abbreviation
        ["M"],                # Single letter
        ["T"],                # Single letter
        ["W"],                # Single letter
        ["F"],                # Single letter
        ["S"],                # Single letter (ambiguous)
        ["1"],                # Numeric
        ["2"],                # Numeric
        ["7"],                # Numeric
        ["FIRST"],            # Ordinal
        ["LAST"],             # Ordinal
        ["TODAY"],            # Relative
        ["TOMORROW"],         # Relative
        ["YESTERDAY"],        # Relative
        [""],                 # Empty string
        ["null"],             # String null
        ["undefined"],        # String undefined
        ["MONDAY", "INVALID"], # Mix of valid and invalid
        ["TUESDAY", "MON"],    # Mix of valid and abbreviation
        ["WEDNESDAY", ""],     # Mix of valid and empty
    ]
    
    for invalid_days in invalid_day_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_week": invalid_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.days_of_week_validation
def test_days_of_week_type_validation(mock_default_db):
    """Test that days_of_week must be a list."""
    invalid_types = [
        "MONDAY",            # String instead of list
        "MONDAY,TUESDAY",    # Comma-separated string
        123,                 # Number
        {"MONDAY": True},    # Dict
        True,                # Boolean
        None,                # None (but this might be handled)
    ]
    
    for invalid_type in invalid_types:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_week": invalid_type,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.days_of_week_validation
def test_days_of_week_duplicate_values(mock_default_db):
    """Test duplicate day values (should be allowed)."""
    duplicate_combinations = [
        ["MONDAY", "MONDAY"],
        ["TUESDAY", "TUESDAY", "TUESDAY"],
        ["MONDAY", "monday"],  # Same day different case
        ["WEDNESDAY", "Wednesday", "WEDNESDAY"],
    ]
    
    for duplicate_days in duplicate_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_week": duplicate_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            # Should pass - duplicates are allowed
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["days_of_week"] == duplicate_days


# ============================================================================
# COMPREHENSIVE WEEKS OF MONTH VALIDATION TESTS
# ============================================================================

@pytest.mark.weeks_of_month_validation
def test_weeks_of_month_valid_numeric_strings(mock_default_db):
    """Test valid numeric strings '1'-'5' for weeks of month."""
    valid_numeric_weeks = [
        ["1"],
        ["2"],
        ["3"],
        ["4"],
        ["5"],
        ["1", "3"],
        ["2", "4"],
        ["1", "2", "3", "4", "5"],
    ]
    
    for valid_weeks in valid_numeric_weeks:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "weeks_of_month": valid_weeks,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["weeks_of_month"] == valid_weeks


@pytest.mark.weeks_of_month_validation
def test_weeks_of_month_valid_word_forms(mock_default_db):
    """Test valid word forms for weeks of month."""
    valid_word_weeks = [
        ["FIRST"],
        ["SECOND"],
        ["THIRD"],
        ["FOURTH"],
        ["LAST"],
        ["FIRST", "THIRD"],
        ["SECOND", "FOURTH"],
        ["FIRST", "SECOND", "THIRD", "FOURTH", "LAST"],
        # Test case variations
        ["first"],
        ["Second"],
        ["THIRD"],
        ["fourth"],
        ["Last"],
        ["FIRST", "second", "Third"],
    ]
    
    for valid_weeks in valid_word_weeks:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "weeks_of_month": valid_weeks,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["weeks_of_month"] == valid_weeks


@pytest.mark.weeks_of_month_validation
def test_weeks_of_month_mixed_formats(mock_default_db):
    """Test mixed numeric and word formats."""
    mixed_combinations = [
        ["1", "THIRD"],
        ["FIRST", "3"],
        ["2", "FOURTH", "5"],
        ["SECOND", "4", "LAST"],
    ]
    
    for mixed_weeks in mixed_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "weeks_of_month": mixed_weeks,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["weeks_of_month"] == mixed_weeks


@pytest.mark.weeks_of_month_validation
def test_weeks_of_month_invalid_values(mock_default_db):
    """Test invalid weeks of month values."""
    invalid_weeks_combinations = [
        ["0"],                # Invalid numeric (too low)
        ["6"],                # Invalid numeric (too high)
        ["7"],                # Invalid numeric
        ["10"],               # Invalid numeric
        ["-1"],              # Negative numeric
        ["ZERO"],             # Invalid word
        ["FIFTH"],            # Invalid word (should be LAST)
        ["SIXTH"],            # Invalid word
        ["BEGINNING"],        # Alternative word
        ["END"],              # Alternative word
        ["MIDDLE"],           # Alternative word
        ["EARLY"],            # Alternative word
        ["LATE"],             # Alternative word
        ["1ST"],              # Ordinal with suffix
        ["2ND"],              # Ordinal with suffix
        ["3RD"],              # Ordinal with suffix
        ["4TH"],              # Ordinal with suffix
        ["5TH"],              # Ordinal with suffix
        ["ONE"],              # Written number
        ["TWO"],              # Written number
        ["THREE"],            # Written number
        ["FOUR"],             # Written number
        ["FIVE"],             # Written number
        ["INVALID"],          # Completely invalid
        [""],                 # Empty string
        ["null"],             # String null
        ["undefined"],        # String undefined
        ["FIRST", "INVALID"], # Mix of valid and invalid
        ["1", "6"],           # Mix of valid and invalid numeric
        ["SECOND", "SIXTH"],  # Mix of valid and invalid word
        ["1.0"],              # Float string
        ["1.5"],              # Float string
    ]
    
    for invalid_weeks in invalid_weeks_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "weeks_of_month": invalid_weeks,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.weeks_of_month_validation
def test_weeks_of_month_type_validation(mock_default_db):
    """Test that weeks_of_month must be a list."""
    invalid_types = [
        "1",                 # String instead of list
        "FIRST",            # String instead of list
        "1,2,3",            # Comma-separated string
        123,                 # Number
        {"1": True},         # Dict
        True,                # Boolean
        None,                # None (might be handled)
    ]
    
    for invalid_type in invalid_types:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "weeks_of_month": invalid_type,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


# ============================================================================
# COMPREHENSIVE DAYS OF MONTH VALIDATION TESTS
# ============================================================================

@pytest.mark.days_of_month_validation
def test_days_of_month_valid_day_x_format(mock_default_db):
    """Test valid DAY_X format (case-insensitive)."""
    valid_day_x_formats = [
        ["DAY_1"], ["day_1"], ["Day_1"], ["DAY_1"],
        ["DAY_15"], ["day_15"], ["Day_15"],
        ["DAY_31"], ["day_31"], ["Day_31"],
        ["DAY_1", "DAY_15", "DAY_31"],
        ["day_5", "DAY_10", "Day_20"],
    ]
    
    for valid_days in valid_day_x_formats:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_month": valid_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["days_of_month"] == valid_days


@pytest.mark.days_of_month_validation
def test_days_of_month_valid_plain_numbers(mock_default_db):
    """Test valid plain numbers 1-31."""
    valid_plain_numbers = [
        ["1"], ["15"], ["31"],
        ["1", "15", "31"],
        ["5", "10", "20", "25"],
        # Edge cases
        ["28"],  # February non-leap
        ["29"],  # February leap
        ["30"],  # April, June, September, November
    ]
    
    for valid_days in valid_plain_numbers:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_month": valid_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["days_of_month"] == valid_days


@pytest.mark.days_of_month_validation
def test_days_of_month_valid_last(mock_default_db):
    """Test valid LAST value (case-insensitive)."""
    valid_last_formats = [
        ["LAST"],
        ["last"],
        ["Last"],
        ["LaSt"],
        ["LAST", "15"],
        ["last", "DAY_10"],
        ["Last", "day_5", "20"],
    ]
    
    for valid_days in valid_last_formats:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_month": valid_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["days_of_month"] == valid_days


@pytest.mark.days_of_month_validation
def test_days_of_month_mixed_formats(mock_default_db):
    """Test mixed valid formats."""
    mixed_combinations = [
        ["1", "DAY_15", "LAST"],
        ["day_5", "10", "Last"],
        ["DAY_1", "15", "last", "DAY_25"],
        ["5", "day_10", "LAST", "20"],
    ]
    
    for mixed_days in mixed_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_month": mixed_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["days_of_month"] == mixed_days


@pytest.mark.days_of_month_validation
def test_days_of_month_invalid_values(mock_default_db):
    """Test invalid days of month values."""
    invalid_days_combinations = [
        ["0"],                # Invalid number (too low)
        ["32"],               # Invalid number (too high)
        ["50"],               # Invalid number
        ["100"],              # Invalid number
        ["-1"],              # Negative number
        ["DAY_0"],            # Invalid DAY_X (too low)
        ["DAY_32"],           # Invalid DAY_X (too high)
        ["DAY_50"],           # Invalid DAY_X
        ["DAY_"],             # Incomplete DAY_X
        ["DAY"],              # Missing number
        ["_15"],              # Missing DAY prefix
        ["FIRST"],            # Week format instead of day
        ["SECOND"],           # Week format instead of day
        ["BEGINNING"],        # Alternative word
        ["END"],              # Alternative word
        ["MIDDLE"],           # Alternative word
        ["1ST"],              # Ordinal with suffix
        ["15TH"],             # Ordinal with suffix
        ["31ST"],             # Ordinal with suffix
        ["ONE"],              # Written number
        ["FIFTEEN"],          # Written number
        ["THIRTY"],           # Written number
        ["INVALID"],          # Completely invalid
        [""],                 # Empty string
        ["null"],             # String null
        ["undefined"],        # String undefined
        ["DAY_1", "INVALID"], # Mix of valid and invalid
        ["15", "32"],          # Mix of valid and invalid number
        ["LAST", "FIRST"],    # Mix of valid day and invalid week
        ["1.0"],              # Float string
        ["15.5"],             # Float string
        ["DAY_1.5"],          # Float in DAY_X format
        ["DAY_-1"],           # Negative in DAY_X format
    ]
    
    for invalid_days in invalid_days_combinations:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_month": invalid_days,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.days_of_month_validation
def test_days_of_month_type_validation(mock_default_db):
    """Test that days_of_month must be a list."""
    invalid_types = [
        "1",                 # String instead of list
        "DAY_15",            # String instead of list
        "LAST",              # String instead of list
        "1,15,31",           # Comma-separated string
        123,                 # Number
        {"1": True},         # Dict
        True,                # Boolean
        None,                # None (might be handled)
    ]
    
    for invalid_type in invalid_types:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "days_of_month": invalid_type,
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)

# ============================================================================
# COMPREHENSIVE OCCURRENCE COUNT VALIDATION TESTS
# ============================================================================

@pytest.mark.occurrence_validation
def test_occurrence_count_valid_values(mock_default_db):
    """Test valid positive occurrence count values."""
    valid_values = [1, 2, 5, 10, 50, 100, 365, 1000]
    
    for valid_count in valid_values:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "occurrence_count": valid_count,
                    "repeat_every_n": 1,  # Required for occurrence_count
                    "repeat_interval_unit": "DAY",  # Required for repeat_every_n > 0
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["occurrence_count"] == valid_count


@pytest.mark.occurrence_validation
def test_occurrence_count_invalid_values(mock_default_db):
    """Test invalid occurrence count values (zero, negative, non-integer)."""
    invalid_values = [
        0,                   # Zero (must be positive)
        -1,                  # Negative
        -10,                 # Large negative
        -100,                # Very large negative
        "1",                 # String number
        "not-a-number",      # String
        1.5,                 # Float
        -1.5,                # Negative float
        0.5,                 # Positive float less than 1
        [],                  # List
        {},                  # Dict
        True,                # Boolean
        False,               # Boolean
    ]
    
    for invalid_count in invalid_values:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "occurrence_count": invalid_count,
                    "repeat_every_n": 1,
                    "repeat_interval_unit": "DAY",
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.occurrence_validation
def test_occurrence_count_consistency_validation(mock_default_db):
    """Test that occurrence_count requires repeat_every_n > 0."""
    # Valid cases - occurrence_count with proper repeat settings
    valid_cases = [
        {"occurrence_count": 5, "repeat_every_n": 1, "repeat_interval_unit": "DAY"},
        {"occurrence_count": 10, "repeat_every_n": 2, "repeat_interval_unit": "WEEK"},
        {"occurrence_count": 3, "repeat_every_n": 1, "repeat_interval_unit": "MONTH"},
    ]
    
    for case in valid_cases:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    **case
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["occurrence_count"] == case["occurrence_count"]
    
    # Invalid cases - occurrence_count without proper repeat settings
    invalid_cases = [
        {"occurrence_count": 5, "repeat_every_n": 0},  # repeat_every_n is 0
        {"occurrence_count": 5},  # No repeat_every_n (defaults to 0)
        {"occurrence_count": 10, "repeat_every_n": None},  # repeat_every_n is None
    ]
    
    for case in invalid_cases:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    **case
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            with pytest.raises(
                ValueError, match="Validation failed for reminder test_reminder"
            ):
                port_generic_reminder_db(source_json)


@pytest.mark.occurrence_validation
def test_occurrence_count_boundary_values(mock_default_db):
    """Test boundary values for occurrence count."""
    boundary_cases = [
        (1, True),     # Minimum valid value
        (2, True),     # Small valid value
        (100, True),   # Large valid value
        (1000, True),  # Very large valid value
        (0, False),    # Invalid - zero
        (-1, False),   # Invalid - negative
    ]
    
    for count_value, should_pass in boundary_cases:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                    "occurrence_count": count_value,
                    "repeat_every_n": 1,
                    "repeat_interval_unit": "DAY",
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            if should_pass:
                result = port_generic_reminder_db(source_json)
                assert result["reminders"]["test_reminder"]["occurrence_count"] == count_value
            else:
                with pytest.raises(
                    ValueError, match="Validation failed for reminder test_reminder"
                ):
                    port_generic_reminder_db(source_json)


# ============================================================================
# COMPREHENSIVE UNICODE AND SPECIAL CHARACTER VALIDATION TESTS
# ============================================================================

@pytest.mark.unicode_validation
def test_unicode_characters_in_title(mock_default_db):
    """Test unicode characters in title field."""
    unicode_titles = [
        "测试提醒 🔔",                    # Chinese with emoji
        "Recordatorio en español",        # Spanish with accents
        "Напоминание на русском",         # Russian Cyrillic
        "リマインダー日本語",               # Japanese
        "العربية تذكير",                 # Arabic
        "עברית תזכורת",                  # Hebrew
        "हिंदी अनुस्मारक",                # Hindi
        "ελληνικά υπενθύμιση",            # Greek
        "🎉🎂🎈 Birthday Party! 🎊🎁",     # Multiple emojis
        "Café ☕ Meeting @ 3PM",          # Mixed symbols
        "Math: α + β = γ",               # Mathematical symbols
        "Temperature: 25°C",              # Degree symbol
        "Price: $100 → €85",             # Currency and arrow
        "Line 1\nLine 2\nLine 3",         # Newlines
        "Tab\tSeparated\tValues",         # Tabs
        "Quote: \"Hello World\"",         # Escaped quotes
        "Backslash: \\",                # Escaped backslash
        "Very long title that exceeds normal length expectations and contains various unicode characters like émojis 🚀, symbols ∑∆π, and foreign text 中文",
    ]
    
    for unicode_title in unicode_titles:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": unicode_title,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["title"] == unicode_title


@pytest.mark.unicode_validation
def test_unicode_characters_in_description(mock_default_db):
    """Test unicode characters in description field."""
    unicode_descriptions = [
        "详细的中文描述，包含特殊字符和表情符号 😊",
        "Descripción detallada en español con acentos: áéíóú",
        "Подробное описание на русском языке с символами",
        "長い日本語の説明文です。特殊文字も含まれています。",
        "Multi-line description\nWith newlines\nAnd unicode: ∑∆π",
        "Special chars: !@#$%^&*()_+-=[]{}|;':,.<>?",
        "HTML-like: <tag>content</tag> & entities: &amp; &lt; &gt;",
        "JSON-like: {\"key\": \"value\", \"number\": 123}",
        "URL: https://example.com/path?param=value&other=123",
        "Email: test@example.com with symbols",
    ]
    
    for unicode_description in unicode_descriptions:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Test",
                    "description": unicode_description,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["description"] == unicode_description


@pytest.mark.unicode_validation
def test_special_characters_edge_cases(mock_default_db):
    """Test edge cases with special characters."""
    edge_cases = [
        {
            "title": "\x00\x01\x02",  # Control characters
            "description": "Control chars test"
        },
        {
            "title": "\u200B\u200C\u200D",  # Zero-width characters
            "description": "Zero-width test"
        },
        {
            "title": "\uFEFF",  # Byte order mark
            "description": "BOM test"
        },
        {
            "title": "🏳️‍🌈🏳️‍⚧️",  # Complex emoji sequences
            "description": "Complex emoji test"
        },
        {
            "title": "👨‍👩‍👧‍👦",  # Family emoji (multiple codepoints)
            "description": "Family emoji test"
        },
        {
            "title": "\U0001F600\U0001F601\U0001F602",  # High codepoint emojis
            "description": "High codepoint test"
        },
    ]
    
    for case in edge_cases:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": case["title"],
                    "description": case["description"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            assert result["reminders"]["test_reminder"]["title"] == case["title"]
            assert result["reminders"]["test_reminder"]["description"] == case["description"]


@pytest.mark.unicode_validation
def test_long_strings(mock_default_db):
    """Test very long strings with unicode characters."""
    # Generate long strings with various unicode characters
    long_title = "🎉" * 1000  # 1000 emoji characters
    long_description = "测试" * 5000 + "\n" + "🚀" * 1000  # Mixed long content
    
    source_data = {
        "reminders": {
            "test_reminder": {
                "id": "test_reminder",
                "title": long_title,
                "description": long_description,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "schedule": "Test schedule",
            }
        }
    }
    
    with patch("builtins.open", mock_default_db):
        source_json = json.dumps(source_data)
        result = port_generic_reminder_db(source_json)
        assert result["reminders"]["test_reminder"]["title"] == long_title
        assert result["reminders"]["test_reminder"]["description"] == long_description


@pytest.mark.unicode_validation
def test_empty_string_handling(mock_default_db):
    """Test empty string handling (should become None)."""
    empty_string_cases = [
        {"title": "", "description": "Normal description"},
        {"title": "Normal title", "description": ""},
        {"title": "", "description": ""},
        {"title": "   ", "description": "Normal description"},  # Whitespace only
        {"title": "\t\n\r", "description": "Normal description"},  # Whitespace chars
    ]
    
    for case in empty_string_cases:
        source_data = {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": case["title"],
                    "description": case["description"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Test schedule",
                }
            }
        }
        
        with patch("builtins.open", mock_default_db):
            source_json = json.dumps(source_data)
            result = port_generic_reminder_db(source_json)
            
            # Empty strings should become None due to BaseReminderModel.handle_empty_strings
            expected_title = None if case["title"].strip() == "" else case["title"]
            expected_description = None if case["description"].strip() == "" else case["description"]
            
            assert result["reminders"]["test_reminder"]["title"] == expected_title
            assert result["reminders"]["test_reminder"]["description"] == expected_description


@pytest.mark.reminder_validation
def test_valid_recurring_daily(mock_default_db):
    """Valid daily recurring reminder."""
    source_json = json.dumps(
        {
            "reminders": {
                "test_reminder": {
                    "id": "test_reminder",
                    "title": "Daily Reminder",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "schedule": "Daily at 9 AM",
                    "repeat_every_n": 1,
                    "repeat_interval_unit": "DAY",
                }
            }
        }
    )

    with patch("builtins.open", mock_default_db):
        result = port_generic_reminder_db(source_json)
        assert result["reminders"]["test_reminder"]["repeat_interval_unit"] == "DAY"
        assert result["reminders"]["test_reminder"]["repeat_every_n"] == 1
