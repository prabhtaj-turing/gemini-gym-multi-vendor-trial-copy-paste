"""
Database structure and state management for Google Docs API simulation.
"""

import json
from typing import Dict, Any, List
import sys
import os
import uuid
import base64
from datetime import datetime
from common_utils.ErrorSimulation import ErrorSimulator

# Add the APIs directory to the Python path
# sys.path.append(os.path.join(os.path.dirname(__file__), "../../../APIs"))
sys.path.append("APIs")
from home_assistant.SimulationEngine.db import DB as home_assistant_DB
import home_assistant

DB = home_assistant_DB  # Ensure shared reference
EVENTS = []

def _create_id() -> str:
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf-8').rstrip('=')


def set_cameras_events(map_dict: dict, project_id: str) -> None:
    """
    Set cameras events.

    Args:
        map_dict (dict): The dict containing in key "events" the list of events to update the EVENTS with.
        project_id (str): The unique identifier of the enterprise or project.
    """
    global EVENTS
    EVENTS.clear()
    list_of_events = map_dict.get("events", [])
    for event in list_of_events:
        timestamp = datetime.strptime(event.get("timestamp"), "%Y-%m-%d %H:%M:%S").isoformat(timespec='seconds') + "Z"
        device_id = event.get("camera_id")
        trigger = event.get("trigger")
        if trigger not in ["Motion", "Person", "Sound", "Chime"]:
            raise ValueError(f"Event trigger '{trigger}' not allowed")
        if trigger != "Chime":
            event_type = f"Camera{trigger}.{trigger}"
        else:
            event_type = f"Doorbell{trigger}.{trigger}"
        event_payload = {
            "eventId" : _create_id(),
            "timestamp" : timestamp,
            "resourceUpdate" : {
                "name" : f"enterprises/{project_id}/devices/{device_id}",
                "events" : {
                f"sdm.devices.events.{event_type}" : {
                    "eventSessionId" : _create_id(),
                    "eventId" : _create_id(),
                }
                }
            },
            "userId" : _create_id(),
            "eventThreadId" : _create_id(),
            "eventThreadState" : "STARTED",
            "resourceGroup" : [
                f"enterprises/{project_id}/devices/{device_id}"
            ]
        }
        EVENTS.append(event_payload)

