import pytest
from device_actions.open_websearch_api import open_websearch
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.models import PhoneState, AppType
from device_actions.SimulationEngine.utils import get_phone_state, update_phone_state
from device_actions.SimulationEngine.custom_errors import NoDefaultBrowserError

@pytest.fixture(autouse=True)
def clear_db():
    DB["phone_state"] = PhoneState().model_dump(mode="json")
    yield

def test_open_websearch():
    result = open_websearch(query="cats")
    assert result["result"] == "Opened websearch with query: cats in Chrome"



    assert get_phone_state().currently_open_app_package == "com.android.chrome"

def test_open_websearch_with_invalid_query():
    with pytest.raises(ValueError):
        open_websearch(query=123)

def test_open_websearch_no_default_browser():
    state = get_phone_state()
    for app in state.installed_apps:
        if app.app_type == AppType.BROWSER:
            app.is_default = False
    update_phone_state({"installed_apps": [app.model_dump(mode="json") for app in state.installed_apps]})
    with pytest.raises(NoDefaultBrowserError):
        open_websearch(query="cats")