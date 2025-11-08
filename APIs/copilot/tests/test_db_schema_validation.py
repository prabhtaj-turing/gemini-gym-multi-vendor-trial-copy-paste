import json
import pytest
from pydantic import ValidationError
from APIs.copilot.SimulationEngine.db_models import CopilotDB
import os


def test_copilot_default_db_schema():
    """
    Validates that the default Copilot database (CopilotDefaultDB.json)
    conforms to the CopilotDB Pydantic model.
    """
    # Construct the path to the JSON file relative to this test file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    json_path = os.path.join(project_root, 'DBs', 'CopilotDefaultDB.json')

    try:
        with open(json_path, 'r') as f:
            db_data = json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Default database file not found at: {json_path}")
    except json.JSONDecodeError:
        pytest.fail("Failed to decode JSON from the default database file.")

    try:
        CopilotDB.model_validate(db_data)
    except ValidationError as e:
        pytest.fail(f"CopilotDefaultDB.json does not match the CopilotDB schema:\n{e}")
