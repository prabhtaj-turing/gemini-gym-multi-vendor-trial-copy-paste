import pytest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import patch

# Import gemini_cli modules
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli.SimulationEngine.utils import (
    update_common_directory,
    get_common_directory,
)

def pytest_configure(config):
    """Configure pytest environment for gemini_cli tests."""
    # Set default environment variable for tests (only if not already set)
    if 'GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM' not in os.environ:
        os.environ['GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM'] = 'false'


@pytest.fixture
def disable_common_file_system():
    """
    Fixture to disable common file system for specific tests.
    
    Usage:
        def test_something(disable_common_file_system):
            # Test runs with common file system disabled
    """
    original_value = os.environ.get('GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM')
    
    # Disable common file system
    os.environ['GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM'] = 'false'
    
    yield
    
    # Restore original value
    if original_value is None:
        os.environ.pop('GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM', None)
    else:
        os.environ['GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM'] = original_value


@pytest.fixture(scope="session", autouse=False)
def setup_common_directory(request):
    """
    Set up a temporary common directory for tests that explicitly need it.
    
    Usage: Add 'setup_common_directory' parameter to tests that require common_file_system.
    Most tests should use logical paths without common_file_system hydration.
    """
    
    # Create a temporary directory for the entire test session
    temp_dir = tempfile.mkdtemp(prefix="gemini_cli_test_common_")
    
    # Create the basic workspace structure based on the default DB
    workspace_path = os.path.join(temp_dir, "home", "user", "project")
    os.makedirs(workspace_path, exist_ok=True)
    
    # Create some basic files and directories from the default DB
    # Load the default DB to get the structure
    db_json_path = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"
    
    try:
        with open(db_json_path, "r", encoding="utf-8") as f:
            default_db = json.load(f)
        
        # Create files and directories from the default DB
        for path, file_info in default_db.get("file_system", {}).items():
            if file_info.get("is_directory", False):
                # Create directory
                full_path = os.path.join(temp_dir, path.lstrip("/"))
                os.makedirs(full_path, exist_ok=True)
            else:
                # Create file
                full_path = os.path.join(temp_dir, path.lstrip("/"))
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file content
                content_lines = file_info.get("content_lines", [])
                content = "".join(content_lines)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
    except Exception as e:
        print(f"Warning: Could not load default DB for test setup: {e}")
        # Create minimal structure if default DB loading fails
        pass
    
    # Store original common directory state (might be None)
    try:
        original_common_dir = get_common_directory()
    except RuntimeError:
        original_common_dir = None
    
    # Update the common directory to use our temporary directory
    update_common_directory(temp_dir)
    
    yield temp_dir
    
    # Cleanup: restore original common directory and remove temp directory
    if original_common_dir is not None:
        try:
            update_common_directory(original_common_dir)
        except:
            pass  # Original directory might not exist anymore
    
    # Remove the temporary directory
    try:
        shutil.rmtree(temp_dir)
    except:
        pass  # Best effort cleanup


# Note: DB reset is handled by individual test fixtures (reload_db) 