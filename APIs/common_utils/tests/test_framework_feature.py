#!/usr/bin/env python3
"""
Tests for framework_feature module.
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from APIs.common_utils.base_case import BaseTestCaseWithErrorHandler
from common_utils.framework_feature import FrameworkFeature, framework_feature_manager


class TestFrameworkFeature(BaseTestCaseWithErrorHandler):
    """Test cases for FrameworkFeature class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset class state before each test
        FrameworkFeature._instance = None
        FrameworkFeature._is_active = False
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Reset class state after each test
        FrameworkFeature._instance = None
        FrameworkFeature._is_active = False
        
        # Clean up test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_singleton_pattern(self):
        """Test that FrameworkFeature follows singleton pattern (lines 41-43)."""
        # Create two instances
        instance1 = FrameworkFeature()
        instance2 = FrameworkFeature()
        
        # Verify they are the same instance
        self.assertIs(instance1, instance2)
        self.assertIs(instance1, FrameworkFeature._instance)

    def test_apply_config_already_active(self):
        """Test applying configuration when already active (lines 41-43)."""
        framework = FrameworkFeature()
        framework._is_active = True
        
        config = {'mutation': {'enabled': True}}
        
        # Should print warning and return early
        with patch('builtins.print') as mock_print:
            framework.apply_config(config)
            
            # Verify warning was printed
            mock_print.assert_called_with("Warning: A configuration is already active. Revert it before applying a new one.")

    def test_apply_config_success_basic(self):
        """Test successful application of configuration (lines 45-59)."""
        framework = FrameworkFeature()
        config = {'mutation': {'enabled': True}}
        
        # Mock _discover_services to return test services
        with patch.object(FrameworkFeature, '_discover_services', return_value=['gdrive']):
            framework.apply_config(config)
            
            # Verify framework is now active
            self.assertTrue(framework._is_active)

    def test_apply_config_with_errorsimulation_special_case(self):
        """Test applying configuration with errorsimulation special case (lines 52-54)."""
        framework = FrameworkFeature()
        config = {'error': {'simulation_enabled': True}}
        
        # Mock _discover_services to return test services
        with patch.object(FrameworkFeature, '_discover_services', return_value=['gdrive']):
            framework.apply_config(config)
            
            # Verify framework is now active
            self.assertTrue(framework._is_active)

    def test_revert_all_success(self):
        """Test successful reversion of all configurations (lines 65-71)."""
        framework = FrameworkFeature()
        framework._is_active = True
        
        framework.revert_all()
        
        # Verify framework is no longer active
        self.assertFalse(framework._is_active)

    def test_revert_all_not_active(self):
        """Test reversion when no configuration is active (lines 65-67)."""
        framework = FrameworkFeature()
        framework._is_active = False
        
        # Should return early without calling any managers
        framework.revert_all()
        
        # Verify framework remains inactive
        self.assertFalse(framework._is_active)

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.abspath')
    def test_discover_services_success(self, mock_abspath, mock_isdir, mock_listdir):
        """Test successful service discovery (lines 77-83)."""
        # Mock the directory structure
        mock_abspath.return_value = '/mock/api/root'
        mock_listdir.return_value = ['gdrive', 'gmail', 'common_utils', 'calendar', 'slack']
        mock_isdir.side_effect = lambda path: path.endswith(('gdrive', 'gmail', 'common_utils', 'calendar', 'slack'))
        
        framework = FrameworkFeature()
        services = framework._discover_services()
        
        # Verify services were discovered correctly (excluding common_utils)
        expected_services = ['calendar', 'gdrive', 'gmail', 'slack']
        self.assertEqual(services, expected_services)
        
        # Verify os.path.abspath was called correctly
        mock_abspath.assert_called_once()

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.abspath')
    def test_discover_services_empty_directory(self, mock_abspath, mock_isdir, mock_listdir):
        """Test service discovery with empty directory (lines 77-83)."""
        # Mock empty directory
        mock_abspath.return_value = '/mock/api/root'
        mock_listdir.return_value = []
        
        framework = FrameworkFeature()
        services = framework._discover_services()
        
        # Verify empty list is returned
        self.assertEqual(services, [])
        
        # Verify os.path.abspath was called correctly
        mock_abspath.assert_called_once()

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.abspath')
    def test_discover_services_only_common_utils(self, mock_abspath, mock_isdir, mock_listdir):
        """Test service discovery when only common_utils exists (lines 77-83)."""
        # Mock directory with only common_utils
        mock_abspath.return_value = '/mock/api/root'
        mock_listdir.return_value = ['common_utils']
        mock_isdir.return_value = True
        
        framework = FrameworkFeature()
        services = framework._discover_services()
        
        # Verify empty list is returned (common_utils is excluded)
        self.assertEqual(services, [])
        
        # Verify os.path.abspath was called correctly
        mock_abspath.assert_called_once()

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.abspath')
    def test_discover_services_mixed_content(self, mock_abspath, mock_isdir, mock_listdir):
        """Test service discovery with mixed content (files and directories) (lines 77-83)."""
        # Mock directory with files and directories
        mock_abspath.return_value = '/mock/api/root'
        mock_listdir.return_value = ['gdrive', 'gmail', 'README.md', 'config.json', 'common_utils']
        mock_isdir.side_effect = lambda path: path.endswith(('gdrive', 'gmail', 'common_utils'))
        
        framework = FrameworkFeature()
        services = framework._discover_services()
        
        # Verify only directories (excluding common_utils) are returned
        expected_services = ['gdrive', 'gmail']
        self.assertEqual(services, expected_services)
        
        # Verify os.path.abspath was called correctly
        mock_abspath.assert_called_once()

    def test_apply_config_with_empty_config(self):
        """Test applying empty configuration (lines 45-59)."""
        framework = FrameworkFeature()
        config = {}
        
        # Mock _discover_services to return test services
        with patch.object(FrameworkFeature, '_discover_services', return_value=['gdrive']):
            framework.apply_config(config)
            
            # Verify framework is still active (even with empty config)
            self.assertTrue(framework._is_active)

    def test_apply_config_with_unknown_framework(self):
        """Test applying configuration with unknown framework name (lines 45-59)."""
        framework = FrameworkFeature()
        config = {
            'unknown_framework': {'enabled': True},
            'mutation': {'enabled': True}
        }
        
        # Mock _discover_services to return test services
        with patch.object(FrameworkFeature, '_discover_services', return_value=['gdrive']):
            framework.apply_config(config)
            
            # Verify framework is now active
            self.assertTrue(framework._is_active)

    def test_apply_config_with_multiple_frameworks(self):
        """Test applying configuration with multiple frameworks (lines 45-59)."""
        framework = FrameworkFeature()
        config = {
            'mutation': {'enabled': True},
            'authentication': {'mode': 'oauth'},
            'documentation': {'doc_mode': 'detailed'},
            'error': {'simulation_enabled': True}
        }
        
        # Mock _discover_services to return test services
        with patch.object(FrameworkFeature, '_discover_services', return_value=['gdrive', 'gmail']):
            framework.apply_config(config)
            
            # Verify framework is now active
            self.assertTrue(framework._is_active)

    def test_apply_config_with_partial_frameworks(self):
        """Test applying configuration with only some frameworks (lines 45-59)."""
        framework = FrameworkFeature()
        config = {
            'mutation': {'enabled': True},
            'documentation': {'doc_mode': 'detailed'}
        }
        
        # Mock _discover_services to return test services
        with patch.object(FrameworkFeature, '_discover_services', return_value=['gdrive']):
            framework.apply_config(config)
            
            # Verify framework is now active
            self.assertTrue(framework._is_active)


if __name__ == '__main__':
    unittest.main()
