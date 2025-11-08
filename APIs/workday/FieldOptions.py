"""
This module provides functionality for managing field options in the Workday
Strategic Sourcing system. It supports creating new field options with specified
parameters and associating them with specific fields. The module enables
comprehensive field option management and configuration capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Optional, Union, Any
import uuid
import re
from .SimulationEngine import db
from .SimulationEngine.models import FieldOptionsModel, FieldOptionItem
from .SimulationEngine.custom_errors import DuplicateExternalIdError, ValidationError, InvalidInputError
from pydantic import ValidationError as PydanticValidationError

@tool_spec(
    spec={
        'name': 'create_field_options',
        'description': 'Creates a new field option with given parameters..',
        'parameters': {
            'type': 'object',
            'properties': {
                'new_id': {
                    'type': 'string',
                    'description': """ The field ID to associate the options with. If not provided, the field ID will be generated.
                    Must be a string if provided. """
                },
                'options': {
                    'type': 'array',
                    'description': """ A list of string options to be associated with the field.
                    Can be None, in which case the field is created with no options.
                    Empty or whitespace-only strings are rejected. """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': []
        }
    }
)
def post(new_id: Optional[str] = None, options: Optional[List[str]] = None) -> Dict[str, Any]:
    """Creates a new field option with given parameters..

    Args:
        new_id (Optional[str]): The field ID to associate the options with. If not provided, the field ID will be generated.
                     Must be a string if provided.
        options (Optional[List[str]]): A list of string options to be associated with the field.
                    Can be None, in which case the field is created with no options.
                    Empty or whitespace-only strings are rejected.
        
    Returns:
        Dict[str, Any]: The created field-option data. Contains:
            - field_id (str): The field ID
            - options (List[str]): The list of validated string options

    Raises:
        TypeError: If new_id is provided but is not a string, or if options is provided but is not a list.
        InvalidInputError: If any option item doesn't have a required 'value' attribute.
        DuplicateExternalIdError: If the provided new_id already exists in the database.
    """
    # Validate new_id type if provided
    if new_id is not None and not isinstance(new_id, str):
        raise TypeError("new_id must be a string")
        
    # Generate a UUID if new_id is not provided
    if not new_id:
        new_id = str(uuid.uuid4())
    
    # Validate new_id format (basic format check - can be expanded as needed)
    if new_id.strip() == "":
        raise InvalidInputError("new_id cannot be empty or whitespace only")
    
    # Check for existing field_id
    if new_id in db.DB["fields"]["field_options"]:
        raise DuplicateExternalIdError(f"Field option with ID '{new_id}' already exists")
    
    # Validate options type if provided
    if options is not None and not isinstance(options, list):
        raise TypeError("options must be a list or None")
    
    # Convert raw options list to properly formatted FieldOptionItem objects if provided
    validated_options: Optional[List[str]] = None
    if options is not None:
        if not isinstance(options, list):
            raise TypeError("options must be a list of strings or None")

        validated_options = []
        for idx, opt in enumerate(options):
            if not isinstance(opt, str):
                raise TypeError(f"Option at index {idx} must be a string")
            if opt.strip() == "":
                print(f"DEBUG: idx={idx}, opt={repr(opt)}")
                raise InvalidInputError(
                    f"Option at index {idx} cannot be empty or whitespace"
                )
            validated_options.append(opt.strip())
    
    # Validate using Pydantic model
    try:
        field_options_data = FieldOptionsModel(
            field_id=new_id,
            options=validated_options
        )
        
        # Store the validated data
        new_field_option = field_options_data.model_dump()
        db.DB["fields"]["field_options"][new_id] = new_field_option
        return new_field_option
        
    except PydanticValidationError as e:
        # Convert Pydantic validation error to a more specific error
        raise ValidationError(f"Field option validation failed: {str(e)}")
    except Exception as e:
        # Handle any other unexpected errors
        raise InvalidInputError(f"Failed to create field option: {str(e)}") 
