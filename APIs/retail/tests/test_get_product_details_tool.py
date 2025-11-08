import pytest
import copy
from retail import get_product_details_tool
from retail.SimulationEngine.custom_errors import ProductNotFoundError, InvalidInputError
from retail.SimulationEngine import db


class TestGetProductDetails:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_get_product_details_success(self):
        product_id = "8310926033"
        result = get_product_details_tool.get_product_details(product_id)
        assert result["product_id"] == product_id

    def test_get_product_details_not_found(self):
        with pytest.raises(ProductNotFoundError, match="Error: product not found"):
            get_product_details_tool.get_product_details("1234567890")

    def test_get_product_details_input_validation(self):
        with pytest.raises(InvalidInputError):
            get_product_details_tool.get_product_details(123)
