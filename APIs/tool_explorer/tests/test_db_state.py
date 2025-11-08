import unittest
import os
import json
import shutil
from ..SimulationEngine import db
from ..SimulationEngine.models import ToolExplorerDB

class TestDBState(unittest.TestCase):
    """Test suite for database state management."""

    def setUp(self):
        """Set up a test state file."""
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        self.state_file = os.path.join(self.test_dir, "state.json")
        db.reset_db()

    def tearDown(self):
        """Clean up the test state file."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_db_schema_validation(self):
        """Test that the default DB schema is valid."""
        try:
            ToolExplorerDB(**db.DB)
        except Exception as e:
            self.fail(f"Default DB schema validation failed: {e}")

    def test_save_and_load_state(self):
        """Test saving and loading the database state."""
        original_services = db.DB['services'].copy()
        
        # Use a valid Tool object for testing
        db.DB["services"] = {
            "test_service": {
                "tool": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "param1": {
                                "type": "STRING",
                                "description": "A test parameter"
                            }
                        },
                        "required": ["param1"]
                    }
                }
            }
        }
        db.save_state(self.state_file)
        
        db.reset_db()
        self.assertEqual(db.DB["services"], original_services)
        
        db.load_state(self.state_file)
        self.assertEqual(db.DB["services"], {
            "test_service": {
                "tool": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "param1": {
                                "type": "STRING",
                                "description": "A test parameter"
                            }
                        },
                        "required": ["param1"]
                    }
                }
            }
        })

        # Validate the loaded state against the schema
        try:
            ToolExplorerDB(**db.DB)
        except Exception as e:
            self.fail(f"Loaded DB state schema validation failed: {e}")

    def test_load_nonexistent_state(self):
        """Test loading a non-existent state file."""
        original_services = db.DB['services'].copy()
        db.load_state("nonexistent.json")
        self.assertEqual(db.DB["services"], original_services)

    def test_load_invalid_json(self):
        """Test loading a state file with invalid JSON."""
        original_services = db.DB['services'].copy()
        invalid_json_file = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_json_file, "w") as f:
            f.write("{'invalid': json}")
        
        db.load_state(invalid_json_file)
        self.assertEqual(db.DB["services"], original_services)

if __name__ == '__main__':
    unittest.main()
