from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import ProductNotFoundError, InvalidInputError
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    GetProductDetailsInput,
    Product,
)


@tool_spec(
    spec={
        'name': 'get_product_details',
        'description': 'Get the inventory details of a product.',
        'parameters': {
            'type': 'object',
            'properties': {
                'product_id': {
                    'type': 'string',
                    'description': "The product id, such as '6086499569'. Be careful the product id is different from the item id."
                }
            },
            'required': [
                'product_id'
            ]
        }
    }
)
def get_product_details(product_id: str) -> Dict[str, Any]:
    """Get the inventory details of a product.

    Args:
        product_id (str): The product id, such as '6086499569'. Be careful the product id is different from the item id.

    Returns:
        Dict[str, Any]: A dictionary representing the product with the following fields:
            - name (str): The name of the product.
            - product_id (str): The ID of the product.
            - variants (Dict[str, Dict[str, Any]]): A dictionary of variants for the product.
                - item_id (str): The ID of the item.
                - options (Dict[str, str]): The options for the item.
                - available (bool): Whether the item is available.
                - price (float): The price of the item.

    Raises:
        ProductNotFoundError: If the product is not found.
        InvalidInputError: If the input is invalid.
    """
    try:
        GetProductDetailsInput(product_id=product_id)
    except ValidationError as e:
        raise InvalidInputError(e)

    products = db.DB["products"]
    if product_id in products:
        return Product(**products[product_id]).model_dump(mode="json")
    raise ProductNotFoundError("Error: product not found")
