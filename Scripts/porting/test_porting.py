import json
import importlib
import inspect
from pathlib import Path
import pytest

# List of all porting services
SERVICES = [
    "contacts",
    "calendar",    
    "gmail",
    "whatsapp"
]
'''    
    "device_settings",
    "media_control",
    "clock",
    "reminders",
    "notes",
]'''

def find_extra_keys(default, ported, path=""):
    """
    Recursively find keys that exist in ported data but not in DefaultDB.

    Args:
        default (dict or list): DefaultDB structure.
        ported (dict or list): PortedDB structure.
        path (str): Current path for reporting.

    Returns:
        list of str: Extra keys in ported data.
    """
    extras = []

    if isinstance(default, dict) and isinstance(ported, dict):
        default_keys = set(default.keys())
        ported_keys = set(ported.keys())

        extra = ported_keys - default_keys
        print(extra)
        for k in extra:
            extras.append(f"Extra key at {path}/{k}" if path else f"Extra key: {k}")

        # Recurse into keys that exist in both
        for k in default_keys & ported_keys:
            extras.extend(find_extra_keys(default[k], ported[k], f"{path}/{k}" if path else k))

    elif isinstance(default, list) and isinstance(ported, list) and default and ported:
        # Compare first element for structure
        extras.extend(find_extra_keys(default[0], ported[0], path=f"{path}[]" if path else "[]"))

    return extras


@pytest.mark.parametrize("service", SERVICES)
def test_porting_with_default(service):
    """
    Ensure ported data does not contain extra/misspelled keys
    compared to DefaultDB.
    """
    # Dynamically import porting module
    module = importlib.import_module(f"Scripts.porting.port_{service}")
    port_func = next(
        (obj for name, obj in inspect.getmembers(module, inspect.isfunction) if name.startswith("port_")),
        None
    )
    assert port_func, f"No porting function found for {service}"

    # Load DefaultDB
    default_path = Path(f"DBs/{service.capitalize()}DefaultDB.json")
    assert default_path.exists(), f"DefaultDB missing for {service}"
    default_data = json.loads(default_path.read_text())

    # Load vendor data
    vendor_path = Path(f"Scripts/porting/PortDBs/{service}/vendor_{service}.json")
    assert vendor_path.exists(), f"Vendor JSON missing for {service}"
    vendor_data = vendor_path.read_text()

    # Port the vendor data
    ported_obj = port_func(vendor_data)

    # Convert Pydantic model to dict
    ported_data = ported_obj.model_dump() if hasattr(ported_obj, "model_dump") else ported_obj.dict()

    # Find extra keys
    extra_keys = find_extra_keys(default_data, ported_data)
    assert not extra_keys, f"Extra keys found in ported data for {service}:\n" + "\n".join(extra_keys)