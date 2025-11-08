import json
import os
from .models import GitHubDB
from pydantic import ValidationError

try:
    from common_utils.ErrorSimulation import ErrorSimulator
except ImportError:
    from common_utils import ErrorSimulator


DB = {
    "CurrentUser": {"login": "default_user", "id": 0},
    "Users": [],
    "Repositories": [],
    "RepositoryCollaborators": [],
    "RepositoryLabels": [],
    "Milestones": [],
    "Issues": [],
    "IssueComments": [],
    "PullRequests": [],
    "PullRequestReviewComments": [],
    "PullRequestReviews": [],
    "Commits": [],
    "Branches": [],
    "BranchCreationDetailsCollection": [],
    "PullRequestFilesCollection": [],
    "CodeSearchResultsCollection": [],
    "CodeScanningAlerts": [],
    "SecretScanningAlerts": [],
    "CommitCombinedStatuses": [],
    "FileContents": {},
}


def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.

    Args:
        filepath: Path to save the state file.
    """
    import json
    from datetime import datetime
    from .utils import _to_iso_string
    
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return _to_iso_string(obj)
            return super().default(obj)
    
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2, cls=DateTimeEncoder)


def _validate_db_state(db_obj):
    """Validate the database state against the Pydantic model."""
    try:
        GitHubDB.model_validate(db_obj)
    except ValidationError as e:
        print(f"Database validation failed: {e}")
        raise

# with open("git.json", "r", encoding="utf-8") as f:
#     db_data = json.load(f)
# github_db_instance = GitHubDB(**db_data)


def load_state(filepath: str):
    """Load database state from a file."""
    global DB
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Clear the existing DB and update it
            DB.clear()
            DB.update(data)
            _validate_db_state(DB)
    except FileNotFoundError:
        # File doesn't exist, skip loading
        pass

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    return DB

def reset_db():
    """Reset database to its initial valid, empty state."""
    global DB
    DB.clear()
    DB.update({
        "CurrentUser": {"login": "default_user", "id": 0},
        "Users": [],
        "Repositories": [],
        "RepositoryCollaborators": [],
        "RepositoryLabels": [],
        "Milestones": [],
        "Issues": [],
        "IssueComments": [],
        "PullRequests": [],
        "PullRequestReviewComments": [],
        "PullRequestReviews": [],
        "Commits": [],
        "Branches": [],
        "BranchCreationDetailsCollection": [],
        "PullRequestFilesCollection": [],
        "CodeSearchResultsCollection": [],
        "CodeScanningAlerts": [],
        "SecretScanningAlerts": [],
        "CommitCombinedStatuses": [],
        "FileContents": {},
    })


# Load default data if available

def load_default_data():

    """Load default database from DBs directory"""

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "DBs",
        "GithubDefaultDB.json"
    )

    if os.path.exists(db_path):
        load_state(db_path)


# Initialize with default data
load_default_data()  # Commented out - call explicitly when needed