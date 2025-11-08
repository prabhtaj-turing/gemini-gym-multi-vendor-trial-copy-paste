#!/usr/bin/env python3
"""
Error Handling Framework Feature Test

This script tests the error handling framework feature to ensure it works correctly
with the framework feature manager and provides proper error handling configuration.

Usage Examples:
    # Get ErrorManager instance
    error_manager = ErrorManager.get_instance()
    
    # Set global error mode
    error_manager.set_error_mode("error_dict")
    
    # Reset to environment variable
    error_manager.reset_error_mode()
    
    # Temporary override within context (uses error_handling.py directly)
    with error_manager.temporary_error_mode("raise"):
        # Code here will use raise mode
        pass
    # Code here will use previous mode
    
    # Apply configuration from JSON
    config = {
        "global": {"error_mode": "error_dict", "print_error_reports": True},
        "services": {"gmail": {"error_mode": "raise"}}
    }
    error_manager.apply_config(config)
    
    # Get service-specific settings
    gmail_mode = ErrorManager.get_error_mode("gmail")
    github_mode = ErrorManager.get_error_mode("github")  # Uses global mode
"""

import sys
import os
import json
import tempfile

# Add APIs to path
sys.path.append('./APIs')

from common_utils.framework_feature import framework_feature_manager
from common_utils.error_manager import ErrorManager
from common_utils.error_handling import get_package_error_mode, get_print_error_reports

def test_error_manager_basic():
    """Test basic ErrorManager functionality."""
    print("🔧 Testing ErrorManager Basic Functionality...")
    
    error_manager = ErrorManager.get_instance()
    
    # Test singleton pattern
    error_manager2 = ErrorManager.get_instance()
    assert error_manager is error_manager2, "ErrorManager should be singleton"
    
    print("✅ ErrorManager singleton pattern works")
    
    # Test initial state
    assert not error_manager._is_active, "ErrorManager should not be active initially"
    assert error_manager.global_config == {}, "Global config should be empty initially"
    assert error_manager.service_configs == {}, "Service configs should be empty initially"
    
    print("✅ ErrorManager initial state is correct")

def test_error_config_application():
    """Test applying error configuration."""
    print("\n🔧 Testing Error Configuration Application...")
    
    error_manager = ErrorManager.get_instance()
    
    # Test configuration
    test_config = {
        "global": {
            "error_mode": "error_dict"
        },
        "services": {
            "gmail": {
                "error_mode": "raise"
            },
            "github": {
                "error_mode": "error_dict"
            }
        }
    }
    
    # Apply configuration
    error_manager.apply_config(test_config)
    
    # Verify configuration was applied
    assert error_manager._is_active, "ErrorManager should be active after applying config"
    assert error_manager.global_config == test_config["global"], "Global config should match"
    assert error_manager.service_configs == test_config["services"], "Service configs should match"
    
    # Verify global settings were applied
    print(f"Global error mode: {get_package_error_mode()}")
    assert get_package_error_mode() == "error_dict", "Global error mode should be error_dict"
    
    print("✅ Error configuration application works")

def test_service_specific_overrides():
    """Test service-specific error handling overrides."""
    print("\n🔧 Testing Service-Specific Overrides...")
    
    error_manager = ErrorManager.get_instance()
    
    # Apply test configuration
    test_config = {
        "global": {
            "error_mode": "error_dict"
        },
        "services": {
            "gmail": {
                "error_mode": "raise"
            },
            "github": {
                "error_mode": "error_dict"
            }
        }
    }
    error_manager.apply_config(test_config)
    
    # Test service-specific error modes
    gmail_mode = error_manager.get_error_mode("gmail")
    github_mode = error_manager.get_error_mode("github")
    unknown_mode = error_manager.get_error_mode("unknown_service")
    
    assert gmail_mode == "raise", f"Gmail should have raise mode, got {gmail_mode}"
    assert github_mode == "error_dict", f"GitHub should have error_dict mode, got {github_mode}"
    assert unknown_mode == "error_dict", f"Unknown service should use global mode, got {unknown_mode}"
    
    print("✅ Service-specific overrides work correctly")

def test_config_rollback():
    """Test configuration rollback functionality."""
    print("\n🔧 Testing Configuration Rollback...")
    
    error_manager = ErrorManager.get_instance()
    
    # Store current state
    current_error_mode = get_package_error_mode()
    
    # Rollback configuration
    error_manager.rollback_config()
    
    # Verify rollback
    assert not error_manager._is_active, "ErrorManager should not be active after rollback"
    assert error_manager.global_config == {}, "Global config should be empty after rollback"
    assert error_manager.service_configs == {}, "Service configs should be empty after rollback"
    
    # Note: The actual error mode and print reports might not be restored to original values
    # because the rollback restores to the state when apply_config was called
    print("✅ Configuration rollback works")

def test_framework_integration():
    """Test integration with framework feature manager."""
    print("\n🔧 Testing Framework Integration...")
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "error": {
                "global": {
                    "error_mode": "error_dict"
                },
                "services": {
                    "gmail": {
                        "error_mode": "raise"
                    }
                }
            },
            "documentation": {}
        }
        json.dump(test_config, f)
        temp_config_path = f.name
    
    try:
        # Load config and apply
        with open(temp_config_path, 'r') as f:
            config = json.load(f)
        framework_feature_manager.apply_config(config)
        
        # Verify framework applied the configuration
        assert get_package_error_mode() == "error_dict", "Framework should apply error_dict mode"
        
        # Test service-specific override
        error_manager = ErrorManager.get_instance()
        gmail_mode = error_manager.get_error_mode("gmail")
        assert gmail_mode == "raise", f"Gmail should have raise mode via framework, got {gmail_mode}"
        
        print("✅ Framework integration works")
        
        # Rollback
        framework_feature_manager.revert_all()
        
    finally:
        # Clean up
        os.unlink(temp_config_path)

def test_default_config():
    """Test the default framework configuration."""
    print("\n🔧 Testing Default Framework Configuration...")
    
    # Load default config
    with open('default_framework_config.json', 'r') as f:
        default_config = json.load(f)
    
    # Verify error_mode section exists
    assert "error_mode" in default_config, "Default config should have error_mode section"
    assert "global" in default_config["error_mode"], "Error mode section should have global config"
    assert "services" in default_config["error_mode"], "Error mode section should have services config"
    
    # Verify global settings
    global_config = default_config["error_mode"]["global"]
    assert "error_mode" in global_config, "Global config should have error_mode"
    assert global_config["error_mode"] in ["raise", "error_dict"], "error_mode should be valid"
    
    # Verify services are configured
    services_config = default_config["error_mode"]["services"]
    assert len(services_config) > 0, "Should have at least one service configured"
    
    # Check that all services have proper configuration
    for service_name, service_config in services_config.items():
        assert "error_mode" in service_config, f"Service {service_name} should have error_mode"
        assert service_config["error_mode"] in ["raise", "error_dict"], f"Service {service_name} error_mode should be valid"
    
    print(f"✅ Default configuration is valid with {len(services_config)} services")

def test_error_handling_modes():
    """Test different error handling modes."""
    print("\n🔧 Testing Error Handling Modes...")
    
    error_manager = ErrorManager.get_instance()
    
    # Test raise mode
    raise_config = {
        "global": {
            "error_mode": "raise",
            "print_error_reports": False
        }
    }
    
    error_manager.apply_config(raise_config)
    assert get_package_error_mode() == "raise", "Should be able to set raise mode"
    
    # Test error_dict mode
    dict_config = {
        "global": {
            "error_mode": "error_dict",
        }
    }
    
    error_manager.rollback_config()
    error_manager.apply_config(dict_config)
    assert get_package_error_mode() == "error_dict", "Should be able to set error_dict mode"
    
    print("✅ Error handling modes work correctly")

def test_error_manager_override_functionality():
    """Test ErrorManager's error override functionality."""
    print("\n🔧 Testing ErrorManager Override Functionality...")
    
    error_manager = ErrorManager.get_instance()
    
    # Test set_error_mode
    error_manager.set_error_mode("raise")
    assert get_package_error_mode() == "raise", "set_error_mode should set raise mode"
    
    error_manager.set_error_mode("error_dict")
    assert get_package_error_mode() == "error_dict", "set_error_mode should set error_dict mode"
    
    # Test reset_error_mode
    error_manager.reset_error_mode()
    # Should fall back to default (raise) since no environment variable is set
    assert get_package_error_mode() == "raise", "reset_error_mode should restore default"
    
    # Test temporary_error_mode context manager
    error_manager.set_error_mode("raise")
    
    with error_manager.temporary_error_mode("error_dict"):
        assert get_package_error_mode() == "error_dict", "temporary_error_mode should set error_dict"
    
    # Should be back to raise after context
    assert get_package_error_mode() == "raise", "temporary_error_mode should restore previous mode"
    
    # Test nested temporary_error_mode
    with error_manager.temporary_error_mode("error_dict"):
        assert get_package_error_mode() == "error_dict", "First context should be error_dict"
        
        with error_manager.temporary_error_mode("raise"):
            assert get_package_error_mode() == "raise", "Nested context should be raise"
        
        assert get_package_error_mode() == "error_dict", "Should return to first context"
    
    assert get_package_error_mode() == "raise", "Should return to original mode"
    
    print("✅ ErrorManager override functionality works correctly")

def main():
    """Run all tests."""
    print("🚀 Starting Error Handling Framework Feature Tests...\n")
    
    try:
        test_error_manager_basic()
        test_error_config_application()
        test_service_specific_overrides()
        test_config_rollback()
        test_framework_integration()
        test_default_config()
        test_error_handling_modes()
        test_error_manager_override_functionality()
        
        print("\n🎉 All tests passed! Error handling framework feature is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
