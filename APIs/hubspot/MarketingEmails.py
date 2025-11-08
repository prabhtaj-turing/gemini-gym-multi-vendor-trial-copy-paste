from common_utils.tool_spec_decorator import tool_spec
# APIs/hubspot/MarketingEmails.py
from typing import Dict, Any, Union, Optional
import uuid
from hubspot.SimulationEngine.db import DB
import builtins
from datetime import datetime


@tool_spec(
    spec={
        'name': 'create_marketing_email',
        'description': 'Creates a new marketing email.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The internal name of the email (required).'
                },
                'subject': {
                    'type': 'string',
                    'description': 'The email subject line. Default is None.'
                },
                'htmlBody': {
                    'type': 'string',
                    'description': 'The HTML body of the email. Default is None.'
                },
                'isTransactional': {
                    'type': 'boolean',
                    'description': 'Whether this is a transactional email. Default is False.'
                },
                'status': {
                    'type': 'string',
                    'description': "The status of the email (e.g. 'scheduled', 'sent'). Default is None."
                },
                'discount_code': {
                    'type': 'string',
                    'description': 'Discount code for promotional emails. Default is None.'
                },
                'expiration': {
                    'type': 'string',
                    'description': 'Expiration date for time-limited offers in YYYY-MM-DD format. Default is None.'
                },
                'launch_date': {
                    'type': 'string',
                    'description': 'Launch date for product announcements in YYYY-MM-DD format. Default is None.'
                },
                'sale_end_date': {
                    'type': 'string',
                    'description': 'End date for sales promotions in YYYY-MM-DD format. Default is None.'
                },
                'reward_points': {
                    'type': 'integer',
                    'description': 'Number of reward points for loyalty program emails. Default is None.'
                },
                'access_code': {
                    'type': 'string',
                    'description': 'Access code for VIP or exclusive offers. Default is None.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def create(
    name: str,
    subject: Optional[str] = None,
    htmlBody: Optional[str] = None,
    isTransactional: Optional[bool] = False,
    status: Optional[str] = None,
    discount_code: Optional[str] = None,
    expiration: Optional[str] = None,
    launch_date: Optional[str] = None,
    sale_end_date: Optional[str] = None,
    reward_points: Optional[int] = None,
    access_code: Optional[str] = None,
) -> Dict[str, Union[str, bool]]:
    """Creates a new marketing email.

    Args:
        name(str): The internal name of the email (required).
        subject(Optional[str]): The email subject line. Default is None.
        htmlBody(Optional[str]): The HTML body of the email. Default is None.
        isTransactional(Optional[bool]): Whether this is a transactional email. Default is False.
        status(Optional[str]): The status of the email (e.g. 'scheduled', 'sent'). Default is None.
        discount_code(Optional[str]): Discount code for promotional emails. Default is None.
        expiration(Optional[str]): Expiration date for time-limited offers in YYYY-MM-DD format. Default is None.
        launch_date(Optional[str]): Launch date for product announcements in YYYY-MM-DD format. Default is None.
        sale_end_date(Optional[str]): End date for sales promotions in YYYY-MM-DD format. Default is None.
        reward_points(Optional[int]): Number of reward points for loyalty program emails. Default is None.
        access_code(Optional[str]): Access code for VIP or exclusive offers. Default is None.

    Returns:
        Dict[str, Union[str, bool]]: A dictionary containing the new email's ID and a success message, or an error message.
        - email_id(str): The unique ID of the marketing email.
        - success(bool): Whether the email was created successfully.
        - message(str): A message indicating the success or failure of the email creation.
    Raises:
        TypeError: If the email_id, name, subject, htmlBody, status, discount_code, expiration, 
                    launch_date, sale_end_date, reward_points, access_code are not a string
                    and isTransactional is not a boolean.
        ValueError: If the launch_date, sale_end_date, expiration are not in the format of YYYY-MM-DD 
                    or if the name is not a non-empty string.
    """
    
    if subject is not None and not isinstance(subject, str):
        raise TypeError("Subject must be a string.")
    
    if htmlBody is not None and not isinstance(htmlBody, str):
        raise TypeError("HTML body must be a string.")

    if isTransactional is not None and not isinstance(isTransactional, bool):
        raise TypeError("isTransactional must be a boolean.")
    
    if status is not None and not isinstance(status, str):
        raise TypeError("Status must be a string.")
    
    if discount_code is not None and not isinstance(discount_code, str):
        raise TypeError("Discount code must be a string.")

    if expiration is not None and not isinstance(expiration, str):
        raise TypeError("Expiration must be a string.")
    
    if launch_date is not None and not isinstance(launch_date, str):
        raise TypeError("Launch date must be a string.")
    
    if sale_end_date is not None and not isinstance(sale_end_date, str):
        raise TypeError("Sale end date must be a string.")
    
    if reward_points is not None and not isinstance(reward_points, int):
        raise TypeError("Reward points must be an integer.")
    
    if access_code is not None and not isinstance(access_code, str):
        raise TypeError("Access code must be a string.")

 
    if expiration is not None:
        try:
            datetime.strptime(expiration, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Expiration must be in the format of YYYY-MM-DD.")
    if launch_date is not None:
        try:
            datetime.strptime(launch_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Launch date must be in the format of YYYY-MM-DD.")
    if sale_end_date is not None:
        try:
            datetime.strptime(sale_end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Sale end date must be in the format of YYYY-MM-DD.")

    if not isinstance(name, str) or not name:
        raise ValueError("Name must be a non-empty string.")
    
    if "marketing_emails" not in DB:
        DB["marketing_emails"] = {}
    
    # Find next available email_id

    email_id = str(uuid.uuid4())

    DB["marketing_emails"][email_id] = {
        "name": name,
        "subject": subject,
        "htmlBody": htmlBody,
        "isTransactional": isTransactional,
        "status": status,
        "discount_code": discount_code,
        "expiration": expiration,
        "launch_date": launch_date,
        "sale_end_date": sale_end_date,
        "reward_points": reward_points,
        "access_code": access_code,
    }
    return {
        "success": True,
        "message": "Marketing email created successfully.",
        "email_id": email_id,
    }


@tool_spec(
    spec={
        'name': 'get_marketing_email_by_id',
        'description': 'Retrieves a marketing email by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email_id': {
                    'type': 'string',
                    'description': 'The unique ID of the marketing email (required).'
                }
            },
            'required': [
                'email_id'
            ]
        }
    }
)
def getById(email_id: str) ->Optional[Dict[str, Union[str, bool, int]]]:
    """Retrieves a marketing email by its ID.
    Args:
        email_id(str): The unique ID of the marketing email (required).

    Returns:
        Optional[Dict[str, Union[str, bool, int]]]: The marketing email object if found, or None if not found.
            - email_id(str): The unique ID of the marketing email.
            - name(str): The internal name of the email.
            - subject(str): The email subject line.
            - htmlBody(str): The HTML body of the email.
            - isTransactional(bool): Whether the email is transactional.
            - status(str): The status of the email (e.g. 'scheduled', 'sent').
            - discount_code(str): Discount code for promotional emails.
            - expiration(str): Expiration date for time-limited offers.
            - launch_date(str): Launch date for product announcements.
            - sale_end_date(str): End date for sales promotions.
            - reward_points(int): Number of reward points for loyalty program emails.
            - access_code(str): Access code for VIP or exclusive offers.

    Raises:
        TypeError: If the email_id is not a string.
        KeyError: If the email_id is not found.
    """

    if not isinstance(email_id, str):
        raise TypeError(f"email_id must be a string, but got {builtins.type(email_id).__name__}.")

    if email_id not in DB["marketing_emails"]:
        raise KeyError(f"Marketing email with id {email_id} not found.")

    email = DB["marketing_emails"].get(email_id)

    return email


@tool_spec(
    spec={
        'name': 'update_marketing_email',
        'description': 'Updates an existing marketing email.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email_id': {
                    'type': 'string',
                    'description': 'The unique ID of the marketing email to update (required).'
                },
                'name': {
                    'type': 'string',
                    'description': 'The internal name of the email.'
                },
                'subject': {
                    'type': 'string',
                    'description': 'The email subject line.'
                },
                'htmlBody': {
                    'type': 'string',
                    'description': 'The HTML body of the email.'
                },
                'isTransactional': {
                    'type': 'boolean',
                    'description': 'Whether this is a transactional email.'
                },
                'status': {
                    'type': 'string',
                    'description': "The status of the email (e.g. 'scheduled', 'sent')."
                },
                'discount_code': {
                    'type': 'string',
                    'description': 'Discount code for promotional emails.'
                },
                'expiration': {
                    'type': 'string',
                    'description': 'Expiration date for time-limited offers.'
                },
                'launch_date': {
                    'type': 'string',
                    'description': 'Launch date for product announcements.'
                },
                'sale_end_date': {
                    'type': 'string',
                    'description': 'End date for sales promotions.'
                },
                'reward_points': {
                    'type': 'integer',
                    'description': 'Number of reward points for loyalty program emails.'
                },
                'access_code': {
                    'type': 'string',
                    'description': 'Access code for VIP or exclusive offers.'
                }
            },
            'required': [
                'email_id'
            ]
        }
    }
)
def update(
    email_id: str,
    name: Optional[str] = None,
    subject: Optional[str] = None,
    htmlBody: Optional[str] = None,
    isTransactional: Optional[bool] = None,
    status: Optional[str] = None,
    discount_code: Optional[str] = None,
    expiration: Optional[str] = None,
    launch_date: Optional[str] = None,
    sale_end_date: Optional[str] = None,
    reward_points: Optional[int] = None,
    access_code: Optional[str] = None,
) -> Dict[str, Union[str, bool]]:
    """Updates an existing marketing email.

    Args:
        email_id(str): The unique ID of the marketing email to update (required).
        name(Optional[str]): The internal name of the email. Defaults to None.
        subject(Optional[str]): The email subject line. Defaults to None.
        htmlBody(Optional[str]): The HTML body of the email. Defaults to None.
        isTransactional(Optional[bool]): Whether this is a transactional email. Defaults to None.
        status(Optional[str]): The status of the email (e.g. 'scheduled', 'sent'). Defaults to None.
        discount_code(Optional[str]): Discount code for promotional emails. Defaults to None.
        expiration(Optional[str]): Expiration date for time-limited offers. Defaults to None.
        launch_date(Optional[str]): Launch date for product announcements. Defaults to None.
        sale_end_date(Optional[str]): End date for sales promotions. Defaults to None.
        reward_points(Optional[int]): Number of reward points for loyalty program emails. Defaults to None.
        access_code(Optional[str]): Access code for VIP or exclusive offers. Defaults to None.

    Returns:
        Dict[str, Union[str, bool]]: A dictionary indicating success and a message.
        - success(bool): Whether the email was updated successfully.
        - message(str): A message indicating the success of the email update.

    Raises:
        TypeError: If the email_id, name, subject, htmlBody, status, discount_code, expiration, 
                    launch_date, sale_end_date, reward_points, access_code are not a string
                    and isTransactional is not a boolean.
        ValueError: If the launch_date, sale_end_date, expiration are not in the format of YYYY-MM-DD or if the email ID is not provided or not found in the database.
    """
    if email_id is None:
        raise ValueError("Email ID is required.")

    if not isinstance(email_id, str):
        raise TypeError("Email ID must be a string.")

    if name is not None and not isinstance(name, str):
        raise TypeError("Name must be a string.")
    
    if subject is not None and not isinstance(subject, str):
        raise TypeError("Subject must be a string.")
    
    if htmlBody is not None and not isinstance(htmlBody, str):
        raise TypeError("HTML body must be a string.")

    if isTransactional is not None and not isinstance(isTransactional, bool):
        raise TypeError("isTransactional must be a boolean.")
    
    if status is not None and not isinstance(status, str):
        raise TypeError("Status must be a string.")
    
    if discount_code is not None and not isinstance(discount_code, str):
        raise TypeError("Discount code must be a string.")

    if expiration is not None and not isinstance(expiration, str):
        raise TypeError("Expiration must be a string.")
    
    if launch_date is not None and not isinstance(launch_date, str):
        raise TypeError("Launch date must be a string.")
    
    if sale_end_date is not None and not isinstance(sale_end_date, str):
        raise TypeError("Sale end date must be a string.")
    
    if reward_points is not None and not isinstance(reward_points, int):
        raise TypeError("Reward points must be an integer.")
    
    if access_code is not None and not isinstance(access_code, str):
        raise TypeError("Access code must be a string.")


    marketing_emails = DB.get("marketing_emails",{})
    if email_id not in marketing_emails:
        raise ValueError(f"Marketing email with given ID not found.")
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if subject is not None:
        update_data["subject"] = subject
    if htmlBody is not None:
        update_data["htmlBody"] = htmlBody
    if isTransactional is not None:
        update_data["isTransactional"] = isTransactional
    if status is not None:
        update_data["status"] = status
    if discount_code is not None:
        update_data["discount_code"] = discount_code
    if expiration is not None:
        try:
            datetime.strptime(expiration, "%Y-%m-%d")
            update_data["expiration"] = expiration
        except ValueError:
            raise ValueError("Expiration must be in the format of YYYY-MM-DD.")
    if launch_date is not None:
        try:
            datetime.strptime(launch_date, "%Y-%m-%d")
            update_data["launch_date"] = launch_date
        except ValueError:
            raise ValueError("Launch date must be in the format of YYYY-MM-DD.")
    if sale_end_date is not None:
        try:
            datetime.strptime(sale_end_date, "%Y-%m-%d")
            update_data["sale_end_date"] = sale_end_date
        except ValueError:
            raise ValueError("Sale end date must be in the format of YYYY-MM-DD.")
    if reward_points is not None:
        update_data["reward_points"] = reward_points
    if access_code is not None:
        update_data["access_code"] = access_code

    DB["marketing_emails"][email_id].update(update_data)
    return {"success": True, "message": "Marketing email updated successfully."}


@tool_spec(
    spec={
        'name': 'delete_marketing_email',
        'description': 'Deletes a marketing email.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email_id': {
                    'type': 'string',
                    'description': 'The unique ID of the marketing email to delete (required).'
                }
            },
            'required': [
                'email_id'
            ]
        }
    }
)
def delete(email_id: str) -> Dict[str, Union[str, bool]]:
    """Deletes a marketing email.

    Args:
        email_id(str): The unique ID of the marketing email to delete (required).

    Returns:
        Dict[str, Union[str, bool]]: A dictionary indicating success and a message.
            - success(bool): Whether the email was deleted successfully.
            - message(str): A message indicating the successof the email deletion.

    Raises:
        TypeError: If email_id is not a string.
        ValueError: If email_id is None or not found in the database.
    """
    if email_id is None:
        raise ValueError("email_id is required")

    if not isinstance(email_id, str):
        raise TypeError("email_id must be a string")

    marketing_emails = DB["marketing_emails"]

    if email_id not in marketing_emails:
        raise ValueError(f"Marketing email with given email_id not found.")

    del DB["marketing_emails"][email_id]
    return {"success": True, "message": "Marketing email deleted successfully."}


@tool_spec(
    spec={
        'name': 'clone_marketing_email',
        'description': 'Clones an existing marketing email.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email_id': {
                    'type': 'string',
                    'description': 'The ID of the marketing email to clone (required).'
                },
                'name': {
                    'type': 'string',
                    'description': 'The name for the new, cloned email (required).'
                }
            },
            'required': [
                'email_id',
                'name'
            ]
        }
    }
)
def clone(email_id: str, name: str) -> Dict[str, Union[str, bool]]:
    """Clones an existing marketing email.

    Args:
        email_id(str): The ID of the marketing email to clone (required).
        name(str): The name for the new, cloned email (required).

    Returns:
        Dict[str, Union[str, bool]]: A dictionary containing the new email's ID and a success message.
            - email_id(str): The unique ID of the newly created (cloned) marketing email.
            - success(bool): Whether the email was cloned successfully.
            - message(str): A message indicating the success of the email cloning.

    Raises:
        ValueError: If email_id is None, name is None, or email_id is not found in the database.
        TypeError: If email_id or name is not a string.
    """
    if email_id is None:
        raise ValueError("email_id is required")

    if not isinstance(email_id, str):
        raise TypeError("email_id must be a string")

    if name is None:
        raise ValueError("name is required")

    if not isinstance(name, str):
        raise TypeError("name must be a string")

    marketing_emails = DB.get("marketing_emails", {})
    if email_id not in marketing_emails:
        raise ValueError(f"Marketing email with given email_id not found.")

    original_email = DB["marketing_emails"][email_id]
    next_id = str(uuid.uuid4())

    DB["marketing_emails"][next_id] = original_email.copy()  # Create a shallow copy
    DB["marketing_emails"][next_id]["name"] = name

    return {
        "success": True,
        "message": "Marketing email cloned successfully.",
        "email_id": next_id,
    }
