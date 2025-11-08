from common_utils.tool_spec_decorator import tool_spec
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import UserNotFoundError, InvalidInputError
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    FindUserIdByEmailInput,
)


@tool_spec(
    spec={
        'name': 'find_user_id_by_email',
        'description': """ Find user id by email.
        
        If the user is not found, the function will return an error message. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'email': {
                    'type': 'string',
                    'description': "The email of the user, such as 'something@example.com'."
                }
            },
            'required': [
                'email'
            ]
        }
    }
)
def find_user_id_by_email(email: str) -> str:
    """Find user id by email.

    If the user is not found, the function will return an error message.

    Args:
        email (str): The email of the user, such as 'something@example.com'.

    Returns:
        str: The user id.

    Raises:
        UserNotFoundError: If the user is not found.
        InvalidInputError: If the input is invalid.
    """
    try:
        FindUserIdByEmailInput(email=email)
    except ValidationError as e:
        raise InvalidInputError(e)

    users = db.DB["users"]
    for user_id, profile in users.items():
        if profile["email"].lower() == email.lower():
            return user_id
    raise UserNotFoundError("Error: user not found")
