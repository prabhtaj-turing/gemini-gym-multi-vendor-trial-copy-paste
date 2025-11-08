import os
import time
import json
import re
import threading
import google.generativeai as genai
from requests.exceptions import ConnectionError
from urllib3.exceptions import ProtocolError

# Thread-safe rate limiting
api_call_lock = threading.Lock()
last_api_call_time = 0

gemini_client = None

def configure_gemini_client(api_key: str, model_name: str):
    """Configures and returns the Gemini API client."""
    global gemini_client
    try:
        if not api_key:
            print("GEMINI_API_KEY not found. Please add it to your environment variables.")
            return None

        genai.configure(api_key=api_key)
        gemini_client = genai.GenerativeModel(model_name)
        print(f"Gemini client initialized successfully with model: {model_name}")
        return gemini_client
    except Exception as e:
        print(f"Error configuring Gemini client: {e}")
        gemini_client = None
        return None

def call_gemini_api_threadsafe(prompt_text: str, api_call_delay: int, thread_id: str = "", max_retries: int = 4) -> str:
    """
    Thread-safe version of Gemini API call with proper rate limiting and retry logic.
    """
    global last_api_call_time, api_call_lock

    if not gemini_client:
        return "Error: Gemini client not initialized."

    for attempt in range(max_retries):
        try:
            with api_call_lock:
                current_time = time.time()
                time_since_last_call = current_time - last_api_call_time

                if time_since_last_call < api_call_delay:
                    sleep_time = api_call_delay - time_since_last_call
                    if attempt == 0:
                        print(f"   🕐 Thread {thread_id}: Waiting {sleep_time:.1f}s for rate limit...")
                    time.sleep(sleep_time)

                last_api_call_time = time.time()

            generation_config_dict = {"temperature": 0.3, "max_output_tokens": 8192}
            safety_settings_dict = {}

            response = gemini_client.generate_content(
                prompt_text,
                generation_config=generation_config_dict,
                safety_settings=safety_settings_dict
            )

            if response.candidates:
                candidate = response.candidates[0]
                try:
                    candidate_reason_value = candidate.finish_reason.value
                except AttributeError:
                    candidate_reason_value = candidate.finish_reason

                if candidate_reason_value == 1: # STOP
                    if candidate.content and candidate.content.parts:
                        return "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    return ""
                else: # Other reasons
                    content_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text')) if candidate.content and candidate.content.parts else ""
                    return f"Error: Gemini response stopped for reason code: {candidate_reason_value}. Content: {content_text}"
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                 return f"Error: Gemini prompt blocked. Reason: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}"
            return "Error: No candidates found in Gemini response."

        except (ConnectionError, ProtocolError, Exception) as e:
            error_msg = str(e)
            if any(error_pattern in error_msg.lower() for error_pattern in ['connection aborted', 'remote end closed connection', 'connection broken', 'protocolerror', 'connectionerror', 'timeout', 'read timeout']):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"   🔄 Thread {thread_id}: Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return f"Connection Error in thread {thread_id}: Failed after {max_retries} attempts - {error_msg}"
            else:
                return f"Gemini API Error in thread {thread_id}: {error_msg}"

    return f"Max retries exceeded in thread {thread_id}"

def analyze_project_structure(api_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    """
    Analyze if all relevant files are present for the API service.
    """
    prompt = prompt_template.format(
        api_name=api_data['api_name'],
        init_status='PRESENT' if api_data['init_file'] else 'MISSING',
        sim_engine_file_count=len(api_data['simulation_engine_files']),
        sim_engine_files=[f['name'] for f in api_data['simulation_engine_files']],
        main_api_file_count=len(api_data['main_api_files']),
        main_api_files=[f['name'] for f in api_data['main_api_files']],
        tests_file_count=len(api_data.get('tests_files', [])),
        tests_files=[f['name'] for f in api_data.get('tests_files', [])]
    )
    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    
    category = "Others"
    notes = response
    category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]', r'STATUS:\s*\[([^\]]+)\]', r'STATUS:\s*([^\n]+)', r'CATEGORY:\s*([^\n]+)']
    for pattern in category_patterns:
        match = re.search(pattern, response)
        if match:
            category = match.group(1).strip()
            break
    notes_patterns = [r'NOTES:\s*\[([^\]]+)\]', r'NOTES:\s*(.+?)(?=\n\n|\Z)', r'(?:STATUS|CATEGORY):\s*[^\n]+\n(.+)']
    for pattern in notes_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            notes = match.group(1).strip()
            break
    valid_categories = ['Complete', 'Mostly Complete', 'Incomplete', 'Poor Structure', 'Others']
    if category not in valid_categories:
        category = "Others"
    return {'status': category, 'notes': notes}


def analyze_docstring_quality(func_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    prompt = prompt_template.format(code=func_data['function_code'])
    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    category = "Others"
    notes = response
    category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]', r'DOCUMENTATION_QUALITY:\s*\[([^\]]+)\]', r'DOCUMENTATION_QUALITY:\s*([^\n]+)', r'CATEGORY:\s*([^\n]+)']
    for pattern in category_patterns:
        match = re.search(pattern, response)
        if match:
            category = match.group(1).strip()
            break
    notes_patterns = [r'NOTES:\s*\[([^\]]+)\]', r'NOTES:\s*(.+?)(?=\n\n|\Z)', r'OBSERVATIONS:\s*(.+?)(?=\n\n|\Z)']
    for pattern in notes_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            notes = match.group(1).strip()
            break
    valid_categories = ['Excellent', 'Good', 'Adequate', 'Poor', 'Missing', 'Others']
    if category not in valid_categories:
        category = "Others"
    return {'status': category, 'notes': notes}


def analyze_pydantic_usage(func_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    prompt = prompt_template.format(code=func_data['function_code'])
    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    category = "Others"
    notes = response
    category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]', r'PYDANTIC_USAGE:\s*\[([^\]]+)\]', r'PYDANTIC_USAGE:\s*([^\n]+)', r'CATEGORY:\s*([^\n]+)']
    for pattern in category_patterns:
        match = re.search(pattern, response)
        if match:
            category = match.group(1).strip()
            break
    notes_patterns = [r'NOTES:\s*\[([^\]]+)\]', r'NOTES:\s*(.+?)(?=\n\n|\Z)', r'OBSERVATIONS:\s*(.+?)(?=\n\n|\Z)']
    for pattern in notes_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            notes = match.group(1).strip()
            break
    valid_categories = ['Properly Used', 'Partially Used', 'Not Needed', 'Missing Validation', 'Not Applicable', 'Others']
    if category not in valid_categories:
        category = "Others"
    return {'status': category, 'notes': notes}

def analyze_input_validation(func_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    prompt = prompt_template.format(code=func_data['function_code'])
    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    category = "Others"
    notes = response
    category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]', r'VALIDATION_COVERAGE:\s*\[([^\]]+)\]', r'VALIDATION_COVERAGE:\s*([^\n]+)', r'CATEGORY:\s*([^\n]+)']
    for pattern in category_patterns:
        match = re.search(pattern, response)
        if match:
            category = match.group(1).strip()
            break
    notes_patterns = [r'NOTES:\s*\[([^\]]+)\]', r'NOTES:\s*(.+?)(?=\n\n|\Z)', r'OBSERVATIONS:\s*(.+?)(?=\n\n|\Z)']
    for pattern in notes_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            notes = match.group(1).strip()
            break
    valid_categories = ['Comprehensive', 'Good', 'Partial', 'Minimal', 'None', 'Others']
    if category not in valid_categories:
        category = "Others"
    return {'status': category, 'notes': notes}

def analyze_function_parameters(func_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    prompt = prompt_template.format(code=func_data['function_code'])
    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    category = "Others"
    notes = response
    category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]', r'PARAMETER_QUALITY:\s*\[([^\]]+)\]', r'PARAMETER_QUALITY:\s*([^\n]+)', r'CATEGORY:\s*([^\n]+)']
    for pattern in category_patterns:
        match = re.search(pattern, response)
        if match:
            category = match.group(1).strip()
            break
    notes_patterns = [r'NOTES:\s*\[([^\]]+)\]', r'NOTES:\s*(.+?)(?=\n\n|\Z)', r'OBSERVATIONS:\s*(.+?)(?=\n\n|\Z)']
    for pattern in notes_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            notes = match.group(1).strip()
            break
    valid_categories = ['Excellent', 'Good', 'Fair', 'Poor', 'Others']
    if category not in valid_categories:
        category = "Others"
    return {'status': category, 'notes': notes}

def analyze_implementation_status(func_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    prompt = prompt_template.format(code=func_data['function_code'])
    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    category = "Others"
    notes = response
    category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]', r'IMPLEMENTATION_STATUS:\s*\[([^\]]+)\]', r'IMPLEMENTATION_STATUS:\s*([^\n]+)', r'CATEGORY:\s*([^\n]+)']
    for pattern in category_patterns:
        match = re.search(pattern, response)
        if match:
            category = match.group(1).strip()
            break
    notes_patterns = [r'NOTES:\s*\[([^\]]+)\]', r'NOTES:\s*(.+?)(?=\n\n|\Z)', r'OBSERVATIONS:\s*(.+?)(?=\n\n|\Z)']
    for pattern in notes_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            notes = match.group(1).strip()
            break
    valid_categories = ['Fully Implemented', 'Mostly Complete', 'Partially Complete', 'Stub', 'Not Implemented', 'Others']
    if category not in valid_categories:
        category = "Others"
    return {'status': category, 'notes': notes}


def analyze_input_normalization(func_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    prompt = prompt_template.format(function_code=func_data['function_code'])
    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    
    try:
        # Primary method: Parse structured JSON response
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Fallback for cases where the markdown is missing but it's still JSON
            json_str = response[response.find('{'):response.rfind('}')+1]

        data = json.loads(json_str)
        
        status = data.get("status", "Error")
        notes = data.get("notes", "Malformed JSON response from API.")

        valid_categories = ['Excellent', 'Good', 'Poor', 'Not Applicable']
        if status not in valid_categories:
            notes = f"Invalid status '{status}' received from API. Original notes: {notes}"
            status = "Error"

        return {'status': status, 'notes': notes}

    except (json.JSONDecodeError, AttributeError, IndexError):
        # Fallback method: Parse unstructured text response using regex
        # This handles cases where the model fails to produce valid JSON.
        category = "Error" # Default to Error if parsing fails
        notes = response
        
        category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]', r'STATUS:\s*\[([^\]]+)\]', r'STATUS:\s*([^\n]+)', r'CATEGORY:\s*([^\n]+)']
        for pattern in category_patterns:
            match = re.search(pattern, response)
            if match:
                category = match.group(1).strip()
                break
        
        notes_patterns = [r'NOTES:\s*\[([^\]]+)\]', r'NOTES:\s*(.+?)(?=\n\n|\Z)', r'(?:STATUS|CATEGORY):\s*[^\n]+\n(.+)']
        for pattern in notes_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                notes = match.group(1).strip()
                break
        
        valid_categories = ['Excellent', 'Good', 'Poor', 'Not Applicable']
        if category not in valid_categories:
            category = "Error" # If regex finds a category but it's invalid
            
        return {'status': category, 'notes': notes}


def analyze_docstring_schema_comparison(func_data: dict, prompt_template: str, api_call_delay: int, thread_id: str = "main") -> dict:
    """
    Analyzes the alignment between a function's docstring and its FCSpec schema.
    """
    service_name = func_data['service_name']
    function_map_key = func_data['function_map_key']

    # Construct the path to the schema file
    schema_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'Schemas', f"{service_name}.json"
    ))

    if not os.path.exists(schema_file_path):
        return {'status': 'Error', 'notes': f"Schema file not found: {schema_file_path}"}

    try:
        with open(schema_file_path, 'r') as f:
            schema_data = json.load(f)
    except json.JSONDecodeError:
        return {'status': 'Error', 'notes': f"Could not decode JSON from {schema_file_path}"}

    # Find the function schema
    function_schema = None
    if isinstance(schema_data, list):
        for func in schema_data:
            if func.get('name') == function_map_key:
                function_schema = func
                break
    elif isinstance(schema_data, dict):
        for tool in schema_data.get('tools', []):
            if tool.get('function_declarations'):
                for func in tool['function_declarations']:
                    if func.get('name') == function_map_key:
                        function_schema = func
                        break
            if function_schema:
                break
    
    if not function_schema:
        return {'status': 'Error', 'notes': f"Function '{function_map_key}' not found in schema."}

    prompt = prompt_template.format(
        code=func_data['function_code'],
        schema=json.dumps(function_schema, indent=2)
    )

    response = call_gemini_api_threadsafe(prompt, api_call_delay, thread_id)
    
    category = "Error"
    notes = response
    
    category_patterns = [r'CATEGORY:\s*\[([^\]]+)\]']
    for pattern in category_patterns:
        match = re.search(pattern, response)
        if match:
            category = match.group(1).strip()
            break
            
    notes_patterns = [r'NOTES:\s*\[(.*)\]', r'NOTES:\s*(.*)']
    for pattern in notes_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            notes = match.group(1).strip()
            break
            
    valid_categories = ['Aligned', 'Mismatched']
    if category not in valid_categories:
        # If the model returns something unexpected, mark it for review.
        category = "Error"
    
    # If the category is Error, but the notes say it's aligned, fix it.
    if category != "Mismatched" and "perfectly aligned" in notes.lower():
        category = "Aligned"
        
    return {'status': category, 'notes': notes}