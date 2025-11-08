import re
from typing import List, Dict, Any, Optional
from APIs.contacts import search_contacts
from APIs.google_search import search_queries
from APIs.google_maps.Places import searchText as search_places

def find_recipients(name: str) -> List[Dict[str, Any]]:
    """Find recipients by name, searching contacts, google_search, and maps.

    This function queries the contacts service first. If no results are found,
    it falls back to searching Google Maps and then Google Search.

    Args:
        name (str): The name of the recipient to search for.

    Returns:
        List[Dict[str, Any]]: A list of recipient dictionaries found. Each dictionary
            contains 'recipient_info' and 'endpoints'. An empty list means no recipients
            were found.
    """
    recipients = []
    
    # 1. Search contacts
    contact_results = search_contacts(query=name)
    for contact in contact_results.get("results", []):
        full_name = " ".join(filter(None, [
            contact.get("names", [{}])[0].get("givenName"),
            contact.get("names", [{}])[0].get("familyName")
        ])).strip() or name

        for phone in contact.get("phoneNumbers", []):
            recipients.append({
                "recipient_info": {
                    "name": full_name,
                    "recipient_type": "CONTACT",
                },
                "endpoints": [{
                    "type": "PHONE_NUMBER",
                    "value": phone.get("value"),
                    "label": phone.get("type"),
                }]
            })

    if recipients:
        return recipients

    # 2. Search Google Maps as fallback
    places_results = search_places(request={"textQuery": name})
    for place in places_results.get("places", []):
        phone_number = place.get("internationalPhoneNumber") or place.get("nationalPhoneNumber")
        if phone_number:
            recipients.append({
                "recipient_info": {
                    "name": place.get("displayName", {}).get("text") or place.get("name"),
                    "recipient_type": "BUSINESS",
                    "address": place.get("formattedAddress"),
                    "distance": place.get("distance"), # Assuming search_places might provide this
                },
                "endpoints": [{
                    "type": "PHONE_NUMBER",
                    "value": phone_number,
                    "label": "main",
                }]
            })
    
    if recipients:
        return recipients

    # 3. Search Google Search as a last resort
    search_results = search_queries(queries=[f"phone number for {name}"])
    for result in search_results:
        # A simple regex to find North American phone numbers. This can be improved.
        phone_numbers = re.findall(r'(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', result.get("result", ""))
        for phone_number in phone_numbers:
            recipients.append({
                "recipient_info": {
                    "name": name,
                    "recipient_type": "BUSINESS",
                },
                "endpoints": [{
                    "type": "PHONE_NUMBER",
                    "value": phone_number,
                    "label": "main",
                }]
            })
            # Typically, the first found number is the most relevant.
            if recipients:
                return recipients

    return recipients

def check_geofencing(distance_str: Optional[str]) -> bool:
    """Checks if a distance string violates the geofencing policy.

    The policy applies if the distance is > 50 miles or > 80 kilometers.

    Args:
        distance_str (Optional[str]): The distance string (e.g., "55 mi", "90 km").

    Returns:
        bool: True if the geofencing policy applies (distance exceeds threshold), 
            False otherwise.
    """
    if not distance_str:
        return False

    distance_str = distance_str.strip().lower()
    try:
        # Using regex to capture number and unit
        match = re.match(r'([0-9.]+)\s*(mi|km|miles|kilometers)', distance_str)
        if not match:
            return False # Cannot parse

        value = float(match.group(1))
        unit = match.group(2)

        if unit in ["mi", "miles"]:
            if value > 50:
                return True
        elif unit in ["km", "kilometers"]:
            if value > 80:
                return True
    except (ValueError, IndexError):
        # Could not parse the distance string
        return False

    return False