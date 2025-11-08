
import unittest
import sys
import os
from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from APIs.ces_system_activation.SimulationEngine.models import FlagTechnicianVisitIssueInput
from APIs.ces_system_activation.SimulationEngine.custom_errors import ValidationError as CustomValidationError

class TestPydanticValidators(unittest.TestCase):
    def test_flag_technician_visit_issue_input_validator_raises_pydantic_error(self):
        with self.assertRaises(PydanticValidationError):
            FlagTechnicianVisitIssueInput(
                accountId=" ",
                customerReportedFailure=True,
                issueSummary="summary",
                orderId="order",
                requestedFollowUpAction="action",
                visitId="visit"
            )
