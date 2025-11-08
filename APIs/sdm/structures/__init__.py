from common_utils.tool_spec_decorator import tool_spec
from sdm.SimulationEngine.db import DB

@tool_spec(
    spec={
        'name': 'list_structures',
        'description': """ Lists all the structures.
        
        Makes a GET call to retrieve a list of all structures that the user has authorized
        for a given enterprise. The response typically includes a collection of structure objects. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_structures() -> list[dict]:
    """
    Lists all the structures.

    Makes a GET call to retrieve a list of all structures that the user has authorized
    for a given enterprise. The response typically includes a collection of structure objects.

    Returns:
        list[dict]: The response containing a list of structure objects. The list is empty if no structures are found.
            Each structure contains the following keys:
                - name (str): The internal name of the structure built from the project id.
                - traits (dict): The traits of the structure including the reference name of the structure.
    """
    
    # Get Structures
    structures = DB.get("environment", {}).get("sdm", {}).get("structures", [])
    return structures