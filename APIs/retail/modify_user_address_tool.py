from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, Optional
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import (
    UserNotFoundError,
    InvalidInputError,
)
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    ModifyUserAddressInput,
    User,
    Address,
)


@tool_spec(
    spec={
        'name': 'modify_user_address',
        'description': """ Modify the default address of a user.
        
        The agent needs to explain the modification detail and ask for explicit user
        confirmation (yes/no) to proceed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': "The user id, such as 'sara_doe_496'."
                },
                'address1': {
                    'type': 'string',
                    'description': "The first line of the address, such as '123 Main St'."
                },
                'address2': {
                    'type': 'string',
                    'description': "The second line of the address, such as 'Apt 1' or ''."
                },
                'city': {
                    'type': 'string',
                    'description': "The city, such as 'San Francisco'."
                },
                'state': {
                    'type': 'string',
                    'description': "The state, such as 'CA'."
                },
                'country': {
                    'type': 'string',
                    'description': "The country, such as 'USA'."
                },
                'zip_code': {
                    'type': 'string',
                    'description': "The zip code, such as '12345'."
                }
            },
            'required': [
                'user_id',
                'address1',
                'address2',
                'city',
                'state',
                'country',
                'zip_code'
            ]
        }
    }
)
def modify_user_address(
    user_id: str,
    address1: str,
    address2: str,
    city: str,
    state: str,
    country: str,
    zip_code: str,
) -> Dict[str, Any]:
    """Modify the default address of a user.

    The agent needs to explain the modification detail and ask for explicit user
    confirmation (yes/no) to proceed.

    Args:
        user_id (str): The user id, such as 'sara_doe_496'.
        address1 (str): The first line of the address, such as '123 Main St'.
        address2 (str): The second line of the address, such as 'Apt 1' or ''.
        city (str): The city, such as 'San Francisco'.
        state (str): The state, such as 'CA'.
        country (str): The country, such as 'USA'.
        zip_code (str): The zip code, such as '12345'.

    Returns:
        Dict[str, Any]: A dictionary representing the updated user with the following fields:
            - name (Dict[str, str]): The name of the user.
                - first_name (str): The first name of the user.
                - last_name (str): The last name of the user.
            - address (Dict[str, str]): The address of the user.
                - address1 (str): The first line of the address.
                - address2 (str): The second line of the address.
                - city (str): The city of the address.
                - country (str): The country of the address.
                - state (str): The state of the address.
                - zip (str): The zip code of the address.
            - email (str): The email of the user.
            - payment_methods (Dict[str, Dict[str, Any]]): A dictionary of payment methods, where the key is the payment method ID.
                - id (str): The ID of the payment method.
                - source (str): The source of the payment method, one of 'credit_card', 'gift_card', or 'paypal'.
                - brand (Optional[str]): The brand of the credit card (if source is 'credit_card').
                - last_four (Optional[str]): The last four digits of the credit card (if source is 'credit_card').
                - balance (Optional[int]): The balance of the gift card (if source is 'gift_card').
            - orders (List[str]): A list of order IDs for the user.

    Raises:
        UserNotFoundError: If the user is not found.
        InvalidInputError: If the input is invalid.
    """
    try:
        ModifyUserAddressInput(
            user_id=user_id,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            country=country,
            zip=zip_code,
        )
    except ValidationError as e:
        raise InvalidInputError(e)

    users = db.DB["users"]
    if user_id not in users:
        raise UserNotFoundError("Error: user not found")

    user = users[user_id]
    user["address"] = {
        "address1": address1,
        "address2": address2,
        "city": city,
        "state": state,
        "country": country,
        "zip": zip_code,
    }
    
    return user
