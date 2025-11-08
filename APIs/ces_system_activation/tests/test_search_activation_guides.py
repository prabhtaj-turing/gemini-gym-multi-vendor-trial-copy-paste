import unittest
from unittest.mock import patch
import sys
import os
import json
from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from APIs.ces_system_activation.ces_system_activation import search_activation_guides
from APIs.ces_system_activation.SimulationEngine.custom_errors import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestSearchActivationGuides(BaseTestCaseWithErrorHandler):

    def test_search_activation_guides_empty_query(self):
        
        self.assert_error_behavior(
            search_activation_guides,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )
        

if __name__ == '__main__':
    unittest.main()