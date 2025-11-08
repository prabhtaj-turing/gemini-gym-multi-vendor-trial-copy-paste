from retail.transfer_to_human_agents_tool import transfer_to_human_agents

def escalate_to_human_support(problem_description: str) -> dict:
    """
    Escalates an issue to a human agent.

    Args:
        problem_description (str): A description of the problem to be escalated.

    Returns:
        dict: A dictionary containing a confirmation message.
        Example: `{"message": "Your request has been escalated to a human agent."}`

    Raises:
        Exception: If an error occurs during the escalation process.
    """
    try:
        message = transfer_to_human_agents(summary=problem_description)
        return {"message": message}
    except Exception as e:
        replacements = {
            "summary": "problem_description"
        }
        error_message = str(e)
        for old, new in replacements.items():
            error_message = error_message.replace(old, new)
        raise e
