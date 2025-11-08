import json
import re, sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))
from whatsapp.SimulationEngine.models import whatsappDB
from contacts.SimulationEngine.models import FullContactDB
from common_utils.phone_utils import normalize_phone_number
BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "whatsapp"

def normalize_date_formats(date_str: str) -> str | None:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_jid(inp: str) -> str:
    return f"{inp}@s.whatsapp.net" if "@" not in inp else inp


def parse_group_metadata(group_metadata: dict) -> dict:
    if not group_metadata:
        return {
            "group_description": "",
            "creation_timestamp": "",
            "owner_jid": "",
            "participants_count": 0,
            "participants": []
        }
    return {
        "group_description": group_metadata.get("group_description", ""),
        "creation_timestamp": normalize_date_formats(group_metadata.get("creation_timestamp", "")),
        "owner_jid": parse_jid(group_metadata.get("owner_jid", "")),
        "participants_count": len(group_metadata.get("participants", []) or []),
        "participants": [
            {
                "jid": parse_jid(p.get("jid", "")),
                "name_in_address_book": p.get("name_in_address_book", ""),
                "profile_name": p.get("profile_name", ""),
                "is_admin": p.get("is_admin", False),
            }
            for p in (group_metadata.get("participants") or [])
            if isinstance(p, dict)
        ],
    }


def convert_whatsapp_contacts(contacts_data: dict, current_user_jid: str) -> dict:
    converted_contacts = {}
    for jid, contact in contacts_data.items():
        jid_full = f"{jid}@s.whatsapp.net"
        names = []
        if contact.get("name_in_address_book"):
            parts = contact["name_in_address_book"].split()
            given = parts[0]
            family = " ".join(parts[1:]) if len(parts) > 1 else ""
            names.append({"givenName": given, "familyName": family})

        phone_numbers = []
        raw = contact.get("phone_number")
        if raw:
            phone_numbers.append({
                "value": normalize_phone_number(contact["phone_number"]),
                "type": "mobile",
                "primary": True
            })

        contact_entry = {
            "resourceName": f"people/{jid_full}",
            "etag": f"etag_{jid}",
            "names": names,
            "emailAddresses": [],
            "phoneNumbers": phone_numbers,
            "organizations": [],
            "whatsapp": {
                "jid": jid_full,
                "name_in_address_book": contact.get("name_in_address_book", ""),
                "profile_name": contact.get("profile_name", ""),
                "phone_number": normalize_phone_number(raw) if raw else "",
                "is_whatsapp_user": contact.get("is_whatsapp_user", False),
            },
        }
        converted_contacts[f"people/{jid_full}"] = contact_entry
    return converted_contacts


def convert_whatsapp_chats(chats_data: dict, current_user_jid: str) -> dict:
    """Convert old WhatsApp chats format to new v0.1.0 format."""
    converted_chats = {}
    for chat_id, chat in chats_data.items():
        suffix = "@g.us" if chat.get("is_group", False) else "@s.whatsapp.net"
        if "@" in chat_id:
            jid_full = chat_id.split("@", 1)[0] + suffix
        else:
            jid_full = chat_id + suffix
        
        messages = []
        for msg in chat["messages"]:
            converted_msg = {
                "message_id": msg["message_id"],
                "chat_jid": jid_full,
                "sender_jid": parse_jid(msg["sender_jid"]),
                "sender_name": msg["sender_name"],
                "timestamp": normalize_date_formats(msg["timestamp"]),
                "text_content": msg["text_content"],
                "is_outgoing": msg["sender_jid"] == current_user_jid,
            }
            if "quoted_message_info" in msg:
                converted_msg["quoted_message_info"] = {
                    "quoted_message_id": msg["quoted_message_info"]["quoted_message_id"],
                    "quoted_sender_jid": parse_jid(msg["quoted_message_info"]["quoted_sender_jid"]),
                    "quoted_text_preview": msg["quoted_message_info"]["quoted_text_preview"],
                }
            messages.append(converted_msg)

        new_chat = {
            "chat_jid": jid_full,
            "name": chat.get("name", ""),
            "is_group": chat.get("is_group", False),
            "last_active_timestamp": normalize_date_formats(messages[-1]["timestamp"]) if messages else None,
            "unread_count": 0,
            "is_archived": chat.get("is_archived", False),
            "is_pinned": chat.get("is_pinned", False),
            "is_muted_until": chat.get("is_muted_until", ""),
            "group_metadata": parse_group_metadata(chat.get("group_metadata", {})),
            "messages": messages,
        }
        converted_chats[jid_full] = new_chat
    return converted_chats

def parse_whatsapp_data(whatsapp_data):
        """Main function to parse old WhatsApp data to new format."""
        current_user_jid = f"{whatsapp_data.get('current_user_jid', str(uuid.uuid4()))}@s.whatsapp.net"

        contacts = convert_whatsapp_contacts(whatsapp_data.get("contacts", {}), whatsapp_data.get('current_user_jid', {}))
        chats = convert_whatsapp_chats(whatsapp_data.get("chats",{}), whatsapp_data.get('current_user_jid', {}))

     
        return current_user_jid, contacts, chats

    # ================================
    # CONTACTS DATA CONVERSION
    # ================================

def merge_whatsapp_contacts(whatsapp_contacts, contacts):
    """Merge WhatsApp contacts into existing contacts without losing data."""
    for resource_name, wa_contact in whatsapp_contacts.items():
        wa_phone = normalize_phone_number(wa_contact["whatsapp"].get("phone_number"))
        wa_phone_str = wa_phone.lstrip("1") if wa_phone.startswith("1") else wa_phone
        contact_resources = [(x["whatsapp"]["jid"],x["resourceName"]) for x in contacts.values()]
        contact_exist = next((x[1] for x in contact_resources if wa_phone_str in x[0]), None)

        if contact_exist or resource_name in contacts:
            contact = contacts[contact_exist or resource_name]

            contact.setdefault("phoneNumbers", [])
            if wa_phone and all(normalize_phone_number(p.get("value")) != wa_phone for p in contact["phoneNumbers"]):
                contact["phoneNumbers"].append({
                    "value": wa_contact["whatsapp"].get("phone_number"),
                    "type": "whatsapp",
                    "primary": False
                })
                contact["whatsapp"] = wa_contact["whatsapp"]
                contact["whatsapp"]["is_whatsapp_user"] = True

        else:
            wa_contact["whatsapp"]["is_whatsapp_user"] = True
            contacts[resource_name] = wa_contact

    return contacts



def parse_contacts_data(contacts_data, whatsapp_contacts):
    parsed_contacts = {}

    phone_to_wa_res = {
        normalize_phone_number(phone.get("value")): res
        for res, wa in whatsapp_contacts.items()
        for phone in wa.get("phoneNumbers", [])
    }

    for _, contact in contacts_data.items():
        names = contact.get("names", [])
        contact_name = f"{names[0].get('givenName', '')} {names[0].get('familyName', '')}".strip() if names else ""
        org_phone_number = contact.get("phoneNumbers", [{"value": str(uuid.uuid4())}])[0]["value"]
        phone_number = normalize_phone_number(org_phone_number)
        if phone_number in phone_to_wa_res:
            resource_name = phone_to_wa_res[phone_number]
        else:
            resource_name = f"people/{uuid.uuid4()}"
        parsed_contacts[resource_name] = {
            "resourceName": resource_name,
            "etag": uuid.uuid4().hex,
            "names": names,
            "emailAddresses": contact.get("emailAddresses", []),
            "phoneNumbers": contact.get("phoneNumbers", []),
            "organizations": contact.get("organizations", []),
            "addresses": contact.get("addresses", []) or [],
            "notes": contact.get("notes", ""),
            "phone": {
                "contact_id": resource_name.split('/')[-1],
                "contact_name": contact_name,
                "contact_photo_url": None,
                "contact_endpoints": [
                    {
                        "endpoint_type": "PHONE_NUMBER",
                        "endpoint_value": p.get("value", ""),
                        "endpoint_label": p.get("type", "")
                    }
                    for p in contact.get("phoneNumbers", [])
                ]
            },
            "whatsapp": {
                "jid": f"{phone_number}@s.whatsapp.net",
                "name_in_address_book": contact_name,
                "profile_name": contact_name,
                "phone_number": org_phone_number,
                "is_whatsapp_user": phone_number in phone_to_wa_res
            }
        }

    return merge_whatsapp_contacts(whatsapp_contacts, parsed_contacts)

def port_db_whatsapp_and_contacts(raw_contacts: str, raw_whatsapp: str, file_path: str | None = None) -> None:
    whatsapp_data = json.loads(raw_whatsapp)
    contact_data = json.loads(raw_contacts)
     # Convert WhatsApp data
    current_user_jid, parsed_whatsapp_contacts, parsed_whatsapp_chats = parse_whatsapp_data(whatsapp_data)

    # # Convert contacts data
    parsed_contacts = parse_contacts_data(contact_data, parsed_whatsapp_contacts)
    ported_whatsapp = {
        "current_user_jid": current_user_jid,
        "contacts": parsed_whatsapp_contacts,
        "chats": parsed_whatsapp_chats,
    }
    
    validated_whatsapp = whatsappDB(**ported_whatsapp)
    ported_contacts = {
        "myContacts": parsed_contacts,
        "otherContacts": {},
        "directory": {}
    }
    validated_contacts = FullContactDB(**ported_contacts)

    if file_path:
        output_data = {
            "whatsapp": validated_whatsapp.model_dump(),
            "contacts": validated_contacts.model_dump()
        }
        Path(file_path).write_text(json.dumps(output_data, indent=2), encoding="utf-8")
    else:
        print(json.dumps({
            "whatsapp": validated_whatsapp.model_dump(),
            "contacts": validated_contacts.model_dump()
        }, indent=2))

    return validated_whatsapp.model_dump(), validated_contacts.model_dump()

if __name__ == "__main__":
    if not sys.stdin.isatty():
        # read raw JSON strings from stdin
        raw_input = sys.stdin.read().strip()
        # If you want to pass both contacts and whatsapp JSON as a single combined JSON:
        data = json.loads(raw_input)
        raw_contacts = data.get("contacts", "{}")
        raw_whatsapp = data.get("whatsapp", "{}")
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:
        # fallback to local files
        contacts_path = BASE_PATH / "vendor_contact.json"
        whatsapp_path = BASE_PATH / "vendor_whatsapp.json"
        raw_contacts = contacts_path.read_text()
        raw_whatsapp = whatsapp_path.read_text()
        output_path = BASE_PATH / "final_whatsapp_contacts.json"

    # call the porting function
    whatsapp, contacts = port_db_whatsapp_and_contacts(raw_contacts, raw_whatsapp, output_path)
