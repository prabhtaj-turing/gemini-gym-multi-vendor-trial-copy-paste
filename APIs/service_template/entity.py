"""
Generic Service-Specific Tool Implementation

This module provides the core functionality for the service.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict,  Union
from .SimulationEngine import utils
from .SimulationEngine.models import ToolInput, ToolOutput
from .SimulationEngine.custom_errors import ValidationError
from APIs.common_utils.tool_spec_decorator import tool_spec, ErrorObject


@tool_spec(
    input_model=ToolInput,
    output_model=ToolOutput,
    error_model=[
        ErrorObject(ValidationError, ["Raised if 'entity_name' is not a non-empty string or exceeds 100 characters.",\
         "Raised if 'complex_param' does not conform to the required structure or if its values have incorrect types (e.g., a non-positive integer for 'value')"]),
    ],
    description="A generic tool that creates or modifies an entity."

)
def tool(
    entity_name: str,
    complex_param: Dict[str, Union[str, int, bool]],
    is_dry_run: bool = False
) -> Dict[str, Union[bool, str, dict]]:
    """A generic tool that creates or modifies an entity.

    This function serves as a template for a standard tool. It validates all
    input parameters, delegates the core business logic to a separate utility
    function, and formats the final output into a structured dictionary.

    Args:
        entity_name (str): The name of the entity to create or modify. This must
            be a non-empty string with a maximum length of 100 characters.
        complex_param (Dict[str, Union[str, int, bool]]): A dictionary containing the configuration
            for the entity. It must conform to the following structure:
            - config_name (str): The name of the configuration. This is a
              mandatory, non-empty string.
            - value (int): A numerical value for the configuration. This is a
              mandatory, positive integer.
            - enabled (bool): A flag to enable or disable this configuration.
              This is optional and defaults to True if not provided.
        is_dry_run (bool): If True, the function will only validate the inputs
            and return a success message without performing any actual entity
            creation or modification. Defaults to False.

    Returns:
        Dict[str, Union[bool, str, dict]]: A dictionary containing the result of the operation,
        structured as follows:
        - success (bool): Indicates whether the operation was successful.
        - message (str): A human-readable message describing the outcome.
        - data (Dict[str, Union[str, dict]]): A dictionary containing the detailed
          payload of the response, with the following keys:
          - entity_id (str): The unique identifier of the entity that was
            affected by the operation. In a dry run, this will be
            'dry-run-not-created'.
          - params_received (dict): A dictionary reflecting the
            exact parameters that were received and validated by the tool. It
            contains the following keys:
            - entity_name (str): The original 'entity_name' input.
            - complex_param (dict): The original 'complex_param' input,
              validated and with defaults applied. It contains 'config_name' (str),
              'value' (int), and 'enabled' (bool).
            - is_dry_run (bool): The original 'is_dry_run' input.

    Raises:
        ValidationError: If any of the input parameters fail validation.
            - Raised if 'entity_name' is not a non-empty string or exceeds
              100 characters.
            - Raised if 'complex_param' does not conform to the required
              structure or if its values have incorrect types (e.g., a
              non-positive integer for 'value').
    """


    if is_dry_run:
        # If it's a dry run, return a success message after validation
        return utils.build_tool_response(
            entity_id="dry-run-not-created",
            message="Dry run successful. Inputs are valid.",
            inputs={
                "entity_name": entity_name,
                "complex_param": complex_param,
                "is_dry_run": is_dry_run
            }
        )

    # 2. Business Logic Delegation
    # Call a utility function to perform the core logic.
    result_data = utils.perform_action(
        name=entity_name
    )

    # 3. Response Formatting
    # The response is built by a dedicated utility function to ensure consistency.
    output = utils.build_tool_response(
        entity_id=result_data["entity_id"],
        message=result_data["status_message"],
        inputs={
            "entity_name": entity_name,
            "complex_param": complex_param,
            "is_dry_run": is_dry_run
        }
    )

    # 4. Return Value
    return output
