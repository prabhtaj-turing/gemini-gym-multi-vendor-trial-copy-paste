import pytest
import copy
from retail import think_tool
from retail.SimulationEngine.custom_errors import InvalidInputError
from retail.SimulationEngine import db


class TestThink:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_think_success(self):
        thought = "This is a test thought."
        result = think_tool.think(thought)
        assert result == ""

    def test_think_input_validation(self):
        with pytest.raises(InvalidInputError):
            think_tool.think(123)
