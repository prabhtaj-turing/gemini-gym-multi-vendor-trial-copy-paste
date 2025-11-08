import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import DB
from .. import azmcp_cosmos_database_list
from .. import azmcp_cosmos_database_container_list
from .. import azmcp_cosmos_account_list
from ..SimulationEngine import custom_errors

class TestAzmcpCosmosDatabaseList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.s1_guid = '00000000-0000-0000-0000-000000000001'
        self.s1_display_name = 'Test Subscription 1 Display Name'
        self.rg1_name = 'rg1'
        self.acc1_name = 'cosmos-acc-1'
        self.db1_name = 'db1'
        self.db2_name = 'db2'
        self.acc_empty_name = 'cosmos-acc-empty'
        self.db1_id = f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}/providers/Microsoft.DocumentDB/databaseAccounts/{self.acc1_name}/sqlDatabases/{self.db1_name}'
        self.db2_id = f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}/providers/Microsoft.DocumentDB/databaseAccounts/{self.acc1_name}/sqlDatabases/{self.db2_name}'
        
        # Main subscription for most tests
        self.sub1_data = {
            'id': f'/subscriptions/{self.s1_guid}', 
            'subscriptionId': self.s1_guid, 
            'displayName': self.s1_display_name, # Added display name
            'state': 'Enabled', 
            'tenantId': 'tenant1-id', 
            'resource_groups': [{
                'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}', 
                'name': self.rg1_name, 
                'location': 'eastus', 
                'subscription_id': self.s1_guid, 
                'cosmos_db_accounts': [{
                    'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}/providers/Microsoft.DocumentDB/databaseAccounts/{self.acc1_name}', 
                    'name': self.acc1_name, 
                    'location': 'eastus', 
                    'kind': 'GlobalDocumentDB', 
                    'resource_group_name': self.rg1_name, 
                    'subscription_id': self.s1_guid, 
                    'databases': [
                        {'name': self.db1_name, 'id': self.db1_id, 'account_name': self.acc1_name}, 
                        {'name': self.db2_name, 'id': self.db2_id, 'account_name': self.acc1_name}
                    ]
                }, {
                    'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}/providers/Microsoft.DocumentDB/databaseAccounts/{self.acc_empty_name}', 
                    'name': self.acc_empty_name, 
                    'location': 'eastus', 
                    'kind': 'GlobalDocumentDB', 
                    'resource_group_name': self.rg1_name, 
                    'subscription_id': self.s1_guid, 
                    'databases': []
                }]
            }]
        }
        DB['subscriptions'] = [self.sub1_data]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_databases_success(self):
        databases = azmcp_cosmos_database_list(subscription=self.s1_guid, account_name=self.acc1_name)
        self.assertIsInstance(databases, list)
        self.assertEqual(len(databases), 2)
        expected_databases_set = {(self.db1_name, self.db1_id), (self.db2_name, self.db2_id)}
        returned_databases_set = {(db['name'], db['id']) for db in databases}
        self.assertEqual(returned_databases_set, expected_databases_set)

    # New test to cover subscription lookup by display name
    def test_list_databases_success_with_subscription_display_name(self):
        """
        Tests successful database listing when the subscription is provided by its display name.
        """
        databases = azmcp_cosmos_database_list(subscription=self.s1_display_name, account_name=self.acc1_name)
        self.assertIsInstance(databases, list)
        self.assertEqual(len(databases), 2)
        expected_databases_set = {(self.db1_name, self.db1_id), (self.db2_name, self.db2_id)}
        returned_databases_set = {(db['name'], db['id']) for db in databases}
        self.assertEqual(returned_databases_set, expected_databases_set)

    def test_list_databases_empty_success(self):
        databases = azmcp_cosmos_database_list(subscription=self.s1_guid, account_name=self.acc_empty_name)
        self.assertIsInstance(databases, list)
        self.assertEqual(len(databases), 0)

    def test_list_databases_with_all_optional_params_success(self):
        databases = azmcp_cosmos_database_list(subscription=self.s1_guid, account_name=self.acc1_name, auth_method='credential', tenant='tenant1-id', retry_max_retries='3', retry_delay='1', retry_max_delay='10', retry_mode='exponential', retry_network_timeout='60')
        self.assertIsInstance(databases, list)
        self.assertEqual(len(databases), 2)

    def test_subscription_not_found_raises_resource_not_found_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message='The specified Azure resource was not found.', subscription='non-existent-sub-guid', account_name=self.acc1_name)

    def test_account_not_found_raises_resource_not_found_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message='The specified Azure resource was not found.', subscription=self.s1_guid, account_name='non-existent-account-name')

    def test_missing_subscription_raises_invalid_input_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='One or more input parameters are invalid or missing.', subscription='', account_name=self.acc1_name)

    def test_missing_account_name_raises_invalid_input_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='One or more input parameters are invalid or missing.', subscription=self.s1_guid, account_name='')

    def test_invalid_retry_max_retries_format_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Input arguments failed validation.', subscription=self.s1_guid, account_name=self.acc1_name, retry_max_retries='not-a-number')

    def test_invalid_retry_delay_format_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Input arguments failed validation.', subscription=self.s1_guid, account_name=self.acc1_name, retry_delay='not-a-float')

    def test_invalid_retry_max_delay_format_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Input arguments failed validation.', subscription=self.s1_guid, account_name=self.acc1_name, retry_max_delay='invalid-time')

    def test_invalid_retry_network_timeout_format_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list,
                                    expected_exception_type=custom_errors.InvalidInputError, # Corrected here
                                    expected_message='Input arguments failed validation.',
                                    subscription=self.s1_guid,
                                    account_name=self.acc1_name,
                                    retry_network_timeout='non-numeric-timeout')
        
    def test_subscription_with_no_resource_groups(self):
        DB['subscriptions'] = [{'id': f'/subscriptions/{self.s1_guid}', 'subscriptionId': self.s1_guid, 'displayName': 'Subscription With No RGs', 'state': 'Enabled', 'tenantId': 'tenant1-id', 'resource_groups': []}]
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message='The specified Azure resource was not found.', subscription=self.s1_guid, account_name=self.acc1_name)

    def test_subscription_with_rg_but_no_cosmos_accounts_key(self):
        DB['subscriptions'] = [{'id': f'/subscriptions/{self.s1_guid}', 'subscriptionId': self.s1_guid, 'displayName': 'Subscription With RG, No Cosmos Accounts Key', 'state': 'Enabled', 'tenantId': 'tenant1-id', 'resource_groups': [{'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}', 'name': self.rg1_name, 'location': 'eastus', 'subscription_id': self.s1_guid}]}]
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message='The specified Azure resource was not found.', subscription=self.s1_guid, account_name=self.acc1_name)

    def test_subscription_with_rg_and_empty_cosmos_accounts_list(self):
        DB['subscriptions'] = [{'id': f'/subscriptions/{self.s1_guid}', 'subscriptionId': self.s1_guid, 'displayName': 'Subscription With RG, Empty Cosmos Accounts List', 'state': 'Enabled', 'tenantId': 'tenant1-id', 'resource_groups': [{'id': f'/subscriptions/{self.s1_guid}/resourceGroups/{self.rg1_name}', 'name': self.rg1_name, 'location': 'eastus', 'subscription_id': self.s1_guid, 'cosmos_db_accounts': []}]}]
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message='The specified Azure resource was not found.', subscription=self.s1_guid, account_name=self.acc1_name)

    # Test case for when subscription display name is found, but has no subscriptionId (should not happen with good data)
    def test_list_databases_sub_display_name_found_but_no_sub_id_in_db_data(self):
        s2_guid = '00000000-0000-0000-0000-000000000002'
        s2_display_name = "Subscription With Missing ID"
        DB['subscriptions'].append({
            'id': f'/subscriptions/{s2_guid}',
            'displayName': s2_display_name, # Has display name
            # 'subscriptionId': s2_guid, # Missing subscriptionId
            'state': 'Enabled',
            'tenantId': 'tenant2-id',
            'resource_groups': []
        })
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_database_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message='The specified Azure resource was not found.',
            subscription=s2_display_name, # Use display name for lookup
            account_name=self.acc1_name
        )
    
    def test_list_databases_sub_display_name_found_sub_id_not_in_find_subscription(self):

        s_orphan_id = "orphan-sub-id-001"
        s_orphan_display_name = "Orphan Display Name Sub"
        
        # Add a subscription that will be found by display name
        DB['subscriptions'].append({
            'id': f'/subscriptions/{s_orphan_id}', # Dummy ID
            'subscriptionId': s_orphan_id, # This ID will be used by the code
            'displayName': s_orphan_display_name,
            'state': 'Enabled',
            'tenantId': 'tenant-orphan',
            'resource_groups': [] # No RGs needed for this test path
        })
        
        original_find_subscription = copy.deepcopy(self._original_DB_state.get('subscriptions', []))

        def mock_find_subscription(subscription_id):
            if subscription_id == s_orphan_id:
                return None # Simulate not found for this specific ID
            # Fallback to original behavior for other IDs if necessary
            for sub in original_find_subscription:
                if sub.get("subscriptionId") == subscription_id:
                    return sub.copy()
            return None
        
        s_ghost_id = "ghost-subscription-id-123"
        s_ghost_display_name = "Ghost Sub Display Name"
        DB['subscriptions'].append({
            'id': f'/subscriptions/some-other-id-for-ghost-entry',
            'subscriptionId': s_ghost_id, # This ID is what will be extracted.
            'displayName': s_ghost_display_name,
            'state': 'Enabled',
            'tenantId': 'tenant-ghost'
            # No resource groups needed as it should fail before that
        })

        DB.clear() # Start fresh for this specific setup
        self.s1_display_name_no_id = "Sub With DisplayName But No ID Field"
        DB['subscriptions'] = [
            { # A valid subscription for other lookups if any, or to make the list non-empty
                'id': f'/subscriptions/{self.s1_guid}', 
                'subscriptionId': self.s1_guid, 
                'displayName': self.s1_display_name, 
                'state': 'Enabled', 
                'tenantId': 'tenant1-id',
                'resource_groups': [copy.deepcopy(self.sub1_data['resource_groups'][0])] # ensure it can succeed if found
            },
            { # The target subscription for the test
                'id': '/subscriptions/dummy-id-for-displayname-only-sub',
                'displayName': self.s1_display_name_no_id, # This will be matched
                # 'subscriptionId': self.s1_guid, # INTENTIONALLY MISSING or None
                'state': 'Enabled',
                'tenantId': 'tenant-no-id-field'
            }
        ]
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_database_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message='The specified Azure resource was not found.',
            subscription=self.s1_display_name_no_id, # Use the display name
            account_name=self.acc1_name
        )
        # Reset DB to the common setUp for subsequent tests
        DB.clear()
        DB['subscriptions'] = [copy.deepcopy(self.sub1_data)]

class TestAzmcpCosmosDatabaseContainerList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.sub_id_1 = '00000000-0000-0000-0000-000000000001'
        self.sub_display_name_1 = 'Primary Test Subscription'
        self.rg_name_1 = 'test-rg-1'
        self.account_name_1 = 'testcosmosacc1'
        self.db_name_1 = 'testdb1'
        self.db_name_empty = 'emptydb'
        self.db_name_one_container = 'dbwithone'
        self.container_A_id = f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}/providers/Microsoft.DocumentDB/databaseAccounts/{self.account_name_1}/sqlDatabases/{self.db_name_1}/containers/containerA'
        self.container_B_id = f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}/providers/Microsoft.DocumentDB/databaseAccounts/{self.account_name_1}/sqlDatabases/{self.db_name_1}/containers/containerB'
        self.container_C_id = f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}/providers/Microsoft.DocumentDB/databaseAccounts/{self.account_name_1}/sqlDatabases/{self.db_name_one_container}/containers/containerC'
        DB['subscriptions'] = [{'id': f'/subscriptions/{self.sub_id_1}', 'subscriptionId': self.sub_id_1, 'displayName': self.sub_display_name_1, 'state': 'Enabled', 'tenantId': 'tenant-0000-0000-0001', 'resource_groups': [{'id': f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}', 'name': self.rg_name_1, 'location': 'eastus', 'subscription_id': self.sub_id_1, 'cosmos_db_accounts': [{'id': f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}/providers/Microsoft.DocumentDB/databaseAccounts/{self.account_name_1}', 'name': self.account_name_1, 'location': 'eastus', 'kind': 'GlobalDocumentDB', 'resource_group_name': self.rg_name_1, 'subscription_id': self.sub_id_1, 'databases': [{'id': f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}/providers/Microsoft.DocumentDB/databaseAccounts/{self.account_name_1}/sqlDatabases/{self.db_name_1}', 'name': self.db_name_1, 'account_name': self.account_name_1, 'containers': [{'id': self.container_A_id, 'name': 'containerA', 'database_name': self.db_name_1, 'account_name': self.account_name_1, 'items': []}, {'id': self.container_B_id, 'name': 'containerB', 'database_name': self.db_name_1, 'account_name': self.account_name_1, 'items': []}]}, {'id': f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}/providers/Microsoft.DocumentDB/databaseAccounts/{self.account_name_1}/sqlDatabases/{self.db_name_empty}', 'name': self.db_name_empty, 'account_name': self.account_name_1, 'containers': []}, {'id': f'/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}/providers/Microsoft.DocumentDB/databaseAccounts/{self.account_name_1}/sqlDatabases/{self.db_name_one_container}', 'name': self.db_name_one_container, 'account_name': self.account_name_1, 'containers': [{'id': self.container_C_id, 'name': 'containerC', 'database_name': self.db_name_one_container, 'account_name': self.account_name_1, 'items': []}]}]}]}]}]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_containers_success_multiple_containers(self):
        result = azmcp_cosmos_database_container_list(subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_1)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        expected_containers = [{'name': 'containerA', 'id': self.container_A_id}, {'name': 'containerB', 'id': self.container_B_id}]
        self.assertEqual(sorted(result, key=lambda x: x['name']), sorted(expected_containers, key=lambda x: x['name']))

    def test_list_containers_success_one_container(self):
        result = azmcp_cosmos_database_container_list(subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_one_container)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'containerC')
        self.assertEqual(result[0]['id'], self.container_C_id)

    def test_list_containers_success_no_containers(self):
        result = azmcp_cosmos_database_container_list(subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_empty)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_list_containers_success_with_all_optional_params(self):
        result = azmcp_cosmos_database_container_list(subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_one_container, auth_method='credential', retry_delay='5', retry_max_delay='30', retry_max_retries='3', retry_mode='exponential', retry_network_timeout='60', tenant='tenant-0000-0000-0001')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'containerC')

    def test_list_containers_success_subscription_by_display_name(self):
        result = azmcp_cosmos_database_container_list(subscription=self.sub_display_name_1, account_name=self.account_name_1, database_name=self.db_name_one_container)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'containerC')

    def test_subscription_not_found(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.SubscriptionNotFoundError, expected_message='The specified Azure subscription was not found or is not accessible.', subscription='non-existent-sub-id', account_name=self.account_name_1, database_name=self.db_name_1)

    def test_account_not_found(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Cosmos DB account 'non-existent-account' not found in resource group '{self.rg_name_1}' and subscription '{self.sub_id_1}'.", subscription=self.sub_id_1, account_name='non-existent-account', database_name=self.db_name_1)

    def test_account_not_found_in_different_rg(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Cosmos DB account 'cosmos-acc-in-wrong-rg' not found in resource group '{self.rg_name_1}' and subscription '{self.sub_id_1}'.", subscription=self.sub_id_1, account_name='cosmos-acc-in-wrong-rg', database_name=self.db_name_1)

    def test_database_not_found(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Cosmos DB database 'non-existent-db' not found in account '{self.account_name_1}'.", subscription=self.sub_id_1, account_name=self.account_name_1, database_name='non-existent-db')

    def test_invalid_auth_method(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_1, auth_method='invalid_auth')

    def test_invalid_retry_delay_format(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_1, retry_delay='not_a_number')

    def test_invalid_retry_max_delay_format(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_1, retry_max_delay='not_a_number')

    def test_invalid_retry_max_retries_format(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_1, retry_max_retries='not_a_number')

    def test_invalid_retry_mode_value(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_1, retry_mode='invalid_mode')

    def test_invalid_retry_network_timeout_format(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name=self.account_name_1, database_name=self.db_name_1, retry_network_timeout='not_a_number')

    def test_empty_subscription_string(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription='', account_name=self.account_name_1, database_name=self.db_name_1)

    def test_empty_account_name_string(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name='', database_name=self.db_name_1)

    def test_empty_database_name_string(self):
        self.assert_error_behavior(func_to_call=azmcp_cosmos_database_container_list, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed', subscription=self.sub_id_1, account_name=self.account_name_1, database_name='')

class TestAzmcpCosmosAccountList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.sub_id_1 = "00000000-0000-0000-0000-000000000001"
        self.sub_name_1 = "My Subscription One"
        self.rg1_name_sub1 = "rg1-sub1"
        self.rg2_name_sub1 = "rg2-sub1"
        self.rg3_name_sub1_no_cosmos = "rg3-sub1-no-cosmos"

        self.cosmos_acc1_s1_rg1 = {
            "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg1_name_sub1}/providers/Microsoft.DocumentDB/databaseAccounts/cosmosAcc1",
            "name": "cosmosAcc1",
            "location": "eastus",
            "kind": "GlobalDocumentDB",
            "resource_group_name": self.rg1_name_sub1,
            "subscription_id": self.sub_id_1,
            "databases": []
        }
        self.cosmos_acc2_s1_rg1 = {
            "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg1_name_sub1}/providers/Microsoft.DocumentDB/databaseAccounts/cosmosAcc2",
            "name": "cosmosAcc2",
            "location": "westus",
            "kind": "MongoDB",
            "resource_group_name": self.rg1_name_sub1,
            "subscription_id": self.sub_id_1,
            "databases": []
        }
        self.cosmos_acc3_s1_rg2 = {
            "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg2_name_sub1}/providers/Microsoft.DocumentDB/databaseAccounts/cosmosAcc3",
            "name": "cosmosAcc3",
            "location": "westus",
            "kind": "Cassandra",
            "resource_group_name": self.rg2_name_sub1,
            "subscription_id": self.sub_id_1,
            "databases": []
        }

        self.sub_id_2_empty = "00000000-0000-0000-0000-000000000002"
        self.sub_name_2_empty = "My Subscription Two (Empty)"
        self.rg1_name_sub2_empty_cosmos = "rg1-sub2-empty"

        self.sub_id_3_no_rg = "00000000-0000-0000-0000-000000000003"
        self.sub_name_3_no_rg = "My Subscription Three (No RGs)"

        self.sub_id_4_one_acc = "00000000-0000-0000-0000-000000000004"
        self.sub_name_4_one_acc = "My Subscription Four (One Account)"
        self.rg1_name_sub4_one_acc = "rg1-sub4-one-acc"
        self.cosmos_acc1_s4_rg1 = {
            "id": f"/subscriptions/{self.sub_id_4_one_acc}/resourceGroups/{self.rg1_name_sub4_one_acc}/providers/Microsoft.DocumentDB/databaseAccounts/cosmosAccSolo",
            "name": "cosmosAccSolo",
            "location": "centralus",
            "kind": "GlobalDocumentDB",
            "resource_group_name": self.rg1_name_sub4_one_acc,
            "subscription_id": self.sub_id_4_one_acc,
            "databases": []
        }

        self.non_existent_sub_id = "11111111-1111-1111-1111-111111111111"
        self.non_existent_sub_name = "NonExistentSubscriptionName"

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.sub_id_1}",
                "subscriptionId": self.sub_id_1,
                "displayName": self.sub_name_1,
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg1_name_sub1}",
                        "name": self.rg1_name_sub1,
                        "location": "eastus",
                        "subscription_id": self.sub_id_1,
                        "cosmos_db_accounts": [
                            copy.deepcopy(self.cosmos_acc1_s1_rg1),
                            copy.deepcopy(self.cosmos_acc2_s1_rg1)
                        ]
                    },
                    {
                        "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg2_name_sub1}",
                        "name": self.rg2_name_sub1,
                        "location": "westus",
                        "subscription_id": self.sub_id_1,
                        "cosmos_db_accounts": [
                            copy.deepcopy(self.cosmos_acc3_s1_rg2)
                        ]
                    },
                    { 
                        "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg3_name_sub1_no_cosmos}",
                        "name": self.rg3_name_sub1_no_cosmos,
                        "location": "centralus",
                        "subscription_id": self.sub_id_1,
                        "cosmos_db_accounts": [] 
                    }
                ]
            },
            { 
                "id": f"/subscriptions/{self.sub_id_2_empty}",
                "subscriptionId": self.sub_id_2_empty,
                "displayName": self.sub_name_2_empty,
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub_id_2_empty}/resourceGroups/{self.rg1_name_sub2_empty_cosmos}",
                        "name": self.rg1_name_sub2_empty_cosmos,
                        "location": "eastus",
                        "subscription_id": self.sub_id_2_empty,
                        "cosmos_db_accounts": [] 
                    }
                ]
            },
            { 
                "id": f"/subscriptions/{self.sub_id_3_no_rg}",
                "subscriptionId": self.sub_id_3_no_rg,
                "displayName": self.sub_name_3_no_rg,
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [] 
            },
            {
                "id": f"/subscriptions/{self.sub_id_4_one_acc}",
                "subscriptionId": self.sub_id_4_one_acc,
                "displayName": self.sub_name_4_one_acc,
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                     {
                        "id": f"/subscriptions/{self.sub_id_4_one_acc}/resourceGroups/{self.rg1_name_sub4_one_acc}",
                        "name": self.rg1_name_sub4_one_acc,
                        "location": "centralus",
                        "subscription_id": self.sub_id_4_one_acc,
                        "cosmos_db_accounts": [
                            copy.deepcopy(self.cosmos_acc1_s4_rg1)
                        ]
                    }
                ]
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_account_lists_equal(self, list1, list2):
        self.assertEqual(len(list1), len(list2), "Lists have different lengths.")
        # Sort by 'id' for consistent comparison, as order is not guaranteed
        sorted_list1 = sorted(list1, key=lambda x: x['id'])
        sorted_list2 = sorted(list2, key=lambda x: x['id'])
        self.assertEqual(sorted_list1, sorted_list2, "Sorted lists are not equal.")

    def test_list_accounts_success_multiple_rgs_by_id(self):
        results = azmcp_cosmos_account_list(subscription=self.sub_id_1)
        expected_accounts = [
            {
                "name": self.cosmos_acc1_s1_rg1["name"], "id": self.cosmos_acc1_s1_rg1["id"],
                "location": self.cosmos_acc1_s1_rg1["location"], "kind": self.cosmos_acc1_s1_rg1["kind"]
            },
            {
                "name": self.cosmos_acc2_s1_rg1["name"], "id": self.cosmos_acc2_s1_rg1["id"],
                "location": self.cosmos_acc2_s1_rg1["location"], "kind": self.cosmos_acc2_s1_rg1["kind"]
            },
            {
                "name": self.cosmos_acc3_s1_rg2["name"], "id": self.cosmos_acc3_s1_rg2["id"],
                "location": self.cosmos_acc3_s1_rg2["location"], "kind": self.cosmos_acc3_s1_rg2["kind"]
            }
        ]
        self._assert_account_lists_equal(results, expected_accounts)

    def test_list_accounts_success_multiple_rgs_by_name(self):
        results = azmcp_cosmos_account_list(subscription=self.sub_name_1)
        expected_accounts = [
            {
                "name": self.cosmos_acc1_s1_rg1["name"], "id": self.cosmos_acc1_s1_rg1["id"],
                "location": self.cosmos_acc1_s1_rg1["location"], "kind": self.cosmos_acc1_s1_rg1["kind"]
            },
            {
                "name": self.cosmos_acc2_s1_rg1["name"], "id": self.cosmos_acc2_s1_rg1["id"],
                "location": self.cosmos_acc2_s1_rg1["location"], "kind": self.cosmos_acc2_s1_rg1["kind"]
            },
            {
                "name": self.cosmos_acc3_s1_rg2["name"], "id": self.cosmos_acc3_s1_rg2["id"],
                "location": self.cosmos_acc3_s1_rg2["location"], "kind": self.cosmos_acc3_s1_rg2["kind"]
            }
        ]
        self._assert_account_lists_equal(results, expected_accounts)

    def test_list_accounts_success_one_account(self):
        results = azmcp_cosmos_account_list(subscription=self.sub_id_4_one_acc)
        expected_accounts = [
            {
                "name": self.cosmos_acc1_s4_rg1["name"], "id": self.cosmos_acc1_s4_rg1["id"],
                "location": self.cosmos_acc1_s4_rg1["location"], "kind": self.cosmos_acc1_s4_rg1["kind"]
            }
        ]
        self._assert_account_lists_equal(results, expected_accounts)

    def test_list_accounts_subscription_with_no_accounts_by_id(self):
        results = azmcp_cosmos_account_list(subscription=self.sub_id_2_empty)
        self.assertEqual(results, [])

    def test_list_accounts_subscription_with_no_accounts_by_name(self):
        results = azmcp_cosmos_account_list(subscription=self.sub_name_2_empty)
        self.assertEqual(results, [])

    def test_list_accounts_subscription_with_no_resource_groups_by_id(self):
        results = azmcp_cosmos_account_list(subscription=self.sub_id_3_no_rg)
        self.assertEqual(results, [])

    def test_list_accounts_subscription_with_no_resource_groups_by_name(self):
        results = azmcp_cosmos_account_list(subscription=self.sub_name_3_no_rg)
        self.assertEqual(results, [])

    def test_subscription_not_found_by_id_raises_subscriptionnotfounderror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message=f"Subscription '{self.non_existent_sub_id}' not found.",
            subscription=self.non_existent_sub_id
        )

    def test_subscription_not_found_by_name_raises_subscriptionnotfounderror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message=f"Subscription '{self.non_existent_sub_name}' not found.",
            subscription=self.non_existent_sub_name
        )

    def test_empty_subscription_string_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_cosmos_account_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Subscription ID or name must be provided.", 
            subscription=""
        )

    def test_optional_parameters_do_not_affect_outcome(self):
        results = azmcp_cosmos_account_list(
            subscription=self.sub_id_1,
            auth_method="credential",
            tenant="some-tenant-id",
            retry_max_retries="5",
            retry_delay="10",
            retry_max_delay="60",
            retry_mode="exponential",
            retry_network_timeout="30"
        )
        expected_accounts = [
            {
                "name": self.cosmos_acc1_s1_rg1["name"], "id": self.cosmos_acc1_s1_rg1["id"],
                "location": self.cosmos_acc1_s1_rg1["location"], "kind": self.cosmos_acc1_s1_rg1["kind"]
            },
            {
                "name": self.cosmos_acc2_s1_rg1["name"], "id": self.cosmos_acc2_s1_rg1["id"],
                "location": self.cosmos_acc2_s1_rg1["location"], "kind": self.cosmos_acc2_s1_rg1["kind"]
            },
            {
                "name": self.cosmos_acc3_s1_rg2["name"], "id": self.cosmos_acc3_s1_rg2["id"],
                "location": self.cosmos_acc3_s1_rg2["location"], "kind": self.cosmos_acc3_s1_rg2["kind"]
            }
        ]
        self._assert_account_lists_equal(results, expected_accounts)

    def test_subscription_with_missing_resource_groups_key_handled_gracefully(self):
        temp_sub_id = "temp-sub-no-rg-key"
        DB["subscriptions"].append({
            "id": f"/subscriptions/{temp_sub_id}",
            "subscriptionId": temp_sub_id,
            "displayName": "Temp Sub Missing RG Key",
            "state": "Enabled",
            "tenantId": "tenant-guid-temp"
        })
        results = azmcp_cosmos_account_list(subscription=temp_sub_id)
        self.assertEqual(results, [])

    def test_resource_group_with_missing_cosmos_accounts_key_handled_gracefully(self):
        temp_sub_id = "temp-sub-rg-no-cosmos-key"
        temp_rg_name = "temp-rg-no-cosmos-key"
        DB["subscriptions"].append({
            "id": f"/subscriptions/{temp_sub_id}",
            "subscriptionId": temp_sub_id,
            "displayName": "Temp Sub RG Missing Cosmos Key",
            "state": "Enabled",
            "tenantId": "tenant-guid-temp",
            "resource_groups": [
                {
                    "id": f"/subscriptions/{temp_sub_id}/resourceGroups/{temp_rg_name}",
                    "name": temp_rg_name,
                    "location": "eastus",
                    "subscription_id": temp_sub_id
                }
            ]
        })
        results = azmcp_cosmos_account_list(subscription=temp_sub_id)
        self.assertEqual(results, [])

    def test_cosmos_account_in_db_missing_required_field_is_skipped(self):
        # This test assumes that if a CosmosDBAccount in the DB is missing a field
        # required for the output (e.g., 'kind'), it should be skipped.
        malformed_sub_id = "sub-malformed-data"
        malformed_rg_name = "rg-malformed-data"

        # Create a deep copy of a valid account to ensure it's not modified elsewhere
        valid_account_template = copy.deepcopy(self.cosmos_acc1_s1_rg1)
        valid_account_in_test = {
            **valid_account_template,
            "subscription_id": malformed_sub_id,
            "resource_group_name": malformed_rg_name,
            "id": f"/subscriptions/{malformed_sub_id}/resourceGroups/{malformed_rg_name}/providers/Microsoft.DocumentDB/databaseAccounts/{valid_account_template['name']}-valid"
        }

        DB["subscriptions"].append({
            "id": f"/subscriptions/{malformed_sub_id}",
            "subscriptionId": malformed_sub_id,
            "displayName": "Subscription with Malformed Cosmos Account Data",
            "state": "Enabled",
            "tenantId": "tenant-guid-malformed",
            "resource_groups": [
                {
                    "id": f"/subscriptions/{malformed_sub_id}/resourceGroups/{malformed_rg_name}",
                    "name": malformed_rg_name,
                    "location": "eastus",
                    "subscription_id": malformed_sub_id,
                    "cosmos_db_accounts": [
                        { 
                            "id": f"/subscriptions/{malformed_sub_id}/resourceGroups/{malformed_rg_name}/providers/Microsoft.DocumentDB/databaseAccounts/cosmosMalformedField",
                            "name": "cosmosMalformedField",
                            "location": "eastus",
                            # "kind" is missing, which is required for the output object
                            "resource_group_name": malformed_rg_name,
                            "subscription_id": malformed_sub_id,
                        },
                        valid_account_in_test # A valid account
                    ]
                }
            ]
        })

        results = azmcp_cosmos_account_list(subscription=malformed_sub_id)

        expected_accounts = [
             {
                "name": valid_account_in_test["name"], 
                "id": valid_account_in_test["id"],
                "location": valid_account_in_test["location"], 
                "kind": valid_account_in_test["kind"]
            }
        ]
        self._assert_account_lists_equal(results, expected_accounts)


if __name__ == '__main__':
    unittest.main()