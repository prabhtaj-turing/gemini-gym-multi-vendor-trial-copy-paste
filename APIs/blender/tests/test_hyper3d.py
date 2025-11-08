"""
Test suite for Hyper3D Rodin integration functionalities in the Blender API simulation.
"""
import copy
import unittest
from unittest.mock import patch
import uuid
from typing import Optional, Any

from blender.SimulationEngine import custom_errors, utils
from blender.SimulationEngine.db import DB
from blender.SimulationEngine.utils import add_job_to_db
from blender.hyper3d import (generate_hyper3d_model_via_images, get_hyper3d_status, poll_rodin_job_status,
                             generate_hyper3d_model_via_text, import_generated_asset)
from common_utils.base_case import BaseTestCaseWithErrorHandler



class TestGetHyper3DStatus(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            'current_scene': {
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
                    'engine': 'CYCLES',  # Corresponds to RenderEngineType.CYCLES.value
                    'resolution_x': 1920,
                    'resolution_y': 1080,
                    'resolution_percentage': 100,
                    'filepath': "/tmp/render_####.png"
                }
            },
            'materials': {},
            'polyhaven_service_status': {
                'is_enabled': True,
                'message': "Polyhaven integration is enabled."
            },
            'polyhaven_categories_cache': {},
            'polyhaven_assets_db': {},
            'hyper3d_jobs': {},
            'execution_logs': []
        })
        DB['hyper3d_service_status'] = {
            'is_enabled': True,
            'mode': 'MAIN_SITE',  # Corresponds to Hyper3DMode.MAIN_SITE.value
            'message': "Hyper3D Rodin integration is enabled."
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_hyper3d_enabled_main_site_mode(self):
        DB['hyper3d_service_status'] = {
            'is_enabled': True,
            'mode': 'MAIN_SITE',
            'message': 'Rodin is active in MAIN_SITE mode.'
        }
        expected_status = {
            'is_enabled': True,
            'mode': 'MAIN_SITE',
            'message': 'Rodin is active in MAIN_SITE mode.'
        }
        status = get_hyper3d_status()
        self.assertEqual(status, expected_status)

    def test_hyper3d_enabled_fal_ai_mode(self):
        DB['hyper3d_service_status'] = {
            'is_enabled': True,
            'mode': 'FAL_AI',
            'message': 'Rodin is active in FAL_AI mode.'
        }
        expected_status = {
            'is_enabled': True,
            'mode': 'FAL_AI',
            'message': 'Rodin is active in FAL_AI mode.'
        }
        status = get_hyper3d_status()
        self.assertEqual(status, expected_status)

    def test_hyper3d_disabled_with_a_mode_set_returns_stored_mode(self):
        DB['hyper3d_service_status'] = {
            'is_enabled': False,
            'mode': 'MAIN_SITE',
            'message': 'Hyper3D Rodin integration is disabled (mode was MAIN_SITE).'
        }
        # The function should return the mode as stored, as Hyper3DServiceStatusModel
        # does not enforce mode=None if is_enabled=False.
        expected_status = {
            'is_enabled': False,
            'mode': 'MAIN_SITE',
            'message': 'Hyper3D Rodin integration is disabled (mode was MAIN_SITE).'
        }
        status = get_hyper3d_status()
        self.assertEqual(status, expected_status)

    def test_hyper3d_status_key_entirely_missing_raises_blendererror(self):
        del DB['hyper3d_service_status']

        self.assert_error_behavior(
            func_to_call=get_hyper3d_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Hyper3D service status not configured in DB."
        )

    def test_hyper3d_status_is_none_raises_blendererror(self):
        DB['hyper3d_service_status'] = None
        self.assert_error_behavior(
            func_to_call=get_hyper3d_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Hyper3D status configuration is missing 'is_enabled' key."
        )

    def test_hyper3d_status_is_list_raises_blendererror(self):
        DB['hyper3d_service_status'] = []  # Not a dictionary
        self.assert_error_behavior(
            func_to_call=get_hyper3d_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Hyper3D status configuration is missing 'is_enabled' key."
        )

    def test_hyper3d_status_empty_dict_raises_blendererror_for_missing_is_enabled(self):
        DB['hyper3d_service_status'] = {}
        self.assert_error_behavior(
            func_to_call=get_hyper3d_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Hyper3D status configuration is missing 'is_enabled' key."
        )

    def test_hyper3d_status_missing_is_enabled_key_raises_blendererror(self):
        DB['hyper3d_service_status'] = {
            # 'is_enabled': True, # Missing
            'mode': 'MAIN_SITE',
            'message': 'Configured for MAIN_SITE'
        }
        self.assert_error_behavior(
            func_to_call=get_hyper3d_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Hyper3D status configuration is missing 'is_enabled' key."
        )

    def test_hyper3d_status_missing_message_key_raises_blendererror(self):
        DB['hyper3d_service_status'] = {
            'is_enabled': True,
            'mode': 'MAIN_SITE',
            # 'message': 'Configured for MAIN_SITE' # Missing
        }
        self.assert_error_behavior(
            func_to_call=get_hyper3d_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Hyper3D status configuration is missing 'message' key."
        )

    def test_hyper3d_status_invalid_mode_value_raises_blendererror(self):
        DB['hyper3d_service_status'] = {
            'is_enabled': True,
            'mode': 'INVALID_MODE_VALUE',
            'message': 'Testing invalid mode value.'
        }
        self.assert_error_behavior(
            func_to_call=get_hyper3d_status,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid value for 'mode' in Hyper3D status configuration."
        )

class TestGenerateHyper3DModelViaText(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({'current_scene': {'id': str(uuid.uuid4()), 'name': 'Scene', 'objects': {}, 'active_camera_name': None, 'world_settings': {'ambient_color': [0.05, 0.05, 0.05], 'horizon_color': [0.5, 0.5, 0.5], 'environment_texture_polyhaven_id': None, 'environment_texture_strength': 1.0}, 'render_settings': {'engine': 'CYCLES', 'resolution_x': 1920, 'resolution_y': 1080, 'resolution_percentage': 100, 'filepath': '/tmp/render_####.png'}}, 'materials': {}, 'polyhaven_service_status': {'is_enabled': True, 'message': 'Polyhaven integration is enabled.'}, 'polyhaven_categories_cache': {}, 'polyhaven_assets_db': {}, 'hyper3d_service_status': {'is_enabled': True, 'mode': 'MAIN_SITE', 'message': 'Hyper3D Rodin integration is enabled.'}, 'hyper3d_jobs': {}, 'execution_logs': []})

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_success_main_site_no_bbox(self):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        text_prompt = 'a red shiny cube'
        result = generate_hyper3d_model_via_text(text_prompt=text_prompt)
        self.assertEqual(result['status'], 'success_queued')
        self.assertTrue(isinstance(result['message'], str) and 'successfully queued' in result['message'])
        self.assertIn('MAIN_SITE', result['message'])
        self.assertIsInstance(result['task_uuid'], str)
        self.assertTrue(len(result['task_uuid']) > 0)
        self.assertIsInstance(result['subscription_key'], str)
        self.assertTrue(len(result['subscription_key']) > 0)
        self.assertIsNone(result['request_id'])
        self.assertEqual(len(DB['hyper3d_jobs']), 1)
        job_id_uuid = list(DB['hyper3d_jobs'].keys())[0]
        self.assertIsInstance(job_id_uuid, uuid.UUID)
        job_data = DB['hyper3d_jobs'][job_id_uuid]
        self.assertEqual(job_data['mode_at_creation'], 'MAIN_SITE')
        self.assertEqual(job_data['text_prompt'], text_prompt)
        self.assertIsNone(job_data['bbox_condition'])
        self.assertEqual(job_data['submission_status'], 'success_queued')
        self.assertEqual(job_data['task_uuid'], result['task_uuid'])
        self.assertEqual(job_data['subscription_key'], result['subscription_key'])
        self.assertIsNone(job_data['request_id'])
        self.assertEqual(job_data['poll_overall_status'], 'PENDING')
        self.assertIsInstance(job_data['internal_job_id'], str)
        self.assertEqual(job_data['internal_job_id'], str(job_id_uuid))

    def test_success_main_site_with_bbox(self):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        text_prompt = 'a tall green vase'
        bbox_condition = [0.5, 0.5, 2.0]
        result = generate_hyper3d_model_via_text(text_prompt=text_prompt, bbox_condition=bbox_condition)
        self.assertEqual(result['status'], 'success_queued')
        self.assertIsInstance(result['task_uuid'], str)
        self.assertTrue(len(result['task_uuid']) > 0)
        self.assertIsInstance(result['subscription_key'], str)
        self.assertTrue(len(result['subscription_key']) > 0)
        self.assertIsNone(result['request_id'])
        self.assertEqual(len(DB['hyper3d_jobs']), 1)
        job_id_uuid = list(DB['hyper3d_jobs'].keys())[0]
        job_data = DB['hyper3d_jobs'][job_id_uuid]
        self.assertEqual(job_data['mode_at_creation'], 'MAIN_SITE')
        self.assertEqual(job_data['text_prompt'], text_prompt)
        self.assertEqual(job_data['bbox_condition'], bbox_condition)
        self.assertEqual(job_data['task_uuid'], result['task_uuid'])
        self.assertEqual(job_data['subscription_key'], result['subscription_key'])

    def test_success_fal_ai_no_bbox(self):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        text_prompt = 'a futuristic blue car'
        result = generate_hyper3d_model_via_text(text_prompt=text_prompt)
        self.assertEqual(result['status'], 'success_queued')
        self.assertTrue(isinstance(result['message'], str) and 'successfully queued' in result['message'])
        self.assertIn('FAL_AI', result['message'])
        self.assertIsInstance(result['request_id'], str)
        self.assertTrue(len(result['request_id']) > 0)
        self.assertIsNone(result['task_uuid'])
        self.assertIsNone(result['subscription_key'])
        self.assertEqual(len(DB['hyper3d_jobs']), 1)
        job_id_uuid = list(DB['hyper3d_jobs'].keys())[0]
        job_data = DB['hyper3d_jobs'][job_id_uuid]
        self.assertEqual(job_data['mode_at_creation'], 'FAL_AI')
        self.assertEqual(job_data['text_prompt'], text_prompt)
        self.assertIsNone(job_data['bbox_condition'])
        self.assertEqual(job_data['submission_status'], 'success_queued')
        self.assertEqual(job_data['request_id'], result['request_id'])
        self.assertIsNone(job_data['task_uuid'])
        self.assertIsNone(job_data['subscription_key'])
        self.assertEqual(job_data['poll_overall_status'], 'PENDING')
        self.assertEqual(job_data['internal_job_id'], str(job_id_uuid))

    def test_success_fal_ai_with_bbox(self):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        text_prompt = 'a small wooden chest'
        bbox_condition = [1.0, 0.8, 0.6]
        result = generate_hyper3d_model_via_text(text_prompt=text_prompt, bbox_condition=bbox_condition)
        self.assertEqual(result['status'], 'success_queued')
        self.assertIsInstance(result['request_id'], str)
        self.assertTrue(len(result['request_id']) > 0)
        self.assertIsNone(result['task_uuid'])
        self.assertIsNone(result['subscription_key'])
        self.assertEqual(len(DB['hyper3d_jobs']), 1)
        job_id_uuid = list(DB['hyper3d_jobs'].keys())[0]
        job_data = DB['hyper3d_jobs'][job_id_uuid]
        self.assertEqual(job_data['mode_at_creation'], 'FAL_AI')
        self.assertEqual(job_data['text_prompt'], text_prompt)
        self.assertEqual(job_data['bbox_condition'], bbox_condition)
        self.assertEqual(job_data['request_id'], result['request_id'])

    def test_error_hyper3d_not_enabled_service_flag_disabled(self):
        DB['hyper3d_service_status']['is_enabled'] = False
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.ObjectNotFoundError,
            expected_message='Hyper3D Rodin integration is not enabled or not configured correctly.',
            text_prompt='a test prompt for disabled service'
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_hyper3d_not_enabled_mode_is_none(self):
        DB['hyper3d_service_status']['mode'] = None
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Encountered an unsupported Hyper3D mode: None.',
            text_prompt='a test prompt for None mode'
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_hyper3d_not_enabled_mode_invalid_string(self):
        DB['hyper3d_service_status']['mode'] = 'INVALID_MODE_STRING'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Encountered an unsupported Hyper3D mode: INVALID_MODE_STRING.',
            text_prompt='a test prompt for invalid mode string'
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_hyper3d_not_enabled_status_key_missing(self):
        del DB['hyper3d_service_status']
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.ObjectNotFoundError,
            expected_message='Hyper3D Rodin integration is not enabled or not configured correctly.',
            text_prompt='a test prompt for missing status key'
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_invalid_input_empty_prompt(self):
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Text prompt cannot be empty.',
            text_prompt=''
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_invalid_input_bbox_wrong_length_too_short(self):
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='bbox_condition must be a list of 3 floats.',
            text_prompt='valid prompt',
            bbox_condition=[1.0, 2.0]
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_invalid_input_bbox_wrong_length_too_long(self):
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='bbox_condition must be a list of 3 floats.',
            text_prompt='valid prompt',
            bbox_condition=[1.0, 2.0, 3.0, 4.0]
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_validation_text_prompt_not_string(self):
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Input validation failed: text_prompt must be a string.',
            text_prompt=12345
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_validation_bbox_condition_not_list_nor_none(self):
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Input validation failed: bbox_condition must be a list of floats or None.',
            text_prompt='valid prompt',
            bbox_condition='not-a-list'
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    def test_error_validation_bbox_condition_list_contains_non_float(self):
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Input validation failed: bbox_condition items must all be floats.',
            text_prompt='valid prompt',
            bbox_condition=[1.0, 'not-a-float', 3.0]
        )
        self.assertEqual(len(DB['hyper3d_jobs']), 0)

    @patch('blender.SimulationEngine.models.Hyper3DJobModel', side_effect=Exception("Simulated model error"))
    def test_error_hyper3djobmodel_raises_hyper3dapierror(self, mock_hyper3djobmodel):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        DB['hyper3d_jobs'] = {}
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_text,
            expected_exception_type=custom_errors.Hyper3DAPIError,
            expected_message="Failed to create a valid job data structure for Hyper3D task. Details: Simulated model error",
            text_prompt='valid prompt'
        )


class TestGenerateHyper3DModelViaImages(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['hyper3d_service_status'] = {'is_enabled': True, 'mode': 'MAIN_SITE', 'message': 'Hyper3D Rodin integration is enabled.'}
        DB['hyper3d_jobs'] = {}
        DB['current_scene'] = {'name': 'Scene', 'id': str(uuid.uuid4()), 'objects': {}, 'active_camera_name': None, 'world_settings': {'ambient_color': [0.05, 0.05, 0.05], 'horizon_color': [0.5, 0.5, 0.5], 'environment_texture_polyhaven_id': None, 'environment_texture_strength': 1.0}, 'render_settings': {'engine': 'CYCLES', 'resolution_x': 1920, 'resolution_y': 1080, 'resolution_percentage': 100, 'filepath': '/tmp/render_####.png'}}
        DB['materials'] = {}
        DB['polyhaven_service_status'] = {'is_enabled': True, 'message': 'Polyhaven enabled.'}
        DB['polyhaven_categories_cache'] = {}
        DB['polyhaven_assets_db'] = {}
        DB['execution_logs'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_hyper3d_not_enabled(self):
        DB['hyper3d_service_status']['is_enabled'] = False
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.ObjectNotFoundError,
            expected_message='Hyper3D Rodin configuration is missing or invalid.',
            input_image_paths=['/path/to/image.jpg']
        )

    def test_hyper3d_mode_not_configured(self):
        DB['hyper3d_service_status']['mode'] = None
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Encountered an unsupported Hyper3D mode: None.',
            input_image_paths=['/path/to/image.jpg']
        )

    def test_both_image_inputs_provided(self):
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Only one of `input_image_paths` or `input_image_urls` should be provided.',
            input_image_paths=['/path/to/image.jpg'],
            input_image_urls=['http://example.com/image.jpg']
        )

    def test_no_image_inputs_provided_main_site_mode(self):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`input_image_paths` is required for MAIN_SITE mode.',
            input_image_paths=None
        )

    def test_no_image_inputs_provided_fal_ai_mode(self):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`input_image_urls` is required for FAL_AI mode.',
            input_image_urls=None
        )

    def test_image_paths_provided_for_fal_ai_mode(self):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`input_image_paths` should not be provided in FAL_AI mode. Use `input_image_urls` instead.',
            input_image_paths=['/path/to/image.jpg']
        )

    def test_image_urls_provided_for_main_site_mode(self):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`input_image_urls` should not be provided in MAIN_SITE mode. Use `input_image_paths` instead.',
            input_image_urls=['http://example.com/image.jpg']
        )

    def test_input_image_paths_not_a_list(self):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images, 
            expected_exception_type=custom_errors.InvalidInputError, 
            expected_message='`input_image_paths` must be a list of strings.', 
            input_image_paths='/path/to/image.jpg'
        )

    def test_input_image_paths_empty_list(self):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`input_image_paths` cannot be an empty list.',
            input_image_paths=[]
        )

    def test_input_image_paths_list_with_non_string(self):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='All items in `input_image_paths` must be strings.',
            input_image_paths=['/path/to/image.jpg', 123]
        )

    def test_input_image_urls_not_a_list(self):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`input_image_urls` must be a list of strings.',
            input_image_urls='http://example.com/image.jpg'
        )

    def test_input_image_urls_empty_list(self):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`input_image_urls` cannot be an empty list.',
            input_image_urls=[]
        )

    def test_input_image_urls_list_with_non_string(self):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='All items in `input_image_urls` must be strings.',
            input_image_urls=['http://example.com/image.jpg', 123]
        )

    @patch('os.path.exists', return_value=True)
    def test_bbox_condition_not_a_list(self, mock_exists):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`bbox_condition` must be a list of 3 integers.',
            input_image_paths=['/path.jpg'],
            bbox_condition='1,2,3'
        )

    @patch('os.path.exists', return_value=True)
    def test_bbox_condition_wrong_length(self, mock_exists):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='`bbox_condition` must be a list of 3 integers.',
            input_image_paths=['/path.jpg'],
            bbox_condition=[1, 2]
        )

    @patch('os.path.exists', return_value=True)
    def test_bbox_condition_invalid_type_in_list(self, mock_exists):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='All items in `bbox_condition` must be integers.',
            input_image_paths=['/path.jpg'],
            bbox_condition=[1, 2, 'a']
        )
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='All items in `bbox_condition` must be integers.',
            input_image_paths=['/path.jpg'],
            bbox_condition=[1, 2, 3.0]
        )

    @patch('os.path.exists')
    def test_input_image_path_not_found(self, mock_os_path_exists):
        mock_os_path_exists.return_value = False
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=FileNotFoundError,
            expected_message="Input image path '/fake/path.jpg' not found.",
            input_image_paths=['/fake/path.jpg']
        )
        mock_os_path_exists.assert_called_once_with('/fake/path.jpg')

    @patch('os.path.exists')
    def test_one_of_multiple_input_image_paths_not_found(self, mock_os_path_exists):

        def side_effect_path_exists(path):
            if path == '/exists.jpg':
                return True
            if path == '/not_exists.jpg':
                return False
            return False
        mock_os_path_exists.side_effect = side_effect_path_exists
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        self.assert_error_behavior(
            func_to_call=generate_hyper3d_model_via_images,
            expected_exception_type=FileNotFoundError,
            expected_message="Input image path '/not_exists.jpg' not found.",
            input_image_paths=['/exists.jpg', '/not_exists.jpg']
        )
        self.assertIn(unittest.mock.call('/exists.jpg'), mock_os_path_exists.call_args_list)
        self.assertIn(unittest.mock.call('/not_exists.jpg'), mock_os_path_exists.call_args_list)

    @patch('os.path.exists', return_value=True)
    @patch('uuid.uuid4')
    def test_success_main_site_mode_with_paths(self, mock_uuid4, mock_os_path_exists):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        mock_job_id = uuid.UUID('12345678-1234-5678-1234-567812345678')
        mock_task_uuid = uuid.UUID('abcdef01-abcd-ef01-abcd-ef0123456789')
        mock_subscription_key = uuid.UUID('00000000-0000-0000-0000-000000000000')
        mock_uuid4.side_effect = [mock_job_id, mock_task_uuid, mock_subscription_key]
        image_paths = ['/path/image1.jpg', '/path/image2.jpg']
        result = generate_hyper3d_model_via_images(input_image_paths=image_paths)
        self.assertEqual(result['status'], 'success_queued')
        self.assertTrue(result['message'].startswith('Hyper3D model generation task successfully submitted.'))
        self.assertEqual(result['task_uuid'], str(mock_task_uuid))
        self.assertEqual(result['subscription_key'], str(mock_subscription_key))
        self.assertIsNone(result.get('request_id'))
        self.assertEqual(len(DB['hyper3d_jobs']), 1)
        job_details = DB['hyper3d_jobs'][str(mock_job_id)]
        self.assertEqual(job_details['internal_job_id'], mock_job_id)
        self.assertEqual(job_details['mode_at_creation'], 'MAIN_SITE')
        self.assertEqual(job_details['input_image_paths'], image_paths)
        self.assertIsNone(job_details['input_image_urls'])
        self.assertIsNone(job_details['bbox_condition'])
        self.assertEqual(job_details['submission_status'], 'success_queued')
        self.assertEqual(job_details['task_uuid'], str(mock_task_uuid))
        self.assertEqual(job_details['subscription_key'], str(mock_subscription_key))
        self.assertEqual(job_details['poll_overall_status'], 'PENDING')

    @patch('os.path.exists', return_value=True)
    @patch('uuid.uuid4')
    def test_success_main_site_mode_with_paths_and_bbox(self, mock_uuid4, mock_os_path_exists):
        DB['hyper3d_service_status']['mode'] = 'MAIN_SITE'
        mock_job_id = uuid.UUID('12345678-1234-5678-1234-567812345678')
        mock_task_uuid = uuid.UUID('abcdef01-abcd-ef01-abcd-ef0123456789')
        mock_subscription_key = uuid.UUID('00000000-0000-0000-0000-000000000000')
        mock_uuid4.side_effect = [mock_job_id, mock_task_uuid, mock_subscription_key]
        image_paths = ['/path/image1.jpg']
        bbox_int = [10, 20, 30]
        bbox_float = [10.0, 20.0, 30.0]
        result = generate_hyper3d_model_via_images(input_image_paths=image_paths, bbox_condition=bbox_int)
        self.assertEqual(result['status'], 'success_queued')
        self.assertEqual(result['task_uuid'], str(mock_task_uuid))
        job_details = DB['hyper3d_jobs'][str(mock_job_id)]
        self.assertEqual(job_details['input_image_paths'], image_paths)
        self.assertEqual(job_details['bbox_condition'], bbox_float)

    @patch('uuid.uuid4')
    def test_success_fal_ai_mode_with_urls(self, mock_uuid4):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        mock_job_id = uuid.UUID('87654321-4321-8765-4321-876543210987')
        mock_request_id = uuid.UUID('fedcba98-fedc-ba98-fedc-ba9876543210')
        mock_uuid4.side_effect = [mock_job_id, mock_request_id]
        image_urls = ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
        result = generate_hyper3d_model_via_images(input_image_urls=image_urls)
        self.assertEqual(result['status'], 'success_queued')
        self.assertTrue(result['message'].startswith('Hyper3D model generation task successfully submitted'))
        self.assertEqual(result['request_id'], str(mock_request_id))
        self.assertIsNone(result.get('task_uuid'))
        self.assertIsNone(result.get('subscription_key'))
        self.assertEqual(len(DB['hyper3d_jobs']), 1)
        job_details = DB['hyper3d_jobs'][str(mock_job_id)]
        self.assertEqual(job_details['internal_job_id'], mock_job_id)
        self.assertEqual(job_details['mode_at_creation'], 'FAL_AI')
        self.assertEqual(job_details['input_image_urls'], image_urls)
        self.assertIsNone(job_details['input_image_paths'])
        self.assertIsNone(job_details['bbox_condition'])
        self.assertEqual(job_details['submission_status'], 'success_queued')
        self.assertEqual(job_details['request_id'], str(mock_request_id))
        self.assertEqual(job_details['poll_overall_status'], 'PENDING')

    @patch('uuid.uuid4')
    def test_success_fal_ai_mode_with_urls_and_bbox(self, mock_uuid4):
        DB['hyper3d_service_status']['mode'] = 'FAL_AI'
        mock_job_id = uuid.UUID('87654321-4321-8765-4321-876543210987')
        mock_request_id = uuid.UUID('fedcba98-fedc-ba98-fedc-ba9876543210')
        mock_uuid4.side_effect = [mock_job_id, mock_request_id]
        image_urls = ['http://example.com/image1.jpg']
        bbox_int = [15, 25, 35]
        bbox_float = [15.0, 25.0, 35.0]
        result = generate_hyper3d_model_via_images(input_image_urls=image_urls, bbox_condition=bbox_int)
        self.assertEqual(result['status'], 'success_queued')
        self.assertEqual(result['request_id'], str(mock_request_id))
        job_details = DB['hyper3d_jobs'][str(mock_job_id)]
        self.assertEqual(job_details['input_image_urls'], image_urls)
        self.assertEqual(job_details['bbox_condition'], bbox_float)



class TestPollRodinJobStatus(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['hyper3d_jobs'] = {}
        self.fal_ai_job_id_str = 'fal_ai_job_id_str'
        self.main_site_sub_key = 'main_site_sub_key'
        self.fal_ai_req_id = 'fal_ai_req_id'
        self.main_site_job_id_str = 'main_site_job_id_str'

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_poll_no_identifier_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Neither subscription_key (for MAIN_SITE mode) nor request_id (for FAL_AI mode) was provided.'
        )

    def test_poll_both_identifiers_provided_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Both subscription_key and request_id were provided. Please provide only one.',
            subscription_key='some_key',
            request_id='some_id'
        )

    def test_poll_empty_subscription_key_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Subscription key provided is invalid.',
            subscription_key=''
        )

    def test_poll_empty_request_id_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Request ID provided is invalid.',
            request_id=''
        )

    def test_poll_main_site_job_not_found_raises_job_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Job not found for subscription_key '{self.main_site_sub_key}' or mode mismatch.",
            subscription_key=self.main_site_sub_key
        )

    def test_poll_fal_ai_job_not_found_raises_job_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Job not found for request_id '{self.fal_ai_req_id}' or mode mismatch.",
            request_id=self.fal_ai_req_id
        )

    def test_poll_main_site_key_for_fal_ai_job_raises_job_not_found_error(self):
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', subscription_key=self.main_site_sub_key, request_id=self.fal_ai_req_id)
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Job not found for subscription_key '{self.main_site_sub_key}' or mode mismatch.",
            subscription_key=self.main_site_sub_key
        )

    def test_poll_fal_ai_id_for_main_site_job_raises_job_not_found_error(self):
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, request_id=self.fal_ai_req_id)
        self.assert_error_behavior(
            func_to_call=poll_rodin_job_status,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Job not found for request_id '{self.fal_ai_req_id}' or mode mismatch.",
            request_id=self.fal_ai_req_id
        )

    def test_poll_main_site_all_done_returns_completed(self):
        details = ['Done', 'Done', 'Done']
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=details, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'COMPLETED')
        self.assertTrue(response['is_completed'])
        self.assertTrue(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) completed successfully.')
        self.assertEqual(response['details'], details)

    def test_poll_main_site_processing_returns_in_progress(self):
        details = ['Processing', 'Queued']
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=details, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'IN_PROGRESS')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) is still in progress.')
        self.assertEqual(response['details'], details)

    def test_poll_main_site_mixed_done_processing_returns_in_progress(self):
        details = ['Done', 'Processing', 'Done']
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=details, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'IN_PROGRESS')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) is still in progress.')
        self.assertEqual(response['details'], details)

    def test_poll_main_site_empty_details_returns_pending(self):
        details = []
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=details, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'PENDING')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) is pending as task details are unavailable.')
        self.assertEqual(response['details'], details)

    def test_poll_main_site_none_details_returns_pending(self):
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=None, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'PENDING')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) is pending as task details are unavailable.')
        self.assertIsNone(response['details'])

    def test_poll_main_site_one_failed_returns_failed(self):
        details = ['Done', 'Failed', 'Processing']
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=details, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'FAILED')
        self.assertTrue(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) failed.')
        self.assertEqual(response['details'], details)

    def test_poll_main_site_one_canceled_returns_canceled(self):
        details = ['Done', 'Canceled']
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=details, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'CANCELED')
        self.assertTrue(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) was canceled.')
        self.assertEqual(response['details'], details)

    def test_poll_main_site_unknown_status_treated_as_in_progress(self):
        details = ['Done', 'WeirdStatus']
        add_job_to_db(internal_job_id=self.main_site_job_id_str, mode_at_creation='MAIN_SITE', subscription_key=self.main_site_sub_key, poll_details_specific=details, task_uuid=str(uuid.uuid4()))
        response = poll_rodin_job_status(subscription_key=self.main_site_sub_key)
        self.assertEqual(response['mode_queried'], 'MAIN_SITE')
        self.assertEqual(response['overall_status'], 'IN_PROGRESS')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (MAIN_SITE) is still in progress.')
        self.assertEqual(response['details'], details)

    def test_poll_fal_ai_completed_status_returns_completed(self):
        details = 'COMPLETED'
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', request_id=self.fal_ai_req_id, poll_details_specific=details)
        response = poll_rodin_job_status(request_id=self.fal_ai_req_id)
        self.assertEqual(response['mode_queried'], 'FAL_AI')
        self.assertEqual(response['overall_status'], 'COMPLETED')
        self.assertTrue(response['is_completed'])
        self.assertTrue(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (FAL_AI) completed successfully.')
        self.assertEqual(response['details'], details)

    def test_poll_fal_ai_in_progress_status_returns_in_progress(self):
        details = 'IN_PROGRESS'
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', request_id=self.fal_ai_req_id, poll_details_specific=details)
        response = poll_rodin_job_status(request_id=self.fal_ai_req_id)
        self.assertEqual(response['mode_queried'], 'FAL_AI')
        self.assertEqual(response['overall_status'], 'IN_PROGRESS')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (FAL_AI) is in progress.')
        self.assertEqual(response['details'], details)

    def test_poll_fal_ai_in_queue_status_returns_pending(self):
        details = 'IN_QUEUE'
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', request_id=self.fal_ai_req_id, poll_details_specific=details)
        response = poll_rodin_job_status(request_id=self.fal_ai_req_id)
        self.assertEqual(response['mode_queried'], 'FAL_AI')
        self.assertEqual(response['overall_status'], 'PENDING')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (FAL_AI) is queued.')
        self.assertEqual(response['details'], details)

    def test_poll_fal_ai_none_details_returns_pending(self):
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', request_id=self.fal_ai_req_id, poll_details_specific=None)
        response = poll_rodin_job_status(request_id=self.fal_ai_req_id)
        self.assertEqual(response['mode_queried'], 'FAL_AI')
        self.assertEqual(response['overall_status'], 'PENDING')
        self.assertFalse(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (FAL_AI) is pending as status detail is unavailable.')
        self.assertIsNone(response['details'])

    def test_poll_fal_ai_failed_status_returns_failed(self):
        details = 'FAILED'
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', request_id=self.fal_ai_req_id, poll_details_specific=details)
        response = poll_rodin_job_status(request_id=self.fal_ai_req_id)
        self.assertEqual(response['mode_queried'], 'FAL_AI')
        self.assertEqual(response['overall_status'], 'FAILED')
        self.assertTrue(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (FAL_AI) failed or was canceled.')
        self.assertEqual(response['details'], details)

    def test_poll_fal_ai_custom_error_status_returns_failed(self):
        details = 'TASK_ERROR_XYZ'
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', request_id=self.fal_ai_req_id, poll_details_specific=details)
        response = poll_rodin_job_status(request_id=self.fal_ai_req_id)
        self.assertEqual(response['mode_queried'], 'FAL_AI')
        self.assertEqual(response['overall_status'], 'FAILED')
        self.assertTrue(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (FAL_AI) failed or was canceled.')
        self.assertEqual(response['details'], details)

    def test_poll_fal_ai_empty_string_details_returns_failed(self):
        details = ''
        add_job_to_db(internal_job_id=self.fal_ai_job_id_str, mode_at_creation='FAL_AI', request_id=self.fal_ai_req_id, poll_details_specific=details)
        response = poll_rodin_job_status(request_id=self.fal_ai_req_id)
        self.assertEqual(response['mode_queried'], 'FAL_AI')
        self.assertEqual(response['overall_status'], 'FAILED')
        self.assertTrue(response['is_completed'])
        self.assertFalse(response['is_successful'])
        self.assertEqual(response['message'], 'Hyper3D Rodin job (FAL_AI) failed or was canceled.')
        self.assertEqual(response['details'], details)


class TestImportGeneratedAsset(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['current_scene'] = {
            'id': str(uuid.uuid4()),
            'name': 'Scene',
            'objects': {},
            'active_camera_name': None,
            'world_settings': {
                'ambient_color': [0.05, 0.05, 0.05],
                'horizon_color': [0.5, 0.5, 0.5],
                'environment_texture_polyhaven_id': None,
                'environment_texture_strength': 1.0
            },
            'render_settings': {
                'engine': 'CYCLES',
                'resolution_x': 1920,
                'resolution_y': 1080,
                'resolution_percentage': 100,
                'filepath': "/tmp/render_####.png"
            }
        }
        DB['materials'] = {}
        DB['polyhaven_service_status'] = {'is_enabled': True, 'message': "Polyhaven integration is enabled."}
        DB['polyhaven_categories_cache'] = {}
        DB['polyhaven_assets_db'] = {}
        DB['hyper3d_service_status'] = {
            'is_enabled': True,
            'mode': 'MAIN_SITE',
            'message': 'Hyper3D Rodin integration is enabled.'
        }
        DB['hyper3d_jobs'] = {}
        DB['execution_logs'] = []

        self.main_site_job_internal_id = str(uuid.uuid4())
        self.main_site_task_uuid = f"task_{self.main_site_job_internal_id}"
        self.fal_ai_job_internal_id = str(uuid.uuid4())
        self.fal_ai_request_id = f"req_{self.fal_ai_job_internal_id}"

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_validation_error_name_is_none(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string",
            name=None,
            task_uuid=self.main_site_task_uuid
        )

    def test_invalid_input_empty_name(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Name cannot be empty.",
            name="",
            task_uuid=self.main_site_task_uuid
        )

    def test_invalid_input_no_identifier(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Either task_uuid or request_id must be provided.",
            name="TestAsset"
        )

    def test_invalid_input_both_identifiers(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Either task_uuid or request_id must be provided, but not both.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid,
            request_id=self.fal_ai_request_id
        )

    def test_invalid_input_empty_task_uuid(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Provided task_uuid cannot be empty.",
            name="TestAsset",
            task_uuid=""
        )

    def test_invalid_input_empty_request_id(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Provided request_id cannot be empty.",
            name="TestAsset",
            request_id=""
        )

    def test_job_not_found_with_task_uuid(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Job with task_uuid '{self.main_site_task_uuid}' not found.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_job_not_found_with_request_id(self):
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Job with request_id '{self.fal_ai_request_id}' not found.",
            name="TestAsset",
            request_id=self.fal_ai_request_id
        )

    def test_asset_not_ready_pending_status_main_site(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE', task_uuid=self.main_site_task_uuid,
                      status='PENDING')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.AssetNotReadyError,
            expected_message=f"Asset generation for job with task_uuid '{self.main_site_task_uuid}' is not complete. Current status: PENDING.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )
        job_in_db = DB['hyper3d_jobs'][self.main_site_job_internal_id]
        self.assertEqual(job_in_db['import_status'], 'error')
        self.assertTrue("not complete. Current status: PENDING" in job_in_db['import_message'])

    def test_asset_not_ready_in_progress_status_fal_ai(self):
        add_job_to_db(self.fal_ai_job_internal_id, mode_at_creation='FAL_AI', request_id=self.fal_ai_request_id,
                              status='IN_PROGRESS')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.AssetNotReadyError,
            expected_message=f"Asset generation for job with request_id '{self.fal_ai_request_id}' is not complete. Current status: IN_PROGRESS.",
            name="TestAsset",
            request_id=self.fal_ai_request_id
        )
        job_in_db = DB['hyper3d_jobs'][self.fal_ai_job_internal_id]
        self.assertEqual(job_in_db['import_status'], 'error')
        self.assertTrue("not complete. Current status: IN_PROGRESS" in job_in_db['import_message'])

    def test_asset_not_ready_failed_status_main_site(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE', task_uuid=self.main_site_task_uuid,
                              status='FAILED')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.AssetNotReadyError,
            expected_message=f"Asset generation for job with task_uuid '{self.main_site_task_uuid}' failed or was canceled. Current status: FAILED.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )
        job_in_db = DB['hyper3d_jobs'][self.main_site_job_internal_id]
        self.assertEqual(job_in_db['import_status'], 'error')
        self.assertTrue("failed or was canceled. Current status: FAILED" in job_in_db['import_message'])

    def test_successful_import_main_site(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE', task_uuid=self.main_site_task_uuid,
                              status='COMPLETED')
        import_name = "ImportedObjectMS"
        result = import_generated_asset(name=import_name, task_uuid=self.main_site_task_uuid)

        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['message'].startswith(f"Successfully imported asset '{import_name}'"))
        self.assertEqual(result['asset_name_in_blender'], import_name)
        self.assertEqual(result['blender_object_type'], 'MESH')

        self.assertIn(import_name, DB['current_scene']['objects'])
        imported_object = DB['current_scene']['objects'][import_name]
        self.assertEqual(imported_object['name'], import_name)
        self.assertEqual(imported_object['type'], 'MESH')
        self.assertIsNotNone(imported_object['id'])

        job_in_db = DB['hyper3d_jobs'][self.main_site_job_internal_id]
        self.assertEqual(job_in_db['import_status'], 'success')
        self.assertEqual(job_in_db['imported_blender_object_name'], import_name)
        self.assertEqual(job_in_db['imported_blender_object_id'], imported_object['id'])
        self.assertEqual(job_in_db['imported_blender_object_type'], 'MESH')

    def test_successful_import_fal_ai(self):
        add_job_to_db(self.fal_ai_job_internal_id, mode_at_creation='FAL_AI', request_id=self.fal_ai_request_id,
                              status='COMPLETED')
        import_name = "ImportedObjectFAL"
        result = import_generated_asset(name=import_name, request_id=self.fal_ai_request_id)

        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['message'].startswith(f"Successfully imported asset '{import_name}'"))
        self.assertEqual(result['asset_name_in_blender'], import_name)
        self.assertEqual(result['blender_object_type'], 'MESH')

        self.assertIn(import_name, DB['current_scene']['objects'])
        imported_object = DB['current_scene']['objects'][import_name]
        self.assertEqual(imported_object['name'], import_name)

        job_in_db = DB['hyper3d_jobs'][self.fal_ai_job_internal_id]
        self.assertEqual(job_in_db['import_status'], 'success')
        self.assertEqual(job_in_db['imported_blender_object_name'], import_name)

    def test_successful_import_name_uniquification(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE', task_uuid=self.main_site_task_uuid,
                              status='COMPLETED')
        existing_object_name = "UniqueAsset"
        DB['current_scene']['objects'][existing_object_name] = {
            'id': str(uuid.uuid4()), 'name': existing_object_name, 'type': 'EMPTY',
            'location': [0, 0, 0], 'rotation_euler': [0, 0, 0], 'scale': [1, 1, 1], 'dimensions': [1, 1, 1]
        }
        result = import_generated_asset(name=existing_object_name, task_uuid=self.main_site_task_uuid)
        expected_new_name = f"{existing_object_name}.001"
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['asset_name_in_blender'], expected_new_name)
        self.assertIn(expected_new_name, DB['current_scene']['objects'])

    def test_successful_import_name_uniquification_multiple(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE', task_uuid=self.main_site_task_uuid,
                              status='COMPLETED')
        base_name = "CollisionAsset"
        DB['current_scene']['objects'][base_name] = {
            'id': str(uuid.uuid4()), 'name': base_name, 'type': 'EMPTY',
            'location': [0, 0, 0], 'rotation_euler': [0, 0, 0], 'scale': [1, 1, 1], 'dimensions': [1, 1, 1]
        }
        DB['current_scene']['objects'][f"{base_name}.001"] = {
            'id': str(uuid.uuid4()), 'name': f"{base_name}.001", 'type': 'CAMERA',
            'location': [0, 0, 0], 'rotation_euler': [0, 0, 0], 'scale': [1, 1, 1], 'dimensions': [1, 1, 1]
        }
        result = import_generated_asset(name=base_name, task_uuid=self.main_site_task_uuid)
        expected_new_name = f"{base_name}.002"
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['asset_name_in_blender'], expected_new_name)
        self.assertIn(expected_new_name, DB['current_scene']['objects'])

    def test_blender_import_error_if_job_asset_name_is_missing(self):
        job_data = add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                                         task_uuid=self.main_site_task_uuid, status='COMPLETED')
        DB['hyper3d_jobs'][self.main_site_job_internal_id]['asset_name_for_import'] = None

        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset into Blender: Essential asset information missing from job details.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )
        job_in_db = DB['hyper3d_jobs'][self.main_site_job_internal_id]
        self.assertEqual(job_in_db['import_status'], 'error')
        self.assertTrue("Essential asset information missing" in job_in_db['import_message'])

    def test_job_found_but_mode_mismatch_task_uuid_for_fal_job(self):
        mismatched_task_uuid = "task_on_fal_job"
        add_job_to_db(self.fal_ai_job_internal_id, mode_at_creation='FAL_AI',
                              task_uuid=mismatched_task_uuid,
                              # Manually adding task_uuid to a FAL_AI mode job for this test
                              request_id=self.fal_ai_request_id, status='COMPLETED')

        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message="Job with task_uuid 'task_on_fal_job' not found.",
            name="TestAsset",
            task_uuid=mismatched_task_uuid
        )

    def test_job_found_but_mode_mismatch_request_id_for_main_site_job(self):
        mismatched_request_id = "req_on_main_site_job"
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                              task_uuid=self.main_site_task_uuid,
                              request_id=mismatched_request_id,  # Manually adding request_id to a MAIN_SITE mode job
                              status='COMPLETED')

        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Job found with request_id '{mismatched_request_id}' was created in MAIN_SITE mode, which is inconsistent for request_id identifier.",
            name="TestAsset",
            request_id=mismatched_request_id
        )

    def test_blender_import_error_no_current_scene(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        if 'current_scene' in DB:
            del DB['current_scene']
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset: No current scene is active in the system.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_blender_import_error_scene_has_no_name(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        DB['current_scene']['name'] = ""
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset: The current active scene has no name.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_blender_import_error_name_uniquification_limit(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        base_name = "LimitAsset"
        # Fill up 1000 names: base_name, base_name.001, ..., base_name.999
        for i in range(1000):
            if i == 0:
                name = base_name
            else:
                name = f"{base_name}.{i:03d}"
            DB['current_scene']['objects'][name] = {
                'id': str(uuid.uuid4()), 'name': name, 'type': 'EMPTY',
                'location': [0, 0, 0], 'rotation_euler': [0, 0, 0], 'scale': [1, 1, 1], 'dimensions': [1, 1, 1]
            }
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to generate a unique name for 'LimitAsset' in scene 'Scene' after 999 attempts. There may be too many objects with similar names.",
            name=base_name,
            task_uuid=self.main_site_task_uuid
        )

    def test_job_found_but_mode_mismatch_task_uuid_for_fal_ai_job(self):
        mismatched_task_uuid = "task_on_fal_job"
        add_job_to_db(self.fal_ai_job_internal_id, mode_at_creation='FAL_AI',
                      task_uuid=mismatched_task_uuid,
                      request_id=self.fal_ai_request_id, status='COMPLETED')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message="Job with task_uuid 'task_on_fal_job' not found.",
            name="TestAsset",
            task_uuid=mismatched_task_uuid
        )



    @patch('blender.SimulationEngine.utils.get_hyper3d_job_data_dict', side_effect=custom_errors.JobNotFoundError)
    def test_job_found_but_status_lookup_fails(self, mock_get_status):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Hyper3D job with internal ID '{self.main_site_job_internal_id}' was found but could not be retrieved for status check. Possible data inconsistency.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    @patch('blender.SimulationEngine.utils.add_object_to_scene', side_effect=custom_errors.DuplicateNameError("Duplicate name"))
    def test_add_object_to_scene_duplicate_name_error(self, mock_add):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset due to an error adding to scene: Duplicate name",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    @patch('blender.SimulationEngine.utils.add_object_to_scene', side_effect=custom_errors.SceneNotFoundError("Scene not found"))
    def test_add_object_to_scene_scene_not_found_error(self, mock_add):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset due to an error adding to scene: Scene not found",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_blender_import_error_if_job_asset_name_is_empty_string(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        DB['hyper3d_jobs'][self.main_site_job_internal_id]['asset_name_for_import'] = ""
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset into Blender: Essential asset information missing from job details.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_blender_import_error_scene_name_none(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        DB['current_scene']['name'] = None
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset: The current active scene has no name.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_blender_import_error_scene_empty_dict(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        DB['current_scene'] = {}
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.BlenderImportError,
            expected_message="Failed to import asset: No current scene is active in the system.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_job_found_but_job_dict_missing(self):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        del DB['hyper3d_jobs'][self.main_site_job_internal_id]
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.JobNotFoundError,
            expected_message=f"Job with task_uuid '{self.main_site_task_uuid}' not found.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    @patch('blender.SimulationEngine.utils.get_hyper3d_job_data_dict', return_value={'is_completed': False})
    def test_job_status_view_missing_poll_overall_status(self, mock_get_status):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='PENDING')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.AssetNotReadyError,
            expected_message=f"Asset generation for job with task_uuid '{self.main_site_task_uuid}' is not complete. Current status: UNKNOWN.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    @patch('blender.SimulationEngine.utils.get_hyper3d_job_data_dict', return_value={'poll_overall_status': 'COMPLETED'})
    def test_job_status_view_missing_is_completed(self, mock_get_status):
        add_job_to_db(self.main_site_job_internal_id, mode_at_creation='MAIN_SITE',
                      task_uuid=self.main_site_task_uuid, status='COMPLETED')
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.AssetNotReadyError,
            expected_message=f"Asset generation for job with task_uuid '{self.main_site_task_uuid}' is not complete. Current status: COMPLETED.",
            name="TestAsset",
            task_uuid=self.main_site_task_uuid
        )

    def test_invalid_input_task_uuid_mode_mismatch(self):
        # Add a job with mode_at_creation != MAIN_SITE but with a task_uuid
        task_uuid = "test-task-uuid"
        job_id = "job-with-mismatched-mode"
        DB['hyper3d_jobs'][job_id] = {
            'mode_at_creation': 'FAL_AI',  # Not MAIN_SITE
            'task_uuid': task_uuid,
            'request_id': None,
            'asset_name_for_import': "Asset",
            'poll_overall_status': "COMPLETED",
            'import_status': None,
            'import_message': None,
            'imported_blender_object_id': None,
            'imported_blender_object_name': None,
            'imported_blender_object_type': None,
        }
        self.assert_error_behavior(
            func_to_call=import_generated_asset,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Job found with task_uuid '{task_uuid}' was created in FAL_AI mode, which is inconsistent for task_uuid identifier.",
            name="TestAsset",
            task_uuid=task_uuid
        )


if __name__ == '__main__':
    unittest.main()
