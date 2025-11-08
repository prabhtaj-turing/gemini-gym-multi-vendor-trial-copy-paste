import unittest
import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import create_extension_in_db
from ..database import list_extensions

class TestCreateExtension(BaseTestCaseWithErrorHandler):
    """
    Test suite for the create_extension function.
    """

    PROJECT_ID_WITH_EXTENSIONS = "proj_valid_with_extensions"
    PROJECT_ID_NO_EXTENSIONS_EMPTY_LIST = "proj_valid_no_extensions_empty_list"
    PROJECT_ID_NO_EXTENSIONS_MISSING_KEY = "proj_valid_no_extensions_missing_key"
    PROJECT_ID_FOR_DB_ERROR_SIM = "proj_for_db_error_sim" 
    NON_EXISTENT_PROJECT_ID = "proj_invalid_non_existent"

    def setUp(self):
        """
        Set up the test environment before each test.
        This involves creating a deep copy of the original DB state,
        clearing the global DB, and populating it with test-specific data.
        """

        
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()  

        DB["projects"] = [
            {
                "id": self.PROJECT_ID_WITH_EXTENSIONS,
                "name": "Project With Extensions",
                "organization_id": "org_test_1",    
                "region": "us-east-1",
                "status": "ACTIVE_HEALTHY",
                "created_at": "2023-01-01T10:00:00Z",
                "version": "15.1.0.114"
            },
            {
                "id": self.PROJECT_ID_NO_EXTENSIONS_EMPTY_LIST,
                "name": "Project No Extensions (Empty List)",
                "organization_id": "org_test_1",
                "region": "eu-west-2",
                "status": "ACTIVE_HEALTHY",
                "created_at": "2023-01-02T11:00:00Z",
                "version": "15.1.0.114"
            },
            {
                "id": self.PROJECT_ID_NO_EXTENSIONS_MISSING_KEY,
                "name": "Project No Extensions (Missing Key)",
                "organization_id": "org_test_2",
                "region": "ap-southeast-1",
                "status": "ACTIVE_HEALTHY",
                "created_at": "2023-01-03T12:00:00Z",
                "version": "15.1.0.114"
            },
            {
                "id": self.PROJECT_ID_NO_EXTENSIONS_MISSING_KEY,
                "name": "Project No Extensions (Missing Key)",
                "organization_id": "org_test_2",
                "region": "ap-southeast-1",
                "status": "ACTIVE_HEALTHY",
                "created_at": "2023-01-03T12:00:00Z",
                "version": "15.1.0.114"
            },
        ]
        DB["extensions"] = {
            self.PROJECT_ID_WITH_EXTENSIONS: [
                {
                    "name": "uuid-ossp",
                    "schema": "public", 
                    "version": "1.1",
                    "description": "generate universally unique identifiers (UUIDs)"
                },
                {
                    "name": "pg_stat_statements",
                    "schema": "public",
                    "version": "1.9",
                    "description": "track execution statistics of all SQL statements executed"
                }
            ],
            self.PROJECT_ID_NO_EXTENSIONS_EMPTY_LIST: []
        }

    def test_create_extension_success(self):
        """
        Test that the create_extension function returns True when the extension is created successfully.
        """
        self.assertTrue(create_extension_in_db(DB, self.PROJECT_ID_WITH_EXTENSIONS, "uuid-ossp", "1.1", "public", "generate universally unique identifiers (UUIDs)"))
        extensions = list_extensions(project_id=self.PROJECT_ID_WITH_EXTENSIONS)
        self.assertIsInstance(extensions, list)
        self.assertEqual(len(extensions), 3)

    def test_create_extension_project_not_found(self):
        """
        Test that the create_extension function returns False when the project is not found.
        """
        self.assertRaises(KeyError, create_extension_in_db, DB, "invalid_project_id", "uuid-ossp", "1.1", "public", "generate universally unique identifiers (UUIDs)")
    
    
    def test_create_extension_invalid_extension_name(self):
        """
        Test that the create_extension function returns False when the extension name is not a string.
        """
        self.assertRaises(TypeError, create_extension_in_db, DB, self.PROJECT_ID_WITH_EXTENSIONS, 123, "1.1", "public", "generate universally unique identifiers (UUIDs)")
    
    def test_create_extension_invalid_extension_version(self):
        """
        Test that the create_extension function returns False when the extension version is not a string.
        """ 
        self.assertRaises(TypeError, create_extension_in_db, DB, self.PROJECT_ID_WITH_EXTENSIONS, "uuid-ossp", 123, "public", "generate universally unique identifiers (UUIDs)")
    
    def test_create_extension_invalid_extension_schema(self):
        """
        Test that the create_extension function returns False when the extension schema is not a string.
        """
        self.assertRaises(TypeError, create_extension_in_db, DB, self.PROJECT_ID_WITH_EXTENSIONS, "uuid-ossp", "1.1", 123, "generate universally unique identifiers (UUIDs)")   
    
    def test_create_extension_invalid_extension_description(self):
        """
        Test that the create_extension function returns False when the extension description is not a string.
        """
        self.assertRaises(TypeError, create_extension_in_db, DB, self.PROJECT_ID_WITH_EXTENSIONS, "uuid-ossp", "1.1", "public", 123)        

    def test_create_extension_missing_project_id(self):
        """
        Test that the create_extension function returns False when the project id is missing.
        """
        DB["extensions"] = {}
        self.assertRaises(KeyError, create_extension_in_db, DB, self.PROJECT_ID_WITH_EXTENSIONS, "uuid-ossp", "1.1", "public", "generate universally unique identifiers (UUIDs)")

    def test_create_extension_missing_extensions_key(self):
        """
        Test that the create_extension function returns False when the extensions key is missing.
        """
        DB = {}
        self.assertRaises(KeyError, create_extension_in_db, DB, self.PROJECT_ID_WITH_EXTENSIONS, "uuid-ossp", "1.1", "public", "generate universally unique identifiers (UUIDs)")


if __name__ == '__main__':
    unittest.main()