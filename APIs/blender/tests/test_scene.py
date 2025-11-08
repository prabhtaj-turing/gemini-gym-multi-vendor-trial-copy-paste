"""
Test suite for scene-related functionalities in the Blender API simulation.
"""
import copy
import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from blender.SimulationEngine.db import DB
from blender.SimulationEngine import custom_errors
from blender.scene import get_scene_info


# Initial DB state for get_scene_info function tests
GET_SCENE_INFO_INITIAL_DB_STATE = {
    "current_scene": {
            'name': "DefaultTestScene",
            'objects': {
                'Cube_Mesh': {'name': 'Cube_Mesh', 'type': 'MESH'},
                'Sphere_Mesh': {'name': 'Sphere_Mesh', 'type': 'MESH'},
                'UserCamera': {'name': 'UserCamera', 'type': 'CAMERA'},
                'SunLight': {'name': 'SunLight', 'type': 'LIGHT'}
            },
            'active_camera_name': 'UserCamera',
            'world_settings': {
                'ambient_color': [0.05, 0.05, 0.05],
                'horizon_color': [0.5, 0.5, 0.5]
            },
            'render_settings': {
                'engine': 'CYCLES',
                'resolution_x': 1920,
                'resolution_y': 1080,
                'resolution_percentage': 100,
                'filepath': "/tmp/render_####.png"
            }
        }
}


class TestGetSceneInfo(BaseTestCaseWithErrorHandler):
    """
    Test suite for the get_scene_info function.
    """

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(GET_SCENE_INFO_INITIAL_DB_STATE))
        pass

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)
        pass

    def setUp(self):
        """Reset DB to initial state for each test method."""
        DB.clear()
        DB.update(copy.deepcopy(GET_SCENE_INFO_INITIAL_DB_STATE))

    def test_get_scene_info_success_with_full_data(self):
        # Uses the default setUp data
        scene_info = get_scene_info()

        expected_info = {
            'name': "DefaultTestScene",
            'camera_count': 1,
            'object_count': 4,
            'light_count': 1,
            'active_camera_name': 'UserCamera',
            'world_settings': {
                'ambient_color': [0.05, 0.05, 0.05],
                'horizon_color': [0.5, 0.5, 0.5]
            },
            'render_settings': {
                'engine': 'CYCLES',
                'resolution_x': 1920,
                'resolution_y': 1080,
                'resolution_percentage': 100,
                'filepath': "/tmp/render_####.png"
            }
        }
        self.assertEqual(scene_info, expected_info)

    def test_get_scene_info_empty_scene_objects(self):
        DB['current_scene']['objects'] = {}
        DB['current_scene']['active_camera_name'] = None # No camera, so no active camera

        scene_info = get_scene_info()

        self.assertEqual(scene_info['name'], "DefaultTestScene")
        self.assertEqual(scene_info['camera_count'], 0)
        self.assertEqual(scene_info['object_count'], 0)
        self.assertEqual(scene_info['light_count'], 0)
        self.assertIsNone(scene_info['active_camera_name'])
        self.assertEqual(scene_info['world_settings'], DB['current_scene']['world_settings'])
        self.assertEqual(scene_info['render_settings'], DB['current_scene']['render_settings'])

    def test_get_scene_info_no_active_camera(self):
        DB['current_scene']['active_camera_name'] = None
        # Ensure there's still a camera object, just not active
        DB['current_scene']['objects']['AnotherCamera'] = {'name': 'AnotherCamera', 'type': 'CAMERA'}

        scene_info = get_scene_info()

        self.assertIsNone(scene_info['active_camera_name'])
        self.assertEqual(scene_info['camera_count'], 2) # UserCamera + AnotherCamera
        self.assertEqual(scene_info['object_count'], 5)

    def test_get_scene_info_only_cameras(self):
        DB['current_scene']['objects'] = {
            'Cam1': {'name': 'Cam1', 'type': 'CAMERA'},
            'Cam2': {'name': 'Cam2', 'type': 'CAMERA'}
        }
        DB['current_scene']['active_camera_name'] = 'Cam1'

        scene_info = get_scene_info()
        self.assertEqual(scene_info['camera_count'], 2)
        self.assertEqual(scene_info['object_count'], 2)
        self.assertEqual(scene_info['light_count'], 0)
        self.assertEqual(scene_info['active_camera_name'], 'Cam1')

    def test_get_scene_info_only_lights(self):
        DB['current_scene']['objects'] = {
            'Light1': {'name': 'Light1', 'type': 'LIGHT'},
            'Light2': {'name': 'Light2', 'type': 'LIGHT'}
        }
        DB['current_scene']['active_camera_name'] = None

        scene_info = get_scene_info()
        self.assertEqual(scene_info['camera_count'], 0)
        self.assertEqual(scene_info['object_count'], 2)
        self.assertEqual(scene_info['light_count'], 2)
        self.assertIsNone(scene_info['active_camera_name'])

    def test_get_scene_info_only_mesh_objects(self):
        DB['current_scene']['objects'] = {
            'Mesh1': {'name': 'Mesh1', 'type': 'MESH'},
            'Mesh2': {'name': 'Mesh2', 'type': 'MESH'}
        }
        DB['current_scene']['active_camera_name'] = None

        scene_info = get_scene_info()
        self.assertEqual(scene_info['camera_count'], 0)
        self.assertEqual(scene_info['object_count'], 2)
        self.assertEqual(scene_info['light_count'], 0)
        self.assertIsNone(scene_info['active_camera_name'])

    def test_get_scene_info_missing_world_settings_key_in_db(self):
        del DB['current_scene']['world_settings']
        scene_info = get_scene_info()
        self.assertEqual(scene_info['world_settings'], {}) # Expect empty dict as per utils.get_scene_data_dict
        # Ensure other parts are correct
        self.assertEqual(scene_info['name'], "DefaultTestScene")
        self.assertEqual(scene_info['render_settings'], DB['current_scene']['render_settings'])

    def test_get_scene_info_empty_world_settings_dict_in_db(self):
        DB['current_scene']['world_settings'] = {}
        scene_info = get_scene_info()
        self.assertEqual(scene_info['world_settings'], {})
        self.assertEqual(scene_info['name'], "DefaultTestScene")

    def test_get_scene_info_partial_world_settings_in_db(self):
        DB['current_scene']['world_settings'] = {'ambient_color': [0.2, 0.3, 0.4]}
        scene_info = get_scene_info()
        self.assertEqual(scene_info['world_settings'], {'ambient_color': [0.2, 0.3, 0.4]})

    def test_get_scene_info_missing_render_settings_key_in_db(self):
        del DB['current_scene']['render_settings']
        scene_info = get_scene_info()
        self.assertEqual(scene_info['render_settings'], {}) # Expect empty dict
        self.assertEqual(scene_info['name'], "DefaultTestScene")
        self.assertEqual(scene_info['world_settings'], DB['current_scene']['world_settings'])

    def test_get_scene_info_empty_render_settings_dict_in_db(self):
        DB['current_scene']['render_settings'] = {}
        scene_info = get_scene_info()
        self.assertEqual(scene_info['render_settings'], {})
        self.assertEqual(scene_info['name'], "DefaultTestScene")

    def test_get_scene_info_partial_render_settings_in_db(self):
        DB['current_scene']['render_settings'] = {'engine': 'EEVEE', 'resolution_x': 800}
        scene_info = get_scene_info()
        self.assertEqual(scene_info['render_settings'], {'engine': 'EEVEE', 'resolution_x': 800})

    def test_get_scene_info_current_scene_is_minimal_dict(self):
        # Test with a scene that only has a name and empty objects, other keys missing
        DB['current_scene'] = {
            'name': "MinimalScene",
            'objects': {}
            # active_camera_name, world_settings, render_settings are missing
        }
        expected_info = {
            'name': "MinimalScene",
            'camera_count': 0,
            'object_count': 0,
            'light_count': 0,
            'active_camera_name': None, # .get('active_camera_name') will be None
            'world_settings': {},       # .get('world_settings', {}) will be {}
            'render_settings': {}       # .get('render_settings', {}) will be {}
        }
        scene_info = get_scene_info()
        self.assertEqual(scene_info, expected_info)

    def test_get_scene_info_current_scene_is_empty_dict_in_db(self):
        DB['current_scene'] = {} # Completely empty scene dict
        expected_info = {
            'name': None, # .get('name') will be None
            'camera_count': 0,
            'object_count': 0,
            'light_count': 0,
            'active_camera_name': None,
            'world_settings': {},
            'render_settings': {}
        }
        scene_info = get_scene_info()
        self.assertEqual(scene_info, expected_info)

class TestGetSceneInfoErrorCases(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        # Intentionally leave DB in a state that might cause errors for these tests

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_scene_info_no_current_scene_key_in_db_raises_error(self):
        # DB is empty, so 'current_scene' key does not exist
        self.assert_error_behavior(
            func_to_call=get_scene_info,
            expected_exception_type=custom_errors.SceneNotFoundError,
            expected_message="No current scene available in DB."
        )

    def test_get_scene_info_current_scene_is_none_raises_error(self):
        DB['current_scene'] = None
        self.assert_error_behavior(
            func_to_call=get_scene_info,
            expected_exception_type=custom_errors.SceneNotFoundError,
            expected_message="No current scene available in DB."
        )


if __name__ == '__main__':
    unittest.main() 