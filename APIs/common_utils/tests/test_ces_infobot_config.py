"""
Comprehensive test cases for CES Infobot Configuration System
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch
from common_utils.ces_infobot_config import CESInfobotConfig, CESInfobotConfigManager


class TestCESInfobotConfig(unittest.TestCase):
    """Test cases for CESInfobotConfig dataclass"""
    
    def test_default_values(self):
        """Test that default configuration values are set correctly"""
        config = CESInfobotConfig()
        
        self.assertEqual(config.gcp_project, "gbot-experimentation")
        self.assertEqual(config.location, "us-east1")
        self.assertEqual(config.app_id, "78151603-8f03-4385-9c2a-42a2431f04e0")
        self.assertEqual(config.api_version, "v1beta")
        self.assertEqual(config.api_endpoint, "https://autopush-ces-googleapis.sandbox.google.com")
        self.assertEqual(config.service_account_info, "")
        self.assertEqual(config.scopes, ["https://www.googleapis.com/auth/cloud-platform"])
        self.assertEqual(config.ca_bundle, "/etc/ssl/certs/ca-certificates.crt")
        self.assertEqual(config.tool_resources, {})
    
    def test_custom_values(self):
        """Test creating config with custom values"""
        custom_tool_resources = {
            "tool1": "resource-id-1",
            "tool2": "resource-id-2"
        }
        
        config = CESInfobotConfig(
            gcp_project="custom-project",
            location="us-west1",
            tool_resources=custom_tool_resources
        )
        
        self.assertEqual(config.gcp_project, "custom-project")
        self.assertEqual(config.location, "us-west1")
        self.assertEqual(config.tool_resources, custom_tool_resources)
    
    def test_parent_resource_property(self):
        """Test parent_resource property generates correct string"""
        config = CESInfobotConfig(
            gcp_project="test-project",
            location="test-location",
            app_id="test-app-id"
        )
        
        expected = "projects/test-project/locations/test-location/apps/test-app-id"
        self.assertEqual(config.parent_resource, expected)
    
    def test_full_api_endpoint_property(self):
        """Test full_api_endpoint property generates correct URL"""
        config = CESInfobotConfig(
            gcp_project="test-project",
            location="test-location",
            app_id="test-app-id",
            api_version="v1",
            api_endpoint="https://test-api.example.com"
        )
        
        expected = "https://test-api.example.com/v1/projects/test-project/locations/test-location/apps/test-app-id"
        self.assertEqual(config.full_api_endpoint, expected)
    
    def test_to_dict(self):
        """Test converting config to dictionary"""
        config = CESInfobotConfig(gcp_project="test-project")
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict["gcp_project"], "test-project")
        self.assertIn("location", config_dict)
        self.assertIn("tool_resources", config_dict)
        self.assertIn("scopes", config_dict)
    
    def test_from_dict(self):
        """Test creating config from dictionary"""
        data = {
            "gcp_project": "dict-project",
            "location": "dict-location",
            "app_id": "dict-app-id",
            "api_version": "v2",
            "api_endpoint": "https://dict-api.example.com",
            "service_account_info": "base64_encoded",
            "scopes": ["scope1", "scope2"],
            "ca_bundle": "/custom/ca-bundle.crt",
            "tool_resources": {"tool1": "id1"}
        }
        
        config = CESInfobotConfig.from_dict(data)
        
        self.assertEqual(config.gcp_project, "dict-project")
        self.assertEqual(config.location, "dict-location")
        self.assertEqual(config.app_id, "dict-app-id")
        self.assertEqual(config.api_version, "v2")
        self.assertEqual(config.scopes, ["scope1", "scope2"])
        self.assertEqual(config.tool_resources, {"tool1": "id1"})
    
    def test_to_dict_from_dict_roundtrip(self):
        """Test that to_dict -> from_dict produces identical config"""
        original = CESInfobotConfig(
            gcp_project="roundtrip-project",
            tool_resources={"tool1": "id1", "tool2": "id2"}
        )
        
        config_dict = original.to_dict()
        restored = CESInfobotConfig.from_dict(config_dict)
        
        self.assertEqual(original.gcp_project, restored.gcp_project)
        self.assertEqual(original.location, restored.location)
        self.assertEqual(original.tool_resources, restored.tool_resources)
        self.assertEqual(original.scopes, restored.scopes)
    
    def test_tool_resources_mutation(self):
        """Test that tool_resources can be modified"""
        config = CESInfobotConfig()
        
        config.tool_resources["new_tool"] = "new-id"
        self.assertEqual(config.tool_resources["new_tool"], "new-id")
        
        config.tool_resources.update({"tool2": "id2", "tool3": "id3"})
        self.assertEqual(len(config.tool_resources), 3)


class TestCESInfobotConfigManager(unittest.TestCase):
    """Test cases for CESInfobotConfigManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        # Clean up any config files created during tests
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initializes with correct defaults"""
        manager = CESInfobotConfigManager(
            service_name="test_service",
            default_tool_resources={"tool1": "id1"}
        )
        
        self.assertEqual(manager.service_name, "test_service")
        self.assertEqual(manager.config_file, "test_service_infobot_config.json")
        
        config = manager.get_config()
        self.assertIsInstance(config, CESInfobotConfig)
        self.assertEqual(config.tool_resources, {"tool1": "id1"})
    
    def test_get_config(self):
        """Test getting configuration"""
        manager = CESInfobotConfigManager("test_service")
        config = manager.get_config()
        
        self.assertIsInstance(config, CESInfobotConfig)
        self.assertEqual(config.gcp_project, "gbot-experimentation")
    
    def test_update_config(self):
        """Test updating configuration"""
        manager = CESInfobotConfigManager("test_service")
        
        manager.update_config(gcp_project="updated-project")
        config = manager.get_config()
        self.assertEqual(config.gcp_project, "updated-project")
        
        manager.update_config(
            location="updated-location",
            api_version="v2"
        )
        config = manager.get_config()
        self.assertEqual(config.location, "updated-location")
        self.assertEqual(config.api_version, "v2")
    
    def test_update_config_with_tool_resources(self):
        """Test updating tool resources"""
        manager = CESInfobotConfigManager("test_service")
        
        new_tools = {"tool1": "new-id1", "tool2": "new-id2"}
        manager.update_config(tool_resources=new_tools)
        
        config = manager.get_config()
        self.assertEqual(config.tool_resources, new_tools)
    
    def test_update_config_invalid_key(self):
        """Test that updating with invalid key raises ValueError"""
        manager = CESInfobotConfigManager("test_service")
        
        with self.assertRaises(ValueError) as context:
            manager.update_config(invalid_key="value")
        
        self.assertIn("Unknown configuration key", str(context.exception))
    
    def test_save_config(self):
        """Test saving configuration to file"""
        manager = CESInfobotConfigManager("test_service")
        manager.update_config(gcp_project="save-test-project")
        
        # Save to default file
        manager.save_config()
        
        # Verify file exists
        self.assertTrue(os.path.exists("test_service_infobot_config.json"))
        
        # Verify file contents
        with open("test_service_infobot_config.json", 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["gcp_project"], "save-test-project")
    
    def test_save_config_custom_path(self):
        """Test saving configuration to custom file path"""
        manager = CESInfobotConfigManager("test_service")
        custom_path = "custom_config.json"
        
        manager.update_config(gcp_project="custom-save-project")
        manager.save_config(custom_path)
        
        self.assertTrue(os.path.exists(custom_path))
        
        with open(custom_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["gcp_project"], "custom-save-project")
    
    def test_load_config(self):
        """Test loading configuration from file"""
        # Create a config file
        config_data = {
            "gcp_project": "loaded-project",
            "location": "loaded-location",
            "app_id": "loaded-app-id",
            "api_version": "v1beta",
            "api_endpoint": "https://autopush-ces-googleapis.sandbox.google.com",
            "service_account_info": "loaded-account",
            "scopes": ["https://www.googleapis.com/auth/cloud-platform"],
            "ca_bundle": "/etc/ssl/certs/ca-certificates.crt",
            "tool_resources": {"tool1": "loaded-id1"}
        }
        
        config_file = "test_load_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Load the config
        manager = CESInfobotConfigManager("test_service")
        manager.load_config(config_file)
        
        config = manager.get_config()
        self.assertEqual(config.gcp_project, "loaded-project")
        self.assertEqual(config.location, "loaded-location")
        self.assertEqual(config.tool_resources, {"tool1": "loaded-id1"})
    
    def test_load_config_on_initialization(self):
        """Test that config is automatically loaded from file if it exists"""
        # Create a config file
        config_data = {
            "gcp_project": "auto-loaded-project",
            "location": "us-central1",
            "app_id": "78151603-8f03-4385-9c2a-42a2431f04e0",
            "api_version": "v1beta",
            "api_endpoint": "https://autopush-ces-googleapis.sandbox.google.com",
            "service_account_info": "",
            "scopes": ["https://www.googleapis.com/auth/cloud-platform"],
            "ca_bundle": "/etc/ssl/certs/ca-certificates.crt",
            "tool_resources": {}
        }
        
        config_file = "auto_load_service_infobot_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Initialize manager - should auto-load from file
        manager = CESInfobotConfigManager("auto_load_service")
        
        config = manager.get_config()
        self.assertEqual(config.gcp_project, "auto-loaded-project")
        self.assertEqual(config.location, "us-central1")
    
    @patch.dict(os.environ, {
        "TEST_SERVICE_INFOBOT_GCP_PROJECT": "env-project",
        "TEST_SERVICE_INFOBOT_LOCATION": "env-location",
        "TEST_SERVICE_INFOBOT_SERVICE_ACCOUNT_INFO": "env-account"
    })
    def test_load_from_environment_variables(self):
        """Test loading configuration from environment variables"""
        manager = CESInfobotConfigManager("test_service")
        
        config = manager.get_config()
        self.assertEqual(config.gcp_project, "env-project")
        self.assertEqual(config.location, "env-location")
        self.assertEqual(config.service_account_info, "env-account")
    
    @patch.dict(os.environ, {
        "ANOTHER_SERVICE_INFOBOT_GCP_PROJECT": "another-env-project",
        "ANOTHER_SERVICE_INFOBOT_API_VERSION": "v2"
    })
    def test_environment_variables_service_specific(self):
        """Test that environment variables are service-specific"""
        manager = CESInfobotConfigManager("another_service")
        
        config = manager.get_config()
        self.assertEqual(config.gcp_project, "another-env-project")
        self.assertEqual(config.api_version, "v2")
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults"""
        manager = CESInfobotConfigManager(
            "test_service",
            default_tool_resources={"tool1": "default-id1"}
        )
        
        # Modify config
        manager.update_config(gcp_project="modified-project", location="modified-location")
        
        # Reset
        manager.reset_to_defaults()
        
        config = manager.get_config()
        self.assertEqual(config.gcp_project, "gbot-experimentation")
        self.assertEqual(config.location, "us-east1")
        # Tool resources should be preserved
        self.assertEqual(config.tool_resources, {"tool1": "default-id1"})
    
    def test_show_config(self):
        """Test showing configuration (output test)"""
        manager = CESInfobotConfigManager("test_service")
        
        # Just verify it doesn't raise an exception
        try:
            manager.show_config()
        except Exception as e:
            self.fail(f"show_config() raised {type(e).__name__}: {e}")
    
    def test_save_and_load_roundtrip(self):
        """Test that save -> load produces identical config"""
        manager = CESInfobotConfigManager("roundtrip_service")
        
        # Set some custom values
        manager.update_config(
            gcp_project="roundtrip-project",
            location="roundtrip-location",
            tool_resources={"tool1": "rt-id1", "tool2": "rt-id2"}
        )
        
        # Save
        config_file = "roundtrip_test.json"
        manager.save_config(config_file)
        
        # Create new manager and load
        new_manager = CESInfobotConfigManager("other_service")
        new_manager.load_config(config_file)
        
        # Compare configs
        original_config = manager.get_config()
        loaded_config = new_manager.get_config()
        
        self.assertEqual(original_config.gcp_project, loaded_config.gcp_project)
        self.assertEqual(original_config.location, loaded_config.location)
        self.assertEqual(original_config.tool_resources, loaded_config.tool_resources)


class TestCESInfobotConfigIntegration(unittest.TestCase):
    """Integration tests for the configuration system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_multiple_services_independent_config(self):
        """Test that multiple services maintain independent configurations"""
        manager1 = CESInfobotConfigManager(
            "service1",
            default_tool_resources={"tool1": "s1-id1"}
        )
        manager2 = CESInfobotConfigManager(
            "service2",
            default_tool_resources={"tool2": "s2-id2"}
        )
        
        # Update each service's config
        manager1.update_config(gcp_project="service1-project")
        manager2.update_config(gcp_project="service2-project")
        
        # Verify they're independent
        config1 = manager1.get_config()
        config2 = manager2.get_config()
        
        self.assertEqual(config1.gcp_project, "service1-project")
        self.assertEqual(config2.gcp_project, "service2-project")
        self.assertEqual(config1.tool_resources, {"tool1": "s1-id1"})
        self.assertEqual(config2.tool_resources, {"tool2": "s2-id2"})
    
    def test_ces_account_management_defaults(self):
        """Test default configuration for ces_account_management"""
        manager = CESInfobotConfigManager(
            "ces_account_management",
            default_tool_resources={
                "account_orders": "46f527f8-0509-4e28-9563-db5666e0790b",
                "plans_features": "c90c11bb-6868-4631-8bf0-7f8b5fe4b92c"
            }
        )
        
        config = manager.get_config()
        self.assertIn("account_orders", config.tool_resources)
        self.assertIn("plans_features", config.tool_resources)
    
    def test_ces_system_activation_defaults(self):
        """Test default configuration for ces_system_activation"""
        manager = CESInfobotConfigManager(
            "ces_system_activation",
            default_tool_resources={
                "activation_guides": "46f527f8-0509-4e28-9563-db5666e0790b",
                "order_details": "c90c11bb-6868-4631-8bf0-7f8b5fe4b92c"
            }
        )
        
        config = manager.get_config()
        self.assertIn("activation_guides", config.tool_resources)
        self.assertIn("order_details", config.tool_resources)
    
    def test_config_persistence_across_instances(self):
        """Test that saved config persists across manager instances"""
        # First instance
        manager1 = CESInfobotConfigManager("persist_service")
        manager1.update_config(gcp_project="persist-project")
        manager1.save_config()
        
        # Second instance - should load saved config
        manager2 = CESInfobotConfigManager("persist_service")
        config2 = manager2.get_config()
        
        self.assertEqual(config2.gcp_project, "persist-project")
    
    def test_typical_workflow(self):
        """Test a typical user workflow"""
        # Initialize service
        manager = CESInfobotConfigManager(
            "workflow_service",
            default_tool_resources={"tool1": "default-id"}
        )
        
        # View initial config
        initial_config = manager.get_config()
        self.assertEqual(initial_config.gcp_project, "gbot-experimentation")
        
        # Update for production
        manager.update_config(
            gcp_project="production-project",
            service_account_info="prod-service-account-base64"
        )
        
        # Save configuration
        manager.save_config("production_config.json")
        
        # Later, load the same configuration
        new_manager = CESInfobotConfigManager("workflow_service")
        new_manager.load_config("production_config.json")
        
        # Verify it works
        prod_config = new_manager.get_config()
        self.assertEqual(prod_config.gcp_project, "production-project")
        self.assertEqual(prod_config.service_account_info, "prod-service-account-base64")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_empty_tool_resources(self):
        """Test handling of empty tool resources"""
        config = CESInfobotConfig(tool_resources={})
        self.assertEqual(config.tool_resources, {})
        
        manager = CESInfobotConfigManager("test_service", default_tool_resources={})
        self.assertEqual(manager.get_config().tool_resources, {})
    
    def test_none_default_tool_resources(self):
        """Test handling of None default tool resources"""
        manager = CESInfobotConfigManager("test_service", default_tool_resources=None)
        self.assertEqual(manager.get_config().tool_resources, {})
    
    def test_load_malformed_json(self):
        """Test loading from malformed JSON file"""
        malformed_file = "malformed.json"
        with open(malformed_file, 'w') as f:
            f.write("{invalid json content")
        
        manager = CESInfobotConfigManager("test_service")
        
        with self.assertRaises(json.JSONDecodeError):
            manager.load_config(malformed_file)
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file"""
        manager = CESInfobotConfigManager("test_service")
        
        with self.assertRaises(FileNotFoundError):
            manager.load_config("nonexistent_file.json")
    
    def test_special_characters_in_values(self):
        """Test handling of special characters in configuration values"""
        special_chars = "test@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        manager = CESInfobotConfigManager("test_service")
        manager.update_config(gcp_project=special_chars)
        
        config = manager.get_config()
        self.assertEqual(config.gcp_project, special_chars)
    
    def test_very_long_configuration_values(self):
        """Test handling of very long configuration values"""
        long_value = "a" * 10000
        
        manager = CESInfobotConfigManager("test_service")
        manager.update_config(service_account_info=long_value)
        
        config = manager.get_config()
        self.assertEqual(config.service_account_info, long_value)
        self.assertEqual(len(config.service_account_info), 10000)


if __name__ == '__main__':
    unittest.main()

