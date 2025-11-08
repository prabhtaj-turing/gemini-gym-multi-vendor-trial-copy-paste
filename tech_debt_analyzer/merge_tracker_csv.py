#!/usr/bin/env python3

"""
This script merges the function-schema map with the main tech debt tracker CSV.
"""

import os
import sys
import csv
import pandas as pd

def main():
    """
    Main function to merge the two CSV files.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    tracker_file = os.path.join(BASE_DIR, "docstring_vs_FCSpec.csv")
    map_file = os.path.join(BASE_DIR, "function_schema_map.csv")
    output_file = os.path.join(BASE_DIR, "docstring_vs_FCSpec_enriched.csv")

    if not os.path.exists(tracker_file) or not os.path.exists(map_file):
        print("Error: Input files not found. Please ensure both")
        print(f"'{os.path.basename(tracker_file)}' and '{os.path.basename(map_file)}' exist.")
        return

    try:
        # Read the two CSV files into pandas DataFrames
        print("Reading tracker and mapping files...")
        tracker_df = pd.read_csv(tracker_file)
        map_df = pd.read_csv(map_file)

        # Merge the two dataframes based on API, File, and Function Name
        print("Merging data...")
        enriched_df = pd.merge(
            tracker_df,
            map_df,
            how="left",
            left_on=["APIs", "File", "Function"],
            right_on=["APIs", "File", "Function Name"]
        )

        # Get the original header and insert the new columns
        original_header = tracker_df.columns.tolist()
        new_header = original_header[:3] + ["Tool Name", "Schema"] + original_header[3:]
        
        # Reorder and select the final columns, dropping the duplicate "Function Name"
        final_df = enriched_df[new_header]

        # Save the final merged dataframe to a new CSV
        print(f"Writing enriched data to '{os.path.basename(output_file)}'...")
        final_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
        
        print("\nSuccessfully created enriched tracker file.")
        print(f"Total rows in new file: {len(final_df)}")

    except Exception as e:
        print(f"An error occurred during the merge process: {e}")

if __name__ == "__main__":
    main()
