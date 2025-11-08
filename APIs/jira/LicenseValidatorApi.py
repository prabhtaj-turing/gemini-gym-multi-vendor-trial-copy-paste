from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/LicenseValidatorApi.py
from .SimulationEngine.db import DB
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'validate_license',
        'description': """ Validate a license key against the database.
        
        This method validates a license key by checking if it exists in the system's
        license database and returns the validation status with decoded information. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'license': {
                    'type': 'string',
                    'description': 'The license key to validate. Cannot be empty or whitespace-only.'
                }
            },
            'required': [
                'license'
            ]
        }
    }
)
def validate_license(license: str) -> Dict[str, Any]:
    """
    Validate a license key against the database.

    This method validates a license key by checking if it exists in the system's
    license database and returns the validation status with decoded information.

    Args:
        license (str): The license key to validate. Cannot be empty or whitespace-only.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - valid (bool): Whether the license is valid.
            - decoded (str): Human-readable information about the license validation result

    Raises:
        TypeError: If license is not a string
        ValueError: If license is empty or whitespace-only
    """
    # Input validation - Type checking
    if not isinstance(license, str):
        raise TypeError("license parameter must be a string")
    
    # Input validation - Value checking
    if not license or not license.strip():
        raise ValueError("license parameter cannot be empty or whitespace-only")
    
    # Find the license in the database
    license = license.strip()
    for license_data in DB.get("licenses", {}).values():
        if license_data.get("key") == license:
            return {
                "valid": True,
                "decoded": f"License validated: {license} (ID: {license_data['id']})"
            }
    
    # License not found
    return {
        "valid": False,
        "decoded": f"License key '{license}' not found in system"
    }
