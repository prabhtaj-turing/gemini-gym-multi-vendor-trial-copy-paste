"""
Supplier Company Field Description Module

This module provides functionality for describing the fields available in the
supplier company object. It allows users to retrieve a list of all available
fields that can be used when working with supplier company data.

The module interfaces with the simulation database to provide field information
for supplier company objects, enabling users to understand the structure and
available attributes of supplier company data.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Tuple, Union, Any, Dict
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'describe_supplier_company_fields',
        'description': 'Describes the Supplier Company object fields.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> Dict[str, Any]:
    """
    Describes the Supplier Company object fields.

    Returns:
        Dict[str, Any]: A dictionary containing the Supplier Company object fields.

            - data (List[str]):  
                List of supplier company field names.

                - type (str):  
                    Object type.  
                    Always `"supplier_company_fields"`.

                - id (str):  
                    Field identifier string.

                - attributes (Dict[str, Any]):  
                    Field metadata including:
                    
                    - name (str):  
                        Human-readable field name.  
                        Maximum length: 255 characters.

                    - data_type (str):  
                        OpenAPI-compatible data type.  
                        One of:
                        - `"string"`
                        - `"number"`
                        - `"integer"`
                        - `"boolean"`
                        - `"array"`
                        - `"object"`

                    - scout_field_type (str):  
                        Internal custom field type name.  
                        One of:
                        - `"Checkbox"`
                        - `"File"`
                        - `"Short Text"`
                        - `"Paragraph"`
                        - `"Date"`
                        - `"Integer"`
                        - `"Currency"`
                        - `"Decimal"`
                        - `"Single Select"`
                        - `"Multiple Select"`
                        - `"URL"`
                        - `"Lookup"`
                        - `"Related"`

                    - custom_field (bool):  
                        Flag indicating whether the field is a **user-created custom field** (`True`)
                        or an **internal system field** (`False`).
    """

    if not db.DB.get("suppliers", {}).get("supplier_companies"):
        return []
    return list(db.DB["suppliers"]["supplier_companies"][list(db.DB["suppliers"]["supplier_companies"].keys())[0]].keys())