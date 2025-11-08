
import pytest
from device_actions.open_camera_api import open_camera
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import CameraType, CameraOperation, CameraMode, PhoneState, AppType
from device_actions.SimulationEngine.utils import get_phone_state, update_phone_state
from device_actions.SimulationEngine.custom_errors import NoDefaultCameraError

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    yield

def test_open_camera_no_args():
    result = open_camera()
    assert result["result"] == "Opened Camera"



    state = get_phone_state()
    assert state.camera.is_open is True
    assert state.camera.type is None
    assert state.camera.operation is None
    assert state.currently_open_app_package == "com.google.android.camera"

def test_open_camera_with_camera_type():
    result = open_camera(camera_type=CameraType.FRONT.value)
    assert result["result"] == "Opened Camera with FRONT camera"



    state = get_phone_state()
    assert state.camera.is_open is True
    assert state.camera.type == CameraType.FRONT
    assert state.camera.operation is None
    assert state.currently_open_app_package == "com.google.android.camera"

def test_open_camera_with_camera_operation():
    result = open_camera(camera_operation=CameraOperation.VIDEO.value)
    assert result["result"] == "Opened Camera in VIDEO mode"



    state = get_phone_state()
    assert state.camera.is_open is True
    assert state.camera.type is None
    assert state.camera.operation == CameraOperation.VIDEO
    assert state.currently_open_app_package == "com.google.android.camera"

def test_open_camera_with_all_args():
    result = open_camera(camera_type=CameraType.REAR.value, camera_operation=CameraOperation.PHOTO.value)
    assert result["result"] == "Opened Camera with REAR camera in PHOTO mode"



    state = get_phone_state()
    assert state.camera.is_open is True
    assert state.camera.type == CameraType.REAR
    assert state.camera.operation == CameraOperation.PHOTO
    assert state.currently_open_app_package == "com.google.android.camera"

def test_open_camera_with_invalid_camera_type():
    with pytest.raises(ValueError):
        open_camera(camera_type="INVALID_TYPE")

def test_open_camera_with_invalid_camera_operation():
    with pytest.raises(ValueError):
        open_camera(camera_operation="INVALID_OPERATION")

def test_open_camera_with_camera_mode():
    result = open_camera(camera_mode=CameraMode.PORTRAIT.value)
    assert result["result"] == "Opened Camera"



    state = get_phone_state()
    assert state.camera.is_open is True
    assert state.camera.type is None
    assert state.camera.operation is None
    assert state.currently_open_app_package == "com.google.android.camera"

def test_open_camera_already_open_same_settings():
    update_phone_state({"camera": {"is_open": True, "type": "FRONT", "operation": "PHOTO"}, "currently_open_app_package": "com.google.android.camera"})
    result = open_camera(camera_type="FRONT", camera_operation="PHOTO")
    assert result["result"] == "Camera is already open with the specified settings."



    state = get_phone_state()
    assert state.camera.is_open is True
    assert state.camera.type == CameraType.FRONT
    assert state.camera.operation == CameraOperation.PHOTO
    assert state.currently_open_app_package == "com.google.android.camera"

def test_open_camera_already_open_different_settings():
    update_phone_state({"camera": {"is_open": True, "type": "FRONT", "operation": "PHOTO"}, "currently_open_app_package": "com.google.android.camera"})
    result = open_camera(camera_type="REAR", camera_operation="VIDEO")
    assert result["result"] == "Opened Camera with REAR camera in VIDEO mode"



    state = get_phone_state()
    assert state.camera.is_open is True
    assert state.camera.type == CameraType.REAR
    assert state.camera.operation == CameraOperation.VIDEO
    assert state.currently_open_app_package == "com.google.android.camera"

def test_open_camera_no_default_camera():
    state = get_phone_state()
    for app in state.installed_apps:
        if app.app_type == AppType.CAMERA:
            app.is_default = False
    update_phone_state({"installed_apps": [app.model_dump(mode="json") for app in state.installed_apps]})
    with pytest.raises(NoDefaultCameraError):
        open_camera()
