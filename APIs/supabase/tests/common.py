# tests/common.py
from ..SimulationEngine.db import DB


def reset_db():
    new_db = {
        "organizations": [],
        "projects": [],
        "tables": {},
        "extensions": {},
        "migrations": {},
        "edge_functions": {},
        "branches": {},
        "costs": {},
        "unconfirmed_costs": {},
        "project_urls": {},
        "project_anon_keys": {},
        "project_ts_types": {},
        "logs": {}
    }
    DB.clear()
    DB.update(new_db)
