import pytest
from device_actions.take_photo_api import take_photo, DB
from device_actions.SimulationEngine.models import CameraType, CameraMode

@pytest.fixture(autouse=True)
def clear_db():
    initial_db_state = {
        "actions": [],
        "phone_state": {
            "photos": [],
            "videos": [],
            "screenshots": [],
        }
    }
    DB.clear()
    DB.update(initial_db_state)
    yield

def test_take_photo_no_args(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "3"
    result = take_photo()
    assert result["result"] == "Captured a photo after a delay of 3 seconds"


def test_take_photo_with_camera_type(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "3"
    result = take_photo(camera_type=CameraType.FRONT.value)
    assert result["result"] == "Captured a photo with FRONT camera after a delay of 3 seconds"


def test_take_photo_with_self_timer_delay(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "5"
    result = take_photo(self_timer_delay="5 seconds")
    assert result["result"] == "Captured a photo after a delay of 5 seconds"


def test_take_photo_with_all_args(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "10"
    result = take_photo(camera_type=CameraType.REAR.value, self_timer_delay="10 seconds", camera_mode=CameraMode.PORTRAIT.value)
    assert result["result"] == "Captured a photo with REAR camera after a delay of 10 seconds in PORTRAIT mode"


def test_take_photo_with_invalid_camera_type():
    with pytest.raises(ValueError):
        take_photo(camera_type="INVALID_TYPE")

def test_take_photo_with_invalid_camera_mode():
    with pytest.raises(ValueError):
        take_photo(camera_mode="INVALID_MODE")

def test_take_photo_adds_to_db(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "3"
    take_photo()
    assert len(DB["phone_state"]["photos"]) == 1
    assert "IMG_" in DB["phone_state"]["photos"][0]["name"]

