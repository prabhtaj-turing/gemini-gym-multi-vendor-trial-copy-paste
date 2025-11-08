import os
import json
import requests
import zipfile
import shutil
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

FOLDER_CONFIGS = {
    "APIs/": "",
    "DefaultDBs/": "1JOECDyxovCbZZx_-jfTETbbEQz4V30kp"
}

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
    requirements_file = False
    default_dbs = list()
    for file_path in changed_files:
        if os.path.basename(file_path) == "requirements.txt":
            requirements_file = True
        elif file_path.startswith("APIs/"):
            parts = file_path.split('/')
            if len(parts) >= 2:
                changed_folders.add(parts[1])
        elif file_path.startswith("DefaultDBs/"):
            default_dbs.append(file_path)

    return list(changed_folders), requirements_file, default_dbs


def authenticate():
    """Authenticate using service account."""
    creds_dict = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def create_folder_in_drive(service, parent_folder_id, folder_name):
    """Create a folder in Drive inside parent folder."""
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    created_folder = service.files().create(body=folder_metadata, fields='id').execute()
    return created_folder['id']

def upload_file_to_drive(service, parent_folder_id, file_path):
    """Upload a single file to Drive inside parent folder."""
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [parent_folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()

def upload_local_folder_to_drive(service, local_folder_path, drive_folder_id):
    """Upload a local folder recursively into a Drive folder."""
    if not os.path.isdir(local_folder_path):
        raise ValueError(f"The provided path '{local_folder_path}' is not a valid directory.")

    local_folder_path = os.path.abspath(local_folder_path)
    path_to_drive_id = {local_folder_path: drive_folder_id}

    for root, dirs, files in os.walk(local_folder_path):
        current_drive_parent_id = path_to_drive_id[root]

        # Create subfolders in Drive
        for directory in dirs:
            local_dir_path = os.path.join(root, directory)
            drive_folder = create_folder_in_drive(service, current_drive_parent_id, directory)
            path_to_drive_id[local_dir_path] = drive_folder

        # Upload files in current folder
        for file in files:
            file_path = os.path.join(root, file)
            upload_file_to_drive(service, current_drive_parent_id, file_path)

def delete_api_folder(service, folder_name, parent_folder_id):
    """Find and delete an existing API folder by name under a parent."""
    query = (
        f"'{parent_folder_id}' in parents and "
        f"name = '{folder_name}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    results = service.files().list(q=query, spaces='drive', fields="files(id)").execute()
    folders = results.get('files', [])
    
    if folders:
        folder_id = folders[0]['id']
        print(f"🗑️ Deleting existing folder '{folder_name}' from Drive...")
        service.files().update(fileId=folder_id, body={'trashed': True}).execute()
    else:
        print(f"ℹ️ No existing folder '{folder_name}' found to delete.")

def create_api_folder(service, folder_name, parent_folder_id):
    """Create a new API folder under a parent and return its ID."""
    print(f"📁 Creating new folder '{folder_name}' in Drive...")
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    created_folder = service.files().create(body=folder_metadata, fields='id').execute()
    return created_folder['id']

def update_requirements_in_drive(service):
    local_path = 'requirements.txt'
    drive_id = '1U_iArhQahn6jvf8P2SPnl0wzF665LeJT'

    query = f"'{drive_id}' in parents and name = '{local_path}' and trashed = false"
    result = service.files().list(q=query, fields="files(id, parents)").execute()
    existing_files = result.get("files", [])

    if existing_files:
        for file in existing_files:
          try:
            media = MediaFileUpload(local_path, resumable=True)
            # Perform the update - ADD supportsAllDrives=True
            updated_file = service.files().update(
                fileId=file['id'],
                media_body=media,
                supportsAllDrives=True,  # <<< ADDED THIS PARAMETER
                fields='id, name'
            ).execute()
            print(f"⬆️ updated: {local_path}")
          except Exception as e:
              print(f"⚠️ Cannot update {local_path}: {e}")
    else:
      try:
          metadata = {"name": local_path, "parents": [drive_id]}
          media = MediaFileUpload(local_path, resumable=True)
          service.files().create(body=metadata, media_body=media, fields="id").execute()
          print(f"new file found, Created {local_path} in Drive")
      except Exception as e:
          print(f"⚠️ Cannot create {local_path}: {e}")

def update_db_in_drive(service, local_path):
    
    drive_id = FOLDER_CONFIGS['DefaultDBs/']

    file_name = os.path.basename(local_path)

    query = f"'{drive_id}' in parents and name = '{file_name}' and trashed = false"
    result = service.files().list(q=query, fields="files(id, parents)").execute()
    existing_files = result.get("files", [])

    if existing_files:
        for file in existing_files:
          try:
            media = MediaFileUpload(local_path, resumable=True)
            # Perform the update - ADD supportsAllDrives=True
            updated_file = service.files().update(
                fileId=file['id'],
                media_body=media,
                supportsAllDrives=True,  # <<< ADDED THIS PARAMETER
                fields='id, name'
            ).execute()
            print(f"⬆️ updated: {local_path}")
          except Exception as e:
              print(f"⚠️ Cannot update {local_path}: {e}")
    else:
      try:
          metadata = {"name": file_name, "parents": [drive_id]}
          media = MediaFileUpload(local_path, resumable=True)
          service.files().create(body=metadata, media_body=media, fields="id").execute()
          print(f"new file found, Created {file_name} in Drive")
      except Exception as e:
          print(f"⚠️ Cannot create {file_name}: {e}")

def update_zip_in_drive(service, local_path):

    drive_id = FOLDER_CONFIGS['APIs/']
    file_id = '115OmIIgGza9K2FewVcQ4yTHSrVVpSOi9'
    file_name = os.path.basename(local_path)

    existing_file = service.files().get(fileId=file_id, fields="id, parents").execute()

    if existing_file:
        try:
          media = MediaFileUpload(local_path, resumable=True)
          # Perform the update - ADD supportsAllDrives=True
          updated_file = service.files().update(
              fileId=file_id,
              media_body=media,
              supportsAllDrives=True,  # <<< ADDED THIS PARAMETER
              fields='id, name'
          ).execute()
          print(f"⬆️ updated: {file_name}")
        except Exception as e:
            print(f"⚠️ Cannot update {file_name}: {e}")
    else:
      print(f"⚠️ Cannot find {file_name} with id: {file_id} in Drive")


def zip_APIs_for_Drive(output_zip_path):
    """
    Moves requirements.txt to APIs/ and zips APIs and DefaultDBs folders into a zip.
    """
    root_folder_path = './'
    apis_folder_path = os.path.join(root_folder_path, 'APIs')
    requirements_file = os.path.join(root_folder_path, 'requirements.txt')
    destination_file = os.path.join(apis_folder_path, 'requirements.txt')

    # Move requirements.txt into APIs if it exists
    if os.path.exists(requirements_file):
        shutil.move(requirements_file, destination_file)

    included_folders = ['APIs']

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder in included_folders:
            folder_path = os.path.join(root_folder_path, folder)
            for root, _, files in os.walk(folder_path):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, start=root_folder_path)
                    zipf.write(abs_path, arcname=rel_path)
    
    shutil.move(destination_file, requirements_file)






if __name__ == "__main__":
    pr_number = os.getenv("PR_NUMBER")
    if not pr_number:
        print("❌ PR number not found in environment.")
        exit(1)

    changed_files = get_changed_files_via_api(pr_number)
    if not changed_files:
        print("🟡 No changes detected in PR.")
        exit(0)

    changed_api_folders, requirements_txt, default_dbs = get_changed_api_folders(changed_files)

    service = authenticate()

    if changed_api_folders or requirements_txt:
        zip_file = 'APIs.zip'

        zip_APIs_for_Drive(zip_file)
        update_zip_in_drive(service, zip_file)

    if default_dbs:
        for db in default_dbs:
            update_db_in_drive(service,db)
