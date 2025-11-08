"""Mock API for the CES Loyalty Auth agent."""

import json
from typing import Any, Dict, Optional, List

from . import db

DB = db.DB


def _set_conversation_status(status: Any, **kwargs) -> None:
    """Sets the conversation status in the database.

    Args:
      status (Any): The conversation status to set.
      **kwargs: Additional session parameters to store with the status.
    """
    DB["CONVERSATION_STATUS"] = {"status": status}
    if kwargs:
        DB["CONVERSATION_STATUS"]["session_params"] = kwargs


def get_conversation_status() -> Any:
    """Gets the conversation status from the database.

    Returns:
      Any: The conversation status.
    """
    return DB.get("CONVERSATION_STATUS")


def _set_session_status(status: Any) -> None:
    """Sets the session status in the database.

    Args:
      status (Any): The session status to set.
    """
    DB["SESSION_STATUS"] = {"status": status}


def get_session_status() -> Any:
    """Gets the session status from the database.

    Returns:
      Any: The session status.
    """
    return DB.get("SESSION_STATUS")


def set_auth_result(auth_result: Dict[str, Any]) -> None:
    """Sets the authentication result in the database.

    Args:
      auth_result (Dict[str, Any]): The authentication result data to store.
    """
    DB["AUTH_RESULT"] = auth_result


def update_auth_status() -> None:
    """Updates the authentication result status to the database.

    This function extracts the authentication status from the stored authentication
    result and updates the AUTH_STATUS in the database. It safely handles cases
    where the authentication result or its nested components may be missing.
    """
    # Safely get the auth result with proper None checking
    auth_result = DB.get("AUTH_RESULT")
    if auth_result is None:
        DB["AUTH_STATUS"] = None
        return

    session_info = auth_result.get("sessionInfo", {})
    if not session_info:
        DB["AUTH_STATUS"] = None
        return

    parameters = session_info.get("parameters", {})
    if not parameters:
        DB["AUTH_STATUS"] = None
        return

    session_map = parameters.get("sessionMap", {})
    if not session_map:
        DB["AUTH_STATUS"] = None
        return

    adaptive_authentication = session_map.get("adaptiveAuthentication", "")
    auth_status = None
    if adaptive_authentication:
        try:
            auth_status = json.loads(adaptive_authentication).get("authstatus")
        except json.JSONDecodeError:
            auth_status = "error: authentication not successful"
    DB["AUTH_STATUS"] = auth_status
	
    if auth_status == "ACCEPT" and parameters.get("authstate") == "AUTHENTICATION_INIT":
        DB["AUTH_RESULT"]["sessionInfo"]["parameters"]["authstate"] = "AUTHENTICATION_PENDING"


def set_preauth_data(preauth_data: Dict[str, Any]) -> None:
    """Sets the pre-authentication data in the database.

    Args:
      preauth_data (Dict[str, Any]): The pre-authentication customer data to store.
    """
    DB["PROFILE_BEFORE_AUTH"] = preauth_data


def set_customer_profile(profile_after_auth: Dict[str, Any]) -> None:
    """Sets the customer profile data after authentication in the database.

    Args:
      profile_after_auth (Dict[str, Any]): The authenticated customer profile data to store.
    """
    DB["PROFILE_AFTER_AUTH"] = profile_after_auth


def get_loyalty_offers() -> Optional[List[Dict[str, str]]]:
    """Gets the loyalty offers from the pre-authentication profile data.

    Returns:
      Optional[List[Dict[str, str]]]: The loyalty offers with the following structure:
        - OfferDesc(str): The description of the offer
        - offerOrder(str): The order of the offer
        - offerType(str): The type of the offer
        - OfferID(str): The ID of the offer
    """
    return (
        DB.get("PROFILE_BEFORE_AUTH", {})
        .get("sessionInfo", {})
        .get("parameters", {})
        .get("loyaltyOffers", [])
    )


def get_offer_enrollment() -> Optional[Dict[str, Any]]:
    """Gets the current offer enrollment status from the database.

    Returns:
      Optional[Dict[str, Any]]: The offer enrollment data with fields:
        - accountNumber(str): - The customer's account number
        - offerId(str): - The ID of the loyalty offer
      Returns None if not set.
    """
    return DB.get("OFFER_ENROLLMENT")


def get_auth_status() -> Optional[str]:
    """Gets the current authentication status from the database.

    Returns:
      Optional[str]: The authentication status (e.g., 'ACCEPT', 'REJECT', 'PENDING'),
      or None if not set.
    """
    return DB.get("AUTH_STATUS")


def get_customer_name_from_preauth() -> Optional[str]:
    """Gets the customer name from the pre-authentication profile data.

    Returns:
      Optional[str]: The customer's full name from PROFILE_BEFORE_AUTH,
      or None if not available.
    """
    profile_before_auth = DB.get("PROFILE_BEFORE_AUTH")
    if not profile_before_auth:
        return None

    session_info = profile_before_auth.get("sessionInfo", {})
    if not session_info:
        return None

    parameters = session_info.get("parameters", {})
    if not parameters:
        return None

    return parameters.get("customerName")

def get_customer_account_number_from_preauth() -> Optional[str]:
    """Gets the customer account number from the pre-authentication profile data.

    Returns:
      Optional[str]: The customer's account number from PROFILE_BEFORE_AUTH,
      or None if not available.
    """
    profile_before_auth = DB.get("PROFILE_BEFORE_AUTH")
    if not profile_before_auth:
        return None

    session_info = profile_before_auth.get("sessionInfo", {})
    if not session_info:
        return None

    parameters = session_info.get("parameters", {})
    if not parameters:
        return None

    return parameters.get("accountNumber")
