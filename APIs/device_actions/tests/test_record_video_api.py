import pytest
from device_actions.record_video_api import record_video, DB
from device_actions.SimulationEngine.models import CameraType

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

def test_record_video_no_args():
    result = record_video()
    assert result["result"] == "Recorded a video"


def test_record_video_with_camera_type():
    result = record_video(camera_type=CameraType.FRONT.value)
    assert result["result"] == "Recorded a video with FRONT camera"


def test_record_video_with_video_duration(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "15"
    result = record_video(video_duration="15 seconds")
    assert result["result"] == "Recorded a video for 15 seconds"


def test_record_video_with_all_args(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "30"
    result = record_video(camera_type=CameraType.REAR.value, video_duration="30 seconds")
    assert result["result"] == "Recorded a video with REAR camera for 30 seconds"


def test_record_video_with_invalid_camera_type():
    with pytest.raises(ValueError):
        record_video(camera_type="INVALID_TYPE")

def test_record_video_with_self_timer_delay():
    result = record_video(self_timer_delay="5 seconds")
    assert result["result"] == "Recorded a video"


def test_record_video_adds_to_db():
    record_video()
    assert len(DB["phone_state"]["videos"]) == 1
    assert "VID_" in DB["phone_state"]["videos"][0]["name"]

def test_record_video_invalid_video_duration():
    # Pass an invalid type for video_duration (e.g., int instead of str)
    with pytest.raises(ValueError):
        record_video(video_duration=123)



