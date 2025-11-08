from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
from typing import Dict, Any, Optional, Union
import ast
import io
import contextlib
import uuid
import inspect
import os
import importlib
from datetime import datetime, timezone

from blender.SimulationEngine.db import DB
from blender.SimulationEngine.models import BlenderCodeExecutionOutcomeModel, ExecutionStatus
from blender.SimulationEngine import models as sim_models # For accessing all models
from blender.SimulationEngine.custom_errors import InvalidInputError, ValidationError

# --- Dynamically discover and import API modules --- #
MODULES_TO_INJECT = []
current_dir = os.path.dirname(os.path.abspath(__file__))
package_name = __package__  # Should be 'APIs.blender' or similar

if package_name: # Proceed only if running as part of a package
    for filename in os.listdir(current_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "execution.py"]:
            module_name_str = filename[:-3]  # Remove .py
            try:
                module = importlib.import_module(f".{module_name_str}", package=package_name)
                MODULES_TO_INJECT.append(module)
            except ImportError as e:
                print_log(f"Warning: Could not dynamically import module '{module_name_str}' from '{filename}': {e}")
else:
    print_log("Warning: Could not determine package name. Dynamic module loading for execute_blender_code will be limited.")

# Explicitly add modules from subdirectories or those requiring specific aliases if not covered dynamically
MODULES_TO_INJECT.append(sim_models)

# Ensure no duplicates if a module somehow got added twice (e.g. future refactoring)
# and preserve order as much as possible (though order isn't strictly critical for globals injection)
unique_modules_temp = []
seen_module_names = set()
for mod in MODULES_TO_INJECT:
    if mod.__name__ not in seen_module_names:
        unique_modules_temp.append(mod)
        seen_module_names.add(mod.__name__)
MODULES_TO_INJECT = unique_modules_temp
# --- End of dynamic module discovery --- #

# @handle_package_errors # Apply this if/where defined
@tool_spec(
    spec={
        'name': 'run_python_script_in_blender',
        'description': """ Execute arbitrary Python code in Blender simulation environment.
        
        Allows access to functions/classes from dynamically discovered API modules 
        (in the same directory as this file, e.g., object.py, scene.py),
        classes from SimulationEngine.models, and the DB object.
        
        This function facilitates the execution of arbitrary Python code within Blender.
        The function executes the entire provided code string in a single execution,
        capturing both standard output and the return value of the last expression
        (if the code ends with an expression). The 'code' parameter accepts the
        Python code string for execution. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'string',
                    'description': 'The Python code string to execute.'
                }
            },
            'required': [
                'code'
            ]
        }
    }
)
def execute_blender_code(code: str) -> Dict[str, Union[str, Any]]:
    """Execute arbitrary Python code in Blender simulation environment.
    Allows access to functions/classes from dynamically discovered API modules 
    (in the same directory as this file, e.g., object.py, scene.py),
    classes from SimulationEngine.models, and the DB object.

    This function facilitates the execution of arbitrary Python code within Blender.
    The function executes the entire provided code string in a single execution,
    capturing both standard output and the return value of the last expression
    (if the code ends with an expression). The 'code' parameter accepts the
    Python code string for execution.

    Args:
        code (str): The Python code string to execute.

    Returns:
        Dict[str, Union[str, Any]]: A dictionary detailing the result of the Python code
            execution. Contains the following keys:
            'status' (str): Indicates the outcome of the execution, e.g., 'success' or 'error'.
            'output' (Optional[str]): Standard output (stdout) captured from the
                executed code. Present if the code produces stdout and execution
                is successful or partially successful.
            'error_message' (Optional[str]): Standard error (stderr) or a Python
                exception message if the code failed or an error occurred.
                Present if 'status' is 'error'.
            'return_value' (Any): The direct return value from the last expression
                evaluated in the Python code, if any. The type of this field
                depends on what the executed code returns.

    Raises:
        InvalidInputError: If the provided 'code' string is malformed, empty, or
                           cannot be compiled by Python.
        ValidationError: If input arguments fail validation.
    """

    if not isinstance(code, str):
        raise ValidationError(f"Input 'code' must be a string, got {type(code).__name__}")

    if not code.strip():
        raise InvalidInputError("Code string cannot be empty.")

    compiled_code_object = None
    try:
        compiled_code_object = compile(code, '<string>', 'exec')
    except SyntaxError as e:
        # Using e.msg and e.lineno for a more informative error message.
        error_detail = f"{e.msg} on line {e.lineno}" if e.lineno else e.msg
        raise InvalidInputError(f"Provided code has syntax errors: {error_detail}")
    except ValueError as e:
        raise InvalidInputError(f"Provided code is malformed: {str(e)}")

    log_id = uuid.uuid4()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    output_capture = io.StringIO()
    # Provide DB (as 'DB') and standard builtins in the execution scope.
    execution_globals = {"DB": DB, "__builtins__": __builtins__}

    # Dynamically add functions and classes from specified API modules to the execution scope
    for module in MODULES_TO_INJECT:
        for name, member in inspect.getmembers(module):
            if not name.startswith('_'): # Avoid private/special members
                if inspect.isfunction(member) or inspect.isclass(member):
                    if name not in execution_globals: # Avoid overwriting existing globals like _simulation_db or builtins
                        execution_globals[name] = member
                    # else: print(f"Skipping {name} from {module.__name__} as it would overwrite an existing global.")

    execution_locals = {} # Each execution runs in its own local scope

    return_value = None
    error_message_str = None
    stdout_str = None
    status_enum = ExecutionStatus.SUCCESS # Assume success initially

    try:
        with contextlib.redirect_stdout(output_capture):
            # Parse the code again (already syntax-checked) to analyze its structure for return value.
            tree = ast.parse(code) 
            
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                # The last part of the code is an expression.
                # Execute all statements before the final expression.
                if len(tree.body) > 1:
                    main_code_module = ast.Module(body=tree.body[:-1], type_ignores=[])
                    main_code_obj = compile(main_code_module, '<string>', 'exec')
                    exec(main_code_obj, execution_globals, execution_locals)
                
                # Compile and evaluate the final expression to get its value.
                last_expr_module = ast.Expression(tree.body[-1].value)
                last_expr_obj = compile(last_expr_module, '<string>', 'eval')
                return_value = eval(last_expr_obj, execution_globals, execution_locals)
            else:
                # The code is empty, or the last part is not an expression (e.g., an assignment).
                # Execute the entire compiled code object.
                if compiled_code_object: # Should always be true if no prior compile error
                    exec(compiled_code_object, execution_globals, execution_locals)
        
        stdout_str = output_capture.getvalue()

    except Exception as e:
        status_enum = ExecutionStatus.ERROR
        error_message_str = f"{type(e).__name__}: {str(e)}"
        # Capture any stdout produced before the error occurred.
        stdout_str = output_capture.getvalue() 
    finally:
        output_capture.close()
        
        log_entry_data_for_db = {
            "id": str(log_id), # Store UUID as string for JSON compatibility in DB
            "timestamp": timestamp,
            "code_executed": code,
            "status": status_enum.value, # Store the string value of the enum
            "output": stdout_str if stdout_str else None, # Store None if output is empty
            "error_message": error_message_str,
            "return_value_str": str(return_value) if return_value is not None else None
        }
        
        try:
            # Validate the structure of the log entry data using the Pydantic model
            # This ensures consistency with the defined schema before storing.
            BlenderCodeExecutionOutcomeModel(**log_entry_data_for_db)
            DB["execution_logs"].append(log_entry_data_for_db)
        except ValidationError as model_val_error:
            # This indicates an internal issue: data generated for logging doesn't match the model.
            print_log(f"INTERNAL ERROR: Failed to validate log entry data for DB: {model_val_error}")
            # Consider a more robust internal error logging mechanism here if needed.

    return {
        'status': status_enum.value,
        'output': stdout_str if stdout_str else None,
        'error_message': error_message_str,
        'return_value': return_value
    }