#!/usr/bin/env python3

"""
This script generates the Function Calling (FC) schemas for all API packages.
It can generate schemas for all services at once or for a single, specified service.
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

# Add the project root to the Python path to allow for absolute imports
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from Scripts.FCSpec_depricated import generate_package_schema

def main():
    """
    Main function to generate schemas for API packages.
    """
    parser = argparse.ArgumentParser(
        description="Generate Function Calling (FC) schemas for API packages."
    )
    parser.add_argument(
        '-s', '--service',
        help='Generate schema for a single service (e.g., mysql). If not provided, generates for all services.'
    )
    args = parser.parse_args()

    apis_dir = os.path.join(BASE_DIR, "APIs")
    fc_dir = os.path.join(BASE_DIR, "Schemas")

    print("\nGenerating FC Schemas")
    os.makedirs(fc_dir, exist_ok=True)

    package_names = []
    if args.service:
        # Generate for a single service
        service_path = os.path.join(apis_dir, args.service)
        if not os.path.isdir(service_path):
            print(f"Error: Service '{args.service}' not found at '{service_path}'.")
            return
        package_names.append(args.service)
        print(f"Targeting single service: {args.service}")
    else:
        # Generate for all services
        print("Targeting all services...")
        try:
            package_names = [
                name
                for name in os.listdir(apis_dir)
                if os.path.isdir(os.path.join(apis_dir, name))
            ]
        except FileNotFoundError:
            print(f"Error: The directory '{apis_dir}' was not found.")
            return
        print(f"Found {len(package_names)} packages in '{apis_dir}'")

    # Iterate through the selected packages and generate the schema for each
    for package_name in package_names:
        package_path = os.path.join(apis_dir, package_name)
        print(f"-> Generating schema for '{package_name}'...")
        try:
            generate_package_schema(package_path, output_folder_path=fc_dir)
        except Exception as e:
            print(f"   Error generating schema for '{package_name}': {e}")

    print("\nSchema generation complete.")
    print(f"Schemas saved in: {fc_dir}")

if __name__ == "__main__":
    main()