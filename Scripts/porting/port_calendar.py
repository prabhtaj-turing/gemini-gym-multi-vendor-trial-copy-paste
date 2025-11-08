import json, sys
from datetime import datetime
from pathlib import Path
from Scripts.porting.helpers import validate_with_default_schema, local_to_UTC
from Scripts.porting.calendar_helpers import validate_google_calendar_datetime
from Scripts.porting.custom_errors import DateTimeValidationError

BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "calendar"

def port_calendar(raw_json: str, file_path: str | None = None):
    """
    Port vendor calendar JSON into our canonical CalendarDefaultDB schema.
    """

    try:
        given_json = json.loads(raw_json)
    except Exception as e:
        return None, f"Invalid JSON input: {e}"

    # Use the same normalization as models.EventDateTimeModel
    # Now using local calendar_helpers instead of common_utils.datetime_utils

    # --- Normalize calendars ---
    calendars = given_json.get("calendars", {})
    if not any(cal_data.get("primary") for cal_data in calendars.values()):
        for i, (cal_id, cal_data) in enumerate(calendars.items()):
            # First calendar is primary
            cal_data["primary"] = (i == 0)

    # --- ACL rules, channels, colors ---
    acl_rules = given_json.get("acl_rules", {})
    channels = given_json.get("channels", {})
    colors = given_json.get("colors", {})

    # --- Normalize events ---
    events = given_json.get("events", {})

    for key, event in events.items():
        if not isinstance(event, dict):
            return None, f"Invalid event structure for key '{key}': expected object"
        for time_key in ("start", "end"):
            if time_key not in event or not isinstance(event[time_key], dict):
                return None, f"Missing or invalid '{time_key}' for event '{key}'"
            if "dateTime" not in event[time_key] and "date" not in event[time_key]:
                return None, f"Invalid format for event '{key}': '{time_key}' must include 'dateTime' or 'date' for event '{key}'"
            if "dateTime" in event[time_key] and "date" in event[time_key]:
                return None, f"Invalid format for event '{key}': '{time_key}' must include only one of 'dateTime' or 'date' for event '{key}'"
            if "date" in event[time_key]:
                # Convert all-day dates to full-day datetime
                tz_present = bool(event[time_key].get("timeZone"))
                if time_key == "start":
                    event[time_key]["dateTime"] = event[time_key]["date"] + ("T00:00:00" + ("" if tz_present else "Z"))
                elif time_key == "end":
                    event[time_key]["dateTime"] = event[time_key]["date"] + ("T23:59:59" + ("" if tz_present else "Z"))
                event[time_key].pop("date", None)
            # Normalize to Google Calendar datetime format using shared validator
            try:
                normalized_dt, normalized_tz = validate_google_calendar_datetime(
                    event[time_key].get("dateTime"),
                    event[time_key].get("timeZone"),
                )
                event[time_key]["dateTime"] = normalized_dt
                if normalized_tz is not None:
                    event[time_key]["timeZone"] = normalized_tz
                else:
                    event[time_key].pop("timeZone", None)
            except DateTimeValidationError as e:
                return None, f"Invalid format for event '{key}' field '{time_key}': {e}"

            event[time_key] = local_to_UTC(event[time_key])

        # Ensure both start and end now have dateTime
        if "start" not in event or "end" not in event or "dateTime" not in event["start"] or "dateTime" not in event["end"]:
            return None, f"Event '{key}' must include both start.dateTime and end.dateTime"

        # Ensure end is not before start
        def _parse_iso_utc(dt: str) -> datetime | None:
            try:
                # Support trailing 'Z'
                if dt.endswith("Z"):
                    dt = dt[:-1] + "+00:00"
                return datetime.fromisoformat(dt)
            except Exception:
                return None

        start_dt = _parse_iso_utc(event["start"]["dateTime"])
        end_dt = _parse_iso_utc(event["end"]["dateTime"])
        if start_dt is None or end_dt is None:
            return None, f"Unable to parse start/end datetime for event '{key}'"
        if end_dt < start_dt:
            return None, f"Event '{key}' has end before start"

    ported_db = {
        "calendars": calendars,
        "calendar_list": calendars,
        "acl_rules": acl_rules,
        "channels": channels,
        "colors": colors,
        "events": events  # keep colon-separated string keys
    }
    status, message = validate_with_default_schema("google_calendar.SimulationEngine.models",ported_db)

    # --- Save ported JSON to variable path---
    if file_path and status:
        out_path = Path(file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(ported_db, indent=2), encoding="utf-8")
        print(f"Output written to: {out_path.resolve()}")

    if not status:
        return None, message
    return ported_db, message


if __name__ == "__main__":
    # Example usage with vendor file
    if not sys.stdin.isatty():
        # read raw string from stdin
        raw = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:   
        vendor_path = BASE_PATH / "vendor_calendar.json"
        raw = vendor_path.read_text()
        output_path = BASE_PATH / "ported_final_calendar.json"
    
    db, msg = port_calendar(raw, output_path)
    print(db)
