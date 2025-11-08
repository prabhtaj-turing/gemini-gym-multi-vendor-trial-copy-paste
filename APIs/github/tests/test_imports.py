import sys
import importlib
from pathlib import Path


def test_direct_module_imports():
    """Test importing GitHub modules directly without complex dependencies."""
    print("🔍 Testing direct module imports for github...")

    # Add the APIs directory to sys.path so top-level package imports work
    apis_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(apis_dir))

    print(f"📂 APIs directory: {apis_dir}")

    # Test individual module imports
    modules_to_test = [
        ("github", "Main github module"),
        ("github.SimulationEngine.db", "DB module"),
        ("github.SimulationEngine.models", "Models module"),
        ("github.SimulationEngine.utils", "Utils module"),
        ("github.issues", "Issues module"),
        ("github.pull_requests", "Pull Requests module"),
        ("github.repositories", "Repositories module"),
        ("github.users", "Users module"),
        ("github.code_scanning", "Code Scanning module"),
        ("github.secret_scanning", "Secret Scanning module"),
        # # Mutations subpackage (light coverage)
        # ("github.mutations.m01", "Mutations package m01"),
        # ("github.mutations.m01.issues", "Mutations m01 issues"),
        # ("github.mutations.m01.pull_requests", "Mutations m01 pull_requests"),
        # ("github.mutations.m01.repositories", "Mutations m01 repositories"),
        # ("github.mutations.m01.users", "Mutations m01 users"),
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


