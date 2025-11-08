
import os
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import analyzer
import utils

def load_config(config_path='config.json'):
    """Loads the configuration file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def run_single_check(analysis_func, file_path, func_name, prompt_template, api_call_delay, service_name=None, function_map_key=None):
    """
    A wrapper to call the analysis for a single function.
    The utility function now handles its own file reading.
    """
    try:
        func_code = utils.get_function_code_from_file(file_path, func_name)
        if "File not found:" in func_code or "Error reading file " in func_code:
            return {"status": "Error", "notes": f"Could not find or read function '{func_name}': {func_code}"}

        func_data = {
            "function_name": func_name,
            "function_code": func_code,
            "file_path": file_path,
            "service_name": service_name,
            "function_map_key": function_map_key
        }
        
        return analysis_func(func_data, prompt_template, api_call_delay, func_name)

    except Exception as e:
        print(f"--- EXCEPTION IN THREAD for {func_name}: {e} ---")
        return {"status": "Error", "notes": f"An unexpected error occurred: {e}"}

def tech_debt_analyzer(services=None, checks=None, tool=None):
    """
    Runs the core analysis logic and returns the results as a dictionary.
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = load_config(config_path)
    
    analyzer.configure_gemini_client(os.environ.get("GEMINI_API_KEY"), config['gemini_model'])

    functions_to_analyze = []
    services_to_analyze = []

    if tool:
        if '/' not in tool:
            return {"error": "Invalid format for --tool. Please use <service_name>/<tool_name>."}
        service_name, tool_name = tool.split('/', 1)
        service_path = os.path.join('APIs', service_name)
        if not os.path.isdir(service_path):
            return {"error": f"Service '{service_name}' not found."}

        function_map = utils.extract_function_map(service_path)
        if not function_map:
            return {"error": f"No `_function_map` found for service '{service_name}'."}
        
        if tool_name not in function_map:
            return {"error": f"Tool '{tool_name}' not found in the function map for service '{service_name}'."}

        module_path = function_map[tool_name]
        path_parts = module_path.split('.')
        actual_func_name = path_parts[-1]
        file_path = os.path.join('APIs', service_name, *path_parts[1:-1]) + '.py'
        
        functions_to_analyze.append({
            "service": service_name,
            "func_name": actual_func_name,
            "file_path": file_path,
            "tool_name": tool_name
        })
        services_to_analyze.append(service_path)

    elif services:
        for service in services:
            service_path = os.path.join('APIs', service)
            if not os.path.isdir(service_path):
                print(f"Warning: Service '{service}' not found at '{service_path}'. Skipping.")
                continue
            services_to_analyze.append(service_path)
            
            function_map = utils.extract_function_map(service_path)
            if not function_map:
                print(f"Warning: No `_function_map` found for service '{service}'.")
                continue

            for api_func_name, module_path in function_map.items():
                path_parts = module_path.split('.')
                actual_func_name = path_parts[-1]
                file_path = os.path.join('APIs', service, *path_parts[1:-1]) + '.py'
                functions_to_analyze.append({
                    "service": service,
                    "func_name": actual_func_name,
                    "file_path": file_path,
                    "tool_name": api_func_name
                })
    else:
        return {"error": "You must specify either services or a tool."}

    print(f"Analyzing {len(functions_to_analyze)} functions...")
    if not functions_to_analyze and not any(c['target_type'] == 'project' for c in config['checks']):
        return {"error": "No functions or project-level checks to run."}

    checks_to_run = [c for c in config['checks'] if c.get('enabled', False) and (not checks or c['output_key'] in checks)]
    print(f"Running the following checks: {[check['name'] for check in checks_to_run]}", flush=True)

    results = {"analysis_timestamp": datetime.utcnow().isoformat() + "Z", "results": {}, "project_level": {}}
    analysis_functions = {
        "docstring_quality": analyzer.analyze_docstring_quality,
        "pydantic_usage": analyzer.analyze_pydantic_usage,
        "input_validation": analyzer.analyze_input_validation,
        "function_parameters": analyzer.analyze_function_parameters,
        "implementation_status": analyzer.analyze_implementation_status,
        "project_structure": analyzer.analyze_project_structure,
        "input_normalization": analyzer.analyze_input_normalization,
        "docstring_v_schema": analyzer.analyze_docstring_schema_comparison,
    }

    for check in checks_to_run:
        prompt_template_path = os.path.join(os.path.dirname(__file__), check['prompt_template_file'])
        with open(prompt_template_path, 'r') as f:
            prompt_template = f.read()
        
        analysis_func = analysis_functions.get(check['output_key'])
        if not analysis_func: continue

        if check['target_type'] == 'function':
            for func_info in functions_to_analyze:
                print(f"Running {check['name']} for {func_info['func_name']}...", flush=True)
                analysis_result = run_single_check(
                    analysis_func,
                    func_info['file_path'],
                    func_info['func_name'],
                    prompt_template,
                    config['api_call_delay_seconds'],
                    func_info['service'],
                    func_info['tool_name']
                )
                # Construct the relative path as service_name/file_name.py
                relative_path = os.path.join(func_info['service'], os.path.basename(func_info['file_path']))
                relative_path = relative_path.replace('\\', '/') # Normalize for consistency
                # Use the actual function name for the function key
                results["results"].setdefault(relative_path, {"functions": {}}).setdefault("functions", {}).setdefault(func_info['func_name'], {})[check['output_key']] = analysis_result

        elif check['target_type'] == 'project':
            for service_path in services_to_analyze:
                api_data = utils.get_api_structure(service_path)
                service_name = api_data['api_name']
                print(f"Running {check['name']} for project {service_name}...", flush=True)
                analysis_result = analysis_func(api_data, prompt_template, config['api_call_delay_seconds'], f"project_structure_{service_name}")
                results["project_level"].setdefault(service_name, {})[check['output_key']] = analysis_result
    
    return results

def main():
    """
    Main entrypoint for command-line execution.
    """
    print("--- Starting Tech Debt Analysis ---")
    parser = argparse.ArgumentParser(description="Tech Debt Analysis Framework")
    parser.add_argument('-s', '--services', nargs='+', help='List of services (API folder names) to analyze.')
    parser.add_argument('-c', '--checks', nargs='+', help='List of checks to run (e.g., docstring_quality).')
    parser.add_argument('-t', '--tool', help='Specify a single tool to analyze in the format <service_name>/<tool_name>.')
    parser.add_argument('-o', '--output', help='Path to save the results JSON file.')
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return
    
    results = tech_debt_analyzer(services=args.services, checks=args.checks, tool=args.tool)

    if "error" in results:
        print(f"An error occurred: {results['error']}")
        return

    if args.output:
        results_path = args.output
    else:
        results_path = os.path.join(os.path.dirname(__file__), 'results', 'results.json')
    
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Analysis complete. Results saved to {results_path}")


if __name__ == '__main__':
    main()