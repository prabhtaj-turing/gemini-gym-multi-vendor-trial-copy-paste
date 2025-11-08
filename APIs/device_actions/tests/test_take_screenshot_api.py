
import pytest
from device_actions.take_screenshot_api import take_screenshot, DB

@pytest.fixture(autouse=True)
def clear_db():
    initial_db_state = {
        "phone_state": {
            "photos": [],
            "videos": [],
            "screenshots": [],
        }
    }
    DB.clear()
    DB.update(initial_db_state)
    yield

def test_take_screenshot():
    result = take_screenshot()
    assert result["result"] == "Captured a screenshot"

def test_take_screenshot_adds_to_db():
    take_screenshot()
    assert len(DB["phone_state"]["screenshots"]) == 1
    assert "Screenshot_" in DB["phone_state"]["screenshots"][0]["name"]
