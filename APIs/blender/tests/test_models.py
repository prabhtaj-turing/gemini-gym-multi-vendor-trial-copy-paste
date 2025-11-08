"""
Test suite for model classes in the Blender API simulation.
Covers all Pydantic models from SimulationEngine/models.py with comprehensive validation tests.
"""
import unittest
import uuid
from datetime import datetime
from typing import Dict, List, Any

from pydantic import ValidationError
from blender.SimulationEngine.custom_errors import InvalidDateTimeFormatError as BlenderInvalidDateTimeFormatError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from blender.SimulationEngine.models import (
    # Enums
    BlenderObjectType,
    RenderEngineType,
    PolyhavenAssetTypeAPI,
    PolyhavenAssetTypeData,
    PolyhavenAssetTypeSearchable,
    Hyper3DMode,
    JobOverallStatus,
    ExecutionStatus,
    # Basic Types
    ColorRGB,
    Vector3D,
    # Models
    WorldSettingsModel,
    RenderSettingsModel,
    MaterialModel,
    BlenderObjectModel,
    BlenderObjectInfoModel,
    SceneModel,
    PolyhavenAssetInternalInfo,
    PolyhavenServiceStatusModel,
    SearchPolyhavenAssetsArguments,
    DownloadPolyhavenAssetArguments,
    Hyper3DServiceStatusModel,
    Hyper3DJobModel,
    BlenderCodeExecutionOutcomeModel,
    BlenderDB,
    GenerateHyper3DModelViaTextResponse,
    ImportGeneratedAssetArguments,
    ImportGeneratedAssetResponse
)


class TestEnums(BaseTestCaseWithErrorHandler):
    """Test enum definitions and values."""

    def test_blender_object_type_enum(self):
        """Test BlenderObjectType enum values."""
        self.assertEqual(BlenderObjectType.MESH, "MESH")
        self.assertEqual(BlenderObjectType.CAMERA, "CAMERA")
        self.assertEqual(BlenderObjectType.LIGHT, "LIGHT")
        self.assertEqual(BlenderObjectType.EMPTY, "EMPTY")
        
        # Test enum membership
        valid_types = ["MESH", "CAMERA", "LIGHT", "EMPTY"]
        for obj_type in valid_types:
            self.assertIn(obj_type, [e.value for e in BlenderObjectType])

    def test_render_engine_type_enum(self):
        """Test RenderEngineType enum values."""
        self.assertEqual(RenderEngineType.CYCLES, "CYCLES")
        self.assertEqual(RenderEngineType.EEVEE, "EEVEE")
        self.assertEqual(RenderEngineType.WORKBENCH, "WORKBENCH")

    def test_polyhaven_asset_type_enums(self):
        """Test Polyhaven asset type enums."""
        # API enum
        self.assertEqual(PolyhavenAssetTypeAPI.HDRIS, "hdris")
        self.assertEqual(PolyhavenAssetTypeAPI.TEXTURES, "textures")
        self.assertEqual(PolyhavenAssetTypeAPI.MODELS, "models")
        
        # Data enum
        self.assertEqual(PolyhavenAssetTypeData.HDRI, "hdri")
        self.assertEqual(PolyhavenAssetTypeData.TEXTURE, "texture")
        self.assertEqual(PolyhavenAssetTypeData.MODEL, "model")
        
        # Searchable enum
        self.assertEqual(PolyhavenAssetTypeSearchable.ALL, "all")
        self.assertEqual(PolyhavenAssetTypeSearchable.HDRIS, "hdris")

    def test_hyper3d_mode_enum(self):
        """Test Hyper3DMode enum values."""
        self.assertEqual(Hyper3DMode.MAIN_SITE, "MAIN_SITE")
        self.assertEqual(Hyper3DMode.FAL_AI, "FAL_AI")

    def test_job_status_enums(self):
        """Test job status enums."""
        # JobOverallStatus
        self.assertEqual(JobOverallStatus.PENDING, "PENDING")
        self.assertEqual(JobOverallStatus.COMPLETED, "COMPLETED")
        self.assertEqual(JobOverallStatus.FAILED, "FAILED")
        
        # ExecutionStatus
        self.assertEqual(ExecutionStatus.SUCCESS, "success")
        self.assertEqual(ExecutionStatus.ERROR, "error")


class TestBasicTypes(BaseTestCaseWithErrorHandler):
    """Test basic type definitions."""

    def test_color_rgb_valid(self):
        """Test ColorRGB with valid values."""
        valid_colors = [
            [0.0, 0.0, 0.0],  # Black
            [1.0, 1.0, 1.0],  # White
            [0.5, 0.2, 0.8],  # Purple
            [1.0, 0.0, 0.0],  # Red
        ]
        
        for color in valid_colors:
            with self.subTest(color=color):
                # ColorRGB is a constrained list, test it works in a model context
                world = WorldSettingsModel(ambient_color=color)
                self.assertEqual(world.ambient_color, color)

    def test_color_rgb_invalid(self):
        """Test ColorRGB with invalid values."""
        invalid_colors = [
            [0.0, 0.0],  # Too short
            [0.0, 0.0, 0.0, 1.0],  # Too long
            "not_a_list",  # Wrong type
            [1.0, "red", 0.0],  # Mixed types
        ]
        
        for color in invalid_colors:
            with self.subTest(color=color):
                with self.assertRaises(ValidationError):
                    WorldSettingsModel(ambient_color=color)

    def test_vector3d_valid(self):
        """Test Vector3D with valid values."""
        valid_vectors = [
            [0.0, 0.0, 0.0],  # Origin
            [1.0, 2.0, 3.0],  # Positive
            [-1.0, -2.0, -3.0],  # Negative
            [0.5, -0.5, 1.5],  # Mixed
        ]
        
        for vector in valid_vectors:
            with self.subTest(vector=vector):
                obj = BlenderObjectModel(name="test", type=BlenderObjectType.MESH, location=vector)
                self.assertEqual(obj.location, vector)

    def test_vector3d_invalid(self):
        """Test Vector3D with invalid values."""
        invalid_vectors = [
            [0.0, 0.0],  # Too short
            [0.0, 0.0, 0.0, 0.0],  # Too long
            "not_a_list",  # Wrong type
            [1.0, "two", 3.0],  # Mixed types
        ]
        
        for vector in invalid_vectors:
            with self.subTest(vector=vector):
                with self.assertRaises(ValidationError):
                    BlenderObjectModel(name="test", type=BlenderObjectType.MESH, location=vector)


class TestWorldSettingsModel(BaseTestCaseWithErrorHandler):
    """Test WorldSettingsModel validation and functionality."""

    def test_world_settings_default_values(self):
        """Test WorldSettingsModel with default values."""
        world = WorldSettingsModel()
        
        self.assertEqual(world.ambient_color, [0.05, 0.05, 0.05])
        self.assertEqual(world.horizon_color, [0.5, 0.5, 0.5])
        self.assertIsNone(world.environment_texture_polyhaven_id)
        self.assertEqual(world.environment_texture_strength, 1.0)

    def test_world_settings_custom_values(self):
        """Test WorldSettingsModel with custom values."""
        world = WorldSettingsModel(
            ambient_color=[0.1, 0.2, 0.3],
            horizon_color=[0.8, 0.9, 1.0],
            environment_texture_polyhaven_id="sky_asset_01",
            environment_texture_strength=0.5
        )
        
        self.assertEqual(world.ambient_color, [0.1, 0.2, 0.3])
        self.assertEqual(world.horizon_color, [0.8, 0.9, 1.0])
        self.assertEqual(world.environment_texture_polyhaven_id, "sky_asset_01")
        self.assertEqual(world.environment_texture_strength, 0.5)

    def test_world_settings_validation(self):
        """Test WorldSettingsModel validation."""
        # Invalid color format
        with self.assertRaises(ValidationError):
            WorldSettingsModel(ambient_color=[0.0, 0.0])  # Too short
        
        # Invalid strength type
        with self.assertRaises(ValidationError):
            WorldSettingsModel(environment_texture_strength="not_a_number")

    def test_world_settings_extra_fields_forbidden(self):
        """Test that WorldSettingsModel forbids extra fields."""
        with self.assertRaises(ValidationError):
            WorldSettingsModel(extra_field="not_allowed")


class TestRenderSettingsModel(BaseTestCaseWithErrorHandler):
    """Test RenderSettingsModel validation and functionality."""

    def test_render_settings_default_values(self):
        """Test RenderSettingsModel with default values."""
        render = RenderSettingsModel()
        
        self.assertEqual(render.engine, RenderEngineType.CYCLES)
        self.assertEqual(render.resolution_x, 1920)
        self.assertEqual(render.resolution_y, 1080)
        self.assertEqual(render.resolution_percentage, 100)
        self.assertEqual(render.filepath, "/tmp/render_####.png")

    def test_render_settings_custom_values(self):
        """Test RenderSettingsModel with custom values."""
        render = RenderSettingsModel(
            engine=RenderEngineType.EEVEE,
            resolution_x=3840,
            resolution_y=2160,
            resolution_percentage=50,
            filepath="/output/custom_####.jpg"
        )
        
        self.assertEqual(render.engine, RenderEngineType.EEVEE)
        self.assertEqual(render.resolution_x, 3840)
        self.assertEqual(render.resolution_y, 2160)
        self.assertEqual(render.resolution_percentage, 50)
        self.assertEqual(render.filepath, "/output/custom_####.jpg")

    def test_render_settings_validation(self):
        """Test RenderSettingsModel validation."""
        # Invalid engine type
        with self.assertRaises(ValidationError):
            RenderSettingsModel(engine="INVALID_ENGINE")
        
        # Invalid resolution types
        with self.assertRaises(ValidationError):
            RenderSettingsModel(resolution_x="not_an_int")


class TestMaterialModel(BaseTestCaseWithErrorHandler):
    """Test MaterialModel validation and functionality."""

    def test_material_model_defaults(self):
        """Test MaterialModel with minimal required fields."""
        material = MaterialModel(name="TestMaterial")
        
        self.assertEqual(material.name, "TestMaterial")
        self.assertIsInstance(material.id, uuid.UUID)
        self.assertEqual(material.base_color_value, [0.8, 0.8, 0.8])
        self.assertIsNone(material.base_color_texture_polyhaven_id)
        self.assertEqual(material.metallic, 0.0)
        self.assertEqual(material.roughness, 0.5)

    def test_material_model_custom_values(self):
        """Test MaterialModel with custom values."""
        custom_id = uuid.uuid4()
        material = MaterialModel(
            id=custom_id,
            name="CustomMaterial",
            base_color_value=[1.0, 0.0, 0.0],
            base_color_texture_polyhaven_id="texture_asset_01",
            metallic=1.0,
            roughness=0.1
        )
        
        self.assertEqual(material.id, custom_id)
        self.assertEqual(material.name, "CustomMaterial")
        self.assertEqual(material.base_color_value, [1.0, 0.0, 0.0])
        self.assertEqual(material.base_color_texture_polyhaven_id, "texture_asset_01")
        self.assertEqual(material.metallic, 1.0)
        self.assertEqual(material.roughness, 0.1)

    def test_material_model_validation(self):
        """Test MaterialModel validation."""
        # Missing required name
        with self.assertRaises(ValidationError):
            MaterialModel()
        
        # Invalid base color
        with self.assertRaises(ValidationError):
            MaterialModel(name="Test", base_color_value=[1.0, 0.0])  # Too short

    def test_material_model_unique_ids(self):
        """Test that MaterialModel generates unique IDs."""
        materials = [MaterialModel(name=f"Material{i}") for i in range(10)]
        ids = [mat.id for mat in materials]
        
        # All IDs should be unique
        self.assertEqual(len(ids), len(set(ids)))


class TestBlenderObjectModel(BaseTestCaseWithErrorHandler):
    """Test BlenderObjectModel validation and functionality."""

    def test_blender_object_defaults(self):
        """Test BlenderObjectModel with minimal required fields."""
        obj = BlenderObjectModel(name="TestObject", type=BlenderObjectType.MESH)
        
        self.assertEqual(obj.name, "TestObject")
        self.assertEqual(obj.type, BlenderObjectType.MESH)
        self.assertIsInstance(obj.id, uuid.UUID)
        self.assertEqual(obj.location, [0.0, 0.0, 0.0])
        self.assertEqual(obj.rotation_euler, [0.0, 0.0, 0.0])
        self.assertEqual(obj.scale, [1.0, 1.0, 1.0])
        self.assertEqual(obj.dimensions, [2.0, 2.0, 2.0])
        self.assertEqual(obj.material_names, [])
        self.assertTrue(obj.is_visible)
        self.assertTrue(obj.is_renderable)
        self.assertIsNone(obj.parent_name)

    def test_blender_object_custom_values(self):
        """Test BlenderObjectModel with custom values."""
        obj = BlenderObjectModel(
            name="CustomObject",
            type=BlenderObjectType.CAMERA,
            location=[1.0, 2.0, 3.0],
            rotation_euler=[0.1, 0.2, 0.3],
            scale=[2.0, 2.0, 2.0],
            dimensions=[4.0, 4.0, 4.0],
            vertex_count=1000,
            material_names=["Material1", "Material2"],
            is_visible=False,
            camera_focal_length=50.0
        )
        
        self.assertEqual(obj.name, "CustomObject")
        self.assertEqual(obj.type, BlenderObjectType.CAMERA)
        self.assertEqual(obj.location, [1.0, 2.0, 3.0])
        self.assertEqual(obj.vertex_count, 1000)
        self.assertEqual(obj.material_names, ["Material1", "Material2"])
        self.assertFalse(obj.is_visible)
        self.assertEqual(obj.camera_focal_length, 50.0)

    def test_blender_object_validation(self):
        """Test BlenderObjectModel validation."""
        # Missing required fields
        with self.assertRaises(ValidationError):
            BlenderObjectModel()
        
        with self.assertRaises(ValidationError):
            BlenderObjectModel(name="Test")  # Missing type
        
        # Invalid type
        with self.assertRaises(ValidationError):
            BlenderObjectModel(name="Test", type="INVALID_TYPE")

    def test_blender_object_type_specific_fields(self):
        """Test type-specific fields in BlenderObjectModel."""
        # Camera object
        camera = BlenderObjectModel(
            name="Camera",
            type=BlenderObjectType.CAMERA,
            camera_focal_length=35.0
        )
        self.assertEqual(camera.camera_focal_length, 35.0)
        
        # Light object
        light = BlenderObjectModel(
            name="Light",
            type=BlenderObjectType.LIGHT,
            light_energy=100.0,
            light_color=[1.0, 0.8, 0.6]
        )
        self.assertEqual(light.light_energy, 100.0)
        self.assertEqual(light.light_color, [1.0, 0.8, 0.6])


class TestBlenderObjectInfoModel(BaseTestCaseWithErrorHandler):
    """Test BlenderObjectInfoModel validation and functionality."""

    def test_blender_object_info_model(self):
        """Test BlenderObjectInfoModel with complete data."""
        obj_info = BlenderObjectInfoModel(
            name="InfoObject",
            type=BlenderObjectType.MESH,
            location=[1.0, 2.0, 3.0],
            rotation_euler=[0.1, 0.2, 0.3],
            scale=[1.5, 1.5, 1.5],
            dimensions=[3.0, 3.0, 3.0],
            vertex_count=500,
            edge_count=750,
            face_count=250,
            material_names=["Mat1", "Mat2"],
            is_visible=True,
            is_renderable=False
        )
        
        self.assertEqual(obj_info.name, "InfoObject")
        self.assertEqual(obj_info.type, BlenderObjectType.MESH)
        self.assertEqual(obj_info.vertex_count, 500)
        self.assertEqual(obj_info.edge_count, 750)
        self.assertEqual(obj_info.face_count, 250)
        self.assertFalse(obj_info.is_renderable)

    def test_blender_object_info_validation(self):
        """Test BlenderObjectInfoModel validation."""
        # Missing required fields
        with self.assertRaises(ValidationError):
            BlenderObjectInfoModel()
        
        # Invalid vector dimensions
        with self.assertRaises(ValidationError):
            BlenderObjectInfoModel(
                name="Test",
                type=BlenderObjectType.MESH,
                location=[1.0, 2.0],  # Too short
                rotation_euler=[0.0, 0.0, 0.0],
                scale=[1.0, 1.0, 1.0],
                dimensions=[2.0, 2.0, 2.0],
                is_visible=True,
                is_renderable=True
            )


class TestSceneModel(BaseTestCaseWithErrorHandler):
    """Test SceneModel validation and functionality."""

    def test_scene_model_defaults(self):
        """Test SceneModel with default values."""
        scene = SceneModel()
        
        self.assertEqual(scene.name, "Scene")
        self.assertIsInstance(scene.id, uuid.UUID)
        self.assertEqual(scene.objects, {})
        self.assertIsNone(scene.active_camera_name)
        self.assertIsInstance(scene.world_settings, WorldSettingsModel)
        self.assertIsInstance(scene.render_settings, RenderSettingsModel)

    def test_scene_model_with_objects(self):
        """Test SceneModel with objects."""
        obj1 = BlenderObjectModel(name="Object1", type=BlenderObjectType.MESH)
        obj2 = BlenderObjectModel(name="Camera1", type=BlenderObjectType.CAMERA)
        
        scene = SceneModel(
            name="TestScene",
            objects={"Object1": obj1, "Camera1": obj2},
            active_camera_name="Camera1"
        )
        
        self.assertEqual(scene.name, "TestScene")
        self.assertEqual(len(scene.objects), 2)
        self.assertEqual(scene.active_camera_name, "Camera1")
        self.assertIn("Object1", scene.objects)
        self.assertIn("Camera1", scene.objects)

    def test_scene_model_properties(self):
        """Test SceneModel computed properties."""
        obj1 = BlenderObjectModel(name="Mesh1", type=BlenderObjectType.MESH)
        obj2 = BlenderObjectModel(name="Camera1", type=BlenderObjectType.CAMERA)
        obj3 = BlenderObjectModel(name="Light1", type=BlenderObjectType.LIGHT)
        obj4 = BlenderObjectModel(name="Camera2", type=BlenderObjectType.CAMERA)
        
        scene = SceneModel(objects={
            "Mesh1": obj1,
            "Camera1": obj2,
            "Light1": obj3,
            "Camera2": obj4
        })
        
        self.assertEqual(scene.camera_count, 2)
        self.assertEqual(scene.light_count, 1)
        self.assertEqual(scene.object_count, 4)

    def test_scene_model_empty(self):
        """Test SceneModel properties with no objects."""
        scene = SceneModel()
        
        self.assertEqual(scene.camera_count, 0)
        self.assertEqual(scene.light_count, 0)
        self.assertEqual(scene.object_count, 0)


class TestPolyhavenModels(BaseTestCaseWithErrorHandler):
    """Test Polyhaven-related models."""

    def test_polyhaven_asset_internal_info(self):
        """Test PolyhavenAssetInternalInfo model."""
        asset = PolyhavenAssetInternalInfo(
            asset_id="test_asset_01",
            name="Test Asset",
            type=PolyhavenAssetTypeData.TEXTURE,
            tags=["wood", "floor"],
            author="Test Author",
            resolution_options=["1k", "2k", "4k"],
            file_format_options=["jpg", "png"],
            is_downloaded=True,
            downloaded_resolution="2k",
            downloaded_file_format="jpg",
            local_file_path="/path/to/asset.jpg"
        )
        
        self.assertEqual(asset.asset_id, "test_asset_01")
        self.assertEqual(asset.name, "Test Asset")
        self.assertEqual(asset.type, PolyhavenAssetTypeData.TEXTURE)
        self.assertEqual(asset.tags, ["wood", "floor"])
        self.assertTrue(asset.is_downloaded)
        self.assertEqual(asset.downloaded_resolution, "2k")

    def test_polyhaven_asset_internal_info_validation(self):
        """Test PolyhavenAssetInternalInfo validation."""
        with self.assertRaises(ValidationError):
            PolyhavenAssetInternalInfo(
                asset_id="test_asset_01",
                type=PolyhavenAssetTypeData.TEXTURE)

        with self.assertRaises(ValidationError):
            PolyhavenAssetInternalInfo(
                asset_id=123,
                name="Test Asset",
                type=PolyhavenAssetTypeData.TEXTURE,
                tags=["wood", "floor"],
                author="Test Author")

    def test_polyhaven_service_status(self):
        """Test PolyhavenServiceStatusModel."""
        status = PolyhavenServiceStatusModel()
        
        self.assertTrue(status.is_enabled)
        self.assertEqual(status.message, "Polyhaven integration is enabled.")
        
        # Custom status
        custom_status = PolyhavenServiceStatusModel(
            is_enabled=False,
            message="Service disabled for testing"
        )
        
        self.assertFalse(custom_status.is_enabled)
        self.assertEqual(custom_status.message, "Service disabled for testing")

    def test_polyhaven_service_status_validation(self):
        """Test PolyhavenServiceStatusModel validation."""
        with self.assertRaises(ValidationError):
            PolyhavenServiceStatusModel(is_enabled="invalid")
        
        with self.assertRaises(ValidationError):
            PolyhavenServiceStatusModel(message=11)

    def test_search_polyhaven_assets_arguments(self):
        """Test SearchPolyhavenAssetsArguments validation."""
        # Valid arguments
        args = SearchPolyhavenAssetsArguments()
        self.assertEqual(args.asset_type, "all")
        self.assertIsNone(args.categories)
        
        # Custom arguments
        custom_args = SearchPolyhavenAssetsArguments(
            asset_type="textures",
            categories="wood,metal"
        )
        self.assertEqual(custom_args.asset_type, "textures")
        self.assertEqual(custom_args.categories, "wood,metal")
        
        # Invalid asset type
        with self.assertRaises(ValidationError):
            SearchPolyhavenAssetsArguments(asset_type="invalid_type")

    def test_download_polyhaven_asset_arguments(self):
        """Test DownloadPolyhavenAssetArguments validation."""
        args = DownloadPolyhavenAssetArguments(
            asset_id="test_asset",
            asset_type="textures"
        )
        
        self.assertEqual(args.asset_id, "test_asset")
        self.assertEqual(args.asset_type, "textures")
        self.assertEqual(args.resolution, "1k")  # Default
        self.assertIsNone(args.file_format)  # Default
        
        # Custom values
        custom_args = DownloadPolyhavenAssetArguments(
            asset_id="custom_asset",
            asset_type="hdris",
            resolution="4k",
            file_format="hdr"
        )
        
        self.assertEqual(custom_args.resolution, "4k")
        self.assertEqual(custom_args.file_format, "hdr")

    def test_download_polyhaven_asset_arguments_validation(self):
        """Test DownloadPolyhavenAssetArguments validation."""
        with self.assertRaises(ValidationError):
            DownloadPolyhavenAssetArguments(asset_id=123, asset_type="invalid_type")
        
        with self.assertRaises(ValidationError):
            DownloadPolyhavenAssetArguments(asset_id="test_asset")


class TestHyper3DModels(BaseTestCaseWithErrorHandler):
    """Test Hyper3D-related models."""

    def test_hyper3d_service_status(self):
        """Test Hyper3DServiceStatusModel."""
        status = Hyper3DServiceStatusModel()
        
        self.assertTrue(status.is_enabled)
        self.assertEqual(status.mode, Hyper3DMode.MAIN_SITE)
        self.assertEqual(status.message, "Hyper3D Rodin integration is enabled.")

    def test_hyper3d_service_status_validation(self):
        """Test Hyper3DServiceStatusModel validation."""
        with self.assertRaises(ValidationError):
            Hyper3DServiceStatusModel(is_enabled="invalid")
        
        with self.assertRaises(ValidationError):
            Hyper3DServiceStatusModel(message=11)

    def test_hyper3d_job_model(self):
        """Test Hyper3DJobModel with various configurations."""
        job = Hyper3DJobModel(
            mode_at_creation=Hyper3DMode.MAIN_SITE,
            text_prompt="Generate a chair",
            submission_status=JobOverallStatus.PENDING
        )
        
        self.assertIsInstance(job.internal_job_id, uuid.UUID)
        self.assertEqual(job.mode_at_creation, Hyper3DMode.MAIN_SITE)
        self.assertEqual(job.text_prompt, "Generate a chair")
        self.assertEqual(job.submission_status, JobOverallStatus.PENDING)
        self.assertEqual(job.poll_overall_status, JobOverallStatus.PENDING)
        
        # Test properties
        self.assertFalse(job.is_completed)
        self.assertIsNone(job.is_successful)

    def test_hyper3d_job_model_completion_states(self):
        """Test Hyper3DJobModel completion properties."""
        # Completed successfully
        completed_job = Hyper3DJobModel(
            mode_at_creation=Hyper3DMode.FAL_AI,
            poll_overall_status=JobOverallStatus.COMPLETED
        )
        
        self.assertTrue(completed_job.is_completed)
        self.assertTrue(completed_job.is_successful)
        
        # Failed job
        failed_job = Hyper3DJobModel(
            mode_at_creation=Hyper3DMode.FAL_AI,
            poll_overall_status=JobOverallStatus.FAILED
        )
        
        self.assertTrue(failed_job.is_completed)
        self.assertFalse(failed_job.is_successful)
        
        # In progress job
        in_progress_job = Hyper3DJobModel(
            mode_at_creation=Hyper3DMode.FAL_AI,
            poll_overall_status=JobOverallStatus.IN_PROGRESS
        )
        
        self.assertFalse(in_progress_job.is_completed)
        self.assertIsNone(in_progress_job.is_successful)

    def test_hyper3d_job_model_validation(self):
        """Test Hyper3DJobModel validation."""
        with self.assertRaises(ValidationError):
            Hyper3DJobModel(mode_at_creation="invalid") 
        with self.assertRaises(ValidationError):
            Hyper3DJobModel(mode_at_creation=Hyper3DMode.FAL_AI, poll_overall_status="invalid")
        


class TestExecutionAndResponseModels(BaseTestCaseWithErrorHandler):
    """Test execution and response models."""

    def test_blender_code_execution_outcome(self):
        """Test BlenderCodeExecutionOutcomeModel."""
        outcome = BlenderCodeExecutionOutcomeModel(
            timestamp="2024-01-15T10:30:00Z",
            code_executed="print('Hello World')",
            status=ExecutionStatus.SUCCESS,
            output="Hello World",
            return_value_str="None"
        )
        
        self.assertIsInstance(outcome.id, uuid.UUID)
        self.assertEqual(outcome.timestamp, "2024-01-15T10:30:00Z")
        self.assertEqual(outcome.code_executed, "print('Hello World')")
        self.assertEqual(outcome.status, ExecutionStatus.SUCCESS)
        self.assertEqual(outcome.output, "Hello World")
        
        # Error case
        error_outcome = BlenderCodeExecutionOutcomeModel(
            timestamp="2024-01-15T10:31:00Z",
            code_executed="raise ValueError('test')",
            status=ExecutionStatus.ERROR,
            error_message="ValueError: test"
        )
        
        self.assertEqual(error_outcome.status, ExecutionStatus.ERROR)
        self.assertEqual(error_outcome.error_message, "ValueError: test")

    def test_blender_code_execution_outcome_validation(self):
        """Test BlenderCodeExecutionOutcomeModel validation."""
        with self.assertRaises(BlenderInvalidDateTimeFormatError):
            BlenderCodeExecutionOutcomeModel(timestamp="invalid")
        with self.assertRaises(ValidationError):
            BlenderCodeExecutionOutcomeModel(code_executed=123)

    def test_generate_hyper3d_response(self):
        """Test GenerateHyper3DModelViaTextResponse."""
        # Success response
        success_response = GenerateHyper3DModelViaTextResponse(
            status="success_queued",
            message="Job queued successfully",
            task_uuid="task_123",
            subscription_key="key_456"
        )
        
        self.assertEqual(success_response.status, "success_queued")
        self.assertEqual(success_response.task_uuid, "task_123")
        
        # Failure response
        failure_response = GenerateHyper3DModelViaTextResponse(
            status="failure",
            message="Failed to queue job"
        )
        
        self.assertEqual(failure_response.status, "failure")
        self.assertIsNone(failure_response.task_uuid)

    def test_generate_hyper3d_response_validation(self):
        """Test GenerateHyper3DModelViaTextResponse validation."""
        with self.assertRaises(ValidationError):
            GenerateHyper3DModelViaTextResponse(status="invalid")
        with self.assertRaises(ValidationError):
            GenerateHyper3DModelViaTextResponse(message=11)

    def test_import_generated_asset_models(self):
        """Test import asset argument and response models."""
        # Arguments
        args = ImportGeneratedAssetArguments(
            name="Generated Chair",
            task_uuid="task_123",
            request_id="req_456"
        )
        
        self.assertEqual(args.name, "Generated Chair")
        self.assertEqual(args.task_uuid, "task_123")
        
        # Response
        response = ImportGeneratedAssetResponse(
            status="success",
            message="Asset imported successfully",
            asset_name_in_blender="Chair_Generated",
            blender_object_type=BlenderObjectType.MESH
        )
        
        self.assertEqual(response.status, "success")
        self.assertEqual(response.asset_name_in_blender, "Chair_Generated")
        self.assertEqual(response.blender_object_type, BlenderObjectType.MESH)

    def test_import_generated_asset_arguments_validation(self):

        with self.assertRaises(ValidationError):
            ImportGeneratedAssetArguments(name=123)


class TestBlenderDB(BaseTestCaseWithErrorHandler):
    """Test the main BlenderDB model."""

    def test_blender_db_defaults(self):
        """Test BlenderDB with default values."""
        db = BlenderDB()
        
        self.assertIsInstance(db.current_scene, SceneModel)
        self.assertEqual(db.materials, {})
        self.assertIsInstance(db.polyhaven_service_status, PolyhavenServiceStatusModel)
        self.assertEqual(db.polyhaven_categories_cache, {})
        self.assertEqual(db.polyhaven_assets_db, {})
        self.assertIsInstance(db.hyper3d_service_status, Hyper3DServiceStatusModel)
        self.assertEqual(db.hyper3d_jobs, {})
        self.assertEqual(db.execution_logs, [])

    def test_blender_db_with_data(self):
        """Test BlenderDB with custom data."""
        # Create some test data
        scene = SceneModel(name="CustomScene")
        material = MaterialModel(name="TestMaterial")
        asset = PolyhavenAssetInternalInfo(
            asset_id="test_asset",
            name="Test Asset",
            type=PolyhavenAssetTypeData.TEXTURE
        )
        job = Hyper3DJobModel(mode_at_creation=Hyper3DMode.MAIN_SITE)
        
        db = BlenderDB(
            current_scene=scene,
            materials={"TestMaterial": material},
            polyhaven_assets_db={"test_asset": asset},
            hyper3d_jobs={job.internal_job_id: job}
        )
        
        self.assertEqual(db.current_scene.name, "CustomScene")
        self.assertIn("TestMaterial", db.materials)
        self.assertIn("test_asset", db.polyhaven_assets_db)
        self.assertEqual(len(db.hyper3d_jobs), 1)

    def test_blender_db_complex_scenario(self):
        """Test BlenderDB with complex nested data."""
        # Create a complex scene
        mesh_obj = BlenderObjectModel(name="Cube", type=BlenderObjectType.MESH)
        camera_obj = BlenderObjectModel(name="Camera", type=BlenderObjectType.CAMERA)
        
        scene = SceneModel(
            name="ComplexScene",
            objects={"Cube": mesh_obj, "Camera": camera_obj},
            active_camera_name="Camera"
        )
        
        # Create materials
        materials = {
            "Material1": MaterialModel(name="Material1"),
            "Material2": MaterialModel(name="Material2")
        }
        
        # Create execution logs
        logs = [
            BlenderCodeExecutionOutcomeModel(
                timestamp="2024-01-15T10:30:00Z",
                code_executed="print('test')",
                status=ExecutionStatus.SUCCESS
            )
        ]
        
        db = BlenderDB(
            current_scene=scene,
            materials=materials,
            execution_logs=logs
        )
        
        self.assertEqual(db.current_scene.object_count, 2)
        self.assertEqual(db.current_scene.camera_count, 1)
        self.assertEqual(len(db.materials), 2)
        self.assertEqual(len(db.execution_logs), 1)

    def test_blender_db_validation(self):
        """Test BlenderDB validation."""
        # Invalid scene type
        with self.assertRaises(ValidationError):
            BlenderDB(current_scene="not_a_scene")
        
        # Invalid materials type
        with self.assertRaises(ValidationError):
            BlenderDB(materials="not_a_dict")


class TestModelIntegration(BaseTestCaseWithErrorHandler):
    """Test integration between different models."""

    def test_scene_with_objects_and_materials(self):
        """Test scene containing objects with materials."""
        # Create materials
        material1 = MaterialModel(name="Wood")
        material2 = MaterialModel(name="Metal")
        
        # Create object with materials
        cube = BlenderObjectModel(
            name="TexturedCube",
            type=BlenderObjectType.MESH,
            material_names=["Wood", "Metal"]
        )
        
        # Create scene
        scene = SceneModel(objects={"TexturedCube": cube})
        
        # Create full DB
        db = BlenderDB(
            current_scene=scene,
            materials={"Wood": material1, "Metal": material2}
        )
        
        # Verify relationships
        self.assertEqual(len(db.current_scene.objects), 1)
        self.assertEqual(len(db.materials), 2)
        cube_in_scene = db.current_scene.objects["TexturedCube"]
        self.assertEqual(cube_in_scene.material_names, ["Wood", "Metal"])
        self.assertIn("Wood", db.materials)
        self.assertIn("Metal", db.materials)

    def test_unicode_content_support(self):
        """Test models with unicode content."""
        # Create objects with unicode names and descriptions
        material = MaterialModel(name="材料_テスト_🎨")
        
        obj = BlenderObjectModel(
            name="オブジェクト_测试_🎯",
            type=BlenderObjectType.MESH
        )
        
        scene = SceneModel(
            name="シーン_场景_🎬",
            objects={"オブジェクト_测试_🎯": obj}
        )
        
        db = BlenderDB(
            current_scene=scene,
            materials={"材料_テスト_🎨": material}
        )
        
        # Verify unicode handling
        self.assertEqual(material.name, "材料_テスト_🎨")
        self.assertEqual(obj.name, "オブジェクト_测试_🎯")
        self.assertEqual(scene.name, "シーン_场景_🎬")

    def test_model_serialization_compatibility(self):
        """Test that models can be properly serialized/deserialized."""
        # Create a complex DB structure
        db = BlenderDB()
        
        # Add some data
        material = MaterialModel(name="TestMaterial")
        db.materials["TestMaterial"] = material
        
        obj = BlenderObjectModel(name="TestObject", type=BlenderObjectType.MESH)
        db.current_scene.objects["TestObject"] = obj
        
        # Convert to dict (simulates JSON serialization)
        db_dict = db.model_dump()
        
        # Verify structure
        self.assertIn("current_scene", db_dict)
        self.assertIn("materials", db_dict)
        self.assertIn("polyhaven_service_status", db_dict)
        
        # Verify nested data
        self.assertIn("TestMaterial", db_dict["materials"])
        self.assertIn("TestObject", db_dict["current_scene"]["objects"])


if __name__ == '__main__':
    unittest.main()
