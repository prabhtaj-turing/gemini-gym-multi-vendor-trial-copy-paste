import pytest
from device_actions.open_url_api import open_url
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import PhoneState, AppType
from device_actions.SimulationEngine.utils import get_phone_state, update_phone_state
from device_actions.SimulationEngine.custom_errors import NoDefaultBrowserError

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    yield

def test_open_url():
    result = open_url(url="https://www.google.com")
    assert result["result"] == "Opened URL: https://www.google.com in Chrome"



    assert get_phone_state().currently_open_app_package == "com.android.chrome"

def test_open_url_with_website_name():
    result = open_url(url="https://www.google.com", website_name="Google")
    assert result["result"] == "Opened URL: https://www.google.com in Chrome"



    assert get_phone_state().currently_open_app_package == "com.android.chrome"

def test_open_url_with_invalid_url():
    with pytest.raises(ValueError):
        open_url(url=123)

def test_open_url_no_default_browser():
    state = get_phone_state()
    for app in state.installed_apps:
        if app.app_type == AppType.BROWSER:
            app.is_default = False
    update_phone_state({"installed_apps": [app.model_dump(mode="json") for app in state.installed_apps]})
    with pytest.raises(NoDefaultBrowserError):
        open_url(url="https://www.google.com")