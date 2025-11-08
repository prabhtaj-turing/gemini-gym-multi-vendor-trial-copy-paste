"""
Test suite for imports in the Blender API simulation.
This is a sample test for how we can check imports for an individual service. 
Along with this, we can check function imports.
"""
import importlib
import sys
import unittest
from pathlib import Path

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestBlenderImports(BaseTestCaseWithErrorHandler):
    """Test importing blender modules directly without complex dependencies."""

    def test_direct_module_imports(self):
        """Test importing modules directly without complex dependencies."""
        print("🔍 Testing direct module imports...")

        # Add the blender directory to path
        blender_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(blender_dir))

        print(f"📂 Blender directory: {blender_dir}")

        # Test individual module imports
        modules_to_test = [
            ("blender", "Main blender module"),
            ("blender.execution", "Execution module"),
            ("blender.object", "Object module"),
            ("blender.scene", "Scene module"),
            ("blender.polyhaven", "Polyhaven module"),
            ("blender.hyper3d", "Hyper3D module"),
        ]

        import_results = {}

        for module_name, description in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "status": "success",
                    "module": module,
                    "attributes": dir(module)
                }
                assert module is not None, f"Module {module_name} imported but is None"
                print(f"✅ {description}: {module_name}")
            except ImportError as e:
                import_results[module_name] = {
                    "status": "import_error",
                    "error": str(e)
                }
                print(f"❌ {description}: {module_name} - ImportError: {e}")
                assert False, f"Failed to import {module_name}: {e}"
            except Exception as e:
                import_results[module_name] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"⚠️ {description}: {module_name} - Error: {e}")
                assert False, f"⚠️ {description}: {module_name} - Error: {e}"

        successful_imports = [name for name, result in import_results.items()
                             if result["status"] == "success"]

        print(f"✅ Successfully imported {len(successful_imports)} modules")
        assert True, import_results

    def test_simulation_engine_imports(self):
        """Test importing SimulationEngine modules directly."""
        print("🔍 Testing SimulationEngine module imports...")

        # Add the blender directory to path
        blender_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(blender_dir))

        print(f"📂 Blender directory: {blender_dir}")

        # Test SimulationEngine module imports
        modules_to_test = [
            ("blender.SimulationEngine", "SimulationEngine main module"),
            ("blender.SimulationEngine.db", "Database module"),
            ("blender.SimulationEngine.models", "Models module"),
            ("blender.SimulationEngine.utils", "Utils module"),
            ("blender.SimulationEngine.file_utils", "File utils module"),
            ("blender.SimulationEngine.custom_errors", "Custom errors module"),
        ]

        import_results = {}

        for module_name, description in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "status": "success",
                    "module": module,
                    "attributes": dir(module)
                }
                assert module is not None, f"Module {module_name} imported but is None"
                print(f"✅ {description}: {module_name}")
            except ImportError as e:
                import_results[module_name] = {
                    "status": "import_error",
                    "error": str(e)
                }
                print(f"❌ {description}: {module_name} - ImportError: {e}")
                assert False, f"Failed to import {module_name}: {e}"
            except Exception as e:
                import_results[module_name] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"⚠️ {description}: {module_name} - Error: {e}")
                assert False, f"⚠️ {description}: {module_name} - Error: {e}"

        successful_imports = [name for name, result in import_results.items()
                             if result["status"] == "success"]

        print(f"✅ Successfully imported {len(successful_imports)} SimulationEngine modules")
        assert True, import_results

    def test_function_imports(self):
        """Test importing specific functions from modules."""
        print("🔍 Testing function imports...")

        # Add the blender directory to path
        blender_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(blender_dir))

        print(f"📂 Blender directory: {blender_dir}")

        # Test function imports
        functions_to_test = [
            ("blender.execution", "execute_blender_code", "Execute Blender code function"),
            ("blender.object", "get_object_info", "Get object info function"),
            ("blender.object", "set_texture", "Set texture function"),
            ("blender.scene", "get_scene_info", "Get scene info function"),
            ("blender.polyhaven", "get_polyhaven_categories", "Get categories function"),
            ("blender.polyhaven", "search_polyhaven_assets", "Search assets function"),
            ("blender.polyhaven", "download_polyhaven_asset", "Download asset function"),
            ("blender.polyhaven", "get_polyhaven_status", "Get status function"),
            ("blender.hyper3d", "get_hyper3d_status", "Get Hyper3D status function"),
            ("blender.hyper3d", "generate_hyper3d_model_via_text", "Generate via text function"),
            ("blender.hyper3d", "generate_hyper3d_model_via_images", "Generate via images function"),
            ("blender.hyper3d", "poll_rodin_job_status", "Poll job status function"),
            ("blender.hyper3d", "import_generated_asset", "Import asset function"),
        ]

        import_results = {}

        for module_name, function_name, description in functions_to_test:
            try:
                module = importlib.import_module(module_name)
                function = getattr(module, function_name)
                
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "success",
                    "module": module,
                    "function": function,
                    "callable": callable(function)
                }
                
                assert function is not None, f"Function {function_name} in {module_name} is None"
                assert callable(function), f"Function {function_name} in {module_name} is not callable"
                print(f"✅ {description}: {module_name}.{function_name}")
                
            except ImportError as e:
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "import_error",
                    "error": str(e)
                }
                print(f"❌ {description}: {module_name}.{function_name} - ImportError: {e}")
                assert False, f"Failed to import {module_name}: {e}"
            except AttributeError as e:
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "attribute_error",
                    "error": str(e)
                }
                print(f"❌ {description}: {module_name}.{function_name} - AttributeError: {e}")
                assert False, f"Function {function_name} not found in {module_name}: {e}"
            except Exception as e:
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"⚠️ {description}: {module_name}.{function_name} - Error: {e}")
                assert False, f"⚠️ {description}: {module_name}.{function_name} - Error: {e}"

        successful_imports = [name for name, result in import_results.items()
                             if result["status"] == "success"]

        print(f"✅ Successfully imported {len(successful_imports)} functions")
        assert True, import_results

    def test_utility_function_imports(self):
        """Test importing utility functions from SimulationEngine."""
        print("🔍 Testing utility function imports...")

        # Add the blender directory to path
        blender_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(blender_dir))

        print(f"📂 Blender directory: {blender_dir}")

        # Test utility function imports
        utility_functions_to_test = [
            ("blender.SimulationEngine.utils", "add_object_to_scene", "Add object to scene function"),
            ("blender.SimulationEngine.utils", "remove_object_from_scene", "Remove object from scene function"),
            ("blender.SimulationEngine.utils", "get_scene_data_dict", "Get scene data function"),
            ("blender.SimulationEngine.utils", "get_object_data_dict", "Get object data function"),
            ("blender.SimulationEngine.utils", "get_material_data_dict", "Get material data function"),
            ("blender.SimulationEngine.utils", "create_material", "Create material function"),
            ("blender.SimulationEngine.utils", "apply_texture_to_material", "Apply texture function"),
            ("blender.SimulationEngine.utils", "assign_material_to_object", "Assign material function"),
            ("blender.SimulationEngine.file_utils", "read_file", "Read file function"),
            ("blender.SimulationEngine.file_utils", "write_file", "Write file function"),
            ("blender.SimulationEngine.file_utils", "is_text_file", "Is text file function"),
            ("blender.SimulationEngine.file_utils", "is_binary_file", "Is binary file function"),
            ("blender.SimulationEngine.file_utils", "get_mime_type", "Get MIME type function"),
            ("blender.SimulationEngine.db", "save_state", "Save state function"),
            ("blender.SimulationEngine.db", "load_state", "Load state function"),
        ]

        import_results = {}

        for module_name, function_name, description in utility_functions_to_test:
            try:
                module = importlib.import_module(module_name)
                function = getattr(module, function_name)
                
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "success",
                    "module": module,
                    "function": function,
                    "callable": callable(function)
                }
                
                assert function is not None, f"Function {function_name} in {module_name} is None"
                assert callable(function), f"Function {function_name} in {module_name} is not callable"
                print(f"✅ {description}: {module_name}.{function_name}")
                
            except ImportError as e:
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "import_error",
                    "error": str(e)
                }
                print(f"❌ {description}: {module_name}.{function_name} - ImportError: {e}")
                assert False, f"Failed to import {module_name}: {e}"
            except AttributeError as e:
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "attribute_error",
                    "error": str(e)
                }
                print(f"❌ {description}: {module_name}.{function_name} - AttributeError: {e}")
                assert False, f"Function {function_name} not found in {module_name}: {e}"
            except Exception as e:
                import_results[f"{module_name}.{function_name}"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"⚠️ {description}: {module_name}.{function_name} - Error: {e}")
                assert False, f"⚠️ {description}: {module_name}.{function_name} - Error: {e}"

        successful_imports = [name for name, result in import_results.items()
                             if result["status"] == "success"]

        print(f"✅ Successfully imported {len(successful_imports)} utility functions")
        assert True, import_results

    def test_main_blender_package_interface(self):
        """Test the main blender package interface using __getattr__."""
        print("🔍 Testing main blender package interface...")

        # Add the blender directory to path
        blender_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(blender_dir))

        print(f"📂 Blender directory: {blender_dir}")

        # Test main package interface functions
        interface_functions_to_test = [
            ("run_python_script_in_blender", "Run Python script function"),
            ("get_hyper3d_status", "Get Hyper3D status function"),
            ("generate_hyper3d_model_via_text", "Generate via text function"),
            ("generate_hyper3d_model_via_images", "Generate via images function"),
            ("poll_hyper3d_rodin_job_status", "Poll job status function"),
            ("import_hyper3d_generated_asset", "Import asset function"),
            ("get_object_info", "Get object info function"),
            ("set_object_texture", "Set object texture function"),
            ("get_polyhaven_categories", "Get categories function"),
            ("search_polyhaven_assets", "Search assets function"),
            ("download_polyhaven_asset", "Download asset function"),
            ("get_polyhaven_status", "Get status function"),
            ("get_scene_info", "Get scene info function"),
        ]

        import_results = {}

        try:
            import blender
            
            for function_name, description in interface_functions_to_test:
                try:
                    function = getattr(blender, function_name)
                    
                    import_results[f"blender.{function_name}"] = {
                        "status": "success",
                        "function": function,
                        "callable": callable(function)
                    }
                    
                    assert function is not None, f"Function {function_name} in blender package is None"
                    assert callable(function), f"Function {function_name} in blender package is not callable"
                    print(f"✅ {description}: blender.{function_name}")
                    
                except AttributeError as e:
                    import_results[f"blender.{function_name}"] = {
                        "status": "attribute_error",
                        "error": str(e)
                    }
                    print(f"❌ {description}: blender.{function_name} - AttributeError: {e}")
                    assert False, f"Function {function_name} not accessible via blender package: {e}"
                except Exception as e:
                    import_results[f"blender.{function_name}"] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"⚠️ {description}: blender.{function_name} - Error: {e}")
                    assert False, f"⚠️ {description}: blender.{function_name} - Error: {e}"
                    
        except ImportError as e:
            print(f"❌ Failed to import main blender package: {e}")
            assert False, f"Failed to import blender package: {e}"

        successful_imports = [name for name, result in import_results.items()
                             if result["status"] == "success"]

        print(f"✅ Successfully accessed {len(successful_imports)} interface functions")
        assert True, import_results


if __name__ == '__main__':
    unittest.main()
