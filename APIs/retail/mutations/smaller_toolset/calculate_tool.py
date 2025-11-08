from retail.calculate_tool import calculate

def evaluate_expression(expression: str) -> dict:
    """
    Evaluates a mathematical expression.

    Args:
        expression (str): The mathematical expression to evaluate.

    Returns:
        dict: A dictionary containing the result of the evaluation.
        Example: `{"result": 4}`

    Raises:
        Exception: If the expression is invalid.
    """
    try:
        return {"result": calculate(expression=expression)}
    except Exception as e:
        raise e
