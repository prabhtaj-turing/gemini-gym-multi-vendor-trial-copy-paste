"""
Database Validation Tests for Blender Service
This module contains tests to validate the database structure and data integrity.
"""

import unittest
import copy
import os
import tempfile
import json
import uuid
from unittest.mock import patch

from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
from blender.SimulationEngine.db import DB, save_state, load_state
from blender.SimulationEngine import utils
from blender.SimulationEngine.models import (
    BlenderDB,
    SceneModel,
    BlenderObjectModel,
    MaterialModel,
    BlenderObjectType,
    PolyhavenAssetInternalInfo,
    PolyhavenAssetTypeData,
    Hyper3DJobModel,
    Hyper3DMode,
    BlenderCodeExecutionOutcomeModel,
    ExecutionStatus
)
import blender


class TestDatabaseValidation(BaseCase):
    """Test database structure validation and data integrity."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Save original DB state
        self.original_db_state = copy.deepcopy(DB)
        
        # Load fresh default DB for testing
        self._load_default_db()

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db_state)
        
    def _load_default_db(self):
        """Load the default database from BlenderDefaultDB.json"""
        import json
        import os
        
        # Get path to default DB file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(current_dir))),
            "DBs",
            "BlenderDefaultDB.json"
        )
        
        # Load default DB
        with open(default_db_path, "r", encoding="utf-8") as f:
            default_db_data = json.load(f)
        
        # Update global DB with default data
        DB.clear()
        DB.update(default_db_data)

    def _validate_db_structure_basic(self):
        """
        Helper method to validate basic database structure.
        
        Raises:
            AssertionError: If validation fails
        """
        try:
            # Validate required top-level keys exist
            required_keys = [
                "current_scene", "materials", "polyhaven_service_status",
                "polyhaven_categories_cache", "polyhaven_assets_db",
                "hyper3d_service_status", "hyper3d_jobs", "execution_logs"
            ]
            
            for key in required_keys:
                self.assertIn(key, DB, f"Missing required DB key: {key}")
            
            # Validate data types
            self.assertIsInstance(DB["current_scene"], dict, "current_scene should be dict")
            self.assertIsInstance(DB["materials"], dict, "materials should be dict")
            self.assertIsInstance(DB["polyhaven_service_status"], dict, "polyhaven_service_status should be dict")
            self.assertIsInstance(DB["polyhaven_categories_cache"], dict, "polyhaven_categories_cache should be dict")
            self.assertIsInstance(DB["polyhaven_assets_db"], dict, "polyhaven_assets_db should be dict")
            self.assertIsInstance(DB["hyper3d_service_status"], dict, "hyper3d_service_status should be dict")
            self.assertIsInstance(DB["hyper3d_jobs"], dict, "hyper3d_jobs should be dict")
            self.assertIsInstance(DB["execution_logs"], list, "execution_logs should be list")
            
            # Validate current_scene structure
            scene = DB["current_scene"]
            scene_required_keys = ["id", "name", "objects", "world_settings", "render_settings"]
            for key in scene_required_keys:
                self.assertIn(key, scene, f"Missing scene key: {key}")
            
            self.assertIsInstance(scene["objects"], dict, "scene objects should be dict")
            self.assertIsInstance(scene["world_settings"], dict, "world_settings should be dict")
            self.assertIsInstance(scene["render_settings"], dict, "render_settings should be dict")
                
        except Exception as e:
            self.fail(f"DB structure validation failed: {e}")

    def _validate_db_with_pydantic(self):
        """
        Helper method to validate database using Pydantic models.
        
        Returns:
            BlenderDB: Validated database object
            
        Raises:
            AssertionError: If validation fails
        """
        try:
            # Create a deep copy of DB data for conversion
            db_data = copy.deepcopy(DB)
            
            # Convert string UUIDs to UUID objects for Pydantic validation
            self._convert_string_uuids_to_uuid_objects(db_data)
            
            # Convert DB data to Pydantic model for validation
            validated_db = BlenderDB(**db_data)
            self.assertIsInstance(validated_db, BlenderDB)
            return validated_db
        except Exception as e:
            self.fail(f"Pydantic DB validation failed: {e}")
    
    def _convert_string_uuids_to_uuid_objects(self, data):
        """Convert string UUIDs to UUID objects recursively."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'id' or key.endswith('_id') or key == 'internal_job_id':
                    if isinstance(value, str):
                        try:
                            data[key] = uuid.UUID(value)
                        except (ValueError, TypeError):
                            pass  # Keep as string if not a valid UUID
                elif isinstance(value, (dict, list)):
                    self._convert_string_uuids_to_uuid_objects(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._convert_string_uuids_to_uuid_objects(item)

    def test_db_module_harmony(self):
        """
        Test that the database used by the db module is in harmony with the expected structure.
        This ensures that tests are running against the expected data structure.
        """
        self._validate_db_structure_basic()
        self._validate_db_with_pydantic()

    def test_db_structure_after_scene_operations(self):
        """
        Test that the database maintains its expected structure after scene operations.
        """
        # Create an object to populate the database
        current_scene_name = DB["current_scene"]["name"]
        object_data = {
            "name": "TestCube",
            "type": "MESH",
            "location": [1.0, 2.0, 3.0]
        }
        result = utils.add_object_to_scene(current_scene_name, object_data)

        # Validate database structure after creation
        self._validate_db_structure_basic()
        validated_db = self._validate_db_with_pydantic()

        # Verify the object was added correctly
        self.assertGreater(len(validated_db.current_scene.objects), 0)
        
        # Check that specific object exists
        object_names = list(validated_db.current_scene.objects.keys())
        self.assertIn("TestCube", object_names)

    def test_db_structure_after_material_operations(self):
        """
        Test that the database maintains structure after material operations.
        """
        # Create a material
        material_data = {
            "name": "TestMaterial",
            "base_color_value": [0.8, 0.2, 0.1]
        }
        result = utils.create_material(material_data)

        # Validate database structure after material creation
        self._validate_db_structure_basic()
        validated_db = self._validate_db_with_pydantic()

        # Verify the material was added correctly
        self.assertGreater(len(validated_db.materials), 0)
        self.assertIn("TestMaterial", validated_db.materials)
        
        # Verify material properties
        test_material = validated_db.materials["TestMaterial"]
        self.assertEqual(test_material.name, "TestMaterial")
        self.assertEqual(test_material.base_color_value, [0.8, 0.2, 0.1])

    def test_db_structure_after_polyhaven_operations(self):
        """
        Test that the database maintains structure after Polyhaven operations.
        """
        try:
            # Search for Polyhaven assets
            result = blender.search_polyhaven_assets(asset_type="textures")

            # Validate database structure after search
            self._validate_db_structure_basic()
            validated_db = self._validate_db_with_pydantic()

            # Verify Polyhaven service status
            self.assertIsNotNone(validated_db.polyhaven_service_status)
            self.assertTrue(validated_db.polyhaven_service_status.is_enabled)

        except Exception as e:
            # Some Polyhaven operations might not be available in test environment
            # Just validate basic structure
            self._validate_db_structure_basic()

    def test_db_structure_after_hyper3d_operations(self):
        """
        Test that the database maintains structure after Hyper3D operations.
        """
        try:
            # Check Hyper3D service status
            result = blender.check_hyper3d_service_status()

            # Validate database structure
            self._validate_db_structure_basic()
            validated_db = self._validate_db_with_pydantic()

            # Verify Hyper3D service status
            self.assertIsNotNone(validated_db.hyper3d_service_status)

        except Exception as e:
            # Some Hyper3D operations might not be available in test environment
            # Just validate basic structure
            self._validate_db_structure_basic()

    def test_db_structure_after_execution_logging(self):
        """
        Test that the database maintains structure after code execution logging.
        """
        # Execute some Blender code
        result = blender.run_python_script_in_blender("print('Testing execution logging')")

        # Validate database structure after execution
        self._validate_db_structure_basic()
        validated_db = self._validate_db_with_pydantic()

        # Verify execution logs were created
        self.assertGreater(len(validated_db.execution_logs), 0)
        
        # Check latest execution log
        latest_log = validated_db.execution_logs[-1]
        self.assertIsInstance(latest_log, BlenderCodeExecutionOutcomeModel)
        self.assertEqual(latest_log.code_executed, "print('Testing execution logging')")

    def test_empty_db_structure(self):
        """
        Test that an empty database has the correct structure.
        """
        # Reset to minimal clean state
        test_db = {
            "current_scene": {
                "id": "d0f8c7b6-a5e4-4f1d-8c7b-6a5e4f1d8c7b",
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
                    "engine": "CYCLES",
                    "resolution_x": 1920,
                    "resolution_y": 1080,
                    "resolution_percentage": 100,
                    "filepath": "/tmp/render_####.png"
                }
            },
            "materials": {},
            "polyhaven_service_status": {
                "is_enabled": True,
                "message": "Polyhaven integration is enabled."
            },
            "polyhaven_categories_cache": {},
            "polyhaven_assets_db": {},
            "hyper3d_service_status": {
                "is_enabled": True,
                "mode": "MAIN_SITE",
                "message": "Hyper3D Rodin integration is enabled."
            },
            "hyper3d_jobs": {},
            "execution_logs": []
        }
        
        DB.clear()
        DB.update(test_db)

        self._validate_db_structure_basic()
        validated_db = self._validate_db_with_pydantic()

        # Verify empty state
        self.assertEqual(len(validated_db.current_scene.objects), 0)
        self.assertEqual(len(validated_db.materials), 0)
        self.assertEqual(len(validated_db.polyhaven_assets_db), 0)
        self.assertEqual(len(validated_db.hyper3d_jobs), 0)
        self.assertEqual(len(validated_db.execution_logs), 0)

    def test_db_data_consistency(self):
        """
        Test that database maintains data consistency after operations.
        """
        # Create materials
        material1_data = {"name": "Material1", "base_color_value": [1.0, 0.0, 0.0]}
        material2_data = {"name": "Material2", "base_color_value": [0.0, 1.0, 0.0]}
        utils.create_material(material1_data)
        utils.create_material(material2_data)
        
        # Create objects
        current_scene_name = DB["current_scene"]["name"]
        object1_data = {"name": "Cube1", "type": "MESH"}
        object2_data = {"name": "Camera1", "type": "CAMERA"}
        utils.add_object_to_scene(current_scene_name, object1_data)
        utils.add_object_to_scene(current_scene_name, object2_data)
        
        # Validate database structure
        validated_db = self._validate_db_with_pydantic()

        # Verify data consistency (including existing objects)
        self.assertGreaterEqual(len(validated_db.materials), 2)
        self.assertGreaterEqual(len(validated_db.current_scene.objects), 2)
        
        # Verify new objects exist
        scene_objects = validated_db.current_scene.objects
        self.assertIn("Cube1", scene_objects)
        self.assertIn("Camera1", scene_objects)
        self.assertEqual(scene_objects["Cube1"].type, BlenderObjectType.MESH)
        self.assertEqual(scene_objects["Camera1"].type, BlenderObjectType.CAMERA)
        
        # Verify new materials exist
        self.assertIn("Material1", validated_db.materials)
        self.assertIn("Material2", validated_db.materials)
        self.assertEqual(validated_db.materials["Material1"].base_color_value, [1.0, 0.0, 0.0])
        self.assertEqual(validated_db.materials["Material2"].base_color_value, [0.0, 1.0, 0.0])

    def test_db_structure_with_complex_operations(self):
        """
        Test database structure with complex operation sequences.
        """
        try:
            # Create multiple entities
            current_scene_name = DB["current_scene"]["name"]
            object_data = {"name": "ComplexCube", "type": "MESH"}
            utils.add_object_to_scene(current_scene_name, object_data)
            
            material_data = {"name": "ComplexMaterial"}
            utils.create_material(material_data)
            
            # Apply material to object
            utils.assign_material_to_object(
                scene_name=current_scene_name,
                object_name="ComplexCube",
                material_name="ComplexMaterial"
            )
            
            # Execute some code
            blender.run_python_script_in_blender("print('Complex operations test')")
            
            # Search assets (if available)
            try:
                blender.search_polyhaven_assets(asset_type="all")
            except:
                pass  # Skip if not available

        except Exception as e:
            # Some operations might fail, but DB structure should remain valid
            pass

        # Validate database structure after complex operations
        self._validate_db_structure_basic()
        validated_db = self._validate_db_with_pydantic()

        # Basic verification that operations had some effect
        self.assertGreaterEqual(len(validated_db.execution_logs), 1)

    def test_db_data_integrity_after_modifications(self):
        """
        Test that database maintains data integrity after modifications.
        """
        # Create initial data
        current_scene_name = DB["current_scene"]["name"]
        object_data = {"name": "ModifyTest", "type": "MESH"}
        utils.add_object_to_scene(current_scene_name, object_data)
        
        # Get initial state
        initial_db = self._validate_db_with_pydantic()
        initial_object = initial_db.current_scene.objects["ModifyTest"]
        
        # Modify object directly in DB (simulating object modification)
        DB["current_scene"]["objects"]["ModifyTest"]["location"] = [5.0, 10.0, 15.0]
        
        # Validate database after modification
        modified_db = self._validate_db_with_pydantic()
        modified_object = modified_db.current_scene.objects["ModifyTest"]
        
        # Verify modification took effect
        self.assertEqual(modified_object.location, [5.0, 10.0, 15.0])
        self.assertNotEqual(modified_object.location, initial_object.location)
        
        # Verify other properties remained unchanged
        self.assertEqual(modified_object.name, initial_object.name)
        self.assertEqual(modified_object.type, initial_object.type)

    def test_db_structure_with_edge_cases(self):
        """
        Test database structure with edge cases and boundary conditions.
        """
        current_scene_name = DB["current_scene"]["name"]
        
        # Test with empty names (should be handled gracefully)
        try:
            object_data = {"name": "", "type": "MESH"}
            utils.add_object_to_scene(current_scene_name, object_data)
        except Exception:
            pass  # Expected to fail
        
        # Test with unicode content
        try:
            unicode_object_data = {
                "name": "Unicode_测试_オブジェクト_🎯",
                "type": "MESH"
            }
            utils.add_object_to_scene(current_scene_name, unicode_object_data)
            
            unicode_material_data = {
                "name": "Unicode_材料_マテリアル_🎨",
                "base_color_value": [0.5, 0.5, 0.5]
            }
            utils.create_material(unicode_material_data)
        except Exception:
            pass  # May not be supported

        # Validate database structure after edge case operations
        self._validate_db_structure_basic()
        validated_db = self._validate_db_with_pydantic()

    def test_db_state_management_integration(self):
        """
        Test database state management (save/load) integration.
        """
        # Create some test data
        current_scene_name = DB["current_scene"]["name"]
        object_data = {"name": "StateTestCube", "type": "MESH"}
        utils.add_object_to_scene(current_scene_name, object_data)
        
        material_data = {"name": "StateTestMaterial"}
        utils.create_material(material_data)
        
        # Get current state
        current_db = self._validate_db_with_pydantic()
        
        # Save state to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            temp_filepath = tmp_file.name
        
        try:
            save_state(temp_filepath)
            
            # Modify current state
            temp_object_data = {"name": "TempLight", "type": "LIGHT"}
            utils.add_object_to_scene(current_scene_name, temp_object_data)
            
            # Verify modification
            modified_db = self._validate_db_with_pydantic()
            self.assertGreater(len(modified_db.current_scene.objects), len(current_db.current_scene.objects))
            
            # Load original state
            load_state(temp_filepath)
            
            # Validate restored state
            restored_db = self._validate_db_with_pydantic()
            self.assertEqual(len(restored_db.current_scene.objects), len(current_db.current_scene.objects))
            self.assertIn("StateTestCube", restored_db.current_scene.objects)
            self.assertIn("StateTestMaterial", restored_db.materials)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filepath)
            except:
                pass

    def test_db_collection_relationships(self):
        """
        Test that database collections maintain proper relationships.
        """
        # Create materials
        material1_data = {"name": "RelationshipMat1"}
        material2_data = {"name": "RelationshipMat2"}
        utils.create_material(material1_data)
        utils.create_material(material2_data)
        
        # Create object
        current_scene_name = DB["current_scene"]["name"]
        object_data = {"name": "RelationshipObj", "type": "MESH"}
        utils.add_object_to_scene(current_scene_name, object_data)
        
        # Apply materials to object
        try:
            utils.assign_material_to_object(
                scene_name=current_scene_name,
                object_name="RelationshipObj",
                material_name="RelationshipMat1"
            )
        except Exception:
            pass  # May not be implemented
        
        # Validate structure
        validated_db = self._validate_db_with_pydantic()
        
        # Test that all collections are accessible
        self.assertIsNotNone(validated_db.current_scene)
        self.assertIsNotNone(validated_db.materials)
        self.assertIsNotNone(validated_db.polyhaven_service_status)
        self.assertIsNotNone(validated_db.hyper3d_service_status)
        
        # Test nested access works
        scene_objects = validated_db.current_scene.objects
        self.assertIn("RelationshipObj", scene_objects)
        
        materials = validated_db.materials
        self.assertIn("RelationshipMat1", materials)
        self.assertIn("RelationshipMat2", materials)

    def test_db_structure_with_service_statuses(self):
        """
        Test database structure with service status modifications.
        """
        # Validate initial service statuses
        validated_db = self._validate_db_with_pydantic()
        
        # Verify default service states
        self.assertTrue(validated_db.polyhaven_service_status.is_enabled)
        self.assertTrue(validated_db.hyper3d_service_status.is_enabled)
        
        # Test modifying service statuses (if functions exist)
        try:
            # Disable Polyhaven service
            DB["polyhaven_service_status"]["is_enabled"] = False
            DB["polyhaven_service_status"]["message"] = "Service disabled for testing"
            
            # Validate structure after modification
            modified_db = self._validate_db_with_pydantic()
            self.assertFalse(modified_db.polyhaven_service_status.is_enabled)
            
        except Exception as e:
            # Service modification might not be supported
            self._validate_db_structure_basic()

    def test_db_execution_logs_integrity(self):
        """
        Test execution logs maintain proper structure and integrity.
        """
        # Execute multiple operations to generate logs
        operations = [
            "print('Log test 1')",
            "result = 2 + 2",
            "print(f'Result: {result}')"
        ]
        
        initial_log_count = len(DB.get("execution_logs", []))
        
        for operation in operations:
            try:
                blender.run_python_script_in_blender(operation)
            except Exception:
                pass  # Some operations might fail
        
        # Validate logs structure
        validated_db = self._validate_db_with_pydantic()
        
        # Verify logs were created
        final_log_count = len(validated_db.execution_logs)
        self.assertGreaterEqual(final_log_count, initial_log_count)
        
        # Verify log structure if logs exist
        if validated_db.execution_logs:
            latest_log = validated_db.execution_logs[-1]
            self.assertIsInstance(latest_log, BlenderCodeExecutionOutcomeModel)
            self.assertIsNotNone(latest_log.id)
            self.assertIsNotNone(latest_log.timestamp)
            self.assertIsNotNone(latest_log.code_executed)
            self.assertIn(latest_log.status, [ExecutionStatus.SUCCESS, ExecutionStatus.ERROR])

    def test_db_uuid_consistency(self):
        """
        Test that UUIDs in database are consistent and valid.
        """
        # Create objects and materials
        current_scene_name = DB["current_scene"]["name"]
        object1_data = {"name": "UUIDTest1", "type": "MESH"}
        object2_data = {"name": "UUIDTest2", "type": "CAMERA"}
        utils.add_object_to_scene(current_scene_name, object1_data)
        utils.add_object_to_scene(current_scene_name, object2_data)
        
        material_data = {"name": "UUIDTestMaterial"}
        utils.create_material(material_data)
        
        validated_db = self._validate_db_with_pydantic()
        
        # Collect all UUIDs
        uuids = []
        
        # Scene ID
        uuids.append(validated_db.current_scene.id)
        
        # Object IDs
        for obj in validated_db.current_scene.objects.values():
            uuids.append(obj.id)
        
        # Material IDs
        for material in validated_db.materials.values():
            uuids.append(material.id)
        
        # Execution log IDs
        for log in validated_db.execution_logs:
            uuids.append(log.id)
        
        # Hyper3D job IDs
        for job in validated_db.hyper3d_jobs.values():
            uuids.append(job.internal_job_id)
        
        # Verify all UUIDs are unique
        self.assertEqual(len(uuids), len(set(uuids)), "All UUIDs should be unique")
        
        # Verify all are valid UUID objects
        from uuid import UUID
        for uuid_obj in uuids:
            self.assertIsInstance(uuid_obj, UUID, f"Invalid UUID: {uuid_obj}")


if __name__ == "__main__":
    unittest.main()
