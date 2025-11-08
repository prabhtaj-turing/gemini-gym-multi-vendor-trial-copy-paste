from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import UserNotFoundError, InvalidInputError
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    GetUserDetailsInput,
    User,
)


@tool_spec(
    spec={
        'name': 'get_user_details',
        'description': 'Get the details of a user, including their orders.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': "The user id, such as 'sara_doe_496'."
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def get_user_details(user_id: str) -> Dict[str, Any]:
    """Get the details of a user, including their orders.

    Args:
        user_id (str): The user id, such as 'sara_doe_496'.

    Returns:
        Dict[str, Any]: A dictionary representing the user with the following fields:
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
        GetUserDetailsInput(user_id=user_id)
    except ValidationError as e:
        raise InvalidInputError(e)

    users = db.DB["users"]
    if user_id in users:
        return User(**users[user_id]).model_dump(mode="json")
    raise UserNotFoundError("Error: user not found")
