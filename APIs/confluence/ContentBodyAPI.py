from common_utils.tool_spec_decorator import tool_spec
# APIs/confluence/ContentBodyAPI.py
from typing import Dict, Any, Optional


@tool_spec(
    spec={
        'name': 'convert_content_body',
        'description': 'Converts a content body from one format to another.',
        'parameters': {
            'type': 'object',
            'properties': {
                'to': {
                    'type': 'string',
                    'description': """ The target format to convert to. Valid values are:
                    - "view": For viewing the content.
                    - "export_view": For exporting the content.
                    - "editor": For editing the content.
                    - "storage": For storing the content. """
                },
                'body': {
                    'type': 'object',
                    'description': 'The content body to convert, containing:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'The current content format type.'
                        },
                        'value': {
                            'type': 'string',
                            'description': 'The actual content value.'
                        },
                        'representation': {
                            'type': 'string',
                            'description': 'The current representation of the content.'
                        }
                    },
                    'required': [
                        'type',
                        'value',
                        'representation'
                    ]
                }
            },
            'required': [
                'to',
                'body'
            ]
        }
    }
)
def convert_content_body(to: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a content body from one format to another.

    Args:
        to (str): The target format to convert to. Valid values are:
            - "view": For viewing the content.
            - "export_view": For exporting the content.
            - "editor": For editing the content.
            - "storage": For storing the content.
        body (Dict[str, Any]): The content body to convert, containing:
            - type (str): The current content format type.
            - value (str): The actual content value.
            - representation (str): The current representation of the content.

    Returns:
        Dict[str, Any]: The converted content body containing:
            - convertedTo (str): The target format it was converted to.
            - originalBody (Dict[str, Any]): The original content body, with:
                  - type (str): The original content format type.
                  - value (str): The original content value.
                  - representation (str): The original representation.
            - value (str): The converted content value.
            - type (str): The target content format type (same as 'to').
            - representation (str): The target representation (same as 'to').

    Raises:
        ValueError: If the target format is not supported or the input body is invalid (i.e., missing required keys 'type' or 'value').
    """
    # Validate target format
    valid_formats = ["view", "export_view", "editor", "storage"]
    if to not in valid_formats:
        raise ValueError(
            f"Unsupported target format '{to}'. Must be one of: {', '.join(valid_formats)}"
        )

    if "type" not in body or "value" not in body:
        raise ValueError("Body must contain 'type' and 'value' fields")

    # Create response with original body
    response = {"convertedTo": to, "originalBody": body.copy()}

    # For this simulation, we'll just return the same content with the new format.
    # In a real implementation, this would perform actual format conversion.
    response.update({"value": body["value"], "type": to, "representation": to})

    return response
