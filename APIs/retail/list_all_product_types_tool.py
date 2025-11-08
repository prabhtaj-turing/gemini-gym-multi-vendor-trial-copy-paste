from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    ListAllProductTypesOutput,
)


@tool_spec(
    spec={
        'name': 'list_all_product_types',
        'description': """ List the name and product id of all product types.
        
        Each product type has a variety of different items with unique item ids and
        options. There are only 50 product types in the store. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_all_product_types() -> Dict[str, Any]:
    """List the name and product id of all product types.

    Each product type has a variety of different items with unique item ids and
    options. There are only 50 product types in the store.

    Returns:
        Dict[str, Any]: A dictionary of product names to product IDs.
            - products (Dict[str, str]): A dictionary where keys are product names and values are product IDs.
    """
    products = db.DB["products"]
    product_dict = {
        product["name"]: product["product_id"] for product in products.values()
    }
    product_dict = dict(sorted(product_dict.items()))
    return ListAllProductTypesOutput(products=product_dict).model_dump(mode="json")
