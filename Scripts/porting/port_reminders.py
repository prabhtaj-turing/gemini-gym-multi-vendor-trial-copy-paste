import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

from generic_reminders.SimulationEngine.models import ReminderModel
BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "reminders"

def port_generic_reminder_db(source_json_str, output_path: str | None = None):
    """
    Ports a vendor Generic Reminders DB to match the default DB schema.
    Does not rely on SimulationEngine; just merges keys and clears missing ones.
    """
    default_db_path = Path("DBs/GenericRemindersDefaultDB.json")

    # Load default DB
    with open(default_db_path) as f:
        default_db = json.load(f)

    # Load vendor/source DB
    source_db = json.loads(source_json_str, strict=False)

    # Merge keys from source, keeping defaults for missing keys
    for key in default_db.keys():
        if key in source_db:
            default_db[key] = source_db[key]
        else:
            # clear lists if key is missing in source
            if isinstance(default_db[key], list):
                default_db[key].clear()
            elif isinstance(default_db[key], dict):
                default_db[key] = {}
    
    # Validate each reminder
    for rid, reminder in default_db.get("reminders", {}).items():
        if "uri" not in reminder: #Patching done, as uri is mandatory parameter in schema
            reminder["uri"] = f"reminder://{rid}"
        try:
            ReminderModel(**reminder)
        except Exception as e:
            raise ValueError(f"Validation failed for reminder {rid}: {e}")

    if output_path:
        out_path = Path(output_path)
        out_path.write_text(json.dumps(default_db, indent=2), encoding="utf-8")

    return default_db

if __name__ == "__main__":
    if not sys.stdin.isatty():
        # Read raw JSON from stdin
        raw_input = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:
        # Fallback to local file
        reminder_path = BASE_PATH / "vendor_reminders.json"
        raw_input = reminder_path.read_text()
        output_path = BASE_PATH / "final_vendor_reminders.json"

    # Port the DB
    ported_db = port_generic_reminder_db(raw_input, output_path)

    # Optional: print summary
    print("Ported Generic Reminders DB keys:", list(ported_db.keys()))