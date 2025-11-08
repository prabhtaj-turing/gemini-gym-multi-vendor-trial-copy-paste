import os
import requests

def get_changed_files_via_api(pr_number):
    """Fetch changed files in a PR using GitHub REST API."""
    print(f"🔍 Getting changed files for PR #{pr_number} using REST API...")
    
    repo = os.getenv("GITHUB_REPOSITORY")  # example: "user/repo"
    token = os.getenv("GITHUB_TOKEN")  # personal access token or GitHub Actions token
    
    if not repo or not token:
        print("❌ Missing GITHUB_REPOSITORY or GITHUB_TOKEN environment variables.")
        return []
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    
    changed_files = []
    page = 1

    while True:
        response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
        if response.status_code != 200:
            print(f"❌ Failed to fetch changed files: {response.status_code} {response.text}")
            return []
        
        files = response.json()
        if not files:
            break
        
        changed_files.extend(file["filename"] for file in files)
        page += 1

    return changed_files

def get_changed_api_folders(changed_files):
    """Identify which API subfolders have changes."""
    changed_folders = set()
    for file_path in changed_files:
        if file_path.startswith("APIs/"):
            parts = file_path.split('/')
            if len(parts) >= 2:
                changed_folders.add(parts[1])

    return list(changed_folders)


def run_coverage_tests(changed_folders):
    """Run coverage tests for changed folders."""
    api_status = {}
    failure = False
    

    for folder in changed_folders:
        source_folder = f"APIs/{folder}"
        
        status = os.system(f"""coverage run --source={source_folder} --parallel-mode --omit="APIs/*/tests/*,/tmp*/*,**/m01/*" -m pytest {source_folder}""")
        api_status[folder] = status

    
    for api,status in api_status.items():
        if status != 0:
            failure = True
            print(f"❌ tests failed for {api}.")
    
    if failure:
        raise Exception(
            """
            ❌ Coverage tests failed for one or more APIs.
            """
            )
    else:
        print("✅ Coverage tests passed for the APIs.")

    os.system("coverage combine")
    os.system("coverage report")
    os.system("coverage xml -o .coverage.xml")


if __name__ == "__main__":
    pr_number = os.getenv("PR_NUMBER")
    changed_files = get_changed_files_via_api(pr_number)
    changed_folders = sorted(get_changed_api_folders(changed_files))
    
    if changed_folders:
        run_coverage_tests(changed_folders)
    else:
        print("No changed files found.")
