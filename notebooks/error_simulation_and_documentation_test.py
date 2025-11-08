#%% [markdown]
# # Framework Features Test: Error Simulation & Documentation

# This notebook validates two key features of the API framework:
# 1.  **Error Simulation**: Verifies that a central configuration is automatically applied to a service's error simulator upon module import.
# 2.  **Documentation Generation**: Verifies that documentation can be generated with varying levels of detail based on a dynamically applied configuration.

#%%
# =============================================================================
# 1. SETUP & INITIALIZATION
# =============================================================================
print("="*60)
print("📦 1. Setting up the environment...")
print("="*60)

import sys
import os
import json
from pathlib import Path
import importlib

# Find and set the project root directory
base_dir = Path("/home/ngota/Turing/Workspace 2/google-api-gen-2")
while not (base_dir / 'default_framework_config.json').exists() and base_dir.parent != base_dir:
    base_dir = base_dir.parent

if not (base_dir / 'default_framework_config.json').exists():
    # As a fallback, use the known path if running from an unexpected location
    base_dir = Path("/home/ngota/Turing/Workspace 2/google-api-gen-2")

print(f"Project root identified as: {base_dir}")
print(f"Changing working directory to: {base_dir}")
os.chdir(base_dir)

# Add necessary directories to the Python path
# According to my memory, PYTHONPATH should be set to the APIs directory [[memory:2958240]]
apis_dir = base_dir / "APIs"
scripts_dir = base_dir / "Scripts"
if str(apis_dir) not in sys.path: sys.path.append(str(apis_dir))
if str(scripts_dir) not in sys.path: sys.path.append(str(scripts_dir))
if str(base_dir) not in sys.path: sys.path.append(str(base_dir))

print("\nPython paths configured.")
for p in sys.path:
    print(f"  - {p}")
#%%
# Import framework modules now that paths are set
from common_utils.framework_feature import framework_feature_manager
import Scripts.FCSpec_depricated as fcspec
from common_utils.ErrorSimulation import ErrorSimulator
config_path = "/home/ngota/Turing/Workspace 2/google-api-gen-2/default_framework_config.json"
with open(config_path, 'r') as f:
    central_config = json.load(f)
    print(central_config)
framework_feature_manager.apply_config(central_config)
print("\n✅ Environment setup complete.")

#%%
import gmail
gmail.add_new_label()
from gmail import error_simulator
error_simulator.get_debug_state()
#%%
from common_utils.error_simulation_manager import APPLY_CENTRAL_CONFIG
APPLY_CENTRAL_CONFIG
#%%
# =============================================================================
# 2. ERROR SIMULATION TEST
# =============================================================================
print("\n" + "="*60)
print("🔬 2. Testing Error Simulation (Apply-First Scenario)")
print("="*60)

# Load the central config to define our test case
config_path = base_dir / "default_framework_config.json"
print(f"Loading central configuration from: {config_path}\n")
with open(config_path, 'r') as f:
    central_config = json.load(f)

# The core of the test: apply the configuration BEFORE the service is imported.
# The framework should cache this configuration and apply it automatically
# when the gmail module is imported for the first time.
print("Applying the central configuration globally...")
framework_feature_manager.apply_config(config=central_config)
print("Central configuration has been applied and cached.\n")
print("-" * 60)

# Now, import the 'gmail' module. Its __init__.py will call the
# create_error_simulator factory, which should now find and apply
# the configuration from the cache.
print("Importing the 'gmail' service...")
import gmail
from gmail import error_simulator
print("Import successful.")
print("-" * 60)

# Verify that the simulator's state matches the centrally-applied config.
print("Verifying the debug state of 'gmail.error_simulator'...")
final_state = error_simulator.get_debug_state()
print(json.dumps(final_state, indent=2))

expected_prob = central_config["error"]["gmail"]["config"]["RuntimeError"]["probability"]
actual_prob = final_state.get("current_probabilities", {}).get("RuntimeError", {})

assert actual_prob == expected_prob, f"Test Failed: Expected probability {expected_prob}, but got {actual_prob}"

# Clean up by rolling back the global config
print("\nRolling back the central configuration...")
framework_feature_manager.revert_all()

print("\n✅ Test Passed: Error simulator was correctly configured upon import from a pre-applied central config.")

#%%
schemas_folder = base_dir / "Schemas" / "test_run"
os.makedirs(schemas_folder, exist_ok=True)
for service in ["github", "gmail"]:
    current_mode = fcspec.get_current_doc_mode(service)
    print(f"  - Generating for '{service}' with doc_mode '{current_mode}'...")
    fcspec.generate_package_schema(
        package_path=str(apis_dir / service),
        output_folder_path=str(schemas_folder),
        doc_mode=current_mode,
        package_import_prefix=service,
        output_file_name=f"{service}.json"
    )
#%%
# =============================================================================
# 3. DOCUMENTATION GENERATION TEST
# =============================================================================
print("\n" + "="*60)
print("📝 3. Testing Documentation Generation")
print("="*60)

# Define a temporary, dynamic configuration for this test
doc_test_config = {
    "documentation": {
        "global": {"doc_mode": "concise"},
        "services": {
            "github": {"doc_mode": "raw_docstring"},
            "gmail": {"doc_mode": "medium_detail"}
        }
    }
}

print("\nApplying temporary documentation configuration:")
print(json.dumps(doc_test_config, indent=2))
# Apply the dynamic config
framework_feature_manager.apply_config(doc_test_config)
print("\n✅ Configuration applied!")

# Check that the doc modes were set correctly for different services
print("\nVerifying current documentation modes:")
test_services = {"github": "raw_docstring", "gmail": "medium_detail", "google_calendar": "concise"}
for service, expected_mode in test_services.items():
    actual_mode = fcspec.get_current_doc_mode(service)
    assert actual_mode == expected_mode
    print(f"  - {service}: {actual_mode} (Correct)")

# Generate documentation into a temporary folder
print("\nGenerating documentation schemas...")
schemas_folder = base_dir / "Schemas" / "test_run"
os.makedirs(schemas_folder, exist_ok=True)

for service in ["github", "gmail"]:
    current_mode = fcspec.get_current_doc_mode(service)
    print(f"  - Generating for '{service}' with doc_mode '{current_mode}'...")
    fcspec.generate_package_schema(
        package_path=str(apis_dir / service),
        output_folder_path=str(schemas_folder),
        doc_mode=current_mode,
        package_import_prefix=service,
        output_file_name=f"{service}.json"
    )

# Verify that the correct files were created based on the doc mode prefixes
print("\nVerifying generated files...")
expected_files = {
    "github": schemas_folder / "github.json",
    "gmail": schemas_folder / "medium_detail_gmail.json"
}
for service, file_path in expected_files.items():
    assert file_path.exists(), f"Missing expected file: {file_path}"
    print(f"  - Found expected file: {file_path}")

print("\n✅ Test Passed: Documentation generated correctly with specified doc modes.")

# Clean up by rolling back the temporary configuration
print("\nRolling back documentation configuration...")
framework_feature_manager.revert_all()
print("✅ Configuration rolled back!")

#%%
print("\n" + "="*60)
print("🎉 All tests completed successfully! 🎉")
print("="*60) 