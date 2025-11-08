import re
from common_utils.custom_errors import InvalidEmailError

def validate_email_custom(email: str) -> str:
    """
    Validate an email address against a set of custom rules.

    This function checks for the basic structure of an email, including the
    presence of an '@' symbol, valid local and domain parts, and overall
    format. It also enforces a maximum length of 512 characters to prevent
    excessively long inputs. If any validation rule is violated, it raises
    an InvalidEmailError with a descriptive message.

    Args:
        email: The email address to validate.

    Returns:
        The validated email address if it is valid.

    Raises:
        InvalidEmailError: If the email address fails any validation check.
    """
    if not isinstance(email, str):
        raise InvalidEmailError("Invalid input: not a string")

    if len(email) > 512:
        raise InvalidEmailError("Invalid email: exceeds 512 characters")

    email = email.strip()

    if '@' not in email:
        raise InvalidEmailError("Invalid email: missing '@' symbol")

    try:
        local_part, domain_part = email.split('@')
    except ValueError:
        raise InvalidEmailError("Invalid email: more than one '@' symbol")

    if not local_part:
        raise InvalidEmailError("Invalid email: missing local part")
    if local_part.startswith('.') or local_part.endswith('.'):
        raise InvalidEmailError("Invalid email: local part starts or ends with a dot")
    if '..' in local_part:
        raise InvalidEmailError("Invalid email: local part has consecutive dots")

    if not domain_part or '.' not in domain_part:
        raise InvalidEmailError("Invalid email: domain part is invalid")
    if domain_part.startswith('-') or domain_part.endswith('-'):
        raise InvalidEmailError("Invalid email: domain starts or ends with a hyphen")
    if '..' in domain_part:
        raise InvalidEmailError("Invalid email: domain part has consecutive dots")

    regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    if not re.fullmatch(regex, email):
        raise InvalidEmailError("Invalid email: format doesn't match standard pattern")

    return email