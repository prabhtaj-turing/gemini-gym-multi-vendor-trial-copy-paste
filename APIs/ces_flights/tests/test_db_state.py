import os
import pytest
import sys
from unittest.mock import patch

# Add the parent directory to the path to fix imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ces_flights.SimulationEngine import db
from ces_flights.SimulationEngine.custom_errors import DatabaseError

TEST_DB_PATH = "test_state.json"

# Module-level patcher
save_patcher = None

def setup_function():
    global save_patcher
    # Mock the automatic save to default DB file
    save_patcher = patch('SimulationEngine.db._save_state_to_file')
    save_patcher.start()
    
    db.DB.clear()
    db.DB.update({"flight_bookings": {}, "_end_of_conversation_status": {}})

def teardown_function():
    global save_patcher
    if save_patcher:
        save_patcher.stop()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_new_record_id_format():
    record_id = db.new_record_id("search")
    assert record_id.startswith("search_")

def test_save_and_load_state(tmp_path):
    path = tmp_path / "state.json"
    db.DB["flight_bookings"]["id1"] = {
        "booking_id": "id1",
        "flight_id": "TEST123",
        "travelers": [],
        "status": "confirmed"
    }
    db.save_state(str(path))
    db.DB.clear()
    db.load_state(str(path))
    assert "id1" in db.DB["flight_bookings"]

def test_load_state_invalid_file(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{not-valid-json}")
    with pytest.raises(DatabaseError):
        db.load_state(str(path))

def test_get_minified_state_counts():
    db.DB["flight_bookings"]["a"] = {"test": 1}
    summary = db.get_minified_state()
    assert summary["flight_bookings"] == 1
