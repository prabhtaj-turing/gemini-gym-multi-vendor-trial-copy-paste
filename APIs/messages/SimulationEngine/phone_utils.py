import re

def normalize_phone_number(phone_number_str: str) -> str | None:
    """
    Normalize and validate a phone number to strict E.164 format.

    Validation Rules:
    - Remove common separators (spaces, hyphens, dots, parentheses) before validation
    - Must start with a single '+'
    - Body after '+' must be 8–15 digits
    - No other characters are allowed; invalid input returns None

    Separators removed: spaces, hyphens, dots, parentheses

    Args:
        phone_number_str: The phone number to normalize.

    Returns:
        Normalized phone number string in E.164 (e.g., '+14155552671') if valid; None otherwise.
    """
    if phone_number_str is None:
        return None

    raw = str(phone_number_str).strip()
    if raw == "":
        return None

    # Preserve whether the original string started with '+'
    has_leading_plus = raw.lstrip().startswith('+')

    # Remove common separators: whitespace, hyphens, parentheses, dots
    cleaned = re.sub(r"[\s\-\.\(\)]", "", raw)

    # Strip all '+' symbols, then add one back if it originally had one
    cleaned = cleaned.lstrip('+')
    if has_leading_plus:
        cleaned = '+' + cleaned

    # Early return if nothing is left
    if not cleaned:
        return None

    # Basic phone number format check (strict E.164):
    # - Must start with '+'
    # - Body after '+' must be 8–15 digits
    if not cleaned.startswith('+'):
        return None

    number_body = cleaned[1:]
    if not number_body.isdigit():
        return None
    if not (8 <= len(number_body) <= 15):
        return None

    return cleaned