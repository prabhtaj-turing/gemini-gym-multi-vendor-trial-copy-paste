import json
import re, sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

from contacts.SimulationEngine.models import FullContactDB
from common_utils.phone_utils import normalize_phone_number

BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "contacts"

def port_contacts(raw_data: str, file_path: str | None = None):
    """
    Port raw Contacts JSON into the default schema and validate.

    Args:
        raw_data (str): Raw JSON string of vendor contact entries.
        persist (bool): If True, save the ported DB to disk. Defaults True.
        
    """
    CONTACTS_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "contacts")
    data = json.loads(raw_data)

    my_contacts = {}

    for _, contact in data.items():
        normalized_phone_numbers = []
        for phone_entry in contact.get("phoneNumbers", []):
            normalized = normalize_phone_number(phone_entry.get("value", ""))
            if normalized:
                normalized_phone_numbers.append({
                    "value": normalized,
                    "type": phone_entry.get("type", ""),
                    "primary": phone_entry.get("primary", None),
                })

        first_phone = normalized_phone_numbers[0]["value"] if normalized_phone_numbers else ""
        email = contact.get("emailAddresses", [{}])[0].get("value", "")
        givenName = contact.get("names", [{}])[0].get("givenName", "")

        if first_phone:
            resource_uuid = uuid.uuid5(CONTACTS_NAMESPACE, first_phone)
        elif email:
            resource_uuid = uuid.uuid5(CONTACTS_NAMESPACE, email)
        else:
            resource_uuid = uuid.uuid5(CONTACTS_NAMESPACE, givenName)

        resource_name = f"people/{resource_uuid}"

        entry = {
            "resourceName": resource_name,
            "etag": str(uuid.uuid5(CONTACTS_NAMESPACE, resource_name)),
            "names": contact.get("names", []),
            "emailAddresses": contact.get("emailAddresses", []),
            "phoneNumbers": normalized_phone_numbers,
            "organizations": contact.get("organizations", []),
            "directory": contact.get("directory", []),
            "notes": contact.get("notes", ""),
        }

        my_contacts[resource_name] = entry

    db_dict = {
        "myContacts": my_contacts,
        "otherContacts": {},
        "directory": {}
    }

    validated = FullContactDB(**db_dict)

    if file_path:
        out_path = Path(file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(validated.model_dump(), indent=2), encoding="utf-8")
        print(f"Output written to: {out_path.resolve()}")

    return validated.model_dump(), None

if __name__ == "__main__":
    if not sys.stdin.isatty():
        # read raw string from stdin
        raw = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:   
        vendor_path = BASE_PATH / "vendor_contacts.json"
        raw = vendor_path.read_text()
        output_path = BASE_PATH / "ported_final_contacts.json"
    
    db, msg = port_contacts(raw, output_path)
