from datetime import datetime
import sys
import json
from pathlib import Path
from Scripts.porting.helpers import validate_with_default_schema
BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "clock_transform"

# ================================
# Helper Functions
# ================================


def build_template(structure):
    """Recursively builds a template from the default DB's structure."""
    if isinstance(structure, dict):
        return {k: build_template(v) for k, v in structure.items()}
    elif isinstance(structure, list):
        if structure and isinstance(structure[0], dict):
            return [build_template(structure[0])]
        else:
            return []
    else:
        if isinstance(structure, str):
            return ""
        elif isinstance(structure, bool):
            return False
        elif isinstance(structure, int):
            return 0
        elif isinstance(structure, float):
            return 0.0
        else:
            return None


def deep_merge(template, data):
    """Recursively merges template and vendor data."""
    if isinstance(template, dict) and isinstance(data, dict):
        merged = {}
        for key in template:
            merged[key] = deep_merge(
                template[key], data.get(key, template[key]))
        return merged
    elif isinstance(template, list) and isinstance(data, list):
        if template and isinstance(template[0], dict):
            return [deep_merge(template[0], item) for item in data]
        else:
            return data
    else:
        return data if data is not None else template

# ================================
# Main Porting Function
# ================================


def port_clock_db(source_json_str: str, file_path: str | None = None):
    """Normalizes any vendor clock DB to match the default DB schema."""
    default_db_path = Path("DBs/ClockDefaultDB.json")

    if default_db_path.exists():
        with default_db_path.open() as f:
            default_db = json.load(f)
    else:
        default_db = {}  # fallback empty DB

    try:
        vendor_db = json.loads(source_json_str, strict=False) if isinstance(
            source_json_str, str) else source_json_str
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return None, f"Invalid input: {str(e)}"

    schema_template = build_template(default_db)
    ported_clock_db = deep_merge(schema_template, vendor_db)

    # Ensure ported_clock_db is a dict before processing
    if not isinstance(ported_clock_db, dict):
        return None, f"Invalid data structure: expected dict, got {type(ported_clock_db).__name__}"

    # Fix timer start_time if missing
    for _, timer in ported_clock_db.get("timers", {}).items():
        if timer.get("created_at") and not timer.get("start_time"):
            timer["start_time"] = timer.get("created_at")
        elif not timer.get("start_time"):
            timer["start_time"] = datetime.now().isoformat()

    status, message = validate_with_default_schema(
        "clock.SimulationEngine.models", ported_clock_db)

    if file_path and status:
        out_path = Path(file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(
            ported_clock_db, indent=2), encoding="utf-8")
        print(f"Output written to: {out_path.resolve()}")

    if not status:
        return None, message

    return ported_clock_db, message

# ================================
# CLI / Fallback Handling
# ================================


if __name__ == "__main__":
    if not sys.stdin.isatty():
        # read raw string from stdin
        raw = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:
        vendor_path = BASE_PATH / "vendor_clock_transform.json"
        raw = vendor_path.read_text()
        output_path = BASE_PATH / "ported_final_clock_transform.json"

    db, msg = port_clock_db(raw, output_path)
