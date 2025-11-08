import json, sys
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))
from notes_and_lists.SimulationEngine.models import NotesAndListsDB
from notes_and_lists.SimulationEngine.utils import update_title_index, update_content_index
from notes_and_lists.SimulationEngine import utils
BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "notes_lists"

def _to_iso_z(ts: str | None) -> str:
    """Normalize 'YYYY-MM-DDTHH:MM:SS' -> 'YYYY-MM-DDTHH:MM:SSZ'."""
    if not ts or not isinstance(ts, str):
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if ts.endswith("Z") or "+" in ts:
        return ts
    return f"{ts}Z"

def port_notes_and_lists_db(source_json_str: str, output_path: str | None = None) -> dict:
    # Create a clean DB shell
    db: dict = {
        "notes": {},
        "lists": {},
        "operation_log": {},
        "title_index": {},
        "content_index": {},
    }

    src: dict = json.loads(source_json_str)

    # Migrate NOTES
    notes_block = src.get("notes", {})
    if isinstance(notes_block, dict):
        for note_key, note in notes_block.items():
            if not isinstance(note, dict):
                continue
            nid = note.get("id", note_key)
            title = note.get("title")
            content = note.get("content", "") or ""
            created_at = _to_iso_z(note.get("created_at"))
            updated_at = _to_iso_z(note.get("updated_at"))
            content_history = note.get("content_history")
            if not isinstance(content_history, list):
                content_history = []

            db["notes"][nid] = {
                "id": nid,
                "title": title,
                "content": content,
                "created_at": created_at,
                "updated_at": updated_at,
                "content_history": content_history,
            }

    # Migrate LISTS
    lists_block = src.get("lists", {})
    if isinstance(lists_block, dict):
        for list_key, lst in lists_block.items():
            if not isinstance(lst, dict):
                continue
            lid = lst.get("id", list_key)
            title = lst.get("title")
            created_at = _to_iso_z(lst.get("created_at"))
            updated_at = _to_iso_z(lst.get("updated_at"))
            item_history = lst.get("item_history")
            if not isinstance(item_history, dict):
                item_history = {}

            items_dict: dict = {}
            raw_items = lst.get("items", {})
            if isinstance(raw_items, dict):
                for item_key, item in raw_items.items():
                    if not isinstance(item, dict):
                        continue
                    iid = item.get("id", item_key)
                    items_dict[iid] = {
                        "id": iid,
                        "content": item.get("content", "") or "",
                        "created_at": _to_iso_z(item.get("created_at")),
                        "updated_at": _to_iso_z(item.get("updated_at")),
                    }

            db["lists"][lid] = {
                "id": lid,
                "title": title,
                "items": items_dict,
                "created_at": created_at,
                "updated_at": updated_at,
                "item_history": item_history,
            }

    utils.DB = db
    # Rebuild indexes
    for nid, note in db["notes"].items():
        update_title_index(note.get("title"), nid)
        update_content_index(nid, note.get("content", ""))

    for lid, lst in db["lists"].items():
        update_title_index(lst.get("title"), lid)
        for item in lst.get("items", {}).values():
            update_content_index(item["id"], item.get("content", ""))
    
    validate = NotesAndListsDB(**db)

    # Persist to file if needed
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(db, indent=2), encoding="utf-8")
    return db

# ============================
# Optional main for stdin/fallback
# ============================
if __name__ == "__main__":
    if not sys.stdin.isatty():
        raw_input = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:
        default_path = BASE_PATH / "vendor_notes_lists.json"
        raw_input = default_path.read_text()
        output_path = BASE_PATH / "final_vendor_notes_list.json"

    ported_db = port_notes_and_lists_db(raw_input, output_path)
    print(ported_db)
    