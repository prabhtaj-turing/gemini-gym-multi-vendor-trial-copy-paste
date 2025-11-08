#!/usr/bin/env python3
"""
API Version Comparison Runner

This script helps you configure and run the API version comparison.
"""

import os
import sys
from pathlib import Path

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if required packages are installed
    try:
        import google.generativeai as genai
        print("✅ google-generativeai is installed")
    except ImportError:
        print("❌ google-generativeai is not installed")
        print("   Please run: pip install -r requirements.txt")
        return False
    
    # Check if version directories exist
    v001_path = Path("APIs_V0.0.1/APIs")
    v008_path = Path("APIs_V0.0.8/APIs")
    
    if not v001_path.exists():
        print(f"❌ Version 0.0.1 directory not found: {v001_path}")
        print(f"   Please ensure the APIs_V0.0.1 directory exists in the current directory")
        return False
    else:
        print(f"✅ Version 0.0.1 directory found: {v001_path}")
    
    if not v008_path.exists():
        print(f"❌ Version 0.0.8 directory not found: {v008_path}")
        print(f"   Please ensure the APIs_V0.0.8 directory exists in the current directory")
        return False
    else:
        print(f"✅ Version 0.0.8 directory found: {v008_path}")
    
    return True

def show_configuration():
    """Show current configuration."""
    print("\n📋 Current Configuration:")
    print("=" * 50)
    print(f"Version 0.0.1 path: APIs_V0.0.1/APIs")
    print(f"Version 0.0.8 path: APIs_V0.0.8/APIs")
    print(f"Output directory: comparison_results")
    print(f"CSV output: api_version_comparison.csv")
    print(f"Changelog output: api_version_changelog.md")
    print(f"Parallel threads: 6")
    print(f"Gemini model: gemini-2.5-flash-preview-05-20")

def list_available_apis():
    """List available APIs in both versions."""
    print("\n📁 Available APIs:")
    print("=" * 50)
    
    v001_path = Path("APIs_V0.0.1/APIs")
    v008_path = Path("APIs_V0.0.8/APIs")
    
    v001_apis = set()
    v008_apis = set()
    
    if v001_path.exists():
        v001_apis = {d.name for d in v001_path.iterdir() if d.is_dir()}
    
    if v008_path.exists():
        v008_apis = {d.name for d in v008_path.iterdir() if d.is_dir()}
    
    all_apis = v001_apis | v008_apis
    common_apis = v001_apis & v008_apis
    new_apis = v008_apis - v001_apis
    removed_apis = v001_apis - v008_apis
    
    print(f"Total APIs: {len(all_apis)}")
    print(f"Common APIs (will be compared): {len(common_apis)}")
    print(f"New APIs (only in v0.0.8): {len(new_apis)}")
    print(f"Removed APIs (only in v0.0.1): {len(removed_apis)}")
    
    if common_apis:
        print(f"\nCommon APIs: {', '.join(sorted(common_apis))}")
    
    if new_apis:
        print(f"\nNew APIs: {', '.join(sorted(new_apis))}")
    
    if removed_apis:
        print(f"\nRemoved APIs: {', '.join(sorted(removed_apis))}")

def run_comparison():
    """Run the API version comparison with incremental saving."""
    print("\n🚀 Starting API Version Comparison (with incremental saving)...")
    print("=" * 50)
    
    # Import and run the comparison
    try:
        from api_version_comparison import run_version_comparison
        run_version_comparison()
    except ImportError as e:
        print(f"❌ Failed to import comparison module: {e}")
        print("   Please ensure api_version_comparison.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False
    
    return True

def analyze_incomplete_entries():
    """Analyze existing CSV to identify incomplete entries."""
    print("\n🔍 Analyzing Existing Results...")
    print("=" * 50)
    
    try:
        from api_version_comparison import identify_incomplete_entries, OUTPUT_DIR, CSV_OUTPUT_FILE
        import os
        
        csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
        if not os.path.exists(csv_path):
            print(f"❌ No existing CSV file found at {csv_path}")
            print("   Please run a comparison first (option 4)")
            return False
        
        incomplete_entries = identify_incomplete_entries(csv_path)
        
        if not incomplete_entries:
            print("✅ No incomplete entries found or analysis failed")
            return True
        
        # Show detailed breakdown
        print("\n📋 Detailed Breakdown:")
        for api_name, statuses in incomplete_entries.items():
            total_incomplete = sum(len(funcs) for status, funcs in statuses.items() if status != 'complete')
            if total_incomplete > 0:
                print(f"\n🔸 {api_name}:")
                for status, funcs in statuses.items():
                    if funcs and status != 'complete':
                        print(f"   {status}: {len(funcs)} functions")
                        if len(funcs) <= 5:  # Show function names if few
                            print(f"      Functions: {', '.join(funcs)}")
        
        total_incomplete = sum(
            len(funcs) for api_data in incomplete_entries.values() 
            for status, funcs in api_data.items() if status != 'complete' and funcs
        )
        
        if total_incomplete > 0:
            print(f"\n💡 Found {total_incomplete} incomplete entries")
            print("   Use option 6 to re-analyze only these entries")
        else:
            print("\n✅ All entries are complete!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import analysis module: {e}")
        return False
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def run_comparison_with_resume():
    """Run the API version comparison with resume capability."""
    print("\n🔄 Starting Resume Analysis...")
    print("=" * 50)
    
    try:
        from api_version_comparison import run_version_comparison_with_resume
        run_version_comparison_with_resume(resume_mode=True)
    except ImportError as e:
        print(f"❌ Failed to import comparison module: {e}")
        print("   Please ensure api_version_comparison.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Resume comparison failed: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("🎬 API Version Comparison Tool")
    print("=" * 60)
    
    while True:
        print("\n📋 Menu:")
        print("1. Check prerequisites")
        print("2. Show configuration")
        print("3. List available APIs")
        print("4. Run comparison")
        print("5. Analyze incomplete entries")
        print("6. Resume incomplete analysis")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == "1":
            if check_prerequisites():
                print("✅ All prerequisites are met!")
            else:
                print("❌ Some prerequisites are missing. Please fix them before running the comparison.")
        
        elif choice == "2":
            show_configuration()
        
        elif choice == "3":
            list_available_apis()
        
        elif choice == "4":
            if check_prerequisites():
                success = run_comparison()
                if success:
                    print("\n🎉 Comparison completed successfully!")
                    print("📊 Check the 'comparison_results' directory for outputs")
                else:
                    print("\n❌ Comparison failed. Please check the error messages above.")
            else:
                print("❌ Prerequisites not met. Please fix them first.")
        
        elif choice == "5":
            analyze_incomplete_entries()
        
        elif choice == "6":
            if check_prerequisites():
                success = run_comparison_with_resume()
                if success:
                    print("\n🎉 Resume analysis completed successfully!")
                    print("📊 Check the 'comparison_results' directory for updated outputs")
                else:
                    print("\n❌ Resume analysis failed. Please check the error messages above.")
            else:
                print("❌ Prerequisites not met. Please fix them first.")
        
        elif choice == "7":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-7.")

if __name__ == "__main__":
    main() 