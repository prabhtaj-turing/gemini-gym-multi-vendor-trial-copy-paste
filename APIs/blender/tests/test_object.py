"""
Test suite for object-related functionalities in the Blender API simulation.
"""
import copy
import unittest
import uuid

from blender.SimulationEngine import custom_errors, models
from blender.SimulationEngine.db import DB
from blender.object import get_object_info
from blender.object import set_texture
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Initial DB state for get_object_info function tests
GET_OBJECT_INFO_INITIAL_DB_STATE = {
    "current_scene": {
        'name': 'MainScene',
        'objects': {
            'Cube_Full': {
                'id': 'uuid-cube-full',  # Not part of return, but good for DB completeness
                'name': 'Cube_Full',
                'type': 'MESH',
                'location': [1.0, 2.0, 3.0],
                'rotation_euler': [0.1, 0.2, 0.3],
                'scale': [1.1, 1.2, 1.3],
                'dimensions': [2.1, 2.2, 2.3],
                'vertex_count': 8,
                'edge_count': 12,
                'face_count': 6,
                'material_names': ['Mat.Generic', 'Mat.Metal'],
                'is_visible': True,
                'is_renderable': True,
                'parent_name': None,  # Example of an extra field in DB
            },
            'Camera_Detailed': {
                'id': 'uuid-camera-detailed',
                'name': 'Camera_Detailed',
                'type': 'CAMERA',
                'location': [0.0, -5.0, 1.0],
                'rotation_euler': [1.570796, 0.0, 0.0],  # pi/2
                'scale': [1.0, 1.0, 1.0],
                'dimensions': [0.5, 0.5, 0.5],
                'vertex_count': None,
                'edge_count': None,
                'face_count': None,
                'material_names': [],
                'is_visible': False,
                'is_renderable': True,
                'camera_focal_length': 50.0,  # Extra field
            },
            'Light_MinimalData': {  # Intentionally missing optional fields in DB
                'id': 'uuid-light-minimal',
                'name': 'Light_MinimalData',
                'type': 'LIGHT',
                'location': [4.0, 1.0, 5.0],
                'rotation_euler': [0.0, 0.0, 0.0],
                'scale': [1.0, 1.0, 1.0],
                'dimensions': [0.1, 0.1, 0.1],
                # vertex_count, edge_count, face_count are missing
                # material_names is missing
                'is_visible': True,
                'is_renderable': False,
            },
            'Mesh_OptionalFieldsSetToNoneInDB': {
                'id': 'uuid-mesh-optional-null',
                'name': 'Mesh_OptionalFieldsSetToNoneInDB',
                'type': 'MESH',
                'location': [0.0, 0.0, 0.0],
                'rotation_euler': [0.0, 0.0, 0.0],
                'scale': [1.0, 1.0, 1.0],
                'dimensions': [2.0, 2.0, 2.0],
                'vertex_count': None,  # Explicitly null in DB
                'edge_count': None,  # Explicitly null in DB
                'face_count': None,  # Explicitly null in DB
                'material_names': ['Mat.Generic'],
                'is_visible': True,
                'is_renderable': True,
            }
        },
        'active_camera_name': 'Camera_Detailed',  # Not used by func, but part of scene
        'world_settings': {},  # Minimal, not used by func
        'render_settings': {}  # Minimal, not used by func
    },
    "materials": {  # Not directly used by func, but linked by material_names
        'Mat.Generic': {'id': 'uuid-mat-generic', 'name': 'Mat.Generic'},
        'Mat.Metal': {'id': 'uuid-mat-metal', 'name': 'Mat.Metal'}
    }
}


class TestGetObjectInfo(BaseTestCaseWithErrorHandler):
    """
    Test suite for the get_object_info function.
    """

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(GET_OBJECT_INFO_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def test_get_mesh_object_info_success_all_fields_present(self):
        obj_info = get_object_info(object_name='Cube_Full')
        expected = {
            'name': 'Cube_Full',
            'type': 'MESH',
            'location': [1.0, 2.0, 3.0],
            'rotation_euler': [0.1, 0.2, 0.3],
            'scale': [1.1, 1.2, 1.3],
            'dimensions': [2.1, 2.2, 2.3],
            'vertex_count': 8,
            'edge_count': 12,
            'face_count': 6,
            'material_names': ['Mat.Generic', 'Mat.Metal'],
            'is_visible': True,
            'is_renderable': True,
        }
        self.assertEqual(obj_info, expected)

    def test_get_camera_object_info_success_non_mesh_counts_none(self):
        obj_info = get_object_info(object_name='Camera_Detailed')
        expected = {
            'name': 'Camera_Detailed',
            'type': 'CAMERA',
            'location': [0.0, -5.0, 1.0],
            'rotation_euler': [1.570796, 0.0, 0.0],
            'scale': [1.0, 1.0, 1.0],
            'dimensions': [0.5, 0.5, 0.5],
            'vertex_count': None,
            'edge_count': None,
            'face_count': None,
            'material_names': [],
            'is_visible': False,
            'is_renderable': True,
        }
        self.assertEqual(obj_info, expected)

    def test_get_light_object_info_missing_optional_fields_in_db_handled(self):
        # Tests if optional fields (vertex counts, material_names) missing in DB data
        # are correctly defaulted to None or empty list in the output.
        obj_info = get_object_info(object_name='Light_MinimalData')
        expected = {
            'name': 'Light_MinimalData',
            'type': 'LIGHT',
            'location': [4.0, 1.0, 5.0],
            'rotation_euler': [0.0, 0.0, 0.0],
            'scale': [1.0, 1.0, 1.0],
            'dimensions': [0.1, 0.1, 0.1],
            'vertex_count': None,
            'edge_count': None,
            'face_count': None,
            'material_names': [],  # Should default to [] if 'material_names' key is missing
            'is_visible': True,
            'is_renderable': False,
        }
        self.assertEqual(obj_info, expected)

    def test_get_mesh_object_info_optional_fields_explicitly_none_in_db(self):
        # Tests if MESH object with null vertex/edge/face counts in DB
        # correctly returns them as None.
        obj_info = get_object_info(object_name='Mesh_OptionalFieldsSetToNoneInDB')
        expected = {
            'name': 'Mesh_OptionalFieldsSetToNoneInDB',
            'type': 'MESH',
            'location': [0.0, 0.0, 0.0],
            'rotation_euler': [0.0, 0.0, 0.0],
            'scale': [1.0, 1.0, 1.0],
            'dimensions': [2.0, 2.0, 2.0],
            'vertex_count': None,
            'edge_count': None,
            'face_count': None,
            'material_names': ['Mat.Generic'],
            'is_visible': True,
            'is_renderable': True,
        }
        self.assertEqual(obj_info, expected)

    def test_get_object_info_object_not_found_raises_object_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=get_object_info,
            expected_exception_type=custom_errors.ObjectNotFoundError,
            expected_message="Object 'NonExistentObject' not found in scene.",
            object_name='NonExistentObject'
        )

    def test_get_object_info_object_name_empty_string_raises_object_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=get_object_info,
            expected_exception_type=custom_errors.ObjectNotFoundError,
            expected_message="Object '' not found in scene.",
            object_name=''
        )

    def test_get_object_info_no_current_scene_in_db_raises_scene_not_found_error(self):
        original_scene = DB.pop('current_scene')
        try:
            self.assert_error_behavior(
                func_to_call=get_object_info,
                expected_exception_type=custom_errors.SceneNotFoundError,
                expected_message="No objects found in scene.",
                object_name='Cube_Full'
            )
        finally:
            DB['current_scene'] = original_scene

    def test_get_object_info_current_scene_is_none_raises_scene_not_found_error(self):
        original_scene_val = DB['current_scene']
        DB['current_scene'] = None
        try:
            self.assert_error_behavior(
                func_to_call=get_object_info,
                expected_exception_type=custom_errors.SceneNotFoundError,
                expected_message="No objects found in scene.",
                object_name='Cube_Full'
            )
        finally:
            DB['current_scene'] = original_scene_val

    def test_get_object_info_no_objects_dict_in_scene_raises_object_not_found_error(self):
        original_objects = DB['current_scene'].pop('objects')
        try:
            self.assert_error_behavior(
                func_to_call=get_object_info,
                expected_exception_type=custom_errors.ObjectNotFoundError,
                expected_message="No objects found in scene.",
                object_name='Cube_Full'
            )
        finally:
            DB['current_scene']['objects'] = original_objects

    def test_get_object_info_empty_objects_dict_in_scene_raises_object_not_found_error(self):
        original_objects = DB['current_scene']['objects']
        DB['current_scene']['objects'] = {}
        try:
            self.assert_error_behavior(
                func_to_call=get_object_info,
                expected_exception_type=custom_errors.ObjectNotFoundError,
                expected_message="Object 'Cube_Full' not found in scene.",
                object_name='Cube_Full'
            )
        finally:
            DB['current_scene']['objects'] = original_objects

    def test_get_object_info_no_objects_key_in_current_scene_raises_object_not_found_error(self):
        """Tests that ObjectNotFoundError is raised if 'objects' key is missing in current_scene."""
        # Ensure current_scene exists but 'objects' key is missing
        temp_scene_backup = copy.deepcopy(DB.get('current_scene'))
        # Create a scene without an 'objects' key
        DB['current_scene'] = {
            'name': 'TestSceneWithoutObjectsKey',
            # 'objects' key is deliberately omitted
            'active_camera_name': None,
            'world_settings': {},
            'render_settings': {}
        }
        try:
            self.assert_error_behavior(
                func_to_call=get_object_info,
                expected_exception_type=custom_errors.ObjectNotFoundError,
                expected_message="No objects found in scene.",
                object_name='AnyObject'
            )
        finally:
            # Restore the original current_scene or remove if it was None
            if temp_scene_backup is None:
                DB.pop('current_scene', None)
            else:
                DB['current_scene'] = temp_scene_backup

    def test_get_object_info_pydantic_validation_error_in_transform(self):
        """Tests that a Pydantic ValidationError during data transformation is caught and re-raised as custom_errors.ValidationError."""
        malformed_object_name = "MalformedCube"
        original_object_data = DB['current_scene']['objects'].get(malformed_object_name)

        DB['current_scene']['objects'][malformed_object_name] = {
            'id': 'uuid-malformed-cube',
            'name': malformed_object_name,
            'type': 'MESH',
            'location': 'not_a_list',  # This will cause a Pydantic error
            'rotation_euler': [0.1, 0.2, 0.3],
            'scale': [1.1, 1.2, 1.3],
            'dimensions': [2.1, 2.2, 2.3],
            'vertex_count': 8,
            'edge_count': 12,
            'face_count': 6,
            'material_names': ['Mat.Generic'],
            'is_visible': True,
            'is_renderable': True,
        }

        try:
            with self.assertRaises(custom_errors.ValidationError) as context_manager:
                get_object_info(object_name=malformed_object_name)

            self.assertRegex(
                str(context_manager.exception),
                "Error transforming object data to BlenderObjectInfoModel"
            )

        finally:
            if original_object_data is None:
                DB['current_scene']['objects'].pop(malformed_object_name, None)
            else:
                DB['current_scene']['objects'][malformed_object_name] = original_object_data

    def test_get_object_info_invalid_object_name_type_integer_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=get_object_info,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="object_name must be a string",
            object_name=123
        )

    def test_get_object_info_invalid_object_name_type_none_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=get_object_info,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="object_name must be a string",
            object_name=None
        )

    def test_get_object_info_invalid_object_name_type_list_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=get_object_info,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="object_name must be a string",
            object_name=[]
        )


# Build an initial DB state tailored for set_texture tests
SET_TEXTURE_INITIAL_DB_STATE = {
    "current_scene": {
        "name": "MainScene",
        "objects": {
            # Object with an existing material
            "CubeWithMat": {
                "id": "uuid-cube-with-mat",
                "name": "CubeWithMat",
                "type": models.BlenderObjectType.MESH.value,
                "location": [0.0, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "dimensions": [2.0, 2.0, 2.0],
                "material_names": ["WoodMat"],
                "is_visible": True,
                "is_renderable": True,
            },
            # Object without any material
            "CubeNoMat": {
                "id": "uuid-cube-nomat",
                "name": "CubeNoMat",
                "type": models.BlenderObjectType.MESH.value,
                "location": [0.0, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "dimensions": [2.0, 2.0, 2.0],
                # material_names intentionally missing -> treated as no material
                "is_visible": True,
                "is_renderable": True,
            },
        },
        "active_camera_name": None,
        "world_settings": {},
        "render_settings": {},
    },
    "materials": {
        "WoodMat": {
            "id": str(uuid.uuid4()),
            "name": "WoodMat",
            "base_color_value": [0.8, 0.8, 0.8],
            "metallic": 0.0,
            "roughness": 0.5,
            "base_color_texture_polyhaven_id": None,
        }
    },
    "polyhaven_assets_db": {
        # Valid, downloaded texture
        "tex-wood": {
            "asset_id": "tex-wood",
            "name": "Oak Wood",
            "type": models.PolyhavenAssetTypeData.TEXTURE.value,
            "tags": ["wood", "planks"],
            "author": "Polyhaven",
            "resolution_options": ["1k", "2k", "4k"],
            "file_format_options": ["png"],
            "is_downloaded": True,
            "downloaded_resolution": "2k",
            "downloaded_file_format": "png",
            "local_file_path": "/tmp/tex-wood.png",
            "blender_name": "Oak_Wood",
            "imported_as_blender_material_id": None,
            "imported_as_blender_object_id": None,
            "imported_as_world_environment": False,
        },
        # Texture not downloaded yet
        "tex-not-downloaded": {
            "asset_id": "tex-not-downloaded",
            "name": "Birch Wood",
            "type": models.PolyhavenAssetTypeData.TEXTURE.value,
            "tags": ["wood"],
            "author": "Polyhaven",
            "resolution_options": ["1k"],
            "file_format_options": ["png"],
            "is_downloaded": False,
        },
        # Asset of wrong type (HDRI)
        "hdri-sky": {
            "asset_id": "hdri-sky",
            "name": "Sky HDRI",
            "type": models.PolyhavenAssetTypeData.HDRI.value,
            "tags": ["sky"],
            "author": "Polyhaven",
            "resolution_options": ["2k"],
            "file_format_options": ["hdr"],
            "is_downloaded": True,
        },
    },
}


class TestSetTexture(BaseTestCaseWithErrorHandler):
    """Test suite for the set_texture function."""

    @classmethod
    def setUpClass(cls):
        # Preserve original DB and load test fixture
        cls._original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(SET_TEXTURE_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        DB.clear()
        DB.update(cls._original_db_state)

    # --- Success paths ---
    def test_set_texture_success_existing_material(self):
        result = set_texture(object_name="CubeWithMat", texture_id="tex-wood")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["object_name"], "CubeWithMat")
        self.assertEqual(result["texture_id"], "tex-wood")

        # Material should have texture id set
        mat_dict = DB["materials"]["WoodMat"]
        self.assertEqual(mat_dict["base_color_texture_polyhaven_id"], "tex-wood")

    def test_set_texture_success_creates_material(self):
        # Ensure CubeNoMat has no materials initially
        self.assertTrue(
            "material_names" not in DB["current_scene"]["objects"]["CubeNoMat"] or not DB["current_scene"]["objects"][
                "CubeNoMat"].get("material_names"))

        result = set_texture(object_name="CubeNoMat", texture_id="tex-wood")
        self.assertEqual(result["status"], "success")
        obj_dict = DB["current_scene"]["objects"]["CubeNoMat"]
        self.assertTrue(obj_dict["material_names"])  # Should not be empty now
        created_material_name = obj_dict["material_names"][0]
        self.assertIn(created_material_name, DB["materials"])
        self.assertEqual(DB["materials"][created_material_name]["base_color_texture_polyhaven_id"], "tex-wood")

    # --- Error paths ---
    def test_set_texture_texture_not_downloaded_raises_invalid_state_error(self):
        self.assert_error_behavior(
            func_to_call=set_texture,
            expected_exception_type=custom_errors.InvalidStateError,
            expected_message="Texture asset 'tex-not-downloaded' must be downloaded before applying.",
            object_name="CubeWithMat",
            texture_id="tex-not-downloaded"
        )

    def test_set_texture_invalid_asset_type_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=set_texture,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Asset 'hdri-sky' is not a texture (type is 'hdri').",
            object_name="CubeWithMat",
            texture_id="hdri-sky"
        )

    def test_set_texture_texture_not_found_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=set_texture,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Texture asset 'bad-id' not found in Polyhaven assets database.",
            object_name="CubeWithMat",
            texture_id="bad-id"
        )

    def test_set_texture_object_not_found_raises_error(self):
        self.assert_error_behavior(
            func_to_call=set_texture,
            expected_exception_type=custom_errors.ObjectNotFoundError,
            expected_message="Object 'NonExist' not found in scene.",
            object_name="NonExist",
            texture_id="tex-wood"
        )

    def test_set_texture_invalid_object_name_type_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=set_texture,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="object_name must be a string",
            object_name=123,  # Non-string type
            texture_id="tex-wood"
        )

    def test_set_texture_invalid_texture_id_type_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=set_texture,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="texture_id must be a string",
            object_name="CubeWithMat",
            texture_id=456  # Non-string type
        )

    def test_set_texture_creates_material_with_unique_name_if_default_exists(self):
        # Add a material that would conflict with the default generated name for CubeNoMat
        conflicting_material_name = "CubeNoMat_Mat"
        DB["materials"][conflicting_material_name] = {
            "id": str(uuid.uuid4()),
            "name": conflicting_material_name,
            "base_color_value": [0.1, 0.2, 0.3],
        }
        # Ensure CubeNoMat has no materials initially for this test
        if "material_names" in DB["current_scene"]["objects"]["CubeNoMat"]:
            del DB["current_scene"]["objects"]["CubeNoMat"]["material_names"]

        result = set_texture(object_name="CubeNoMat", texture_id="tex-wood")
        self.assertEqual(result["status"], "success")
        obj_dict = DB["current_scene"]["objects"]["CubeNoMat"]
        self.assertTrue(obj_dict["material_names"])
        created_material_name = obj_dict["material_names"][0]

        # The created material name should be unique, e.g., "CubeNoMat_Mat_1"
        self.assertNotEqual(created_material_name, conflicting_material_name)
        self.assertTrue(created_material_name.startswith(f"{conflicting_material_name}_"))
        self.assertIn(created_material_name, DB["materials"])
        self.assertEqual(DB["materials"][created_material_name]["base_color_texture_polyhaven_id"], "tex-wood")

        # Clean up the added material for other tests
        del DB["materials"][conflicting_material_name]
        # Also remove the material created by this test to ensure test isolation for subsequent runs if any
        del DB["materials"][created_material_name]
        # And reset material_names for CubeNoMat
        if "material_names" in DB["current_scene"]["objects"]["CubeNoMat"]:
            del DB["current_scene"]["objects"]["CubeNoMat"]["material_names"]


if __name__ == '__main__':
    unittest.main()
