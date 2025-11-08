import os
import sys
import subprocess

# Add the parent directory to the sys.path to allow imports from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DevScripts.validate_changes import main as validate_main

def run_debugger():
    """
    Generates a diff using the same command as the pre-push hook
    and runs the validator script for debugging.
    """
    print("--- Running Validator in Debug Mode ---")
    
    try:
        # Use the exact same command as the pre-push hook to get the diff
        command = ['git', 'diff', '@{u}', 'HEAD']
        print(f"Executing command: `{' '.join(command)}`")
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        diff_content = result.stdout

        if not diff_content:
            print("No changes to validate compared to the upstream branch.")
            sys.exit(0)
            
        print("\n--- Diff Content ---")
        print(diff_content)
        print("--- End Diff Content ---\n")

        validate_main(diff_content)

    except FileNotFoundError:
        print("Error: 'git' command not found. Please ensure Git is installed and in your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing git diff command: {e}")
        print("This can happen if the upstream branch is not set. Try running: git branch --set-upstream-to=origin/<branch_name>")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during debugging: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_debugger()
