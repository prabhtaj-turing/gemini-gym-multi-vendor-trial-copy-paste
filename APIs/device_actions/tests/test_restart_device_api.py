import pytest
from device_actions.restart_device_api import restart_device
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import PhoneState
from device_actions.SimulationEngine.utils import get_phone_state

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    DB["phone_state"]["is_on"] = True
    DB["phone_state"]["last_shutdown_timestamp"] = None
    DB["phone_state"]["last_restart_timestamp"] = None
    yield

def test_restart_device():
    result = restart_device()
    assert result["result"] == "Opened power options menu"



    assert DB["phone_state"]["is_on"] == True
    assert DB["phone_state"]["last_shutdown_timestamp"] is None
    assert DB["phone_state"]["last_restart_timestamp"] is not None