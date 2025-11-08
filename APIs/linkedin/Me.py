from common_utils.tool_spec_decorator import tool_spec
from typing import Type, Dict, Any, Optional, TypedDict, Union
import re
from .SimulationEngine.db import DB
from .SimulationEngine.models import PersonDataModel, ProjectionModel
from .SimulationEngine.custom_errors import UserNotFoundError
from pydantic import ValidationError
"""
API simulation for the '/me' resource.
"""

class PreferredLocale(TypedDict):
    country: str
    language: str

class LocalizedName(TypedDict):
    localized: Dict[str, str]
    preferredLocale: PreferredLocale

class PersonData(TypedDict):
    localizedFirstName: str
    localizedLastName: str
    vanityName: str
    firstName: LocalizedName
    lastName: LocalizedName
    id: str
@tool_spec(
    spec={
        'name': 'get_my_profile',
        'description': "Retrieves the authenticated member's profile data from the database.",
        'parameters': {
            'type': 'object',
            'properties': {
                'projection': {
                    'type': 'string',
                    'description': """ Field projection syntax for controlling which fields to return.
                    The projection string should consist of comma-separated field names and may optionally
                    be enclosed in parentheses. Defaults to None. """
                }
            },
            'required': []
        }
    }
)
def get_me(projection: Optional[str] = None
           ) -> Dict[str, Union[Dict[str, Union[str, Dict[str, Dict[str, str]]]]]]:
    """
    Retrieves the authenticated member's profile data from the database.

    Args:
        projection (Optional[str]): Field projection syntax for controlling which fields to return.
            The projection string should consist of comma-separated field names and may optionally
            be enclosed in parentheses. Defaults to None.

    Returns:
        Dict[str, Union[Dict[str, Union[str, Dict[str, Dict[str, str]]]]]]:
        - On successful retrieval, returns a dictionary with the following keys and value types:
            - 'data' (Dict[str, Union[str, Dict[str, Dict[str, str]]]]): Dictionary of member profile data with keys:
                - 'id' (str): Unique identifier of the member.
                - 'localizedFirstName' (str): Member's first name.
                - 'localizedLastName' (str): Member's last name.
                - 'vanityName' (str): URL-friendly version of the member's name.
                - 'firstName' (Dict[str, Dict[str, str]]): Localized first name with keys:
                    - 'localized' (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                    - 'preferredLocale' (Dict[str, str]): Dictionary with keys:
                        - 'country' (str): Country code (e.g., 'US').
                        - 'language' (str): Language code (e.g., 'en').
                - 'lastName' (Dict[str, Dict[str, str]]): Localized last name with keys:
                    - 'localized' (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                    - 'preferredLocale' (Dict[str, str]): Dictionary with keys:
                        - 'country' (str): Country code (e.g., 'US').
                        - 'language' (str): Language code (e.g., 'en').
    Raises:
        ValidationError: If projection string is malformed.
        UserNotFoundError: If not authenticated user is found.
    """
    current_id = DB.get("current_person_id")
    if current_id is None:
        raise UserNotFoundError("No authenticated member.")
    person = DB["people"].get(current_id)
    if person is None:
        raise UserNotFoundError("Authenticated person not found.")

    try:
        validated = ProjectionModel(projection=projection)
    except ValidationError as e:
        raise e

    if projection == "":
        return {"data": person}
    if validated.projection:
        fields = [field.strip() for field in validated.projection.strip("()").split(',')]
        projected_person = {field: person.get(field) for field in fields if field in person}
        return {"data": projected_person}

    return {"data": person}

@tool_spec(
    spec={
        'name': 'create_my_profile',
        'description': 'Creates a new member profile and sets it as the current authenticated member.',
        'parameters': {
            'type': 'object',
            'properties': {
                'person_data': {
                    'type': 'object',
                    'description': "Dictionary containing the new member's profile data with keys:",
                    'properties': {
                        'localizedFirstName': {
                            'type': 'string',
                            'description': "Member's first name."
                        },
                        'localizedLastName': {
                            'type': 'string',
                            'description': "Member's last name."
                        },
                        'vanityName': {
                            'type': 'string',
                            'description': "URL-friendly version of the member's name."
                        },
                        'firstName': {
                            'type': 'object',
                            'description': 'Localized first name with keys:',
                            'properties': {
                                'localized': {
                                    'type': 'object',
                                    'description': "Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.",
                                    'properties': {},
                                    'required': []
                                },
                                'preferredLocale': {
                                    'type': 'object',
                                    'description': 'Dictionary with keys:',
                                    'properties': {
                                        'country': {
                                            'type': 'string',
                                            'description': "Country code (e.g., 'US')."
                                        },
                                        'language': {
                                            'type': 'string',
                                            'description': "Language code (e.g., 'en')."
                                        }
                                    },
                                    'required': [
                                        'country',
                                        'language'
                                    ]
                                }
                            },
                            'required': [
                                'localized',
                                'preferredLocale'
                            ]
                        },
                        'lastName': {
                            'type': 'object',
                            'description': 'Localized last name with keys:',
                            'properties': {
                                'localized': {
                                    'type': 'object',
                                    'description': "Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.",
                                    'properties': {},
                                    'required': []
                                },
                                'preferredLocale': {
                                    'type': 'object',
                                    'description': 'Dictionary with keys:',
                                    'properties': {
                                        'country': {
                                            'type': 'string',
                                            'description': "Country code (e.g., 'US')."
                                        },
                                        'language': {
                                            'type': 'string',
                                            'description': "Language code (e.g., 'en')."
                                        }
                                    },
                                    'required': [
                                        'country',
                                        'language'
                                    ]
                                }
                            },
                            'required': [
                                'localized',
                                'preferredLocale'
                            ]
                        }
                    },
                    'required': [
                        'localizedFirstName',
                        'localizedLastName',
                        'vanityName',
                        'firstName',
                        'lastName'
                    ]
                }
            },
            'required': [
                'person_data'
            ]
        }
    }
)
def create_me(person_data: Dict[str, Union[str, Dict[str, Dict[str, str]]]]
              ) -> Dict[str, Dict[str, Union[str, Dict[str, Dict[str, str]]]]]:
    """
    Creates a new member profile and sets it as the current authenticated member.

    Args:
        person_data (Dict[str, Union[str, Dict[str, Dict[str, str]]]]): Dictionary containing the new member's profile data with keys:
            - localizedFirstName (str): Member's first name.
            - localizedLastName (str): Member's last name.
            - vanityName (str): URL-friendly version of the member's name.
            - firstName (Dict[str, Dict[str, str]]): Localized first name with keys:
                - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                - preferredLocale (Dict[str, str]): Dictionary with keys:
                    - country (str): Country code (e.g., 'US').
                    - language (str): Language code (e.g., 'en').
            - lastName (Dict[str, Dict[str, str]]): Localized last name with keys:
                - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                - preferredLocale (Dict[str, str]): Dictionary with keys:
                    - country (str): Country code (e.g., 'US').
                    - language (str): Language code (e.g., 'en').

    Returns:
        Dict[str, Dict[str, Union[str, Dict[str, Dict[str, str]]]]]: It returns a Member Profile.
            - data (Dict[str, Union[str, Dict[str, Dict[str, str]]]]): Dictionary containing the new member's profile data with keys:
                - id (str): Newly assigned unique identifier.
                - localizedFirstName (str): Member's first name.
                - localizedLastName (str): Member's last name.
                - vanityName (str): URL-friendly version of the member's name.
                - firstName (Dict[str, Dict[str, str]]): Localized first name with keys:
                    - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                    - preferredLocale (Dict[str, str]): Dictionary with keys:
                        - country (str): Country code (e.g., 'US').
                        - language (str): Language code (e.g., 'en').
                - lastName (Dict[str, Dict[str, str]]): Localized last name with keys:
                    - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                    - preferredLocale (Dict[str, str]): Dictionary with keys:
                        - country (str): Country code (e.g., 'US').
                        - language (str): Language code (e.g., 'en').

    Raises:
        ValueError: If the authenticated member already exists or if the person data is invalid.
    """
    if DB.get("current_person_id") is not None:
        raise ValueError("Authenticated member already exists.")
    
    # Validate the person_data before processing
    try:    
        validated_data = PersonDataModel(**person_data)
        person_data = validated_data.model_dump()
    except ValidationError as e:
        for error_detail in e.errors():
            loc = error_detail.get('loc')
            msg = error_detail.get('msg')
            field_name = ".".join(map(str, loc)) if loc else "unknown_field"
            error_message = f"Input Validation Failed for {field_name}"
            raise ValueError(error_message)

     
    new_id = str(DB["next_person_id"])
    DB["next_person_id"] += 1
    person_data["id"] = new_id
    DB["people"][new_id] = person_data
    DB["current_person_id"] = new_id
    return {"data": person_data}

@tool_spec(
    spec={
        'name': 'update_my_profile',
        'description': "Updates the authenticated member's profile data in the database.",
        'parameters': {
            'type': 'object',
            'properties': {
                'person_data': {
                    'type': 'object',
                    'description': 'Dictionary containing updated member profile data to be applied.:',
                    'properties': {
                        'localizedFirstName': {
                            'type': 'string',
                            'description': 'Updated first name.'
                        },
                        'localizedLastName': {
                            'type': 'string',
                            'description': 'Updated last name.'
                        },
                        'vanityName': {
                            'type': 'string',
                            'description': "URL-friendly version of the member's name."
                        },
                        'firstName': {
                            'type': 'object',
                            'description': 'Localized first name with keys:',
                            'properties': {
                                'localized': {
                                    'type': 'object',
                                    'description': "Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.",
                                    'properties': {},
                                    'required': []
                                },
                                'preferredLocale': {
                                    'type': 'object',
                                    'description': 'Dictionary with keys:',
                                    'properties': {
                                        'country': {
                                            'type': 'string',
                                            'description': "Country code (e.g., 'US')."
                                        },
                                        'language': {
                                            'type': 'string',
                                            'description': "Language code (e.g., 'en')."
                                        }
                                    },
                                    'required': [
                                        'country',
                                        'language'
                                    ]
                                }
                            },
                            'required': [
                                'localized',
                                'preferredLocale'
                            ]
                        },
                        'lastName': {
                            'type': 'object',
                            'description': 'Localized last name with keys:',
                            'properties': {
                                'localized': {
                                    'type': 'object',
                                    'description': "Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.",
                                    'properties': {},
                                    'required': []
                                },
                                'preferredLocale': {
                                    'type': 'object',
                                    'description': 'Dictionary with keys:',
                                    'properties': {
                                        'country': {
                                            'type': 'string',
                                            'description': "Country code (e.g., 'US')."
                                        },
                                        'language': {
                                            'type': 'string',
                                            'description': "Language code (e.g., 'en')."
                                        }
                                    },
                                    'required': [
                                        'country',
                                        'language'
                                    ]
                                }
                            },
                            'required': [
                                'localized',
                                'preferredLocale'
                            ]
                        }
                    },
                    'required': [
                        'localizedFirstName',
                        'localizedLastName',
                        'vanityName',
                        'firstName',
                        'lastName'
                    ]
                }
            },
            'required': [
                'person_data'
            ]
        }
    }
)
def update_me(person_data: Dict[str, Union[str, Dict[str, Dict[str, str]]]]
              ) -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, Dict[str, str]]]]]]:
    """
    Updates the authenticated member's profile data in the database.

    Args:
        person_data (Dict[str, Union[str, Dict[str, Dict[str, str]]]]): Dictionary containing the updated member profile data with keys:
            - localizedFirstName (str): Updated first name.
            - localizedLastName (str): Updated last name.
            - vanityName (str): URL-friendly version of the member's name.
            - firstName (Dict[str, Dict[str, str]]): Localized first name with keys:
                - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                - preferredLocale (Dict[str, str]): Dictionary with keys:
                    - country (str): Country code (e.g., 'US').
                    - language (str): Language code (e.g., 'en').
            - lastName (Dict[str, Dict[str, str]]): Localized last name with keys:
                - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                - preferredLocale (Dict[str, str]): Dictionary with keys:
                    - country (str): Country code (e.g., 'US').
                    - language (str): Language code (e.g., 'en').

    Returns:
        Dict[str, Union[str, Dict[str, Union[str, Dict[str, Dict[str, str]]]]]]: It returns a Updated Member Profile.
            - data (Dict[str, Union[str, Dict[str, Dict[str, str]]]]): Dictionary containing the updated member's profile data with keys:
                - id (str): Member's unique identifier.
                - localizedFirstName (str): Updated first name.
                - localizedLastName (str): Updated last name.
                - vanityName (str): URL-friendly version of the member's name.
                - firstName (Dict[str, Dict[str, str]]): Localized first name with keys:
                    - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                    - preferredLocale (Dict[str, str]): Dictionary with keys:
                        - country (str): Country code (e.g., 'US').
                        - language (str): Language code (e.g., 'en').
                - lastName (Dict[str, Dict[str, str]]): Localized last name with keys:
                    - localized (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                    - preferredLocale (Dict[str, str]): Dictionary with keys:
                        - country (str): Country code (e.g., 'US').
                        - language (str): Language code (e.g., 'en').

    Raises:
        ValueError: If the authenticated member is not found or if the person data is invalid.
    """
    current_id = DB.get("current_person_id")
    if current_id is None or current_id not in DB["people"]:
        raise ValueError("Authenticated member not found.")
    
    # Validate the person_data before processing
    try:    
        validated_data = PersonDataModel(**person_data)
        person_data = validated_data.model_dump()
    except ValidationError as e:
        for error_detail in e.errors():
            loc = error_detail.get('loc')
            field_name = ".".join(map(str, loc)) if loc else "unknown_field"
            error_message = f"Input Validation Failed for {field_name}"
            raise ValueError(error_message)

    person_data["id"] = current_id
    DB["people"][current_id] = person_data
    return {"data": person_data}

@tool_spec(
    spec={
        'name': 'delete_my_profile',
        'description': "Deletes the authenticated member's profile from the database.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def delete_me() -> Dict[str, str]:
    """
    Deletes the authenticated member's profile from the database.

    Returns:
        Dict[str, str]:
        - On successful deletion, returns a dictionary with the following keys and value types:
            - 'status' (str): Success message confirming deletion.

    Raises:
        ValueError: If no authenticated member exists or the authenticated
            member's profile is not found.
    """
    current_id = DB.get("current_person_id")
    if current_id is None or current_id not in DB["people"]:
        raise ValueError("Authenticated member not found.")
    del DB["people"][current_id]
    DB["current_person_id"] = None
    return {"status": "Authenticated member deleted."}