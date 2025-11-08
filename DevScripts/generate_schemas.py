
#!/usr/bin/env python3

"""
This script generates the Function Calling (FC) schemas for all API packages
using the new decorator-based introspection method.

It is a drop-in replacement for the original generate_schemas.py script, but
for this test, it is hardcoded to run only for the 'service_template'.
"""

import os
import sys
import argparse

# Get the absolute path to the project root directory
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    # Fallback for interactive environments
    BASE_DIR = os.path.abspath(os.path.join(os.getcwd()))

# Add the project root and the APIs directory to the Python path
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
APIS_DIR_PATH = os.path.join(BASE_DIR, "APIs")
if APIS_DIR_PATH not in sys.path:
    sys.path.append(APIS_DIR_PATH)

# --- Import from the NEW decorator-based schema generator ---
from Scripts.FCSpec import generate_package_schema, generate_schemas_for_packages

def main():
    """
    Main function to generate schemas for API packages.
    """
    parser = argparse.ArgumentParser(
        description="Generate Function Calling (FC) schemas from @tool_spec decorators."
    )
    parser.add_argument(
        '-s', '--service',
        help='Generate schema for a single service.'
    )
    args = parser.parse_args()

    apis_dir = os.path.join(BASE_DIR, "APIs")
    fc_dir = os.path.join(BASE_DIR, "Schemas")

    print("\nGenerating FC Schemas from @tool_spec decorators")
    os.makedirs(fc_dir, exist_ok=True)

    if args.service:
        # Generate for a single service
        service_path = os.path.join(apis_dir, args.service)
        if not os.path.isdir(service_path):
            print(f"Error: Service '{args.service}' not found at '{service_path}'.")
            return
        print(f"Targeting single service: {args.service}")
        print(f"-> Generating schema for '{args.service}'...")
        try:
            generate_package_schema(service_path, output_folder_path=fc_dir)
        except Exception as e:
            print(f"   Error generating schema for '{args.service}': {e}")
    else:
        # Generate for all services using the parallel processing function
        print("Targeting all services...")
        print("Using parallel processing (mysql will be processed last)...")
        try:
            # Use the function that handles parallel processing and mysql sequentially
            generate_schemas_for_packages(apis_dir, fc_dir)
        except Exception as e:
            print(f"Error during schema generation: {e}")
            return

    print("\nSchema generation complete.")
    print(f"Schemas saved in: {fc_dir}")


if __name__ == "__main__":
    main()
