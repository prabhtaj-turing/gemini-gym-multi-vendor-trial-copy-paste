#!/usr/bin/env python3
"""
Contacts, Phone, and WhatsApp API Demo Script

This script demonstrates:
1. Creating contacts using the Contacts API
2. Searching contacts using the Phone API
3. Searching contacts using the WhatsApp API
"""

import sys
import os

# Add the APIs directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../APIs'))

# Import the required APIs
import contacts
import phone
import whatsapp

def create_sample_contacts():
    """Create sample contacts using the Contacts API."""
    print("=== Creating Sample Contacts ===")
    
    contacts_to_create = [
        {
            "given_name": "Alex",
            "family_name": "Thompson",
            "email": "alex.thompson@demo.com",
            "phone": "+15551234567"
        },
        {
            "given_name": "Sarah",
            "family_name": "Martinez",
            "email": "sarah.martinez@demo.com",
            "phone": "+15559876543"
        },
        {
            "given_name": "David",
            "family_name": "Chen",
            "email": "david.chen@demo.com",
            "phone": "+15551112233"
        },
        {
            "given_name": "Emma",
            "family_name": "Williams",
            "email": "emma.williams@demo.com",
            "phone": "+15554445556"
        },
        {
            "given_name": "Marcus",
            "family_name": "Garcia",
            "email": "marcus.garcia@demo.com",
            "phone": "+15556667778"
        }
    ]
    
    created_contacts = []
    
    for contact_data in contacts_to_create:
        try:
            result = contacts.create_contact(
                given_name=contact_data["given_name"],
                family_name=contact_data["family_name"],
                email=contact_data["email"],
                phone=contact_data["phone"]
            )
            created_contacts.append(result)
            print(f"✅ Created contact: {contact_data['given_name']} {contact_data['family_name']}")
            print(f"   Resource Name: {result.get('resourceName', 'N/A')}")
            print(f"   Phone: {contact_data['phone']}")
        except Exception as e:
            print(f"❌ Failed to create contact {contact_data['given_name']}: {e}")
    
    print(f"\nTotal contacts created: {len(created_contacts)}")
    return created_contacts

def list_all_contacts():
    """List all contacts in the database."""
    print("\n=== Listing All Contacts ===")
    
    try:
        all_contacts = contacts.list_contacts()
        print(f"Total contacts in database: {len(all_contacts.get('contacts', []))}")
        print("\nAll contacts:")
        for contact in all_contacts.get('contacts', []):
            names = contact.get('names', [{}])
            name = names[0] if names else {}
            given_name = name.get('givenName', 'N/A')
            family_name = name.get('familyName', 'N/A')
            
            phone_numbers = contact.get('phoneNumbers', [])
            phone = phone_numbers[0].get('value', 'N/A') if phone_numbers else 'N/A'
            
            print(f"  • {given_name} {family_name} - {phone}")
    except Exception as e:
        print(f"Error listing contacts: {e}")

def search_contacts_with_phone_api():
    """Search contacts using the Phone API."""
    print("\n=== Searching Contacts with Phone API ===")
    
    # Use the new contact names
    search_queries = ["Alex", "Sarah", "David", "Emma", "Marcus"]
    
    for query in search_queries:
        print(f"\n🔍 Searching for '{query}' using Phone API:")
        
        try:
            # Prepare call to search for the contact
            prepare_result = phone.prepare_call(recipients=[{"contact_name": query}])
            
            if prepare_result.get('recipients'):
                recipients = prepare_result['recipients']
                print(f"  Found {len(recipients)} recipient(s):")
                
                for i, recipient in enumerate(recipients, 1):
                    print(f"    {i}. {recipient.get('contact_name', 'N/A')}")
                    
                    endpoints = recipient.get('contact_endpoints', [])
                    if endpoints:
                        print(f"       Phone numbers: {[ep.get('phone_number', 'N/A') for ep in endpoints]}")
                    else:
                        print(f"       No phone numbers found")
            else:
                print(f"  No recipients found for '{query}'")
                
        except Exception as e:
            print(f"  Error searching for '{query}': {e}")
            # Try alternative search method
            try:
                print(f"  Trying alternative search method...")
                # Try searching with phone number directly
                phone_number = None
                if query == "Alex":
                    phone_number = "+15551234567"
                elif query == "Sarah":
                    phone_number = "+15559876543"
                elif query == "David":
                    phone_number = "+15551112233"
                elif query == "Emma":
                    phone_number = "+15554445556"
                elif query == "Marcus":
                    phone_number = "+15556667778"
                
                if phone_number:
                    call_result = phone.make_call(recipient_phone_number=phone_number)
                    print(f"  ✅ Direct call to {phone_number}: {call_result.get('observation', 'Call initiated')}")
            except Exception as e2:
                print(f"  Alternative search also failed: {e2}")

def test_phone_calls():
    """Test making calls with specific phone numbers."""
    print("\n=== Testing Phone Calls ===")
    
    # Use the new phone numbers
    test_phone_numbers = ["+15551234567", "+15559876543", "+15551112233"]
    
    for phone_number in test_phone_numbers:
        print(f"\n📞 Testing call to {phone_number}:")
        
        try:
            # Try to make a call with the phone number
            call_result = phone.make_call(
                recipient_phone_number=phone_number,
                on_speakerphone=False
            )
            
            print(f"  ✅ Call result: {call_result.get('observation', 'Call initiated')}")
            
        except Exception as e:
            print(f"  ❌ Error making call: {e}")

def search_contacts_with_whatsapp_api():
    """Search contacts using the WhatsApp API."""
    print("\n=== Searching Contacts with WhatsApp API ===")
    
    # Use the new contact names
    whatsapp_search_queries = ["Alex", "Sarah", "David", "Emma", "Marcus"]
    
    for query in whatsapp_search_queries:
        print(f"\n📱 Searching for '{query}' using WhatsApp API:")
        
        try:
            # Search contacts in WhatsApp
            whatsapp_contacts = whatsapp.search_contacts(query)
            
            if whatsapp_contacts:
                print(f"  Found {len(whatsapp_contacts)} WhatsApp contact(s):")
                
                for i, contact in enumerate(whatsapp_contacts, 1):
                    print(f"    {i}. JID: {contact.get('jid', 'N/A')}")
                    print(f"       Name: {contact.get('name_in_address_book', 'N/A')}")
                    print(f"       Profile Name: {contact.get('profile_name', 'N/A')}")
                    print(f"       Phone: {contact.get('phone_number', 'N/A')}")
                    print(f"       WhatsApp User: {contact.get('is_whatsapp_user', False)}")
            else:
                print(f"  No WhatsApp contacts found for '{query}'")
                
        except Exception as e:
            print(f"  Error searching WhatsApp for '{query}': {e}")

def search_whatsapp_by_phone_numbers():
    """Search WhatsApp using phone numbers directly."""
    print("\n=== Searching WhatsApp by Phone Numbers ===")
    
    # Use the new phone numbers (without +1 prefix for WhatsApp search)
    phone_numbers_to_search = ["5551234567", "5559876543", "5551112233"]
    
    for phone_number in phone_numbers_to_search:
        print(f"\n📱 Searching WhatsApp for phone number {phone_number}:")
        
        try:
            # Search contacts in WhatsApp by phone number
            whatsapp_contacts = whatsapp.search_contacts(phone_number)
            
            if whatsapp_contacts:
                print(f"  Found {len(whatsapp_contacts)} WhatsApp contact(s):")
                
                for i, contact in enumerate(whatsapp_contacts, 1):
                    print(f"    {i}. JID: {contact.get('jid', 'N/A')}")
                    print(f"       Name: {contact.get('name_in_address_book', 'N/A')}")
                    print(f"       Phone: {contact.get('phone_number', 'N/A')}")
                    print(f"       WhatsApp User: {contact.get('is_whatsapp_user', False)}")
            else:
                print(f"  No WhatsApp contacts found for phone number {phone_number}")
                
        except Exception as e:
            print(f"  Error searching WhatsApp for phone {phone_number}: {e}")

def get_detailed_contact_info(created_contacts):
    """Get detailed information about created contacts."""
    print("\n=== Detailed Contact Information ===")
    
    for contact in created_contacts:
        resource_name = contact.get('resourceName')
        if resource_name:
            try:
                detailed_contact = contacts.get_contact(resource_name)
                
                names = detailed_contact.get('names', [{}])
                name = names[0] if names else {}
                given_name = name.get('givenName', 'N/A')
                family_name = name.get('familyName', 'N/A')
                
                emails = detailed_contact.get('emailAddresses', [])
                email = emails[0].get('value', 'N/A') if emails else 'N/A'
                
                phones = detailed_contact.get('phoneNumbers', [])
                phone = phones[0].get('value', 'N/A') if phones else 'N/A'
                
                print(f"\n  👤 {given_name} {family_name}")
                print(f"     📧 Email: {email}")
                print(f"     📞 Phone: {phone}")
                print(f"     🆔 Resource: {resource_name}")
                
            except Exception as e:
                print(f"  Error getting details for {resource_name}: {e}")

def test_contact_search_functionality():
    """Test the contact search functionality."""
    print("\n=== Testing Contact Search Functionality ===")
    
    try:
        # Test searching contacts by name
        search_results = contacts.search_contacts("Alex", max_results=5)
        print(f"Search results for 'Alex': {len(search_results.get('contacts', []))} contacts found")
        
        # Test searching contacts by email
        search_results = contacts.search_contacts("demo.com", max_results=5)
        print(f"Search results for 'demo.com': {len(search_results.get('contacts', []))} contacts found")
        
    except Exception as e:
        print(f"Error testing contact search: {e}")

def main():
    """Main function to run the demo."""
    print("🚀 Starting Contacts, Phone, and WhatsApp API Demo\n")
    
    # Step 1: Create contacts
    created_contacts = create_sample_contacts()
    
    # Step 2: List all contacts
    list_all_contacts()
    
    # Step 3: Test contact search functionality
    test_contact_search_functionality()
    
    # Step 4: Search contacts with Phone API
    search_contacts_with_phone_api()
    
    # Step 5: Test phone calls
    test_phone_calls()
    
    # Step 6: Search contacts with WhatsApp API
    search_contacts_with_whatsapp_api()
    
    # Step 7: Search WhatsApp by phone numbers
    search_whatsapp_by_phone_numbers()
    
    # Step 8: Get detailed contact information
    get_detailed_contact_info(created_contacts)
    
    print("\n" + "="*50)
    print("✅ Demo completed successfully!")
    print("\nThis demo shows how to:")
    print("1. Create contacts using the Contacts API")
    print("2. Search contacts using the Phone API")
    print("3. Search contacts using the WhatsApp API")
    print("4. Make calls using the Phone API")
    print("5. Retrieve detailed contact information")
    print("6. Test contact search functionality")

if __name__ == "__main__":
    main() 