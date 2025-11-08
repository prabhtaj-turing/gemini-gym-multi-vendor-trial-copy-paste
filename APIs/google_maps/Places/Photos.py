from common_utils.tool_spec_decorator import tool_spec
# google_maps/Places/Photos.py
import re
from google_maps.SimulationEngine.models import PhotoMedia, GetMediaInputModel
from google_maps.SimulationEngine.custom_errors import ZeroResultsError
from typing import Dict, List, Optional, Any
from google_maps.SimulationEngine.db import DB
from pydantic import ValidationError

@tool_spec(
    spec={
        'name': 'get_place_photo_media',
        'description': 'Retrieves photo media by resource name.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': " The resource name of a photo, formatted as\n'places/{place_id}/photos/{photo_reference}/media'. (Required) "
                },
                'maxWidthPx': {
                    'type': 'integer',
                    'description': 'The maximum desired photo width (range 1–4800).'
                },
                'maxHeightPx': {
                    'type': 'integer',
                    'description': 'The maximum desired photo height (range 1–4800).'
                },
                'skipHttpRedirect': {
                    'type': 'boolean',
                    'description': 'If True, skips HTTP redirects and returns JSON data.\nDefaults to False.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)

def getMedia(name: str, maxWidthPx: Optional[int] = None, maxHeightPx: Optional[int] = None,
             skipHttpRedirect: bool = False) -> List[Dict[str, str]]:
    """
    Retrieves photo media by resource name.

    Args:
        name (str): The resource name of a photo, formatted as
            "places/{place_id}/photos/{photo_reference}/media". (Required)
        maxWidthPx (Optional[int]): The maximum desired photo width (range 1–4800).
        maxHeightPx (Optional[int]): The maximum desired photo height (range 1–4800).
        skipHttpRedirect (bool, optional): If True, skips HTTP redirects and returns JSON data.
            Defaults to False.

    Returns:
        List[Dict[str, str]]: A list of photo media objects, each containing:
            - photoUri (str): The URL to the photo media.
            - name (str): The full resource name of the photo.

    Raises:
        ValueError: If the resource name does not match the expected format, if dimensions are invalid,
                    or if neither maxWidthPx nor maxHeightPx is specified.
        ZeroResultsError: If no photo is found.
    """
    try:
        params = GetMediaInputModel(
            name=name,
            maxWidthPx=maxWidthPx,
            maxHeightPx=maxHeightPx,
            skipHttpRedirect=skipHttpRedirect,
        )
    except ValidationError as e:
        error = e.errors()[0]
        raise ValueError(f"Invalid request data: {error['msg']}")

    # Extract the place_id and photo_reference.
    parts = params.name.split("/")
    place_id = parts[1]
    photo_ref = parts[3]

    results = []
    # Search through the static DB.
    place = DB.get(place_id, None)
    if place:
        for photo in place.get("photos", []):
            # Stored photo names are in the format "places/{place_id}/photos/{photo_reference}".
            if photo.get("name") == f"places/{place_id}/photos/{photo_ref}":
                dims = []
                if params.maxWidthPx is not None:
                    dims.append(f"w{params.maxWidthPx}")
                if params.maxHeightPx is not None:
                    dims.append(f"h{params.maxHeightPx}")
                dims_str = "_".join(dims)
                
                redirect_param = "" if params.skipHttpRedirect else "&redirect=true"
                dummy_photo_uri = f"https://maps.example.com/media/{photo.get('name')}/media?dims={dims_str}{redirect_param}"
                photo_media = PhotoMedia(photoUri=dummy_photo_uri, name=name)
                results.append(photo_media.model_dump())
    
    if not results:
        raise ZeroResultsError("No photo found for the given reference.")
    return results
