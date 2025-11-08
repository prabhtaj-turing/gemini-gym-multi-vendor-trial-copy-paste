import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from mongomock import MongoClient
from pymongo.errors import OperationFailure, CollectionInvalid
from bson import json_util, ObjectId

class MongoDB:
    def __init__(self, state_file: str = "db_state.json"):
        self.state_file = Path(state_file)
        self.connections: Dict[str, MongoClient] = {}  # Key: connection name
        self.current_conn: str = None  # Active connection name
        self.current_db: str = None    # Active database name

    def switch_connection(self, conn_string: Optional[str] = None):
        """Switch to a connection or create a new one if it doesn't exist.
        
        Args:
            conn_string: Connection string identifier, creates a default if None
        """
        conn_name = conn_string or "default"
        if conn_name not in self.connections:
            # Create a new connection
            self.connections[conn_name] = MongoClient()
        
        self.current_conn = conn_name
        return {"status": "success", "message": f"Switched to connection: {conn_name}"}

    def use_database(self, db_name: str):
        """Set active database for the current connection."""
        if not self.current_conn:
            raise ValueError("No active connection.")
        self.current_db = db_name
        return self.connections[self.current_conn][db_name]


# Create global DB instance
DB = MongoDB()


def load_state(state_file: str = "db_state.json"):
    """Load connections, databases, and collections from JSON."""
    file_path = Path(state_file)
    if not file_path.exists():
        return

    with open(file_path, "r") as f:
        state = json.load(f, object_hook=json_util.object_hook)

    for conn_name, conn_data in state.get("connections", {}).items():
        client = MongoClient()
        for db_name, db_data in conn_data.get("databases", {}).items():
            db = client[db_name]
            for coll_name, coll_data in db_data.get("collections", {}).items():
                coll = db.create_collection(coll_name)
                if coll_data.get("documents"):
                    coll.insert_many(coll_data.get("documents", []))
                # Create indexes
                for index in coll_data.get("indexes", []):
                    coll.create_index(
                        [tuple(field) for field in index["key"]],
                        **index.get("options", {})
                    )
        DB.connections[conn_name] = client

    if DB.connections:
        DB.current_conn = next(iter(DB.connections.keys()))


def save_state(state_file: str = "db_state.json"):
    """Save all connections and their states to JSON."""
    state = {"connections": {}}
    for conn_name, client in DB.connections.items():
        conn_state = {"databases": {}}
        for db_name in client.list_database_names():
            db = client[db_name]
            conn_state["databases"][db_name] = {"collections": {}}
            for coll_name in db.list_collection_names():
                coll = db[coll_name]
                conn_state["databases"][db_name]["collections"][coll_name] = {
                    "documents": list(coll.find({})),
                    "indexes": [
                        {"key": idx["key"], "options": idx.get("options", {})}
                        for idx in coll.index_information().values()
                    ],
                    "metadata": {
                        "storage_size_mb": len(json_util.dumps(list(coll.find({})))) / 1e6
                    }
                }
        state["connections"][conn_name] = conn_state

    with open(state_file, "w") as f:
        json.dump(state, f, default=json_util.default, indent=2)


# Initialize the DB by loading the state
load_state(DB.state_file)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
