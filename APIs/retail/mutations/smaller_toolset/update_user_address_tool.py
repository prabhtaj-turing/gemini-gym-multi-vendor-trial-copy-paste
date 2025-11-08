from retail.modify_user_address_tool import modify_user_address

def update_user_address(user_id: str, address1: str, address2: str, city: str, state: str, country: str, zip_code: str) -> dict:
    """
    Updates a user's address.

    Args:
        user_id (str): The ID of the user to modify.
        address1 (str): The first line of the address, such as '123 Main St'.
        address2 (str): The second line of the address, such as 'Apt 1' or ''.
        city (str): The city, such as 'San Francisco'.
        state (str): The state, such as 'CA'.
        country (str): The country, such as 'USA'.
        zip_code (str): The zip code, such as '12345'.

    Returns:
        dict: A dictionary containing the updated user information:
        - name (dict): The name of the user.
            - first_name (str): The first name of the user.
            - last_name (str): The last name of the user.
        - address (dict): The address of the user.
            - address1 (str): The first line of the address.
            - address2 (str): The second line of the address.
            - city (str): The city of the address.
            - country (str): The country of the address.
            - state (str): The state of the address.
            - zip (str): The zip code of the address.
        - email (str): The email of the user.
        - payment_methods (dict): A dictionary of payment methods.
        - orders (list): A list of order IDs for the user.

    Raises:
        Exception: If the user is not found or another error occurs.
    """
    try:
        return modify_user_address(user_id=user_id, address1=address1, address2=address2, city=city, state=state, country=country, zip_code=zip_code)
    except Exception as e:
        raise e
