import pytest
from device_actions.get_installed_apps_api import get_installed_apps
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import PhoneState

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    yield

def test_get_installed_apps():
    result = get_installed_apps()
    assert isinstance(result, list)
    assert len(result) == 8
    assert {"name": "Google Maps"} in result