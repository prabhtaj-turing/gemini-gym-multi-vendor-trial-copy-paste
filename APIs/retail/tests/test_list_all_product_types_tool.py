import pytest
import copy
from retail import list_all_product_types_tool
from retail.SimulationEngine import db


class TestListAllProductTypes:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_list_all_product_types(self):
        result = list_all_product_types_tool.list_all_product_types()
        assert "products" in result
        assert isinstance(result["products"], dict)
        assert len(result["products"]) > 0
