import sys
import importlib
from pathlib import Path


def test_direct_module_imports():
    """Test importing modules directly without complex dependencies."""
    print("🔍 Testing direct module imports for google_home...")

    # Add the APIs directory to sys.path so top-level package imports work
    google_home_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(google_home_dir))

    print(f"📂 APIs directory: {google_home_dir}")

    # Test individual module imports
    modules_to_test = [
        ("google_home", "Main google_home module"),
        ("google_home.SimulationEngine.db", "DB module"),
        ("google_home.SimulationEngine.models", "Models module"),
        ("google_home.SimulationEngine.utils", "Utils module"),
        ("google_home.details_api", "Details API"),
        ("google_home.devices_api", "Devices API"),
        ("google_home.get_devices_api", "Get Devices API"),
        ("google_home.get_all_devices_api", "Get All Devices API"),
        ("google_home.view_schedules_api", "View Schedules API"),
        ("google_home.cancel_schedules_api", "Cancel Schedules API"),
        ("google_home.run_api", "Run API"),
        ("google_home.mutate_api", "Mutate API"),
        ("google_home.mutate_traits_api", "Mutate Traits API"),
        ("google_home.see_devices_api", "See Devices API"),
        ("google_home.search_home_events_api", "Search Home Events API"),
        ("google_home.generate_home_automation_api", "Generate Home Automation API"),
    ]

    import_results = {}

    for module_name, description in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            import_results[module_name] = {
                "status": "success",
                "module": module,
                "attributes": dir(module),
            }
            assert module is not None, f"Module {module_name} imported but is None"
        except ImportError as e:
            import_results[module_name] = {
                "status": "import_error",
                "error": str(e),
            }
            assert False, f"Failed to import {module_name}: {e}"
        except Exception as e:
            import_results[module_name] = {"status": "error", "error": str(e)}
            assert False, f"⚠️ {description}: {module_name} - Error: {e}"

    successful_imports = [
        name for name, result in import_results.items() if result["status"] == "success"
    ]
    print(f"✅ Successful imports: {successful_imports}")

    assert True, import_results


