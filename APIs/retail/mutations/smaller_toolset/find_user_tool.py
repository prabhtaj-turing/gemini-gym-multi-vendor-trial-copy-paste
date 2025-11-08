from typing import Optional
from retail.find_user_id_by_email_tool import find_user_id_by_email
from retail.find_user_id_by_name_zip_tool import find_user_id_by_name_zip

def find_user(email: Optional[str] = None, user_name: Optional[str] = None, zip_code: Optional[str] = None) -> dict:
    """
    Finds a user by email or by name and zip code.

    Args:
        email (Optional[str]): The email of the user to find.
        user_name (Optional[str]): The name of the user to find.
        zip_code (Optional[str]): The zip code of the user to find.

    Returns:
        dict: A dictionary containing the user ID.
        Example: `{"user_id": "user_12345"}`

    Raises:
        ValueError: If the required parameters for finding a user are not provided.
        Exception: If the user is not found or another error occurs.
    """
    try:
        if email:
            return find_user_id_by_email(email=email)
        elif user_name and zip_code:
            return find_user_id_by_name_zip(user_name=user_name, zip_code=zip_code)
        else:
            raise ValueError("Either email or both user_name and zip_code must be provided.")
    except Exception as e:
        raise e
