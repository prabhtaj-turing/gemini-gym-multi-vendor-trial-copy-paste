from common_utils.tool_spec_decorator import tool_spec
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import InvalidExpressionError, InvalidInputError
from retail.SimulationEngine.models import CalculateInput


@tool_spec(
    spec={
        'name': 'calculate',
        'description': 'Calculate the result of a mathematical expression.',
        'parameters': {
            'type': 'object',
            'properties': {
                'expression': {
                    'type': 'string',
                    'description': """ The mathematical expression to calculate, such as '2 + 2'.
                    The expression can contain numbers, operators (+, -, *, /),
                    parentheses, and spaces. """
                }
            },
            'required': [
                'expression'
            ]
        }
    }
)
def calculate(expression: str) -> str:
    """Calculate the result of a mathematical expression.

    Args:
        expression (str): The mathematical expression to calculate, such as '2 + 2'.
            The expression can contain numbers, operators (+, -, *, /),
            parentheses, and spaces.

    Returns:
        str: The result of the calculation.

    Raises:
        InvalidExpressionError: If the expression is invalid.
        InvalidInputError: If the input is invalid.
    """
    try:
        CalculateInput(expression=expression)
    except ValidationError as e:
        raise InvalidInputError(e)

    if not all(char in "0123456789+-*/(). " for char in expression):
        raise InvalidExpressionError("Error: invalid characters in expression")
    try:
        result = round(float(eval(expression, {"__builtins__": None}, {})), 2)
        return str(result)
    except Exception as e:
        raise InvalidExpressionError(f"Error: {e}")
