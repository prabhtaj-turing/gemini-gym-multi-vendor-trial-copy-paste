import pytest
from device_actions.open_home_screen_api import open_home_screen
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import PhoneState
from device_actions.SimulationEngine.utils import get_phone_state, update_phone_state

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    yield

def test_open_home_screen():
    result = open_home_screen()
    assert result["result"] == "Successfully navigated to the home screen"



    assert get_phone_state().currently_open_app_package == "com.google.android.apps.nexuslauncher"

def test_open_home_screen_already_open():
    update_phone_state({"currently_open_app_package": "com.google.android.apps.nexuslauncher"})
    result = open_home_screen()
    assert result["result"] == "Already on the home screen."



    assert get_phone_state().currently_open_app_package == "com.google.android.apps.nexuslauncher"