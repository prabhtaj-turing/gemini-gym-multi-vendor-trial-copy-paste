from sdm.SimulationEngine.db import DB, SERVED_IMAGES, ONGOING_STREAMS
from sdm.SimulationEngine.utils import _resolve_image, _resolve_image_from_event, process_image_to_url, _generate_answer_sdp, _compress_and_encode_base64, encrypt_url, decrypt_url
from sdm.devices import get_device_info
from sdm.devices.errors import CameraNotAvailableError, CommandNotSupportedError, IncorrectEventError
from PIL import Image
from typing import Optional
from datetime import datetime, timedelta
import re
import base64
import uuid

def generate_camera_event_image(event_id: str, device_id: str, project_id: str) -> dict:
    """
    Captures an event image from a camera device for a specific event.

    Args:
        event_id (str): The event identifier.
        device_id (str): The ID of the camera device.
        project_id (str): The ID of the enterprise or project.

    Returns:
        dict: The response from the API, containing the result of the command execution.
    """
    image_path = _resolve_image_from_event(event_id, device_id)
    image_url = process_image_to_url(image_path)
    encoded_url = encrypt_url(image_url)
    # response follows the real API output, however the output is the image base64 format, for LLM usage
    response = {
        "results" : {
            "url" : encoded_url,
            "token" : "g.0.eventToken"
        }
    }

    SERVED_IMAGES["EVENT_IMAGES"].append(image_path)
    try:
        return _compress_and_encode_base64(image_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found at path: {image_path}")
    except Exception as e:
        raise Exception(f"Error converting image to base64: {str(e)}")

def generate_rtsp_stream(device_id: str, project_id: str) -> dict:
    """
    Generates an RTSP stream for a camera device.

    Args:
        device_id (str): The ID of the camera device.
        project_id (str): The ID of the enterprise or project.

    Returns:
        dict: The response from the API, containing the result of the command execution.
    """
    global ONGOING_STREAMS
    # Check if camera is online
    device_state = DB.get("environment", {}).get("sdm", {}).get("devices", {}).get(device_id, {}).get("attributes", {}).get("state", "")
    device_state = device_state.lower()
    if device_state != 'on':
        raise CameraNotAvailableError()

    # Check if device supports RTSP protocol
    device_schema = get_device_info(device_id, project_id)
    supported_protocols = device_schema.get("traits", {}).get("sdm.devices.traits.CameraLiveStream", {}).get("supportedProtocols", [])
    if 'RTSP' in supported_protocols:
        image_path = _resolve_image(device_id)
        auth = "g.0.streamingToken"
        encoded_path = encrypt_url(image_path, auth)
        # Generate a random token
        uid = uuid.uuid4()
        b64 = base64.urlsafe_b64encode(uid.bytes).decode('utf-8').rstrip('=')
        response = {
            "results": {
                "streamUrls": {
                    "rtspUrl": f"rtsps://sdmvideostream.com/{encoded_path}?auth={auth}"
                },
                "streamExtensionToken": b64,
                "streamToken": "g.0.streamingToken",
                "expiresAt": (datetime.now() + timedelta(minutes=5)).isoformat()
            }
        }
        ONGOING_STREAMS.append(response)
        return response
    else:
        raise CommandNotSupportedError()

def stop_rtsp_stream(device_id: str, project_id: str, stream_extension_token: str) -> dict:
    """
    Stops an ongoing stream.

    Args:
        device_id (str): The ID of the camera device.
        project_id (str): The ID of the enterprise or project.
        stream_extension_token (str): Token to identify the stream to stop.

    Returns:
        dict: Returns the stream stopping status.
    """
    global ONGOING_STREAMS
    for stream in ONGOING_STREAMS:
        if stream.get("results", {}).get("streamExtensionToken", "") == stream_extension_token:
            ONGOING_STREAMS.remove(stream)
            return {"status": "success"}
    return {"status": "failure"}
        
def generate_image_from_rtsp_stream(device_id: str, project_id: str, rtsp_url: str) -> str:
    """
    Generates a base64 encoded live camera image from an RTSP stream.

    Agrs:
        device_id (str): The ID of the camera device.
        project_id (str): The ID of the enterprise or project.
        rtsp_url (str): The RTSP URL of the stream.

    Returns:
        str: Base64 encoded string of the image.
    
    Raises:
        FileNotFoundError: If the image file doesn't exist.
        Exception: For other potential errors during encoding.
    """
    # Check if device is correct
    check_image_path = _resolve_image(device_id)
    match = re.search(r"sdmvideostream\.com/(?P<encoded_path>[^?]+)\?auth=(?P<auth>[^&]+)", rtsp_url)
    encoded_path = match.group("encoded_path")
    auth = match.group("auth")
    image_path = decrypt_url(encoded_path, auth)
    if image_path == check_image_path:
        SERVED_IMAGES["STREAM_IMAGES"].append(image_path)
        try:
            return _compress_and_encode_base64(image_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Image file not found at path: {image_path}")
        except Exception as e:
            raise Exception(f"Error converting image to base64: {str(e)}")
    else:
        raise IncorrectEventError()

def generate_web_rtc_stream(device_id: str, project_id: str, offer_sdp: str) -> dict:
    """
    Generates an WEB_RTC stream for a camera device.

    Args:
        device_id (str): The ID of the camera device.
        project_id (str): The ID of the enterprise or project.
        offer_sdp (str): The SDP offer containing the request's parameters definition.

    Returns:
        dict: The response from the API, containing the result of the command execution.
    """
    global ONGOING_STREAMS
    # Check if camera is online
    device_state = DB.get("environment", {}).get("sdm", {}).get("devices", {}).get(device_id, {}).get("attributes", {}).get("state", "")
    device_state = device_state.lower()
    if device_state != 'on':
        raise CameraNotAvailableError()
    
    # Check if device supports RTSP protocol
    device_schema = get_device_info(device_id, project_id)
    supported_protocols = device_schema.get("traits", {}).get("sdm.devices.traits.CameraLiveStream", {}).get("supportedProtocols", [])
    if 'WEB_RTC' in supported_protocols:
        image_path = _resolve_image(device_id)
        encoded_url = encrypt_url(image_path)
        # Generate a random token
        uid = uuid.uuid4()
        b64 = base64.urlsafe_b64encode(uid.bytes).decode('utf-8').rstrip('=')

        # Generate the answer_sdp
        device_schema = get_device_info(device_id, project_id)
        answer_sdp = _generate_answer_sdp(device_schema, encoded_url)

        response = {
            "results" : {
                "answerSdp" : answer_sdp,
                "expiresAt" : (datetime.now() + timedelta(minutes=5)).isoformat(),
                "mediaSessionId" : b64
            }
        }
        ONGOING_STREAMS.append(response)
        return response
    else:
        raise CommandNotSupportedError()

def stop_web_rtc_stream(device_id: str, project_id: str, stream_media_session_id: str) -> dict:
    """
    Stops an ongoing stream.

    Args:
        device_id (str): The ID of the camera device.
        project_id (str): The ID of the enterprise or project.
        stream_media_session_id (str): Token to identify the stream to stop.

    Returns:
        dict: Returns the stream stopping status.
    """
    global ONGOING_STREAMS
    for stream in ONGOING_STREAMS:
        if stream.get("results", {}).get("mediaSessionId", "") == stream_media_session_id:
            ONGOING_STREAMS.remove(stream)
            return {"status": "success"}
    return {"status": "failure"}

def generate_image_from_web_rtc_stream(device_id: str, project_id: str, answer_sdp: str) -> str:
    """
    Generates a live camera image from an WEB_RTC stream.

    Agrs:
        device_id (str): The ID of the camera device.
        project_id (str): The ID of the enterprise or project.
        answer_sdp (str): The answer SDP generated by the camera containing the video stream's parameters definition.

    Returns:
        str: Base64 encoded string of the image.

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        Exception: For other potential errors during encoding.
    """
    # Check if device is correct
    check_image_path = _resolve_image(device_id)
    encoded_path = re.search(r"\r?\na=image-path:(.+?)\r?\n", answer_sdp).group(1)
    image_path = decrypt_url(encoded_path)
    if image_path == check_image_path:
        SERVED_IMAGES["STREAM_IMAGES"].append(image_path)
        try:
            return _compress_and_encode_base64(image_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Image file not found at path: {image_path}")
        except Exception as e:
            raise Exception(f"Error converting image to base64: {str(e)}")
    else:
        raise IncorrectEventError()

def get_served_images() -> list:
    """
    Returns a list of images that have been served.
    """
    return SERVED_IMAGES

def reset_served_images() -> dict:
    """
    Resets the SERVED_IMAGES to an empty dict.

    Returns:
        dict: Returns the update status.
    """
    global SERVED_IMAGES
    SERVED_IMAGES = {"EVENT_IMAGES" : list(), "STREAM_IMAGES" : list()}
    return {"status": "success"}