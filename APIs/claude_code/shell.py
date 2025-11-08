"""claude_code shell tool implementations.
"""
from __future__ import annotations
from common_utils.tool_spec_decorator import tool_spec

import logging
import os
import platform
import subprocess
from typing import Any, Dict, Optional

from common_utils.log_complexity import log_complexity

from .SimulationEngine.custom_errors import (
    CommandExecutionError,
    InvalidInputError,
    WorkspaceNotAvailableError,
)
from .SimulationEngine.db import DB
from .SimulationEngine.file_utils import _is_within_workspace
from .SimulationEngine.env_manager import (
    prepare_command_environment,
    expand_variables,
    handle_env_command
)
from .SimulationEngine.utils import with_common_file_system

logger = logging.getLogger(__name__)

DEFAULT_COMMAND_TIMEOUT = 60


@log_complexity
@with_common_file_system
@tool_spec(
    spec={
        'name': 'bash',
        'description': 'Execute a shell command in the workspace environment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'The shell command to execute.'
                },
                'description': {
                    'type': 'string',
                    'description': "A brief description of the command's purpose. This is not used in the function logic but can be useful for logging or debugging. Defaults to None."
                },
                'directory': {
                    'type': 'string',
                    'description': 'The directory to execute the command in, relative to the workspace root. If not provided, the command is executed in the workspace root. Defaults to None.'
                },
                'background': {
                    'type': 'boolean',
                    'description': 'Whether to run the command in the background. This is not currently implemented and is ignored. Defaults to False.'
                }
            },
            'required': [
                'command'
            ]
        }
    }
)
def bash(
    command: str,
    *,
    description: Optional[str] = None,
    directory: Optional[str] = None,
    background: Optional[bool] = False,
) -> Dict[str, Any]:
    """Execute a shell command in the workspace environment.

    Args:
        command (str): The shell command to execute.
        description (Optional[str]): A brief description of the command's purpose. This is not used in the function logic but can be useful for logging or debugging. Defaults to None.
        directory (Optional[str]): The directory to execute the command in, relative to the workspace root. If not provided, the command is executed in the workspace root. Defaults to None.
        background (Optional[bool]): Whether to run the command in the background. This is not currently implemented and is ignored. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing the execution result with the following keys:
            - command (str): The command that was executed.
            - directory (str): The execution directory.
            - stdout (str): The standard output of the command.
            - stderr (str): The standard error of the command.
            - returncode (int): The return code of the command.

    Raises:
        InvalidInputError: If the 'command' argument is empty or if the specified 'directory' is outside the workspace.
        WorkspaceNotAvailableError: If the workspace root is not configured.
        CommandExecutionError: If the command is not found, times out, or if any other unexpected error occurs during execution.
    """
    if not isinstance(command, str) or not command.strip():
        raise InvalidInputError("'command' cannot be empty")

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    exec_dir = workspace_root
    if directory:
        exec_dir = os.path.join(workspace_root, directory)
        if not _is_within_workspace(exec_dir, workspace_root):
            raise InvalidInputError("Directory is outside of the workspace")

    # Handle environment commands
    stripped_command = command.strip()
    if stripped_command in ('env',) or stripped_command.startswith(('export ', 'unset ')):
        return handle_env_command(stripped_command, DB)

    try:
        # Prepare environment for command execution
        env_vars = prepare_command_environment(DB, exec_dir)
        
        # Expand environment variables in the command
        expanded_command = expand_variables(command, env_vars)
        
        kwargs = {
            "stdout": subprocess.PIPE, 
            "stderr": subprocess.PIPE, 
            "text": True,
            "env": env_vars
        }
        if os.path.exists(exec_dir):
            kwargs["cwd"] = exec_dir

        if platform.system() == "Windows":
            process = subprocess.Popen(["cmd.exe", "/c", expanded_command], **kwargs)
        else:
            process = subprocess.Popen(["bash", "-c", expanded_command], **kwargs)

        stdout, stderr = process.communicate(timeout=DEFAULT_COMMAND_TIMEOUT)

        return {
            "command": command,
            "directory": exec_dir,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode,
        }

    except FileNotFoundError:
        raise CommandExecutionError(f"Command not found: {command.split()[0]}")
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        raise CommandExecutionError(
            f"Command timed out after {DEFAULT_COMMAND_TIMEOUT} seconds"
        )
    except Exception as e:
        raise CommandExecutionError(f"An unexpected error occurred: {e}")
