import pytest
import tempfile
import os
from pathlib import Path
from APIs.github.SimulationEngine import db as github_db
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

def test_save_state():
    """Test save_state function to improve coverage."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Test save_state
        github_db.save_state(temp_file)
        
        # Verify file was created and contains data
        assert os.path.exists(temp_file)
        with open(temp_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, dict)
            # Check for any key that indicates the DB structure
            assert len(data) > 0
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_load_state_file_not_found():
    """Test load_state with non-existent file to improve coverage."""
    # This should not raise an exception due to the try-except block
    github_db.load_state("non_existent_file.json")

def test_reset_db():
    """Test reset_db function to ensure it restores the default state."""
    # Modify the DB to a non-reset state to ensure reset_db is actually working
    github_db.DB["Users"].append({"login": "testuser", "id": 123})
    github_db.DB["CurrentUser"] = {}  # Corrupt the state to test restoration

    # Test reset_db
    github_db.reset_db()

    # Verify the DB is reset to its default state
    assert github_db.DB["CurrentUser"] == {"login": "default_user", "id": 0}

    # Verify all other collections are cleared
    for key, value in github_db.DB.items():
        if key == "CurrentUser":
            continue  # Already checked this key
        
        if isinstance(value, list):
            assert len(value) == 0, f"List '{key}' should be empty after reset."
        elif isinstance(value, dict):
            assert len(value) == 0, f"Dictionary '{key}' should be empty after reset."

def test_save_state_datetime_encoder():
    """Test save_state DateTimeEncoder datetime handling (lines 927-929)."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Add a datetime object to the DB to test the DateTimeEncoder
        test_datetime = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Store original state
        original_db = github_db.DB.copy()
        
        # Add a test entry with datetime
        github_db.DB['TestDatetime'] = test_datetime
        
        # Test save_state - this should trigger the DateTimeEncoder.default method
        github_db.save_state(temp_file)
        
        # Verify file was created and contains the datetime as ISO string
        assert os.path.exists(temp_file)
        with open(temp_file, 'r') as f:
            data = json.load(f)
            assert 'TestDatetime' in data
            # The datetime should be converted to ISO string format
            assert data['TestDatetime'] == "2023-01-01T12:00:00Z"
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        # Restore original DB state
        github_db.DB.clear()
        github_db.DB.update(original_db)

def test_save_state_datetime_encoder_non_datetime():
    """Test save_state DateTimeEncoder with non-datetime object (line 929)."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Store original state
        original_db = github_db.DB.copy()
        
        # Add a test entry with non-datetime object
        github_db.DB['TestString'] = "test_string"
        github_db.DB['TestInt'] = 42
        
        # Test save_state - this should trigger the DateTimeEncoder.default method
        # but fall through to super().default() for non-datetime objects
        github_db.save_state(temp_file)
        
        # Verify file was created and contains the data
        assert os.path.exists(temp_file)
        with open(temp_file, 'r') as f:
            data = json.load(f)
            assert data['TestString'] == "test_string"
            assert data['TestInt'] == 42
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        # Restore original DB state
        github_db.DB.clear()
        github_db.DB.update(original_db)

def test_validate_db_state_validation_error():
    """Test _validate_db_state ValidationError handling (lines 939-941)."""
    # Create invalid DB data that will cause ValidationError
    invalid_db = {
        "CurrentUser": {"id": "invalid_id", "login": "test"},  # id should be int
        "Users": "not_a_list",  # should be a list
        "Repositories": []
    }
    
    # Test that ValidationError is raised and printed
    with patch('builtins.print') as mock_print:
        with pytest.raises(ValidationError):
            github_db._validate_db_state(invalid_db)
        
        # Verify that the error message was printed
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Database validation failed:" in call_args

def test_validate_db_state_success():
    """Test _validate_db_state with valid data."""
    # Create valid DB data
    valid_db = {
        "CurrentUser": {"id": 1, "login": "test"},
        "Users": [],
        "Repositories": [],
        "CodeSearchResultsCollection": []
    }
    
    # This should not raise any exception
    github_db._validate_db_state(valid_db)
