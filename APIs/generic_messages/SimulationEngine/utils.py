from typing import Any, Dict, List, Optional


def _validate_endpoint_value(endpoint_type: str, endpoint_value: str) -> bool:
    """Validate endpoint value based on endpoint type.
    
    Args:
        endpoint_type (str): The type of endpoint (PHONE_NUMBER or WHATSAPP_PROFILE).
        endpoint_value (str): The value to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(endpoint_value, str):
        return False
    endpoint_value = endpoint_value.strip()
    if not endpoint_value:
        return False
    
    if endpoint_type == "PHONE_NUMBER":
        # Basic E.164 validation
        return endpoint_value.startswith("+") and len(endpoint_value) > 5
    elif endpoint_type == "WHATSAPP_PROFILE":
        # WhatsApp format: {number}@s.whatsapp.net
        return "@s.whatsapp.net" in endpoint_value
    
    return False
