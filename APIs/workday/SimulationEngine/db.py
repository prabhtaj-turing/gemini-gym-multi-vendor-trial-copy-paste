"""
Database structure and persistence helpers for Workday Strategic Sourcing API Simulation.
"""

import json
from typing import Dict, Any
import os

# ---------------------------------------------------------------------------------------
# In-Memory Database Structure
# ---------------------------------------------------------------------------------------
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "WorkdayStrategicSourcingDefaultDB.json",
)

DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB.update(json.load(f))

# -------------------------------------------------------------------
# Persistence Helpers
# -------------------------------------------------------------------
def save_state(filepath: str) -> None:
    """Saves the current state of the API to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> object:
    """Loads the API state from a JSON file."""
    try:
        with open(filepath, "r") as f:
            state = json.load(f)
        # For backward compatibility, merge loaded data with existing DB structure
        global DB
        if state:  # Only update if we have valid data
            for key, value in state.items():
                if key in DB and isinstance(DB[key], dict) and isinstance(value, dict):
                    DB[key].update(value)
                else:
                    DB[key] = value
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def reset_db():
    """Reset database to initial state"""
    global DB
    # Ensure DB is always reset to the exact initial structure
    DB.clear()
    DB.update({
        'attachments': {},
        'awards': {'award_line_items': [], 'awards': []},
        'contracts': {'award_line_items': [],
                    'awards': {},
                    'contract_types': {},
                    'contracts': {}},
        'events': {'bid_line_items': {},
                    'bids': {},
                    'event_templates': {},
                    'events': {},
                    'line_items': {},
                    'worksheets': {}},
        'fields': {'field_groups': {}, 'field_options': {}, 'fields': {}},
        'payments': {'payment_currencies': [],
                    'payment_currency_id_counter': "",
                    'payment_term_id_counter': "",
                    'payment_terms': [],
                    'payment_type_id_counter': "",
                    'payment_types': []},
        'projects': {'project_types': {}, 'projects': {}},
        'reports': {'contract_milestone_reports_entries': [],
                    'contract_milestone_reports_schema': {},
                    'contract_reports_entries': [],
                    'contract_reports_schema': {},
                    'event_reports': [],
                    'event_reports_1_entries': [],
                    'event_reports_entries': [],
                    'event_reports_schema': {},
                    'performance_review_answer_reports_entries': [],
                    'performance_review_answer_reports_schema': {},
                    'performance_review_reports_entries': [],
                    'performance_review_reports_schema': {},
                    'project_milestone_reports_entries': [],
                    'project_milestone_reports_schema': {},
                    'project_reports_1_entries': [],
                    'project_reports_entries': [],
                    'project_reports_schema': {},
                    'savings_reports_entries': [],
                    'savings_reports_schema': {},
                    'supplier_reports_entries': [],
                    'supplier_reports_schema': {},
                    'supplier_review_reports_entries': [],
                    'supplier_review_reports_schema': {},
                    'suppliers': []},
        'scim': {'resource_types': [],
                'schemas': [],
                'service_provider_config': {},
                'users': []},
        'spend_categories': {},
        'suppliers': {'contact_types': {},
                    'supplier_companies': {},
                    'supplier_company_segmentations': {},
                    'supplier_contacts': {}}
    }) 



def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
