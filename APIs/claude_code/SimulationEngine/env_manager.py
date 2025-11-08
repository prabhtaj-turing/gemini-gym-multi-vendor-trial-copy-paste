"""
Environment manager for claude_code SimulationEngine.

This module handles environment variables, variable expansion, and environment-related
shell commands for the claude_code service.
"""

import logging
from typing import Dict, Any, List, Optional

# Get logger for this module
logger = logging.getLogger(__name__)

# List of allowed system environment variables
ALLOWED_SYSTEM_VARS: List[str] = [
    'PATH', 'LANG', 'HOME', 'USER', 'SHELL', 'TERM',
    'DISPLAY', 'EDITOR', 'VISUAL', 'PAGER', 'TZ'
]


def prepare_command_environment(db: Dict[str, Any], temp_dir: str) -> Dict[str, str]:
    """
    Prepare an isolated environment dictionary for command execution.
    
    Args:
        db: The database dictionary containing environment configuration
        temp_dir: The temporary directory path for command execution
    
    Returns:
        Dict[str, str]: The prepared environment dictionary
    """
    # Get shell config environment variables
    shell_config = db.get('shell_config', {})
    config_env = shell_config.get('environment_variables', {})
    
    # Initialize with base environment variables from shell config
    env: Dict[str, str] = {
        'PWD': temp_dir,
        'SHELL': '/bin/bash',
        'USER': config_env.get('USER', 'user'),
        'HOME': config_env.get('HOME', '/home/user'),
        'PATH': config_env.get('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
        'TERM': 'xterm-256color',
        'LANG': 'en_US.UTF-8',
        'LC_ALL': 'en_US.UTF-8',
        'HOSTNAME': 'isolated-env',
        'TZ': 'UTC'
    }
    
    # Add any additional environment variables from shell config
    for key, value in config_env.items():
        if key not in ['USER', 'HOME', 'PATH']:  # Already set above
            env[key] = value
    
    # Add workspace environment variables (overriding base vars)
    workspace_env = db.get('environment', {}).get('workspace', {})
    env.update(workspace_env)
    
    # Add session environment variables (overriding workspace and base vars)
    session_env = db.get('environment', {}).get('session', {})
    env.update(session_env)
    
    return env


def expand_variables(command: str, env: Dict[str, str]) -> str:
    """
    Expand environment variables in the command string.
    
    Args:
        command: The command string potentially containing environment variables
        env: The environment dictionary to use for expansion
    
    Returns:
        str: The command with environment variables expanded
    """
    result = []
    i = 0
    in_single_quotes = False
    in_double_quotes = False
    
    while i < len(command):
        char = command[i]
        
        # Handle quotes
        if char == "'" and not in_double_quotes:
            in_single_quotes = not in_single_quotes
            result.append(char)
            i += 1
            continue
        elif char == '"' and not in_single_quotes:
            in_double_quotes = not in_double_quotes
            result.append(char)
            i += 1
            continue
        
        # Handle variable expansion
        if char == '$' and not in_single_quotes:
            if i + 1 < len(command):
                next_char = command[i + 1]
                if next_char == '{':
                    # ${VAR} format
                    end_brace = command.find('}', i)
                    if end_brace != -1:
                        var_name = command[i+2:end_brace]
                        if var_name in env:
                            result.append(env[var_name])
                        else:
                            result.append('')  # Empty string for undefined vars
                        i = end_brace + 1
                        continue
                elif next_char.isalpha() or next_char == '_':
                    # $VAR format
                    var_start = i + 1
                    var_end = var_start
                    while var_end < len(command) and (command[var_end].isalnum() or command[var_end] == '_'):
                        var_end += 1
                    var_name = command[var_start:var_end]
                    if var_name in env:
                        result.append(env[var_name])
                    else:
                        result.append('')  # Empty string for undefined vars
                    i = var_end
                    continue
        
        result.append(char)
        i += 1
    
    return ''.join(result)


def handle_env_command(command: str, db: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle environment-related shell commands (env, export, unset).
    
    Args:
        command: The command string to handle
        db: The database dictionary to modify
    
    Returns:
        Dict[str, Any]: Command execution result
    """
    command = command.strip()
    
    # Initialize environment structure if it doesn't exist
    if 'environment' not in db:
        db['environment'] = {'session': {}, 'workspace': {}}
    
    session_env = db['environment']['session']
    
    # Handle 'env' command - list all environment variables
    if command == 'env':
        env_vars = prepare_command_environment(db, db.get('cwd', '/home/user'))
        env_output = '\n'.join([f"{k}={v}" for k, v in sorted(env_vars.items())])
        
        return {
            'command': command,
            'directory': db.get('cwd', '/home/user'),
            'stdout': env_output,
            'stderr': '',
            'returncode': 0,
            'pid': None,
            'process_group_id': None,
            'signal': None,
            'message': 'Environment variables listed successfully'
        }
    
    # Handle 'export VAR=value' or 'export VAR'
    elif command.startswith('export '):
        export_arg = command[7:].strip()
        
        if '=' in export_arg:
            # export VAR=value
            var_name, var_value = export_arg.split('=', 1)
            var_name = var_name.strip()
            var_value = var_value.strip().strip('"\'')  # Remove quotes
            session_env[var_name] = var_value
            message = f"Environment variable '{var_name}' exported"
        else:
            # export VAR (promote existing variable to environment)
            var_name = export_arg.strip()
            if var_name not in session_env:
                session_env[var_name] = ''  # Set to empty if not exists
            message = f"Variable '{var_name}' exported to environment"
        
        return {
            'command': command,
            'directory': db.get('cwd', '/home/user'),
            'stdout': '',
            'stderr': '',
            'returncode': 0,
            'pid': None,
            'process_group_id': None,
            'signal': None,
            'message': message
        }
    
    # Handle 'unset VAR'
    elif command.startswith('unset '):
        var_name = command[6:].strip()
        if var_name in session_env:
            del session_env[var_name]
            message = f"Environment variable '{var_name}' unset"
        else:
            message = f"Environment variable '{var_name}' was not set"
        
        return {
            'command': command,
            'directory': db.get('cwd', '/home/user'),
            'stdout': '',
            'stderr': '',
            'returncode': 0,
            'pid': None,
            'process_group_id': None,
            'signal': None,
            'message': message
        }
    
    # Unknown environment command
    else:
        return {
            'command': command,
            'directory': db.get('cwd', '/home/user'),
            'stdout': '',
            'stderr': f"bash: {command.split()[0]}: command not found",
            'returncode': 127,
            'pid': None,
            'process_group_id': None,
            'signal': None,
            'message': f"Unknown environment command: {command}"
        }


def save_workspace_environment(db: Dict[str, Any]) -> Optional[str]:
    """
    Save workspace environment to a .env file.
    
    Args:
        db: The database dictionary containing environment configuration
    
    Returns:
        Optional[str]: Path to the saved .env file or None if save failed
    """
    import os
    try:
        workspace_root = db.get('workspace_root')
        if not workspace_root:
            logger.error("workspace_root not configured in database")
            return None
            
        env_file = os.path.join(workspace_root, '.env')
        workspace_env = db.get('environment', {}).get('workspace', {})
        
        with open(env_file, 'w') as f:
            for key, value in sorted(workspace_env.items()):
                # Escape values that contain spaces or special characters
                if ' ' in value or '"' in value or "'" in value:
                    escaped_value = value.replace('"', '\\"')
                    value = f'"{escaped_value}"'
                f.write(f'export {key}={value}\n')
        
        logger.info(f"Workspace environment saved to {env_file}")
        return env_file
    except Exception as e:
        logger.error(f"Failed to save workspace environment: {e}")
        return None


def load_workspace_environment(db: Dict[str, Any]) -> bool:
    """
    Load workspace environment from .env file.
    
    Args:
        db: The database dictionary to update with loaded environment
    
    Returns:
        bool: True if environment was loaded successfully
    """
    import os
    try:
        workspace_root = db.get('workspace_root')
        if not workspace_root:
            logger.error("workspace_root not configured in database")
            return False
            
        env_file = os.path.join(workspace_root, '.env')
        if not os.path.exists(env_file):
            logger.debug(f"No .env file found at {env_file}")
            return False
        
        # Initialize environment structure if it doesn't exist
        if 'environment' not in db:
            db['environment'] = {'session': {}, 'workspace': {}}
        
        loaded_count = 0
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                if line.startswith('export '):
                    # Parse export VAR=value
                    var_assignment = line[7:].strip()
                    if '=' in var_assignment:
                        key, value = var_assignment.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        # Unescape quotes
                        value = value.replace('\\"', '"')
                        
                        db['environment']['workspace'][key] = value
                        loaded_count += 1
                    else:
                        logger.warning(f"Invalid export format on line {line_num}: {line}")
                else:
                    logger.warning(f"Unsupported line format on line {line_num}: {line}")
        
        logger.info(f"Loaded {loaded_count} environment variables from {env_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load workspace environment: {e}")
        return False
