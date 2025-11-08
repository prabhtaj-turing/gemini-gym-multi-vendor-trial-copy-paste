from common_utils.tool_spec_decorator import tool_spec
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import UserNotFoundError, InvalidInputError
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    FindUserIdByNameZipInput,
)


@tool_spec(
    spec={
        'name': 'find_user_id_by_name_zip',
        'description': """ Find user id by first name, last name, and zip code.
        
        If the user is not found, the function will return an error message. By default,
        find user id by email, and only call this function if the user is not found
        by email or cannot remember email. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'first_name': {
                    'type': 'string',
                    'description': "The first name of the customer, such as 'John'."
                },
                'last_name': {
                    'type': 'string',
                    'description': "The last name of the customer, such as 'Doe'."
                },
                'zip_code': {
                    'type': 'string',
                    'description': "The zip code of the customer, such as '12345'."
                }
            },
            'required': [
                'first_name',
                'last_name',
                'zip_code'
            ]
        }
    }
)
def find_user_id_by_name_zip(
    first_name: str, last_name: str, zip_code: str
) -> str:
    """Find user id by first name, last name, and zip code.

    If the user is not found, the function will return an error message. By default,
    find user id by email, and only call this function if the user is not found
    by email or cannot remember email.

    Args:
        first_name (str): The first name of the customer, such as 'John'.
        last_name (str): The last name of the customer, such as 'Doe'.
        zip_code (str): The zip code of the customer, such as '12345'.

    Returns:
        str: The user id.

    Raises:
        UserNotFoundError: If the user is not found.
        InvalidInputError: If the input is invalid.
    """
    try:
        FindUserIdByNameZipInput(
            first_name=first_name, last_name=last_name, zip=zip_code
        )
    except ValidationError as e:
        raise InvalidInputError(e)

    users = db.DB["users"]
    for user_id, profile in users.items():
        if (
            profile["name"]["first_name"].lower() == first_name.lower()
            and profile["name"]["last_name"].lower() == last_name.lower()
            and profile["address"]["zip"] == zip_code
        ):
            return user_id
    raise UserNotFoundError("Error: user not found")
