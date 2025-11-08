# -*- coding: utf-8 -*-
"""API Version Comparison Script

Compares API functions between version 0.0.1 and 0.0.8 across multiple dimensions.
Generates CSV results and textual changelog.

Usage:
    python api_version_comparison.py
"""

import os
import time
import json
import ast
import csv
import traceback
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re
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
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Gemini Configuration (loaded from environment variables)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")
API_CALL_DELAY = int(os.getenv("API_CALL_DELAY", "6"))  # Reduced for faster processing

# Version paths (relative to current directory)
VERSION_0_0_1_PATH = "APIs_V0.0.1/APIs"
VERSION_0_0_8_PATH = "APIs_V0.0.8/APIs"

# Output configuration
OUTPUT_DIR = "comparison_results"
CSV_OUTPUT_FILE = "api_version_comparison.csv"
CHANGELOG_OUTPUT_FILE = "api_version_changelog.md"

# Threading configuration
MAX_FUNCTION_THREADS = int(os.getenv("MAX_FUNCTION_THREADS", "10"))  # Parallel function processing
MAX_ANALYSIS_THREADS = int(os.getenv("MAX_ANALYSIS_THREADS", "10"))  # Parallel dimension analysis per function

# APIs to compare (leave empty to compare all APIs found)
TARGET_APIS = []

# Analysis dimensions
COMPARISON_DIMENSIONS = [
    'new_function',
    'function_input_validation_implementation', 
    'function_inputs_changes',
    'function_input_signature_change',
    'function_output_signature_change', 
    'function_implementation_logic_change',
    'other_changes'
]

# Global variables
gemini_client = None
api_call_lock = threading.Lock()
csv_write_lock = threading.Lock()  # Lock for thread-safe CSV writing
last_api_call_time = 0
comparison_results = []
changelog_entries = []

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
                    return f"Error: Response stopped with reason: {finish_reason}"
            
            return "Error: No candidates found in response."
            
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1 and ('connection' in error_msg.lower() or 'timeout' in error_msg.lower()):
                wait_time = (attempt + 1) * 2
                print(f"   🔄 Thread {thread_id}: Retrying in {wait_time}s after error: {error_msg}")
                time.sleep(wait_time)
                continue
            else:
                return f"Gemini API Error in thread {thread_id}: {error_msg}"
    
    return f"Max retries exceeded in thread {thread_id}"

# =============================================================================
# FILE PARSING AND EXTRACTION
# =============================================================================

def extract_functions_from_file(file_path: str) -> List[Dict]:
    """Extract all function definitions from a Python file."""
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else find_function_end(lines, start_line)
                
                # Extract function code
                function_code = '\n'.join(lines[start_line:end_line])
                
                # Extract function signature
                signature = get_function_signature(node)
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                functions.append({
                    'name': node.name,
                    'signature': signature,
                    'code': function_code,
                    'docstring': docstring or "",
                    'start_line': start_line + 1,
                    'end_line': end_line,
                    'file_path': file_path
                })
                
    except Exception as e:
        print(f"⚠️ Error parsing file {file_path}: {e}")
    
    return functions

def get_function_signature(node: ast.FunctionDef) -> str:
    """Extract function signature from AST node."""
    try:
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(vararg_str)
        
        # **kwargs
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(kwarg_str)
        
        # Return type annotation
        return_annotation = ""
        if node.returns:
            return_annotation = f" -> {ast.unparse(node.returns)}"
        
        return f"{node.name}({', '.join(args)}){return_annotation}"
        
    except Exception as e:
        return f"{node.name}(...)"

def find_function_end(lines: List[str], start_line: int) -> int:
    """Find the end line of a function by analyzing indentation."""
    if start_line >= len(lines):
        return start_line + 1
    
    func_line = lines[start_line]
    base_indent = len(func_line) - len(func_line.lstrip())
    
    end_line = start_line + 1
    while end_line < len(lines):
        line = lines[end_line]
        
        if line.strip() == "":
            end_line += 1
            continue
        
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= base_indent:
            break
        
        end_line += 1
    
    return end_line

def scan_api_versions(version_path: str) -> Dict[str, Dict[str, List[Dict]]]:
    """Scan API version directory and extract all functions."""
    print(f"📁 Scanning API version: {version_path}")
    
    if not os.path.exists(version_path):
        print(f"❌ Version path not found: {version_path}")
        return {}
    
    api_functions = {}
    
    # Get all API directories
    for api_dir in os.listdir(version_path):
        api_path = os.path.join(version_path, api_dir)
        
        if not os.path.isdir(api_path):
            continue
        
        # Skip if we have specific target APIs and this isn't one of them
        if TARGET_APIS and api_dir not in TARGET_APIS:
            continue
        
        print(f"   📋 Processing API: {api_dir}")
        
        api_functions[api_dir] = {}
        
        # Scan all Python files in the API directory (excluding SimulationEngine and tests)
        for root, dirs, files in os.walk(api_path):
            # Skip SimulationEngine and tests directories
            dirs[:] = [d for d in dirs if d not in ['SimulationEngine', 'tests', '__pycache__']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, api_path)
                    
                    functions = extract_functions_from_file(file_path)
                    
                    if functions:
                        api_functions[api_dir][relative_path] = functions
                        print(f"      📝 Found {len(functions)} functions in {relative_path}")
    
    total_apis = len(api_functions)
    total_files = sum(len(files) for files in api_functions.values())
    total_functions = sum(len(funcs) for files in api_functions.values() for funcs in files.values())
    
    print(f"📊 Scan complete: {total_apis} APIs, {total_files} files, {total_functions} functions")
    
    return api_functions

# =============================================================================
# COMPARISON ANALYSIS
# =============================================================================

def analyze_function_comparison(api_name: str, function_name: str, file_path: str,
                               old_function: Optional[Dict], new_function: Dict,
                               thread_id: str = "main", save_incrementally: bool = True) -> Dict:
    """Analyze comparison between two function versions using Gemini."""
    
    # If old_function is None, this is a new function
    if old_function is None:
        return {
            'api_name': api_name,
            'function_name': function_name,
            'file_path': file_path,
            'new_function': True,
            'function_input_validation_implementation': False,
            'function_inputs_changes': False,
            'function_input_signature_change': False,
            'function_output_signature_change': False,
            'function_implementation_logic_change': False,
            'other_changes': False,
            'analysis_notes': 'New function - not present in v0.0.1',
            'changelog_summary': f"NEW: Added function {function_name} in {file_path}"
        }
    
    # Prepare the comparison prompt
    prompt = f"""
    You are a code analyst comparing two versions of the same function to identify changes.
    
    API: {api_name}
    Function: {function_name}
    File: {file_path}
    
    VERSION 0.0.1 (OLD):
    Signature: {old_function['signature']}
    Code:
    ```python
    {old_function['code']}
    ```
    
    VERSION 0.0.8 (NEW):
    Signature: {new_function['signature']}
    Code:
    ```python
    {new_function['code']}
    ```
    
    TASK: Analyze the differences between these two versions and provide a boolean assessment for each dimension:
    
    1. **function_input_validation_implementation**: Has input validation been added, removed, or significantly changed?
    2. **function_inputs_changes**: Have the input parameters changed (added, removed, or modified)?
    3. **function_input_signature_change**: Has the function signature changed (parameter names, types, defaults)?
    4. **function_output_signature_change**: Has the return type or structure changed?
    5. **function_implementation_logic_change**: Has the core implementation logic changed?
    6. **other_changes**: Are there any other significant changes (docstring, comments, etc.)?
    
    RESPONSE FORMAT:
    function_input_validation_implementation: [true/false]
    function_inputs_changes: [true/false]
    function_input_signature_change: [true/false]
    function_output_signature_change: [true/false]
    function_implementation_logic_change: [true/false]
    other_changes: [true/false]
    
    ANALYSIS_NOTES: [Detailed explanation of the changes found]
    CHANGELOG_SUMMARY: [Brief summary suitable for changelog]
    """
    
    response = call_gemini_api_threadsafe(prompt, thread_id)
    
    # Parse the response
    result = {
        'api_name': api_name,
        'function_name': function_name,
        'file_path': file_path,
        'new_function': False,
        'function_input_validation_implementation': False,
        'function_inputs_changes': False,
        'function_input_signature_change': False,
        'function_output_signature_change': False,
        'function_implementation_logic_change': False,
        'other_changes': False,
        'analysis_notes': response,
        'changelog_summary': 'Analysis failed'
    }
    
    # Parse boolean values from response
    for dimension in COMPARISON_DIMENSIONS[1:]:  # Skip 'new_function' as it's always false here
        pattern = fr'{dimension}:\s*\[?(true|false)\]?'
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            result[dimension] = match.group(1).lower() == 'true'
    
    # Extract analysis notes
    notes_match = re.search(r'ANALYSIS_NOTES:\s*(.+?)(?=CHANGELOG_SUMMARY:|$)', response, re.DOTALL)
    if notes_match:
        result['analysis_notes'] = notes_match.group(1).strip()
    
    # Extract changelog summary
    changelog_match = re.search(r'CHANGELOG_SUMMARY:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
    if changelog_match:
        result['changelog_summary'] = changelog_match.group(1).strip()
    
    # Save result incrementally if enabled
    if save_incrementally:
        save_result_incrementally(result)
    
    return result

def compare_function_versions(api_name: str, old_functions: Dict[str, List[Dict]], 
                            new_functions: Dict[str, List[Dict]], thread_id: str = "main",
                            functions_filter: Set[str] = None, existing_results: Dict[str, Dict] = None) -> List[Dict]:
    """Compare functions between two versions for a single API."""
    
    print(f"   🔄 Thread {thread_id}: Comparing {api_name}")
    
    results = []
    
    # Create lookup dictionaries for faster access
    old_func_lookup = {}
    for file_path, funcs in old_functions.items():
        for func in funcs:
            old_func_lookup[f"{file_path}:{func['name']}"] = func
    
    new_func_lookup = {}
    for file_path, funcs in new_functions.items():
        for func in funcs:
            new_func_lookup[f"{file_path}:{func['name']}"] = func
    
    # Process all functions in new version
    for file_path, funcs in new_functions.items():
        for func in funcs:
            func_key = f"{file_path}:{func['name']}"
            
            # Apply function filter if provided
            if functions_filter is not None and func['name'] not in functions_filter:
                # If there's an existing result for this function, use it
                if existing_results:
                    existing_key = f"{api_name}|{func['name']}"
                    if existing_key in existing_results:
                        results.append(existing_results[existing_key])
                continue
            
            old_func = old_func_lookup.get(func_key)
            
            # Analyze the function comparison
            result = analyze_function_comparison(
                api_name, func['name'], file_path, old_func, func, f"{thread_id}-{func['name'][:10]}", save_incrementally=True
            )
            
            results.append(result)
            
            # Log progress
            if old_func is None:
                print(f"      ✨ New function: {func['name']} in {file_path}")
            elif any(result[dim] for dim in COMPARISON_DIMENSIONS[1:]):
                print(f"      🔄 Changed function: {func['name']} in {file_path}")
            else:
                print(f"      ✅ Unchanged function: {func['name']} in {file_path}")
    
    print(f"   ✅ Thread {thread_id}: Completed {api_name} - {len(results)} functions analyzed")
    
    return results

# =============================================================================
# MAIN COMPARISON PIPELINE
# =============================================================================

def identify_incomplete_entries(csv_file_path: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Analyze existing CSV file to identify entries that need re-analysis.
    
    Returns:
        Dict[api_name][status] = [function_names]
        where status is: 'missing_analysis', 'error_analysis', 'timeout_analysis'
    """
    if not os.path.exists(csv_file_path):
        print(f"📄 No existing CSV file found at {csv_file_path}")
        return {}
    
    print(f"🔍 Analyzing existing CSV file: {csv_file_path}")
    
    incomplete_entries = {}
    total_entries = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_entries += 1
                api_name = row.get('api_name', '')
                function_name = row.get('function_name', '')
                analysis_notes = row.get('analysis_notes', '').strip()
                new_function = row.get('new_function', '').lower() == 'true'
                
                if not api_name or not function_name:
                    continue
                    
                # Initialize API entry if not exists
                if api_name not in incomplete_entries:
                    incomplete_entries[api_name] = {
                        'missing_analysis': [],
                        'error_analysis': [],
                        'timeout_analysis': [],
                        'complete': []
                    }
                
                # Check if analysis is incomplete
                needs_reanalysis = False
                reason = 'complete'
                
                if new_function:
                    # For new functions, simple message is expected
                    if not analysis_notes or analysis_notes == '':
                        needs_reanalysis = True
                        reason = 'missing_analysis'
                    elif any(pattern in analysis_notes.lower() for pattern in [
                        'api key not found', 'api key invalid', 'authentication failed',
                        'gemini api error', 'connection error', 'timeout', 'failed after',
                        'max retries exceeded', 'error in thread'
                    ]):
                        needs_reanalysis = True
                        reason = 'error_analysis'
                else:
                    # For existing functions, detailed analysis is expected
                    if not analysis_notes or len(analysis_notes.strip()) < 50:
                        needs_reanalysis = True
                        reason = 'missing_analysis'
                    elif any(pattern in analysis_notes.lower() for pattern in [
                        'api key not found', 'api key invalid', 'authentication failed',
                        'gemini api error', 'connection error', 'timeout', 'failed after',
                        'max retries exceeded', 'error in thread'
                    ]):
                        needs_reanalysis = True
                        reason = 'error_analysis'
                    elif 'timeout' in analysis_notes.lower():
                        needs_reanalysis = True
                        reason = 'timeout_analysis'
                
                incomplete_entries[api_name][reason].append(function_name)
        
        # Print summary
        print(f"📊 Analysis Summary:")
        print(f"   Total entries analyzed: {total_entries}")
        
        total_incomplete = 0
        for api_name, statuses in incomplete_entries.items():
            api_incomplete = sum(len(funcs) for status, funcs in statuses.items() if status != 'complete')
            if api_incomplete > 0:
                total_incomplete += api_incomplete
                print(f"   {api_name}: {api_incomplete} entries need re-analysis")
                for status, funcs in statuses.items():
                    if funcs and status != 'complete':
                        print(f"      {status}: {len(funcs)} functions")
        
        if total_incomplete == 0:
            print("   ✅ All entries are complete!")
        else:
            print(f"   🔄 Total entries needing re-analysis: {total_incomplete}")
            
    except Exception as e:
        print(f"❌ Error analyzing CSV file: {e}")
        return {}
    
    return incomplete_entries

def load_existing_results(csv_file_path: str) -> Dict[str, Dict]:
    """
    Load existing results from CSV file.
    
    Returns:
        Dict[api_name|function_name] = row_data_dict
    """
    existing_results = {}
    
    if not os.path.exists(csv_file_path):
        return existing_results
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                api_name = row.get('api_name', '')
                function_name = row.get('function_name', '')
                if api_name and function_name:
                    key = f"{api_name}|{function_name}"
                    existing_results[key] = row
        
        print(f"📥 Loaded {len(existing_results)} existing results from CSV")
        
    except Exception as e:
        print(f"⚠️ Error loading existing results: {e}")
    
    return existing_results

def run_version_comparison():
    """Main function to run the complete version comparison."""
    
    print("🚀 Starting API Version Comparison")
    print("=" * 80)
    print(f"📊 Comparing {VERSION_0_0_1_PATH} vs {VERSION_0_0_8_PATH}")
    print(f"🧵 Using {MAX_FUNCTION_THREADS} parallel threads")
    
    # Initialize Gemini client
    if not configure_gemini_client():
        print("❌ Failed to initialize Gemini client")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize incremental CSV file for immediate saving
    initialize_incremental_csv()
    
    # Scan both versions
    print("\n📁 Scanning API versions...")
    old_version_functions = scan_api_versions(VERSION_0_0_1_PATH)
    new_version_functions = scan_api_versions(VERSION_0_0_8_PATH)
    
    if not old_version_functions or not new_version_functions:
        print("❌ Failed to scan one or both versions")
        return
    
    # Find common APIs
    common_apis = set(old_version_functions.keys()) & set(new_version_functions.keys())
    new_apis = set(new_version_functions.keys()) - set(old_version_functions.keys())
    
    print(f"\n📊 Found {len(common_apis)} common APIs and {len(new_apis)} new APIs")
    
    # Process APIs in parallel
    print(f"\n🚀 Starting parallel comparison for {len(common_apis)} APIs...")
    
    all_results = []
    
    with ThreadPoolExecutor(max_workers=MAX_FUNCTION_THREADS, thread_name_prefix="API") as executor:
        # Submit comparison tasks
        future_to_api = {}
        for i, api_name in enumerate(common_apis):
            thread_id = f"API-{i+1}"
            future = executor.submit(
                compare_function_versions, 
                api_name, 
                old_version_functions[api_name], 
                new_version_functions[api_name], 
                thread_id
            )
            future_to_api[future] = api_name
        
        # Collect results
        completed_apis = 0
        for future in as_completed(future_to_api):
            api_name = future_to_api[future]
            try:
                api_results = future.result()
                all_results.extend(api_results)
                completed_apis += 1
                progress = (completed_apis / len(common_apis)) * 100
                print(f"🎯 Progress: {completed_apis}/{len(common_apis)} ({progress:.1f}%) - {api_name} completed")
            except Exception as e:
                print(f"❌ Error processing {api_name}: {e}")
    
    # Handle new APIs (all functions are new)
    if new_apis:
        print(f"\n✨ Processing {len(new_apis)} new APIs...")
        for api_name in new_apis:
            for file_path, funcs in new_version_functions[api_name].items():
                for func in funcs:
                    result = {
                        'api_name': api_name,
                        'function_name': func['name'],
                        'file_path': file_path,
                        'new_function': True,
                        'function_input_validation_implementation': False,
                        'function_inputs_changes': False,
                        'function_input_signature_change': False,
                        'function_output_signature_change': False,
                        'function_implementation_logic_change': False,
                        'other_changes': False,
                        'analysis_notes': f'New API - {api_name} was added in v0.0.8',
                        'changelog_summary': f"NEW API: Added {api_name} with function {func['name']}"
                    }
                    # Save result incrementally
                    save_result_incrementally(result)
                    all_results.append(result)
    
    # Generate outputs
    print(f"\n📄 Generating outputs...")
    generate_csv_output(all_results)
    generate_changelog_output(all_results)
    
    # Summary statistics
    print_summary_statistics(all_results)
    
    print(f"\n🎉 Comparison completed successfully!")
    print(f"📊 Results saved to: {OUTPUT_DIR}/")

def run_version_comparison_with_resume(resume_mode: bool = False):
    """Enhanced version comparison with resume capability."""
    
    print("🚀 Starting API Version Comparison" + (" (Resume Mode)" if resume_mode else ""))
    print("=" * 80)
    
    csv_output_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
    
    existing_results = {}
    incomplete_entries = {}
    
    if resume_mode and os.path.exists(csv_output_path):
        print("🔄 Resume mode enabled - analyzing existing results...")
        existing_results = load_existing_results(csv_output_path)
        incomplete_entries = identify_incomplete_entries(csv_output_path)
        
        # Check if any entries need re-analysis
        total_incomplete = sum(
            len(funcs) for api_data in incomplete_entries.values() 
            for status, funcs in api_data.items() if status != 'complete' and funcs
        )
        
        if total_incomplete == 0:
            print("✅ All entries are already complete! No re-analysis needed.")
            return
        else:
            print(f"🎯 Found {total_incomplete} entries that need re-analysis")
    
    print(f"📊 Comparing {VERSION_0_0_1_PATH} vs {VERSION_0_0_8_PATH}")
    print(f"🧵 Using {MAX_FUNCTION_THREADS} parallel threads")
    
    # Initialize Gemini client
    if not configure_gemini_client():
        print("❌ Failed to initialize Gemini client")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize incremental CSV file for immediate saving (if not in resume mode)
    if not resume_mode:
        initialize_incremental_csv()
    
    # Scan both versions
    print("\n📁 Scanning API versions...")
    old_version_functions = scan_api_versions(VERSION_0_0_1_PATH)
    new_version_functions = scan_api_versions(VERSION_0_0_8_PATH)
    
    if not old_version_functions or not new_version_functions:
        print("❌ Failed to scan one or both versions")
        return
    
    # Find common and new APIs
    common_apis = set(old_version_functions.keys()) & set(new_version_functions.keys())
    new_apis = set(new_version_functions.keys()) - set(old_version_functions.keys())
    
    # Filter APIs based on resume mode
    if resume_mode and incomplete_entries:
        # Only process APIs that have incomplete entries
        apis_to_process = set(incomplete_entries.keys())
        common_apis = common_apis & apis_to_process
        new_apis = new_apis & apis_to_process
        print(f"🎯 Resume mode: Processing {len(common_apis)} common APIs and {len(new_apis)} new APIs with incomplete entries")
    
    print(f"\n📊 Found {len(common_apis)} common APIs and {len(new_apis)} new APIs")
    
    # Process APIs in parallel
    all_results = []
    
    if common_apis:
        print(f"\n🚀 Starting parallel comparison for {len(common_apis)} APIs...")
        
        with ThreadPoolExecutor(max_workers=MAX_FUNCTION_THREADS, thread_name_prefix="API") as executor:
            # Submit comparison tasks
            future_to_api = {}
            for i, api_name in enumerate(common_apis):
                thread_id = f"API-{i+1}"
                
                # Determine which functions to process for this API
                functions_to_process = None
                if resume_mode and api_name in incomplete_entries:
                    incomplete_functions = []
                    for status in ['missing_analysis', 'error_analysis', 'timeout_analysis']:
                        incomplete_functions.extend(incomplete_entries[api_name][status])
                    functions_to_process = set(incomplete_functions) if incomplete_functions else None
                
                future = executor.submit(
                    compare_function_versions, 
                    api_name, 
                    old_version_functions[api_name], 
                    new_version_functions[api_name], 
                    thread_id,
                    functions_to_process,
                    existing_results
                )
                future_to_api[future] = api_name
            
            # Collect results
            completed_apis = 0
            for future in as_completed(future_to_api):
                api_name = future_to_api[future]
                try:
                    api_results = future.result()
                    all_results.extend(api_results)
                    completed_apis += 1
                    progress = (completed_apis / len(common_apis)) * 100
                    print(f"🎯 Progress: {completed_apis}/{len(common_apis)} ({progress:.1f}%) - {api_name} completed")
                except Exception as e:
                    print(f"❌ Error processing {api_name}: {e}")
    
    # Handle new APIs (all functions are new)
    if new_apis:
        print(f"\n✨ Processing {len(new_apis)} new APIs...")
        for api_name in new_apis:
            # Determine which functions to process for this API
            functions_to_process = None
            if resume_mode and api_name in incomplete_entries:
                incomplete_functions = []
                for status in ['missing_analysis', 'error_analysis', 'timeout_analysis']:
                    incomplete_functions.extend(incomplete_entries[api_name][status])
                functions_to_process = set(incomplete_functions) if incomplete_functions else None
            
            for file_path, funcs in new_version_functions[api_name].items():
                for func in funcs:
                    # Apply function filter if provided
                    if functions_to_process is not None and func['name'] not in functions_to_process:
                        # Use existing result if available
                        if existing_results:
                            existing_key = f"{api_name}|{func['name']}"
                            if existing_key in existing_results:
                                all_results.append(existing_results[existing_key])
                        continue
                    
                    result = {
                        'api_name': api_name,
                        'function_name': func['name'],
                        'file_path': file_path,
                        'new_function': True,
                        'function_input_validation_implementation': False,
                        'function_inputs_changes': False,
                        'function_input_signature_change': False,
                        'function_output_signature_change': False,
                        'function_implementation_logic_change': False,
                        'other_changes': False,
                        'analysis_notes': f'New API - {api_name} was added in v0.0.8',
                        'changelog_summary': f"NEW API: Added {api_name} with function {func['name']}"
                    }
                    # Save result incrementally (even in resume mode for new analyses)
                    save_result_incrementally(result)
                    all_results.append(result)
    
    # Merge with existing results if in resume mode
    if resume_mode and existing_results:
        print(f"🔄 Merging {len(all_results)} new results with {len(existing_results)} existing results...")
        
        # Create a lookup for new results
        new_results_lookup = {}
        for result in all_results:
            key = f"{result['api_name']}|{result['function_name']}"
            new_results_lookup[key] = result
        
        # Merge: use new results where available, keep existing otherwise
        merged_results = []
        for key, existing_row in existing_results.items():
            if key in new_results_lookup:
                merged_results.append(new_results_lookup[key])
            else:
                merged_results.append(existing_row)
        
        # Add any completely new results not in existing
        for result in all_results:
            key = f"{result['api_name']}|{result['function_name']}"
            if key not in existing_results:
                merged_results.append(result)
        
        all_results = merged_results
        print(f"✅ Merged results: {len(all_results)} total entries")
    
    # Generate outputs
    print(f"\n📄 Generating outputs...")
    generate_csv_output(all_results)
    generate_changelog_output(all_results)
    
    # Summary statistics
    print_summary_statistics(all_results)
    
    print(f"\n🎉 Comparison completed successfully!")
    print(f"📊 Results saved to: {OUTPUT_DIR}/")

# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def generate_csv_output(results: List[Dict]):
    """Generate CSV output with all comparison results."""
    
    csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
    
    # Define CSV headers
    headers = [
        'api_name',
        'function_name', 
        'file_path',
        'new_function',
        'function_input_validation_implementation',
        'function_inputs_changes',
        'function_input_signature_change',
        'function_output_signature_change',
        'function_implementation_logic_change',
        'other_changes',
        'analysis_notes',
        'changelog_summary'
    ]
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for result in results:
            writer.writerow(result)
    
    print(f"✅ CSV output generated: {csv_path}")

def save_result_incrementally(result: Dict, create_header: bool = False):
    """Save a single result to CSV immediately (incremental saving)."""
    
    csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
    
    # Define CSV headers
    headers = [
        'api_name',
        'function_name', 
        'file_path',
        'new_function',
        'function_input_validation_implementation',
        'function_inputs_changes',
        'function_input_signature_change',
        'function_output_signature_change',
        'function_implementation_logic_change',
        'other_changes',
        'analysis_notes',
        'changelog_summary'
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
        'new_function',
        'function_input_validation_implementation',
        'function_inputs_changes',
        'function_input_signature_change',
        'function_output_signature_change',
        'function_implementation_logic_change',
        'other_changes',
        'analysis_notes',
        'changelog_summary'
    ]
    
    # Create fresh CSV file with headers
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
    
    print(f"📄 Initialized incremental CSV: {csv_path}")

def generate_changelog_output(results: List[Dict]):
    """Generate markdown changelog output."""
    
    changelog_path = os.path.join(OUTPUT_DIR, CHANGELOG_OUTPUT_FILE)
    
    # Group results by API
    api_groups = {}
    for result in results:
        api_name = result['api_name']
        if api_name not in api_groups:
            api_groups[api_name] = []
        api_groups[api_name].append(result)
    
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write("# API Version Comparison Changelog\n\n")
        f.write(f"**Comparison**: v0.0.1 → v0.0.8\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary statistics
        total_functions = len(results)
        new_functions = sum(1 for r in results if r['new_function'])
        changed_functions = sum(1 for r in results if not r['new_function'] and any(r[dim] for dim in COMPARISON_DIMENSIONS[1:]))
        
        f.write("## Summary\n\n")
        f.write(f"- **Total Functions Analyzed**: {total_functions}\n")
        f.write(f"- **New Functions**: {new_functions}\n")
        f.write(f"- **Changed Functions**: {changed_functions}\n")
        f.write(f"- **Unchanged Functions**: {total_functions - new_functions - changed_functions}\n")
        f.write(f"- **APIs Covered**: {len(api_groups)}\n\n")
        
        # Detailed changes by API
        f.write("## Detailed Changes by API\n\n")
        
        for api_name in sorted(api_groups.keys()):
            api_results = api_groups[api_name]
            
            # API-level summary
            api_new = sum(1 for r in api_results if r['new_function'])
            api_changed = sum(1 for r in api_results if not r['new_function'] and any(r[dim] for dim in COMPARISON_DIMENSIONS[1:]))
            
            f.write(f"### {api_name}\n\n")
            f.write(f"- Functions analyzed: {len(api_results)}\n")
            f.write(f"- New functions: {api_new}\n")
            f.write(f"- Changed functions: {api_changed}\n\n")
            
            # Group by change type
            new_funcs = [r for r in api_results if r['new_function']]
            changed_funcs = [r for r in api_results if not r['new_function'] and any(r[dim] for dim in COMPARISON_DIMENSIONS[1:])]
            
            if new_funcs:
                f.write("#### New Functions\n\n")
                for result in new_funcs:
                    f.write(f"- **{result['function_name']}** in `{result['file_path']}`\n")
                    f.write(f"  - {result['changelog_summary']}\n\n")
            
            if changed_funcs:
                f.write("#### Changed Functions\n\n")
                for result in changed_funcs:
                    f.write(f"- **{result['function_name']}** in `{result['file_path']}`\n")
                    
                    # List specific changes
                    changes = []
                    for dim in COMPARISON_DIMENSIONS[1:]:
                        if result[dim]:
                            changes.append(dim.replace('_', ' ').title())
                    
                    if changes:
                        f.write(f"  - Changes: {', '.join(changes)}\n")
                    
                    f.write(f"  - {result['changelog_summary']}\n\n")
    
    print(f"✅ Changelog generated: {changelog_path}")

def print_summary_statistics(results: List[Dict]):
    """Print summary statistics of the comparison."""
    
    print("\n📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    total_functions = len(results)
    new_functions = sum(1 for r in results if r['new_function'])
    
    # Count changes by dimension
    dimension_counts = {}
    for dim in COMPARISON_DIMENSIONS[1:]:
        dimension_counts[dim] = sum(1 for r in results if r[dim])
    
    print(f"Total Functions Analyzed: {total_functions}")
    print(f"New Functions: {new_functions}")
    print(f"Existing Functions: {total_functions - new_functions}")
    print()
    
    print("Changes by Dimension:")
    for dim, count in dimension_counts.items():
        percentage = (count / total_functions) * 100 if total_functions > 0 else 0
        print(f"  {dim.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    # API-level summary
    api_counts = {}
    for result in results:
        api_name = result['api_name']
        if api_name not in api_counts:
            api_counts[api_name] = {'total': 0, 'new': 0, 'changed': 0}
        
        api_counts[api_name]['total'] += 1
        if result['new_function']:
            api_counts[api_name]['new'] += 1
        elif any(result[dim] for dim in COMPARISON_DIMENSIONS[1:]):
            api_counts[api_name]['changed'] += 1
    
    print(f"\nTop APIs by Changes:")
    sorted_apis = sorted(api_counts.items(), key=lambda x: x[1]['changed'] + x[1]['new'], reverse=True)
    
    for api_name, counts in sorted_apis[:10]:  # Top 10
        total_changes = counts['new'] + counts['changed']
        print(f"  {api_name}: {total_changes} changes ({counts['new']} new, {counts['changed']} modified)")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🎬 API Version Comparison Tool")
    print("=" * 60)
    
    # Verify paths exist
    if not os.path.exists(VERSION_0_0_1_PATH):
        print(f"❌ Version 0.0.1 path not found: {VERSION_0_0_1_PATH}")
        exit(1)
    
    if not os.path.exists(VERSION_0_0_8_PATH):
        print(f"❌ Version 0.0.8 path not found: {VERSION_0_0_8_PATH}")
        exit(1)
    
    print(f"✅ Version paths verified")
    print(f"📁 v0.0.1: {VERSION_0_0_1_PATH}")
    print(f"📁 v0.0.8: {VERSION_0_0_8_PATH}")
    print(f"📄 Output directory: {OUTPUT_DIR}")
    
    # Run the comparison
    try:
        run_version_comparison()
    except KeyboardInterrupt:
        print("\n⏹️ Comparison interrupted by user")
    except Exception as e:
        print(f"\n❌ Comparison failed: {e}")
        traceback.print_exc() 