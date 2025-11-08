import pytest
import json
import tempfile
import os
from unittest.mock import patch
from google_home.SimulationEngine.utils import (
    add_structure,
    get_structure,
    update_structure,
    delete_structure,
    add_room,
    get_room,
    update_room,
    delete_room,
    add_device,
    get_device,
    update_device,
    delete_device,
)
from google_home.SimulationEngine.db import (
    load_state,
    restore_default_data,
    clear_db,
    save_state,
    DB
)
from google_home.SimulationEngine.custom_errors import (
    InvalidInputError,
    DeviceNotFoundError,
)

@pytest.fixture
def mock_db():
    with patch("google_home.SimulationEngine.utils.DB", {"structures": {}}) as _mock_db:
        yield _mock_db

# region Structure Tests
def test_add_structure(mock_db):
    structure_data = {"name": "Home", "rooms": {}}
    result = add_structure(structure_data)
    assert result["name"] == "Home"
    assert "Home" in mock_db["structures"]

def test_add_existing_structure(mock_db):
    structure_data = {"name": "Home", "rooms": {}}
    add_structure(structure_data)
    with pytest.raises(InvalidInputError, match="Structure 'Home' already exists."):
        add_structure(structure_data)

def test_add_invalid_structure(mock_db):
    with pytest.raises(InvalidInputError):
        add_structure({"rooms": {}})  # Missing 'name'

def test_get_structure(mock_db):
    structure_data = {"name": "Home", "rooms": {}}
    add_structure(structure_data)
    result = get_structure("Home")
    assert result is not None
    assert result["name"] == "Home"

def test_get_nonexistent_structure(mock_db):
    result = get_structure("NonExistentHome")
    assert result is None

def test_update_structure(mock_db):
    structure_data = {"name": "Home", "rooms": {}}
    add_structure(structure_data)
    update_data = {"name": "New Home"}
    result = update_structure("Home", update_data)
    assert result["name"] == "New Home"
    assert "New Home" in mock_db["structures"]
    assert "Home" not in mock_db["structures"]

def test_update_nonexistent_structure(mock_db):
    with pytest.raises(DeviceNotFoundError, match="Structure 'NonExistentHome' not found."):
        update_structure("NonExistentHome", {"name": "New Name"})

def test_update_structure_with_invalid_data(mock_db):
    structure_data = {"name": "Home", "rooms": {}}
    add_structure(structure_data)
    with pytest.raises(InvalidInputError):
        update_structure("Home", {"name": 123})  # Invalid type for name

def test_delete_structure(mock_db):
    structure_data = {"name": "Home", "rooms": {}}
    add_structure(structure_data)
    delete_structure("Home")
    assert "Home" not in mock_db["structures"]

def test_delete_nonexistent_structure(mock_db):
    with pytest.raises(DeviceNotFoundError, match="Structure 'NonExistentHome' not found."):
        delete_structure("NonExistentHome")
# endregion

# region Room Tests
def test_add_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    room_data = {"name": "Living Room", "devices": {}}
    result = add_room("Home", room_data)
    assert result["name"] == "Living Room"
    assert "Living Room" in mock_db["structures"]["Home"]["rooms"]

def test_add_room_to_nonexistent_structure(mock_db):
    with pytest.raises(DeviceNotFoundError, match="Structure 'NonExistentHome' not found."):
        add_room("NonExistentHome", {"name": "Living Room", "devices": {}})

def test_add_existing_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    room_data = {"name": "Living Room", "devices": {}}
    add_room("Home", room_data)
    with pytest.raises(InvalidInputError, match="Room 'Living Room' already exists in structure 'Home'."):
        add_room("Home", room_data)

def test_add_invalid_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    with pytest.raises(InvalidInputError):
        add_room("Home", {"devices": {}})  # Missing 'name'

def test_get_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    result = get_room("Home", "Living Room")
    assert result is not None
    assert result["name"] == "Living Room"

def test_get_nonexistent_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    assert get_room("Home", "NonExistentRoom") is None
    assert get_room("NonExistentHome", "Living Room") is None

def test_update_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    update_data = {"name": "Family Room"}
    result = update_room("Home", "Living Room", update_data)
    assert result["name"] == "Family Room"
    assert "Family Room" in mock_db["structures"]["Home"]["rooms"]
    assert "Living Room" not in mock_db["structures"]["Home"]["rooms"]

def test_update_nonexistent_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    with pytest.raises(DeviceNotFoundError, match="Room 'NonExistentRoom' in structure 'Home' not found."):
        update_room("Home", "NonExistentRoom", {"name": "New Name"})

def test_update_room_with_invalid_data(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    with pytest.raises(InvalidInputError):
        update_room("Home", "Living Room", {"name": 123})

def test_delete_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    delete_room("Home", "Living Room")
    assert "Living Room" not in mock_db["structures"]["Home"]["rooms"]

def test_delete_nonexistent_room(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    with pytest.raises(DeviceNotFoundError, match="Room 'NonExistentRoom' in structure 'Home' not found."):
        delete_room("Home", "NonExistentRoom")
# endregion

# region Device Tests
@pytest.fixture
def device_data():
    return {
        "id": "light-123",
        "names": ["Main Light"],
        "types": ["LIGHT"],
        "traits": ["OnOff"],
        "room_name": "Living Room",
        "structure": "Home",
        "toggles_modes": [],
        "device_state": [{"name": "on", "value": False}],
    }

def test_add_device(mock_db, device_data):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    result = add_device("Home", "Living Room", device_data)
    assert result["id"] == "light-123"
    assert result in mock_db["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"]

def test_add_device_to_nonexistent_room(mock_db, device_data):
    with pytest.raises(DeviceNotFoundError, match="Room 'NonExistentRoom' in structure 'Home' not found."):
        add_device("Home", "NonExistentRoom", device_data)

def test_add_existing_device(mock_db, device_data):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    add_device("Home", "Living Room", device_data)
    with pytest.raises(InvalidInputError, match="Device with ID 'light-123' already exists."):
        add_device("Home", "Living Room", device_data)

def test_add_invalid_device(mock_db):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    with pytest.raises(InvalidInputError):
        add_device("Home", "Living Room", {"id": "invalid-device"}) # Missing fields

def test_get_device(mock_db, device_data):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    add_device("Home", "Living Room", device_data)
    result = get_device("light-123")
    assert result is not None
    assert result["id"] == "light-123"

def test_get_nonexistent_device(mock_db):
    assert get_device("nonexistent-device") is None

def test_update_device(mock_db, device_data):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    add_device("Home", "Living Room", device_data)
    update_data = {"names": ["New Main Light"]}
    result = update_device("light-123", update_data)
    assert result["names"] == ["New Main Light"]
    assert get_device("light-123")["names"] == ["New Main Light"]

def test_update_nonexistent_device(mock_db):
    with pytest.raises(DeviceNotFoundError, match="Device with ID 'nonexistent-device' not found."):
        update_device("nonexistent-device", {"names": ["New Name"]})

def test_update_device_with_invalid_data(mock_db, device_data):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    add_device("Home", "Living Room", device_data)
    with pytest.raises(InvalidInputError):
        update_device("light-123", {"traits": ["InvalidTrait"]})

def test_delete_device(mock_db, device_data):
    add_structure({"name": "Home", "rooms": {}})
    add_room("Home", {"name": "Living Room", "devices": {}})
    add_device("Home", "Living Room", device_data)
    delete_device("light-123")
    assert get_device("light-123") is None

def test_delete_nonexistent_device(mock_db):
    with pytest.raises(DeviceNotFoundError, match="Device with ID 'nonexistent-device' not found."):
        delete_device("nonexistent-device")

# region Database Loading Tests
@pytest.fixture
def sample_db_data():
    """Sample database data for testing DB loading functions."""
    return {
        "structures": {
            "TestHome": {
                "name": "TestHome",
                "rooms": {
                    "TestRoom": {
                        "name": "TestRoom", 
                        "devices": {
                            "LIGHT": [
                                {
                                    "id": "test-light-1",
                                    "names": ["Test Light"],
                                    "types": ["LIGHT"],
                                    "traits": ["OnOff"],
                                    "room_name": "TestRoom",
                                    "structure": "TestHome",
                                    "toggles_modes": [],
                                    "device_state": [{"name": "on", "value": False}]
                                }
                            ]
                        }
                    }
                }
            }
        }
    }

@pytest.fixture
def temp_db_file(sample_db_data):
    """Create a temporary JSON file with sample database data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_db_data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_state_clears_existing_data(temp_db_file):
    """Test that load_state clears existing data before loading new data."""
    from google_home.SimulationEngine.db import DB
    
    # Setup: Add some initial data to DB
    original_data = DB.copy()  # Save original state
    DB.update({"structures": {"OldHome": {"name": "OldHome", "rooms": {}}}})
    assert "OldHome" in DB.get("structures", {})
    
    try:
        # Act: Load new state
        load_state(temp_db_file)
        
        # Assert: Old data is cleared, new data is loaded
        assert "OldHome" not in DB.get("structures", {})
        assert "TestHome" in DB.get("structures", {})
        assert DB["structures"]["TestHome"]["name"] == "TestHome"
    finally:
        # Restore original state
        DB.clear()
        DB.update(original_data)

def test_load_state_prevents_data_accumulation(temp_db_file):
    """Test that multiple calls to load_state don't accumulate data."""
    from google_home.SimulationEngine.db import DB
    
    # Save original state
    original_data = DB.copy()
    
    try:
        # First load
        load_state(temp_db_file)
        initial_device_count = len(DB["structures"]["TestHome"]["rooms"]["TestRoom"]["devices"]["LIGHT"])
        
        # Second load of same data
        load_state(temp_db_file)
        final_device_count = len(DB["structures"]["TestHome"]["rooms"]["TestRoom"]["devices"]["LIGHT"])
        
        # Assert: Device count should be the same, not doubled
        assert initial_device_count == final_device_count == 1
    finally:
        # Restore original state
        DB.clear()
        DB.update(original_data)

def test_restore_default_data_clears_existing_data(sample_db_data):
    """Test that restore_default_data clears existing data before loading default data."""
    from google_home.SimulationEngine.db import DB
    
    # Setup: Mock the default DB file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_db_data, f)
        temp_path = f.name
    
    # Save original state
    original_data = DB.copy()
    
    try:
        # Setup: Add some initial data to DB
        DB.update({"structures": {"ExistingHome": {"name": "ExistingHome", "rooms": {}}}})
        assert "ExistingHome" in DB.get("structures", {})
        
        # Mock the DEFAULT_DB_PATH to point to our temp file
        with patch('google_home.SimulationEngine.db.DEFAULT_DB_PATH', temp_path):
            # Act: Restore default data
            restore_default_data()
        
        # Assert: Old data is cleared, default data is loaded
        assert "ExistingHome" not in DB.get("structures", {})
        assert "TestHome" in DB.get("structures", {})
    finally:
        os.unlink(temp_path)
        # Restore original state
        DB.clear()
        DB.update(original_data)

def test_restore_default_data_prevents_accumulation(sample_db_data):
    """Test that multiple calls to restore_default_data don't accumulate data."""
    from google_home.SimulationEngine.db import DB
    
    # Setup: Mock the default DB file  
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_db_data, f)
        temp_path = f.name
    
    # Save original state
    original_data = DB.copy()
    
    try:
        with patch('google_home.SimulationEngine.db.DEFAULT_DB_PATH', temp_path):
            # First restore
            restore_default_data()
            initial_device_count = len(DB["structures"]["TestHome"]["rooms"]["TestRoom"]["devices"]["LIGHT"])
            
            # Second restore
            restore_default_data()
            final_device_count = len(DB["structures"]["TestHome"]["rooms"]["TestRoom"]["devices"]["LIGHT"])
            
            # Assert: Device count should be the same, not doubled
            assert initial_device_count == final_device_count == 1
    finally:
        os.unlink(temp_path)
        # Restore original state
        DB.clear()
        DB.update(original_data)

def test_clear_db_functionality():
    """Test that clear_db properly clears all database data."""
    from google_home.SimulationEngine.db import DB
    
    # Save original state
    original_data = DB.copy()
    
    try:
        # Setup: Add test data
        DB.update({
            "structures": {"Home": {"rooms": {}}},
            "actions": [{"id": "action1"}],
            "test_list": ["item1", "item2"],
            "test_dict": {"key": "value"}
        })
        
        # Verify data exists
        assert len(DB) > 0
        assert "structures" in DB
        assert len(DB["actions"]) > 0
        
        # Act: Clear database
        clear_db()
        
        # Assert: All collections are cleared but keys remain
        assert DB["structures"] == {}
        assert DB["actions"] == []
        # Note: clear_db only clears dict and list values, doesn't remove keys
    finally:
        # Restore original state
        DB.clear()
        DB.update(original_data)

def test_save_state_creates_proper_json(sample_db_data):
    """Test that save_state creates a proper JSON file."""
    from google_home.SimulationEngine.db import DB
    
    # Save original state
    original_data = DB.copy()
    
    try:
        # Setup: Load data into DB
        DB.clear()
        DB.update(sample_db_data)
        
        # Create temp file for saving
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Act: Save state
            save_state(temp_path)
            
            # Assert: File exists and contains correct data
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == sample_db_data
            assert "TestHome" in saved_data["structures"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    finally:
        # Restore original state
        DB.clear()
        DB.update(original_data)

def test_db_update_vs_assignment_behavior(sample_db_data):
    """Test the difference between DB.update() and DB = assignment."""
    from google_home.SimulationEngine.db import DB
    
    # Save original state
    original_data = DB.copy()
    
    try:
        # Test 1: DB.update() should merge with existing data
        DB.clear()
        DB.update({"existing_key": "existing_value"})
        DB.update(sample_db_data)
        
        # Should have both existing and new data
        assert "existing_key" in DB
        assert "structures" in DB
        assert DB["existing_key"] == "existing_value"
        
        # Test 2: Simulate what DB = assignment would do (complete replacement)
        # Clear and update simulates the corrected behavior
        DB.clear()
        DB.update(sample_db_data)
        
        # Should only have new data
        assert "existing_key" not in DB
        assert "structures" in DB
    finally:
        # Restore original state
        DB.clear()
        DB.update(original_data)

def test_load_state_with_invalid_json():
    """Test that load_state handles invalid JSON gracefully."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        temp_path = f.name
    
    try:
        with pytest.raises(json.JSONDecodeError):
            load_state(temp_path)
    finally:
        os.unlink(temp_path)

def test_load_state_with_nonexistent_file():
    """Test that load_state handles nonexistent files gracefully."""
    nonexistent_path = "/path/that/does/not/exist.json"
    
    with pytest.raises(FileNotFoundError):
        load_state(nonexistent_path)

def test_load_state_with_minimal_valid_file():
    """Test that load_state handles minimal valid JSON file."""
    from google_home.SimulationEngine.db import DB
    
    # Save original state
    original_data = DB.copy()
    
    # Create minimal valid GoogleHomeDB structure
    minimal_data = {"structures": {}}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(minimal_data, f)
        temp_path = f.name
    
    try:
        # Should not raise an error
        load_state(temp_path)
        
        # DB should be valid with minimal structure
        assert isinstance(DB, dict)
        assert "structures" in DB
        assert DB["structures"] == {}
    finally:
        os.unlink(temp_path)
        # Restore original state
        DB.clear()
        DB.update(original_data)

# endregion
