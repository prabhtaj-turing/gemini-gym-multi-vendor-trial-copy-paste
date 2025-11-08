from retail.think_tool import think

def log_thought(thought: str) -> dict:
    """
    Logs a thought.

    Args:
        thought (str): The thought to log.

    Returns:
        dict: A dictionary containing a confirmation message.
        Example: `{"status": "Thought logged"}`

    Raises:
        Exception: If an error occurs during the process.
    """
    try:
        think(thought=thought)
        return {"status": "Thought logged"}
    except Exception as e:
        raise e
