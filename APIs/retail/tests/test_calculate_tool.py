import pytest
import copy
from retail import calculate_tool
from retail.SimulationEngine.custom_errors import InvalidExpressionError, InvalidInputError
from retail.SimulationEngine import db


class TestCalculate:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_calculate_success(self):
        result = calculate_tool.calculate("2 + 2")
        assert result == "4.0"

    def test_calculate_invalid_chars(self):
        with pytest.raises(InvalidExpressionError, match="Error: invalid characters in expression"):
            calculate_tool.calculate("2 + a")

    def test_calculate_eval_error(self):
        with pytest.raises(InvalidExpressionError):
            calculate_tool.calculate("2 +")

    def test_calculate_input_validation(self):
        with pytest.raises(InvalidInputError):
            calculate_tool.calculate(123)
