import unittest
import copy
from typing import List, Optional
from pydantic import BaseModel, ValidationError

from ..SimulationEngine.db import DB
from ..SimulationEngine.models import FigmaDB as FigmaDB_Base, FigmaFile as FigmaFile_Base, DBDocumentNode, DBCanvasNode, Node
from common_utils.base_case import BaseTestCaseWithErrorHandler

# A known-good, minimal DB structure for validation.
SAMPLE_DB = {
    "files": [],
    "current_selection_node_ids": [],
    "projects": [],
    "current_file_key": None,
    "current_figma_channel": None
}

# Local models for complete validation, since the global ones are incomplete.
class Project(BaseModel):
    projectId: str
    name: str

class FigmaFile(FigmaFile_Base):
    projectId: Optional[str] = None

class FigmaDB(FigmaDB_Base):
    files: Optional[List[FigmaFile]] = []
    projects: Optional[List[Project]] = []
    current_file_key: Optional[str] = None
    current_figma_channel: Optional[str] = None


class TestDBValidation(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a clean, validated database before each test."""
        self.db_backup = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(SAMPLE_DB))

        # Create a test node structure using Pydantic models for validation
        self.test_node = Node(
            id="node_1",
            name="Test Node",
            type="RECTANGLE"
        )

        self.test_canvas = DBCanvasNode(
            id="canvas_1",
            name="Test Canvas",
            type="CANVAS",
            children=[self.test_node]
        )

        self.test_document = DBDocumentNode(
            id="doc_1",
            name="Test Document",
            type="DOCUMENT",
            children=[self.test_canvas]
        )
        
        self.test_file = FigmaFile(
            fileKey="file_1",
            name="Test File",
            document=self.test_document,
            components={},
            componentSets={},
            globalVars={},
            projectId="project_1"
        )

        self.test_project = Project(
            projectId="project_1",
            name="Test Project"
        )

        # Add the validated data to the database
        DB["files"].append(self.test_file.model_dump())
        DB["current_file_key"] = "file_1"
        DB["projects"].append(self.test_project.model_dump())


    def tearDown(self):
        """Restore the original database state after each test."""
        DB.clear()
        DB.update(self.db_backup)

    def test_db_module_harmony(self):
        """
        Test that the database schema is in harmony with the Pydantic model.
        """
        try:
            validated_db = FigmaDB(**DB)
            self.assertIsInstance(validated_db, FigmaDB)
        except ValidationError as e:
            self.fail(f"Database schema validation failed: {e}")

    def test_pydantic_validation_error_on_invalid_data(self):
        """
        Test that a Pydantic ValidationError is raised for invalid data.
        """
        invalid_project_data = {
            "projectId": "proj_2",
            "name": 12345 # Invalid type for name
        }

        with self.assertRaises(ValidationError):
            Project(**invalid_project_data)

    def test_setup_data_is_valid(self):
        """
        Test that the data added in setUp is valid and present in the DB.
        """
        self.assertEqual(len(DB["files"]), 1)
        self.assertEqual(DB["files"][0]["name"], "Test File")
        self.assertEqual(DB["files"][0]["projectId"], "project_1")
        self.assertEqual(DB["current_file_key"], "file_1")
        self.assertEqual(DB["files"][0]["document"]["children"][0]["children"][0]["name"], "Test Node")
        self.assertEqual(len(DB["projects"]), 1)
        self.assertEqual(DB["projects"][0]["name"], "Test Project")


if __name__ == "__main__":
    unittest.main()
