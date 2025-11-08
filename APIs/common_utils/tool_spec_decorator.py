import inspect
from functools import wraps
from pydantic import BaseModel, ValidationError, Field
from typing import List, Type

class ErrorObject:
    """A simple class to describe a type of error and its reasons."""
    def __init__(self, error_type: Type[Exception], reasons: List[str]):
        if not (isinstance(error_type, type) and issubclass(error_type, Exception)):
            raise ValueError("error_type must be an Exception class")
        
        self.error_type = error_type.__name__
        self.error_class = error_type
        self.reasons = reasons

    def to_dict(self):
        return {"type": self.error_type, "description": " ".join(self.reasons)}

def _clean_and_inline_schema(schema, definitions, is_property=False):
    """
    Recursively cleans a Pydantic-generated schema to match the legacy format.
    - Removes 'title' keys.
    - Inlines nested models from the '$defs' section.
    - Removes Pydantic-specific fields like 'default', 'minLength', 'maxLength', etc.
    - Keeps only 'description' and 'type' for properties (plus 'anyOf' for nullable fields).
    - Ensures 'required' is always present as an empty array if not specified.
    """
    if isinstance(schema, dict):
        # Remove title
        schema.pop("title", None)
        
        # Remove the description from the root parameters object (input model docstring)
        # But keep properties, type, and required
        if "properties" in schema and "description" in schema and schema.get("type") == "object":
            # This is the parameters object - remove its description
            schema.pop("description", None)
        
        # Inline references
        if "$ref" in schema:
            def_name = schema["$ref"].split("/")[-1]
            nested_schema = definitions.get(def_name, {})
            return _clean_and_inline_schema(nested_schema, definitions, is_property)
        
        # For properties inside a properties object, clean extra fields
        if is_property and ("type" in schema or "anyOf" in schema):
            # This is a property definition - keep only essential fields
            # Preserve 'required' for nested objects to retain strictness
            allowed_fields = {"description", "type", "anyOf", "properties", "required"}
            schema = {k: v for k, v in schema.items() if k in allowed_fields}
        
        # Ensure required array exists for object types with properties
        if schema.get("type") == "object" and "properties" in schema:
            if "required" not in schema:
                schema["required"] = []
        
        # Recursively clean all values and ensure proper field ordering
        result = {}
        
        # For parameters object: type, properties, required (in that order)
        if schema.get("type") == "object" and "properties" in schema:
            # Add type first
            result["type"] = "object"
            # Then properties
            if isinstance(schema["properties"], dict):
                result["properties"] = {k: _clean_and_inline_schema(v, definitions, is_property=True) 
                                       for k, v in schema["properties"].items()}
            # Then required
            if "required" in schema:
                result["required"] = schema["required"]
            # Then any other keys
            for key, value in schema.items():
                if key not in ["type", "properties", "required"]:
                    result[key] = _clean_and_inline_schema(value, definitions, is_property=False)
        else:
            # For other objects, process normally
            for key, value in schema.items():
                if key == "properties" and isinstance(value, dict):
                    result[key] = {k: _clean_and_inline_schema(v, definitions, is_property=True) 
                                  for k, v in value.items()}
                else:
                    result[key] = _clean_and_inline_schema(value, definitions, is_property=False)
        
        return result
            
    elif isinstance(schema, list):
        return [_clean_and_inline_schema(item, definitions, is_property) for item in schema]
    return schema

def tool_spec(
    input_model=None,
    output_model=None,
    error_model: List[ErrorObject] = None,
    spec=None,
    description=None
):
    """
    A decorator that attaches a specification to a function and handles
    Pydantic-based validation.
    ...
    """
    def decorator(func):
        if input_model and output_model:
            # --- Pydantic Mode ---
            raw_schema = input_model.model_json_schema()
            definitions = raw_schema.pop('$defs', {})
            input_schema = _clean_and_inline_schema(raw_schema, definitions)
            final_spec = {
                "name": func.__name__,
                "description": description or func.__doc__,
                "parameters": input_schema,
            }

            @wraps(func)
            def wrapper(*args, **kwargs):

                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                input_data = dict(bound_args.arguments)
                validated_input = input_model(**input_data)
                result = func(**validated_input.model_dump())
                
                # Handle string return types - validate but don't wrap
                if isinstance(result, str):
                    # Get the first field name from the output model
                    output_fields = list(output_model.model_fields.keys())
                    if output_fields:
                        field_name = output_fields[0]
                        # Validate by wrapping, but return the original string
                        validated_output = output_model(**{field_name: result})
                        return result  # Return original string, not wrapped dict
                
                validated_output = output_model(**result)
                return validated_output.model_dump()

            wrapper.spec = spec or final_spec
            return wrapper
        else:
            # --- Legacy Mode ---
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            # Attach the spec dictionary directly to the wrapper.
            wrapper.spec = spec
            return wrapper
    return decorator
