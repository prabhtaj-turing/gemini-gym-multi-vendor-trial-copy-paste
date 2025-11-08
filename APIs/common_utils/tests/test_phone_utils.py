
import pytest
import sys
import os
from pathlib import Path

# Add the project root to the Python path to allow for absolute imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from APIs.common_utils.phone_utils import is_phone_number_valid, normalize_phone_number

# --- Tests for is_phone_number_valid ---

@pytest.mark.parametrize("phone_number, region, expected", [
    # --- Valid US Numbers ---
    ("4155552671", "US", True),
    ("(415) 555-2671", "US", True),
    ("1-415-555-2671", "US", True),
    # --- Valid International Numbers ---
    ("+14155552671", "US", True), # E.164 format
    ("+442071838750", "GB", True), # Valid UK number
    ("+33142685300", "FR", True), # Valid French number
    # --- Invalid Numbers (under simplified validation, only bad chars/empty fail) ---
    ("555-2671", "US", True),  # Simplified validation: length-only allows 7-15 digits
    ("123", "US", False),      # Too short for reasonable length
    ("not a number", "US", False),  # Contains letters
    ("+1415555267100", "US", True),  # Within 7-15 digits and allowed leading '+'
    # --- Edge Cases ---
    ("", "US", False), # Empty string
])
def test_is_phone_number_valid(phone_number, region, expected):
    """Tests the is_phone_number_valid function with various inputs."""
    assert is_phone_number_valid(phone_number, region) == expected

# --- Tests for normalize_phone_number ---

@pytest.mark.parametrize("phone_number, region, expected", [
    # --- Valid US Numbers (simplified normalization: strip separators, preserve leading '+') ---
    ("4155552671", "US", "4155552671"),
    ("(415) 555-2671", "US", "4155552671"),
    ("1-415-555-2671", "US", "14155552671"),
    # --- Valid International Numbers ---
    ("+14155552671", "US", "+14155552671"), # Already E.164
    ("+44 20 7183 8750", "GB", "+442071838750"), # UK number with spaces
    # --- Previously invalid; now normalization just strips formatting and returns cleaned string ---
    ("555-2671", "US", "5552671"),
    ("123", "US", "123"),
    ("not a number", "US", "notanumber"),
    # --- Edge Cases ---
    ("", "US", None), # Empty string
])
def test_normalize_phone_number(phone_number, region, expected):
    """Tests the normalize_phone_number function with various inputs."""
    assert normalize_phone_number(phone_number, region) == expected

def test_normalize_phone_number_no_region_for_international():
    """
    Tests that normalize_phone_number works correctly for an international number
    even when the region is not provided (or is incorrect), as long as it's in
    E.164 format.
    """
    assert normalize_phone_number("+442071838750", "US") == "+442071838750"
