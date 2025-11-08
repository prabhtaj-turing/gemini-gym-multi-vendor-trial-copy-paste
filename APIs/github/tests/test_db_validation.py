import unittest
from pydantic import ValidationError
from ..SimulationEngine.db import DB
from ..SimulationEngine.models import GitHubDB


class TestDatabaseValidation(unittest.TestCase):
    """
    Test suite for validating the GitHub in-memory database against Pydantic models.
    This test ensures that the default database state loaded from GithubDefaultDB.json
    at startup conforms to the strict GitHubDB schema.
    """

    def test_default_db_schema_compliance(self):
        """
        Validates the global DB object against the GitHubDB Pydantic model.
        """
        try:
            GitHubDB.model_validate(DB)
        except ValidationError as e:
            # The test fails if a ValidationError is raised, providing the details.
            self.fail(f"Default DB loaded from GithubDefaultDB.json failed validation:\n{e}")

if __name__ == '__main__':
    unittest.main()


