import re


def is_phone_number_valid(phone_number_str: str, region_code: str = "") -> bool:
    """
    Validates that the phone number can be normalized to xxx-xxx-xxxx format.

    Args:
        phone_number_str: The raw phone number string to validate.
        region_code: Ignored; kept for backward compatibility.

    Returns:
        True if the phone number can be normalized to xxx-xxx-xxxx format.
    """
    if phone_number_str is None:
        return False
    
    # First check if it's already in the correct format
    pattern = r'^\d{3}-\d{3}-\d{4}$'
    if re.match(pattern, str(phone_number_str).strip()):
        return True
    
    # If not, try to normalize it and check if normalization succeeds
    normalized = normalize_phone_number(phone_number_str, region_code)
    return normalized is not None

def normalize_phone_number(phone_number_str: str, region_code: str = "") -> str | None:
    """
    Normalize the phone number to xxx-xxx-xxxx format.

    Args:
        phone_number_str: The phone number to normalize.
        region_code: Ignored; kept for backward compatibility.

    Returns:
        The normalized phone number in xxx-xxx-xxxx format, or None if input is invalid.
    """
    if phone_number_str is None:
        return None

    raw = str(phone_number_str).strip()
    if raw == "":
        return None

    # Remove all non-digit characters
    digits_only = re.sub(r"[^\d]", "", raw)
    
    # Check if we have exactly 10 digits
    if len(digits_only) != 10:
        return None
    
    # Format as xxx-xxx-xxxx
    return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
