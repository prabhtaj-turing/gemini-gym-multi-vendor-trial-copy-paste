import copy

from azure.cosmos import azmcp_cosmos_account_create
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import DB
from ..SimulationEngine import custom_errors


class TestAzmcpCosmosAccountCreate(BaseTestCaseWithErrorHandler):
    """Test cases for azmcp_cosmos_account_create function."""

    def setUp(self):
        """Set up test data before each test."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # Test data setup
        self.s1_guid = '00000000-0000-0000-0000-000000000001'
        self.s1_display_name = 'Development Subscription'
        self.rg1_name = 'rg-compute-east'
        self.rg2_name = 'rg-data-west'
        self.acc1_name = 'existing-cosmos-account'

        # Main subscription for most tests
        self.sub1_data = {
            'id': f'/subscriptions/{self.s1_guid}',
            'subscriptionId': self.s1_guid,
            'displayName': self.s1_display_name,
            'state': 'Enabled',
            'tenantId': 'tenant1-id',
            'resource_groups': [
                {
                    'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}',
                    'name': self.rg1_name,
                    'location': 'eastus',
                    'subscription_id': self.s1_guid,
                    'cosmos_db_accounts': [
                        {
                            'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}/providers/Microsoft.DocumentDB/databaseAccounts/{self.acc1_name}',
                            'name': self.acc1_name,
                            'location': 'eastus',
                            'kind': 'GlobalDocumentDB',
                            'resource_group_name': self.rg1_name,
                            'subscription_id': self.s1_guid,
                            'databases': []
                        }
                    ]
                },
                {
                    'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg2_name}',
                    'name': self.rg2_name,
                    'location': 'westus2',
                    'subscription_id': self.s1_guid,
                    'cosmos_db_accounts': []
                }
            ]
        }
        DB['subscriptions'] = [self.sub1_data]

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_create_cosmos_account_success(self):
        """Test successful creation of a Cosmos DB account."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="newcosmosdb01",
            location="eastus",
            kind="GlobalDocumentDB"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "newcosmosdb01")
        self.assertEqual(result["location"], "eastus")
        self.assertEqual(result["kind"], "GlobalDocumentDB")
        self.assertEqual(result["resource_group_name"], self.rg1_name)
        self.assertEqual(result["subscription_id"], self.s1_guid)
        self.assertEqual(result["provisioning_state"], "Succeeded")
        self.assertEqual(result["databases"], [])
        self.assertIn("id", result)
        expected_id_pattern = f"/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}/providers/Microsoft.DocumentDB/databaseAccounts/newcosmosdb01"
        self.assertEqual(result["id"], expected_id_pattern)

    def test_create_cosmos_account_with_subscription_name(self):
        """Test creation using subscription display name instead of ID."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_display_name,
            resource_group=self.rg1_name,
            account_name="newcosmosdb02",
            location="eastus"
        )

        self.assertEqual(result["name"], "newcosmosdb02")
        self.assertEqual(result["subscription_id"], self.s1_guid)

    def test_create_cosmos_account_mongodb_kind(self):
        """Test creation of MongoDB type Cosmos DB account."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="newmongodb01",
            location="westus2",
            kind="MongoDB"
        )

        self.assertEqual(result["name"], "newmongodb01")
        self.assertEqual(result["kind"], "MongoDB")
        self.assertEqual(result["location"], "westus2")

    def test_create_cosmos_account_parse_kind(self):
        """Test creation of Parse type Cosmos DB account."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="newparse01",
            location="northeurope",
            kind="Parse"
        )

        self.assertEqual(result["name"], "newparse01")
        self.assertEqual(result["kind"], "Parse")
        self.assertEqual(result["location"], "northeurope")

    def test_create_cosmos_account_default_kind(self):
        """Test that GlobalDocumentDB is used as default kind when not specified."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="defaultkindaccount",
            location="eastus"
        )

        self.assertEqual(result["kind"], "GlobalDocumentDB")

    def test_create_cosmos_account_with_all_optional_params_success(self):
        """Test creation with all optional parameters (should not affect the result)."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="optionalparamsaccount",
            location="eastus",
            kind="GlobalDocumentDB",
            auth_method="credential",
            tenant="test-tenant",
            retry_max_retries="3",
            retry_delay="1",
            retry_max_delay="30",
            retry_mode="exponential",
            retry_network_timeout="60"
        )

        self.assertEqual(result["name"], "optionalparamsaccount")
        self.assertEqual(result["kind"], "GlobalDocumentDB")
        self.assertEqual(result["location"], "eastus")

    def test_create_cosmos_account_verifies_database_list_empty(self):
        """Test that newly created account has empty databases list."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="emptydatabasesaccount",
            location="eastus"
        )

        self.assertEqual(result["databases"], [])
        self.assertIsInstance(result["databases"], list)

    def test_create_cosmos_account_different_resource_groups_same_name(self):
        """Test that accounts with same name can exist in different resource groups."""
        # Create account in first resource group
        result1 = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="samenameaccount",
            location="eastus"
        )

        # Create account with same name in different resource group
        result2 = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg2_name,
            account_name="samenameaccount",
            location="westus2"
        )

        self.assertEqual(result1["name"], "samenameaccount")
        self.assertEqual(result1["resource_group_name"], self.rg1_name)
        self.assertEqual(result2["name"], "samenameaccount")
        self.assertEqual(result2["resource_group_name"], self.rg2_name)

    def test_missing_subscription_raises_validation_error(self):
        """Test error when subscription is missing."""
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed",
            subscription="",
            resource_group=self.rg1_name,
            account_name="testaccount",
            location="eastus"
        )

    def test_missing_resource_group_raises_validation_error(self):
        """Test error when resource group is missing."""
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed",
            subscription=self.s1_guid,
            resource_group="",
            account_name="testaccount",
            location="eastus"
        )

    def test_missing_account_name_raises_validation_error(self):
        """Test error when account name is missing."""
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed",
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="",
            location="eastus"
        )

    def test_missing_location_raises_validation_error(self):
        """Test error when location is missing."""
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed",
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="testaccount",
            location=""
        )

    def test_invalid_kind_raises_validation_error(self):
        """Test error when kind is invalid."""
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed",
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="testaccount",
            location="eastus",
            kind="InvalidKind"
        )

    def test_subscription_not_found_raises_subscriptionnotfounderror(self):
        """Test error when subscription does not exist."""
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="The specified Azure subscription was not found or is not accessible.",
            subscription="nonexistent-subscription",
            resource_group=self.rg1_name,
            account_name="testaccount",
            location="eastus"
        )

    def test_resource_group_not_found_raises_resource_not_found_error(self):
        """Test error when resource group does not exist."""
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Resource group 'nonexistent-rg' not found in subscription '{self.s1_guid}'.",
            subscription=self.s1_guid,
            resource_group="nonexistent-rg",
            account_name="testaccount",
            location="eastus"
        )

    def test_account_already_exists_raises_conflict_error(self):
        """Test error when Cosmos DB account already exists."""
        # First create an account
        azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="duplicateaccount",
            location="eastus"
        )

        # Try to create another account with the same name
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ConflictError,
            expected_message=f"Cosmos DB account 'duplicateaccount' already exists in resource group '{self.rg1_name}'.",
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="duplicateaccount",
            location="eastus"
        )

    def test_subscription_with_no_resource_groups(self):
        """Test error when subscription has no resource groups."""
        # Create a subscription with no resource groups
        sub_no_rg = {
            'id': f'/subscriptions/00000000-0000-0000-0000-000000000002',
            'subscriptionId': '00000000-0000-0000-0000-000000000002',
            'displayName': 'No Resource Groups Subscription',
            'state': 'Enabled',
            'tenantId': 'tenant2-id',
            'resource_groups': []
        }
        DB['subscriptions'].append(sub_no_rg)

        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Resource group 'test-rg' not found in subscription '00000000-0000-0000-0000-000000000002'.",
            subscription='00000000-0000-0000-0000-000000000002',
            resource_group="test-rg",
            account_name="testaccount",
            location="eastus"
        )

    def test_subscription_with_missing_resource_groups_key(self):
        """Test error when subscription data is missing resource_groups key."""
        # Create a subscription without resource_groups key
        sub_missing_rg = {
            'id': f'/subscriptions/00000000-0000-0000-0000-000000000003',
            'subscriptionId': '00000000-0000-0000-0000-000000000003',
            'displayName': 'Missing Resource Groups Key Subscription',
            'state': 'Enabled',
            'tenantId': 'tenant3-id'
            # Missing resource_groups key
        }
        DB['subscriptions'].append(sub_missing_rg)

        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_create,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Resource group 'test-rg' not found in subscription '00000000-0000-0000-0000-000000000003'.",
            subscription='00000000-0000-0000-0000-000000000003',
            resource_group="test-rg",
            account_name="testaccount",
            location="eastus"
        )

    def test_resource_group_with_missing_cosmos_accounts_key(self):
        """Test that resource group without cosmos_accounts key works correctly."""
        # Create a resource group without cosmos_accounts key
        rg_no_cosmos = {
            'id': f'/subscriptions/{self.s1_guid}/resourceGroups/rg-no-cosmos',
            'name': 'rg-no-cosmos',
            'location': 'eastus',
            'subscription_id': self.s1_guid
            # Missing cosmos_db_accounts key
        }
        DB['subscriptions'][0]['resource_groups'].append(rg_no_cosmos)

        # Should work correctly (cosmos_accounts will be created as empty list)
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group="rg-no-cosmos",
            account_name="newaccount",
            location="eastus"
        )

        self.assertEqual(result["name"], "newaccount")
        self.assertEqual(result["resource_group_name"], "rg-no-cosmos")

    def test_arm_id_format_correctness(self):
        """Test that the generated ARM ID follows the correct format."""
        result = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="armidtestaccount",
            location="eastus"
        )

        expected_id_pattern = f"/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}/providers/Microsoft.DocumentDB/databaseAccounts/armidtestaccount"
        self.assertEqual(result["id"], expected_id_pattern)

    def test_optional_parameters_do_not_affect_outcome(self):
        """Test that optional parameters don't affect the creation outcome."""
        # Create account without optional parameters
        result1 = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="testaccount1",
            location="eastus"
        )

        # Create account with all optional parameters
        result2 = azmcp_cosmos_account_create(
            subscription=self.s1_guid,
            resource_group=self.rg1_name,
            account_name="testaccount2",
            location="eastus",
            kind="GlobalDocumentDB",
            auth_method="credential",
            tenant="test-tenant",
            retry_max_retries="3",
            retry_delay="1",
            retry_max_delay="30",
            retry_mode="exponential",
            retry_network_timeout="60"
        )

        # Both should have the same structure and default values
        self.assertEqual(result1["kind"], result2["kind"])
        self.assertEqual(result1["provisioning_state"], result2["provisioning_state"])
        self.assertEqual(result1["databases"], result2["databases"])
        self.assertIn("id", result1)
        self.assertIn("id", result2)
