from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
from home_assistant.SimulationEngine.db import DB
from typing import Literal, List, Optional
from home_assistant.SimulationEngine.utils import _get_home_assistant_devices, _get_device_type, allowed_states

# Function to return available devices
@tool_spec(
    spec={
        'name': 'list_devices',
        'description': 'Retrieve all entities in Home Assistant, optionally filtered by domain, to monitor and manage devices, automations, and system components effectively.',
        'parameters': {
            'type': 'object',
            'properties': {
                'domain': {
                    'type': 'string',
                    'description': """ Optional domain filter (e.g., light, switch, automation).
                    If not provided, returns all entities. """
                }
            },
            'required': []
        }
    }
)
def list_devices(domain: Optional[str] = None) -> dict:
    """
    Retrieve all entities in Home Assistant, optionally filtered by domain, to monitor and manage devices, automations, and system components effectively.

    Args:
        domain (Optional[str]): Optional domain filter (e.g., light, switch, automation).
            If not provided, returns all entities.

    Returns:
        dict: A dictionary with an "entities" key containing all matching entities.
    """
    home_assistant_devices = _get_home_assistant_devices()
    if domain:
        return {
            "entities": [{id: device} for id, device in home_assistant_devices.items() if device.get('type','').lower() == domain.lower()]
        }
    return {
        "entities": [{id: device} for id, device in home_assistant_devices.items()]
    }

@tool_spec(
    spec={
        'name': 'get_device_info',
        'description': 'Retrieve all informations of a specific Home Assistant entity, such as a light or sensor, by providing its device ID for real-time monitoring and control.',
        'parameters': {
            'type': 'object',
            'properties': {
                'device_id': {
                    'type': 'string',
                    'description': 'The device ID to get state for (e.g., "LIGHT_001").'
                }
            },
            'required': [
                'device_id'
            ]
        }
    }
)
def get_device_info(device_id: str) -> dict:
    """
        Retrieve all informations of a specific Home Assistant entity, such as a light or sensor, by providing its device ID for real-time monitoring and control.

        Args:
            device_id (str): The device ID to get state for (e.g., "LIGHT_001").

        Returns:
            dict: A dictionary containing the device ID and its informations.

        Raises:
            ValueError: If 'device_id' is missing or not found in the database.
        """
    # Function to get the state of a specific device
    home_assistant_devices = _get_home_assistant_devices()
    if device_id not in home_assistant_devices:
        raise KeyError("device_id must be a valid device ID.")
    return {
            "entity_id": device_id,
            "state": home_assistant_devices.get(device_id, {})
        }   

@tool_spec(
    spec={
        'name': 'get_state',
        'description': 'Retrieve the current state (on/off) of a specific Home Assistant entity, such as a light or sensor, by providing its entity ID for real-time monitoring and control.',
        'parameters': {
            'type': 'object',
            'properties': {
                'entity_id': {
                    'type': 'string',
                    'description': 'The device ID to get state for (e.g., "LIGHT_001").'
                }
            },
            'required': [
                'entity_id'
            ]
        }
    }
)
def get_state(entity_id: str) -> dict:
    """
        Retrieve the current state (on/off) of a specific Home Assistant entity, such as a light or sensor, by providing its entity ID for real-time monitoring and control.

        Args:
            entity_id (str): The device ID to get state for (e.g., "LIGHT_001").

        Returns:
            dict: A dictionary containing the entity ID and its state.

        Raises:
            ValueError: If 'entity_id' is missing or not found in the database.
        """
    # Function to get the state of a specific device
    home_assistant_devices = _get_home_assistant_devices()
    if entity_id not in home_assistant_devices:
        raise ValueError("entity_id must be a valid device ID.")
    return {
            "entity_id": entity_id,
            "state": home_assistant_devices.get(entity_id, {}).get('attributes', {}).get('state', {})
        }   

@tool_spec(
    spec={
        'name': 'toggle_device',
        'description': """ Controls the state of a Home Assistant device.
        
        If 'state' is provided, sets the device to the state if it's valid for its type.
        If 'state' is not provided, cycles to the next allowed state for the device.
        Allowed states are 'On'/'Off' for electronic devices and
        'Open'/'Closed' or 'Locked/Unlocked' for openable items like doors and windows. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'entity_id': {
                    'type': 'string',
                    'description': 'The entity ID to control (e.g., "LIGHT_001").'
                },
                'state': {
                    'type': 'string',
                    'description': """ The desired state to set.
                    If None, the device will cycle to its next allowed state. Defaults to None. """
                }
            },
            'required': [
                'entity_id'
            ]
        }
    }
)
def toggle_device(entity_id: str, state: Optional[str] = None) -> dict:
    """
    Controls the state of a Home Assistant device.
    If 'state' is provided, sets the device to the state if it's valid for its type.
    If 'state' is not provided, cycles to the next allowed state for the device.
    Allowed states are 'On'/'Off' for electronic devices and
    'Open'/'Closed' or 'Locked/Unlocked' for openable items like doors and windows.

    Args:
        entity_id (str): The entity ID to control (e.g., "LIGHT_001").
        state (Optional[str]): The desired state to set.
            If None, the device will cycle to its next allowed state. Defaults to None.

    Returns:
        dict: {"status": "SUCCESS"} if updated successfully.

    Raises:
        ValueError: If entity_id is missing, not found, its device type is not defined
                    in `allowed_states`, the provided state is invalid for the device type,
                    or (when cycling) its current state is not in the allowed list.
    """
    home_assistant_devices = _get_home_assistant_devices()

    if not entity_id:
        raise ValueError("Missing required field: entity_id")
    if entity_id not in home_assistant_devices:
        raise ValueError(f"Entity '{entity_id}' not found.")

    device_info = home_assistant_devices[entity_id]
    current_device_state_value = device_info["attributes"].get("state")

    device_type = _get_device_type(entity_id, home_assistant_devices)

    if device_type not in allowed_states:
        raise ValueError(f"Device type '{device_type}' for entity '{entity_id}' not defined in allowed_states.")

    states_for_device_type: List[str] = allowed_states[device_type]

    if not states_for_device_type:
        raise ValueError(f"No allowed states defined for device type '{device_type}'.")

    new_state_to_set: str

    if state is not None:
        # User provided a specific state
        if state.lower() not in [state.lower() for state in states_for_device_type]:
            raise ValueError(
                f"Invalid state '{state}' for device type '{device_type}'. "
                f"Allowed states are: {states_for_device_type}."
            )
        new_state_index = [st.lower() for st in states_for_device_type].index(state.lower())
        new_state_to_set = states_for_device_type[new_state_index]
        action_type = "Set"
        # print(f"Device '{entity_id}' is now in state '{new_state_to_set}'")
    else:
        # No state provided, so cycle
        action_type = "Cycled"
        try:
            current_state_index = [state.lower() for state in states_for_device_type].index(current_device_state_value.lower())
        except ValueError:
            print_log(
                f"Warning: Current state '{current_device_state_value}' for '{entity_id}' "
                f"not in allowed states {states_for_device_type}. Defaulting to first allowed state for cycling."
            )
            new_state_to_set = states_for_device_type[0]
        else:
            next_state_index = (current_state_index + 1) % len(states_for_device_type)
            new_state_to_set = states_for_device_type[next_state_index]

    # print(f"Device '{entity_id}' is now in state '{new_state_to_set}'")
    # Update the device's state
    home_assistant_devices[entity_id]["attributes"]["state"] = new_state_to_set
    # Optional: print statement for demonstration during development
    # print(f"{action_type} '{entity_id}' from '{current_device_state_value}' to '{new_state_to_set}'")

    return {"status": "SUCCESS"}

@tool_spec(
    spec={
        'name': 'set_device_property',
        'description': 'Update a specific Home Assistant device properties based on a dictionary containing the new attributes values, enabling automated control of connected devices and routines.',
        'parameters': {
            'type': 'object',
            'properties': {
                'entity_id': {
                    'type': 'string',
                    'description': 'The entity ID to update'
                },
                'new_attributes': {
                    'type': 'object',
                    'description': """ A dictionary containing key-value pairs representing the device's properties to update. Any device-specific attributes are accepted and stored as-is under the device's `attributes`.
                    Properties:
                    Note: Any additional device-specific attributes are accepted and stored as-is
                        under the device's `attributes`. """,
                    'properties': {
                        'state': {
                            'type': 'string',
                            'description': """ Desired device state. Allowed values vary by device type. (e.g., "On"/"Off" for lights).
                                    Allowed values:
                                        "light": ["On", "Off"],
                                        "fan": ["On", "Off"],
                                        "pump": ["On", "Off"],
                                        "sprinkler": ["On", "Off"],
                                        "door": ["Open", "Closed", "Locked", "Unlocked"],
                                        "window": ["Open", "Closed"],
                                        "wifi": ["On", "Off"],
                                        "frame": ["On", "Off"],
                                        "speaker": ["On", "Off"],
                                        "clock": ["On", "Off"],
                                        "tv": ["On", "Off"],
                                        "alarm": ["On", "Off"],
                                        "vacuum": ["On", "Off"],
                                        "pet_feeder": ["On", "Off"],
                                        "curtain": ["Open", "Closed"] """
                        },
                        'brightness': {
                            'type': 'integer',
                            'description': """ Brightness level for compatible devices (e.g., lights, screens), typically
                                     from 0 to 100. """
                        },
                        'name': {
                            'type': 'string',
                            'description': """ Optional friendly name for the device. If provided, stored on the device and can
                                     be used by functions like `get_id_by_name`. """
                        }
                    },
                    'required': [
                        'state',
                        'brightness'
                    ]
                }
            },
            'required': [
                'entity_id',
                'new_attributes'
            ]
        }
    }
)
def set_device_property(entity_id: str, new_attributes: dict) -> dict:
    """
    Update a specific Home Assistant device properties based on a dictionary containing the new attributes values, enabling automated control of connected devices and routines.

    Args:
        entity_id (str): The entity ID to update
        new_attributes (dict): A dictionary containing key-value pairs representing the device's properties to update. Any device-specific attributes are accepted and stored as-is under the device's `attributes`.
            Properties:
                state (str): Desired device state. Allowed values vary by device type. (e.g., "On"/"Off" for lights).
                    Allowed values:
                        "light": ["On", "Off"],
                        "fan": ["On", "Off"],
                        "pump": ["On", "Off"],
                        "sprinkler": ["On", "Off"],
                        "door": ["Open", "Closed", "Locked", "Unlocked"],
                        "window": ["Open", "Closed"],
                        "wifi": ["On", "Off"],
                        "frame": ["On", "Off"],
                        "speaker": ["On", "Off"],
                        "clock": ["On", "Off"],
                        "tv": ["On", "Off"],
                        "alarm": ["On", "Off"],
                        "vacuum": ["On", "Off"],
                        "pet_feeder": ["On", "Off"],
                        "curtain": ["Open", "Closed"]
                brightness (int): Brightness level for compatible devices (e.g., lights, screens), typically
                    from 0 to 100.
                name (Optional[str]): Optional friendly name for the device. If provided, stored on the device and can
                    be used by functions like `get_id_by_name`.
            Note: Any additional device-specific attributes are accepted and stored as-is
                under the device's `attributes`.

    Returns:
        dict: {"status": "SUCCESS"} if updated.

    Raises:
        TypeError: If required parameter is not a dictionary.
        ValueError: If required parameters are missing or invalid.
    """
    home_assistant_devices = _get_home_assistant_devices()
    if not entity_id:
        raise ValueError("Missing required field: entity_id")
    if entity_id not in home_assistant_devices:
        raise ValueError(f"Entity '{entity_id}' not found.")
    if not new_attributes:
        raise ValueError("Missing required field: new_attributes")
    if not isinstance(new_attributes, dict):
        raise TypeError("new_attributes must be a dictionary.")

    for attr, value in new_attributes.items():
        home_assistant_devices[entity_id]['attributes'][attr] = value
    return {"status": "SUCCESS"}


@tool_spec(
    spec={
        'name': 'get_id_by_name',
        'description': 'Retrieve the device_id based on a device name.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of a device.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def get_id_by_name(name: str) -> str:
    """
    Retrieve the device_id based on a device name.

    Args:
        name (str): The name of a device.

    Returns:
        str: The device ID associated to a device.

    Raises:
        ValueError: If 'name' is missing or not found.
    """
    home_assistant_devices = _get_home_assistant_devices()
    for device_id, device in home_assistant_devices.items():
        if device.get('name') == name:
            return device_id
    raise ValueError(f"No device found with name '{name}'.")