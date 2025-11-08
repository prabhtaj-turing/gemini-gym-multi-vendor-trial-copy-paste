import unittest
import copy
from datetime import datetime
import re
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..project import generate_typescript_types

class TestGenerateTypeScriptTypes(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB['organizations'] = [{'id': 'org_1', 'name': 'Org One', 'created_at': datetime.utcnow(), 'subscription_plan': None}]
        DB['projects'] = [{'id': 'proj_1', 'name': 'Project One', 'organization_id': 'org_1', 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'}, {'id': 'proj_2', 'name': 'Project Two', 'organization_id': 'org_1', 'region': 'eu-central-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'}, {'id': 'proj_empty', 'name': 'Empty Project', 'organization_id': 'org_1', 'region': 'ap-south-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'}, {'id': 'proj_table_no_cols', 'name': 'Project Table No Columns', 'organization_id': 'org_1', 'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'}, {'id': 'proj_unsupported_type', 'name': 'Project Unsupported Type', 'organization_id': 'org_1', 'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'}]
        DB['tables'] = {'proj_1': [{'name': 'users', 'schema': 'public', 'comment': 'User table', 'columns': [{'name': 'id', 'data_type': 'integer', 'is_nullable': False, 'default_value': "nextval('users_id_seq'::regclass)"}, {'name': 'username', 'data_type': 'text', 'is_nullable': False}, {'name': 'email', 'data_type': 'varchar', 'is_nullable': True}], 'primary_keys': [{'name': 'id'}], 'relationships': []}], 'proj_2': [{'name': 'products', 'schema': 'public', 'comment': None, 'columns': [{'name': 'product_id', 'data_type': 'uuid', 'is_nullable': False}, {'name': 'name', 'data_type': 'text', 'is_nullable': False}, {'name': 'price', 'data_type': 'numeric', 'is_nullable': False}, {'name': 'is_available', 'data_type': 'boolean', 'is_nullable': False}, {'name': 'created_at', 'data_type': 'timestamp', 'is_nullable': False, 'default_value': 'now()'}, {'name': 'tags', 'data_type': 'text[]', 'is_nullable': True}, {'name': 'metadata', 'data_type': 'jsonb', 'is_nullable': True}, {'name': 'stock_count', 'data_type': 'int4', 'is_nullable': True}, {'name': 'description', 'data_type': 'character varying', 'is_nullable': True}], 'primary_keys': [{'name': 'product_id'}], 'relationships': []}, {'name': 'orders', 'schema': 'custom_schema', 'comment': 'Order details', 'columns': [{'name': 'order_id', 'data_type': 'bigint', 'is_nullable': False}, {'name': 'details', 'data_type': 'json', 'is_nullable': True}], 'primary_keys': [{'name': 'order_id'}], 'relationships': []}], 'proj_table_no_cols': [{'name': 'empty_table', 'schema': 'public', 'comment': None, 'columns': [], 'primary_keys': [], 'relationships': []}], 'proj_unsupported_type': [{'name': 'bad_table', 'schema': 'public', 'comment': None, 'columns': [{'name': 'id', 'data_type': 'integer', 'is_nullable': False}, {'name': 'problem_column', 'data_type': 'SUPER_CUSTOM_UNSUPPORTED_TYPE', 'is_nullable': False}], 'primary_keys': [{'name': 'id'}], 'relationships': []}]}
        DB['extensions'] = {}
        DB['migrations'] = {}
        DB['edge_functions'] = {}
        DB['branches'] = {}
        DB['costs'] = {}
        DB['unconfirmed_costs'] = {}
        DB['project_urls'] = {}
        DB['project_anon_keys'] = {}
        DB['project_ts_types'] = {}
        DB['logs'] = {}

    def tearDown(self):
        DB = self._original_DB_state

    def _ts_pascal_case(self, name: str) -> str:
        name = re.sub('[^a-zA-Z0-9_]+', '_', name)
        if not name or name == '_':
            return 'UnnamedInterface'
        return ''.join((word.capitalize() for word in name.split('_') if word))

    def _ts_camel_case(self, name: str) -> str:
        name = re.sub('[^a-zA-Z0-9_]+', '_', name)
        if not name:
            return '_'
        if name[0].isdigit():
            name = '_' + name
        parts = [part for part in name.split('_') if part]
        if not parts:
            return '_'
        result = parts[0][0].lower() + parts[0][1:]
        for part in parts[1:]:
            result += part[0].upper() + part[1:]
        return result

    def _map_db_type_to_ts(self, db_type: str, is_nullable: bool) -> str:
        ts_type = 'any'
        db_type_lower = db_type.lower()
        if db_type_lower.endswith('[]'):
            element_type = db_type_lower[:-2]
            ts_element_type = self._map_db_type_to_ts(element_type, False).replace(' | null', '')
            ts_type = f'{ts_element_type}[]'
        elif db_type_lower in ['integer', 'bigint', 'smallint', 'numeric', 'decimal', 'real', 'double precision', 'int', 'int2', 'int4', 'int8', 'serial', 'bigserial', 'smallserial', 'float4', 'float8', 'money']:
            ts_type = 'number'
        elif db_type_lower in ['text', 'varchar', 'char', 'bpchar', 'uuid', 'inet', 'citext', 'name', 'character varying', 'character', 'string']:
            ts_type = 'string'
        elif db_type_lower in ['boolean', 'bool']:
            ts_type = 'boolean'
        elif db_type_lower in ['date', 'timestamp', 'timestamptz', 'time', 'timetz', 'interval']:
            ts_type = 'string'
        elif db_type_lower in ['json', 'jsonb']:
            ts_type = 'any'
        elif db_type_lower == 'bytea':
            ts_type = 'string'
        return f"{ts_type}{(' | null' if is_nullable else '')}"

    def _generate_expected_ts_interface_string(self, interface_name: str, columns_data: list[tuple[str, str, bool]]) -> str:
        if not columns_data:
            return f'export interface {interface_name} {{}}\n'
        properties_ts = []
        for col_name, col_type, is_nullable in columns_data:
            ts_prop_name = col_name
            ts_type_str = self._map_db_type_to_ts(col_type, is_nullable)
            properties_ts.append(f'  {ts_prop_name}: {ts_type_str};')
        cols_str = '\n'.join(properties_ts)
        return f'export interface {interface_name} {{\n{cols_str}\n}}\n'

    def test_generate_types_success_simple_project(self):
        project_id = 'proj_1'
        result = generate_typescript_types(project_id=project_id)
        self.assertEqual(result['project_id'], project_id)
        self.assertEqual(result['generation_status'], 'SUCCESS')
        self.assertIsNone(result['message'])
        interface_name = 'users'
        expected_ts_content = self._generate_expected_ts_interface_string(interface_name, [('id', 'integer', False), ('username', 'text', False), ('email', 'varchar', True)])
        self.assertEqual(result['types_content'].strip(), expected_ts_content.strip())

    def test_generate_types_success_complex_project_all_types_and_schemas(self):
        project_id = 'proj_2'
        result = generate_typescript_types(project_id=project_id)
        self.assertEqual(result['project_id'], project_id)
        self.assertEqual(result['generation_status'], 'SUCCESS')
        self.assertIsNone(result['message'])
        products_interface_name = 'products'
        products_ts = self._generate_expected_ts_interface_string(products_interface_name, [('product_id', 'uuid', False), ('name', 'text', False), ('price', 'numeric', False), ('is_available', 'boolean', False), ('created_at', 'timestamp', False), ('tags', 'text[]', True), ('metadata', 'jsonb', True), ('stock_count', 'int4', True), ('description', 'character varying', True)])
        orders_interface_name = 'orders'
        orders_ts = self._generate_expected_ts_interface_string(orders_interface_name, [('order_id', 'bigint', False), ('details', 'json', True)])
        expected_ts_content_ordered_by_setup = products_ts + orders_ts
        self.assertEqual(result['types_content'].strip(), expected_ts_content_ordered_by_setup.strip())

    def test_generate_types_success_project_no_tables(self):
        project_id = 'proj_empty'
        result = generate_typescript_types(project_id=project_id)
        self.assertEqual(result['project_id'], project_id)
        self.assertEqual(result['generation_status'], 'SUCCESS')
        self.assertIsNone(result['message'])
        self.assertEqual(result['types_content'], '')

    def test_generate_types_success_project_table_no_columns(self):
        project_id = 'proj_table_no_cols'
        result = generate_typescript_types(project_id=project_id)
        self.assertEqual(result['project_id'], project_id)
        self.assertEqual(result['generation_status'], 'SUCCESS')
        self.assertIsNone(result['message'])
        interface_name = 'empty_table'
        expected_ts_content = self._generate_expected_ts_interface_string(interface_name, [])
        self.assertEqual(result['types_content'].strip(), expected_ts_content.strip())

    def test_generate_types_error_project_not_found(self):
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.NotFoundError, expected_message="Project with ID 'proj_nonexistent' not found.", project_id='proj_nonexistent')

    def test_generate_types_error_type_generation_failure_unsupported_type(self):
        project_id = 'proj_unsupported_type'
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.TypeGenerationError, expected_message=f"Type generation failed for project {project_id}: Encountered unsupported data type 'SUPER_CUSTOM_UNSUPPORTED_TYPE' in table 'bad_table', column 'problem_column'.", project_id=project_id)

    def test_generate_types_error_type_generation_failure_table_missing_name(self):
        project_id = 'proj_table_missing_name'
        DB['projects'].append({'id': project_id, 'name': 'Project Table Missing Name', 'organization_id': 'org_1', 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'})
        DB['tables'][project_id] = [{'schema': 'public', 'columns': []}]
        expected_message = f"Table in project '{project_id}' (schema: 'public') found with no name. Schema introspection failed."
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.TypeGenerationError, expected_message=expected_message, project_id=project_id)

    def test_generate_types_error_type_generation_failure_column_missing_details(self):
        project_id = 'proj_col_missing_details'
        DB['projects'].append({'id': project_id, 'name': 'Project Column Missing Details', 'organization_id': 'org_1', 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'})
        
        DB['tables'][project_id] = [{'name': 'test_table', 'schema': 'public', 'columns': [{'data_type': 'integer'}]}]
        expected_message = f"Column in table 'public.test_table' (project '{project_id}') is missing name or data_type. Schema introspection failed."
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.TypeGenerationError, expected_message=expected_message, project_id=project_id)
        
        DB['tables'][project_id] = [{'name': 'test_table', 'schema': 'public', 'columns': [{'name': 'id'}]}]
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.TypeGenerationError, expected_message=expected_message, project_id=project_id)

    def test_generate_types_input_validation_error_non_string_project_id(self):
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: project_id must be a string.', project_id=12345)

    def test_generate_types_input_validation_error_empty_project_id(self):
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: project_id cannot be empty.', project_id='')

    def test_generate_types_input_validation_error_none_project_id(self):
        self.assert_error_behavior(func_to_call=generate_typescript_types, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: project_id cannot be null or not a string.', project_id=None)

    def test_generate_types_success_column_name_sanitization(self):
        project_id = 'proj_special_cols'
        DB['projects'].append({'id': project_id, 'name': 'Project Special Columns', 'organization_id': 'org_1', 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'})
        DB['tables'][project_id] = [{'name': 'data_entries', 'schema': 'public', 'comment': None, 'columns': [{'name': 'entry-id', 'data_type': 'integer', 'is_nullable': False}, {'name': 'user_name', 'data_type': 'text', 'is_nullable': False}, {'name': 'is-active?', 'data_type': 'boolean', 'is_nullable': True}, {'name': '2fa_enabled', 'data_type': 'boolean', 'is_nullable': False}, {'name': 'metadata value', 'data_type': 'json', 'is_nullable': True}, {'name': '__internal__field__', 'data_type': 'text', 'is_nullable': False}], 'primary_keys': [{'name': 'entry-id'}], 'relationships': []}]
        result = generate_typescript_types(project_id=project_id)
        self.assertEqual(result['generation_status'], 'SUCCESS')
        interface_name = 'data_entries'
        expected_ts_content = self._generate_expected_ts_interface_string(interface_name, [('entry-id', 'integer', False), ('user_name', 'text', False), ('is-active?', 'boolean', True), ('2fa_enabled', 'boolean', False), ('metadata value', 'json', True), ('__internal__field__', 'text', False)])
        self.assertEqual(result['types_content'].strip(), expected_ts_content.strip())

    def test_generate_types_success_table_name_sanitization(self):
        project_id = 'proj_special_tables'
        DB['projects'].append({'id': project_id, 'name': 'Project Special Tables', 'organization_id': 'org_1', 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime.utcnow(), 'version': '15.1'})
        DB['tables'][project_id] = [{'name': 'user-profiles-data', 'schema': 'public', 'comment': None, 'columns': [{'name': 'id', 'data_type': 'integer', 'is_nullable': False}], 'primary_keys': [{'name': 'id'}], 'relationships': []}, {'name': 'API_Keys', 'schema': 'public', 'comment': None, 'columns': [{'name': 'key_value', 'data_type': '_text', 'is_nullable': False}], 'primary_keys': [], 'relationships': []}]
        result = generate_typescript_types(project_id=project_id)
        self.assertEqual(result['generation_status'], 'SUCCESS')
        interface1_name = 'user-profiles-data'
        table1_ts = self._generate_expected_ts_interface_string(interface1_name, [('id', 'integer', False)])
        interface2_name = 'API_Keys'
        table2_ts = 'export interface API_Keys {\n  key_value: string[];\n}'
        expected_ts_content = table1_ts + table2_ts
        self.assertEqual(result['types_content'].strip(), expected_ts_content.strip())

if __name__ == '__main__':
    unittest.main()