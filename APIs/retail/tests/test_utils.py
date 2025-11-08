import pytest
import copy
from retail.SimulationEngine import utils, db
from retail.SimulationEngine.custom_errors import InvalidInputError, DataConflictError

@pytest.fixture(autouse=True)
def setup_db():
    original_db = copy.deepcopy(db.DB)
    yield
    db.DB = original_db

class TestUserUtils:
    def test_get_user(self):
        user = utils.get_user("james_li_5688")
        assert user is not None
        assert user["name"]["first_name"] == "James"

    def test_get_user_not_found(self):
        user = utils.get_user("invalid_user")
        assert user is None

    def test_list_users(self):
        users = utils.list_users()
        assert len(users) > 0
        paginated_users = utils.list_users(limit=1, offset=1)
        assert len(paginated_users) == 1

    def test_list_users_no_limit(self):
        users = utils.list_users(offset=1)
        assert len(users) == len(db.DB["users"]) - 1

    def test_create_user(self):
        new_user_data = {
            "name": {"first_name": "Jane", "last_name": "Doe"},
            "address": {
                "address1": "456 Oak St",
                "city": "Othertown",
                "country": "USA",
                "state": "NY",
                "zip": "54321",
            },
            "email": "jane.doe@example.com",
            "payment_methods": {},
            "orders": [],
        }
        created_user = utils.create_user(new_user_data)
        assert created_user["name"]["first_name"] == "Jane"
        user_id = [user for user in db.DB["users"] if user.startswith("jane_doe_")][0]
        assert utils.get_user(user_id) is not None

    def test_create_user_with_invalid_data(self):
        new_user_data = {"name": {"first_name": "Jane"}}
        with pytest.raises(InvalidInputError):
            utils.create_user(new_user_data)

    def test_create_user_with_nonexistent_order(self):
        new_user_data = {
            "name": {"first_name": "Jane", "last_name": "Doe"},
            "address": {
                "address1": "456 Oak St",
                "city": "Othertown",
                "country": "USA",
                "state": "NY",
                "zip": "54321",
            },
            "email": "jane.doe@example.com",
            "payment_methods": {},
            "orders": ["nonexistent_order"],
        }
        with pytest.raises(DataConflictError):
            utils.create_user(new_user_data)

    def test_create_user_with_order_for_other_user(self):
        new_user_data = {
            "name": {"first_name": "Jane", "last_name": "Doe"},
            "address": {
                "address1": "456 Oak St",
                "city": "Othertown",
                "country": "USA",
                "state": "NY",
                "zip": "54321",
            },
            "email": "jane.doe@example.com",
            "payment_methods": {},
            "orders": ["#W2611340"],
        }
        with pytest.raises(DataConflictError):
            utils.create_user(new_user_data)

    def test_create_user_already_exists(self):
        user_id = "james_li_5688"
        new_user_data = {
            "name": {"first_name": "James", "last_name": "Li"},
            "address": {
                "address1": "215 River Road",
                "city": "New York",
                "country": "USA",
                "state": "NY",
                "zip": "10083",
            },
            "email": "james_li_5688@example.com",
            "payment_methods": {},
            "orders": [],
        }
        db.DB["users"][user_id] = new_user_data
        with pytest.raises(DataConflictError):
            utils.create_user(new_user_data)

    def test_update_user(self):
        update_data = {"name": {"first_name": "Jimmy", "last_name": "Li"}}
        updated_user = utils.update_user("james_li_5688", update_data)
        assert updated_user["name"]["first_name"] == "Jimmy"

    def test_update_user_not_found(self):
        update_data = {"name": {"first_name": "Jimmy", "last_name": "Li"}}
        updated_user = utils.update_user("invalid_user", update_data)
        assert updated_user is None

    def test_update_user_with_nonexistent_order(self):
        update_data = {"orders": ["nonexistent_order"]}
        with pytest.raises(DataConflictError):
            utils.update_user("james_li_5688", update_data)

    def test_update_user_with_order_for_other_user(self):
        update_data = {"orders": ["#W4817420"]}
        with pytest.raises(DataConflictError):
            utils.update_user("james_li_5688", update_data)

    def test_update_user_with_invalid_data(self):
        update_data = {"name": {"first_name": "Jimmy"}}
        with pytest.raises(InvalidInputError):
            utils.update_user("james_li_5688", update_data)

    def test_delete_user(self):
        assert utils.delete_user("james_li_5688") is True
        assert utils.get_user("james_li_5688") is None

    def test_delete_user_not_found(self):
        assert utils.delete_user("invalid_user") is False

class TestOrderUtils:
    def test_get_order(self):
        order = utils.get_order("#W2611340")
        assert order is not None
        assert order["user_id"] == "james_li_5688"

    def test_get_order_not_found(self):
        order = utils.get_order("invalid_order")
        assert order is None

    def test_list_orders(self):
        orders = utils.list_orders()
        assert len(orders) > 0
        paginated_orders = utils.list_orders(limit=1, offset=1)
        assert len(paginated_orders) == 1

    def test_list_orders_no_limit(self):
        orders = utils.list_orders(offset=1)
        assert len(orders) == len(db.DB["orders"]) - 1

    def test_create_order(self):
        new_order_data = {
            "user_id": "james_li_5688",
            "address": {
                "address1": "215 River Road",
                "city": "New York",
                "country": "USA",
                "state": "NY",
                "zip": "10083",
            },
            "items": [],
            "fulfillments": [],
            "status": "pending",
            "payment_history": [],
        }
        created_order = utils.create_order(new_order_data)
        assert created_order["user_id"] == "james_li_5688"
        assert utils.get_order(created_order["order_id"]) is not None

    def test_create_order_with_invalid_user(self):
        new_order_data = {
            "user_id": "invalid_user",
            "address": {
                "address1": "215 River Road",
                "city": "New York",
                "country": "USA",
                "state": "NY",
                "zip": "10083",
            },
            "items": [],
            "fulfillments": [],
            "status": "pending",
            "payment_history": [],
        }
        with pytest.raises(DataConflictError):
            utils.create_order(new_order_data)

    def test_create_order_with_payment_exceeding_total(self):
        new_order_data = {
            "user_id": "james_li_5688",
            "address": {
                "address1": "215 River Road",
                "city": "New York",
                "country": "USA",
                "state": "NY",
                "zip": "10083",
            },
            "items": [],
            "fulfillments": [],
            "status": "pending",
            "payment_history": [{"transaction_type": "payment", "amount": 1.0, "payment_method_id": "gift_card_1725971"}],
        }
        with pytest.raises(DataConflictError):
            utils.create_order(new_order_data)

    def test_create_order_with_invalid_product(self):
        new_order_data = {
            "user_id": "james_li_5688",
            "address": {
                "address1": "215 River Road",
                "city": "New York",
                "country": "USA",
                "state": "NY",
                "zip": "10083",
            },
            "items": [{"product_id": "invalid_product", "item_id": "invalid_item", "name": "invalid", "price": 0.0, "options": {}}],
            "fulfillments": [],
            "status": "pending",
            "payment_history": [],
        }
        with pytest.raises(DataConflictError):
            utils.create_order(new_order_data)

    def test_create_order_with_invalid_item(self):
        new_order_data = {
            "user_id": "james_li_5688",
            "address": {
                "address1": "215 River Road",
                "city": "New York",
                "country": "USA",
                "state": "NY",
                "zip": "10083",
            },
            "items": [{"product_id": "8310926033", "item_id": "invalid_item", "name": "invalid", "price": 0.0, "options": {}}],
            "fulfillments": [],
            "status": "pending",
            "payment_history": [],
        }
        with pytest.raises(DataConflictError):
            utils.create_order(new_order_data)

    def test_create_order_with_invalid_data(self):
        new_order_data = {"user_id": 123}
        with pytest.raises(InvalidInputError):
            utils.create_order(new_order_data)

    def test_update_order_with_nonexistent_user(self):
        order_id = "#W2611340"
        update_data = {"user_id": "non_existent_user"}
        with pytest.raises(DataConflictError):
            utils.update_order(order_id, update_data)

    def test_create_order_already_exists(self):
        new_order_data = {
            "order_id": "#W2611340",
            "user_id": "james_li_5688",
            "address": {
                "address1": "215 River Road",
                "city": "New York",
                "country": "USA",
                "state": "NY",
                "zip": "10083",
            },
            "items": [],
            "fulfillments": [],
            "status": "pending",
            "payment_history": [],
        }
        with pytest.raises(DataConflictError):
            utils.create_order(new_order_data)

    def test_update_order_with_invalid_item(self):
        update_data = {"items": [{"product_id": "invalid_product", "item_id": "invalid_item", "name": "invalid", "price": 0.0, "options": {}}]}
        with pytest.raises(DataConflictError):
            utils.update_order("#W2611340", update_data)

    def test_update_order_with_item_not_in_product_variants(self):
        order_id = "#W2611340"
        original_order = utils.get_order(order_id)
        
        # Ensure the original item is valid
        original_item = original_order["items"][0]
        assert original_item["item_id"] in db.DB["products"][original_item["product_id"]]["variants"]

        # Create an item that is not a valid variant
        invalid_item = original_item.copy()
        invalid_item["item_id"] = "invalid_variant_id"
        
        update_data = {"items": [invalid_item], "payment_history": []}
        
        with pytest.raises(DataConflictError, match=f"Item {invalid_item['item_id']} not found in product {original_item['product_id']}."):
            utils.update_order(order_id, update_data)

    def test_update_order_with_payment_exceeding_total(self):
        update_data = {"payment_history": [{"transaction_type": "payment", "amount": 10000.0, "payment_method_id": "gift_card_1725971"}]}
        with pytest.raises(DataConflictError):
            utils.update_order("#W2611340", update_data)

    def test_update_order(self):
        update_data = {"status": "shipped"}
        updated_order = utils.update_order("#W2611340", update_data)
        assert updated_order["status"] == "shipped"

    def test_update_order_not_found(self):
        update_data = {"status": "shipped"}
        updated_order = utils.update_order("invalid_order", update_data)
        assert updated_order is None

    def test_update_order_with_invalid_data(self):
        update_data = {"user_id": 123}
        with pytest.raises(InvalidInputError):
            utils.update_order("#W2611340", update_data)

    def test_delete_order(self):
        order_id = "#W2611340"
        user_id = utils.get_order(order_id)["user_id"]
        assert order_id in utils.get_user(user_id)["orders"]
        assert utils.delete_order(order_id) is True
        assert utils.get_order(order_id) is None
        assert order_id not in utils.get_user(user_id)["orders"]

    def test_delete_order_not_found(self):
        assert utils.delete_order("invalid_order") is False

    def test_delete_order_user_not_found(self):
        order_id = "#W2611340"
        user_id = utils.get_order(order_id)["user_id"]
        del db.DB["users"][user_id]
        assert utils.delete_order(order_id) is True
        assert utils.get_order(order_id) is None
    def test_update_order_with_nonexistent_product(self):
        # Get a valid order to update
        order_id = "#W2611340"
        original_order = utils.get_order(order_id)
        assert original_order is not None
        # Copy the first item and set its product_id to a non-existent one
        invalid_item = original_order["items"][0].copy()
        invalid_item["product_id"] = "nonexistent_product_id"
        update_data = {"items": [invalid_item], "payment_history": []}
        with pytest.raises(DataConflictError, match="Product nonexistent_product_id not found."):
            utils.update_order(order_id, update_data)


class TestProductUtils:
    def test_get_product(self):
        product = utils.get_product("8310926033")
        assert product is not None
        assert product["name"] == "Water Bottle"

    def test_get_product_not_found(self):
        product = utils.get_product("invalid_product")
        assert product is None

    def test_list_products(self):
        products = utils.list_products()
        assert len(products) > 0
        paginated_products = utils.list_products(limit=1, offset=1)
        assert len(paginated_products) == 1

    def test_list_products_no_limit(self):
        products = utils.list_products(offset=1)
        assert len(products) == len(db.DB["products"]) - 1

    def test_create_product(self):
        new_product_data = {
            "name": "New Product",
            "variants": {},
        }
        created_product = utils.create_product(new_product_data)
        assert created_product["name"] == "New Product"
        assert utils.get_product(created_product["product_id"]) is not None

    def test_create_product_with_invalid_data(self):
        new_product_data = {"name": 123}
        with pytest.raises(InvalidInputError):
            utils.create_product(new_product_data)

    def test_create_product_already_exists(self):
        new_product_data = {
            "product_id": "8310926033",
            "name": "Water Bottle",
            "variants": {},
        }
        with pytest.raises(DataConflictError):
            utils.create_product(new_product_data)

    def test_update_product(self):
        update_data = {"name": "Updated Product"}
        updated_product = utils.update_product("8310926033", update_data)
        assert updated_product["name"] == "Updated Product"

    def test_update_product_not_found(self):
        update_data = {"name": "Updated Product"}
        updated_product = utils.update_product("invalid_product", update_data)
        assert updated_product is None

    def test_update_product_with_invalid_data(self):
        update_data = {"name": 123}
        with pytest.raises(InvalidInputError):
            utils.update_product("8310926033", update_data)

    def test_delete_product(self):
        assert utils.delete_product("8310926033") is True
        assert utils.get_product("8310926033") is None

    def test_delete_product_not_found(self):
        assert utils.delete_product("invalid_product") is False
