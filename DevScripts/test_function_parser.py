import os
import sys

# Add the project root to the sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tech_debt_analyzer import utils

def test_parser():
    """
    Tests the get_function_code_from_file utility on a specific file
    to ensure it can find all expected functions.
    """
    print("--- Testing Function Parser on APIs/airline/airline.py ---")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    airline_service_path = os.path.join(base_dir, 'APIs', 'airline')
    airline_file_path = os.path.join(airline_service_path, 'airline.py')

    # 1. Get the list of expected function names from the __init__.py
    function_map = utils.extract_function_map(airline_service_path)
    if not function_map:
        print("FAILURE: Could not extract function map from __init__.py")
        return

    expected_functions = [path.split('.')[-1] for path in function_map.values()]
    print(f"Found {len(expected_functions)} functions to test: {expected_functions}\n")

    # 2. Read the content of the airline.py file
    try:
        with open(airline_file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"FAILURE: Could not read file: {airline_file_path}")
        return

    # 3. Loop through and test each function
    all_passed = True
    for func_name in expected_functions:
        result = utils.get_function_code_from_file(file_content, func_name)
        
        if "Function not found" in result:
            print(f"  -> FAILURE: Could not find function '{func_name}'")
            all_passed = False
        else:
            print(f"  -> SUCCESS: Found function '{func_name}'")

    print("\n--- Test Complete ---")
    if all_passed:
        print("Result: All functions were found successfully!")
    else:
        print("Result: Some functions could not be found.")

if __name__ == "__main__":
    test_parser()
