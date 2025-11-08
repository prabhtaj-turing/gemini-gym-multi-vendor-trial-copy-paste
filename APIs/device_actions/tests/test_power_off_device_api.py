import pytest
from device_actions.power_off_device_api import power_off_device
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

def test_power_off_device():
    result = power_off_device()
    assert result["result"] == "Opened power options menu"



    assert DB["phone_state"]["is_on"] == False
    assert DB["phone_state"]["last_shutdown_timestamp"] is not None
    assert DB["phone_state"]["last_restart_timestamp"] is None