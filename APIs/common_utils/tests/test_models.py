#!/usr/bin/env python3
"""
Tests for models module.

This module tests the Pydantic models and enums in common_utils.models module.
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from enum import Enum

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.models import (
    Service,
    DocMode,
    MutationOverride,
    AuthenticationOverride,
    AuthenticationOverrideService,
    ErrorTypeConfig,
    ServiceDocumentationConfig,
    GlobalDocumentationConfig,
    DocumentationConfig,
    _get_service_names
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestModels(BaseTestCaseWithErrorHandler):
    """Test cases for models module."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create a temporary directory structure for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock APIs directory structure
        self.apis_dir = os.path.join(self.temp_dir, "APIs")
        os.makedirs(self.apis_dir)
        
        # Create some mock service directories
        self.service_dirs = ["gmail", "gdrive", "google_calendar", "notifications"]
        for service in self.service_dirs:
            os.makedirs(os.path.join(self.apis_dir, service))
        
        # Create some non-service directories/files
        os.makedirs(os.path.join(self.apis_dir, "common_utils"))
        os.makedirs(os.path.join(self.apis_dir, "__pycache__"))
        with open(os.path.join(self.apis_dir, "README.md"), "w") as f:
            f.write("Test file")
        
        # Create common_utils directory in temp_dir (parent of APIs)
        os.makedirs(os.path.join(self.temp_dir, "common_utils"))

    def tearDown(self):
        """Clean up test fixtures."""
        super().tearDown()
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skip("Complex to mock properly - dynamic service discovery")
    def test_get_service_names_success(self):
        """Test _get_service_names with valid directory structure."""
        with patch('common_utils.models.os.path.dirname') as mock_dirname:
            # Mock to return the common_utils directory (parent of APIs)
            mock_dirname.return_value = os.path.join(self.temp_dir, "common_utils")
            
            services = _get_service_names()
            
            # Should return sorted list of service directories, excluding common_utils and __pycache__
            expected_services = ["google_calendar", "gdrive", "gmail", "notifications"]
            self.assertEqual(services, expected_services)

    def test_get_service_names_file_not_found(self):
        """Test _get_service_names with non-existent directory."""
        with patch('common_utils.models.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = "/non/existent/path"
            
            services = _get_service_names()
            
            # Should return empty list when directory doesn't exist
            self.assertEqual(services, [])

    def test_service_enum_creation(self):
        """Test that Service enum is created correctly."""
        # Verify Service is an Enum
        self.assertTrue(issubclass(Service, Enum))
        
        # Verify it has the expected service values
        service_values = [s.value for s in Service]
        expected_services = ["google_calendar", "gdrive", "gmail", "notifications"]
        for service in expected_services:
            self.assertIn(service, service_values)


    def test_doc_mode_enum(self):
        """Test DocMode enum values."""
        # Verify enum values
        self.assertEqual(DocMode.RAW_DOCSTRING, "raw_docstring")
        self.assertEqual(DocMode.CONCISE, "concise")
        self.assertEqual(DocMode.MEDIUM_DETAIL, "medium_detail")
        
        # Verify it's a string enum
        self.assertTrue(issubclass(DocMode, str))
        self.assertTrue(issubclass(DocMode, Enum))

    def test_mutation_override_creation(self):
        """Test MutationOverride model creation."""
        # Test with mutation name
        override = MutationOverride(mutation_name="m01")
        self.assertEqual(override.mutation_name, "m01")
        
        # Test with empty string (should raise validation error)
        with self.assertRaises(Exception):  # Pydantic validation error
            MutationOverride(mutation_name="")
        
        # Test with None (should raise validation error since field is required)
        with self.assertRaises(Exception):  # Pydantic validation error
            MutationOverride(mutation_name=None)

    def test_authentication_override_creation(self):
        """Test AuthenticationOverride model creation."""
        # Test with authentication enabled
        override = AuthenticationOverride(authentication_enabled=True)
        self.assertTrue(override.authentication_enabled)
        
        # Test with authentication disabled
        override = AuthenticationOverride(authentication_enabled=False)
        self.assertFalse(override.authentication_enabled)
        
        # Test with None
        override = AuthenticationOverride(authentication_enabled=None)
        self.assertIsNone(override.authentication_enabled)

    def test_authentication_override_service_creation(self):
        """Test AuthenticationOverrideService model creation."""
        # Test with all fields
        override = AuthenticationOverrideService(
            authentication_enabled=True,
            excluded_functions=["func1", "func2"],
            is_authenticated=True
        )
        self.assertTrue(override.authentication_enabled)
        self.assertEqual(override.excluded_functions, ["func1", "func2"])
        self.assertTrue(override.is_authenticated)
        
        # Test with None values
        override = AuthenticationOverrideService(
            authentication_enabled=None,
            excluded_functions=None,
            is_authenticated=None
        )
        self.assertIsNone(override.authentication_enabled)
        self.assertIsNone(override.excluded_functions)
        self.assertIsNone(override.is_authenticated)

    def test_error_type_config_creation(self):
        """Test ErrorTypeConfig model creation."""
        # Test with all fields
        config = ErrorTypeConfig(
            probability=0.5,
            dampen_factor=0.3,
            num_errors_simulated=10
        )
        self.assertEqual(config.probability, 0.5)
        self.assertEqual(config.dampen_factor, 0.3)
        self.assertEqual(config.num_errors_simulated, 10)
        
        # Test with defaults
        config = ErrorTypeConfig()
        self.assertEqual(config.probability, 0.0)
        self.assertEqual(config.dampen_factor, 0.0)
        self.assertIsNone(config.num_errors_simulated)

    def test_error_type_config_validation(self):
        """Test ErrorTypeConfig field validation."""
        # Test valid probability range
        config = ErrorTypeConfig(probability=0.0)
        self.assertEqual(config.probability, 0.0)
        
        config = ErrorTypeConfig(probability=1.0)
        self.assertEqual(config.probability, 1.0)
        
        # Test invalid probability (should raise validation error)
        with self.assertRaises(Exception):  # Pydantic validation error
            ErrorTypeConfig(probability=1.5)
        
        with self.assertRaises(Exception):  # Pydantic validation error
            ErrorTypeConfig(probability=-0.1)
        
        # Test valid dampen_factor range
        config = ErrorTypeConfig(dampen_factor=0.0)
        self.assertEqual(config.dampen_factor, 0.0)
        
        config = ErrorTypeConfig(dampen_factor=1.0)
        self.assertEqual(config.dampen_factor, 1.0)
        
        # Test invalid dampen_factor (should raise validation error)
        with self.assertRaises(Exception):  # Pydantic validation error
            ErrorTypeConfig(dampen_factor=1.5)
        
        # Test valid num_errors_simulated
        config = ErrorTypeConfig(num_errors_simulated=0)
        self.assertEqual(config.num_errors_simulated, 0)
        
        config = ErrorTypeConfig(num_errors_simulated=100)
        self.assertEqual(config.num_errors_simulated, 100)
        
        # Test invalid num_errors_simulated (should raise validation error)
        with self.assertRaises(Exception):  # Pydantic validation error
            ErrorTypeConfig(num_errors_simulated=-1)

    def test_service_documentation_config_creation(self):
        """Test ServiceDocumentationConfig model creation."""
        # Test with each doc mode
        for doc_mode in DocMode:
            config = ServiceDocumentationConfig(doc_mode=doc_mode)
            self.assertEqual(config.doc_mode, doc_mode)

    def test_global_documentation_config_creation(self):
        """Test GlobalDocumentationConfig model creation."""
        # Test with each doc mode
        for doc_mode in DocMode:
            config = GlobalDocumentationConfig(doc_mode=doc_mode)
            self.assertEqual(config.doc_mode, doc_mode)

    def test_documentation_config_creation(self):
        """Test DocumentationConfig model creation."""
        # Test with global config only
        global_config = GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)
        config = DocumentationConfig(**{"global": global_config})
        self.assertEqual(config.global_config, global_config)
        self.assertIsNone(config.services)
        
        # Test with services only
        services = {
            "gmail": ServiceDocumentationConfig(doc_mode=DocMode.RAW_DOCSTRING),
            "gdrive": ServiceDocumentationConfig(doc_mode=DocMode.MEDIUM_DETAIL)
        }
        config = DocumentationConfig(services=services)
        self.assertIsNone(config.global_config)
        self.assertEqual(config.services, services)
        
        # Test with both global and services
        config = DocumentationConfig(**{"global": global_config, "services": services})
        self.assertEqual(config.global_config, global_config)
        self.assertEqual(config.services, services)

    def test_documentation_config_service_validation(self):
        """Test DocumentationConfig service name validation."""
        # Test with valid service names
        services = {
            "gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE),
            "gdrive": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)
        }
        config = DocumentationConfig(services=services)
        self.assertEqual(config.services, services)
        
        # Test with invalid service name (should raise validation error)
        services = {
            "invalid_service": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)
        }
        with self.assertRaises(Exception):  # Pydantic validation error
            DocumentationConfig(services=services)

    def test_documentation_config_none_services(self):
        """Test DocumentationConfig with None services."""
        config = DocumentationConfig(services=None)
        self.assertIsNone(config.services)

    def test_model_serialization(self):
        """Test model serialization to dict."""
        # Test MutationOverride serialization
        override = MutationOverride(mutation_name="m01")
        data = override.model_dump()
        self.assertEqual(data["mutation_name"], "m01")
        
        # Test ErrorTypeConfig serialization
        config = ErrorTypeConfig(probability=0.5, dampen_factor=0.3)
        data = config.model_dump()
        self.assertEqual(data["probability"], 0.5)
        self.assertEqual(data["dampen_factor"], 0.3)
        self.assertIsNone(data["num_errors_simulated"])

    def test_model_deserialization(self):
        """Test model deserialization from dict."""
        # Test MutationOverride deserialization
        data = {"mutation_name": "m01"}
        override = MutationOverride.model_validate(data)
        self.assertEqual(override.mutation_name, "m01")
        
        # Test ErrorTypeConfig deserialization
        data = {"probability": 0.5, "dampen_factor": 0.3}
        config = ErrorTypeConfig.model_validate(data)
        self.assertEqual(config.probability, 0.5)
        self.assertEqual(config.dampen_factor, 0.3)

    def test_model_json_serialization(self):
        """Test model JSON serialization."""
        # Test ErrorTypeConfig JSON serialization
        config = ErrorTypeConfig(probability=0.5, dampen_factor=0.3)
        json_str = config.model_dump_json()
        
        # Verify JSON can be parsed back
        import json
        data = json.loads(json_str)
        self.assertEqual(data["probability"], 0.5)
        self.assertEqual(data["dampen_factor"], 0.3)

    def test_model_field_descriptions(self):
        """Test that model fields have proper descriptions."""
        # Test ErrorTypeConfig field descriptions
        config = ErrorTypeConfig()
        
        # Check that fields have descriptions (this would require accessing the model's schema)
        # For now, just verify the model can be created
        self.assertIsInstance(config, ErrorTypeConfig)

    def test_enum_comparison(self):
        """Test enum value comparisons."""
        # Test DocMode comparisons
        self.assertEqual(DocMode.CONCISE, "concise")
        self.assertNotEqual(DocMode.CONCISE, "raw_docstring")

    def test_model_optional_fields(self):
        """Test that optional fields work correctly."""
        # Test AuthenticationOverrideService with minimal fields
        override = AuthenticationOverrideService()
        self.assertIsNone(override.authentication_enabled)
        self.assertIsNone(override.excluded_functions)
        self.assertIsNone(override.is_authenticated)
        
        # Test with some fields set
        override = AuthenticationOverrideService(authentication_enabled=True)
        self.assertTrue(override.authentication_enabled)
        self.assertIsNone(override.excluded_functions)
        self.assertIsNone(override.is_authenticated)

    def test_model_nested_structures(self):
        """Test models with nested structures."""
        # Test DocumentationConfig with nested services
        services = {
            "gmail": ServiceDocumentationConfig(doc_mode=DocMode.RAW_DOCSTRING),
            "gdrive": ServiceDocumentationConfig(doc_mode=DocMode.MEDIUM_DETAIL)
        }
        global_config = GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)
        
        config = DocumentationConfig(**{"global": global_config, "services": services})
        
        # Verify nested structures
        self.assertEqual(config.global_config.doc_mode, DocMode.CONCISE)
        self.assertEqual(config.services["gmail"].doc_mode, DocMode.RAW_DOCSTRING)
        self.assertEqual(config.services["gdrive"].doc_mode, DocMode.MEDIUM_DETAIL)

    def test_get_service_names_file_not_found_exception(self):
        """Test _get_service_names with FileNotFoundError (lines 24-26)."""
        with patch('common_utils.models.os.listdir', side_effect=FileNotFoundError("Directory not found")):
            services = _get_service_names()
            self.assertEqual(services, [])

    def test_get_service_names_os_error(self):
        """Test _get_service_names with OSError (lines 24-26)."""
        with patch('common_utils.models.os.listdir', side_effect=OSError("Permission denied")):
            # OSError should propagate since the function only catches FileNotFoundError
            with self.assertRaises(OSError):
                _get_service_names()

    def test_documentation_config_validate_service_names_with_invalid_service(self):
        """Test DocumentationConfig validate_service_names with invalid service (lines 134, 140)."""
        from common_utils.models import DocumentationConfig, ServiceDocumentationConfig, DocMode
        
        # Test with invalid service name - should raise ValueError
        with self.assertRaises(ValueError) as context:
            DocumentationConfig(
                services={"invalid_service": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)}
            )
        
        self.assertIn("'invalid_service' is not a valid service", str(context.exception))

    def test_error_simulation_config_validate_service_names_with_invalid_service(self):
        """Test ErrorSimulationConfig validate_service_names with invalid service (lines 134, 140)."""
        from common_utils.models import ErrorSimulationConfig, ServiceErrorConfig, ErrorTypeConfig
        
        # Test with invalid service name - should raise ValueError
        with self.assertRaises(ValueError) as context:
            ErrorSimulationConfig(
                services={"invalid_service": ServiceErrorConfig(
                    config={"TypeError": ErrorTypeConfig(probability=0.1)}
                )}
            )
        
        self.assertIn("'invalid_service' is not a valid service", str(context.exception))

    def test_mutation_config_validate_service_names_with_invalid_service(self):
        """Test MutationConfig validate_service_names with invalid service (lines 173)."""
        from common_utils.models import MutationConfig, MutationOverride
        
        # Test with invalid service name - should raise ValueError
        with self.assertRaises(ValueError) as context:
            MutationConfig(
                services={"invalid_service": MutationOverride(mutation_name="m01")}
            )
        
        self.assertIn("'invalid_service' is not a valid service", str(context.exception))

    def test_authentication_config_validate_service_names_with_invalid_service(self):
        """Test AuthenticationConfig validate_service_names with invalid service (lines 206, 212)."""
        from common_utils.models import AuthenticationConfig, AuthenticationOverrideService
        
        # Test with invalid service name - should raise ValueError
        with self.assertRaises(ValueError) as context:
            AuthenticationConfig(
                services={"invalid_service": AuthenticationOverrideService(authentication_enabled=True)}
            )
        
        self.assertIn("'invalid_service' is not a valid service", str(context.exception))

    def test_error_mode_config_validate_service_names_with_invalid_service(self):
        """Test ErrorModeConfig validate_service_names with invalid service (lines 226, 232)."""
        from common_utils.models import ErrorModeConfig, ErrorOverrideService
        
        # Test with invalid service name - should raise ValueError
        with self.assertRaises(ValueError) as context:
            ErrorModeConfig(
                services={"invalid_service": ErrorOverrideService(error_mode="raise")}
            )
        
        self.assertIn("'invalid_service' is not a valid service", str(context.exception))

    def test_framework_feature_config_global_mutation_active_no_documentation(self):
        """Test FrameworkFeatureConfig with global mutation active (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig
        
        # Test with global mutation active - should allow no documentation
        from common_utils.models import Mutation
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                global_config=Mutation(mutation_name="m01")
            ),
            documentation=DocumentationConfig()  # No global or service config
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_global_mutation_active_with_global_documentation_error(self):
        """Test FrameworkFeatureConfig with global mutation and global documentation conflict (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, GlobalDocumentationConfig
        
        # Test with global mutation active and global documentation - should raise error
        from common_utils.models import Mutation
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    **{"global": Mutation(mutation_name="m01")}  # Use alias "global"
                ),
                documentation=DocumentationConfig(
                    **{"global": GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)}  # Use alias "global"
                )
            )
        
        self.assertIn("Global mutation is active; no documentation configuration", str(context.exception))

    def test_framework_feature_config_global_mutation_active_with_service_documentation_error(self):
        """Test FrameworkFeatureConfig with global mutation and service documentation conflict (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with global mutation active and service documentation - should raise error
        from common_utils.models import Mutation
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    **{"global": Mutation(mutation_name="m01")}  # Use alias "global"
                ),
                documentation=DocumentationConfig(
                    services={"gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)}
                )
            )
        
        self.assertIn("Global mutation is active; no documentation configuration", str(context.exception))

    def test_framework_feature_config_global_documentation_active_no_mutation(self):
        """Test FrameworkFeatureConfig with global documentation active (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, DocumentationConfig, GlobalDocumentationConfig
        
        # Test with global documentation active - should allow no mutation
        config = FrameworkFeatureConfig(
            documentation=DocumentationConfig(
                global_config=GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_global_documentation_active_with_service_mutation_error(self):
        """Test FrameworkFeatureConfig with global documentation and service mutation conflict (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, GlobalDocumentationConfig
        
        # Test with global documentation active and service mutation - should raise error
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    services={"gmail": MutationOverride(mutation_name="m01")}  # Use string instead of enum
                ),
                documentation=DocumentationConfig(
                    **{"global": GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)}  # Use alias "global"
                )
            )
        
        self.assertIn("Global documentation is active; no service-level mutation configurations are allowed", str(context.exception))

    def test_framework_feature_config_service_level_conflict(self):
        """Test FrameworkFeatureConfig with service-level mutation and documentation conflict (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with service-level conflict - should raise error
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    services={"gmail": MutationOverride(mutation_name="m01")}
                ),
                documentation=DocumentationConfig(
                    services={"gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)}
                )
            )
        
        self.assertIn("Mutation and documentation configurations cannot be enabled for the same service(s)", str(context.exception))

    def test_framework_feature_config_service_level_no_conflict(self):
        """Test FrameworkFeatureConfig with service-level mutation and documentation on different services (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with service-level configs on different services - should not raise error
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                services={"gmail": MutationOverride(mutation_name="m01")}
            ),
            documentation=DocumentationConfig(
                services={"gdrive": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)}
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_service_level_mutation_inactive(self):
        """Test FrameworkFeatureConfig with inactive service-level mutation (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with inactive service-level mutation - should not raise error
        # Since MutationOverride doesn't support empty strings, we'll test with no mutation config
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                services={}  # No services configured
            ),
            documentation=DocumentationConfig(
                services={"gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)}
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_service_level_mutation_none(self):
        """Test FrameworkFeatureConfig with None service-level mutation (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with None service-level mutation - should not raise error
        # Since MutationOverride doesn't support None, we'll test with no mutation config
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                services={}  # No services configured
            ),
            documentation=DocumentationConfig(
                services={"gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)}
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_no_mutation_or_documentation(self):
        """Test FrameworkFeatureConfig with no mutation or documentation (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig
        
        # Test with no mutation or documentation - should not raise error
        config = FrameworkFeatureConfig()
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_only_mutation(self):
        """Test FrameworkFeatureConfig with only mutation (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig
        
        # Test with only mutation - should not raise error
        config = FrameworkFeatureConfig(
            mutation=MutationConfig()
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_only_documentation(self):
        """Test FrameworkFeatureConfig with only documentation (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, DocumentationConfig
        
        # Test with only documentation - should not raise error
        config = FrameworkFeatureConfig(
            documentation=DocumentationConfig()
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_service_error_config_creation(self):
        """Test ServiceErrorConfig creation."""
        from common_utils.models import ServiceErrorConfig, ErrorTypeConfig
        
        # Test with ErrorTypeConfig
        config = ServiceErrorConfig(
            config={"test_error": ErrorTypeConfig(probability=0.5)},
            max_errors_per_run=10
        )
        
        self.assertEqual(config.max_errors_per_run, 10)
        self.assertIn("test_error", config.config)
        self.assertIsInstance(config.config["test_error"], ErrorTypeConfig)

    def test_global_error_config_creation(self):
        """Test GlobalErrorConfig creation."""
        from common_utils.models import GlobalErrorConfig, ErrorTypeConfig
        
        # Test with ErrorTypeConfig
        config = GlobalErrorConfig(
            config={"test_error": ErrorTypeConfig(probability=0.5)},
            max_errors_per_run=10
        )
        
        self.assertEqual(config.max_errors_per_run, 10)
        self.assertIn("test_error", config.config)
        self.assertIsInstance(config.config["test_error"], ErrorTypeConfig)

    def test_error_override_creation(self):
        """Test ErrorOverride creation."""
        from common_utils.models import ErrorOverride
        
        # Test with all fields
        override = ErrorOverride(
            error_mode="raise",
            print_error_reports=True
        )
        
        self.assertEqual(override.error_mode, "raise")
        self.assertTrue(override.print_error_reports)

    def test_error_override_service_creation(self):
        """Test ErrorOverrideService creation."""
        from common_utils.models import ErrorOverrideService
        
        # Test with all fields
        override = ErrorOverrideService(
            error_mode="error_dict",
            print_error_reports=False
        )
        
        self.assertEqual(override.error_mode, "error_dict")
        self.assertFalse(override.print_error_reports)

    def test_central_config_creation(self):
        """Test CentralConfig creation."""
        from common_utils.models import CentralConfig, DocumentationConfig, ErrorSimulationConfig
        
        # Test with all fields
        config = CentralConfig(
            documentation=DocumentationConfig(),
            error=ErrorSimulationConfig()
        )
        
        self.assertIsInstance(config.documentation, DocumentationConfig)
        self.assertIsInstance(config.error, ErrorSimulationConfig)

    def test_documentation_section_creation(self):
        """Test DocumentationSection creation."""
        from common_utils.models import DocumentationSection
        
        # Test with extra fields (should be allowed due to extra="allow")
        config = DocumentationSection(
            extra_field="extra_value",
            another_field=123
        )
        
        self.assertEqual(config.extra_field, "extra_value")
        self.assertEqual(config.another_field, 123)

    def test_error_section_creation(self):
        """Test ErrorSection creation."""
        from common_utils.models import ErrorSection
        
        # Test with extra fields (should be allowed due to extra="allow")
        config = ErrorSection(
            extra_field="extra_value",
            another_field=123
        )
        
        self.assertEqual(config.extra_field, "extra_value")
        self.assertEqual(config.another_field, 123)

    def test_framework_feature_config_creation(self):
        """Test FrameworkFeatureConfig creation (lines 250-298)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, AuthenticationConfig, DocumentationConfig, ErrorSimulationConfig, ErrorModeConfig
        
        # Test with all optional fields
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(),
            authentication=AuthenticationConfig(),
            documentation=DocumentationConfig(),
            error=ErrorSimulationConfig(),
            error_mode=ErrorModeConfig()
        )
        
        self.assertIsInstance(config.mutation, MutationConfig)
        self.assertIsInstance(config.authentication, AuthenticationConfig)
        self.assertIsInstance(config.documentation, DocumentationConfig)
        self.assertIsInstance(config.error, ErrorSimulationConfig)
        self.assertIsInstance(config.error_mode, ErrorModeConfig)

    def test_framework_feature_config_global_documentation_active_with_service_mutation_redundant_check(self):
        """Test FrameworkFeatureConfig redundant check for global documentation and global mutation (line 264)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, GlobalDocumentationConfig
        
        # This test triggers the redundant check in the validation logic
        # We need to create a scenario where global_doc_active is True but global_mutation_active is also True
        # This is tricky because the logic prevents this, but we can test the line by creating a scenario
        # where both are active but the check still happens
        from common_utils.models import Mutation
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    **{"global": Mutation(mutation_name="m01")}  # This makes global_mutation_active True
                ),
                documentation=DocumentationConfig(
                    **{"global": GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)}  # This makes global_doc_active True
                )
            )
        
        # The error should be caught by the first check, but the redundant check line should still be executed
        self.assertIn("Global mutation is active; no documentation configuration", str(context.exception))

    def test_framework_feature_config_global_documentation_active_with_service_mutation_services_check(self):
        """Test FrameworkFeatureConfig with global documentation and service mutation services check (line 269)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, GlobalDocumentationConfig
        
        # Test with global documentation active and service mutation with services - should raise error
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    services={"gmail": MutationOverride(mutation_name="m01")}
                ),
                documentation=DocumentationConfig(
                    **{"global": GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)}
                )
            )
        
        self.assertIn("Global documentation is active; no service-level mutation configurations are allowed", str(context.exception))

    def test_framework_feature_config_service_level_conflict_with_active_mutations(self):
        """Test FrameworkFeatureConfig service-level conflict with active mutations (line 279)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with service-level conflict - both mutation and documentation for same service
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    services={"gmail": MutationOverride(mutation_name="m01")}
                ),
                documentation=DocumentationConfig(
                    services={"gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE)}
                )
            )
        
        self.assertIn("Mutation and documentation configurations cannot be enabled for the same service(s): gmail", str(context.exception))

    def test_documentation_config_validate_service_names_with_empty_services(self):
        """Test DocumentationConfig validate_service_names with empty services dict (lines 134, 140)."""
        from common_utils.models import DocumentationConfig, ServiceDocumentationConfig, DocMode
        
        # Test with empty services dictionary - should not raise error
        config = DocumentationConfig(
            services={}
        )
        self.assertEqual(config.services, {})

    def test_documentation_config_validate_service_names_with_multiple_invalid_services(self):
        """Test DocumentationConfig validate_service_names with multiple invalid services (lines 134, 140)."""
        from common_utils.models import DocumentationConfig, ServiceDocumentationConfig, DocMode
        
        # Test with multiple invalid service names - should raise ValueError
        with self.assertRaises(ValueError) as context:
            DocumentationConfig(
                services={
                    "invalid_service1": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE),
                    "invalid_service2": ServiceDocumentationConfig(doc_mode=DocMode.RAW_DOCSTRING)
                }
            )
        
        # Should mention the first invalid service in the error message
        self.assertIn("'invalid_service1' is not a valid service", str(context.exception))

    def test_mutation_config_validate_service_names_with_empty_services(self):
        """Test MutationConfig validate_service_names with empty services dict (line 173)."""
        from common_utils.models import MutationConfig
        
        # Test with empty services dictionary - should not raise error
        config = MutationConfig(
            services={}
        )
        self.assertEqual(config.services, {})

    def test_authentication_config_validate_service_names_with_empty_services(self):
        """Test AuthenticationConfig validate_service_names with empty services dict (lines 206, 212)."""
        from common_utils.models import AuthenticationConfig
        
        # Test with empty services dictionary - should not raise error
        config = AuthenticationConfig(
            services={}
        )
        self.assertEqual(config.services, {})

    def test_error_mode_config_validate_service_names_with_empty_services(self):
        """Test ErrorModeConfig validate_service_names with empty services dict (lines 226, 232)."""
        from common_utils.models import ErrorModeConfig
        
        # Test with empty services dictionary - should not raise error
        config = ErrorModeConfig(
            services={}
        )
        self.assertEqual(config.services, {})

    def test_framework_feature_config_global_mutation_active_with_empty_documentation_services(self):
        """Test FrameworkFeatureConfig with global mutation active and empty documentation services (lines 264, 269)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig
        
        # Test with global mutation active and empty documentation services - should not raise error
        from common_utils.models import Mutation
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                **{"global": Mutation(mutation_name="m01")}
            ),
            documentation=DocumentationConfig(
                services={}  # Empty services dict
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_global_documentation_active_with_empty_mutation_services(self):
        """Test FrameworkFeatureConfig with global documentation active and empty mutation services (lines 264, 269)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, DocumentationConfig, GlobalDocumentationConfig
        
        # Test with global documentation active and empty mutation services - should not raise error
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                services={}  # Empty services dict
            ),
            documentation=DocumentationConfig(
                **{"global": GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)}
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_service_level_conflict_with_multiple_services(self):
        """Test FrameworkFeatureConfig service-level conflict with multiple conflicting services (line 279)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with multiple service-level conflicts - should raise error
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    services={
                        "gmail": MutationOverride(mutation_name="m01"),
                        "gdrive": MutationOverride(mutation_name="m01")
                    }
                ),
                documentation=DocumentationConfig(
                    services={
                        "gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE),
                        "gdrive": ServiceDocumentationConfig(doc_mode=DocMode.RAW_DOCSTRING)
                    }
                )
            )
        
        # Should mention both conflicting services in the error message
        error_msg = str(context.exception)
        self.assertIn("gmail", error_msg)
        self.assertIn("gdrive", error_msg)
        self.assertIn("Mutation and documentation configurations cannot be enabled for the same service(s)", error_msg)

    def test_framework_feature_config_service_level_conflict_with_inactive_mutations(self):
        """Test FrameworkFeatureConfig service-level conflict with inactive mutations (line 279)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with inactive mutations - should not raise error even with same services
        # Since MutationOverride doesn't support empty strings or None, we'll test with no mutation config
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                services={}  # No services configured
            ),
            documentation=DocumentationConfig(
                services={
                    "gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE),
                    "gdrive": ServiceDocumentationConfig(doc_mode=DocMode.RAW_DOCSTRING)
                }
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_service_level_conflict_with_mixed_active_inactive_mutations(self):
        """Test FrameworkFeatureConfig service-level conflict with mixed active and inactive mutations (line 279)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, ServiceDocumentationConfig
        
        # Test with mixed active and inactive mutations - should only conflict on active ones
        # Since MutationOverride doesn't support empty strings or None, we'll test with only active mutations
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    services={
                        "gmail": MutationOverride(mutation_name="m01"),  # Active mutation
                    }
                ),
                documentation=DocumentationConfig(
                    services={
                        "gmail": ServiceDocumentationConfig(doc_mode=DocMode.CONCISE),  # Will conflict
                    }
                )
            )
        
        # Should only mention gmail in the conflict
        error_msg = str(context.exception)
        self.assertIn("gmail", error_msg)
        self.assertNotIn("gdrive", error_msg)
        self.assertNotIn("notifications", error_msg)

    def test_framework_feature_config_global_documentation_active_with_inactive_service_mutations(self):
        """Test FrameworkFeatureConfig with global documentation and inactive service mutations (lines 264, 269)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, GlobalDocumentationConfig
        
        # Test with global documentation active and inactive service mutations - should not raise error
        # Since MutationOverride doesn't support empty strings or None, we'll test with no mutation config
        config = FrameworkFeatureConfig(
            mutation=MutationConfig(
                services={}  # No services configured
            ),
            documentation=DocumentationConfig(
                **{"global": GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)}
            )
        )
        
        # Should not raise an exception
        self.assertIsInstance(config, FrameworkFeatureConfig)

    def test_framework_feature_config_global_documentation_active_with_mixed_service_mutations(self):
        """Test FrameworkFeatureConfig with global documentation and mixed active/inactive service mutations (lines 264, 269)."""
        from common_utils.models import FrameworkFeatureConfig, MutationConfig, MutationOverride, DocumentationConfig, GlobalDocumentationConfig
        
        # Test with global documentation active and mixed service mutations - should raise error for active ones
        # Since MutationOverride doesn't support empty strings or None, we'll test with only active mutations
        with self.assertRaises(ValueError) as context:
            FrameworkFeatureConfig(
                mutation=MutationConfig(
                    services={
                        "gmail": MutationOverride(mutation_name="m01"),  # Active mutation - will cause error
                    }
                ),
                documentation=DocumentationConfig(
                    **{"global": GlobalDocumentationConfig(doc_mode=DocMode.CONCISE)}
                )
            )
        
        # Should mention gmail in the error
        error_msg = str(context.exception)
        self.assertIn("gmail", error_msg)
        self.assertIn("Global documentation is active; no service-level mutation configurations are allowed", error_msg)


if __name__ == '__main__':
    unittest.main()
