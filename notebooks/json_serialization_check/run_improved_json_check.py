#!/usr/bin/env python3
"""
Improved JSON Serialization Check Runner

This script helps you configure and run the improved JSON serialization check
with LLM analysis and incremental saving capabilities.

Usage:
    python run_improved_json_check.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv('.env')

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if required packages are installed
    try:
        import google.generativeai as genai
        print("✅ google-generativeai is installed")
    except ImportError:
        print("❌ google-generativeai is not installed")
        print("   Please run: pip install google-generativeai")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv is installed")
    except ImportError:
        print("❌ python-dotenv is not installed")
        print("   Please run: pip install python-dotenv")
        return False
    
    # Check if SDK directory exists
    api_path = Path("../../APIs")
    
    if not api_path.exists():
        print(f"❌ SDK modules directory not found: {api_path}")
        print(f"   Please ensure you're running from the correct directory")
        return False
    else:
        print(f"✅ SDK modules directory found: {api_path}")
    
    # Count available SDK modules
    api_dirs = [d for d in api_path.iterdir() if d.is_dir() and not d.name.startswith('__')]
    print(f"✅ Found {len(api_dirs)} SDK modules")
    
    # Check for environment variables
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not found in environment")
        print("   Please create a .env file with: GEMINI_API_KEY=your_api_key_here")
        print("   Or set the environment variable directly")
        return False
    else:
        print("✅ GEMINI_API_KEY is configured")
    
    return True

def show_configuration():
    """Show current configuration."""
    print("\n📋 Current Configuration:")
    print("=" * 50)
    print(f"SDK modules path: ../../APIs")
    print(f"Output directory: json_serialization_results")
    print(f"CSV output: improved_json_serialization_check.csv")
    print(f"Summary output: improved_json_serialization_summary.md")
    print(f"Parallel threads: {os.getenv('MAX_THREADS')}")
    print(f"Timeout per module: {os.getenv('TIMEOUT_SECONDS')} seconds")
    print(f"Gemini model: {os.getenv('GEMINI_MODEL_NAME')}")
    print(f"API call delay: {os.getenv('API_CALL_DELAY')} seconds")
    print(f"Gemini API key: {'✅ Configured' if os.getenv('GEMINI_API_KEY') else '❌ Not configured'}")

def list_available_apis():
    """List available SDK modules."""
    print("\n📁 Available SDK Modules:")
    print("=" * 50)
    
    api_path = Path("../../APIs")
    
    if not api_path.exists():
        print("❌ SDK modules directory not found")
        return
    
    api_dirs = []
    for item in api_path.iterdir():
        if item.is_dir() and not item.name.startswith('__'):
            api_dirs.append(item.name)
    
    api_dirs.sort()
    
    print(f"Total SDK modules found: {len(api_dirs)}")
    print("\nSDK module list:")
    for i, api_name in enumerate(api_dirs, 1):
        print(f"{i:3d}. {api_name}")

def run_improved_json_check():
    """Run the improved JSON serialization check for SDK persistence."""
    print("\n🚀 Starting SDK JSON Persistence Analysis...")
    print("=" * 50)
    
    # Import and run the check
    try:
        from improved_json_serialization_checker import run_improved_json_serialization_check
        run_improved_json_serialization_check()
    except ImportError as e:
        print(f"❌ Failed to import checker module: {e}")
        print("   Please ensure improved_json_serialization_checker.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Check failed: {e}")
        return False
    
    return True

def run_improved_json_check_with_resume():
    """Run the improved JSON serialization check with resume capability."""
    print("\n🔄 Starting Resume Analysis...")
    print("=" * 50)
    
    try:
        from improved_json_serialization_checker import run_improved_json_serialization_check_with_resume
        run_improved_json_serialization_check_with_resume(resume_mode=True)
    except ImportError as e:
        print(f"❌ Failed to import checker module: {e}")
        print("   Please ensure improved_json_serialization_checker.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Resume check failed: {e}")
        return False
    
    return True

def analyze_existing_results():
    """Analyze existing results."""
    print("\n🔍 Analyzing Existing Results...")
    print("=" * 50)
    
    results_dir = Path("json_serialization_results")
    csv_file = results_dir / "improved_json_serialization_check.csv"
    
    if not csv_file.exists():
        print(f"❌ No existing results found at {csv_file}")
        print("   Please run the check first (option 4)")
        return False
    
    try:
        import csv
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            results = list(reader)
        
        if not results:
            print("❌ No data found in results file")
            return False
        
        # Calculate statistics
        total = len(results)
        serializable = sum(1 for r in results if r.get('is_json_serializable', 'false').lower() == 'true')
        non_serializable = total - serializable
        
        execution_stats = {}
        for result in results:
            status = result.get('execution_status', 'unknown')
            execution_stats[status] = execution_stats.get(status, 0) + 1
        
        # API breakdown
        api_stats = {}
        for result in results:
            api_name = result['api_name']
            if api_name not in api_stats:
                api_stats[api_name] = {'total': 0, 'serializable': 0}
            api_stats[api_name]['total'] += 1
            if result.get('is_json_serializable', 'false').lower() == 'true':
                api_stats[api_name]['serializable'] += 1
        
        # Issue type breakdown
        issue_stats = {
            'has_custom_objects': sum(1 for r in results if r.get('has_custom_objects', 'false').lower() == 'true'),
            'has_generators': sum(1 for r in results if r.get('has_generators', 'false').lower() == 'true'),
            'has_callables': sum(1 for r in results if r.get('has_callables', 'false').lower() == 'true'),
            'has_file_handles': sum(1 for r in results if r.get('has_file_handles', 'false').lower() == 'true'),
            'has_network_objects': sum(1 for r in results if r.get('has_network_objects', 'false').lower() == 'true'),
            'has_threading_objects': sum(1 for r in results if r.get('has_threading_objects', 'false').lower() == 'true'),
            'requires_parameters': sum(1 for r in results if r.get('requires_parameters', 'false').lower() == 'true')
        }
        
        print(f"📊 Results Summary:")
        print(f"   Total Functions: {total}")
        print(f"   JSON Serializable: {serializable} ({serializable/total*100:.1f}%)")
        print(f"   Non-Serializable: {non_serializable} ({non_serializable/total*100:.1f}%)")
        print(f"   APIs Analyzed: {len(api_stats)}")
        
        print(f"\n📋 Execution Status Breakdown:")
        for status, count in sorted(execution_stats.items()):
            percentage = (count / total) * 100
            print(f"   {status.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        print(f"\n🔍 Issue Type Breakdown:")
        for issue_type, count in sorted(issue_stats.items()):
            if count > 0:
                percentage = (count / total) * 100
                print(f"   {issue_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Show problematic APIs
        problematic_apis = []
        for api_name, stats in api_stats.items():
            serializable_pct = (stats['serializable'] / stats['total']) * 100
            if serializable_pct < 100:
                problematic_apis.append((api_name, stats['total'] - stats['serializable'], serializable_pct))
        
        if problematic_apis:
            print(f"\n⚠️  APIs with Non-Serializable Functions:")
            problematic_apis.sort(key=lambda x: x[1], reverse=True)  # Sort by number of issues
            for api_name, issues, pct in problematic_apis[:10]:  # Show top 10
                print(f"   {api_name}: {issues} issues ({pct:.1f}% serializable)")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def analyze_incomplete_entries():
    """Analyze existing CSV to identify incomplete entries."""
    print("\n🔍 Analyzing Existing Results...")
    print("=" * 50)
    
    try:
        from improved_json_serialization_checker import identify_incomplete_entries, OUTPUT_DIR, CSV_OUTPUT_FILE
        import os
        
        csv_path = os.path.join(OUTPUT_DIR, CSV_OUTPUT_FILE)
        if not os.path.exists(csv_path):
            print(f"❌ No existing CSV file found at {csv_path}")
            print("   Please run a check first (option 4)")
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

def main():
    """Main function."""
    print("🧪 SDK JSON Persistence Analyzer")
    print("=" * 60)
    
    while True:
        print("\n📋 Menu:")
        print("1. Check prerequisites")
        print("2. Show configuration")
        print("3. List available APIs")
        print("4. Run SDK JSON persistence analysis")
        print("5. Analyze existing results")
        print("6. Resume incomplete analysis")
        print("7. Analyze incomplete entries")
        print("8. Exit")
        
        choice = input("\nSelect an option (1-8): ").strip()
        
        if choice == "1":
            if check_prerequisites():
                print("✅ All prerequisites are met!")
            else:
                print("❌ Some prerequisites are missing. Please fix them before running the check.")
        
        elif choice == "2":
            show_configuration()
        
        elif choice == "3":
            list_available_apis()
        
        elif choice == "4":
            if check_prerequisites():
                success = run_improved_json_check()
                if success:
                    print("\n🎉 SDK JSON persistence analysis completed successfully!")
                    print("📊 Check the 'json_serialization_results' directory for outputs")
                else:
                    print("\n❌ Analysis failed. Please see the error messages above.")
            else:
                print("❌ Prerequisites not met. Please fix them first.")
        
        elif choice == "5":
            analyze_existing_results()
        
        elif choice == "6":
            if check_prerequisites():
                success = run_improved_json_check_with_resume()
                if success:
                    print("\n🎉 Resume analysis completed successfully!")
                    print("📊 Check the 'json_serialization_results' directory for updated outputs")
                else:
                    print("\n❌ Resume analysis failed. Please check the error messages above.")
            else:
                print("❌ Prerequisites not met. Please fix them first.")
        
        elif choice == "7":
            analyze_incomplete_entries()
        
        elif choice == "8":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-8.")

if __name__ == "__main__":
    main() 