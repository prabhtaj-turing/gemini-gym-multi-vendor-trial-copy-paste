import pytest
import copy
from retail import transfer_to_human_agents_tool
from retail.SimulationEngine.custom_errors import InvalidInputError
from retail.SimulationEngine import db


class TestTransferToHumanAgents:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_transfer_to_human_agents_success(self):
        summary = "This is a test summary."
        result = transfer_to_human_agents_tool.transfer_to_human_agents(summary)
        assert result == "Transfer successful"

    def test_transfer_to_human_agents_input_validation(self):
        with pytest.raises(InvalidInputError):
            transfer_to_human_agents_tool.transfer_to_human_agents(123)
