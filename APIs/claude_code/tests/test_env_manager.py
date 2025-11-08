"""
Comprehensive tests for the claude_code SimulationEngine env_manager module.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from claude_code.SimulationEngine.db import DB
from claude_code.SimulationEngine.env_manager import (
    prepare_command_environment, 
    expand_variables, 
    handle_env_command,
    save_workspace_environment, 
    load_workspace_environment, 
    ALLOWED_SYSTEM_VARS
)


class TestPrepareCommandEnvironment(BaseTestCaseWithErrorHandler):
    """Test suite for the prepare_command_environment function."""

    def test_prepare_command_environment_minimal_db(self):
        """Test prepare_command_environment with minimal database."""
        db = {}
        temp_dir = "/tmp/test"
        
        result = prepare_command_environment(db, temp_dir)
        
        # Should have base environment variables
        expected_base_vars = {
            'PWD': temp_dir,
            'SHELL': '/bin/bash',
            'USER': 'user',
            'HOME': '/home/user',
            'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'TERM': 'xterm-256color',
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
            'HOSTNAME': 'isolated-env',
            'TZ': 'UTC'
        }
        
        for key, value in expected_base_vars.items():
            self.assertIn(key, result)
            self.assertEqual(result[key], value)

    def test_prepare_command_environment_with_shell_config(self):
        """Test prepare_command_environment with shell config variables."""
        db = {
            'shell_config': {
                'environment_variables': {
                    'USER': 'test_user',
                    'HOME': '/home/test_user',
                    'PATH': '/custom/bin:/usr/bin',
                    'CUSTOM_VAR': 'custom_value'
                }
            }
        }
        temp_dir = "/tmp/test"
        
        result = prepare_command_environment(db, temp_dir)
        
        # Should use shell config values
        self.assertEqual(result['USER'], 'test_user')
        self.assertEqual(result['HOME'], '/home/test_user')
        self.assertEqual(result['PATH'], '/custom/bin:/usr/bin')
        self.assertEqual(result['CUSTOM_VAR'], 'custom_value')
        self.assertEqual(result['PWD'], temp_dir)

    def test_prepare_command_environment_with_workspace_env(self):
        """Test prepare_command_environment with workspace environment."""
        db = {
            'shell_config': {
                'environment_variables': {
                    'BASE_VAR': 'base_value'
                }
            },
            'environment': {
                'workspace': {
                    'WORKSPACE_VAR': 'workspace_value',
                    'BASE_VAR': 'overridden_base'  # Should override base
                }
            }
        }
        temp_dir = "/tmp/test"
        
        result = prepare_command_environment(db, temp_dir)
        
        self.assertEqual(result['WORKSPACE_VAR'], 'workspace_value')
        self.assertEqual(result['BASE_VAR'], 'overridden_base')

    def test_prepare_command_environment_with_session_env(self):
        """Test prepare_command_environment with session environment."""
        db = {
            'shell_config': {
                'environment_variables': {
                    'BASE_VAR': 'base_value'
                }
            },
            'environment': {
                'workspace': {
                    'WORKSPACE_VAR': 'workspace_value',
                    'SHARED_VAR': 'workspace_shared'
                },
                'session': {
                    'SESSION_VAR': 'session_value',
                    'SHARED_VAR': 'session_shared'  # Should override workspace
                }
            }
        }
        temp_dir = "/tmp/test"
        
        result = prepare_command_environment(db, temp_dir)
        
        self.assertEqual(result['SESSION_VAR'], 'session_value')
        self.assertEqual(result['WORKSPACE_VAR'], 'workspace_value')
        self.assertEqual(result['SHARED_VAR'], 'session_shared')  # Session wins
        self.assertEqual(result['BASE_VAR'], 'base_value')

    def test_prepare_command_environment_missing_environment_structure(self):
        """Test prepare_command_environment with missing environment structure."""
        db = {
            'environment': {}  # Empty environment structure
        }
        temp_dir = "/tmp/test"
        
        result = prepare_command_environment(db, temp_dir)
        
        # Should work without workspace or session environments
        self.assertEqual(result['PWD'], temp_dir)
        self.assertEqual(result['USER'], 'user')  # Default value

    def test_prepare_command_environment_partial_environment_structure(self):
        """Test prepare_command_environment with partial environment structure."""
        db = {
            'environment': {
                'session': {
                    'SESSION_ONLY': 'session_value'
                }
                # Missing 'workspace' key
            }
        }
        temp_dir = "/tmp/test"
        
        result = prepare_command_environment(db, temp_dir)
        
        self.assertEqual(result['SESSION_ONLY'], 'session_value')
        self.assertEqual(result['PWD'], temp_dir)


class TestExpandVariables(BaseTestCaseWithErrorHandler):
    """Test suite for the expand_variables function."""

    def test_expand_variables_no_variables(self):
        """Test expand_variables with no variables to expand."""
        command = "echo hello world"
        env = {'VAR1': 'value1'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo hello world")

    def test_expand_variables_simple_variable(self):
        """Test expand_variables with simple $VAR format."""
        command = "echo $HOME/file.txt"
        env = {'HOME': '/home/user'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo /home/user/file.txt")

    def test_expand_variables_brace_format(self):
        """Test expand_variables with ${VAR} format."""
        command = "echo ${HOME}/file.txt"
        env = {'HOME': '/home/user'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo /home/user/file.txt")

    def test_expand_variables_multiple_variables(self):
        """Test expand_variables with multiple variables."""
        command = "cp $SRC/${FILE} $DEST/backup"
        env = {'SRC': '/source', 'FILE': 'data.txt', 'DEST': '/backup'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "cp /source/data.txt /backup/backup")

    def test_expand_variables_undefined_variable(self):
        """Test expand_variables with undefined variables."""
        command = "echo $UNDEFINED_VAR and ${ALSO_UNDEFINED}"
        env = {'DEFINED': 'value'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo  and ")

    def test_expand_variables_single_quotes_no_expansion(self):
        """Test expand_variables with single quotes (no expansion)."""
        command = "echo '$HOME is not expanded'"
        env = {'HOME': '/home/user'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo '$HOME is not expanded'")

    def test_expand_variables_double_quotes_with_expansion(self):
        """Test expand_variables with double quotes (expansion allowed)."""
        command = 'echo "$HOME is expanded"'
        env = {'HOME': '/home/user'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, 'echo "/home/user is expanded"')

    def test_expand_variables_mixed_quotes(self):
        """Test expand_variables with mixed quote types."""
        command = "echo '$HOME' \"$USER\" $PATH"
        env = {'HOME': '/home', 'USER': 'test', 'PATH': '/bin'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo '$HOME' \"test\" /bin")

    def test_expand_variables_nested_quotes(self):
        """Test expand_variables with nested quotes."""
        command = 'echo "Value is: \'$VAR\'"'
        env = {'VAR': 'test'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, 'echo "Value is: \'test\'"')

    def test_expand_variables_incomplete_brace(self):
        """Test expand_variables with incomplete brace format."""
        command = "echo ${INCOMPLETE and $NORMAL"
        env = {'NORMAL': 'value'}
        
        result = expand_variables(command, env)
        
        # Incomplete brace should remain as-is, normal var should expand
        self.assertEqual(result, "echo ${INCOMPLETE and value")

    def test_expand_variables_special_characters_in_values(self):
        """Test expand_variables with special characters in values."""
        command = "echo $VAR1 $VAR2"
        env = {'VAR1': 'value with spaces', 'VAR2': 'value"with"quotes'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, 'echo value with spaces value"with"quotes')

    def test_expand_variables_numeric_variable_names(self):
        """Test expand_variables with numeric in variable names."""
        command = "echo $VAR1 $VAR_2 $VAR123"
        env = {'VAR1': 'one', 'VAR_2': 'two', 'VAR123': 'onetwothree'}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo one two onetwothree")

    def test_expand_variables_empty_values(self):
        """Test expand_variables with empty variable values."""
        command = "echo start$EMPTY${ALSO_EMPTY}end"
        env = {'EMPTY': '', 'ALSO_EMPTY': ''}
        
        result = expand_variables(command, env)
        
        self.assertEqual(result, "echo startend")

    def test_expand_variables_dollar_sign_edge_cases(self):
        """Test expand_variables with edge cases around dollar signs."""
        command = "echo $ $$ $1 $@ $ test"
        env = {}
        
        result = expand_variables(command, env)
        
        # Should handle edge cases gracefully
        self.assertEqual(result, "echo $ $$ $1 $@ $ test")


class TestHandleEnvCommand(BaseTestCaseWithErrorHandler):
    """Test suite for the handle_env_command function."""

    def test_handle_env_command_env_list(self):
        """Test handle_env_command with 'env' command."""
        db = {
            'cwd': '/test/dir',
            'shell_config': {
                'environment_variables': {
                    'TEST_VAR': 'test_value'
                }
            }
        }
        
        result = handle_env_command('env', db)
        
        self.assertEqual(result['command'], 'env')
        self.assertEqual(result['directory'], '/test/dir')
        self.assertEqual(result['returncode'], 0)
        self.assertIn('TEST_VAR=test_value', result['stdout'])
        self.assertIn('PWD=/test/dir', result['stdout'])
        self.assertEqual(result['stderr'], '')

    def test_handle_env_command_env_with_default_cwd(self):
        """Test handle_env_command with 'env' command and default cwd."""
        db = {}
        
        result = handle_env_command('env', db)
        
        self.assertEqual(result['directory'], '/home/user')
        self.assertIn('PWD=/home/user', result['stdout'])

    def test_handle_env_command_export_with_value(self):
        """Test handle_env_command with 'export VAR=value'."""
        db = {}
        
        result = handle_env_command('export TEST_VAR=test_value', db)
        
        self.assertEqual(result['command'], 'export TEST_VAR=test_value')
        self.assertEqual(result['returncode'], 0)
        self.assertIn('environment', db)
        self.assertIn('session', db['environment'])
        self.assertEqual(db['environment']['session']['TEST_VAR'], 'test_value')
        self.assertIn("Environment variable 'TEST_VAR' exported", result['message'])

    def test_handle_env_command_export_with_quotes(self):
        """Test handle_env_command with quoted values."""
        db = {}
        
        # Test double quotes
        result1 = handle_env_command('export VAR1="quoted value"', db)
        self.assertEqual(db['environment']['session']['VAR1'], 'quoted value')
        
        # Test single quotes
        result2 = handle_env_command("export VAR2='single quoted'", db)
        self.assertEqual(db['environment']['session']['VAR2'], 'single quoted')

    def test_handle_env_command_export_without_value(self):
        """Test handle_env_command with 'export VAR' (no value)."""
        db = {}
        
        result = handle_env_command('export NEW_VAR', db)
        
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(db['environment']['session']['NEW_VAR'], '')
        self.assertIn("Variable 'NEW_VAR' exported", result['message'])

    def test_handle_env_command_export_existing_variable(self):
        """Test handle_env_command exporting existing variable."""
        db = {
            'environment': {
                'session': {
                    'EXISTING_VAR': 'existing_value'
                },
                'workspace': {}
            }
        }
        
        result = handle_env_command('export EXISTING_VAR', db)
        
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(db['environment']['session']['EXISTING_VAR'], 'existing_value')

    def test_handle_env_command_unset_existing(self):
        """Test handle_env_command with 'unset VAR' for existing variable."""
        db = {
            'environment': {
                'session': {
                    'TO_REMOVE': 'value_to_remove',
                    'TO_KEEP': 'value_to_keep'
                },
                'workspace': {}
            }
        }
        
        result = handle_env_command('unset TO_REMOVE', db)
        
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn('TO_REMOVE', db['environment']['session'])
        self.assertIn('TO_KEEP', db['environment']['session'])
        self.assertIn("Environment variable 'TO_REMOVE' unset", result['message'])

    def test_handle_env_command_unset_nonexistent(self):
        """Test handle_env_command with 'unset VAR' for non-existent variable."""
        db = {
            'environment': {
                'session': {},
                'workspace': {}
            }
        }
        
        result = handle_env_command('unset NONEXISTENT', db)
        
        self.assertEqual(result['returncode'], 0)
        self.assertIn("Environment variable 'NONEXISTENT' was not set", result['message'])

    def test_handle_env_command_unknown_command(self):
        """Test handle_env_command with unknown command."""
        db = {}
        
        result = handle_env_command('unknown_env_command', db)
        
        self.assertEqual(result['returncode'], 127)
        self.assertIn('command not found', result['stderr'])
        self.assertIn('Unknown environment command', result['message'])

    def test_handle_env_command_initializes_environment_structure(self):
        """Test handle_env_command initializes environment structure."""
        db = {}
        
        handle_env_command('export TEST=value', db)
        
        self.assertIn('environment', db)
        self.assertIn('session', db['environment'])
        self.assertIn('workspace', db['environment'])

    def test_handle_env_command_whitespace_handling(self):
        """Test handle_env_command with various whitespace."""
        db = {}
        
        # Test leading/trailing whitespace in command
        result = handle_env_command('  export  VAR=value  ', db)
        
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(db['environment']['session']['VAR'], 'value')

    def test_handle_env_command_export_complex_values(self):
        """Test handle_env_command with complex export values."""
        db = {}
        
        # Test value with spaces and special characters
        handle_env_command('export COMPLEX_VAR=path/with spaces:other/path', db)
        
        self.assertEqual(db['environment']['session']['COMPLEX_VAR'], 'path/with spaces:other/path')


class TestSaveWorkspaceEnvironment(BaseTestCaseWithErrorHandler):
    """Test suite for the save_workspace_environment function."""

    def setUp(self):
        """Set up test database state."""
        self.original_db_state = DB.copy()
        DB.clear()
        DB.update({
            "workspace_root": "/test_workspace",
            "cwd": "/test_workspace"
        })
    
    def tearDown(self):
        """Clean up test environment."""
        DB.clear()
        DB.update(self.original_db_state)

    def test_save_workspace_environment_success(self):
        """Test save_workspace_environment successful save."""
        db = {
            'workspace_root': "/test_workspace",
            'environment': {
                'workspace': {
                    'VAR1': 'value1',
                    'VAR2': 'value2',
                    'PATH': '/custom/bin:/usr/bin'
                }
            }
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.join') as mock_join:
                mock_join.return_value = '/test/workspace/.env'
                
                result = save_workspace_environment(db)
                
                self.assertEqual(result, '/test/workspace/.env')
                mock_file.assert_called_once_with('/test/workspace/.env', 'w')
                
                # Check written content
                handle = mock_file()
                written_calls = handle.write.call_args_list
                written_content = ''.join([call[0][0] for call in written_calls])
                
                self.assertIn('export VAR1=value1\n', written_content)
                self.assertIn('export VAR2=value2\n', written_content)

    def test_save_workspace_environment_with_quotes_in_values(self):
        """Test save_workspace_environment with quotes in values."""
        db = {
            'workspace_root': '/test/workspace',
            'environment': {
                'workspace': {
                    'VAR_WITH_SPACES': 'value with spaces',
                    'VAR_WITH_QUOTES': 'value "with" quotes',
                    'VAR_WITH_APOSTROPHE': "value 'with' apostrophe",
                    'VAR_WITH_SPECIAL': 'value;with&special*chars'
                }
            }
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.join') as mock_join:
                mock_join.return_value = '/test/workspace/.env'
                
                result = save_workspace_environment(db)
                
                self.assertEqual(result, '/test/workspace/.env')
                
                # Check written content for proper escaping
                handle = mock_file()
                written_calls = handle.write.call_args_list
                written_content = ''.join([call[0][0] for call in written_calls])
                
                self.assertIn('export VAR_WITH_SPACES="value with spaces"\n', written_content)
                self.assertIn('export VAR_WITH_QUOTES="value \\"with\\" quotes"\n', written_content)
                self.assertIn('export VAR_WITH_APOSTROPHE="value \'with\' apostrophe"\n', written_content)

    def test_save_workspace_environment_missing_workspace_root(self):
        """Test save_workspace_environment with missing workspace_root."""
        db = {
            'environment': {
                'workspace': {
                    'VAR1': 'value1'
                }
            }
        }
        
        with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
            result = save_workspace_environment(db)
            
            self.assertIsNone(result)
            mock_logger.error.assert_called_once_with("workspace_root not configured in database")

    def test_save_workspace_environment_no_workspace_root_key(self):
        """Test save_workspace_environment with None workspace_root."""
        db = {
            'workspace_root': None,
            'environment': {
                'workspace': {
                    'VAR1': 'value1'
                }
            }
        }
        
        with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
            result = save_workspace_environment(db)
            
            self.assertIsNone(result)
            mock_logger.error.assert_called_once_with("workspace_root not configured in database")

    def test_save_workspace_environment_file_write_error(self):
        """Test save_workspace_environment with file write error."""
        db = {
            'workspace_root': '/test/workspace',
            'environment': {
                'workspace': {
                    'VAR1': 'value1'
                }
            }
        }
        
        with patch('builtins.open', side_effect=IOError("Permission denied")) as mock_file:
            with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
                result = save_workspace_environment(db)
                
                self.assertIsNone(result)
                mock_logger.error.assert_called()
                # Check that error message contains the exception
                error_call = mock_logger.error.call_args_list[-1][0][0]
                self.assertIn("Failed to save workspace environment", error_call)

    def test_save_workspace_environment_empty_workspace_env(self):
        """Test save_workspace_environment with empty workspace environment."""
        db = {
            'workspace_root': '/test/workspace',
            'environment': {
                'workspace': {}
            }
        }
        
        result = save_workspace_environment(db)
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.join') as mock_join:
                mock_join.return_value = '/test/workspace/.env'
                
                result = save_workspace_environment(db)
                
                self.assertEqual(result, '/test/workspace/.env')
                # Should still create file even if empty
                mock_file.assert_called_once()

    def test_save_workspace_environment_missing_environment_structure(self):
        """Test save_workspace_environment with missing environment structure."""
        db = {
            'workspace_root': '/test/workspace'
        }
        
        result = save_workspace_environment(db)
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.join') as mock_join:
                mock_join.return_value = '/test/workspace/.env'
                
                result = save_workspace_environment(db)
                
                self.assertEqual(result, '/test/workspace/.env')
                # Should handle missing structure gracefully
                mock_file.assert_called_once()


class TestLoadWorkspaceEnvironment(BaseTestCaseWithErrorHandler):
    """Test suite for the load_workspace_environment function."""

    def setUp(self):
        """Set up test database state."""
        self.original_db_state = DB.copy()
        DB.clear()
        DB.update({
            "workspace_root": "/test_workspace",
            "cwd": "/test_workspace"
        })
    
    def tearDown(self):
        """Clean up test environment."""
        DB.clear()
        DB.update(self.original_db_state)

    def test_load_workspace_environment_success(self):
        """Test load_workspace_environment successful load."""
        db = {'workspace_root': '/test/workspace'}
        env_content = """export VAR1=value1
export VAR2=value2
export VAR3="quoted value"
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', mock_open(read_data=env_content)):
                    with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
                        result = load_workspace_environment(db)
                        
                        self.assertTrue(result)
                        self.assertIn('environment', db)
                        self.assertEqual(db['environment']['workspace']['VAR1'], 'value1')
                        self.assertEqual(db['environment']['workspace']['VAR2'], 'value2')
                        self.assertEqual(db['environment']['workspace']['VAR3'], 'quoted value')
                        
                        mock_logger.info.assert_called()
                        info_call = mock_logger.info.call_args[0][0]
                        self.assertIn("Loaded 3 environment variables", info_call)

    def test_load_workspace_environment_with_comments_and_empty_lines(self):
        """Test load_workspace_environment with comments and empty lines."""
        db = {'workspace_root': '/test/workspace'}
        env_content = """# This is a comment
export VAR1=value1

# Another comment
export VAR2=value2

# Empty line above
export VAR3=value3
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', mock_open(read_data=env_content)):
                    result = load_workspace_environment(db)
                    
                    self.assertTrue(result)
                    self.assertEqual(len(db['environment']['workspace']), 3)
                    self.assertEqual(db['environment']['workspace']['VAR1'], 'value1')
                    self.assertEqual(db['environment']['workspace']['VAR2'], 'value2')
                    self.assertEqual(db['environment']['workspace']['VAR3'], 'value3')

    def test_load_workspace_environment_quote_handling(self):
        """Test load_workspace_environment with various quote formats."""
        db = {'workspace_root': '/test/workspace'}
        env_content = '''export VAR1="double quoted"
export VAR2='single quoted'
export VAR3=unquoted
export VAR4="escaped \\"quotes\\""
'''
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', mock_open(read_data=env_content)):
                    result = load_workspace_environment(db)
                    
                    self.assertTrue(result)
                    self.assertEqual(db['environment']['workspace']['VAR1'], 'double quoted')
                    self.assertEqual(db['environment']['workspace']['VAR2'], 'single quoted')
                    self.assertEqual(db['environment']['workspace']['VAR3'], 'unquoted')
                    self.assertEqual(db['environment']['workspace']['VAR4'], 'escaped "quotes"')

    def test_load_workspace_environment_missing_workspace_root(self):
        """Test load_workspace_environment with missing workspace_root."""
        db = {}
        
        with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
            result = load_workspace_environment(db)
            
            self.assertFalse(result)
            mock_logger.error.assert_called_once_with("workspace_root not configured in database")

    def test_load_workspace_environment_missing_env_file(self):
        """Test load_workspace_environment with missing .env file."""
        db = {'workspace_root': '/test/workspace'}
        
        with patch('os.path.exists', return_value=False):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
                    result = load_workspace_environment(db)
                    
                    self.assertFalse(result)
                    mock_logger.debug.assert_called()
                    debug_call = mock_logger.debug.call_args[0][0]
                    self.assertIn("No .env file found", debug_call)

    def test_load_workspace_environment_invalid_export_format(self):
        """Test load_workspace_environment with invalid export formats."""
        db = {'workspace_root': '/test/workspace'}
        env_content = """export VAR1=value1
export INVALID_LINE_NO_EQUALS
export VAR2=value2
just_a_random_line
export VAR3=value3
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', mock_open(read_data=env_content)):
                    with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
                        result = load_workspace_environment(db)
                        
                        self.assertTrue(result)
                        # Should load valid lines and warn about invalid ones
                        self.assertEqual(len(db['environment']['workspace']), 3)
                        self.assertEqual(db['environment']['workspace']['VAR1'], 'value1')
                        
                        # Check warnings were logged
                        warning_calls = [call for call in mock_logger.warning.call_args_list]
                        self.assertTrue(len(warning_calls) >= 2)  # At least 2 invalid lines

    def test_load_workspace_environment_preserves_existing_session(self):
        """Test load_workspace_environment preserves existing session variables."""
        db = {
            'workspace_root': '/test/workspace',
            'environment': {
                'session': {
                    'EXISTING_SESSION_VAR': 'session_value'
                },
                'workspace': {}
            }
        }
        
        env_content = """export WORKSPACE_VAR=workspace_value
export COMMON_VAR=workspace_override
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', mock_open(read_data=env_content)):
                    result = load_workspace_environment(db)
                    
                    self.assertTrue(result)
                    
                    # Check that workspace variables were loaded
                    self.assertEqual(db['environment']['workspace']['WORKSPACE_VAR'], 'workspace_value')
                    self.assertEqual(db['environment']['workspace']['COMMON_VAR'], 'workspace_override')
                    
                    # Check that existing session variables were preserved
                    self.assertEqual(db['environment']['session']['EXISTING_SESSION_VAR'], 'session_value')
    
    def test_roundtrip_save_and_load_integration(self):
        """Test save and load integration with mocks."""
        # Test data
        original_workspace_env = {
            'PROJECT_NAME': 'test-project',
            'DEBUG': 'true',
            'PATH': '/custom/bin:/usr/bin',
        }
        
        # Mock save operation
        save_db = {
            'workspace_root': '/test/workspace',
            'environment': {
                'workspace': original_workspace_env
            }
        }
        
        # Step 1: Test save
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.join', return_value='/test/workspace/.env'):
                result = save_workspace_environment(save_db)
                self.assertEqual(result, '/test/workspace/.env')
                mock_file.assert_called_once()
        
        # Step 2: Test load with same data
        load_db = {'workspace_root': '/test/workspace'}
        expected_content = 'export PROJECT_NAME=test-project\nexport DEBUG=true\nexport PATH=/custom/bin:/usr/bin\n'
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', mock_open(read_data=expected_content)):
                    result = load_workspace_environment(load_db)
                    
                    self.assertTrue(result)
                    loaded_env = load_db['environment']['workspace']
                    self.assertEqual(loaded_env['PROJECT_NAME'], 'test-project')
                    self.assertEqual(loaded_env['DEBUG'], 'true')
                    self.assertEqual(loaded_env['PATH'], '/custom/bin:/usr/bin')

    def test_load_workspace_environment_file_read_error(self):
        """Test load_workspace_environment with file read error."""
        db = {'workspace_root': '/test/workspace'}
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', side_effect=IOError("Permission denied")):
                    with patch('claude_code.SimulationEngine.env_manager.logger') as mock_logger:
                        result = load_workspace_environment(db)
                        
                        self.assertFalse(result)
                        mock_logger.error.assert_called()
                        error_call = mock_logger.error.call_args[0][0]
                        self.assertIn("Failed to load workspace environment", error_call)

    def test_load_workspace_environment_initializes_structure(self):
        """Test load_workspace_environment initializes environment structure."""
        db = {'workspace_root': '/test/workspace'}
        env_content = "export VAR1=value1\n"
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value='/test/workspace/.env'):
                with patch('builtins.open', mock_open(read_data=env_content)):
                    result = load_workspace_environment(db)
                    
                    self.assertTrue(result)
                    self.assertIn('environment', db)
                    self.assertIn('workspace', db['environment'])
                    self.assertIn('session', db['environment'])

class TestAllowedSystemVars(BaseTestCaseWithErrorHandler):
    """Test suite for ALLOWED_SYSTEM_VARS constant."""

    def test_allowed_system_vars_contains_expected_vars(self):
        """Test ALLOWED_SYSTEM_VARS contains expected variables."""
        expected_vars = ['PATH', 'LANG', 'HOME', 'USER', 'SHELL', 'TERM', 'DISPLAY', 'EDITOR', 'VISUAL', 'PAGER', 'TZ']
        
        for var in expected_vars:
            self.assertIn(var, ALLOWED_SYSTEM_VARS)

    def test_allowed_system_vars_is_list(self):
        """Test ALLOWED_SYSTEM_VARS is a list."""
        self.assertIsInstance(ALLOWED_SYSTEM_VARS, list)

    def test_allowed_system_vars_all_strings(self):
        """Test all items in ALLOWED_SYSTEM_VARS are strings."""
        for var in ALLOWED_SYSTEM_VARS:
            self.assertIsInstance(var, str)


if __name__ == "__main__":
    unittest.main()
