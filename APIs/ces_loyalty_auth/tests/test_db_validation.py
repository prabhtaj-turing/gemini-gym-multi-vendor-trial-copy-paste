"""
Test cases for validating the database schema of the CES Loyalty Auth API.

This module ensures that the default database file (`CesLoyaltyAuthDefaultDB.json`)
conforms to the Pydantic models defined in the simulation engine.
"""

import unittest
import os
import json
from ces_loyalty_auth.SimulationEngine import db
from ces_loyalty_auth.SimulationEngine.models import (
    GetPreAuthenticationCallDataResponse,
)
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestDatabaseValidation(LoyaltyAuthBaseTestCase):
    """
    Test suite for validating the default database against Pydantic models.
    """

    def setUp(self):
        """
        Load the default database state for validation.
        """
        super().setUp()
        self.db_state = db.DB

    def test_default_db_state_validation(self):
        """
        Test that the default database state loaded from the JSON file
        conforms to the GetPreAuthenticationCallDataResponse model.
        """
        try:
            # The PROFILE_BEFORE_AUTH section should match the response model
            if "PROFILE_BEFORE_AUTH" in self.db_state:
                GetPreAuthenticationCallDataResponse(
                    **self.db_state["PROFILE_BEFORE_AUTH"]
                )
        except Exception as e:
            self.fail(f"Default DB state validation failed: {e}")


if __name__ == "__main__":
    unittest.main()
