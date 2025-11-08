from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict

import requests
from common_utils.log_complexity import log_complexity


@log_complexity
@tool_spec(
    spec={
        'name': 'webFetch',
        'description': 'Fetches content from a given URL.',
        'parameters': {
            'type': 'object',
            'properties': {
                'url': {
                    'type': 'string',
                    'description': 'The URL to fetch content from.'
                }
            },
            'required': [
                'url'
            ]
        }
    }
)
def web_fetch(
    url: str,
) -> Dict[str, Any]:
    """Fetches content from a given URL.

    Args:
        url (str): The URL to fetch content from.

    Returns:
        Dict[str, Any]: A dictionary containing the content and status code of the response, with the following keys:
            - content (str): The text content of the response.
            - status_code (int): The HTTP status code of the response.

    Raises:
        TypeError: If the 'url' argument is not a string.
        ConnectionError: If a connection to the URL could not be established.
        TimeoutError: If the request to the URL times out.
        Exception: For any other request-related errors or unexpected issues.
    """
    if not isinstance(url, str):
        raise TypeError("url must be a string")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        return {
            "content": response.text,
            "status_code": response.status_code,
        }
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Could not connect to {url}: {e}")
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request to {url} timed out")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP Error: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
