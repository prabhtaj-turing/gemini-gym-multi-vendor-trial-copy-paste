from common_utils.print_log import print_log
# zendesk/SimulationEngine/db.py

import json
import os
# ------------------------------------------------------------------------------
# Global In-Memory Database (JSON-serializable)
# ------------------------------------------------------------------------------
# Original core collections (PRESERVED - DO NOT MODIFY)
DB = {"tickets": {}, "users": {}, "organizations": {}}

# Initialize additional collections for enhanced functionality (ADDITIVE ONLY)
def _initialize_enhanced_collections():
    """
    Initialize additional collections needed for enhanced API functionality.
    This function only ADDS new collections without modifying existing ones.
    """
    # Add new collections only if they don't exist
    if "comments" not in DB:
        DB["comments"] = {}
    if "attachments" not in DB:
        DB["attachments"] = {}
    if "upload_tokens" not in DB:
        DB["upload_tokens"] = {}
    if "ticket_audits" not in DB:
        DB["ticket_audits"] = {}
    if "search_index" not in DB:
        DB["search_index"] = {"tickets": {}, "users": {}, "organizations": {}}
    
    # Placeholder collections for future expansion
    if "groups" not in DB:
        DB["groups"] = {}
    if "macros" not in DB:
        DB["macros"] = {}
    if "custom_field_definitions" not in DB:
        DB["custom_field_definitions"] = {}
    
    # ID counters - only add if they don't exist (preserve existing values)
    if "next_ticket_id" not in DB:
        DB["next_ticket_id"] = 1
    if "next_user_id" not in DB:
        DB["next_user_id"] = 100
    if "next_organization_id" not in DB:
        DB["next_organization_id"] = 1
    if "next_audit_id" not in DB:
        DB["next_audit_id"] = 1
    if "next_comment_id" not in DB:
        DB["next_comment_id"] = 1
    if "next_attachment_id" not in DB:
        DB["next_attachment_id"] = 1
    if "next_upload_token_id" not in DB:
        DB["next_upload_token_id"] = 1

# Initialize enhanced collections at module import
_initialize_enhanced_collections()


# ------------------------------------------------------------------------------
# Save and Load State
# ------------------------------------------------------------------------------
def save_state(filepath: str) -> None:
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> None:
    """
    Loads data from a JSON file into the global DB dictionary.
    """
    global DB
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                loaded_data = json.load(f)
            DB.update(loaded_data) # Merge loaded data into existing DB
            print_log(f"INFO: DB state loaded from {filepath} into the global DB.")
        except json.JSONDecodeError as e:
            print_log(f"ERROR: Invalid JSON in DB state file {filepath}: {e}. DB not loaded.")
        except IOError as e:
            print_log(f"ERROR: Failed to read DB state file {filepath}: {e}. DB not loaded.")
    else:
        print_log(f"INFO: DB state file not found at {filepath}. DB remains in its current state.")




def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
