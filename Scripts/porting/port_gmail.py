import json, sys
import uuid
import re
import calendar
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel, EmailStr, ValidationError
from Scripts.porting.helpers import validate_with_default_schema

# Timezone handling - try zoneinfo first (Python 3.9+), fallback to basic UTC handling
try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False
    class ZoneInfo:
        def __init__(self, key):
            self.key = key

ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "gmail"
DB_PATH = Path(__file__).resolve().parent.parent.parent / "DBs" / "GmailDefaultDB.json"

# Pydantic email validator model
class EmailValidator(BaseModel):
    email: EmailStr

def validate_email(email: str) -> bool:
    """Validate email address format using Pydantic EmailStr."""
    if not isinstance(email, str):
        return False
    
    try:
        EmailValidator(email=email.strip())
        return True
    except (ValidationError, ValueError):
        return False

def validate_datetime_format(date_str: str) -> bool:
    """Validate datetime string format."""
    if not isinstance(date_str, str):
        return False
    if not date_str.strip():
        return False
    
    # Basic ISO format validation
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$'
    return bool(re.match(iso_pattern, date_str.strip()))

def convert_datetime_with_tz(date_str: str, tz_str: str):
    """Convert vendor datetime string with timezone to UTC + epoch string."""
    # Validate input format
    if not validate_datetime_format(date_str):
        raise ValueError(f"Invalid datetime format: {date_str}")
    
    if not isinstance(tz_str, str):
        raise TypeError("Invalid input type: timezone must be string")
    
    # Parse the datetime
    try:
        dt = datetime.fromisoformat(date_str.strip())
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {date_str}") from e
    
    # Handle timezone conversion
    if HAS_ZONEINFO and tz_str.strip():
        try:
            # Convert to UTC if timezone is specified
            if tz_str.strip().upper() == "UTC":
                # Already UTC, just ensure it's timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('UTC'))
            else:
                # Convert from source timezone to UTC
                if dt.tzinfo is None:
                    # Treat as naive datetime in the specified timezone
                    dt = dt.replace(tzinfo=ZoneInfo(tz_str.strip()))
                # Convert to UTC
                dt = dt.astimezone(ZoneInfo('UTC'))
        except Exception:
            # If timezone conversion fails, treat as UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo('UTC'))
    else:
        # Fallback: assume UTC if no timezone support or no zoneinfo
        if dt.tzinfo is None:
            # Create a basic UTC offset mapping for common timezones
            timezone_offsets = {
                'America/New_York': -5,  # EST (winter time)
                'America/Los_Angeles': -8,  # PST (winter time)  
                'Europe/London': 0,  # GMT (winter time)
                'Asia/Tokyo': 9,  # JST
            }
            
            offset_hours = timezone_offsets.get(tz_str.strip(), 0)  # Default to UTC
            # Add offset hours to convert to UTC
            dt = dt + timedelta(hours=-offset_hours)  # Subtract offset to get UTC
    
    # Format to UTC string and epoch
    utc_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    # Calculate epoch timestamp
    if dt.tzinfo:
        epoch_str = str(int(dt.timestamp()))
    else:
        # For naive datetimes, treat as UTC
        epoch_str = str(int(calendar.timegm(dt.timetuple())))
    
    return utc_str, epoch_str


def transform_email_entry(entry: dict) -> dict:
    """Convert a vendor message entry into Gmail schema message."""
    # Validate required fields
    if "id" not in entry:
        raise ValueError("Message missing required field: id")
    
    # Validate sender email if present
    sender = entry.get("sender", "")
    if sender and not validate_email(sender):
        raise ValueError(f"Invalid email format in sender: {sender}")
    
    # Validate recipients
    recipients = entry.get("recipients", [])
    if recipients:
        for recipient in recipients:
            if not validate_email(recipient):
                raise ValueError(f"Invalid email format in recipients: {recipient}")
    
    # Convert datetime with validation
    utc_date, epoch = convert_datetime_with_tz(entry["date"], entry["timeZone"])

    recipients_str = ", ".join(recipients)
    headers = [
        {"name": "From", "value": sender},
        {"name": "To", "value": recipients_str},
        {"name": "Subject", "value": entry.get("subject", "")},
        {"name": "Date", "value": utc_date},
    ]

    raw = f"Subject: {entry.get('subject', '')}\n\n{entry.get('body', '')}"

    return {
        "id": entry["id"],
        "threadId": entry.get("threadId", ""),
        "raw": raw,
        "sender": sender,
        "recipient": recipients_str,
        "subject": entry.get("subject", ""),
        "body": entry.get("body", ""),
        "date": utc_date,
        "internalDate": epoch,
        "isRead": entry.get("isRead", False),
        "labelIds": entry.get("labelIds", []),
        "payload": {
            "mimeType": "text/plain",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": entry.get("body", "")}}
            ],
            "headers": headers,
        },
    }


def normalize_labels(label_list: list[str]) -> dict:
    """Merge system labels with vendor-defined custom labels."""
    labels_dict = {
        "INBOX": {
            "id": "INBOX", "name": "Inbox", "type": "system",
            "labelListVisibility": "labelShow", "messageListVisibility": "show"
        },
        "UNREAD": {
            "id": "UNREAD", "name": "Unread", "type": "system",
            "labelListVisibility": "labelShow", "messageListVisibility": "show"
        },
        "IMPORTANT": {
            "id": "IMPORTANT", "name": "Important", "type": "system",
            "labelListVisibility": "labelShow", "messageListVisibility": "show"
        },
        "SENT": {
            "id": "SENT", "name": "Sent", "type": "system",
            "labelListVisibility": "labelHide", "messageListVisibility": "hide"
        },
        "DRAFT": {
            "id": "DRAFT", "name": "Draft", "type": "system",
            "labelListVisibility": "labelHide", "messageListVisibility": "hide"
        },
        "TRASH": {
            "id": "TRASH", "name": "Trash", "type": "system",
            "labelListVisibility": "labelHide", "messageListVisibility": "hide"
        },
        "SPAM": {
            "id": "SPAM", "name": "Spam", "type": "system",
            "labelListVisibility": "labelHide", "messageListVisibility": "hide"
        },
    }

    for label_name in label_list:
        key = label_name.upper().replace(" ", "_")
        if key not in labels_dict:
            labels_dict[key] = {
                "id": key,
                "name": label_name,
                "type": "user",
                "labelListVisibility": "labelHide",
                "messageListVisibility": "hide",
            }
    return labels_dict


def port_gmail(raw_data: str, file_path: str | None = None):
    """
    Port raw Gmail vendor JSON into our Gmail schema and validate.
    Returns (result_dict, message) where result_dict is None on failure.
    """
    try:
        # Parse JSON with error handling
        try:
            source_db = json.loads(raw_data, strict=False)
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON syntax: {str(e)}"
        
        # Validate input structure
        if not isinstance(source_db, dict):
            return None, "Input must be a JSON object"
        
        # Validate required profile section
        if "profile" not in source_db:
            return None, "Missing required profile section"
        
        profile = source_db.get("profile", {})
        if not isinstance(profile, dict):
            return None, "Profile must be an object"
        
        # Validate required email address
        if "emailAddress" not in profile:
            return None, "Missing required emailAddress in profile"
        
        email = profile.get("emailAddress", "")
        if not isinstance(email, str):
            return None, "emailAddress must be a string"
        
        if not validate_email(email):
            return None, f"Invalid email format: {email}"

        # Validate messages structure if present
        messages_data = source_db.get("messages", {})
        if not isinstance(messages_data, dict):
            return None, "messages must be an object"

        db_dict = {
            "users": {
                "me": {
                    "profile": profile,
                    "messages": {},
                    "drafts": {},
                    "threads": source_db.get("threads", {}),
                    "labels": normalize_labels(source_db.get("labels", [])),
                    "history": source_db.get("history", []),
                    "watch": source_db.get("watch", {}),
                    "vacation": source_db.get("settings", {}).get(
                        "vacation", {"enableAutoReply": False, "responseBodyPlainText": ""}
                    ),
                    "autoForwarding": source_db.get("settings", {}).get(
                        "autoForwarding", {"enabled": False}
                    ),
                }
            },
            "attachments": source_db.get("attachments", {}),
        }

        me = db_dict["users"]["me"]

        # Process Messages with validation
        try:
            for msg_id, msg_data in messages_data.items():
                if not isinstance(msg_data, dict):
                    return None, f"Invalid message structure for {msg_id}"
                me["messages"][msg_id] = transform_email_entry(msg_data)
        except (ValueError, TypeError, KeyError) as e:
            return None, f"Message processing error: {str(e)}"

        # Process Drafts with validation
        try:
            for draft_id, draft_data in source_db.get("drafts", {}).items():
                if not isinstance(draft_data, dict):
                    return None, f"Invalid draft structure for {draft_id}"
                
                # Handle both nested message format and direct format
                if "message" in draft_data:
                    # Nested format: draft contains a message object
                    message_data = draft_data["message"]
                    if not isinstance(message_data, dict):
                        return None, f"Invalid draft message structure for {draft_id}"
                    
                    # Ensure the nested message has an ID
                    message_data_copy = message_data.copy()
                    if "id" not in message_data_copy:
                        message_data_copy["id"] = draft_id  # Use draft_id for the message ID
                    
                    me["drafts"][draft_id] = {
                        "id": draft_data.get("id", draft_id),  # Use draft_id as fallback
                        "message": transform_email_entry(message_data_copy),
                    }
                else:
                    # Direct format: draft data IS the message
                    # Ensure draft has an ID
                    draft_data_copy = draft_data.copy()
                    if "id" not in draft_data_copy:
                        draft_data_copy["id"] = draft_id
                    
                    me["drafts"][draft_id] = {
                        "id": draft_data.get("id", draft_id),
                        "message": transform_email_entry(draft_data_copy),
                    }
        except (ValueError, TypeError, KeyError) as e:
            return None, f"Draft processing error: {str(e)}"

        # Generate settings with validated email
        me["settings"] = {
            "imap": source_db.get("settings", {}).get(
                "imap", {"enabled": True, "server": "imap.gmail.com", "port": 993}
            ),
            "pop": source_db.get("settings", {}).get(
                "pop", {"enabled": False, "server": "pop.gmail.com", "port": 995}
            ),
            "vacation": me["vacation"],
            "language": source_db.get("settings", {}).get(
                "language", {"displayLanguage": "en-US"}
            ),
            "autoForwarding": me["autoForwarding"],
            "sendAs": source_db.get("settings", {}).get(
                "sendAs",
                {
                    email: {
                        "sendAsEmail": email,
                        "displayName": email.split("@")[0].title(),
                        "replyToAddress": email,
                        "signature": f"Regards,\n{email.split('@')[0].title()}",
                        "verificationStatus": "accepted",
                        "smimeInfo": {
                            "smime_mock_1": {
                                "id": "smime_mock_1",
                                "encryptedKey": "mock_encrypted_key",
                                "default": True,
                            }
                        },
                    }
                },
            ),
        }

        # Generate counters
        db_dict["counters"] = {
            "message": len(me["messages"]),
            "thread": len(me["threads"]),
            "draft": len(me["drafts"]),
            "label": len(me["labels"]),
            "history": len(me["history"]),
            "attachment": len(db_dict.get("attachments", {})),
            "smime": sum(
                len(info.get("smimeInfo", {})) for info in me["settings"]["sendAs"].values()
            ),
        }

        # Validate against schema
        status, message = validate_with_default_schema("gmail.SimulationEngine.models", db_dict)
        
        if file_path and status:
            try:
                out_path = Path(file_path)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(db_dict, indent=2), encoding="utf-8")
                print(f"Output written to: {out_path.resolve()}")
            except Exception as e:
                return None, f"Failed to write output file: {str(e)}"
        
        if not status:
            return None, message
        return db_dict, message
        
    except Exception as e:
        # Catch any unexpected errors and return gracefully
        return None, f"Unexpected error during processing: {str(e)}"


if __name__ == "__main__":
    if not sys.stdin.isatty():
        # read raw string from stdin
        raw = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:   
        vendor_path = BASE_PATH / "vendor_gmail.json"
        raw = vendor_path.read_text()
        output_path = BASE_PATH / "ported_final_gmail.json"
    
    result, message = port_gmail(raw, output_path)
    if result is None:
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Gmail porting completed successfully")
