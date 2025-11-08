import json
import sys
import uuid
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

from phone.SimulationEngine.models import PhoneDB
from common_utils.phone_utils import normalize_phone_number, is_phone_number_valid

BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "phone"

def normalize_contact_name(given_name: str, family_name: str) -> str | None:
    """
    Normalize contact name, handling empty/whitespace strings.
    
    Args:
        given_name: Given name string
        family_name: Family name string
        
    Returns:
        Normalized contact name or None if both are empty/whitespace.
        Never returns empty string to comply with RecipientModel validation.
    """
    given = given_name.strip() if given_name else ""
    family = family_name.strip() if family_name else ""
    
    if not given and not family:
        return None
    
    # Ensure we never return empty string - return None instead
    result = f"{given} {family}".strip()
    return result if result else None

def normalize_call_id(call_id: str, fallback_id: str) -> str:
    """
    Normalize call_id, ensuring it's not empty/whitespace.
    
    Args:
        call_id: Original call ID
        fallback_id: Fallback ID to use if original is invalid
        
    Returns:
        Normalized call_id (guaranteed to be non-empty string)
    """
    # Try provided call_id first
    if call_id and isinstance(call_id, str) and call_id.strip():
        return call_id.strip()
    
    # Try fallback_id next  
    if fallback_id and isinstance(fallback_id, str) and fallback_id.strip():
        return fallback_id.strip()
    
    # Generate UUID if both are invalid to comply with model validation
    return str(uuid.uuid4())

def normalize_boolean_value(value, default: bool = False) -> bool:
    """
    Normalize boolean value from various inputs.
    
    Args:
        value: Input value of any type
        default: Default boolean value if conversion fails
        
    Returns:
        Normalized boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ["true", "1", "yes", "on"]:
            return True
        elif val_lower in ["false", "0", "no", "off"]:
            return False
    
    return default

def normalize_status(status: str) -> str:
    """
    Normalize call status to valid values.
    
    Args:
        status: Original status string
        
    Returns:
        Normalized status ("completed" only, as per model requirement)
    """
    if status and isinstance(status, str):
        status_lower = status.lower().strip()
        if status_lower == "completed":
            return "completed"
    
    # Model only accepts "completed", so default to that
    return "completed"

def normalize_recipient_name(name: str) -> str:
    """
    Normalize recipient name, ensuring it's not empty.
    
    Args:
        name: Original recipient name
        
    Returns:
        Normalized recipient name or empty string
    """
    if name and isinstance(name, str):
        normalized = name.strip()
        if normalized:
            return normalized
    
    return ""

def load_default_db() -> dict:
    """Load default DB or create fallback structure."""
    default_db_path = Path("DBs/PhoneDefaultDB.json")
    
    if default_db_path.exists():
        with default_db_path.open() as f:
            return json.load(f)
    
    # Create a minimal default structure
    return {
        "contacts": {},
        "businesses": {},
        "special_contacts": {},
        "call_history": {},
        "prepared_calls": {},
        "recipient_choices": {},
        "not_found_records": {}
    }

def parse_input_jsons(phone_db_str: str, contacts_db_str: str) -> tuple[dict, dict, str | None]:
    """Parse input JSON strings and return parsed objects or error."""
    try:
        received_json = json.loads(phone_db_str)
        contacts_db = json.loads(contacts_db_str)
        return received_json, contacts_db, None
    except json.JSONDecodeError as e:
        return {}, {}, f"Invalid JSON input: {e}"

def process_phone_numbers_for_contact(contact: dict) -> list[dict]:
    """Process phone numbers for a single contact and return normalized list."""
    normalized_numbers = []
    
    for phone_entry in contact.get("phoneNumbers", []):
        if not phone_entry:
            continue
            
        phone_value = phone_entry.get("value", "")
        norm_value = normalize_phone_number(phone_value)
        
        if norm_value and is_phone_number_valid(norm_value):
            normalized_numbers.append({
                "value": norm_value,
                "type": phone_entry.get("type", ""),
                "primary": phone_entry.get("primary", False)
            })
    
    return normalized_numbers

def create_contact_entry(contact: dict, normalized_numbers: list, contacts_namespace: uuid.UUID) -> dict:
    """Create a contact entry with proper structure."""
    first_phone = normalized_numbers[0]["value"] if normalized_numbers else ""
    names_list = contact.get("names", [])
    first_name_entry = names_list[0] if names_list else {}
    given_name = first_name_entry.get("givenName", "")
    family_name = first_name_entry.get("familyName", "")

    # Generate resource UUID
    uuid_seed = first_phone if first_phone else given_name + family_name
    resource_uuid = uuid.uuid5(contacts_namespace, uuid_seed)
    resource_name = f"people/{resource_uuid}"
    
    # Normalize contact name
    normalized_contact_name = normalize_contact_name(given_name, family_name)

    # Create contact endpoints
    contact_endpoints = [
        {
            "endpoint_type": "PHONE_NUMBER",
            "endpoint_value": num["value"],
            "endpoint_label": num.get("type", "")
        }
        for num in normalized_numbers
    ] if normalized_numbers else None

    return {
        "resourceName": resource_name,
        "etag": str(uuid.uuid5(contacts_namespace, resource_name)),
        "names": contact.get("names", []),
        "emailAddresses": contact.get("emailAddresses", []),
        "phoneNumbers": normalized_numbers,
        "organizations": contact.get("organizations", []),
        "isWorkspaceUser": contact.get("isWorkspaceUser", False),
        "phone": {
            "contact_id": resource_name.split("/")[-1],
            "contact_name": normalized_contact_name,
            "recipient_type": "CONTACT",
            "contact_photo_url": None,
            "contact_endpoints": contact_endpoints
        }
    }

def convert_contacts_section(contacts_db: dict, contacts_namespace: uuid.UUID) -> tuple[dict, dict]:
    """Convert contacts section and build phone-to-contact mapping."""
    contacts_section = {}
    phone_to_contact = {}
    
    for key, contact in contacts_db.items():
        normalized_numbers = process_phone_numbers_for_contact(contact)
        
        # Build phone-to-contact mapping
        for num in normalized_numbers:
            phone_to_contact[num["value"]] = contact
        
        # Create contact entry
        entry = create_contact_entry(contact, normalized_numbers, contacts_namespace)
        contacts_section[entry["resourceName"]] = entry

    return contacts_section, phone_to_contact

def parse_timestamp(timestamp_value) -> float:
    """Parse timestamp from various input formats."""
    if timestamp_value is None:
        return 0.0
        
    if isinstance(timestamp_value, (int, float)):
        return float(timestamp_value)
    
    if not isinstance(timestamp_value, str):
        return 0.0
    
    try:
        # Handle various timestamp formats
        if "T" in timestamp_value:
            # ISO format with T separator
            if "-" in timestamp_value.split("T")[1]:
                # Format: 2024-01-15T10-30-00
                dt = datetime.strptime(timestamp_value, "%Y-%m-%dT%H-%M-%S")
            else:
                # Standard ISO format: 2024-01-15T10:30:00
                dt = datetime.fromisoformat(timestamp_value.replace("Z", ""))
        else:
            # Other formats
            dt = datetime.fromisoformat(timestamp_value)
        return dt.timestamp()
    except Exception:
        return 0.0

def get_recipient_info(phone_number: str, call: dict, phone_to_contact: dict) -> tuple[str, str]:
    """Get recipient name and photo URL based on phone number matching."""
    recipient_contact = phone_to_contact.get(phone_number)
    
    if not recipient_contact:
        recipient_name = normalize_recipient_name(call.get("recipient_name", ""))
        return recipient_name, None
    
    # Use contact information
    names = recipient_contact.get('names', [])
    first_name_entry = names[0] if names else {}
    given_name = first_name_entry.get('givenName', '')
    family_name = first_name_entry.get('familyName', '')
    recipient_name = normalize_contact_name(given_name, family_name) or ""
    
    return recipient_name, None

def process_single_call(call_id: str, call: dict, phone_to_contact: dict) -> dict:
    """Process a single call history entry."""
    # Parse timestamp
    epoch_time = parse_timestamp(call.get("timestamp"))
    
    # Process phone number
    phone_number = normalize_phone_number(call.get("phone_number", ""))
    if not phone_number or not is_phone_number_valid(phone_number):
        phone_number = ""
    
    # Get recipient information
    recipient_name, recipient_photo_url = get_recipient_info(phone_number, call, phone_to_contact)
    
    # Normalize call data
    normalized_call_id = normalize_call_id(call.get("call_id"), call_id)
    normalized_on_speakerphone = normalize_boolean_value(call.get("on_speakerphone"), False)
    normalized_status = normalize_status(call.get("status", "completed"))
    
    return {
        "call_id": normalized_call_id,
        "timestamp": epoch_time,
        "phone_number": phone_number,
        "recipient_name": recipient_name,
        "recipient_photo_url": recipient_photo_url,
        "on_speakerphone": normalized_on_speakerphone,
        "status": normalized_status
    }

def convert_call_history_section(received_json: dict, phone_to_contact: dict) -> dict:
    """Convert call history section."""
    call_history = {}
    
    for call_id, call in received_json.get("call_history", {}).items():
        call_history[call_id] = process_single_call(call_id, call, phone_to_contact)
    
    return call_history

def copy_other_sections(received_json: dict, default_db: dict) -> dict:
    """Copy other sections from received JSON; leave empty when missing.

    This avoids injecting data (e.g. businesses, special contacts) from the
    default DB that wasn't provided in the inputs.
    """
    sections = ["businesses", "special_contacts", "prepared_calls", "recipient_choices", "not_found_records"]
    result = {}
    for section in sections:
        result[section] = received_json.get(section, {})
    return result

def validate_and_save(final_json: dict, file_path: str | None) -> tuple[dict | None, str]:
    """Validate final JSON and optionally save to file."""
    try:
        validated_db = PhoneDB(**final_json)
        final_json = validated_db.model_dump()
        message = "Validation successful"
    except Exception as e:
        return None, f"Validation failed: {str(e)}"
    
    # Save to file if path provided
    if file_path:
        out_path = Path(file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(final_json, indent=2), encoding="utf-8")
        print(f"Output written to: {out_path.resolve()}")
    
    return final_json, message

def port_phone_db(phone_db_str: str, contacts_db_str: str, file_path: str | None = None):
    """
    Port raw Phone JSON into the default schema and validate.

    Args:
        phone_db_str (str): Raw JSON string of phone database.
        contacts_db_str (str): Raw JSON string of contacts database.
        file_path (str | None): Path to save the ported DB. If None, doesn't save to disk.
        
    Returns:
        tuple: (ported_db_dict, error_message)
    """
    contacts_namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "contacts")
    
    # Load default DB
    default_db = load_default_db()
    
    # Parse input JSONs
    received_json, contacts_db, parse_error = parse_input_jsons(phone_db_str, contacts_db_str)
    if parse_error:
        return None, parse_error
    
    # Convert contacts section
    contacts_section, phone_to_contact = convert_contacts_section(contacts_db, contacts_namespace)
    
    # Convert call history section
    call_history_section = convert_call_history_section(received_json, phone_to_contact)
    
    # Copy other sections
    other_sections = copy_other_sections(received_json, default_db)
    
    # Build final JSON
    final_json = {
        "contacts": contacts_section,
        "call_history": call_history_section,
        **other_sections
    }
    
    # Validate and save
    return validate_and_save(final_json, file_path)

def load_file_with_fallback(file_path: str, fallback_path: Path | None = None) -> str:
    """Load file with optional fallback path."""
    try:
        return Path(file_path).read_text()
    except FileNotFoundError:
        if fallback_path and fallback_path.exists():
            return fallback_path.read_text()
        raise

def handle_stdin_input(args: list[str]) -> tuple[str, str, str | None]:
    """Handle input from stdin."""
    phone_db_raw = sys.stdin.read().strip()
    contacts_db_path = args[1]
    output_path = args[2] if len(args) > 2 else None
    
    try:
        contacts_db_raw = Path(contacts_db_path).read_text()
    except FileNotFoundError:
        print(f"Contacts DB file not found: {contacts_db_path}")
        sys.exit(1)
    
    return phone_db_raw, contacts_db_raw, output_path

def handle_file_input(args: list[str]) -> tuple[str, str, str | None]:
    """Handle input from command line file arguments."""
    phone_db_path = args[1]
    contacts_db_path = args[2] if len(args) > 2 else None
    output_path = args[3] if len(args) > 3 else None
    
    # Load phone DB
    vendor_phone_path = BASE_PATH / "vendor_phone.json"
    try:
        phone_db_raw = load_file_with_fallback(phone_db_path, vendor_phone_path)
    except FileNotFoundError:
        print(f"Phone DB file not found: {phone_db_path}")
        sys.exit(1)
    
    # Load contacts DB
    if contacts_db_path:
        try:
            contacts_db_raw = Path(contacts_db_path).read_text()
        except FileNotFoundError:
            print(f"Contacts DB file not found: {contacts_db_path}")
            sys.exit(1)
    else:
        vendor_contacts_path = BASE_PATH / "vendor_contacts.json"
        if vendor_contacts_path.exists():
            contacts_db_raw = vendor_contacts_path.read_text()
        else:
            print("No contacts DB provided and default file not found")
            sys.exit(1)
    
    if not output_path:
        output_path = BASE_PATH / "ported_final_phone.json"
    
    return phone_db_raw, contacts_db_raw, output_path

if __name__ == "__main__":
    # Determine input method and get data
    if not sys.stdin.isatty():
        phone_db_raw, contacts_db_raw, output_path = handle_stdin_input(sys.argv)
    else:
        if len(sys.argv) >= 2:
            # File paths provided via CLI
            phone_db_raw, contacts_db_raw, output_path = handle_file_input(sys.argv)
        else:
            # No args provided: auto-fallback to vendor sample files (like port_contacts.py)
            vendor_phone_path = BASE_PATH / "vendor_phone.json"
            # Prefer phone folder's contacts, then global contacts sample
            vendor_contacts_path_primary = BASE_PATH / "vendor_contacts.json"
            vendor_contacts_path_fallback = Path(__file__).resolve().parent / "SampleDBs" / "contacts" / "vendor_contacts.json"

            if not vendor_phone_path.exists():
                print("Usage: python port_phone.py <phone_db_json> [contacts_db_json] [output_path]")
                print("   or: echo 'phone_db_json' | python port_phone.py contacts_db_json [output_path]")
                sys.exit(1)

            phone_db_raw = vendor_phone_path.read_text()
            if vendor_contacts_path_primary.exists():
                contacts_db_raw = vendor_contacts_path_primary.read_text()
            elif vendor_contacts_path_fallback.exists():
                contacts_db_raw = vendor_contacts_path_fallback.read_text()
            else:
                contacts_db_raw = "{}"  # allow empty contacts

            output_path = BASE_PATH / "ported_final_phone.json"
    
    # Process the data
    db, msg = port_phone_db(phone_db_raw, contacts_db_raw, output_path)
    
    if db is None:
        print(f"Error: {msg}")
        sys.exit(1)
    else:
        print("Phone DB porting completed successfully!")
