from sdm.SimulationEngine.db import STATE_DICTS
from sdm.SimulationEngine.db import DB
from sdm.SimulationEngine.events import EVENTS
from sdm.devices.errors import IncorrectEventError
from home_assistant.devices import get_state, list_devices
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from PIL import Image
import base64
import io
import importlib
import json
import urllib.parse
import sdm.SimulationEngine.db as db
import re

def create_state_env():
    influencing_ids = db.INFLUENCING_IDS

    # Create a state to check in STATE_DICTS
    state = {}
    for influencing_id in influencing_ids:
        state_items = DB.get("environment", {}).get("state", {})
        home_assistant_devices = list_devices()
        entities = home_assistant_devices.get('entities', []) if home_assistant_devices else []
        if influencing_id in state_items:
            state[influencing_id] = state_items.get(influencing_id)
        elif entities:
            # Match by key in the entity dict (not by attribute)
            matching_devices = [device for device in entities if influencing_id in device]
            if len(matching_devices) > 1:
                raise ValueError(f"Multiple devices found for {influencing_id}")
            elif len(matching_devices) == 1:
                device_info = matching_devices[0][influencing_id]
                device_type = device_info.get("type", '')
                if device_type:
                    state[device_type.lower()] = get_state(influencing_id).get('state')
                else:
                    raise ValueError(f"Device {influencing_id} has no type")
            else:
                raise ValueError(f"Device {influencing_id} not found in entities")
        else:
            raise ValueError(f"Device {influencing_id} not found")
    return state

def _match_event_id(event_id: str, device_id: str) -> dict:
    payload_data = {}
    for event_payload in EVENTS:
        payload_event_id = next(iter(event_payload.get("resourceUpdate").get("events").values())).get("eventId")
        if payload_event_id == event_id:
            payload_data["event_id"] = event_id
            payload_data["device_id"] = event_payload.get("resourceUpdate").get("name").split("/")[-1]
            payload_data["trigger"] = next(iter(event_payload.get("resourceUpdate").get("events"))).split(".")[-1]
            payload_data["timestamp"] = datetime.strptime(event_payload.get("timestamp"), "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
            # Found event_id
            if device_id != payload_data.get("device_id"):
                raise IncorrectEventError()
            return payload_data
    raise IncorrectEventError()


def _resolve_image_from_event(event_id: str, device_id: str):
    payload_data = _match_event_id(event_id, device_id)
    
    # Retrieving image
    for event in STATE_DICTS.get("events", []):
        trigger = event.get("trigger", "")
        timestamp = event.get("timestamp", "")
        device_id = event.get("camera_id", "")
        if trigger == payload_data.get("trigger") and timestamp == payload_data.get("timestamp") and device_id == payload_data.get("device_id"):
            image_path = event.get("image_path")
            return image_path
            

def _resolve_image(device_id: str):
    current_state = create_state_env()
        
    # Normalize current_state to lowercase keys and values
    norm_current = {str(k).lower(): str(v).lower() for k, v in current_state.items()}
    # Check if only 1 image and no state
    camera_entries = STATE_DICTS.get("cameras", {}).get(device_id, [])
    if len(camera_entries) == 1:
        if "state" not in camera_entries[0]:
            return camera_entries[0]["image_path"]
    # Normal check with state
    for entry in camera_entries:
        entry_state = entry["state"]
        # Normalize entry_state too
        norm_entry = {str(k).lower(): str(v).lower() for k, v in entry_state.items()}
        # Check all current_state items match (case-insensitive)
        if all(norm_entry.get(k) == v for k, v in norm_current.items()):
            return entry["image_path"]
    return None

def process_image_to_url(image_path: str) -> str:
    """
    Processes a relative image path to construct a full, URL-encoded URL.

    The function ensures that the provided `image_path` is appended
    to a predefined base URL. It correctly handles cases where `image_path`
    might inadvertently start with one or more leading slashes, ensuring
    it's treated as relative to the base URL's full path.
    Spaces, question marks, and other special characters intended to be part
    of the path/filename will be properly URL-encoded.

    Args:
        image_path: The path to the image, e.g., "living room/lamp.jpg",
                    "/bedroom/night stand.png", or even paths with special
                    characters like "photos/query?icon.png" (where '?' is
                    part of the filename).

    Returns:
        A string representing the full, correctly formed, and URL-encoded
        URL to the image.
    """
    # The fixed base URL for smart home images.
    # This is assumed to always end with a trailing slash.
    BASE_URL = "https://sdmhomeserver.com/sdm/events/images/"

    # 1. Normalize the image_path by removing any leading slashes.
    path_segment = image_path.lstrip('/')

    # 2. Explicitly URL-encode the path segment.
    encoded_path_segment = urllib.parse.quote(path_segment, safe='/')

    # 3. Combine the BASE_URL with fully encoded path segment.
    final_url = urllib.parse.urljoin(BASE_URL, encoded_path_segment)

    return final_url

def resolve_callable_from_path(path: str):
    """
    Resolves a callable (function) from a fully qualified Python path string.
    Example: 'devices.commands.set_thermostat_mode'
    """
    try:
        module_path, func_name = path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except Exception as e:
        return None


def _format_to_sdm_device(device_dict: dict, project_id: str) -> dict:
    """Format our DB device schema to sdm device schema"""
    device_id, device_info = device_dict
    model = device_info.get("attributes", {}).get("model", "")
    name = device_info.get("name", "")

    current_dir = Path(__file__).parent
    json_path = current_dir / "sdm_devices.json"
    with open(json_path, "r") as file:
        sdm_devices = json.load(file)

    if model not in sdm_devices.keys():
        raise ValueError(f"sdm device {device_id} model is not one of Google allowed models.\nUse one of following: ['Google Nest Cam Indoor', 'Google Nest Cam (indoor, wired)', 'Google Nest Cam (outdoor or indoor, battery)', 'Google Nest Cam IQ Indoor', 'Google Nest Cam IQ Outdoor', 'Google Nest Cam Outdoor', 'Nest Cam with floodlight', 'Nest Doorbell (battery)', 'Nest Doorbell (legacy)', 'Nest Doorbell (wired)', 'Nest Hub Max']")

    traits_schema = sdm_devices.get(model, {}).get("schema", {})
    traits_schema.setdefault("traits", {}).setdefault("sdm.devices.traits.Info", {})["customName"] = name

    device = {
        "name": f"enterprises/{project_id}/devices/{device_id}",
        "type": traits_schema.get("type", ""),
        "traits": traits_schema.get("traits", {}),
        "project_id": project_id,
        "parentRelations": [
            {
                "parent": device_info.get("attributes", {}).get("parent", ""),
                "displayName": name
            }
        ]
    }

    return device

def _generate_answer_sdp(device_schema: dict, image_path: str) -> str:
    video_codec = device_schema.get("traits", {}).get("sdm.devices.traits.CameraLiveStream", {}).get("videoCodecs", [])[0]
    audio_codec = device_schema.get("traits", {}).get("sdm.devices.traits.CameraLiveStream", {}).get("audioCodecs", [])[0]

    # Map codecs to payload types
    codec_payload_map = {
        "H264": ("96", "H264/90000"),
        "VP8": ("96", "VP8/90000"),
        "OPUS": ("111", "opus/48000/2"),
        "AAC": ("97", "mpeg4-generic/48000/2")
    }

    audio_payload_type, audio_codec_info = codec_payload_map.get(audio_codec.upper(), ("111", "opus/48000/2"))
    video_payload_type, video_codec_info = codec_payload_map.get(video_codec.upper(), ("96", "H264/90000"))

    sdp = (
        "v=0\r\n"
        "o=- 46117336 2 IN IP4 127.0.0.1\r\n"
        "s=-\r\n"
        "t=0 0\r\n"
        "a=group:BUNDLE audio video application\r\n"
        "a=msid-semantic: WMS\r\n"
        f"m=audio 9 UDP/TLS/RTP/SAVPF {audio_payload_type}\r\n"
        "c=IN IP4 0.0.0.0\r\n"
        "a=sendonly\r\n"
        "a=rtcp-mux\r\n"
        f"a=rtpmap:{audio_payload_type} {audio_codec_info}\r\n"
        f"m=video 9 UDP/TLS/RTP/SAVPF {video_payload_type}\r\n"
        "c=IN IP4 0.0.0.0\r\n"
        "a=sendonly\r\n"
        "a=rtcp-mux\r\n"
        f"a=rtpmap:{video_payload_type} {video_codec_info}\r\n"
        "m=application 9 DTLS/SCTP 5000\r\n"
        "c=IN IP4 0.0.0.0\r\n"
        "a=sctpmap:5000 webrtc-datachannel 1024\r\n"
        f"a=image-path:{image_path}\r\n"
    )
    return sdp

def _compress_and_encode_base64(image_path, target_size_mb=5, resize_if_too_large=True):
    max_bytes = target_size_mb * 1024 * 1024
    img = Image.open(image_path)

    if resize_if_too_large:
        max_dim = 2048
        if max(img.size) > max_dim:
            scale = max_dim / max(img.size)
            new_size = tuple(int(dim * scale) for dim in img.size)
            img = img.resize(new_size, Image.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Compress in memory with decreasing quality
    for quality in range(95, 19, -5):
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        size = buffer.tell()
        if size <= max_bytes:
            break

    # Encode to base64
    buffer.seek(0)
    encoded_string = base64.b64encode(buffer.read()).decode('utf-8')
    return "Image base64: " + encoded_string

def encrypt_url(url, salt="gemini"):
    combined = f"{salt}{url}"
    encoded = base64.urlsafe_b64encode(combined.encode()).decode()
    return encoded

def decrypt_url(encoded, salt="gemini"):
    decoded = base64.urlsafe_b64decode(encoded.encode()).decode()
    if decoded.startswith(salt):
        return decoded[len(salt):]
    raise ValueError("Invalid salt or corrupted data.")