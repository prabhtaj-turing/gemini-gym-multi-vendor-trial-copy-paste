from common_utils.tool_spec_decorator import tool_spec
from sdm.SimulationEngine.db import DB
from sdm.SimulationEngine.events import EVENTS
from sdm.SimulationEngine.utils import resolve_callable_from_path, _format_to_sdm_device
from typing import Optional, Dict, Any

@tool_spec(
    spec={
        'name': 'execute_command',
        'description': 'Executes a command on a specific device managed by the enterprise.',
        'parameters': {
            'type': 'object',
            'properties': {
                'device_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the device within the enterprise. For example, "CAM_001"'
                },
                'project_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the enterprise or project.'
                },
                'command_request': {
                    'type': 'object',
                    'description': 'The command request payload, Contains the keys:',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': """ The name of the command to execute. One of the following (followed by a brief explanation):
                                 - sdm.devices.commands.generate_camera_event_image (retrieve the image from a camera through a triggered event)
                                - sdm.devices.commands.generate_rtsp_stream (start the rtsp stream mode of a camera)
                                - sdm.devices.commands.stop_rtsp_stream (stop the rtsp stream mode of a camera)
                                - sdm.devices.commands.generate_image_from_rtsp_stream (retrieve the image from a camera through its ongoing rtsp stream)
                                - sdm.devices.commands.generate_web_rtc_stream (start the web_rtc stream mode of a camera)
                                - sdm.devices.commands.stop_web_rtc_stream (stop the web_rtc stream mode of a camera)
                                - sdm.devices.commands.generate_image_from_web_rtc_stream (retrieve the image from a camera through its ongoing web_rtc stream) """
                        },
                        'params': {
                            'type': 'object',
                            'description': """ A dictionary of parameters for the command. This can be
                                 omitted if a command requires no parameters. The parameters for each
                                command are as follows: for `sdm.devices.commands.generate_camera_event_image`
                                the `event_id` (the unique identifier for a camera event) is required; for
                                `sdm.devices.commands.stop_rtsp_stream` the `stream_extension_token` (a unique
                                token that identifies an active RTSP stream) is required; for
                                `sdm.devices.commands.generate_image_from_rtsp_stream` the `rtsp_url` (the
                                RTSP URL from which the camera stream can be accessed) is required; for
                                `sdm.devices.commands.generate_web_rtc_stream` the `offer_sdp` (the SDP offer
                                from the client, containing proposed WebRTC session parameters) is required; for
                                `sdm.devices.commands.stop_web_rtc_stream` the `stream_media_session_id` (a unique
                                identifier for an active WebRTC media session) is required; and for
                                `sdm.devices.commands.generate_image_from_web_rtc_stream` the `answer_sdp` (the
                                SDP answer from the client, sent in response to the SDP offer) is required.
                                The `sdm.devices.commands.generate_rtsp_stream` command does not require any parameters. """,
                            'properties': {},
                            'required': []
                        }
                    },
                    'required': [
                        'command'
                    ]
                }
            },
            'required': [
                'device_id',
                'project_id',
                'command_request'
            ]
        }
    }
)
def execute_command(
    device_id: str,
    project_id: str,
    command_request: Dict[str, Any],
) -> dict:
    """
    Executes a command on a specific device managed by the enterprise.

    Args:
        device_id (str): The unique identifier of the device within the enterprise. For example, "CAM_001"
        project_id (str): The unique identifier of the enterprise or project.
        command_request (Dict[str, Any]): The command request payload, Contains the keys:
            - command (str): The name of the command to execute. One of the following (followed by a brief explanation):
                - sdm.devices.commands.generate_camera_event_image (retrieve the image from a camera through a triggered event)
                - sdm.devices.commands.generate_rtsp_stream (start the rtsp stream mode of a camera)
                - sdm.devices.commands.stop_rtsp_stream (stop the rtsp stream mode of a camera)
                - sdm.devices.commands.generate_image_from_rtsp_stream (retrieve the image from a camera through its ongoing rtsp stream)
                - sdm.devices.commands.generate_web_rtc_stream (start the web_rtc stream mode of a camera)
                - sdm.devices.commands.stop_web_rtc_stream (stop the web_rtc stream mode of a camera)
                - sdm.devices.commands.generate_image_from_web_rtc_stream (retrieve the image from a camera through its ongoing web_rtc stream)
            - params (Optional[Dict[str, str]]): A dictionary of parameters for the command. This can be
                omitted if a command requires no parameters. The parameters for each
                command are as follows: for `sdm.devices.commands.generate_camera_event_image`
                the `event_id` (the unique identifier for a camera event) is required; for
                `sdm.devices.commands.stop_rtsp_stream` the `stream_extension_token` (a unique
                token that identifies an active RTSP stream) is required; for
                `sdm.devices.commands.generate_image_from_rtsp_stream` the `rtsp_url` (the
                RTSP URL from which the camera stream can be accessed) is required; for
                `sdm.devices.commands.generate_web_rtc_stream` the `offer_sdp` (the SDP offer
                from the client, containing proposed WebRTC session parameters) is required; for
                `sdm.devices.commands.stop_web_rtc_stream` the `stream_media_session_id` (a unique
                identifier for an active WebRTC media session) is required; and for
                `sdm.devices.commands.generate_image_from_web_rtc_stream` the `answer_sdp` (the
                SDP answer from the client, sent in response to the SDP offer) is required.
                The `sdm.devices.commands.generate_rtsp_stream` command does not require any parameters.

    Returns:
        dict: The response from the API, containing the result of the command execution.

    Raises:
        ValueError: If any required parameter is missing or invalid.
    """
    # Input Validation
    if not project_id:
        raise ValueError("project_id is required")
    if not device_id:
        raise ValueError("device_id is required")
    if not command_request:
        raise ValueError("command_request is required")
    if not command_request.get("command"):
        raise ValueError("command is required")
    
    # Execute Command
    command_name = command_request.get("command")
    command_params = command_request.get("params", {})
    command_params["device_id"] = device_id
    command_params["project_id"] = project_id
    command_function = resolve_callable_from_path(command_name)
    if not command_function:
        raise ValueError(f"Command {command_name} not found")
    return command_function(**command_params)

@tool_spec(
    spec={
        'name': 'get_device_info',
        'description': 'Retrieves information about an authorized device.',
        'parameters': {
            'type': 'object',
            'properties': {
                'device_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the device within the enterprise.'
                },
                'project_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the enterprise or project.'
                }
            },
            'required': [
                'device_id',
                'project_id'
            ]
        }
    }
)
def get_device_info(
    device_id: str,
    project_id: str
) -> dict:
    """
    Retrieves information about an authorized device.

    Args:
        device_id (str): The unique identifier of the device within the enterprise.
        project_id (str): The unique identifier of the enterprise or project.

    Returns:
        dict: The device information including all traits and the parentRelations object. 
            Contains the following keys:
                - name (str): The internal name of the device built from the enterprise and device id.
                - type (str): The type of the device.
                - traits (dict): The traits of the device including the reference name of the device.
                - parentRelations (list): The parent relations of the device.  

    Raises:
        ValueError: If any required parameter is missing or invalid.
    """
    # Input Validation
    if not project_id:
        raise ValueError("project_id is required")
    if not device_id:
        raise ValueError("device_id is required")
    
    # Get Device Info
    device_info = DB.get("environment", {}).get("sdm", {}).get("devices", {}).get(device_id, {})
    if not device_info:
        raise ValueError(f"Device {device_id} not found")
    device = _format_to_sdm_device((device_id, device_info), project_id)
    return device

@tool_spec(
    spec={
        'name': 'list_devices',
        'description': """ Makes a GET call to retrieve a list of all devices that the user has authorized
        
        for a given enterprise. The response typically includes a collection of device objects. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_devices(
) -> dict:
    """
    Makes a GET call to retrieve a list of all devices that the user has authorized
    for a given enterprise. The response typically includes a collection of device objects.

    Returns:
        dict: The response containing a list of device objects.
            Contains the following keys:
                - devices (list): The list of device objects. The list is empty if no devices are found.
                Each device object contains the following keys:
                    - name (str): The internal name of the device built from the enterprise and device id.
                    - type (str): The type of the device.
                    - traits (dict): The traits of the device including the reference name of the device.
                    - project_id (str): The enterprise or project id that the device belongs to.
                    - parentRelations (list): The parent relations of the device.  
    """
    project_id = next(
        (v for k, v in DB.items() if k.lower() == "project_id"), "project_id"
    )

    # Get Devices
    devices = DB.get("environment", {}).get("sdm", {}).get("devices", {})
    devices_list = []
    for device_dict in devices.items():
        device = _format_to_sdm_device(device_dict, project_id)
        devices_list.append(device)
    response = {"devices": devices_list}
    return response


@tool_spec(
    spec={
        'name': 'get_events_list',
        'description': 'Returns a list of events that were triggered.',
        'parameters': {
            'type': 'object',
            'properties': {
                'device_id': {
                    'type': 'string',
                    'description': 'Optional unique identifier of a device to filter events. For example, "CAM_001".'
                },
                'event_type': {
                    'type': 'string',
                    'description': """ Optional event_type to filter events.
                    Should be one of: "Motion", "Person", "Sound" or "Chime".
                    It also accepts formats such as: "sdm.devices.events.CameraMotion.Motion".
                    If no device_id or event_type provided, returns all events. """
                }
            },
            'required': []
        }
    }
)
def get_events_list(device_id: Optional[str] = None, event_type: Optional[str] = None) -> list:
    """
    Returns a list of events that were triggered.

    Args:
        device_id (Optional[str]): Optional unique identifier of a device to filter events. For example, "CAM_001".
        event_type (Optional[str]): Optional event_type to filter events.
            Should be one of: "Motion", "Person", "Sound" or "Chime".
            It also accepts formats such as: "sdm.devices.events.CameraMotion.Motion".
            If no device_id or event_type provided, returns all events.

    Returns:
        list: A list containing event payloads.
    """
    # Get Events
    events = EVENTS
    filtered_events = []

    if device_id:
        for event_payload in events:
            payload_device_id = event_payload.get("resourceUpdate").get("name").split("/")[-1]
            if payload_device_id == device_id:
                filtered_events.append(event_payload)
    else:
        filtered_events = events

    events = filtered_events
    filtered_events = []

    if event_type:
        trigger = event_type.split('.')[-1]
        if trigger not in ["Motion", "Person", "Sound", "Chime"]:
            raise ValueError(f"Event_type '{event_type}' not allowed")
        for event_payload in events:
            payload_event_type = next(iter(event_payload.get("resourceUpdate").get("events"))).split(".")[-1]
            if payload_event_type == trigger:
                filtered_events.append(event_payload)
    else:
        filtered_events = events

    return filtered_events

