import pytest
from device_actions.open_app_api import open_app
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import PhoneState
from device_actions.SimulationEngine.utils import get_phone_state, update_phone_state
from device_actions.SimulationEngine.custom_errors import AppNotFoundError, AppNameAndPackageMismatchError

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    yield

def test_open_app():
    result = open_app(app_name="Google Maps")
    assert result["result"] == "Opened app: Google Maps"

    assert get_phone_state().currently_open_app_package == "com.google.android.apps.maps"

def test_open_app_with_package_name():
    result = open_app(app_name="Google Maps", app_package_name="com.google.android.apps.maps")
    assert result["result"] == "Opened app: Google Maps"

    assert get_phone_state().currently_open_app_package == "com.google.android.apps.maps"

def test_open_app_with_extras():
    result = open_app(app_name="Pixel Screenshots", extras='{"query": "search for cats"}')
    assert result["result"] == "Opened app: Pixel Screenshots"

    assert get_phone_state().currently_open_app_package == "com.google.android.apps.photosgo"

def test_open_app_with_invalid_app_name():
    with pytest.raises(ValueError):
        open_app(app_name=123)

def test_open_app_not_found():
    with pytest.raises(AppNotFoundError):
        open_app(app_name="New App")

def test_open_app_with_fallback(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "Google Maps"
    result = open_app(app_name="maps")
    assert result["result"] == "Opened app: Google Maps"

    assert get_phone_state().currently_open_app_package == "com.google.android.apps.maps"

def test_open_app_with_mismatched_package_name():
    with pytest.raises(AppNameAndPackageMismatchError):
        open_app(app_name="Google Maps", app_package_name="com.google.android.apps.photos")


def test_open_app_pixel_screenshots_extras_empty_object():
    with pytest.raises(ValueError):
        open_app(app_name="Pixel Screenshots", extras='{}')


def test_open_app_pixel_screenshots_extras_command_injection_like_query():
    # Should not execute anything; simply treat as data and open the app
    dangerous_extras = '{"query": "find photos; ls -la /"}'
    result = open_app(app_name="Pixel Screenshots", extras=dangerous_extras)
    assert result["result"] == "Opened app: Pixel Screenshots"

def test_open_app_empty_name_llm_not_found(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "NOT FOUND"
    with pytest.raises(AppNotFoundError):
        open_app(app_name="")

def test_open_app_empty_name_llm_failure_maps_to_not_found(monkeypatch):
    # Simulate LLM failing (e.g., missing API key) and ensure we still raise AppNotFoundError
    import device_actions.open_app_api as open_app_api

    def _raise_llm_failure(*args, **kwargs):
        raise Exception('LLM failure')

    monkeypatch.setattr(open_app_api, 'call_llm', _raise_llm_failure)
    with pytest.raises(AppNotFoundError):
        open_app(app_name="")

def test_open_app_with_invalid_package_name():
    with pytest.raises(ValueError):
        open_app(app_name="Google Maps", app_package_name="invalid-package-name")

def test_open_app_not_found_with_fallback(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "Not an app"
    with pytest.raises(AppNotFoundError):
        open_app(app_name="not an app")

def test_open_app_already_open():
    update_phone_state({"currently_open_app_package": "com.google.android.apps.maps"})
    result = open_app(app_name="Google Maps")
    assert result["result"] == "App 'Google Maps' is already open."

    assert get_phone_state().currently_open_app_package == "com.google.android.apps.maps"

def test_open_app_with_no_fallback(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "Not an app"
    with pytest.raises(AppNotFoundError):
        open_app(app_name="some app")

def test_open_app_with_no_match(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "Not an app"
    with pytest.raises(AppNotFoundError):
        open_app(app_name="some app")

def test_open_app_with_no_match_and_no_fallback(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "NOT FOUND"
    with pytest.raises(AppNotFoundError):
        open_app(app_name="some app")

def test_open_app_with_mismatched_package_name():
    with pytest.raises(AppNameAndPackageMismatchError):
        open_app(app_name="Google Maps", app_package_name="com.google.android.apps.photos")


def test_open_app_with_package_allows_fallback_when_name_not_found(llm_mocker):
    if llm_mocker:
        llm_mocker.return_value = "Google Maps"
    result = open_app(app_name="YouTube", app_package_name="com.google.android.youtube")
    assert result["result"] == "Opened app: Google Maps"