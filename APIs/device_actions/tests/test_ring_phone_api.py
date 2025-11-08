import pytest
from device_actions.ring_phone_api import ring_phone
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import PhoneState
from device_actions.SimulationEngine.utils import get_phone_state

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    yield

def test_ring_phone():
    result = ring_phone()
    assert result["result"] == "Successfully rang the user's phone."



    assert get_phone_state().last_ring_timestamp is not None