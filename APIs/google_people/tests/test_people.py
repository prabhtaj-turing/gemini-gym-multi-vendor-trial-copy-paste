import copy
import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .common import reset_db
from pydantic import ValidationError as PydanticValidationError
from .. import (create_contact, delete_contact, get_batch_get, get_contact, get_directory_person, list_connections, list_directory_people, search_directory_people, search_people, update_contact)

class TestPeopleAPI(BaseTestCaseWithErrorHandler):
    """Test class for Google People API functions."""

    def setUp(self):
        """Set up test database with sample data."""
        reset_db()
        from ..SimulationEngine.db import DB
        
        # Initialize test data
        DB.set("people", {
            "people/123456789": {
                "resourceName": "people/123456789",
                "etag": "etag_123456789",
                "names": [{"displayName": "John Doe", "givenName": "John", "familyName": "Doe"}],
                "emailAddresses": [{"value": "john.doe@example.com", "type": "work"}],
                "phoneNumbers": [{"value": "+1-555-123-4567", "type": "mobile"}],
                "addresses": [{"formattedValue": "123 Main St, City, State"}],
                "organizations": [{"name": "Tech Corp", "title": "Developer"}],
                "created": "2023-01-15T10:30:00Z",
                "updated": "2024-01-15T14:20:00Z"
            },
            "people/987654321": {
                "resourceName": "people/987654321",
                "etag": "etag_987654321",
                "names": [{"displayName": "Jane Smith", "givenName": "Jane", "familyName": "Smith"}],
                "emailAddresses": [{"value": "jane.smith@example.com", "type": "personal"}],
                "phoneNumbers": [{"value": "+1-555-987-6543", "type": "home"}],
                "created": "2023-02-20T11:00:00Z",
                "updated": "2024-01-10T09:15:00Z"
            },
            "people/555666777": {
                "resourceName": "people/555666777",
                "etag": "etag_555666777",
                "names": [{"displayName": "Mary O'Connor", "givenName": "Mary", "familyName": "O'Connor"}],
                "emailAddresses": [{"value": "mary.oconnor@example.com", "type": "work"}],
                "phoneNumbers": [{"value": "+1-555-555-5555", "type": "mobile"}],
                "created": "2023-03-10T12:00:00Z",
                "updated": "2024-01-05T16:30:00Z"
            }
        })

        DB.set("directoryPeople", {
            "directoryPeople/111222333": {
                "resourceName": "directoryPeople/111222333",
                "etag": "etag_dir_111222333",
                "names": [{"displayName": "Bob Wilson", "givenName": "Bob", "familyName": "Wilson"}],
                "emailAddresses": [{"value": "bob.wilson@company.com", "type": "work"}],
                "organizations": [{"name": "Company Inc", "title": "Manager"}],
                "created": "2023-03-10T08:00:00Z",
                "updated": "2024-01-05T16:30:00Z"
            }
        })

        DB.set("otherContacts", {
            "otherContacts/555666777": {
                "resourceName": "otherContacts/555666777",
                "etag": "etag_other_555666777",
                "names": [{"displayName": "Alice Johnson", "givenName": "Alice", "familyName": "Johnson"}],
                "emailAddresses": [{"value": "alice.johnson@external.com", "type": "work"}],
                "organizations": [{"name": "External Corp", "title": "Consultant"}],
                "created": "2023-04-15T09:00:00Z",
                "updated": "2024-01-08T12:00:00Z"
            }
        })

    def tearDown(self):
        """Clean up after tests."""
        reset_db()

    def test_get_contact_success(self):
        """Test successful retrieval of a contact."""
        result = get_contact("people/123456789")

        self.assertEqual(result["resourceName"], "people/123456789")
        self.assertEqual(result["etag"], "etag_123456789")
        self.assertEqual(len(result["names"]), 1)
        self.assertEqual(result["names"][0]["displayName"], "John Doe")

    def test_get_contact_with_fields_filter(self):
        """Test contact retrieval with field filtering."""
        result = get_contact("people/123456789", person_fields="names,emailAddresses")

        self.assertIn("names", result)
        self.assertIn("emailAddresses", result)
        self.assertNotIn("phoneNumbers", result)
        self.assertNotIn("addresses", result)

    def test_get_contact_not_found(self):
        """Test contact retrieval when contact doesn't exist."""
        self.assert_error_behavior(
            func_to_call=get_contact,
            expected_exception_type=ValueError,
            expected_message="Person with resource name 'people/nonexistent' not found",
            resource_name="people/nonexistent"
        )

    def test_get_contact_invalid_resource_name(self):
        """Test contact retrieval with invalid resource name."""
        self.assert_error_behavior(
            func_to_call=get_contact,
            expected_exception_type=PydanticValidationError,
            expected_message='Resource name must start with "people/"',
            resource_name="invalid_name"
        )

    def test_create_contact_success(self):
        """Test successful contact creation."""
        person_data = {
            "names": [{"displayName": "New Person", "givenName": "New", "familyName": "Person"}],
            "emailAddresses": [{"value": "new.person@example.com", "type": "work"}]
        }

        result = create_contact(person_data)

        self.assertIn("resourceName", result)
        self.assertIn("etag", result)
        self.assertEqual(result["names"][0]["displayName"], "New Person")
        self.assertEqual(result["emailAddresses"][0]["value"], "new.person@example.com")

    def test_create_contact_with_existing_data(self):
        """Test contact creation with existing database data."""
        person_data = {
            "names": [{"displayName": "Another Person", "givenName": "Another", "familyName": "Person"}],
            "emailAddresses": [{"value": "another.person@example.com", "type": "work"}]
        }

        result = create_contact(person_data)

        self.assertIn("resourceName", result)
        self.assertIn("etag", result)
        self.assertEqual(result["names"][0]["displayName"], "Another Person")

    def test_update_contact_success(self):
        """Test successful contact update."""
        update_data = {
            "phoneNumbers": [{"value": "+14155552671", "type": "mobile"}]
        }

        result = update_contact("people/123456789", update_data)

        self.assertEqual(result["resourceName"], "people/123456789")
        self.assertEqual(result["phoneNumbers"][0]["value"], "+14155552671")

    def test_update_contact_with_field_filter(self):
        """Test contact update with specific field filtering."""
        update_data = {
            "phoneNumbers": [{"value": "+14155552671", "type": "mobile"}],
            "organizations": [{"name": "New Company", "title": "Senior Developer"}]
        }

        result = update_contact("people/123456789", update_data, "phoneNumbers")

        self.assertEqual(result["phoneNumbers"][0]["value"], "+1-555-123-4567")
        # Should not update organizations since it's not in the field filter
        self.assertEqual(result["organizations"][0]["name"], "Tech Corp")

    def test_update_contact_not_found(self):
        """Test contact update when contact doesn't exist."""
        update_data = {"names": [{"displayName": "Updated Name"}]}

        self.assert_error_behavior(
            func_to_call=update_contact,
            expected_exception_type=ValueError,
            expected_message="Person with resource name 'people/nonexistent' not found",
            resource_name="people/nonexistent",
            person_data=update_data
        )

    def test_delete_contact_success(self):
        """Test successful contact deletion."""
        result = delete_contact("people/123456789")

        self.assertTrue(result["success"])
        self.assertEqual(result["deletedResourceName"], "people/123456789")
        self.assertEqual(result["message"], "Person deleted successfully")

    def test_delete_contact_not_found(self):
        """Test contact deletion when contact doesn't exist."""
        self.assert_error_behavior(
            func_to_call=delete_contact,
            expected_exception_type=ValueError,
            expected_message="Person with resource name 'people/nonexistent' not found",
            resource_name="people/nonexistent"
        )

    def test_list_connections_success(self):
        """Test successful listing of connections."""
        result = list_connections()

        self.assertIn("connections", result)
        self.assertIn("totalItems", result)
        self.assertEqual(len(result["connections"]), 3)

    def test_list_connections_with_pagination(self):
        """Test listing connections with pagination."""
        result = list_connections(page_size=1)

        self.assertEqual(len(result["connections"]), 1)
        self.assertIn("nextPageToken", result)

    def test_list_connections_with_sorting(self):
        """Test listing connections with sorting."""
        result = list_connections(sort_order="FIRST_NAME_ASCENDING")

        self.assertIn("connections", result)
        self.assertIn("totalItems", result)

    def test_list_connections_with_fields_filter(self):
        """Test listing connections with field filtering."""
        result = list_connections(person_fields="names,emailAddresses")

        for connection in result["connections"]:
            self.assertIn("names", connection)
            self.assertIn("emailAddresses", connection)
            self.assertNotIn("phoneNumbers", connection)

    def test_list_connections_enum_serialization(self):
        """Test that enum values are properly serialized as strings (Bug #1007 fix)."""
        from ..SimulationEngine.models import PhoneNumber, PhoneType, Person, EmailAddress, EmailType, Address, AddressType
        
        # Create a person with Pydantic model instances containing enum types
        test_person = Person(
            resourceName='people/test_enum_serialization',
            etag='etag_test_enum',
            phoneNumbers=[
                PhoneNumber(
                    value='+1-555-123-4567',
                    type=PhoneType.MOBILE,
                    formattedType='Mobile'
                ),
                PhoneNumber(
                    value='+1-555-987-6543',
                    type=PhoneType.HOME,
                    formattedType='Home'
                )
            ],
            emailAddresses=[
                EmailAddress(
                    value='test@example.com',
                    type=EmailType.WORK,
                    formattedType='Work'
                )
            ],
            addresses=[
                Address(
                    type=AddressType.HOME,
                    formattedValue='123 Main St, City, State',
                    city='City',
                    region='State',
                    postalCode='12345'
                )
            ]
        )
        
        # Store in DB
        from ..SimulationEngine.db import DB
        DB.set('people', {'people/test_enum_serialization': test_person})
        
        # Test list_connections
        result = list_connections()
        
        # Find our test connection
        test_connection = None
        for connection in result["connections"]:
            if connection.get('resourceName') == 'people/test_enum_serialization':
                test_connection = connection
                break
        
        self.assertIsNotNone(test_connection, "Test connection not found in results")
        
        # Check phone numbers - enum values should be strings
        phone_numbers = test_connection.get('phoneNumbers', [])
        self.assertEqual(len(phone_numbers), 2)
        
        for i, phone in enumerate(phone_numbers):
            phone_type = phone.get('type')
            self.assertIsInstance(phone_type, str, f"Phone {i} type should be string, got {type(phone_type)}: {phone_type}")
            self.assertIn(phone_type, ['mobile', 'home'], f"Phone {i} type should be valid enum value, got: {phone_type}")
        
        # Check email addresses - enum values should be strings
        email_addresses = test_connection.get('emailAddresses', [])
        self.assertEqual(len(email_addresses), 1)
        
        for i, email in enumerate(email_addresses):
            email_type = email.get('type')
            self.assertIsInstance(email_type, str, f"Email {i} type should be string, got {type(email_type)}: {email_type}")
            self.assertIn(email_type, ['work', 'home', 'other'], f"Email {i} type should be valid enum value, got: {email_type}")
        
        # Check addresses - enum values should be strings
        addresses = test_connection.get('addresses', [])
        self.assertEqual(len(addresses), 1)
        
        for i, address in enumerate(addresses):
            address_type = address.get('type')
            self.assertIsInstance(address_type, str, f"Address {i} type should be string, got {type(address_type)}: {address_type}")
            self.assertIn(address_type, ['home', 'work', 'other'], f"Address {i} type should be valid enum value, got: {address_type}")

    def test_search_people_success(self):
        """Test successful search of people."""
        result = search_people("john", read_mask="names,emailAddresses,organizations,phoneNumbers")

        self.assertIn("results", result)
        self.assertIn("totalItems", result)
        self.assertEqual(len(result["results"]), 2)  # Now finds both John Doe and Alice Johnson
        # Check that John Doe is found
        john_found = any(person["names"][0]["givenName"] == "John" for person in result["results"])
        self.assertTrue(john_found)

    def test_search_people_by_email(self):
        """Test searching people by email address."""
        result = search_people("john.doe@example.com", read_mask="names,emailAddresses,phoneNumbers")

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["emailAddresses"][0]["value"], "john.doe@example.com")

    def test_search_people_by_organization(self):
        """Test searching people by organization."""
        result = search_people("Tech Corp", read_mask="names,organizations")

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["organizations"][0]["name"], "Tech Corp")

    def test_search_people_with_read_mask(self):
        """Test searching people with read mask filtering."""
        result = search_people("john", read_mask="names,emailAddresses")

        for person in result["results"]:
            self.assertIn("names", person)
            self.assertIn("emailAddresses", person)
            self.assertNotIn("phoneNumbers", person)

    def test_search_people_handles_none_values(self):
        """Test that search_people handles None values in data gracefully."""
        from ..SimulationEngine.db import DB
        
        # Add data with None values that could cause AttributeError
        DB.set("people", {
            "people/test_none": {
                "resourceName": "people/test_none",
                "etag": "etag_test_none",
                "names": None,  # This could cause issues
                "emailAddresses": None,  # This could cause issues
                "organizations": None  # This could cause issues
            },
            "people/test_partial_none": {
                "resourceName": "people/test_partial_none",
                "etag": "etag_test_partial_none",
                "names": [
                    {"displayName": "Test User", "givenName": "Test", "familyName": "User"},
                    {"displayName": None, "givenName": None, "familyName": None}  # None values in list
                ],
                "emailAddresses": [
                    {"value": "test@example.com", "type": "work"},
                    {"value": None, "type": "work"}  # None value in list
                ],
                "organizations": [
                    {"name": "Test Corp", "title": "Developer"},
                    {"name": None, "title": None}  # None values in list
                ]
            }
        })
        
        # These should not raise AttributeError
        result1 = search_people("test", read_mask="names,emailAddresses")
        self.assertIn("results", result1)
        self.assertIn("totalItems", result1)
        
        result2 = search_people("user", read_mask="names,emailAddresses")
        self.assertIn("results", result2)
        self.assertIn("totalItems", result2)
        
        result3 = search_people("example.com", read_mask="names,emailAddresses")
        self.assertIn("results", result3)
        self.assertIn("totalItems", result3)
        
        result4 = search_people("corp", read_mask="names,emailAddresses")
        self.assertIn("results", result4)
        self.assertIn("totalItems", result4)

    def test_search_people_missing_read_mask_error(self):
        """Test that search_people raises error when read_mask is missing."""
        # Since the function signature requires read_mask as a positional argument,
        # we test this by passing None which will trigger validation error
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            query="john",
            read_mask=None
        )

    def test_search_people_empty_read_mask_error(self):
        """Test that search_people raises error when read_mask is empty."""
        # Test empty string
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="read_mask cannot be empty",
            query="john",
            read_mask=""
        )
        
        # Test whitespace-only string
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="read_mask cannot be empty",
            query="john",
            read_mask="   "
        )

    def test_search_people_invalid_read_mask_fields(self):
        """Test that search_people raises error when read_mask contains invalid fields."""
        # Test invalid field name
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid field(s) in read_mask",
            query="john",
            read_mask="names,invalidField"
        )

    def test_search_people_valid_read_mask(self):
        """Test that search_people accepts valid read_mask values."""
        # Test single valid field
        result = search_people(query="john", read_mask="names")
        self.assertIn("results", result)
        
        # Test multiple valid fields
        result = search_people(query="john", read_mask="names,emailAddresses,phoneNumbers")
        self.assertIn("results", result)
        
        # Test fields with spaces (should be trimmed)
        result = search_people(query="john", read_mask="names, emailAddresses , phoneNumbers")
        self.assertIn("results", result)
        
        # Test mandatory fields
        result = search_people(query="john", read_mask="resourceName,etag")
        self.assertIn("results", result)
        
        # Test that trailing commas are now allowed
        result = search_people(query="john", read_mask="names,")
        self.assertIn("results", result)
        
        # Test that leading commas are now allowed
        result = search_people(query="john", read_mask=",names")
        self.assertIn("results", result)
        
        # Test that double commas are now allowed
        result = search_people(query="john", read_mask="names,,emailAddresses")
        self.assertIn("results", result)

    def test_search_people_read_mask_includes_mandatory_fields(self):
        """Test that read_mask always includes mandatory fields like resourceName."""
        result = search_people("john", read_mask="names,emailAddresses")

        for person in result["results"]:
            # Mandatory fields should always be included
            self.assertIn("resourceName", person)
            self.assertIn("etag", person)
            self.assertIn("names", person)
            self.assertIn("emailAddresses", person)
            self.assertNotIn("phoneNumbers", person)
            self.assertNotIn("addresses", person)

    def test_search_people_with_special_characters(self):
        """Test searching people with special characters like apostrophes."""
        result = search_people("O'Connor", read_mask="names,emailAddresses")

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["names"][0]["familyName"], "O'Connor")

    def test_search_people_by_phone_number(self):
        """Test searching people by phone number with normalization."""
        # The stored phone is +1-555-123-4567; query without separators should match
        result = search_people("+1555123", read_mask="phoneNumbers")
        self.assertIn("results", result)
        self.assertGreaterEqual(len(result["results"]), 1)
        self.assertIn("phoneNumbers", result["results"][0])

    def test_search_people_by_nickname(self):
        """Test searching people by nickname (added via create_contact)."""
        created = create_contact({
            "names": [{"displayName": "John Nick", "givenName": "John", "familyName": "Nick"}],
            "emailAddresses": [{"value": "john.nick@example.com"}],
            "nicknames": [{"value": "Johnny"}]
        })

        result = search_people("Johnny", read_mask="nicknames")
        self.assertIn("results", result)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result["results"]))

    def test_search_people_by_nickname_case_insensitive(self):
        """Test searching people by nickname with case insensitive matching."""
        created = create_contact({
            "names": [{"displayName": "Jane Doe", "givenName": "Jane", "familyName": "Doe"}],
            "emailAddresses": [{"value": "jane.doe@example.com"}],
            "nicknames": [{"value": "JaneD"}]
        })

        # Test lowercase search for uppercase nickname
        result = search_people("janed", read_mask="nicknames")
        self.assertIn("results", result)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result["results"]))

        # Test uppercase search for lowercase nickname
        created2 = create_contact({
            "names": [{"displayName": "Bob Smith", "givenName": "Bob", "familyName": "Smith"}],
            "emailAddresses": [{"value": "bob.smith@example.com"}],
            "nicknames": [{"value": "bobby"}]
        })

        result2 = search_people("BOBBY", read_mask="nicknames")
        self.assertIn("results", result2)
        self.assertTrue(any(p.get("resourceName") == created2.get("resourceName") for p in result2["results"]))

    def test_search_people_by_nickname_partial_match(self):
        """Test searching people by nickname with partial matching."""
        created = create_contact({
            "names": [{"displayName": "Alice Johnson", "givenName": "Alice", "familyName": "Johnson"}],
            "emailAddresses": [{"value": "alice.johnson@example.com"}],
            "nicknames": [{"value": "AllyCat"}]
        })

        # Test partial match
        result = search_people("Ally", read_mask="nicknames")
        self.assertIn("results", result)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result["results"]))

        # Test another partial match
        result2 = search_people("Cat", read_mask="nicknames")
        self.assertIn("results", result2)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result2["results"]))

    def test_search_people_by_multiple_nicknames(self):
        """Test searching people with multiple nicknames."""
        created = create_contact({
            "names": [{"displayName": "Charlie Brown", "givenName": "Charlie", "familyName": "Brown"}],
            "emailAddresses": [{"value": "charlie.brown@example.com"}],
            "nicknames": [
                {"value": "Chuck"},
                {"value": "CB"},
                {"value": "CharlieBoy"}
            ]
        })

        # Test search by first nickname
        result1 = search_people("Chuck", read_mask="nicknames")
        self.assertIn("results", result1)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result1["results"]))

        # Test search by second nickname
        result2 = search_people("CB", read_mask="nicknames")
        self.assertIn("results", result2)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result2["results"]))

        # Test search by third nickname
        result3 = search_people("CharlieBoy", read_mask="nicknames")
        self.assertIn("results", result3)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result3["results"]))

    def test_search_people_by_nickname_with_metadata(self):
        """Test searching people by nickname that includes metadata."""
        created = create_contact({
            "names": [{"displayName": "David Wilson", "givenName": "David", "familyName": "Wilson"}],
            "emailAddresses": [{"value": "david.wilson@example.com"}],
            "nicknames": [{
                "value": "Dave",
                "type": "DEFAULT",
                "metadata": {
                    "primary": True,
                    "sourcePrimary": True,
                    "verified": True,
                    "source": {
                        "type": "PROFILE",
                        "id": "test-source-id",
                        "etag": "test-etag",
                        "updateTime": "2023-01-01T00:00:00Z"
                    }
                }
            }]
        })

        result = search_people("Dave", read_mask="nicknames")
        self.assertIn("results", result)
        self.assertTrue(any(p.get("resourceName") == created.get("resourceName") for p in result["results"]))

    def test_search_people_by_nickname_no_results(self):
        """Test searching people by nickname that doesn't exist."""
        # Create a contact without the searched nickname
        created = create_contact({
            "names": [{"displayName": "Eve Adams", "givenName": "Eve", "familyName": "Adams"}],
            "emailAddresses": [{"value": "eve.adams@example.com"}],
            "nicknames": [{"value": "Eve"}]
        })

        # Search for a nickname that doesn't exist
        result = search_people("NonExistentNickname", read_mask="nicknames")
        self.assertIn("results", result)
        # Should not find the contact since nickname doesn't match
        self.assertFalse(any(p.get("resourceName") == created.get("resourceName") for p in result["results"]))

    def test_get_batch_get_success(self):
        """Test successful batch retrieval of people."""
        result = get_batch_get(["people/123456789", "people/987654321"])

        self.assertIn("responses", result)
        self.assertIn("notFound", result)
        self.assertEqual(len(result["responses"]), 2)
        self.assertEqual(len(result["notFound"]), 0)

    def test_get_batch_get_with_missing_people(self):
        """Test batch retrieval with some missing people."""
        result = get_batch_get(["people/123456789", "people/nonexistent"])

        self.assertEqual(len(result["responses"]), 1)
        self.assertEqual(len(result["notFound"]), 1)
        self.assertIn("people/nonexistent", result["notFound"])

    def test_get_batch_get_with_fields_filter(self):
        """Test batch retrieval with field filtering."""
        result = get_batch_get(["people/123456789"], person_fields="names,emailAddresses")

        person = result["responses"][0]
        self.assertIn("names", person)
        self.assertIn("emailAddresses", person)
        self.assertNotIn("phoneNumbers", person)

    def test_get_directory_person_success(self):
        """Test successful retrieval of a directory person."""
        result = get_directory_person("directoryPeople/111222333")

        self.assertEqual(result["resourceName"], "directoryPeople/111222333")
        self.assertEqual(result["etag"], "etag_dir_111222333")
        self.assertEqual(len(result["names"]), 1)
        self.assertEqual(result["names"][0]["displayName"], "Bob Wilson")

    def test_get_directory_person_not_found(self):
        """Test directory person retrieval when person doesn't exist."""
        self.assert_error_behavior(
            func_to_call=get_directory_person,
            expected_exception_type=ValueError,
            expected_message="Directory person with resource name 'directoryPeople/nonexistent' not found",
            resource_name="directoryPeople/nonexistent"
        )

    def test_get_directory_person_with_read_mask(self):
        """Test directory person retrieval with read mask filtering."""
        result = get_directory_person("directoryPeople/111222333", read_mask="names,emailAddresses")

        self.assertIn("names", result)
        self.assertIn("emailAddresses", result)
        self.assertNotIn("organizations", result)

    def test_list_directory_people_success(self):
        """Test successful listing of directory people."""
        result = list_directory_people(read_mask="names,emailAddresses")

        self.assertIn("people", result)
        self.assertIn("totalItems", result)
        self.assertEqual(len(result["people"]), 1)

    def test_list_directory_people_without_read_mask(self):
        """Test listing directory people without required read_mask."""
        self.assert_error_behavior(
            func_to_call=list_directory_people,
            expected_exception_type=ValueError,
            expected_message="read_mask is required for list_directory_people"
        )

    def test_list_directory_people_with_pagination(self):
        """Test listing directory people with pagination."""
        result = list_directory_people(read_mask="names", page_size=1)

        self.assertEqual(len(result["people"]), 1)
        self.assertIn("nextPageToken", result)

    def test_search_directory_people_success(self):
        """Test successful search of directory people."""
        result = search_directory_people("bob", read_mask="names,emailAddresses")

        self.assertIn("results", result)
        self.assertIn("totalItems", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["names"][0]["givenName"], "Bob")

    def test_search_directory_people_without_read_mask(self):
        """Test searching directory people without required read_mask."""
        self.assert_error_behavior(
            func_to_call=search_directory_people,
            expected_exception_type=ValueError,
            expected_message="read_mask is required for search_directory_people",
            query="bob"
        )

    def test_search_directory_people_with_pagination(self):
        """Test searching directory people with pagination."""
        result = search_directory_people("bob", read_mask="names", page_size=1)

        self.assertEqual(len(result["results"]), 1)
        self.assertIn("nextPageToken", result)

    def test_search_directory_people_by_email(self):
        """Test searching directory people by email address."""
        result = search_directory_people("bob.wilson@company.com", read_mask="names,emailAddresses")

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["emailAddresses"][0]["value"], "bob.wilson@company.com")

    def test_search_directory_people_by_organization(self):
        """Test searching directory people by organization."""
        result = search_directory_people("Company Inc", read_mask="names,organizations")

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["organizations"][0]["name"], "Company Inc")

    def test_search_people_invalid_sources_enum(self):
        """Test that search_people rejects invalid source enum values."""
        # Test with shell command injection attempt
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["READ_SOURCE_TYPE_PROFILE", "; rm -rf /", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))
        self.assertIn("; rm -rf /", str(context.exception))

        # Test with completely invalid values
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["INVALID_SOURCE", "ANOTHER_INVALID"]
            )
        self.assertIn("Invalid source values", str(context.exception))
        self.assertIn("INVALID_SOURCE", str(context.exception))
        self.assertIn("ANOTHER_INVALID", str(context.exception))

        # Test with empty string
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["", "READ_SOURCE_TYPE_PROFILE"]
            )
        self.assertIn("Invalid source values", str(context.exception))

        # Test with None values in list
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=[None, "READ_SOURCE_TYPE_PROFILE"]
            )
        # Pydantic catches None values before our custom validator
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_search_people_valid_sources_enum(self):
        """Test that search_people accepts valid source enum values."""
        # Test with all valid sources
        result = search_people(
            query="test",
            read_mask="names",
            sources=[
                "READ_SOURCE_TYPE_PROFILE",
                "READ_SOURCE_TYPE_CONTACT",
                "READ_SOURCE_TYPE_DOMAIN_CONTACT",
                "READ_SOURCE_TYPE_OTHER_CONTACT"
            ]
        )
        self.assertIn("results", result)

        # Test with single valid source
        result = search_people(
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE"]
        )
        self.assertIn("results", result)

        # Test with None sources (should be allowed)
        result = search_people(
            query="test",
            read_mask="names",
            sources=None
        )
        self.assertIn("results", result)

    def test_get_batch_get_invalid_sources_enum(self):
        """Test that get_batch_get rejects invalid source enum values."""
        # Test with shell command injection attempt
        with self.assertRaises(PydanticValidationError) as context:
            get_batch_get(
                resource_names=["people/123456789"],
                sources=["READ_SOURCE_TYPE_PROFILE", "| cat /etc/passwd", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))
        self.assertIn("| cat /etc/passwd", str(context.exception))

        # Test with completely invalid values
        with self.assertRaises(PydanticValidationError) as context:
            get_batch_get(
                resource_names=["people/123456789"],
                sources=["MALICIOUS_SOURCE", "INJECTION_ATTEMPT"]
            )
        self.assertIn("Invalid source values", str(context.exception))

    def test_get_batch_get_valid_sources_enum(self):
        """Test that get_batch_get accepts valid source enum values."""
        # Test with valid sources
        result = get_batch_get(
            resource_names=["people/123456789"],
            sources=["READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT"]
        )
        self.assertIn("responses", result)

    def test_get_contact_invalid_sources_enum(self):
        """Test that get_contact rejects invalid source enum values."""
        # Test with shell command injection attempt
        with self.assertRaises(PydanticValidationError) as context:
            get_contact(
                resource_name="people/123456789",
                sources=["READ_SOURCE_TYPE_PROFILE", "`whoami`", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))
        self.assertIn("`whoami`", str(context.exception))

    def test_get_contact_valid_sources_enum(self):
        """Test that get_contact accepts valid source enum values."""
        # Test with valid sources
        result = get_contact(
            resource_name="people/123456789",
            sources=["READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT"]
        )
        self.assertIn("resourceName", result)

    def test_search_directory_people_invalid_sources_enum(self):
        """Test that search_directory_people rejects invalid source enum values."""
        # Test with shell command injection attempt
        with self.assertRaises(PydanticValidationError) as context:
            search_directory_people(
                query="test",
                read_mask="names",
                sources=["READ_SOURCE_TYPE_PROFILE", "&& echo 'hacked'", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))
        self.assertIn("&& echo 'hacked'", str(context.exception))

        # Test with completely invalid values
        with self.assertRaises(PydanticValidationError) as context:
            search_directory_people(
                query="test",
                read_mask="names",
                sources=["INVALID_SOURCE", "SHELL_INJECTION"]
            )
        self.assertIn("Invalid source values", str(context.exception))

    def test_search_directory_people_valid_sources_enum(self):
        """Test that search_directory_people accepts valid source enum values."""
        # Test with valid sources
        result = search_directory_people(
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_OTHER_CONTACT"]
        )
        self.assertIn("results", result)

    def test_sources_enum_security_edge_cases(self):
        """Test various security edge cases for sources parameter."""
        # Test with SQL injection attempt
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["READ_SOURCE_TYPE_PROFILE", "'; DROP TABLE users; --", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))

        # Test with path traversal attempt
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["READ_SOURCE_TYPE_PROFILE", "../../../etc/passwd", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))

        # Test with XSS attempt
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["READ_SOURCE_TYPE_PROFILE", "<script>alert('xss')</script>", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))

        # Test with mixed case valid values (should be rejected)
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["read_source_type_profile", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))

        # Test with partial valid values (should be rejected)
        with self.assertRaises(PydanticValidationError) as context:
            search_people(
                query="test",
                read_mask="names",
                sources=["READ_SOURCE_TYPE_PROFILE_EXTRA", "READ_SOURCE_TYPE_CONTACT"]
            )
        self.assertIn("Invalid source values", str(context.exception))

    def test_models_validation_edge_cases(self):
        """Test edge cases for model validation to ensure full coverage."""
        from ..SimulationEngine.models import (
            CreateContactRequest, UpdateContactRequest, Person, Name, EmailAddress
        )
        
        # Test CreateContactRequest with missing names
        with self.assertRaises(PydanticValidationError) as context:
            person_data = Person(
                names=[],  # Empty names list
                emailAddresses=[EmailAddress(value="test@example.com")]
            )
            CreateContactRequest(person_data=person_data)
        self.assertIn("At least one name is required", str(context.exception))
        
        # Test CreateContactRequest with missing email addresses
        with self.assertRaises(PydanticValidationError) as context:
            person_data = Person(
                names=[Name(displayName="Test User")],
                emailAddresses=[]  # Empty email addresses list
            )
            CreateContactRequest(person_data=person_data)
        self.assertIn("At least one email address is required", str(context.exception))
        
        # Test UpdateContactRequest with invalid resource name
        with self.assertRaises(PydanticValidationError) as context:
            person_data = Person(
                names=[Name(displayName="Test User")],
                emailAddresses=[EmailAddress(value="test@example.com")]
            )
            UpdateContactRequest(
                resource_name="invalid_resource",  # Should start with "people/"
                person_data=person_data
            )
        self.assertIn("Resource name must start with \"people/\"", str(context.exception))

    def test_models_etag_validation(self):
        """Test ETag validation to ensure full coverage."""
        from ..SimulationEngine.models import Person, Name, EmailAddress
        
        # Test Person with invalid ETag
        with self.assertRaises(PydanticValidationError) as context:
            Person(
                names=[Name(displayName="Test User")],
                emailAddresses=[EmailAddress(value="test@example.com")],
                etag="invalid_etag"  # Should start with "etag_"
            )
        self.assertIn("ETag must start with \"etag_\"", str(context.exception))

    def test_models_resource_name_validation_edge_cases(self):
        """Test resource name validation edge cases."""
        from ..SimulationEngine.models import GetContactRequest, GetDirectoryPersonRequest, GetOtherContactRequest
        
        # Test GetContactRequest with empty resource name
        with self.assertRaises(PydanticValidationError) as context:
            GetContactRequest(resource_name="")
        # This should fail due to Field(..., description=...) requirement
        
        # Test GetDirectoryPersonRequest with invalid resource name
        with self.assertRaises(PydanticValidationError) as context:
            GetDirectoryPersonRequest(resource_name="invalid_directory_people/123")
        self.assertIn("Resource name must start with \"directoryPeople/\"", str(context.exception))
        
        # Test GetOtherContactRequest with invalid resource name
        with self.assertRaises(PydanticValidationError) as context:
            GetOtherContactRequest(resource_name="invalid_other_contacts/123")
        self.assertIn("Resource name must start with \"otherContacts/\"", str(context.exception))

    def test_models_person_fields_validation(self):
        """Test person fields validation to ensure full coverage."""
        from ..SimulationEngine.models import GetContactRequest
        
        # Test GetContactRequest with invalid person fields
        with self.assertRaises(PydanticValidationError) as context:
            GetContactRequest(
                resource_name="people/123456789",
                person_fields="invalid_field,another_invalid_field"
            )
        self.assertIn("Invalid person fields", str(context.exception))

    def test_models_read_mask_validation(self):
        """Test read mask validation to ensure full coverage."""
        from ..SimulationEngine.models import GetOtherContactRequest
        
        # Test GetOtherContactRequest with invalid read mask
        with self.assertRaises(PydanticValidationError) as context:
            GetOtherContactRequest(
                resource_name="otherContacts/123456789",
                read_mask="invalid_field,another_invalid_field"
            )
        self.assertIn("Invalid read mask fields", str(context.exception))

    def test_models_sort_order_validation(self):
        """Test sort order validation to ensure full coverage."""
        from ..SimulationEngine.models import ListConnectionsRequest
        
        # Test ListConnectionsRequest with invalid sort order
        with self.assertRaises(PydanticValidationError) as context:
            ListConnectionsRequest(sort_order="INVALID_SORT_ORDER")
        self.assertIn("Invalid sort order", str(context.exception))

    def test_models_contact_group_validation(self):
        """Test contact group validation to ensure full coverage."""
        from ..SimulationEngine.models import CreateContactGroupRequest, ContactGroup
        
        # Test CreateContactGroupRequest with invalid contact group type
        with self.assertRaises(PydanticValidationError) as context:
            contact_group = ContactGroup(
                name="Test Group",
                contact_group_type="INVALID_TYPE"
            )
            CreateContactGroupRequest(contact_group=contact_group)
        # This should fail due to invalid enum value

    def test_models_contact_group_member_validation(self):
        """Test contact group member validation to ensure full coverage."""
        from ..SimulationEngine.models import ModifyMembersRequest
        
        # Test ModifyMembersRequest with invalid resource name
        with self.assertRaises(PydanticValidationError) as context:
            ModifyMembersRequest(
                resource_name="invalid_contact_groups/test_group",
                resource_names_to_add=["people/123456789"]
            )
        # This should fail due to invalid resource name format

    def test_additional_security_scenarios(self):
        """Test additional security scenarios commonly reported in bug reports."""
        # Test with command chaining attempts
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "&& echo 'hacked'", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with pipe command attempts
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "| cat /etc/passwd", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with redirect attempts
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "> /tmp/malicious.txt", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with environment variable injection
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "$(whoami)", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with backtick command substitution
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "`id`", "READ_SOURCE_TYPE_CONTACT"]
        )

    def test_unicode_and_encoding_attacks(self):
        """Test Unicode and encoding-based attack attempts."""
        # Test with Unicode escape sequences
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "\u0027; DROP TABLE users; --", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with URL encoding attempts
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "%3Cscript%3Ealert%28%27xss%27%29%3C%2Fscript%3E", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with HTML entity encoding
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "&lt;script&gt;alert('xss')&lt;/script&gt;", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with null byte injection
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "malicious\x00payload", "READ_SOURCE_TYPE_CONTACT"]
        )

    def test_whitespace_and_special_characters(self):
        """Test various whitespace and special character scenarios."""
        # Test with only whitespace
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "   ", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with tabs and newlines
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "\t\n\r", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with special characters
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "!@#$%^&*()", "READ_SOURCE_TYPE_CONTACT"]
        )

        # Test with control characters
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "\x01\x02\x03", "READ_SOURCE_TYPE_CONTACT"]
        )

    def test_boundary_value_attacks(self):
        """Test boundary value and overflow attack attempts."""
        # Test with extremely long strings
        long_string = "A" * 10000
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            sources=["READ_SOURCE_TYPE_PROFILE", long_string, "READ_SOURCE_TYPE_CONTACT"],
            read_mask="names"
        )

        # Test with repeated valid values (should be allowed)
        result = search_people(
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_PROFILE"]
        )
        self.assertIn("results", result)
        
        # Test with duplicate valid values (should be allowed)
        result = search_people(
            query="test",
            read_mask="names",
            sources=["READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT", "READ_SOURCE_TYPE_PROFILE"]
        )
        self.assertIn("results", result)

    def test_case_sensitivity_edge_cases(self):
        """Test various case sensitivity edge cases."""
        # Test with all lowercase
        self.assert_error_behavior(
            func_to_call=search_people,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            query="test",
            read_mask="names",
            sources=["read_source_type_profile", "read_source_type_contact"]
        )

        # Test with mixed case variations
        case_variations = [
            "Read_Source_Type_Profile",
            "read_SOURCE_TYPE_profile",
            "READ_source_TYPE_PROFILE",
            "Read_SOURCE_Type_Profile"
        ]
        
        for variation in case_variations:
            with self.subTest(variation=variation):
                self.assert_error_behavior(
                    func_to_call=search_people,
                    expected_exception_type=PydanticValidationError,
                    expected_message="Invalid source values",
                    query="test",
                    read_mask="names",
                    sources=[variation, "READ_SOURCE_TYPE_CONTACT"]
                )

    def test_unicode_normalization_attacks(self):
        """Test Unicode normalization attack attempts."""
        # Test with Unicode normalization attacks
        unicode_attacks = [
            "READ_SOURCE_TYPE_PROFILE\u200B",  # Zero-width space
            "READ_SOURCE_TYPE_PROFILE\u200C",  # Zero-width non-joiner
            "READ_SOURCE_TYPE_PROFILE\u200D",  # Zero-width joiner
            "READ_SOURCE_TYPE_PROFILE\uFEFF",  # Zero-width no-break space
        ]
        
        for attack in unicode_attacks:
            with self.subTest(attack=repr(attack)):
                self.assert_error_behavior(
                    func_to_call=search_people,
                    expected_exception_type=PydanticValidationError,
                    expected_message="Invalid source values",
                    query="test",
                    read_mask="names",
                    sources=[attack, "READ_SOURCE_TYPE_CONTACT"]
                )

    def test_regex_injection_attempts(self):
        """Test regex injection attempt scenarios."""
        # Test with regex special characters
        regex_attacks = [
            ".*",
            "[a-zA-Z]",
            "READ_SOURCE_TYPE_PROFILE.*",
            "READ_SOURCE_TYPE_PROFILE+",
            "READ_SOURCE_TYPE_PROFILE?",
            "READ_SOURCE_TYPE_PROFILE{1,}",
            "READ_SOURCE_TYPE_PROFILE$",
            "^READ_SOURCE_TYPE_PROFILE"
        ]
        
        for attack in regex_attacks:
            with self.subTest(attack=attack):
                self.assert_error_behavior(
                    func_to_call=search_people,
                    expected_exception_type=PydanticValidationError,
                    expected_message="Invalid source values",
                    query="test",
                    read_mask="names",
                    sources=[attack, "READ_SOURCE_TYPE_CONTACT"]
                )

    def test_missing_models_scenarios(self):
        """Test specific lines that were missing coverage in models.py."""
        from ..SimulationEngine.models import (
            SearchPeopleRequest, BatchGetRequest, GetDirectoryPersonRequest,
            SearchDirectoryPeopleRequest, GetOtherContactRequest
        )
        
        # Test line 316: Empty query validation in SearchPeopleRequest
        self.assert_error_behavior(
            func_to_call=SearchPeopleRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Query cannot be empty",
            query="   "  # Only whitespace
        )
        
        # Empty string is caught by Pydantic's min_length=1 before our custom validator
        self.assert_error_behavior(
            func_to_call=SearchPeopleRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            query=""  # Empty string
        )
        
        # Test line 347: Resource name validation in BatchGetRequest
        self.assert_error_behavior(
            func_to_call=BatchGetRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Resource name invalid_resource must start with \"people/\"",
            resource_names=["invalid_resource", "people/123456789"]
        )
        
        self.assert_error_behavior(
            func_to_call=BatchGetRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Resource name invalid_resource must start with \"people/\"",
            resource_names=["people/123", "invalid_resource", "people/456"]
        )
        
        # Test lines 385-395: Sources validation in GetDirectoryPersonRequest
        self.assert_error_behavior(
            func_to_call=GetDirectoryPersonRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            resource_name="directoryPeople/123456789",
            sources=["INVALID_SOURCE", "READ_SOURCE_TYPE_PROFILE"]
        )
        
        # Test line 418: Empty query validation in SearchDirectoryPeopleRequest
        self.assert_error_behavior(
            func_to_call=SearchDirectoryPeopleRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Query cannot be empty",
            query="   "  # Only whitespace
        )
        
        # Empty string is caught by Pydantic's min_length=1 before our custom validator
        self.assert_error_behavior(
            func_to_call=SearchDirectoryPeopleRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            query=""  # Empty string
        )
        
        # Test lines 695-705: Sources validation in GetOtherContactRequest
        self.assert_error_behavior(
            func_to_call=GetOtherContactRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            resource_name="otherContacts/123456789",
            sources=["INVALID_SOURCE", "READ_SOURCE_TYPE_PROFILE"]
        )

    def test_query_validation_edge_cases(self):
        """Test query validation edge cases for comprehensive coverage."""
        from ..SimulationEngine.models import SearchPeopleRequest, SearchDirectoryPeopleRequest
        
        # Test various whitespace patterns
        whitespace_queries = [" ", "\t", "\n", "\r", "   ", "\t\n\r "]
        
        for query in whitespace_queries:
            with self.subTest(query=repr(query)):
                # Test SearchPeopleRequest
                self.assert_error_behavior(
                    func_to_call=SearchPeopleRequest,
                    expected_exception_type=PydanticValidationError,
                    expected_message="Query cannot be empty",
                    query=query
                )
                
                # Test SearchDirectoryPeopleRequest
                self.assert_error_behavior(
                    func_to_call=SearchDirectoryPeopleRequest,
                    expected_exception_type=PydanticValidationError,
                    expected_message="Query cannot be empty",
                    query=query
                )

    def test_resource_names_validation_comprehensive(self):
        """Test comprehensive resource names validation in BatchGetRequest."""
        from ..SimulationEngine.models import BatchGetRequest
        
        # Test multiple invalid resource names (validator stops at first invalid)
        self.assert_error_behavior(
            func_to_call=BatchGetRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Resource name invalid1 must start with \"people/\"",
            resource_names=[
                "invalid1",
                "people/123456789", 
                "invalid2",
                "people/987654321",
                "invalid3"
            ]
        )
        
        # Test single invalid resource name
        self.assert_error_behavior(
            func_to_call=BatchGetRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Resource name completely_invalid must start with \"people/\"",
            resource_names=["completely_invalid"]
        )

    def test_sources_validation_comprehensive_coverage(self):
        """Test comprehensive sources validation for all models to ensure full coverage."""
        from ..SimulationEngine.models import (
            GetDirectoryPersonRequest, GetOtherContactRequest
        )
        
        # Test GetDirectoryPersonRequest sources validation (lines 385-395)
        invalid_sources = ["INVALID1", "INVALID2", "READ_SOURCE_TYPE_PROFILE"]
        
        self.assert_error_behavior(
            func_to_call=GetDirectoryPersonRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            resource_name="directoryPeople/123456789",
            sources=invalid_sources
        )
        
        # Test GetOtherContactRequest sources validation (lines 695-705)
        self.assert_error_behavior(
            func_to_call=GetOtherContactRequest,
            expected_exception_type=PydanticValidationError,
            expected_message="Invalid source values",
            resource_name="otherContacts/123456789",
            sources=invalid_sources
        )

    def test_valid_cases_for_coverage(self):
        """Test valid cases to ensure the validation logic paths are covered."""
        from ..SimulationEngine.models import (
            SearchPeopleRequest, BatchGetRequest, GetDirectoryPersonRequest,
            SearchDirectoryPeopleRequest, GetOtherContactRequest
        )
        
        # Test valid SearchPeopleRequest with query stripping
        valid_search = SearchPeopleRequest(query="  valid query  ", read_mask="names")
        self.assertEqual(valid_search.query, "valid query")  # Should be stripped
        
        # Test valid BatchGetRequest
        valid_batch = BatchGetRequest(resource_names=["people/123", "people/456"])
        self.assertEqual(len(valid_batch.resource_names), 2)
        
        # Test valid GetDirectoryPersonRequest with sources
        valid_dir = GetDirectoryPersonRequest(
            resource_name="directoryPeople/123456789",
            sources=["READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT"]
        )
        self.assertEqual(len(valid_dir.sources), 2)
        
        # Test valid SearchDirectoryPeopleRequest with query stripping
        valid_dir_search = SearchDirectoryPeopleRequest(query="  valid search  ")
        self.assertEqual(valid_dir_search.query, "valid search")  # Should be stripped
        
        # Test valid GetOtherContactRequest with sources
        valid_other = GetOtherContactRequest(
            resource_name="otherContacts/123456789",
            sources=["READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT"]
        )
        self.assertEqual(len(valid_other.sources), 2)

    def test_search_people_sources_filtering_contacts_only(self):
        """Test search_people with READ_SOURCE_TYPE_CONTACT source filtering."""
        result = search_people("John", read_mask="names,emailAddresses", sources=["READ_SOURCE_TYPE_CONTACT"])
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["resourceName"], "people/123456789")

    def test_search_people_sources_filtering_domain_contact_only(self):
        """Test search_people with READ_SOURCE_TYPE_DOMAIN_CONTACT source filtering."""
        result = search_people("Bob", read_mask="names,emailAddresses", sources=["READ_SOURCE_TYPE_DOMAIN_CONTACT"])
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["resourceName"], "directoryPeople/111222333")

    def test_search_people_sources_filtering_other_contact_only(self):
        """Test search_people with READ_SOURCE_TYPE_OTHER_CONTACT source filtering."""
        result = search_people("Alice", read_mask="names,emailAddresses", sources=["READ_SOURCE_TYPE_OTHER_CONTACT"])
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["resourceName"], "otherContacts/555666777")

    def test_search_people_sources_filtering_profile_only(self):
        """Test search_people with READ_SOURCE_TYPE_PROFILE source filtering."""
        result = search_people("John", read_mask="names,emailAddresses", sources=["READ_SOURCE_TYPE_PROFILE"])
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["resourceName"], "people/123456789")

    def test_search_people_sources_filtering_multiple_sources(self):
        """Test search_people with multiple source types."""
        result = search_people("John", read_mask="names,emailAddresses", sources=["READ_SOURCE_TYPE_CONTACT", "READ_SOURCE_TYPE_DOMAIN_CONTACT"])
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["resourceName"], "people/123456789")

    def test_search_people_sources_filtering_no_sources_specified(self):
        """Test search_people with no sources specified (should search all collections)."""
        result = search_people("John", read_mask="names,emailAddresses", sources=None)
        
        self.assertIn("results", result)
        # Should find John from people collection
        self.assertGreaterEqual(len(result["results"]), 1)
        john_found = any(person["resourceName"] == "people/123456789" for person in result["results"])
        self.assertTrue(john_found)

    def test_search_people_sources_filtering_invalid_source(self):
        """Test search_people with invalid source type."""
        with self.assertRaises(PydanticValidationError) as context:
            search_people("John", read_mask="names", sources=["INVALID_SOURCE"])
        
        self.assertIn("Invalid source values", str(context.exception))
        self.assertIn("INVALID_SOURCE", str(context.exception))

    def test_search_people_sources_filtering_empty_sources_list(self):
        """Test search_people with empty sources list."""
        result = search_people("John", read_mask="names,emailAddresses", sources=[])
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 0)

    def test_search_people_sources_filtering_cross_collection_search(self):
        """Test that sources filtering correctly limits search to specified collections."""
        # Search for "Bob" with only contacts source - should not find directory people
        result = search_people("Bob", read_mask="names,emailAddresses", sources=["READ_SOURCE_TYPE_CONTACT"])
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 0)

    def test_search_people_sources_filtering_verification(self):
        """Test that sources filtering works correctly by verifying no cross-contamination."""
        # Search for "John" in domain contact only - should not find people collection
        result = search_people("John", read_mask="names,emailAddresses", sources=["READ_SOURCE_TYPE_DOMAIN_CONTACT"])
        
        self.assertIn("results", result)
        # Should not find John from people collection
        john_from_people_found = any(person["resourceName"] == "people/123456789" for person in result["results"])
        self.assertFalse(john_from_people_found)

    def test_search_people_bug_993_fix_verification(self):
        """Test verification for bug #993: enum serialization and None handling."""
        from ..SimulationEngine.db import DB
        
        # Add data that could cause issues
        DB.get("people")["people/bug_993_test"] = {
            "resourceName": "people/bug_993_test",
            "etag": "etag_bug_993",
            "names": [{"displayName": None, "givenName": None, "familyName": None}],
            "phoneNumbers": [{"value": "+1-555-555-5555", "type": "work"}],
            "emailAddresses": [{"value": "bug@example.com"}]
        }
        
        # 1. Test enum serialization
        result = search_people("bug@example.com", read_mask="phoneNumbers")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        phone_numbers = result["results"][0].get("phoneNumbers")
        self.assertIsNotNone(phone_numbers)
        self.assertEqual(len(phone_numbers), 1)
        # Ensure the enum is serialized to a string
        self.assertEqual(phone_numbers[0].get("type"), "work")

        # 2. Test None handling in names
        result_none = search_people("bug@example.com", read_mask="names")
        # The main thing is that this should not raise an AttributeError.
        self.assertIn("results", result_none)
        self.assertEqual(len(result_none["results"]), 1)
        names = result_none["results"][0].get("names")
        self.assertIsNotNone(names)
        self.assertEqual(len(names), 1)
        self.assertIsNone(names[0].get("displayName"))
    def test_search_people_safety_net_enum_objects(self):
        """Test that search_people handles enum objects gracefully with safety net."""
        from google_people.SimulationEngine.models import PhoneType
        from ..SimulationEngine.db import DB
        
        # Create a test record with enum objects (simulating old buggy behavior)
        test_record = {
            "resourceName": "people/test_enum_safety",
            "etag": "etag_test_enum_safety",
            "names": [{"displayName": "Safety Test User", "givenName": "Safety", "familyName": "Test"}],
            "emailAddresses": [{"value": "safety.test@example.com", "type": "work"}],
            "phoneNumbers": [
                {
                    "value": "+1-555-999-7777",
                    "type": PhoneType.MOBILE  # This is an enum object - should trigger safety net
                }
            ],
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z"
        }
        
        # Add the test record to the database
        people_data = DB.get("people", {})
        people_data["people/test_enum_safety"] = test_record
        DB.set("people", people_data)
        
        try:
            # Test search_people function with enum objects
            result = search_people("Safety Test", read_mask="resourceName,names,phoneNumbers")
            
            # Should not return None (safety net should prevent serialization failure)
            self.assertIsNotNone(result, "search_people should not return None even with enum objects")
            
            # Should find the test record
            self.assertGreater(result["totalItems"], 0, "Should find the test record")
            
            # Check that phone types are converted to strings
            found_test_record = False
            for person in result["results"]:
                if person["resourceName"] == "people/test_enum_safety":
                    found_test_record = True
                    if "phoneNumbers" in person:
                        for phone in person["phoneNumbers"]:
                            phone_type = phone.get("type")
                            # Should be a string, not an enum object
                            self.assertIsInstance(phone_type, str, 
                                f"Phone type should be string, got {type(phone_type)}: {phone_type}")
                            self.assertEqual(phone_type, "mobile", 
                                f"Phone type should be 'mobile', got '{phone_type}'")
                    break
            
            self.assertTrue(found_test_record, "Should find the test record in results")
            
        finally:
            # Clean up: remove the test record
            people_data = DB.get("people", {})
            if "people/test_enum_safety" in people_data:
                del people_data["people/test_enum_safety"]
                DB.set("people", people_data)

    def test_search_people_safety_net_serialization(self):
        """Test that search_people results can be JSON serialized even with enum objects."""
        from google_people.SimulationEngine.models import PhoneType
        from ..SimulationEngine.db import DB
        import json
        
        # Create a test record with enum objects
        test_record = {
            "resourceName": "people/test_serialization",
            "etag": "etag_test_serialization",
            "names": [{"displayName": "Serialization Test", "givenName": "Serialization", "familyName": "Test"}],
            "emailAddresses": [{"value": "serialization.test@example.com", "type": "work"}],
            "phoneNumbers": [
                {
                    "value": "+1-555-888-6666",
                    "type": PhoneType.WORK  # Enum object
                },
                {
                    "value": "+1-555-777-5555",
                    "type": PhoneType.HOME  # Another enum object
                }
            ],
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z"
        }
        
        # Add the test record to the database
        people_data = DB.get("people", {})
        people_data["people/test_serialization"] = test_record
        DB.set("people", people_data)
        
        try:
            # Test search_people function
            result = search_people("Serialization", read_mask="resourceName,names,phoneNumbers")
            
            # Should not return None
            self.assertIsNotNone(result, "search_people should not return None")
            
            # Should be able to serialize the result to JSON
            try:
                json_str = json.dumps(result)
                self.assertIsInstance(json_str, str, "Result should be serializable to JSON string")
            except Exception as e:
                self.fail(f"Result should be JSON serializable, but got error: {e}")
            
            # Verify phone types are strings in the serialized result
            parsed_result = json.loads(json_str)
            found_test_record = False
            for person in parsed_result["results"]:
                if person["resourceName"] == "people/test_serialization":
                    found_test_record = True
                    if "phoneNumbers" in person:
                        for phone in person["phoneNumbers"]:
                            phone_type = phone.get("type")
                            self.assertIsInstance(phone_type, str, 
                                f"Phone type should be string after serialization, got {type(phone_type)}")
                        # Check specific values
                        phone_types = [phone.get("type") for phone in person["phoneNumbers"]]
                        self.assertIn("work", phone_types, "Should have 'work' phone type")
                        self.assertIn("home", phone_types, "Should have 'home' phone type")
                    break
            
            self.assertTrue(found_test_record, "Should find the test record in serialized results")
            
        finally:
            # Clean up: remove the test record
            people_data = DB.get("people", {})
            if "people/test_serialization" in people_data:
                del people_data["people/test_serialization"]
                DB.set("people", people_data)


if __name__ == '__main__':
    unittest.main()
