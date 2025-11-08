from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/AvatarApi.py

from .SimulationEngine.db import DB
from .SimulationEngine.utils import _check_empty_field, _generate_id


@tool_spec(
    spec={
        'name': 'upload_avatar',
        'description': """ Upload a new avatar to Jira.
        
        This method allows uploading a new avatar image to be used in Jira.
        The avatar can be used for users, projects, or other entities. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filetype': {
                    'type': 'string',
                    'description': """ The type of avatar being uploaded. Must be one of:
                    - "user": For user avatars
                    - "project": For project avatars
                    - "system": For system-wide avatars """
                },
                'filename': {
                    'type': 'string',
                    'description': 'The name of the file being uploaded'
                }
            },
            'required': [
                'filetype',
                'filename'
            ]
        }
    }
)
def upload_avatar(filetype: str, filename: str) -> dict:
    """
    Upload a new avatar to Jira.

    This method allows uploading a new avatar image to be used in Jira.
    The avatar can be used for users, projects, or other entities.

    Args:
        filetype (str): The type of avatar being uploaded. Must be one of:
            - "user": For user avatars
            - "project": For project avatars
            - "system": For system-wide avatars
        filename (str): The name of the file being uploaded

    Returns:
        dict: A dictionary containing:
            - uploaded (bool): True if the avatar was successfully uploaded
            - avatar (dict): The uploaded avatar object containing:
                - id (str): The unique identifier for the uploaded avatar
                - type (str): The type of avatar
                - filename (str): The name of the uploaded file

    Raises:
        ValueError: If filetype or filename is empty
    """
    err = _check_empty_field("type", filetype) + _check_empty_field(
        "filename", filename
    )
    if err:
        return {"error": err}

    new_avatar = {
        "id": _generate_id("avatar", DB["avatars"]),
        "type": filetype,
        "filename": filename,
    }
    DB["avatars"].append(new_avatar)
    return {"uploaded": True, "avatar": new_avatar}


@tool_spec(
    spec={
        'name': 'upload_temporary_avatar',
        'description': """ Upload a temporary avatar to Jira.
        
        This method allows uploading a temporary avatar that can be used for preview
        before making it permanent. Temporary avatars are typically used during the
        avatar selection process. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filetype': {
                    'type': 'string',
                    'description': """ The type of avatar being uploaded. Must be one of:
                    - "user": For user avatars
                    - "project": For project avatars
                    - "system": For system-wide avatars """
                },
                'filename': {
                    'type': 'string',
                    'description': 'The name of the file being uploaded'
                }
            },
            'required': [
                'filetype',
                'filename'
            ]
        }
    }
)
def upload_temporary_avatar(filetype: str, filename: str) -> dict:
    """
    Upload a temporary avatar to Jira.

    This method allows uploading a temporary avatar that can be used for preview
    before making it permanent. Temporary avatars are typically used during the
    avatar selection process.

    Args:
        filetype (str): The type of avatar being uploaded. Must be one of:
            - "user": For user avatars
            - "project": For project avatars
            - "system": For system-wide avatars
        filename (str): The name of the file being uploaded

    Returns:
        dict: A dictionary containing:
            - uploaded (bool): True if the temporary avatar was successfully uploaded
            - avatar (dict): The temporary avatar object containing:
                - id (str): The unique identifier for the temporary avatar
                - type (str): The type of avatar
                - filename (str): The name of the uploaded file
                - temporary (bool): Always True for temporary avatars

    Raises:
        ValueError: If filetype or filename is empty
    """
    err = _check_empty_field("type", filetype) + _check_empty_field(
        "filename", filename
    )
    if err:
        return {"error": err}

    temp_avatar = {
        "id": _generate_id("avatar_temp", DB["avatars"]),
        "type": filetype,
        "filename": filename,
        "temporary": True,
    }
    DB["avatars"].append(temp_avatar)
    return {"uploaded": True, "avatar": temp_avatar}


@tool_spec(
    spec={
        'name': 'crop_temporary_avatar',
        'description': """ Crop a temporary avatar in Jira.
        
        This method allows cropping a temporary avatar to the desired dimensions
        before making it permanent. This is typically used after uploading a
        temporary avatar to adjust its appearance. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'cropDimensions': {
                    'type': 'object',
                    'description': 'A dictionary containing the crop dimensions:',
                    'properties': {
                        'x': {
                            'type': 'integer',
                            'description': 'The x-coordinate of the top-left corner'
                        },
                        'y': {
                            'type': 'integer',
                            'description': 'The y-coordinate of the top-left corner'
                        },
                        'width': {
                            'type': 'integer',
                            'description': 'The width of the crop area'
                        },
                        'height': {
                            'type': 'integer',
                            'description': 'The height of the crop area'
                        }
                    },
                    'required': [
                        'x',
                        'y',
                        'width',
                        'height'
                    ]
                }
            },
            'required': [
                'cropDimensions'
            ]
        }
    }
)
def crop_temporary_avatar(cropDimensions: dict) -> dict:
    """
    Crop a temporary avatar in Jira.

    This method allows cropping a temporary avatar to the desired dimensions
    before making it permanent. This is typically used after uploading a
    temporary avatar to adjust its appearance.

    Args:
        cropDimensions (dict): A dictionary containing the crop dimensions:
            - x (int): The x-coordinate of the top-left corner
            - y (int): The y-coordinate of the top-left corner
            - width (int): The width of the crop area
            - height (int): The height of the crop area

    Returns:
        dict: A dictionary containing:
            - cropped (bool): True if the avatar was successfully cropped
            - dimensions (dict): The applied crop dimensions

    Raises:
        ValueError: If cropDimensions is empty or invalid
    """
    err = _check_empty_field("cropDimensions", cropDimensions)
    if err:
        return {"error": err}
    return {"cropped": True, "dimensions": cropDimensions}
