import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

from media_control.SimulationEngine.db_models import MediaPlayer
BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "media_control"

def normalize_media_type(value: str) -> str:
    """Map vendor media_type strings to schema-compatible values."""
    mapping = {
        "AUDIOBOOK": "AUDIO_BOOK",   # vendor → schema
        "PODCAST": "PODCAST_SERIES", # example
        # add other normalizations as needed
    }
    return mapping.get(value, value)  # fallback to original if no mapping

def port_media_control_db(source_json_str, output_path: str | None = None):

    default_db_path = Path("DBs/MediaControlDefaultDB.json")
    with open(default_db_path) as f:
        defaultdb = json.load(f)

    # Parse vendor JSON
    source_db = json.loads(source_json_str, strict=False)

    # Overwrite active player
    defaultdb['active_media_player'] = source_db.get(
        'active_media_player', defaultdb.get('active_media_player')
    )

    # Merge media players while preserving default apps
    merged_players = defaultdb.get('media_players', {}).copy()
    vendor_players = source_db.get('media_players', {})
    merged_players.update(vendor_players)

    for app_name, app_data in merged_players.items():
        # Normalize current_media if present
        current = app_data.get("current_media")
        if current and isinstance(current, dict) and "media_type" in current:
            current["media_type"] = normalize_media_type(current["media_type"])

        # Normalize playlist items safely
        playlist = app_data.get("playlist") or []
        for item in playlist:
            if isinstance(item, dict) and "media_type" in item:
                item["media_type"] = normalize_media_type(item["media_type"])

        # Validate each app individually
        try:
            MediaPlayer(**app_data)  # if whole DB is validated at once
            # OR: MediaAppModel(**app_data) if your schema allows per-app validation
        except Exception as e:
            raise ValueError(f"Validation failed for {app_name}: {e}")

    defaultdb['media_players'] = merged_players
    
    # Persist to file if needed
    if output_path:
        out_path = Path(output_path)
        out_path.write_text(json.dumps(defaultdb, indent=2), encoding="utf-8")

    return defaultdb

if __name__ == "__main__":
    if not sys.stdin.isatty():
        raw_input = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:
        media_path = BASE_PATH / "vendor_media_control.json"
        raw_input = media_path.read_text()
        output_path = BASE_PATH / "final_vendor_media_control.json"

    ported_db = port_media_control_db(raw_input, output_path)
    print("Ported Media Control DB loaded successfully.")