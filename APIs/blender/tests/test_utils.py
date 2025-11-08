"""
Test suite for utility functions in the Blender API simulation.
Covers utilities from SimulationEngine/utils.py with comprehensive unit tests.
"""
import copy
import unittest
import uuid
import os
import tempfile
from unittest.mock import patch, mock_open

from common_utils.base_case import BaseTestCaseWithErrorHandler
from blender.SimulationEngine import utils, custom_errors, models
from blender.SimulationEngine.db import DB


# Initial DB state for utility function tests
UTILITIES_INITIAL_DB_STATE = {
    "current_scene": {
        "name": "UtilTestScene",
        "objects": {
            "TestCube": {
                "id": "uuid-test-cube",
                "name": "TestCube",
                "type": models.BlenderObjectType.MESH.value,
                "location": [0.0, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "dimensions": [2.0, 2.0, 2.0],
                "material_names": ["TestMaterial"],
                "is_visible": True,
                "is_renderable": True,
            },
            "TestCamera": {
                "id": "uuid-test-camera",
                "name": "TestCamera",
                "type": models.BlenderObjectType.CAMERA.value,
                "location": [0.0, -5.0, 1.0],
                "rotation_euler": [1.570796, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "dimensions": [0.5, 0.5, 0.5],
                "material_names": [],
                "is_visible": False,
                "is_renderable": True,
            },
            "TestLight": {
                "id": "uuid-test-light",
                "name": "TestLight",
                "type": models.BlenderObjectType.LIGHT.value,
                "location": [4.0, 1.0, 5.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "dimensions": [0.1, 0.1, 0.1],
                "material_names": [],
                "is_visible": True,
                "is_renderable": False,
            }
        },
        "active_camera_name": "TestCamera",
        "world_settings": {
            "ambient_color": [0.05, 0.05, 0.05],
            "horizon_color": [0.5, 0.5, 0.5]
        },
        "render_settings": {
            "engine": "CYCLES",
            "resolution_x": 1920,
            "resolution_y": 1080,
            "resolution_percentage": 100,
            "filepath": "/tmp/render_####.png"
        }
    },
    "materials": {
        "TestMaterial": {
            "id": "uuid-test-material",
            "name": "TestMaterial",
            "base_color_value": [0.8, 0.8, 0.8],
            "metallic": 0.0,
            "roughness": 0.5,
            "base_color_texture_polyhaven_id": None,
        },
        "WoodMaterial": {
            "id": "uuid-wood-material",
            "name": "WoodMaterial",
            "base_color_value": [0.6, 0.4, 0.2],
            "metallic": 0.0,
            "roughness": 0.8,
            "base_color_texture_polyhaven_id": "wood-texture-01",
        }
    },
    "polyhaven_assets_db": {
        "wood-texture-01": {
            "asset_id": "wood-texture-01",
            "name": "Oak Wood Texture",
            "type": models.PolyhavenAssetTypeData.TEXTURE.value,
            "tags": ["wood", "planks"],
            "author": "Polyhaven",
            "resolution_options": ["1k", "2k", "4k"],
            "file_format_options": ["png"],
            "is_downloaded": True,
            "downloaded_resolution": "2k",
            "downloaded_file_format": "png",
            "local_file_path": "/tmp/wood-texture-01.png",
            "blender_name": "Oak_Wood_Texture",
            "imported_as_blender_object_id": None,
            "imported_as_blender_material_id": None,
            "imported_as_world_environment": False,
        },
        "sky-hdri-01": {
            "asset_id": "sky-hdri-01",
            "name": "Clear Sky HDRI",
            "type": models.PolyhavenAssetTypeData.HDRI.value,
            "tags": ["sky", "clear"],
            "author": "Polyhaven",
            "resolution_options": ["2k", "4k"],
            "file_format_options": ["hdr"],
            "is_downloaded": False,
            "downloaded_resolution": None,
            "downloaded_file_format": None,
            "local_file_path": None,
            "blender_name": None,
            "imported_as_blender_object_id": None,
            "imported_as_blender_material_id": None,
            "imported_as_world_environment": False,
        }
    },
    "hyper3d_jobs": {
        "job-123": {
            "internal_job_id": "job-123",
            "mode_at_creation": "MAIN_SITE",
            "text_prompt": "A wooden chair",
            "input_image_paths": None,
            "input_image_urls": None,
            "bbox_condition": None,
            "submission_status": "success_queued",
            "submission_message": "Job initiated.",
            "task_uuid": "task-456",
            "request_id": "req-789",
            "subscription_key": "sub-key-123",
            "poll_overall_status": "COMPLETED",
            "poll_message": "Job completed successfully.",
            "poll_details_specific": {"result_url": "https://example.com/result.glb"},
            "asset_name_for_import": "WoodenChair_Asset",
            "import_status": models.ExecutionStatus.SUCCESS.value,
            "import_message": "Successfully imported.",
            "imported_blender_object_id": "uuid-imported-chair",
            "imported_blender_object_name": "ImportedChair",
            "imported_blender_object_type": models.BlenderObjectType.MESH.value
        }
    }
}


class TestUtilityFunctions(BaseTestCaseWithErrorHandler):
    """Test suite for utility functions from SimulationEngine/utils.py"""

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(UTILITIES_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Reset DB to initial state before each test."""
        DB.clear()
        DB.update(copy.deepcopy(UTILITIES_INITIAL_DB_STATE))

    # Test add_object_to_scene function
    def test_add_object_to_scene_success_with_full_data(self):
        """Test successful addition of object with all fields provided."""
        object_data = {
            "name": "NewCube",
            "id": "uuid-new-cube",
            "type": models.BlenderObjectType.MESH.value,
            "location": [1.0, 2.0, 3.0],
            "rotation_euler": [0.1, 0.2, 0.3],
            "scale": [1.1, 1.2, 1.3],
            "dimensions": [2.1, 2.2, 2.3],
            "material_names": ["TestMaterial"],
            "is_visible": True,
            "is_renderable": True,
        }
        
        result = utils.add_object_to_scene("UtilTestScene", object_data)
        
        # Check return value
        self.assertEqual(result["name"], "NewCube")
        self.assertEqual(result["id"], "uuid-new-cube")
        
        # Check object was added to DB
        scene_objects = DB["current_scene"]["objects"]
        self.assertIn("NewCube", scene_objects)
        self.assertEqual(scene_objects["NewCube"]["name"], "NewCube")

    def test_add_object_to_scene_success_minimal_data_with_defaults(self):
        """Test successful addition of object with minimal data, verifying defaults."""
        object_data = {
            "name": "MinimalObject"
        }
        
        result = utils.add_object_to_scene("UtilTestScene", object_data)
        
        # Check that defaults were applied
        self.assertEqual(result["type"], models.BlenderObjectType.MESH.value)
        self.assertEqual(result["location"], [0.0, 0.0, 0.0])
        self.assertEqual(result["rotation_euler"], [0.0, 0.0, 0.0])
        self.assertEqual(result["scale"], [1.0, 1.0, 1.0])
        self.assertEqual(result["dimensions"], [2.0, 2.0, 2.0])
        self.assertEqual(result["material_names"], [])
        self.assertTrue(result["is_visible"])
        self.assertTrue(result["is_renderable"])
        self.assertIsInstance(result["id"], str)
        
        # Check object was added to DB
        self.assertIn("MinimalObject", DB["current_scene"]["objects"])

    def test_add_object_to_scene_auto_generates_uuid_id(self):
        """Test that UUID ID is auto-generated when not provided."""
        object_data = {"name": "AutoUUIDObject"}
        
        result = utils.add_object_to_scene("UtilTestScene", object_data)
        
        # Check UUID was generated
        self.assertIsInstance(result["id"], str)
        self.assertTrue(len(result["id"]) > 0)
        
        # Verify it's a valid UUID format
        try:
            uuid.UUID(result["id"])
        except ValueError:
            self.fail("Generated ID is not a valid UUID")

    def test_add_object_to_scene_converts_uuid_object_to_string(self):
        """Test that UUID object is converted to string ID."""
        test_uuid = uuid.uuid4()
        object_data = {
            "name": "UUIDConvertObject",
            "id": test_uuid
        }
        
        result = utils.add_object_to_scene("UtilTestScene", object_data)
        
        self.assertEqual(result["id"], str(test_uuid))
        self.assertIsInstance(result["id"], str)

    def test_add_object_to_scene_duplicate_name_raises_error(self):
        """Test that adding object with duplicate name raises DuplicateNameError."""
        object_data = {"name": "TestCube"}  # Already exists in test DB
        
        self.assert_error_behavior(
            utils.add_object_to_scene,
            custom_errors.DuplicateNameError,
            "Object 'TestCube' already exists in scene 'UtilTestScene'.",
            scene_name="UtilTestScene",
            object_data=object_data
        )

    def test_add_object_to_scene_no_name_raises_error(self):
        """Test that missing name field raises ValueError."""
        object_data = {"type": "MESH"}  # Missing name
        
        with self.assertRaises(ValueError) as cm:
            utils.add_object_to_scene("UtilTestScene", object_data)
        self.assertIn("Object data must include a 'name'", str(cm.exception))

    def test_add_object_to_scene_scene_mismatch_raises_error(self):
        """Test that scene name mismatch raises SceneNotFoundError."""
        object_data = {"name": "NewObject"}
        
        self.assert_error_behavior(
            utils.add_object_to_scene,
            custom_errors.SceneNotFoundError,
            "Scene 'WrongScene' does not match current scene 'UtilTestScene'.",
            scene_name="WrongScene",
            object_data=object_data
        )

    def test_add_object_to_scene_no_current_scene_raises_error(self):
        """Test that missing current_scene raises SceneNotFoundError."""
        DB.pop("current_scene")
        object_data = {"name": "NewObject"}
        
        self.assert_error_behavior(
            utils.add_object_to_scene,
            custom_errors.SceneNotFoundError,
            "No current scene available in DB.",
            scene_name="AnyScene",
            object_data=object_data
        )

    # Test remove_object_from_scene function
    def test_remove_object_from_scene_success(self):
        """Test successful removal of object from scene."""
        # Verify object exists initially
        self.assertIn("TestCube", DB["current_scene"]["objects"])
        
        result = utils.remove_object_from_scene("UtilTestScene", "TestCube")
        
        # Check return value
        self.assertTrue(result)
        
        # Check object was removed from DB
        self.assertNotIn("TestCube", DB["current_scene"]["objects"])

    def test_remove_object_from_scene_updates_active_camera(self):
        """Test that removing active camera updates active_camera_name to None."""
        # Set TestCamera as active camera and then remove it
        DB["current_scene"]["active_camera_name"] = "TestCamera"
        
        result = utils.remove_object_from_scene("UtilTestScene", "TestCamera")
        
        self.assertTrue(result)
        self.assertIsNone(DB["current_scene"]["active_camera_name"])

    def test_remove_object_from_scene_updates_parent_references(self):
        """Test that removing object updates parent_name references in other objects."""
        # Add a child object that references TestCube as parent
        child_object = {
            "name": "ChildObject",
            "parent_name": "TestCube",
            "type": "MESH"
        }
        DB["current_scene"]["objects"]["ChildObject"] = child_object
        
        utils.remove_object_from_scene("UtilTestScene", "TestCube")
        
        # Check that parent reference was cleared
        self.assertIsNone(DB["current_scene"]["objects"]["ChildObject"]["parent_name"])

    def test_remove_object_from_scene_object_not_found_raises_error(self):
        """Test that removing non-existent object raises ObjectNotFoundError."""
        self.assert_error_behavior(
            utils.remove_object_from_scene,
            custom_errors.ObjectNotFoundError,
            "Object 'NonExistentObject' not found in scene 'UtilTestScene'.",
            scene_name="UtilTestScene",
            object_name="NonExistentObject"
        )

    def test_remove_object_from_scene_scene_mismatch_raises_error(self):
        """Test that scene name mismatch raises SceneNotFoundError."""
        self.assert_error_behavior(
            utils.remove_object_from_scene,
            custom_errors.SceneNotFoundError,
            "Scene 'WrongScene' does not match current scene 'UtilTestScene'.",
            scene_name="WrongScene",
            object_name="TestCube"
        )

    # Test update_polyhaven_asset_download_status function
    def test_update_polyhaven_asset_download_status_success_downloaded(self):
        """Test successful update of asset download status to downloaded."""
        result = utils.update_polyhaven_asset_download_status(
            asset_id="sky-hdri-01",
            is_downloaded=True,
            downloaded_resolution="4k",
            downloaded_file_format="hdr",
            local_file_path="/tmp/sky-hdri-01.hdr",
            blender_name="Clear_Sky_HDRI",
            imported_as_world_environment=True
        )
        
        # Check return value
        self.assertTrue(result["is_downloaded"])
        self.assertEqual(result["downloaded_resolution"], "4k")
        self.assertEqual(result["local_file_path"], "/tmp/sky-hdri-01.hdr")
        
        # Check DB was updated
        asset_data = DB["polyhaven_assets_db"]["sky-hdri-01"]
        self.assertTrue(asset_data["is_downloaded"])
        self.assertEqual(asset_data["downloaded_resolution"], "4k")
        self.assertTrue(asset_data["imported_as_world_environment"])

    def test_update_polyhaven_asset_download_status_success_not_downloaded(self):
        """Test successful update of asset download status to not downloaded."""
        # First ensure asset is downloaded
        DB["polyhaven_assets_db"]["wood-texture-01"]["is_downloaded"] = True
        
        result = utils.update_polyhaven_asset_download_status(
            asset_id="wood-texture-01",
            is_downloaded=False
        )
        
        # Check return value
        self.assertFalse(result["is_downloaded"])
        self.assertIsNone(result["downloaded_resolution"])
        self.assertIsNone(result["local_file_path"])
        
        # Check DB was updated with reset fields
        asset_data = DB["polyhaven_assets_db"]["wood-texture-01"]
        self.assertFalse(asset_data["is_downloaded"])
        self.assertIsNone(asset_data["downloaded_resolution"])
        self.assertFalse(asset_data["imported_as_world_environment"])

    def test_update_polyhaven_asset_download_status_asset_not_found_raises_error(self):
        """Test that updating non-existent asset raises AssetNotFoundError."""
        self.assert_error_behavior(
            utils.update_polyhaven_asset_download_status,
            custom_errors.AssetNotFoundError,
            "Polyhaven asset 'non-existent' not found.",
            asset_id="non-existent",
            is_downloaded=True
        )

    # Test apply_texture_to_material function
    def test_apply_texture_to_material_success_with_texture(self):
        """Test successful application of texture to material."""
        result = utils.apply_texture_to_material(
            material_name="TestMaterial",
            texture_polyhaven_id="wood-texture-01"
        )
        
        # Check return value
        self.assertEqual(result["base_color_texture_polyhaven_id"], "wood-texture-01")
        self.assertEqual(result["base_color_value"], [0.8, 0.8, 0.8])
        
        # Check DB was updated
        material_data = DB["materials"]["TestMaterial"]
        self.assertEqual(material_data["base_color_texture_polyhaven_id"], "wood-texture-01")

    def test_apply_texture_to_material_success_with_color(self):
        """Test successful application of base color to material."""
        result = utils.apply_texture_to_material(
            material_name="TestMaterial",
            base_color_value=[1.0, 0.5, 0.2]
        )
        
        # Check return value
        self.assertEqual(result["base_color_value"], [1.0, 0.5, 0.2])
        self.assertIsNone(result["base_color_texture_polyhaven_id"])
        
        # Check DB was updated
        material_data = DB["materials"]["TestMaterial"]
        self.assertEqual(material_data["base_color_value"], [1.0, 0.5, 0.2])
        self.assertIsNone(material_data["base_color_texture_polyhaven_id"])

    def test_apply_texture_to_material_material_not_found_raises_error(self):
        """Test that applying texture to non-existent material raises error."""
        self.assert_error_behavior(
            utils.apply_texture_to_material,
            custom_errors.MaterialNotFoundError,
            "Material 'NonExistentMaterial' not found.",
            material_name="NonExistentMaterial",
            texture_polyhaven_id="wood-texture-01"
        )

    def test_apply_texture_to_material_texture_not_found_raises_error(self):
        """Test that applying non-existent texture raises error."""
        self.assert_error_behavior(
            utils.apply_texture_to_material,
            custom_errors.AssetNotFoundError,
            "Polyhaven texture asset 'non-existent-texture' not found.",
            material_name="TestMaterial",
            texture_polyhaven_id="non-existent-texture"
        )

    def test_apply_texture_to_material_wrong_asset_type_raises_error(self):
        """Test that applying non-texture asset raises error."""
        with self.assertRaises(ValueError) as cm:
            utils.apply_texture_to_material(
                material_name="TestMaterial",
                texture_polyhaven_id="sky-hdri-01"  # This is HDRI, not texture
            )
        self.assertIn("is not a texture", str(cm.exception))



    def test_apply_texture_to_material_texture_not_downloaded_raises_error(self):
        """Test that applying non-downloaded texture raises error."""
        # Create a texture asset that's not downloaded
        not_downloaded_texture = {
            "asset_id": "not-downloaded-texture",
            "name": "Not Downloaded Texture",
            "type": models.PolyhavenAssetTypeData.TEXTURE.value,
            "is_downloaded": False
        }
        DB["polyhaven_assets_db"]["not-downloaded-texture"] = not_downloaded_texture
        
        self.assert_error_behavior(
            utils.apply_texture_to_material,
            custom_errors.InvalidStateError,
            "Texture asset 'not-downloaded-texture' must be downloaded before applying.",
            material_name="TestMaterial",
            texture_polyhaven_id="not-downloaded-texture"
        )

    def test_apply_texture_to_material_invalid_color_format_raises_error(self):
        """Test that invalid base color format raises error."""
        with self.assertRaises(ValueError) as cm:
            utils.apply_texture_to_material(
                material_name="TestMaterial",
                base_color_value=[1.0, 0.5]  # Missing third component
            )
        self.assertIn("Invalid base_color_value format", str(cm.exception))

    def test_apply_texture_to_material_no_texture_or_color_raises_error(self):
        """Test that providing neither texture nor color raises error."""
        with self.assertRaises(ValueError) as cm:
            utils.apply_texture_to_material(material_name="TestMaterial")
        self.assertIn("Either texture_polyhaven_id or base_color_value must be provided", str(cm.exception))

    # Test getter functions
    def test_get_scene_data_dict_success(self):
        """Test successful retrieval of scene data."""
        result = utils.get_scene_data_dict("UtilTestScene")
        
        self.assertEqual(result["name"], "UtilTestScene")
        self.assertEqual(result["camera_count"], 1)
        self.assertEqual(result["object_count"], 3)
        self.assertEqual(result["light_count"], 1)
        self.assertEqual(result["active_camera_name"], "TestCamera")
        self.assertIn("world_settings", result)
        self.assertIn("render_settings", result)

    def test_get_scene_data_dict_empty_scene(self):
        """Test retrieval of empty scene."""
        self.assert_error_behavior(
            utils.get_scene_data_dict,
            custom_errors.SceneNotFoundError,
            "Requested scene 'EmptyScene' does not match current scene 'UtilTestScene'.",
            scene_name="EmptyScene"
        )

    def test_get_scene_data_dict_invalid_scene_name_raises_error(self):
        """Test retrieval of invalid scene name."""
        self.assert_error_behavior(
            utils.get_scene_data_dict,
            custom_errors.SceneNotFoundError,
            "Requested scene 'InvalidScene' does not match current scene 'UtilTestScene'.",
            scene_name="InvalidScene"
        )

    def test_get_scene_data_dict_default_scene(self):
        """Test retrieval of scene data with no scene name (uses current)."""
        result = utils.get_scene_data_dict()
        
        self.assertEqual(result["name"], "UtilTestScene")

    def test_transform_object_to_info_model(self):
        """Test that transform_object_to_info_model works."""
        object_data = {
            "name": "TestObject",
            "type": "MESH",
            "location": [0.0, 0.0, 0.0],
            "rotation_euler": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
            "dimensions": [2.0, 2.0, 2.0],
            "vertex_count": 8,
            "edge_count": 12,
            "face_count": 6,
            "material_names": ["TestMaterial"],
            "is_visible": True,
            "is_renderable": True
        }

        result = utils.transform_object_to_info_model(object_data)
        
        self.assertEqual(result["name"], "TestObject")
        self.assertEqual(result["type"], "MESH")
        self.assertEqual(result["location"], [0.0, 0.0, 0.0])
        self.assertEqual(result["rotation_euler"], [0.0, 0.0, 0.0])

    def test_get_object_data_dict_success(self):
        """Test successful retrieval of object data."""
        result = utils.get_object_data_dict("TestCube")
        
        self.assertEqual(result["name"], "TestCube")
        self.assertEqual(result["type"], "MESH")
        self.assertEqual(result["location"], [0.0, 0.0, 0.0])

    def test_get_object_data_dict_object_not_found_raises_error(self):
        """Test that retrieving non-existent object raises ObjectNotFoundError."""
        self.assert_error_behavior(
            utils.get_object_data_dict,
            custom_errors.ObjectNotFoundError,
            "Object 'NonExistentObject' not found in scene.",
            object_name="NonExistentObject"
        )

    def test_get_object_data_dict_no_current_scene_raises_error(self):
        """Test that retrieving object from no current scene raises SceneNotFoundError."""
        del DB["current_scene"]
        self.assert_error_behavior(
            utils.get_object_data_dict,
            custom_errors.SceneNotFoundError,
            "No current scene available in DB.",
            object_name="TestCube"
        )

    def test_get_material_data_dict_success(self):
        """Test successful retrieval of material data."""
        result = utils.get_material_data_dict("TestMaterial")
        
        self.assertEqual(result["name"], "TestMaterial")
        self.assertEqual(result["base_color_value"], [0.8, 0.8, 0.8])

    def test_get_material_data_dict_material_not_found_raises_error(self):
        """Test that retrieving non-existent material raises MaterialNotFoundError."""
        self.assert_error_behavior(
            utils.get_material_data_dict,
            custom_errors.MaterialNotFoundError,
            "Material 'NonExistentMaterial' not found.",
            material_name="NonExistentMaterial"
        )

    def test_get_polyhaven_asset_data_dict_success(self):
        """Test successful retrieval of polyhaven asset data."""
        result = utils.get_polyhaven_asset_data_dict("wood-texture-01")
        
        self.assertEqual(result["asset_id"], "wood-texture-01")
        self.assertEqual(result["name"], "Oak Wood Texture")
        self.assertEqual(result["type"], "texture")

    def test_get_polyhaven_asset_data_dict_asset_not_found_raises_error(self):
        """Test that retrieving non-existent polyhaven asset raises AssetNotFoundError."""
        self.assert_error_behavior(
            utils.get_polyhaven_asset_data_dict,
            custom_errors.AssetNotFoundError,
            "Polyhaven asset 'non-existent-asset' not found.",
            asset_id="non-existent-asset"
        )

    def test_get_hyper3d_job_data_dict_success(self):
        """Test successful retrieval of hyper3d job data."""
        result = utils.get_hyper3d_job_data_dict("job-123")
        
        self.assertEqual(result["internal_job_id"], "job-123")
        self.assertEqual(result["text_prompt"], "A wooden chair")
        self.assertTrue(result["is_completed"])
        self.assertTrue(result["is_successful"])

    # Test helper functions
    def test_generate_simulated_file_path(self):
        """Test file path generation."""
        result = utils.generate_simulated_file_path(
            base_path="/tmp/assets",
            asset_category="textures",
            asset_id="wood-plank",
            resolution="2k",
            file_format="png"
        )
        
        expected = os.path.join("/tmp/assets", "textures", "wood-plank_2k.png")
        self.assertEqual(result, expected)

    def test_generate_blender_name_texture(self):
        """Test Blender name generation for texture."""
        result = utils.generate_blender_name(
            asset_name="Oak Wood",
            asset_id="oak-wood-01",
            asset_data_type=models.PolyhavenAssetTypeData.TEXTURE
        )
        
        expected = "PH Oak Wood (oak_wood_01) Material"
        self.assertEqual(result, expected)

    def test_generate_blender_name_hdri(self):
        """Test Blender name generation for HDRI."""
        result = utils.generate_blender_name(
            asset_name="Clear Sky",
            asset_id="clear-sky-01",
            asset_data_type=models.PolyhavenAssetTypeData.HDRI
        )
        
        expected = "PH Clear Sky (clear_sky_01) WorldHDRI"
        self.assertEqual(result, expected)

    def test_generate_blender_name_model(self):
        """Test Blender name generation for model."""
        result = utils.generate_blender_name(
            asset_name="Wooden Chair",
            asset_id="wooden-chair-01",
            asset_data_type=models.PolyhavenAssetTypeData.MODEL
        )
        
        expected = "PH Wooden Chair (wooden_chair_01) Model"
        self.assertEqual(result, expected)

    # Test create functions
    def test_create_material_success(self):
        """Test successful material creation."""
        material_data = {
            "name": "NewMaterial",
            "base_color_value": [1.0, 0.0, 0.0],
            "metallic": 0.5,
            "roughness": 0.3
        }
        
        result = utils.create_material(material_data)
        
        self.assertEqual(result["name"], "NewMaterial")
        self.assertEqual(result["base_color_value"], [1.0, 0.0, 0.0])
        self.assertEqual(result["metallic"], 0.5)
        self.assertIsInstance(result["id"], str)
        
        # Check material was added to DB
        self.assertIn("NewMaterial", DB["materials"])

    def test_create_material_with_defaults(self):
        """Test material creation with default values."""
        material_data = {"name": "DefaultMaterial"}
        
        result = utils.create_material(material_data)
        
        self.assertEqual(result["base_color_value"], [0.8, 0.8, 0.8])
        self.assertEqual(result["metallic"], 0.0)
        self.assertEqual(result["roughness"], 0.5)
        self.assertIsNone(result["base_color_texture_polyhaven_id"])

    def test_create_asset_success(self):
        """Test successful asset creation."""
        result = utils.create_asset(
            asset_id="test-asset",
            name="Test Asset",
            type="texture",
            tags=["test", "demo"],
            author="Test Author",
            res_opts=["1k", "2k"],
            fmt_opts=["png", "jpg"]
        )
        
        self.assertEqual(result["asset_id"], "test-asset")
        self.assertEqual(result["name"], "Test Asset")
        self.assertEqual(result["type"], "texture")
        self.assertEqual(result["tags"], ["test", "demo"])
        self.assertFalse(result["is_downloaded"])
        self.assertIsNone(result["downloaded_resolution"])

    # Test assign_material_to_object function
    def test_assign_material_to_object_success_replace(self):
        """Test successful material assignment with replacement."""
        result = utils.assign_material_to_object(
            scene_name="UtilTestScene",
            object_name="TestCube",
            material_name="WoodMaterial",
            replace_existing=True
        )
        
        self.assertTrue(result)
        
        # Check material was assigned (replacing existing)
        obj_materials = DB["current_scene"]["objects"]["TestCube"]["material_names"]
        self.assertEqual(obj_materials, ["WoodMaterial"])

    def test_assign_material_to_object_success_append(self):
        """Test successful material assignment without replacement."""
        result = utils.assign_material_to_object(
            scene_name="UtilTestScene",
            object_name="TestCube",
            material_name="WoodMaterial",
            replace_existing=False
        )
        
        self.assertTrue(result)
        
        # Check material was appended (not replacing existing)
        obj_materials = DB["current_scene"]["objects"]["TestCube"]["material_names"]
        self.assertIn("TestMaterial", obj_materials)
        self.assertIn("WoodMaterial", obj_materials)

    def test_assign_material_to_object_no_duplicate_append(self):
        """Test that appending same material doesn't create duplicates."""
        # First assign the material
        utils.assign_material_to_object(
            scene_name="UtilTestScene",
            object_name="TestCube",
            material_name="WoodMaterial",
            replace_existing=False
        )
        
        # Try to assign the same material again
        utils.assign_material_to_object(
            scene_name="UtilTestScene",
            object_name="TestCube",
            material_name="WoodMaterial",
            replace_existing=False
        )
        
        # Check material appears only once
        obj_materials = DB["current_scene"]["objects"]["TestCube"]["material_names"]
        material_count = obj_materials.count("WoodMaterial")
        self.assertEqual(material_count, 1)

    def test_add_job_to_db_success(self):
        """Test successful addition of job to DB."""
        utils.add_job_to_db(
            internal_job_id="job-123",
            mode_at_creation="MAIN_SITE",
            subscription_key="sub-key-123",
        )
        
        self.assertIn("job-123", DB["hyper3d_jobs"])
        self.assertEqual(DB["hyper3d_jobs"]["job-123"]["internal_job_id"], "job-123")
        self.assertEqual(DB["hyper3d_jobs"]["job-123"]["mode_at_creation"], "MAIN_SITE")
        self.assertEqual(DB["hyper3d_jobs"]["job-123"]["subscription_key"], "sub-key-123")

    def test_update_job_import_failure_success(self):
        """Test successful update of job import failure."""
        job_dict_in_db = DB["hyper3d_jobs"]["job-123"]
        utils.update_job_import_failure(job_dict_in_db, "Import failed.")
        self.assertEqual(DB["hyper3d_jobs"]["job-123"]["import_status"], models.ExecutionStatus.ERROR.value)
        self.assertEqual(DB["hyper3d_jobs"]["job-123"]["import_message"], "Import failed.")


if __name__ == '__main__':
    unittest.main()
