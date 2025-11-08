"""
This module provides functionality for managing payment terms used in the Workday Strategic Sourcing system.
It supports operations for retrieving all available payment terms and creating new term entries.
Each payment term is identified by its name and an optional external identifier, which is useful for
integration with external systems that maintain their own payment term identifiers.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict,  Optional, Any
from .SimulationEngine import db
from .SimulationEngine import custom_errors

@tool_spec(
    spec={
        'name': 'list_payment_terms',
        'description': """ Retrieves a list of all available payment terms in the system.
        
        This function returns a list of dictionaries, each containing the details of a payment term in the Database. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[Dict]:
    """
    Retrieves a list of all available payment terms in the system.

    This function returns a list of dictionaries, each containing the details of a payment term in the Database.

    Returns:
        List[Dict]: A list of payment term objects, each containing any of the following fields:
                   - id (int): Payment term identifier string
                   - name (str): The name of the payment term
                   - external_id (str, optional): Optional external identifier
    """
    if "payments" not in db.DB:
        return []
    if "payment_terms" not in db.DB["payments"]:
        return []
    return db.DB["payments"]["payment_terms"]

@tool_spec(
    spec={
        'name': 'create_payment_term',
        'description': """ Creates a new payment term entry in the system.
        
        This function includes a new payment term entry in the database given a name and an optional external identifier. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the payment term (e.g., "Net 30", "Net 60").'
                },
                'external_id': {
                    'type': 'string',
                    'description': 'An external identifier for the payment term.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def post(name: str, external_id: Optional[str] = None) -> Dict:
    """
    Creates a new payment term entry in the system.

    This function includes a new payment term entry in the database given a name and an optional external identifier.

    Args:
        name (str): The name of the payment term (e.g., "Net 30", "Net 60").
        external_id (Optional[str]): An external identifier for the payment term.

    Returns:
        Dict: The newly created payment term object containing any of the following fields:
            - id (str): Payment term identifier string
            - name (str): The name of the payment term
            - external_id (Optional[str]): Optional external identifier
    
    Raises:
        InvalidInputError: If the input parameters are not valid
    """
    # Input Validation
    if not isinstance(name, str):
        raise custom_errors.InvalidInputError("Name must be a string")
    
    if name == "":
        raise custom_errors.InvalidInputError("Name cannot be empty")
    
    if name.strip() == "":
        raise custom_errors.InvalidInputError("Name cannot have only whitespace")
    
    if external_id is not None:
        if not isinstance(external_id, str):
            raise custom_errors.InvalidInputError("External ID must be a string")
        
        if external_id == "":
            raise custom_errors.InvalidInputError("External ID cannot be empty")
        
        if external_id.strip() == "":
            raise custom_errors.InvalidInputError("External ID cannot have only whitespace")
    
    new_term = {
        "id": db.DB["payments"]["payment_term_id_counter"],
        "name": name,
        "external_id": external_id,
    }
    db.DB["payments"]["payment_terms"].append(new_term)
    db.DB["payments"]["payment_term_id_counter"] += 1
    return new_term 