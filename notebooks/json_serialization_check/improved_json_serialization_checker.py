#!/usr/bin/env python3
"""
Improved JSON Serialization Checker

This script checks all API functions to ensure they return JSON serializable data
using intelligent LLM analysis and incremental CSV saving.

Usage:
    python improved_json_serialization_checker.py
"""

import os
import sys
import json
import ast
import csv
import traceback
import time
import importlib
import inspect
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

# Only import what we need for local execution
try:
    import google.generativeai as genai
    print("✅ Google Generative AI imported successfully")
except ImportError:
    print("❌ Failed to import google.generativeai. Please install: pip install google-generativeai")
    exit(1)

try:
    from dotenv import load_dotenv
    print("✅ Python-dotenv imported successfully")
except ImportError:
    print("❌ Failed to import python-dotenv. Please install: pip install python-dotenv")
    exit(1)

print("✅ All required packages available!")

# Load environment variables from .env file
load_dotenv('.env')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Gemini Configuration (loaded from environment variables)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
API_CALL_DELAY = int(os.getenv("API_CALL_DELAY"))

# Output configuration
OUTPUT_DIR = "json_serialization_results"
CSV_OUTPUT_FILE = "improved_json_serialization_check.csv"
SUMMARY_OUTPUT_FILE = "improved_json_serialization_summary.md"

# Processing configuration
MAX_THREADS = int(os.getenv("MAX_THREADS"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS"))

# API base path (relative to script location)
API_BASE_PATH = "../../APIs"

# Analysis dimensions
ANALYSIS_DIMENSIONS = [
    'is_json_serializable',
    'has_custom_objects',
    'has_generators',
    'has_callables',
    'has_file_handles',
    'has_network_objects',
    'has_threading_objects',
    'requires_parameters',
    'execution_successful'
]

# Global variables
gemini_client = None
api_call_lock = threading.Lock()
csv_write_lock = threading.Lock()
last_api_call_time = 0
analysis_results = []

# =============================================================================
# GEMINI API SETUP
# =============================================================================

def configure_gemini_client():
    """Configure and initialize the Gemini API client."""
    global gemini_client
    try:
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not configured. Please set it in the .env file.")
            print("   Create a .env file in this directory with: GEMINI_API_KEY=your_api_key_here")
            return None
            
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_client = genai.GenerativeModel(MODEL_NAME)
        print(f"✅ Gemini client initialized successfully with model: {MODEL_NAME}")
        return gemini_client
    except Exception as e:
        print(f"❌ Error configuring Gemini client: {e}")
        return None

def call_gemini_api_threadsafe(prompt_text: str, thread_id: str = "", max_retries: int = 3) -> str:
    """Thread-safe Gemini API call with rate limiting and retry logic."""
    global last_api_call_time, api_call_lock
    
    if not gemini_client:
        return "Error: Gemini client not initialized."
    
    for attempt in range(max_retries):
        try:
            # Thread-safe rate limiting
            with api_call_lock:
                current_time = time.time()
                time_since_last_call = current_time - last_api_call_time
                
                if time_since_last_call < API_CALL_DELAY:
                    sleep_time = API_CALL_DELAY - time_since_last_call
                    time.sleep(sleep_time)
                
                last_api_call_time = time.time()
            
            # Make API call
            response = gemini_client.generate_content(
                prompt_text,
                generation_config={"temperature": 0.3}
            )
            
            if response.candidates:
                candidate = response.candidates[0]
                
                try:
                    finish_reason = candidate.finish_reason.value
                except AttributeError:
                    finish_reason = candidate.finish_reason
                
                if finish_reason == 1:  # STOP
                    if candidate.content and candidate.content.parts:
                        return "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    return ""
                elif finish_reason == 2:  # MAX_TOKENS
                    content = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text')) if candidate.content else ""
                    return f"Error: Response truncated due to MAX_TOKENS. Content: {content}"
                else:
                    return f"Error: Unexpected finish reason: {finish_reason}"
            else:
                return "Error: No response candidates"
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Thread {thread_id}: API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"❌ Thread {thread_id}: API call failed after {max_retries} attempts: {e}")
                return f"Error: API call failed after {max_retries} attempts: {e}"
    
    return "Error: Unexpected error in API call"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def ensure_output_directory():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created output directory: {OUTPUT_DIR}")
    else:
        print(f"📁 Output directory exists: {OUTPUT_DIR}")

def get_api_directories() -> List[str]:
    """Get list of all API directories."""
    api_path = Path(API_BASE_PATH)
    if not api_path.exists():
        print(f"❌ API directory not found: {api_path}")
        return []
    
    api_dirs = []
    for item in api_path.iterdir():
        if item.is_dir() and not item.name.startswith('__'):
            api_dirs.append(item.name)
    
    print(f"📋 Found {len(api_dirs)} API directories (excluding tests only)")
    return sorted(api_dirs)

def extract_functions_from_file(file_path: str) -> List[Dict]:
    """Extract all function definitions from a Python file, excluding test and private functions."""
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions, test functions, and internal utilities
                if (node.name.startswith('_') or 
                    node.name.startswith('test') or 
                    node.name.endswith('_test') or
                    'test' in node.name.lower()):
                    continue
                
                # Extract function signature
                signature = get_function_signature(node)
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                # Extract function code
                lines = content.split('\n')
                function_code = extract_function_code(lines, node.lineno, node.end_lineno)
                
                functions.append({
                    'name': node.name,
                    'signature': signature,
                    'docstring': docstring or "",
                    'line_number': node.lineno,
                    'code': function_code
                })
                
    except Exception as e:
        print(f"⚠️  Error extracting functions from {file_path}: {e}")
    
    return functions

def get_function_signature(node: ast.FunctionDef) -> str:
    """Extract function signature from AST node."""
    try:
        # Get function name
        name = node.name
        
        # Get arguments
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            if hasattr(arg, 'annotation') and arg.annotation:
                arg_type = ast.unparse(arg.annotation)
                args.append(f"{arg_name}: {arg_type}")
            else:
                args.append(arg_name)
        
        # Get return type annotation
        return_type = ""
        if hasattr(node, 'returns') and node.returns:
            return_type = f" -> {ast.unparse(node.returns)}"
        
        return f"{name}({', '.join(args)}){return_type}"
        
    except Exception as e:
        print(f"⚠️  Error extracting signature: {e}")
        return f"{node.name}(...)" 

def extract_function_code(lines: List[str], start_line: int, end_line: int) -> str:
    """Extract function code from lines."""
    try:
        return '\n'.join(lines[start_line-1:end_line])
    except:
        return ""

def get_api_functions(api_name: str) -> Dict[str, List[Dict]]:
    """Get all functions from an API directory, excluding test files."""
    api_path = Path(API_BASE_PATH) / api_name
    if not api_path.exists():
        return {}
    
    functions_by_file = {}
    
    for py_file in api_path.rglob("*.py"):
        # Skip test directories and test files only
        if (py_file.name.startswith('__') or 
            'test' in py_file.parts or 
            py_file.name.startswith('test_') or 
            py_file.name.endswith('_test.py') or
            'tests' in str(py_file)):
            continue
        
        relative_path = str(py_file.relative_to(api_path))
        functions = extract_functions_from_file(str(py_file))
        
        if functions:
            functions_by_file[relative_path] = functions
    
    return functions_by_file

def is_json_serializable(obj) -> Tuple[bool, str, Dict[str, bool]]:
    """Enhanced check if an object is JSON serializable with detailed analysis."""
    analysis = {
        'has_custom_objects': False,
        'has_generators': False,
        'has_callables': False,
        'has_file_handles': False,
        'has_network_objects': False,
        'has_threading_objects': False
    }
    
    try:
        # First, try basic JSON serialization
        json.dumps(obj)
        
        # If successful, do deeper analysis for potential issues
        analysis = analyze_object_structure(obj)
        
        return True, "JSON serializable", analysis
        
    except TypeError as e:
        error_msg = str(e)
        
        # Analyze the error to determine the type of non-serializable object
        if "generator" in error_msg.lower():
            analysis['has_generators'] = True
        elif "callable" in error_msg.lower() or "function" in error_msg.lower():
            analysis['has_callables'] = True
        elif "file" in error_msg.lower():
            analysis['has_file_handles'] = True
        elif "thread" in error_msg.lower() or "lock" in error_msg.lower():
            analysis['has_threading_objects'] = True
        elif "socket" in error_msg.lower() or "connection" in error_msg.lower():
            analysis['has_network_objects'] = True
        else:
            analysis['has_custom_objects'] = True
        
        return False, f"Not JSON serializable: {error_msg}", analysis
        
    except Exception as e:
        return False, f"Serialization error: {str(e)}", analysis

def analyze_object_structure(obj, max_depth=3, current_depth=0) -> Dict[str, bool]:
    """Recursively analyze object structure for potential serialization issues."""
    analysis = {
        'has_custom_objects': False,
        'has_generators': False,
        'has_callables': False,
        'has_file_handles': False,
        'has_network_objects': False,
        'has_threading_objects': False
    }
    
    if current_depth >= max_depth:
        return analysis
    
    try:
        obj_type = type(obj).__name__
        
        # Check for problematic types
        if obj_type in ['generator', 'Generator']:
            analysis['has_generators'] = True
        elif callable(obj):
            analysis['has_callables'] = True
        elif hasattr(obj, 'fileno'):  # File-like objects
            analysis['has_file_handles'] = True
        elif obj_type in ['socket', 'Socket', 'SSLSocket']:
            analysis['has_network_objects'] = True
        elif obj_type in ['thread', 'Thread', 'Lock', 'RLock', 'Event']:
            analysis['has_threading_objects'] = True
        elif hasattr(obj, '__dict__') and not obj_type in ['dict', 'list', 'tuple', 'str', 'int', 'float', 'bool']:
            analysis['has_custom_objects'] = True
        
        # Recursively check containers
        if isinstance(obj, (dict, list, tuple)):
            for item in (obj.values() if isinstance(obj, dict) else obj):
                if current_depth < max_depth:
                    item_analysis = analyze_object_structure(item, max_depth, current_depth + 1)
                    for key in analysis:
                        analysis[key] = analysis[key] or item_analysis[key]
        
        return analysis
        
    except Exception:
        analysis['has_custom_objects'] = True
        return analysis

def analyze_return_type_annotation(signature: str) -> Tuple[bool, str]:
    """Analyze return type annotation to predict JSON serialization potential."""
    if " -> " not in signature:
        return False, "No return type annotation"
    
    return_type = signature.split(" -> ")[-1].strip()
    
    # Common JSON-serializable types
    json_types = {
        "Dict[str, Any]", "dict", "Dict", "List", "list", "str", "int", "float", "bool", "None",
        "Optional[str]", "Optional[int]", "Optional[float]", "Optional[bool]",
        "List[str]", "List[int]", "List[Dict]", "List[Dict[str, Any]]",
        "Union[str, None]", "Union[int, None]", "Union[float, None]", "Union[bool, None]",
        "Tuple", "tuple", "Set", "set"
    }
    
    # Check if return type suggests JSON serializability
    for json_type in json_types:
        if json_type in return_type:
            return True, f"Likely JSON serializable based on annotation: {return_type}"
    
    # Check for problematic patterns
    problematic_patterns = [
        "Response", "Model", "BaseModel", "Pydantic", "Object", "Class",
        "Generator", "Iterator", "Callable", "AsyncGenerator", "Coroutine"
    ]
    
    for pattern in problematic_patterns:
        if pattern in return_type:
            return False, f"Potentially not JSON serializable: {return_type} (contains {pattern})"
    
    return False, f"Uncertain JSON serialization potential: {return_type}"

def analyze_function_with_llm(api_name: str, function_name: str, file_path: str, 
                            function_info: Dict, execution_result: Dict, thread_id: str = "") -> Dict[str, Any]:
    """Use LLM to analyze SDK function serialization issues for JSON file persistence."""
    
    prompt = f"""
    You are a code analyst specializing in SDK JSON serialization analysis for data persistence.
    
    CONTEXT: This is an SDK method that returns data which gets saved to JSON files. Any non-serializable objects will cause the JSON save operation to fail.
    
    API: {api_name}
    Function: {function_name}
    File: {file_path}
    
    FUNCTION SIGNATURE:
    {function_info['signature']}
    
    FUNCTION CODE:
    ```python
    {function_info['code']}
    ```
    
    EXECUTION RESULT:
    - Execution Status: {execution_result.get('execution_status', 'unknown')}
    - Is JSON Serializable: {execution_result.get('is_json_serializable', False)}
    - Serialization Notes: {execution_result.get('serialization_notes', '')}
    - Error Details: {execution_result.get('error_details', '')}
    - Return Type Analysis: {execution_result.get('return_type_analysis', '')}
    
    TASK: Analyze this SDK function to determine if it returns data that can be safely saved to JSON files. Focus on identifying objects that would break JSON serialization when the SDK tries to persist data.
    
    RESPONSE FORMAT:
    is_json_serializable: [true/false]
    has_custom_objects: [true/false]
    has_generators: [true/false]
    has_callables: [true/false]
    has_file_handles: [true/false]
    has_network_objects: [true/false]
    has_threading_objects: [true/false]
    requires_parameters: [true/false]
    execution_successful: [true/false]
    
    ANALYSIS_NOTES: [Detailed explanation of why this function would or wouldn't work for JSON file persistence]
    RECOMMENDATIONS: [Specific suggestions to make the function return JSON-serializable data for SDK persistence]
    """
    
    response = call_gemini_api_threadsafe(prompt, thread_id)
    
    # Parse the response
    result = {
        'api_name': api_name,
        'function_name': function_name,
        'file_path': file_path,
        'function_signature': function_info['signature'],
        'is_json_serializable': False,
        'has_custom_objects': False,
        'has_generators': False,
        'has_callables': False,
        'has_file_handles': False,
        'has_network_objects': False,
        'has_threading_objects': False,
        'requires_parameters': False,
        'execution_successful': False,
        'analysis_notes': response,
        'recommendations': 'Analysis failed',
        'execution_status': execution_result.get('execution_status', 'unknown'),
        'error_details': execution_result.get('error_details', ''),
        'return_type_analysis': execution_result.get('return_type_analysis', ''),
        'timestamp': datetime.now().isoformat()
    }
    
    # Parse boolean values from response
    for dimension in ANALYSIS_DIMENSIONS:
        pattern = fr'{dimension}:\s*\[?(true|false)\]?'
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            result[dimension] = match.group(1).lower() == 'true'
    
    # Extract analysis notes
    notes_match = re.search(r'ANALYSIS_NOTES:\s*(.+?)(?=RECOMMENDATIONS:|$)', response, re.DOTALL)
    if notes_match:
        result['analysis_notes'] = notes_match.group(1).strip()
    
    # Extract recommendations
    rec_match = re.search(r'RECOMMENDATIONS:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
    if rec_match:
        result['recommendations'] = rec_match.group(1).strip()
    
    return result 

def check_function_return_serialization(api_name: str, file_path: str, function_info: Dict) -> Dict[str, Any]:
    """Enhanced check if a function's return value is JSON serializable."""
    function_name = function_info['name']
    signature = function_info['signature']
    
    result = {
        'api_name': api_name,
        'file_path': file_path,
        'function_name': function_name,
        'function_signature': signature,
        'is_json_serializable': False,
        'serialization_notes': '',
        'execution_status': 'static_analysis',
        'error_details': '',
        'return_type_analysis': '',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Analyze return type annotation
        is_likely_serializable, annotation_analysis = analyze_return_type_annotation(signature)
        result['return_type_analysis'] = annotation_analysis
        
        # Check if function has parameters
        if "(" in signature and ")" in signature:
            params_part = signature[signature.find("(")+1:signature.rfind(")")]
            params = [p.strip() for p in params_part.split(",") if p.strip()]
            
            # Remove 'self' parameter if present
            if params and params[0] == "self":
                params = params[1:]
            
            # Check for required parameters
            required_params = []
            for param in params:
                if "=" not in param and param.strip():
                    required_params.append(param.split(":")[0].strip())
            
            if required_params:
                result['execution_status'] = 'requires_parameters'
                result['error_details'] = f"Function requires parameters: {required_params}"
                result['serialization_notes'] = f"Static analysis only - {annotation_analysis}"
                result['is_json_serializable'] = is_likely_serializable
                return result
        
        # For parameter-less functions, try dynamic analysis
        try:
            # Add the specific API directory to Python path
            api_dir_path = os.path.abspath(os.path.join(API_BASE_PATH, api_name))
            if api_dir_path not in sys.path:
                sys.path.insert(0, api_dir_path)
            
            # Import the module
            module_name = file_path.replace('/', '.').replace('.py', '')
            if '/' not in file_path:
                module_name = file_path.replace('.py', '')
            
            module = importlib.import_module(module_name)
            
            # Get the function
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                
                # Try to execute the function
                return_value = func()
                result['execution_status'] = 'executed_successfully'
                
                # Enhanced JSON serialization check
                is_serializable, serialization_message, detailed_analysis = is_json_serializable(return_value)
                result['is_json_serializable'] = is_serializable
                result['serialization_notes'] = serialization_message
                
                # Add detailed analysis to result
                for key, value in detailed_analysis.items():
                    result[key] = value
                
                # Detailed return type analysis
                if return_value is None:
                    result['return_type_analysis'] = "Returns None (JSON serializable)"
                else:
                    type_name = type(return_value).__name__
                    result['return_type_analysis'] = f"Returns {type_name}"
                    
                    if hasattr(return_value, '__dict__'):
                        result['return_type_analysis'] += " (custom object - may not be JSON serializable)"
                    elif isinstance(return_value, (dict, list, tuple)):
                        result['return_type_analysis'] += f" with {len(return_value)} items (likely JSON serializable)"
                        
            else:
                result['execution_status'] = 'function_not_found'
                result['error_details'] = f"Function {function_name} not found in module"
                result['serialization_notes'] = f"Static analysis only - {annotation_analysis}"
                result['is_json_serializable'] = is_likely_serializable
                
        except ImportError as e:
            result['execution_status'] = 'import_failed'
            result['error_details'] = f"Import error: {str(e)}"
            result['serialization_notes'] = f"Static analysis only - {annotation_analysis}"
            result['is_json_serializable'] = is_likely_serializable
            
        except Exception as e:
            result['execution_status'] = 'execution_failed'
            result['error_details'] = f"Execution error: {str(e)}"
            result['serialization_notes'] = f"Static analysis only - {annotation_analysis}"
            result['is_json_serializable'] = is_likely_serializable
            
    except Exception as e:
        result['execution_status'] = 'analysis_failed'
        result['error_details'] = f"Analysis error: {str(e)}"
        result['serialization_notes'] = "Could not analyze function"
        
    finally:
        # Clean up sys.path to avoid conflicts
        try:
            api_dir_path = os.path.abspath(os.path.join(API_BASE_PATH, api_name))
            if api_dir_path in sys.path:
                sys.path.remove(api_dir_path)
        except:
            pass  # Ignore cleanup errors
    
    return result

def process_api_functions(api_name: str, thread_id: str) -> List[Dict[str, Any]]:
    """Process all API functions for a single module with LLM analysis."""
    print(f"🔍 Thread {thread_id}: Processing API module: {api_name}")
    
    try:
        # Add the project root to Python path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        functions_by_file = get_api_functions(api_name)
        results = []
        
        if not functions_by_file:
            print(f"⚠️  Thread {thread_id}: No functions found for API {api_name}")
            return results
        
        total_functions = sum(len(funcs) for funcs in functions_by_file.values())
        processed_functions = 0
        
        for file_path, functions in functions_by_file.items():
            for function_info in functions:
                try:
                    # First, do basic execution analysis
                    execution_result = check_function_return_serialization(api_name, file_path, function_info)
                    
                    # Then, use LLM for enhanced analysis
                    llm_result = analyze_function_with_llm(api_name, function_info['name'], file_path, 
                                                         function_info, execution_result, thread_id)
                    
                    # Merge results
                    final_result = {**execution_result, **llm_result}
                    
                    results.append(final_result)
                    
                    # Save result incrementally
                    save_result_incrementally(final_result)
                    
                    processed_functions += 1
                    if processed_functions % 5 == 0:  # Progress update every 5 functions
                        progress = (processed_functions / total_functions) * 100
                        print(f"   Thread {thread_id}: {api_name} - {processed_functions}/{total_functions} ({progress:.1f}%)")
                        
                except Exception as e:
                    print(f"❌ Thread {thread_id}: Error processing {api_name}/{function_info['name']}: {e}")
                    # Create error result
                    error_result = {
                        'api_name': api_name,
                        'file_path': file_path,
                        'function_name': function_info['name'],
                        'function_signature': function_info['signature'],
                        'is_json_serializable': False,
                        'execution_status': 'processing_error',
                        'error_details': str(e),
                        'analysis_notes': f"Error during processing: {str(e)}",
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(error_result)
                    save_result_incrementally(error_result)
        
        print(f"✅ Thread {thread_id}: Completed API {api_name} - {processed_functions} API functions")
        return results
        
    except Exception as e:
        print(f"❌ Thread {thread_id}: Error processing API {api_name}: {e}")
        return []

def save_result_incrementally(result: Dict[str, Any], create_header: bool = False):
    """Save a single result to CSV immediately (incremental saving)."""
    
    csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
    
    # Define CSV headers
    headers = [
        'api_name',
        'function_name', 
        'file_path',
        'function_signature',
        'is_json_serializable',
        'has_custom_objects',
        'has_generators',
        'has_callables',
        'has_file_handles',
        'has_network_objects',
        'has_threading_objects',
        'requires_parameters',
        'execution_successful',
        'execution_status',
        'error_details',
        'return_type_analysis',
        'serialization_notes',
        'analysis_notes',
        'recommendations',
        'timestamp'
    ]
    
    # Use a lock to ensure thread-safe writing
    global csv_write_lock
    if 'csv_write_lock' not in globals():
        csv_write_lock = threading.Lock()
    
    with csv_write_lock:
        # Check if we need to create the file with header
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # Write header if file is new or explicitly requested
            if not file_exists or create_header:
                writer.writeheader()
            
            # Write the result
            writer.writerow(result)
    
    print(f"💾 Saved result: {result['api_name']}/{result['function_name']}")

def initialize_incremental_csv():
    """Initialize the CSV file with headers for incremental saving."""
    
    csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
    
    # Define CSV headers
    headers = [
        'api_name',
        'function_name', 
        'file_path',
        'function_signature',
        'is_json_serializable',
        'has_custom_objects',
        'has_generators',
        'has_callables',
        'has_file_handles',
        'has_network_objects',
        'has_threading_objects',
        'requires_parameters',
        'execution_successful',
        'execution_status',
        'error_details',
        'return_type_analysis',
        'serialization_notes',
        'analysis_notes',
        'recommendations',
        'timestamp'
    ]
    
    # Create fresh CSV file with headers
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
    
    print(f"📄 Initialized incremental CSV: {csv_path}")

def identify_incomplete_entries(csv_file_path: str) -> Dict[str, Dict[str, List[str]]]:
    """Identify incomplete entries in the CSV file."""
    incomplete_entries = {}
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                api_name = row['api_name']
                function_name = row['function_name']
                
                if api_name not in incomplete_entries:
                    incomplete_entries[api_name] = {
                        'complete': [],
                        'incomplete': [],
                        'error': []
                    }
                
                # Check if entry is complete
                if row.get('analysis_notes', '').strip() and row.get('recommendations', '').strip():
                    incomplete_entries[api_name]['complete'].append(function_name)
                elif row.get('execution_status') in ['processing_error', 'analysis_failed']:
                    incomplete_entries[api_name]['error'].append(function_name)
                else:
                    incomplete_entries[api_name]['incomplete'].append(function_name)
                    
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
    
    return incomplete_entries

def load_existing_results(csv_file_path: str) -> Dict[str, Dict]:
    """Load existing results from CSV file."""
    existing_results = {}
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['api_name']}:{row['function_name']}"
                existing_results[key] = row
                    
    except Exception as e:
        print(f"❌ Error loading existing results: {e}")
    
    return existing_results 

def run_improved_json_serialization_check():
    """Run the improved JSON serialization check for API functions analysis."""
    print("🚀 Starting API Functions JSON Serialization Analysis...")
    print("=" * 60)
    
    # Initialize Gemini client
    if not configure_gemini_client():
        print("❌ Failed to configure Gemini client. Exiting.")
        return False
    
    # Ensure output directory exists
    ensure_output_directory()
    
    # Initialize CSV file
    initialize_incremental_csv()
    
    # Get API directories
    api_dirs = get_api_directories()
    if not api_dirs:
        print("❌ No API directories found. Exiting.")
        return False
    
    print(f"📋 Processing {len(api_dirs)} API modules with {MAX_THREADS} threads")
    print(f"⏱️  Timeout per module: {TIMEOUT_SECONDS} seconds")
    print(f"🤖 Using LLM model: {MODEL_NAME}")
    print()
    
    # Process APIs in parallel
    all_results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit all API processing tasks
        future_to_api = {
            executor.submit(process_api_functions, api_name, f"T{i+1}"): api_name 
            for i, api_name in enumerate(api_dirs)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_api):
            api_name = future_to_api[future]
            try:
                results = future.result(timeout=TIMEOUT_SECONDS)
                all_results.extend(results)
                print(f"✅ Completed API module: {api_name} ({len(results)} functions)")
            except Exception as e:
                print(f"❌ Error processing SDK module {api_name}: {e}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n🎉 API serialization analysis completed in {total_time:.2f} seconds")
    print(f"📊 Total API functions analyzed: {len(all_results)}")
    
    # Generate summary report
    generate_summary_report(all_results)
    
    return True

def run_improved_json_serialization_check_with_resume(resume_mode: bool = False):
    """Run the improved JSON serialization check with resume capability."""
    print("🔄 Starting Resume Analysis..." if resume_mode else "🚀 Starting Improved JSON Serialization Check...")
    print("=" * 60)
    
    # Initialize Gemini client
    if not configure_gemini_client():
        print("❌ Failed to configure Gemini client. Exiting.")
        return False
    
    # Ensure output directory exists
    ensure_output_directory()
    
    csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
    
    if resume_mode:
        # Check if CSV file exists
        if not os.path.exists(csv_path):
            print(f"❌ No existing CSV file found at {csv_path}")
            print("   Please run a full analysis first")
            return False
        
        # Identify incomplete entries
        incomplete_entries = identify_incomplete_entries(csv_path)
        if not incomplete_entries:
            print("✅ No incomplete entries found")
            return True
        
        # Load existing results
        existing_results = load_existing_results(csv_path)
        
        # Calculate what needs to be processed
        total_incomplete = sum(
            len(funcs) for api_data in incomplete_entries.values() 
            for status, funcs in api_data.items() if status != 'complete' and funcs
        )
        
        if total_incomplete == 0:
            print("✅ All entries are complete!")
            return True
        
        print(f"📋 Found {total_incomplete} incomplete entries to process")
        
        # Get API directories
        api_dirs = get_api_directories()
        if not api_dirs:
            print("❌ No API directories found. Exiting.")
            return False
        
        # Process only APIs with incomplete entries
        apis_to_process = [api for api in api_dirs if api in incomplete_entries]
        
        print(f"📋 Processing {len(apis_to_process)} APIs with incomplete entries")
        print(f"⏱️  Timeout per API: {TIMEOUT_SECONDS} seconds")
        print(f"🤖 Using LLM model: {MODEL_NAME}")
        print()
        
        # Process APIs in parallel
        all_results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit API processing tasks
            future_to_api = {
                executor.submit(process_api_functions_with_resume, api_name, existing_results, f"T{i+1}"): api_name 
                for i, api_name in enumerate(apis_to_process)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_api):
                api_name = future_to_api[future]
                try:
                    results = future.result(timeout=TIMEOUT_SECONDS)
                    all_results.extend(results)
                    print(f"✅ Completed API: {api_name} ({len(results)} functions)")
                except Exception as e:
                    print(f"❌ Error processing API {api_name}: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n🎉 Resume analysis completed in {total_time:.2f} seconds")
        print(f"📊 Total functions processed: {len(all_results)}")
        
    else:
        # Initialize CSV file
        initialize_incremental_csv()
        
        # Get API directories
        api_dirs = get_api_directories()
        if not api_dirs:
            print("❌ No API directories found. Exiting.")
            return False
        
        print(f"📋 Processing {len(api_dirs)} APIs with {MAX_THREADS} threads")
        print(f"⏱️  Timeout per API: {TIMEOUT_SECONDS} seconds")
        print(f"🤖 Using LLM model: {MODEL_NAME}")
        print()
        
        # Process APIs in parallel
        all_results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit all API processing tasks
            future_to_api = {
                executor.submit(process_api_functions, api_name, f"T{i+1}"): api_name 
                for i, api_name in enumerate(api_dirs)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_api):
                api_name = future_to_api[future]
                try:
                    results = future.result(timeout=TIMEOUT_SECONDS)
                    all_results.extend(results)
                    print(f"✅ Completed API: {api_name} ({len(results)} functions)")
                except Exception as e:
                    print(f"❌ Error processing API {api_name}: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n🎉 Analysis completed in {total_time:.2f} seconds")
        print(f"📊 Total functions analyzed: {len(all_results)}")
    
    # Generate summary report
    generate_summary_report(all_results)
    
    return True

def process_api_functions_with_resume(api_name: str, existing_results: Dict[str, Dict], thread_id: str) -> List[Dict[str, Any]]:
    """Process API functions with resume capability."""
    print(f"🔍 Thread {thread_id}: Processing API: {api_name} (resume mode)")
    
    try:
        # Add the project root to Python path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        functions_by_file = get_api_functions(api_name)
        results = []
        
        if not functions_by_file:
            print(f"⚠️  Thread {thread_id}: No functions found for API {api_name}")
            return results
        
        total_functions = sum(len(funcs) for funcs in functions_by_file.values())
        processed_functions = 0
        skipped_functions = 0
        
        for file_path, functions in functions_by_file.items():
            for function_info in functions:
                function_key = f"{api_name}:{function_info['name']}"
                
                # Check if this function already has complete analysis
                if function_key in existing_results:
                    existing_result = existing_results[function_key]
                    if (existing_result.get('analysis_notes', '').strip() and 
                        existing_result.get('recommendations', '').strip()):
                        skipped_functions += 1
                        continue
                
                try:
                    # First, do basic execution analysis
                    execution_result = check_function_return_serialization(api_name, file_path, function_info)
                    
                    # Then, use LLM for enhanced analysis
                    llm_result = analyze_function_with_llm(api_name, function_info['name'], file_path, 
                                                         function_info, execution_result, thread_id)
                    
                    # Merge results
                    final_result = {**execution_result, **llm_result}
                    
                    results.append(final_result)
                    
                    # Save result incrementally
                    save_result_incrementally(final_result)
                    
                    processed_functions += 1
                    if processed_functions % 5 == 0:  # Progress update every 5 functions
                        progress = (processed_functions / total_functions) * 100
                        print(f"   Thread {thread_id}: {api_name} - {processed_functions}/{total_functions} ({progress:.1f}%)")
                        
                except Exception as e:
                    print(f"❌ Thread {thread_id}: Error processing {api_name}/{function_info['name']}: {e}")
                    # Create error result
                    error_result = {
                        'api_name': api_name,
                        'file_path': file_path,
                        'function_name': function_info['name'],
                        'function_signature': function_info['signature'],
                        'is_json_serializable': False,
                        'execution_status': 'processing_error',
                        'error_details': str(e),
                        'analysis_notes': f"Error during processing: {str(e)}",
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(error_result)
                    save_result_incrementally(error_result)
        
        print(f"✅ Thread {thread_id}: Completed API {api_name} - {processed_functions} processed, {skipped_functions} skipped")
        return results
        
    except Exception as e:
        print(f"❌ Thread {thread_id}: Error processing API {api_name}: {e}")
        return []

def generate_summary_report(results: List[Dict[str, Any]]):
    """Generate comprehensive summary report for SDK JSON persistence analysis."""
    print("📊 Generating summary report...")
    
    summary_path = os.path.join(OUTPUT_DIR, SUMMARY_OUTPUT_FILE)
    
    # Calculate statistics
    total_functions = len(results)
    serializable_functions = sum(1 for r in results if r.get('is_json_serializable', False))
    non_serializable_functions = total_functions - serializable_functions
    
    # Execution status breakdown
    execution_stats = {}
    for result in results:
        status = result.get('execution_status', 'unknown')
        execution_stats[status] = execution_stats.get(status, 0) + 1
    
    # Issue type breakdown
    issue_stats = {
        'has_custom_objects': sum(1 for r in results if r.get('has_custom_objects', False)),
        'has_generators': sum(1 for r in results if r.get('has_generators', False)),
        'has_callables': sum(1 for r in results if r.get('has_callables', False)),
        'has_file_handles': sum(1 for r in results if r.get('has_file_handles', False)),
        'has_network_objects': sum(1 for r in results if r.get('has_network_objects', False)),
        'has_threading_objects': sum(1 for r in results if r.get('has_threading_objects', False)),
        'requires_parameters': sum(1 for r in results if r.get('requires_parameters', False))
    }
    
    # API breakdown
    api_stats = {}
    for result in results:
        api_name = result['api_name']
        if api_name not in api_stats:
            api_stats[api_name] = {'total': 0, 'serializable': 0, 'non_serializable': 0}
        api_stats[api_name]['total'] += 1
        if result.get('is_json_serializable', False):
            api_stats[api_name]['serializable'] += 1
        else:
            api_stats[api_name]['non_serializable'] += 1
    
    # Generate markdown report
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# SDK JSON Persistence Analysis Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model Used**: {MODEL_NAME}\n")
        f.write(f"**Purpose**: Analysis of SDK methods for JSON file persistence compatibility\n\n")
        
        # Summary statistics
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total SDK Methods Analyzed**: {total_functions}\n")
        f.write(f"- **Safe for JSON Persistence**: {serializable_functions} ({serializable_functions/total_functions*100:.1f}%)\n")
        f.write(f"- **Will Break JSON Persistence**: {non_serializable_functions} ({non_serializable_functions/total_functions*100:.1f}%)\n")
        f.write(f"- **SDK Modules Analyzed**: {len(api_stats)}\n\n")
        
        # Execution status breakdown
        f.write("## Execution Status Breakdown\n\n")
        for status, count in sorted(execution_stats.items()):
            percentage = (count / total_functions) * 100
            f.write(f"- **{status.replace('_', ' ').title()}**: {count} ({percentage:.1f}%)\n")
        f.write("\n")
        
        # Issue type breakdown
        f.write("## Issue Type Breakdown\n\n")
        for issue_type, count in sorted(issue_stats.items()):
            if count > 0:
                percentage = (count / total_functions) * 100
                f.write(f"- **{issue_type.replace('_', ' ').title()}**: {count} ({percentage:.1f}%)\n")
        f.write("\n")
        
        # API breakdown
        f.write("## API Breakdown\n\n")
        f.write("| API | Total | Serializable | Non-Serializable | % Serializable |\n")
        f.write("|-----|-------|--------------|------------------|----------------|\n")
        
        for api_name, stats in sorted(api_stats.items()):
            serializable_pct = (stats['serializable'] / stats['total']) * 100
            f.write(f"| {api_name} | {stats['total']} | {stats['serializable']} | {stats['non_serializable']} | {serializable_pct:.1f}% |\n")
        
        f.write("\n")
        
        # Problematic SDK modules (less than 100% serializable)
        problematic_apis = []
        for api_name, stats in api_stats.items():
            serializable_pct = (stats['serializable'] / stats['total']) * 100
            if serializable_pct < 100:
                problematic_apis.append((api_name, stats['non_serializable'], serializable_pct))
        
        if problematic_apis:
            f.write("## SDK Modules Requiring Attention\n\n")
            f.write("The following SDK modules have methods that will break JSON file persistence:\n\n")
            f.write("| SDK Module | Methods Breaking JSON Persistence | % Safe |\n")
            f.write("|------------|-----------------------------------|---------|\n")
            
            problematic_apis.sort(key=lambda x: x[1], reverse=True)  # Sort by number of issues
            for api_name, issues, pct in problematic_apis:
                f.write(f"| {api_name} | {issues} | {pct:.1f}% |\n")
            
            f.write("\n")
        
        # Sample problematic SDK methods
        non_serializable_functions = [r for r in results if not r.get('is_json_serializable', False)]
        if non_serializable_functions:
            f.write("## Sample SDK Methods Breaking JSON Persistence\n\n")
            f.write("Here are some examples of SDK methods that will cause JSON save operations to fail:\n\n")
            
            for i, result in enumerate(non_serializable_functions[:10]):  # Show first 10
                f.write(f"### {i+1}. {result['api_name']}/{result['function_name']}\n\n")
                f.write(f"**File**: {result['file_path']}\n\n")
                f.write(f"**Signature**: `{result['function_signature']}`\n\n")
                f.write(f"**Status**: {result.get('execution_status', 'unknown')}\n\n")
                f.write(f"**JSON Persistence Issue**: {result.get('serialization_notes', 'Unknown')}\n\n")
                
                if result.get('analysis_notes'):
                    f.write(f"**Analysis**: {result['analysis_notes']}\n\n")
                
                if result.get('recommendations'):
                    f.write(f"**Recommendations**: {result['recommendations']}\n\n")
                
                f.write("---\n\n")
    
    print(f"📄 Summary report generated: {summary_path}")

def print_summary_statistics(results: List[Dict[str, Any]]):
    """Print summary statistics to console."""
    total_functions = len(results)
    serializable_functions = sum(1 for r in results if r.get('is_json_serializable', False))
    non_serializable_functions = total_functions - serializable_functions
    
    print(f"\n📊 Summary Statistics:")
    print(f"   Total Functions: {total_functions}")
    print(f"   JSON Serializable: {serializable_functions} ({serializable_functions/total_functions*100:.1f}%)")
    print(f"   Non-Serializable: {non_serializable_functions} ({non_serializable_functions/total_functions*100:.1f}%)")
    
    # Execution status breakdown
    execution_stats = {}
    for result in results:
        status = result.get('execution_status', 'unknown')
        execution_stats[status] = execution_stats.get(status, 0) + 1
    
    print(f"\n📋 Execution Status:")
    for status, count in sorted(execution_stats.items()):
        percentage = (count / total_functions) * 100
        print(f"   {status.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")