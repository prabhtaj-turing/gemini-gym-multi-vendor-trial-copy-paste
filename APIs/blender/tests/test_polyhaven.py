"""
Test suite for Polyhaven integration functionalities in the Blender API simulation.
"""
import copy
import unittest
import uuid
from blender import get_polyhaven_categories
from blender import get_polyhaven_status
from blender import search_polyhaven_assets
from blender.SimulationEngine import custom_errors
from blender.SimulationEngine.custom_errors import InvalidAssetTypeError, InvalidInputError
from blender.SimulationEngine.db import DB
from blender.SimulationEngine.models import PolyhavenAssetTypeSearchable
from blender.polyhaven import download_polyhaven_asset
from common_utils.base_case import BaseTestCaseWithErrorHandler
from blender.SimulationEngine.utils import create_asset
from unittest.mock import patch, MagicMock
from pydantic import ValidationError as PydanticValidationError

# Initial DB state for get_polyhaven_categories function tests
GET_POLYHAVEN_CATEGORIES_INITIAL_DB_STATE = {}


class TestGetPolyhavenCategories(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['polyhaven_categories_cache'] = {
            "hdris": ["Indoor", "Outdoor", "Studio", "SharedCategory"],
            "textures": ["Wood", "Metal", "Fabric", "SharedCategory"],
            "models": ["Furniture", "Vehicle", "Nature", "AnotherShared"]
        }
        # Initialize other parts of DB to mimic a complete DB structure,
        # even if not directly used by this specific function.
        DB['current_scene'] = {
            "id": "scene_uuid_str_default",
            "name": "Scene",
            "objects": {},
            "active_camera_name": None,
            "world_settings": {
                "ambient_color": [0.05, 0.05, 0.05],
                "horizon_color": [0.5, 0.5, 0.5],
                "environment_texture_polyhaven_id": None,
                "environment_texture_strength": 1.0
            },
            "render_settings": {
                "engine": "CYCLES",  # Default from RenderEngineType
                "resolution_x": 1920,
                "resolution_y": 1080,
                "resolution_percentage": 100,
                "filepath": "/tmp/render_####.png"
            }
        }
        DB['materials'] = {}
        DB['polyhaven_service_status'] = {
            "is_enabled": True,
            "message": "Polyhaven integration is enabled."
        }
        DB['polyhaven_assets_db'] = {}
        DB['hyper3d_service_status'] = {
            "is_enabled": True,
            "mode": "MAIN_SITE",  # Default from Hyper3DMode
            "message": "Hyper3D Rodin integration is enabled."
        }
        DB['hyper3d_jobs'] = {}
        DB['execution_logs'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_categories_default_asset_type_hdris_success(self):
        # Default asset_type is "hdris"
        expected_categories = sorted(DB['polyhaven_categories_cache']['hdris'])
        result = get_polyhaven_categories()
        self.assertEqual(sorted(result), expected_categories, "Categories for default asset_type (hdris) should match.")

    def test_get_categories_explicit_asset_type_hdris_success(self):
        expected_categories = sorted(DB['polyhaven_categories_cache']['hdris'])
        result = get_polyhaven_categories(asset_type="hdris")
        self.assertEqual(sorted(result), expected_categories, "Categories for asset_type='hdris' should match.")

    def test_get_categories_hdris_cache_key_missing_returns_empty_list(self):
        del DB['polyhaven_categories_cache']['hdris']
        result = get_polyhaven_categories(asset_type="hdris")
        self.assertEqual(result, [], "Should return empty list if 'hdris' key is missing in cache.")

    def test_get_categories_hdris_cache_value_empty_list_returns_empty_list(self):
        DB['polyhaven_categories_cache']['hdris'] = []
        result = get_polyhaven_categories(asset_type="hdris")
        self.assertEqual(result, [], "Should return empty list if 'hdris' categories list is empty.")

    def test_get_categories_asset_type_textures_success(self):
        expected_categories = sorted(DB['polyhaven_categories_cache']['textures'])
        result = get_polyhaven_categories(asset_type="textures")
        self.assertEqual(sorted(result), expected_categories, "Categories for asset_type='textures' should match.")

    def test_get_categories_textures_cache_key_missing_returns_empty_list(self):
        del DB['polyhaven_categories_cache']['textures']
        result = get_polyhaven_categories(asset_type="textures")
        self.assertEqual(result, [], "Should return empty list if 'textures' key is missing in cache.")

    def test_get_categories_asset_type_models_success(self):
        expected_categories = sorted(DB['polyhaven_categories_cache']['models'])
        result = get_polyhaven_categories(asset_type="models")
        self.assertEqual(sorted(result), expected_categories, "Categories for asset_type='models' should match.")

    def test_get_categories_models_cache_key_missing_returns_empty_list(self):
        del DB['polyhaven_categories_cache']['models']
        result = get_polyhaven_categories(asset_type="models")
        self.assertEqual(result, [], "Should return empty list if 'models' key is missing in cache.")

    def test_get_categories_asset_type_all_success_combines_unique_sorted(self):
        hdri_cats = DB['polyhaven_categories_cache'].get('hdris', [])
        texture_cats = DB['polyhaven_categories_cache'].get('textures', [])
        model_cats = DB['polyhaven_categories_cache'].get('models', [])

        combined_unique_sorted = sorted(list(set(hdri_cats + texture_cats + model_cats)))

        result = get_polyhaven_categories(asset_type="all")
        # Assuming the function returns a sorted list for "all"
        self.assertEqual(result, combined_unique_sorted, "Categories for 'all' should be combined, unique, and sorted.")

    def test_get_categories_all_one_type_missing_in_cache(self):
        # 'textures' categories are removed from cache
        original_textures_cache = DB['polyhaven_categories_cache'].pop('textures', None)

        hdri_cats = DB['polyhaven_categories_cache'].get('hdris', [])
        model_cats = DB['polyhaven_categories_cache'].get('models', [])
        combined_unique_sorted = sorted(list(set(hdri_cats + model_cats)))

        result = get_polyhaven_categories(asset_type="all")
        self.assertEqual(result, combined_unique_sorted,
                         "Categories for 'all' with one type missing should be correct.")

        if original_textures_cache is not None:  # Restore for other tests if needed before tearDown
            DB['polyhaven_categories_cache']['textures'] = original_textures_cache

    def test_get_categories_all_all_types_missing_in_cache_returns_empty_list(self):
        DB['polyhaven_categories_cache'] = {}  # All type keys missing
        result = get_polyhaven_categories(asset_type="all")
        self.assertEqual(result, [], "Should return empty list for 'all' if all type keys are missing in cache.")

    def test_get_categories_all_all_types_empty_lists_in_cache_returns_empty_list(self):
        DB['polyhaven_categories_cache']['hdris'] = []
        DB['polyhaven_categories_cache']['textures'] = []
        DB['polyhaven_categories_cache']['models'] = []
        result = get_polyhaven_categories(asset_type="all")
        self.assertEqual(result, [], "Should return empty list for 'all' if all category lists are empty.")

    def test_get_categories_polyhaven_cache_itself_missing_returns_empty_lists(self):
        original_cache = DB.pop('polyhaven_categories_cache')

        result_hdris = get_polyhaven_categories(asset_type="hdris")
        self.assertEqual(result_hdris, [], "Should return empty list for 'hdris' if cache dict is missing.")

        result_all = get_polyhaven_categories(asset_type="all")
        self.assertEqual(result_all, [], "Should return empty list for 'all' if cache dict is missing.")

        DB['polyhaven_categories_cache'] = original_cache  # Restore

    def test_get_categories_invalid_asset_type_string_raises_invalidassettypeerror(self):
        valid_types = [e.value for e in PolyhavenAssetTypeSearchable]
        self.assert_error_behavior(
            func_to_call=get_polyhaven_categories,
            expected_exception_type=InvalidAssetTypeError,
            expected_message=f"Invalid asset_type 'unknown_type'. Must be one of {valid_types}.",
            asset_type="unknown_type"
        )

    def test_get_categories_empty_string_asset_type_raises_invalidassettypeerror(self):
        valid_types = [e.value for e in PolyhavenAssetTypeSearchable]
        self.assert_error_behavior(
            func_to_call=get_polyhaven_categories,
            expected_exception_type=InvalidAssetTypeError,
            expected_message=f"Invalid asset_type ''. Must be one of {valid_types}.",
            asset_type=""
        )

    def test_get_categories_invalid_asset_type_int_raises_pydantic_validationerror(self):
        self.assert_error_behavior(
            func_to_call=get_polyhaven_categories,
            expected_exception_type=InvalidAssetTypeError,
            expected_message="Input should be a valid string",
            asset_type=123
        )

    def test_get_categories_invalid_asset_type_none_raises_pydantic_validationerror(self):
        self.assert_error_behavior(
            func_to_call=get_polyhaven_categories,
            expected_exception_type=InvalidAssetTypeError,
            expected_message="Input should be a valid string",
            asset_type=None
        )

    def test_get_categories_all_with_no_shared_categories(self):
        DB['polyhaven_categories_cache'] = {
            "hdris": ["AlphaHdri", "BravoHdri"],
            "textures": ["CharlieTexture", "DeltaTexture"],
            "models": ["EchoModel", "FoxtrotModel"]
        }
        expected = sorted(["AlphaHdri", "BravoHdri", "CharlieTexture", "DeltaTexture", "EchoModel", "FoxtrotModel"])
        result = get_polyhaven_categories(asset_type="all")
        self.assertEqual(result, expected, "Should correctly combine unique categories when none are shared.")

    def test_get_categories_all_complex_shared_categories_and_sorting(self):
        DB['polyhaven_categories_cache'] = {
            "hdris": ["Zulu", "Alpha", "Common1", "UniqueHdri"],
            "textures": ["Bravo", "Common1", "Common2", "UniqueTexture"],
            "models": ["Charlie", "Common2", "Alpha", "UniqueModel"]  # Alpha is shared with HDRIs
        }

        all_cats_set = set()
        all_cats_set.update(DB['polyhaven_categories_cache']['hdris'])
        all_cats_set.update(DB['polyhaven_categories_cache']['textures'])
        all_cats_set.update(DB['polyhaven_categories_cache']['models'])
        expected = sorted(list(all_cats_set))

        result = get_polyhaven_categories(asset_type="all")
        self.assertEqual(result, expected, "Should handle complex sharing and provide a sorted unique list.")

class TestSearchPolyhavenAssets(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['polyhaven_assets_db'] = {}
        DB['polyhaven_service_status'] = {'is_enabled': True, 'message': 'Polyhaven integration is enabled.'}
        DB['polyhaven_categories_cache'] = {}
        DB['current_scene'] = {'name': 'Scene', 'id': 'default_scene_id', 'objects': {}, 'active_camera_name': None, 'world_settings': {'ambient_color': [0.05, 0.05, 0.05], 'horizon_color': [0.5, 0.5, 0.5], 'environment_texture_polyhaven_id': None, 'environment_texture_strength': 1.0}, 'render_settings': {'engine': 'CYCLES', 'resolution_x': 1920, 'resolution_y': 1080, 'resolution_percentage': 100, 'filepath': '/tmp/render_####.png'}}
        DB['materials'] = {}
        DB['hyper3d_service_status'] = {'is_enabled': True, 'mode': 'MAIN_SITE', 'message': 'Hyper3D enabled.'}
        DB['hyper3d_jobs'] = {}
        DB['execution_logs'] = []
        self._setup_test_assets()

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _setup_test_assets(self):
        DB['polyhaven_assets_db'] = {'hdri_001': create_asset('hdri_001', 'Sunrise Sky', 'hdri', ['sky', 'sunrise', 'outdoor'], 'Photographer A', ['1k', '2k', '4k'], ['hdr', 'exr']), 'texture_001': create_asset('texture_001', 'Oak Wood', 'texture', ['wood', 'nature', 'material'], 'Artist B', ['1k', '2k'], ['jpg', 'png']), 'model_001': create_asset('model_001', 'Robot Character', 'model', ['character', 'sci-fi', 'robot'], None, ['low', 'high'], ['gltf', 'fbx']), 'hdri_002': create_asset('hdri_002', 'Night Forest', 'hdri', ['forest', 'night', 'outdoor', 'nature'], 'Photographer A', ['2k', '8k'], ['hdr']), 'texture_002': create_asset('texture_002', 'Rusty Metal', 'texture', ['metal', 'rust', 'industrial'], 'Artist C', ['1k', '4k'], ['png']), 'model_002': create_asset('model_002', 'Sports Car', 'model', ['vehicle', 'car', 'sport'], 'Artist B', ['standard'], ['blend', 'fbx']), 'texture_003': create_asset('texture_003', 'Cotton Fabric', 'texture', ['fabric', 'pattern', 'textile'], None, ['512', '1k'], ['jpg']), 'hdri_003': create_asset('hdri_003', 'Studio Light', 'hdri', ['indoor', 'studio', 'light'], 'Photographer C', ['1k', '16k'], ['exr']), 'model_003_no_tags': create_asset('model_003_no_tags', 'Untagged Model', 'model', [], 'Artist D', ['1k'], ['gltf']), 'texture_004_specific_tag': create_asset('texture_004_specific_tag', 'Old Pine Wood', 'texture', ['wood', 'old wood', 'pine'], 'Artist B', ['2k'], ['png'])}

    def _assert_search_results(self, results, expected_asset_ids):
        self.assertIsInstance(results, list, 'Results should be a list.')
        returned_asset_ids = sorted([r['asset_id'] for r in results])
        expected_asset_ids_sorted = sorted(list(expected_asset_ids))
        self.assertEqual(len(results), len(expected_asset_ids_sorted), f'Expected {len(expected_asset_ids_sorted)} results, got {len(results)}. Expected IDs: {expected_asset_ids_sorted}, Got IDs: {returned_asset_ids}')
        self.assertListEqual(returned_asset_ids, expected_asset_ids_sorted, 'Mismatch in asset IDs returned.')
        for asset_dict in results:
            self.assertIsInstance(asset_dict, dict, f"Asset {asset_dict.get('asset_id')} should be a dict.")
            original_asset = DB['polyhaven_assets_db'].get(asset_dict.get('asset_id'))
            self.assertIsNotNone(original_asset, f"Asset ID {asset_dict.get('asset_id')} not found in DB for verification.")
            expected_keys = {'asset_id', 'name', 'type', 'tags', 'author', 'resolution_options', 'file_format_options'}
            self.assertSetEqual(set(asset_dict.keys()), expected_keys, f"Asset {asset_dict['asset_id']} has unexpected or missing keys. Expected: {expected_keys}, Got: {set(asset_dict.keys())}")
            self.assertEqual(asset_dict['asset_id'], original_asset['asset_id'])
            self.assertEqual(asset_dict['name'], original_asset['name'])
            self.assertEqual(asset_dict['type'], original_asset['type'])
            self.assertListEqual(sorted(asset_dict['tags']), sorted(original_asset['tags']))
            self.assertEqual(asset_dict['author'], original_asset['author'])
            self.assertListEqual(sorted(asset_dict['resolution_options']), sorted(original_asset['resolution_options']))
            self.assertListEqual(sorted(asset_dict['file_format_options']), sorted(original_asset['file_format_options']))

    def test_search_all_assets_no_categories(self):
        results = search_polyhaven_assets(asset_type='all', categories=None)
        all_asset_ids = list(DB['polyhaven_assets_db'].keys())
        self._assert_search_results(results, all_asset_ids)

    def test_search_default_asset_type_no_categories(self):
        results = search_polyhaven_assets(categories=None)
        all_asset_ids = list(DB['polyhaven_assets_db'].keys())
        self._assert_search_results(results, all_asset_ids)

    def test_search_hdris_no_categories(self):
        results = search_polyhaven_assets(asset_type='hdris')
        expected_ids = ['hdri_001', 'hdri_002', 'hdri_003']
        self._assert_search_results(results, expected_ids)

    def test_search_textures_no_categories(self):
        results = search_polyhaven_assets(asset_type='textures')
        expected_ids = ['texture_001', 'texture_002', 'texture_003', 'texture_004_specific_tag']
        self._assert_search_results(results, expected_ids)

    def test_search_models_no_categories(self):
        results = search_polyhaven_assets(asset_type='models')
        expected_ids = ['model_001', 'model_002', 'model_003_no_tags']
        self._assert_search_results(results, expected_ids)

    def test_search_all_types_single_category_nature(self):
        results = search_polyhaven_assets(asset_type='all', categories='nature')
        expected_ids = ['texture_001', 'hdri_002']
        self._assert_search_results(results, expected_ids)

    def test_search_hdris_single_category_outdoor(self):
        results = search_polyhaven_assets(asset_type='hdris', categories='outdoor')
        expected_ids = ['hdri_001', 'hdri_002']
        self._assert_search_results(results, expected_ids)

    def test_search_textures_multiple_categories_or_logic(self):
        results = search_polyhaven_assets(asset_type='textures', categories='wood,metal')
        expected_ids = ['texture_001', 'texture_002', 'texture_004_specific_tag']
        self._assert_search_results(results, expected_ids)

    def test_search_models_multiple_categories_one_matches(self):
        results = search_polyhaven_assets(asset_type='models', categories='robot,fruit')
        expected_ids = ['model_001']
        self._assert_search_results(results, expected_ids)

    def test_search_categories_with_leading_trailing_spaces(self):
        results = search_polyhaven_assets(asset_type='all', categories='  sky ,  nature  ')
        expected_ids = ['hdri_001', 'texture_001', 'hdri_002']
        self._assert_search_results(results, expected_ids)

    def test_search_categories_with_internal_spaces_and_empty_parts(self):
        results = search_polyhaven_assets(asset_type='all', categories='sky ,, nature, , outdoor ')
        expected_ids = ['hdri_001', 'hdri_002', 'texture_001']
        self._assert_search_results(results, expected_ids)

    def test_search_category_exact_match_behavior(self):
        results_wood = search_polyhaven_assets(asset_type='textures', categories='wood')
        expected_ids_wood = ['texture_001', 'texture_004_specific_tag']
        self._assert_search_results(results_wood, expected_ids_wood)
        results_old_wood = search_polyhaven_assets(asset_type='textures', categories='old wood')
        expected_ids_old_wood = ['texture_004_specific_tag']
        self._assert_search_results(results_old_wood, expected_ids_old_wood)

    def test_search_category_case_sensitive_match(self):
        results_sky_upper = search_polyhaven_assets(asset_type='hdris', categories='SKY')
        self._assert_search_results(results_sky_upper, [])
        results_sky_lower = search_polyhaven_assets(asset_type='hdris', categories='sky')
        expected_ids_sky_lower = ['hdri_001']
        self._assert_search_results(results_sky_lower, expected_ids_sky_lower)

    def test_search_empty_polyhaven_assets_db(self):
        DB['polyhaven_assets_db'].clear()
        results = search_polyhaven_assets(asset_type='all')
        self._assert_search_results(results, [])

    def test_search_asset_type_valid_but_no_assets_of_type_in_db(self):
        model_ids_to_remove = [k for k, v in DB['polyhaven_assets_db'].items() if v['type'] == 'model']
        original_models = {mid: DB['polyhaven_assets_db'].pop(mid) for mid in model_ids_to_remove}
        results = search_polyhaven_assets(asset_type='models')
        self._assert_search_results(results, [])
        DB['polyhaven_assets_db'].update(original_models)

    def test_search_category_matches_no_assets(self):
        results = search_polyhaven_assets(asset_type='all', categories='nonexistent_category_xyz123')
        self._assert_search_results(results, [])

    def test_search_asset_with_empty_tags_list_no_category_filter(self):
        results = search_polyhaven_assets(asset_type='models', categories=None)
        self.assertTrue(any((r['asset_id'] == 'model_003_no_tags' for r in results)), 'Model with no tags not found when no category filter applied.')

    def test_search_asset_with_empty_tags_list_with_category_filter(self):
        results = search_polyhaven_assets(asset_type='models', categories='any_tag_filter')
        self.assertFalse(any((r['asset_id'] == 'model_003_no_tags' for r in results)), 'Model with no tags found when category filter applied.')

    def test_search_categories_empty_string_acts_as_no_filter(self):
        results = search_polyhaven_assets(asset_type='all', categories='')
        all_asset_ids = list(DB['polyhaven_assets_db'].keys())
        self._assert_search_results(results, all_asset_ids)

    def test_search_categories_whitespace_string_acts_as_no_filter(self):
        results = search_polyhaven_assets(asset_type='all', categories='   ')
        all_asset_ids = list(DB['polyhaven_assets_db'].keys())
        self._assert_search_results(results, all_asset_ids)

    def test_search_categories_commas_only_string_acts_as_no_filter(self):
        results = search_polyhaven_assets(asset_type='all', categories=' ,, , ')
        all_asset_ids = list(DB['polyhaven_assets_db'].keys())
        self._assert_search_results(results, all_asset_ids)

    def test_search_invalid_asset_type_string_value(self):
        self.assert_error_behavior(func_to_call=search_polyhaven_assets, expected_exception_type=InvalidInputError, expected_message="Invalid asset_type: 'badtype'. Must be one of ['all', 'hdris', 'textures', 'models'].", asset_type='badtype')

    def test_search_invalid_asset_type_is_integer(self):
        self.assert_error_behavior(func_to_call=search_polyhaven_assets, expected_exception_type=InvalidInputError, expected_message='Asset type must be a string.', asset_type=123)

    def test_search_categories_invalid_type_is_integer(self):
        self.assert_error_behavior(func_to_call=search_polyhaven_assets, expected_exception_type=InvalidInputError, expected_message='Categories parameter must be a string if provided.', categories=12345)

    def test_search_categories_invalid_type_is_list(self):
        self.assert_error_behavior(func_to_call=search_polyhaven_assets, expected_exception_type=InvalidInputError, expected_message='Categories parameter must be a string if provided.', categories=['sky', 'nature'])

    @patch("blender.polyhaven.SearchPolyhavenAssetsArguments")
    def test_asset_type_unknown_pydantic_error_type_fallback(self, MockSearchPolyhavenModel):
        asset_type_input_value = "unrecognized_asset_type_value"
        pydantic_detail_message = "A non-standard Pydantic error occurred."
        desired_errors_output = [{
            'type': 'exotic_pydantic_error',
            'loc': ('asset_type',),
            'msg': pydantic_detail_message,
            'input': asset_type_input_value,
            'ctx': None
        }]

        exception_to_raise = None
        try:
            exception_to_raise = PydanticValidationError("TestModelTitle", [], "python")
        except TypeError as e_init:
            self.fail(
                f"Failed to instantiate '{type(PydanticValidationError).__name__}' directly with positional arguments "
                f"(title, [], 'python'). Error: {e_init}. "
                f"This Pydantic environment ({PydanticValidationError.__module__}) is proving very difficult for "
                f"programmatic ValidationError creation. Consider resolving the Pydantic setup to provide "
                f"the standard pydantic.errors.ValidationError Python wrapper."
            )
            return

        exception_to_raise.errors = MagicMock(return_value=desired_errors_output)
        
        MockSearchPolyhavenModel.side_effect = exception_to_raise

        # --- Rest of your test logic ---
        expected_msg = f"Invalid asset_type: {asset_type_input_value}. Details: {pydantic_detail_message}"
        self.assert_error_behavior(
            func_to_call=search_polyhaven_assets,
            expected_exception_type=InvalidInputError,
            expected_message=expected_msg,
            asset_type=asset_type_input_value,
            categories=None
        )

    @patch("blender.polyhaven.SearchPolyhavenAssetsArguments") # Ensure this is the correct patch target
    def test_asset_type_value_error_missing_ctx_fallback(self, MockSearchPolyhavenModel):
        custom_pydantic_message = "Asset type has a value error without context."
        asset_type_input_for_error = "some_input_that_caused_value_error"
        desired_errors_output = [{
            'type': 'value_error',
            'loc': ('asset_type',),
            'msg': custom_pydantic_message,
            'input': asset_type_input_for_error
        }]

        exception_to_raise = None
        try:
            exception_to_raise = PydanticValidationError("TestModelTitle", [], "python")
        except TypeError as e_init:
            self.fail(f"Failed to instantiate PydanticValidationError with positional args: {e_init}")
            return
            
        exception_to_raise.errors = MagicMock(return_value=desired_errors_output)
        MockSearchPolyhavenModel.side_effect = exception_to_raise
            
        self.assert_error_behavior(
            func_to_call=search_polyhaven_assets,
            expected_exception_type=InvalidInputError,
            expected_message=custom_pydantic_message,
            asset_type=asset_type_input_for_error,
            categories=None
        )

    @patch("blender.polyhaven.SearchPolyhavenAssetsArguments")
    def test_categories_unknown_pydantic_error_type_fallback(self, MockSearchPolyhavenModel):
        categories_input_value = "unrecognized_categories_value"
        pydantic_detail_message = "Another non-standard Pydantic error for categories."
        desired_errors_output = [{
            'type': 'super_rare_pydantic_error',
            'loc': ('categories',),
            'msg': pydantic_detail_message,
            'input': categories_input_value,
            'ctx': None
        }]
        
        exception_to_raise = None
        try:
            exception_to_raise = PydanticValidationError("TestModelTitle", [], "python")
        except TypeError as e_init:
            self.fail(f"Failed to instantiate PydanticValidationError: {e_init}")
            return

        exception_to_raise.errors = MagicMock(return_value=desired_errors_output)
        MockSearchPolyhavenModel.side_effect = exception_to_raise

        expected_msg = f"Invalid categories parameter: {categories_input_value}. Details: {pydantic_detail_message}"
        self.assert_error_behavior(
            func_to_call=search_polyhaven_assets,
            expected_exception_type=InvalidInputError,
            expected_message=expected_msg,
            asset_type='all',
            categories=categories_input_value
        )

    @patch("blender.polyhaven.SearchPolyhavenAssetsArguments")
    def test_categories_value_error_missing_ctx_fallback(self, MockSearchPolyhavenModel):
        custom_pydantic_message = "Categories parameter has a value error without context."
        categories_input_for_error = "some_category_input_for_value_error"
        desired_errors_output = [{
            'type': 'value_error',
            'loc': ('categories',),
            'msg': custom_pydantic_message,
            'input': categories_input_for_error
            # NO 'ctx' key here
        }]
        
        exception_to_raise = None
        try:
            exception_to_raise = PydanticValidationError("TestModelTitle", [], "python")
        except TypeError as e_init:
            self.fail(f"Failed to instantiate PydanticValidationError with positional args: {e_init}")
            return

        exception_to_raise.errors = MagicMock(return_value=desired_errors_output)
        MockSearchPolyhavenModel.side_effect = exception_to_raise
            
        self.assert_error_behavior(
            func_to_call=search_polyhaven_assets,
            expected_exception_type=InvalidInputError,
            expected_message=custom_pydantic_message,
            asset_type='all',
            categories=categories_input_for_error
        )

class TestDownloadPolyhavenAsset(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['polyhaven_service_status'] = {'is_enabled': True, 'message': 'Polyhaven integration is enabled.'}
        self.hdri_asset_id = 'sunset_sky'
        self.texture_asset_id = 'wood_planks'
        self.model_asset_id = 'modern_chair'
        self.texture_import_fail_id = 'marble_texture_dup'
        self.asset_no_1k_res_id = 'special_hdri_no_1k'
        self.asset_empty_formats_id = 'texture_no_formats'
        self.asset_empty_resolutions_id = 'model_no_resolutions'
        DB['polyhaven_assets_db'] = {
            self.hdri_asset_id: {'asset_id': self.hdri_asset_id, 'name': 'Sunset Sky', 'type': 'hdri',
                                 'tags': ['sky', 'outdoor', 'sunset'], 'author': 'PH Team',
                                 'resolution_options': ['1k', '2k', '4k', '8k'], 'file_format_options': ['hdr'],
                                 'is_downloaded': False, 'downloaded_resolution': None, 'downloaded_file_format': None,
                                 'local_file_path': None, 'blender_name': None, 'imported_as_blender_object_id': None,
                                 'imported_as_blender_material_id': None, 'imported_as_world_environment': False},
            self.texture_asset_id: {'asset_id': self.texture_asset_id, 'name': 'Wood Planks', 'type': 'texture',
                                    'tags': ['wood', 'floor', 'pbr'], 'author': 'PH Team',
                                    'resolution_options': ['1k', '2k', '4k'], 'file_format_options': ['jpg', 'png'],
                                    'is_downloaded': False, 'downloaded_resolution': None,
                                    'downloaded_file_format': None, 'local_file_path': None, 'blender_name': None,
                                    'imported_as_blender_object_id': None, 'imported_as_blender_material_id': None,
                                    'imported_as_world_environment': False},
            self.model_asset_id: {'asset_id': self.model_asset_id, 'name': 'Modern Chair', 'type': 'model',
                                  'tags': ['furniture', 'chair', 'modern'], 'author': 'PH Team',
                                  'resolution_options': ['1k', '2k'], 'file_format_options': ['gltf', 'fbx'],
                                  'is_downloaded': False, 'downloaded_resolution': None, 'downloaded_file_format': None,
                                  'local_file_path': None, 'blender_name': None, 'imported_as_blender_object_id': None,
                                  'imported_as_blender_material_id': None, 'imported_as_world_environment': False},
            self.texture_import_fail_id: {'asset_id': self.texture_import_fail_id, 'name': 'Marble Texture DupName',
                                          'type': 'texture', 'tags': ['marble', 'stone'], 'author': 'PH Team',
                                          'resolution_options': ['1k'], 'file_format_options': ['jpg'],
                                          'is_downloaded': False, 'downloaded_resolution': None,
                                          'downloaded_file_format': None, 'local_file_path': None, 'blender_name': None,
                                          'imported_as_blender_object_id': None,
                                          'imported_as_blender_material_id': None,
                                          'imported_as_world_environment': False},
            self.asset_no_1k_res_id: {'asset_id': self.asset_no_1k_res_id, 'name': 'Special HDRI No 1k', 'type': 'hdri',
                                      'resolution_options': ['2k', '4k'], 'file_format_options': ['hdr'],
                                      'is_downloaded': False, 'downloaded_resolution': None,
                                      'downloaded_file_format': None, 'local_file_path': None, 'blender_name': None,
                                      'imported_as_blender_object_id': None, 'imported_as_blender_material_id': None,
                                      'imported_as_world_environment': False},
            self.asset_empty_formats_id: {'asset_id': self.asset_empty_formats_id, 'name': 'Texture No Formats',
                                          'type': 'texture', 'resolution_options': ['1k'], 'file_format_options': [],
                                          'is_downloaded': False, 'downloaded_resolution': None,
                                          'downloaded_file_format': None, 'local_file_path': None, 'blender_name': None,
                                          'imported_as_blender_object_id': None,
                                          'imported_as_blender_material_id': None,
                                          'imported_as_world_environment': False},
            self.asset_empty_resolutions_id: {'asset_id': self.asset_empty_resolutions_id,
                                              'name': 'Model No Resolutions', 'type': 'model', 'resolution_options': [],
                                              'file_format_options': ['gltf'], 'is_downloaded': False,
                                              'downloaded_resolution': None, 'downloaded_file_format': None,
                                              'local_file_path': None, 'blender_name': None,
                                              'imported_as_blender_object_id': None,
                                              'imported_as_blender_material_id': None,
                                              'imported_as_world_environment': False}}
        DB['current_scene'] = {'id': str(uuid.uuid4()), 'name': 'TestScene', 'objects': {}, 'active_camera_name': None,
                               'world_settings': {'ambient_color': [0.05, 0.05, 0.05], 'horizon_color': [0.5, 0.5, 0.5],
                                                  'environment_texture_polyhaven_id': None,
                                                  'environment_texture_strength': 1.0},
                               'render_settings': {'resolution_x': 1920, 'resolution_y': 1080}}
        DB['materials'] = {}
        colliding_material_name = 'PH Marble Texture DupName (marble_texture_dup) Material'
        DB['materials'][colliding_material_name] = {'id': str(uuid.uuid4()), 'name': colliding_material_name,
                                                    'base_color_value': [0.1, 0.1, 0.1],
                                                    'base_color_texture_polyhaven_id': None, 'metallic': 0.0,
                                                    'roughness': 0.5}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _check_success_return_structure(self, result, expected_blender_name_part, expected_file_path_suffix):
        self.assertEqual(result['status'], 'success')
        self.assertIsInstance(result['message'], str)
        self.assertTrue(len(result['message']) > 0)
        self.assertIn(expected_blender_name_part, result['asset_name_in_blender'])
        self.assertIsInstance(result['file_path'], str)
        self.assertTrue(result['file_path'].endswith(expected_file_path_suffix),
                        f"Expected file_path to end with '{expected_file_path_suffix}', but got '{result['file_path']}'")

    def _check_db_asset_downloaded_state(self, asset_id, resolution, file_format, blender_name_part, is_world_env=False,
                                         is_material=False, is_object=False):
        asset_info = DB['polyhaven_assets_db'][asset_id]
        self.assertTrue(asset_info['is_downloaded'])
        self.assertEqual(asset_info['downloaded_resolution'], resolution)
        self.assertEqual(asset_info['downloaded_file_format'], file_format)
        self.assertIsNotNone(asset_info['local_file_path'])
        expected_file_suffix = f'{asset_id}_{resolution}.{file_format}'
        self.assertTrue(asset_info['local_file_path'].endswith(expected_file_suffix),
                        f"Expected local_file_path to end with '{expected_file_suffix}', but got '{asset_info['local_file_path']}'")
        self.assertIsNotNone(asset_info['blender_name'])
        self.assertIn(blender_name_part, asset_info['blender_name'])
        if is_world_env:
            self.assertTrue(asset_info['imported_as_world_environment'])
            self.assertIsNone(asset_info['imported_as_blender_material_id'])
            self.assertIsNone(asset_info['imported_as_blender_object_id'])
        if is_material:
            self.assertIsNotNone(asset_info['imported_as_blender_material_id'])
            self.assertIsInstance(asset_info['imported_as_blender_material_id'], str)
            self.assertFalse(asset_info['imported_as_world_environment'])
            self.assertIsNone(asset_info['imported_as_blender_object_id'])
        if is_object:
            self.assertIsNotNone(asset_info['imported_as_blender_object_id'])
            self.assertIsInstance(asset_info['imported_as_blender_object_id'], str)
            self.assertFalse(asset_info['imported_as_world_environment'])
            self.assertIsNone(asset_info['imported_as_blender_material_id'])

    def test_download_hdri_success_specific_res_format(self):
        resolution = '2k'
        file_format = 'hdr'
        result = download_polyhaven_asset(self.hdri_asset_id, 'hdris', resolution=resolution, file_format=file_format)
        self._check_success_return_structure(result, 'Sunset Sky', f'{self.hdri_asset_id}_{resolution}.{file_format}')
        self._check_db_asset_downloaded_state(self.hdri_asset_id, resolution, file_format, 'Sunset Sky',
                                              is_world_env=True)
        self.assertEqual(DB['current_scene']['world_settings']['environment_texture_polyhaven_id'], self.hdri_asset_id)
        self.assertEqual(DB['polyhaven_assets_db'][self.hdri_asset_id]['blender_name'], result['asset_name_in_blender'])

    def test_download_hdri_success_default_res_no_format(self):
        expected_resolution = '1k'
        expected_format = 'hdr'
        result = download_polyhaven_asset(self.hdri_asset_id, 'hdris')
        self._check_success_return_structure(result, 'Sunset Sky',
                                             f'{self.hdri_asset_id}_{expected_resolution}.{expected_format}')
        self._check_db_asset_downloaded_state(self.hdri_asset_id, expected_resolution, expected_format, 'Sunset Sky',
                                              is_world_env=True)
        self.assertEqual(DB['current_scene']['world_settings']['environment_texture_polyhaven_id'], self.hdri_asset_id)

    def test_download_texture_success_specific_res_format(self):
        resolution = '4k'
        file_format = 'png'
        result = download_polyhaven_asset(self.texture_asset_id, 'textures', resolution=resolution,
                                          file_format=file_format)
        self._check_success_return_structure(result, 'Wood Planks',
                                             f'{self.texture_asset_id}_{resolution}.{file_format}')
        self._check_db_asset_downloaded_state(self.texture_asset_id, resolution, file_format, 'Wood Planks',
                                              is_material=True)
        material_name = result['asset_name_in_blender']
        self.assertIn(material_name, DB['materials'])
        material_data = DB['materials'][material_name]
        self.assertEqual(material_data['base_color_texture_polyhaven_id'], self.texture_asset_id)
        self.assertEqual(DB['polyhaven_assets_db'][self.texture_asset_id]['blender_name'], material_name)
        self.assertEqual(DB['polyhaven_assets_db'][self.texture_asset_id]['imported_as_blender_material_id'],
                         material_data['id'])

    def test_download_texture_success_default_res_no_format(self):
        expected_resolution = '1k'
        expected_format = 'jpg'
        result = download_polyhaven_asset(self.texture_asset_id, 'textures')
        self._check_success_return_structure(result, 'Wood Planks',
                                             f'{self.texture_asset_id}_{expected_resolution}.{expected_format}')
        self._check_db_asset_downloaded_state(self.texture_asset_id, expected_resolution, expected_format,
                                              'Wood Planks', is_material=True)
        material_name = result['asset_name_in_blender']
        self.assertIn(material_name, DB['materials'])
        self.assertEqual(DB['materials'][material_name]['base_color_texture_polyhaven_id'], self.texture_asset_id)

    def test_download_model_success_specific_res_format(self):
        resolution = '2k'
        file_format = 'fbx'
        result = download_polyhaven_asset(self.model_asset_id, 'models', resolution=resolution, file_format=file_format)
        self._check_success_return_structure(result, 'Modern Chair',
                                             f'{self.model_asset_id}_{resolution}.{file_format}')
        self._check_db_asset_downloaded_state(self.model_asset_id, resolution, file_format, 'Modern Chair',
                                              is_object=True)
        object_name = result['asset_name_in_blender']
        self.assertIn(object_name, DB['current_scene']['objects'])
        object_data = DB['current_scene']['objects'][object_name]
        self.assertEqual(object_data['type'], 'MESH')
        self.assertEqual(DB['polyhaven_assets_db'][self.model_asset_id]['blender_name'], object_name)
        self.assertEqual(DB['polyhaven_assets_db'][self.model_asset_id]['imported_as_blender_object_id'],
                         object_data['id'])

    def test_download_model_success_default_res_no_format(self):
        expected_resolution = '1k'
        expected_format = 'gltf'
        result = download_polyhaven_asset(self.model_asset_id, 'models')
        self._check_success_return_structure(result, 'Modern Chair',
                                             f'{self.model_asset_id}_{expected_resolution}.{expected_format}')
        self._check_db_asset_downloaded_state(self.model_asset_id, expected_resolution, expected_format, 'Modern Chair',
                                              is_object=True)
        object_name = result['asset_name_in_blender']
        self.assertIn(object_name, DB['current_scene']['objects'])

    def test_asset_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=download_polyhaven_asset,
            expected_exception_type=custom_errors.AssetNotFoundError,
            expected_message="Polyhaven asset 'non_existent_asset' not found.",
            asset_id='non_existent_asset', asset_type='hdris')

    def test_invalid_input_error_invalid_asset_type_arg(self):
        self.assert_error_behavior(
            func_to_call=download_polyhaven_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Invalid asset_type provided: 'invalid_type'. Must be one of ['hdris', 'textures', 'models'].",
            asset_id=self.hdri_asset_id, asset_type='invalid_type')

    def test_invalid_input_error_asset_type_mismatch_in_db(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=f"Asset '{self.hdri_asset_id}' is of type 'hdri', not 'textures'.",
                                   asset_id=self.hdri_asset_id, asset_type='textures')

    def test_invalid_input_error_resolution_not_available(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=f"Resolution '16k' not available for asset '{self.hdri_asset_id}'. Available: ['1k', '2k', '4k', '8k'].",
                                   asset_id=self.hdri_asset_id, asset_type='hdris', resolution='16k')

    def test_invalid_input_error_default_resolution_not_available(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=f"Default resolution '1k' not available for asset '{self.asset_no_1k_res_id}'. Available: ['2k', '4k'].",
                                   asset_id=self.asset_no_1k_res_id, asset_type='hdris')

    def test_invalid_input_error_file_format_not_available(self):
        self.assert_error_behavior(
            func_to_call=download_polyhaven_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"File format 'exr' not available for asset '{self.hdri_asset_id}' (type 'hdri'). Available: ['hdr'].",
            asset_id=self.hdri_asset_id, asset_type='hdris', file_format='exr')

    def test_invalid_input_error_file_format_is_invalid(self):
        self.assert_error_behavior(
            func_to_call=download_polyhaven_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"File format 'tiff' is not compatible with asset type 'hdris'.",
            asset_id=self.hdri_asset_id, asset_type='hdris', file_format='tiff')

    def test_invalid_input_error_file_format_incompatible_with_asset_type(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=f"File format 'gltf' is not compatible with asset type 'hdris'.",
                                   asset_id=self.hdri_asset_id, asset_type='hdris', file_format='gltf')

    def test_invalid_input_error_no_default_file_format_choosable(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=f"Cannot determine default file format for asset '{self.asset_empty_formats_id}' (type 'texture') as no formats are listed.",
                                   asset_id=self.asset_empty_formats_id, asset_type='textures', file_format=None)

    def test_invalid_input_error_no_resolutions_available(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.InvalidInputError,
                                   expected_message=f"Resolution '1k' not available for asset '{self.asset_empty_resolutions_id}'. No resolutions listed.",
                                   asset_id=self.asset_empty_resolutions_id, asset_type='models', resolution='1k')

    def test_download_error_service_disabled(self):
        DB['polyhaven_service_status']['is_enabled'] = False
        DB['polyhaven_service_status']['message'] = 'Service is offline for maintenance.'
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.DownloadError,
                                   expected_message='Polyhaven download failed: Service is offline for maintenance.',
                                   asset_id=self.hdri_asset_id, asset_type='hdris')

    def test_blender_import_error_name_collision_for_material(self):
        expected_colliding_blender_name = 'PH Marble Texture DupName (marble_texture_dup) Material'
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.BlenderImportError,
                                   expected_message=f"Failed to import asset into Blender: Material '{expected_colliding_blender_name}' could not be created or updated due to a name conflict or other import issue.",
                                   asset_id=self.texture_import_fail_id, asset_type='textures', resolution='1k',
                                   file_format='jpg')
        asset_info = DB['polyhaven_assets_db'][self.texture_import_fail_id]
        self.assertTrue(asset_info['is_downloaded'])
        self.assertEqual(asset_info['downloaded_resolution'], '1k')
        self.assertEqual(asset_info['downloaded_file_format'], 'jpg')
        self.assertIsNotNone(asset_info['local_file_path'])
        self.assertIsNone(asset_info['blender_name'])
        self.assertIsNone(asset_info['imported_as_blender_material_id'])
        self.assertFalse(asset_info['imported_as_world_environment'])

    def test_validation_error_asset_id_not_string(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.ValidationError,
                                   expected_message='Input should be a valid string', asset_id=123, asset_type='hdris')

    def test_validation_error_asset_type_not_string(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.ValidationError,
                                   expected_message='Input should be a valid string', asset_id=self.hdri_asset_id,
                                   asset_type=None)

    def test_validation_error_resolution_not_string(self):
        self.assert_error_behavior(
            func_to_call=download_polyhaven_asset,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Input should be a valid string',
            asset_id=self.hdri_asset_id, asset_type='hdris', resolution=1000)

    def test_validation_error_file_format_not_string_if_provided(self):
        self.assert_error_behavior(func_to_call=download_polyhaven_asset,
                                   expected_exception_type=custom_errors.ValidationError,
                                   expected_message='Input should be a valid string', asset_id=self.hdri_asset_id,
                                   asset_type='hdris', file_format=['hdr'])

class TestGetPolyhavenStatus(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # Initialize DB with a default structure, focusing on polyhaven_service_status
        # but also providing other top-level keys from BlenderDB schema for robustness.
        DB['polyhaven_service_status'] = {
            'is_enabled': True,
            'message': "Polyhaven integration is enabled by default in setup."
        }

        DB['current_scene'] = {
            'id': str(uuid.uuid4()),
            'name': "Scene",
            'objects': {},
            'active_camera_name': None,
            'world_settings': {
                'ambient_color': [0.05, 0.05, 0.05],
                'horizon_color': [0.5, 0.5, 0.5],
                'environment_texture_polyhaven_id': None,
                'environment_texture_strength': 1.0
            },
            'render_settings': {
                'engine': "CYCLES",
                'resolution_x': 1920,
                'resolution_y': 1080,
                'resolution_percentage': 100,
                'filepath': "/tmp/render_####.png"
            }
        }
        DB['materials'] = {}
        DB['polyhaven_categories_cache'] = {
            "hdris": [],
            "textures": [],
            "models": [],
            "all": []
        }
        DB['polyhaven_assets_db'] = {}
        DB['hyper3d_service_status'] = {
            'is_enabled': True,
            'mode': "MAIN_SITE",
            'message': "Hyper3D Rodin integration is enabled."
        }
        DB['hyper3d_jobs'] = {}
        DB['execution_logs'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_polyhaven_enabled_by_default_setup(self):
        """
        Tests retrieving status when Polyhaven is enabled as per default setUp.
        """
        # DB is set up with enabled status in self.setUp
        expected_status = {
            'is_enabled': True,
            'message': "Polyhaven integration is enabled by default in setup."
        }
        result = get_polyhaven_status()
        self.assertEqual(result, expected_status)

    def test_polyhaven_explicitly_enabled_different_message(self):
        """
        Tests retrieving status when Polyhaven is enabled with a custom message.
        """
        DB['polyhaven_service_status'] = {
            'is_enabled': True,
            'message': "PolyHaven is active and ready for awesome assets!"
        }
        expected_status = {
            'is_enabled': True,
            'message': "PolyHaven is active and ready for awesome assets!"
        }
        result = get_polyhaven_status()
        self.assertEqual(result, expected_status)

    def test_polyhaven_explicitly_disabled(self):
        """
        Tests retrieving status when Polyhaven is disabled.
        """
        DB['polyhaven_service_status'] = {
            'is_enabled': False,
            'message': "PolyHaven integration is currently disabled by the user."
        }
        expected_status = {
            'is_enabled': False,
            'message': "PolyHaven integration is currently disabled by the user."
        }
        result = get_polyhaven_status()
        self.assertEqual(result, expected_status)

    def test_polyhaven_status_message_can_be_empty_when_enabled(self):
        """
        Tests that an empty message is handled correctly when enabled.
        """
        DB['polyhaven_service_status'] = {
            'is_enabled': True,
            'message': ""  # Empty message
        }
        expected_status = {
            'is_enabled': True,
            'message': ""
        }
        result = get_polyhaven_status()
        self.assertEqual(result, expected_status)

    def test_polyhaven_status_message_can_be_empty_when_disabled(self):
        """
        Tests that an empty message is handled correctly when disabled.
        """
        DB['polyhaven_service_status'] = {
            'is_enabled': False,
            'message': ""  # Empty message
        }
        expected_status = {
            'is_enabled': False,
            'message': ""
        }
        result = get_polyhaven_status()
        self.assertEqual(result, expected_status)

    def test_polyhaven_status_message_can_be_long(self):
        """
        Tests that a long message is handled correctly.
        """
        long_message = "This is an exceptionally long and detailed message concerning the operational status of the PolyHaven integration features. It confirms that all subsystems are nominal, connectivity is established, and the asset library is synchronized. Users can expect full functionality."
        DB['polyhaven_service_status'] = {
            'is_enabled': True,
            'message': long_message
        }
        expected_status = {
            'is_enabled': True,
            'message': long_message
        }
        result = get_polyhaven_status()
        self.assertEqual(result, expected_status)

    def test_return_value_is_a_copy_not_direct_db_reference(self):
        """
        Ensures that the returned dictionary is a copy and modifying it
        does not affect the original DB state. This is important for data integrity.
        """
        original_status_in_db = copy.deepcopy(DB['polyhaven_service_status'])

        result = get_polyhaven_status()

        self.assertIsNot(result, DB['polyhaven_service_status'],
                         "Returned dictionary should be a copy, not the DB object itself.")

        # Modify the returned dictionary
        result['is_enabled'] = not result['is_enabled']  # Flip the boolean
        result['message'] = "This message was modified in the test result."

        # Check that the DB state remains unchanged by comparing with the deepcopy made earlier
        self.assertEqual(DB['polyhaven_service_status'], original_status_in_db,
                         "Modifying the returned dictionary should not alter the DB state.")

        # Explicitly check original values in DB to be super sure
        self.assertEqual(DB['polyhaven_service_status']['is_enabled'], original_status_in_db['is_enabled'],
                         "DB 'is_enabled' should remain unchanged after modifying result.")
        self.assertEqual(DB['polyhaven_service_status']['message'], original_status_in_db['message'],
                         "DB 'message' should remain unchanged after modifying result.")

    def test_polyhaven_status_not_configured_in_db(self):
        """
        Tests that an error is raised when Polyhaven status is not configured in DB.
        """
        DB.clear()
        self.assert_error_behavior(
            func_to_call=get_polyhaven_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Polyhaven service status not configured in DB."
        )

    def test_polyhaven_status_missing_is_enabled_key(self):
        """
        Tests that an error is raised when Polyhaven status is missing the 'is_enabled' key.
        """
        DB['polyhaven_service_status'] = {
            'message': "Polyhaven integration is enabled by default in setup."
        }
        self.assert_error_behavior(
            func_to_call=get_polyhaven_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Polyhaven service status is missing 'is_enabled' key."
        )
        
    def test_polyhaven_status_missing_message_key(self):
        """
        Tests that an error is raised when Polyhaven status is missing the 'message' key.
        """
        DB['polyhaven_service_status'] = {
            'is_enabled': True
        }
        self.assert_error_behavior(
            func_to_call=get_polyhaven_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Polyhaven service status is missing 'message' key."
        )

if __name__ == '__main__':
    unittest.main()
