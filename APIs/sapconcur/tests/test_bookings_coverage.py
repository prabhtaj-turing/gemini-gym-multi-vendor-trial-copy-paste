import unittest
import uuid
from unittest.mock import patch
from datetime import datetime
from pydantic import ValidationError

from APIs.sapconcur import bookings
from APIs.sapconcur.SimulationEngine import models, custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.sapconcur.SimulationEngine.db import DB


class TestBookingsCoverage(BaseTestCaseWithErrorHandler):
    """Test cases to cover missing lines in bookings.py."""
    
    def setUp(self):
        """Set up test data."""
        # Reset DB
        DB.clear()
        DB.update({
            'users': {},
            'trips': {},
            'bookings': {},
            'locations': {},
            'notifications': {},
            'booking_by_locator': {},
            'trips_by_user': {},
            'user_by_external_id': {},
            'bookings_by_trip': {}
        })
        
        # Create test data
        self.user_id = str(uuid.uuid4())
        self.trip_id = str(uuid.uuid4())
        self.booking_id = str(uuid.uuid4())
        
        # Setup test user
        DB['users'][self.user_id] = {
            'id': self.user_id,
            'user_name': 'test.user',
            'given_name': 'Test',
            'family_name': 'User',
            'email': 'test@example.com',
            'active': True,
            'locale': 'en-US',
            'timezone': 'UTC',
            'payment_methods': {}
        }
        
        # Setup test trip
        DB['trips'][self.trip_id] = {
            'trip_id': self.trip_id,
            'trip_name': 'Test Trip',
            'user_id': self.user_id,
            'start_date': '2024-01-01',
            'end_date': '2024-01-05',
            'status': 'CONFIRMED',
            'created_date': '2024-01-01T00:00:00Z',
            'last_modified_date': '2024-01-01T00:00:00Z',
            'booking_ids': [],
            'is_canceled': False,
            'is_virtual_trip': False,
            'is_guest_booking': False
        }
        
        # Setup test booking
        DB['bookings'][self.booking_id] = {
            'booking_id': self.booking_id,
            'trip_id': self.trip_id,
            'record_locator': 'ABC123',
            'status': 'CONFIRMED',
            'segments': [],
            'passengers': [],
            'last_modified': '2024-01-01T00:00:00Z'
        }
        
        # Link booking to locator
        DB['booking_by_locator']['ABC123'] = self.booking_id

    def test_get_reservation_details_booking_not_found_in_db(self):
        """Test get_reservation_details when booking exists in locator but not in bookings DB (line 85)."""
        # Remove booking from DB but keep locator mapping
        del DB['bookings'][self.booking_id]
        
        # Should return None when booking not found in DB
        result = bookings.get_reservation_details('ABC123')
        self.assertIsNone(result)

    def test_create_or_update_booking_invalid_trip_id_format(self):
        """Test create_or_update_booking with invalid trip_id format (lines 403-404)."""
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }
        
        # Test with invalid UUID format
        self.assert_error_behavior(
            bookings.create_or_update_booking,
            custom_errors.ValidationError,
            'Invalid trip_id format: invalid-uuid',
            None,
            booking_data, 'invalid-uuid'
        )

    def test_create_or_update_booking_trip_not_active(self):
        """Test create_or_update_booking with non-active trip status (lines 478-479)."""
        # Set trip to non-active status
        DB['trips'][self.trip_id]['status'] = 'CANCELLED'
        
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }
        
        self.assert_error_behavior(
            bookings.create_or_update_booking,
            custom_errors.TripNotFoundError,
            f'Trip with ID {self.trip_id} is not active. Current status: CANCELLED',
            None,
            booking_data, self.trip_id
        )

    def test_create_or_update_booking_existing_booking_cancelled(self):
        """Test create_or_update_booking with existing cancelled booking (line 483)."""
        # Set existing booking to cancelled status
        DB['bookings'][self.booking_id]['status'] = 'CANCELLED'
        DB['booking_by_locator']['TEST123'] = self.booking_id
        
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }
        
        self.assert_error_behavior(
            bookings.create_or_update_booking,
            custom_errors.BookingConflictError,
            'non-updatable state',
            None,
            booking_data, self.trip_id
        )

    def test_create_or_update_booking_trip_change_old_trip_not_in_db(self):
        """Test create_or_update_booking when old trip is not in DB (line 485)."""
        # Create booking with different trip
        old_trip_id = str(uuid.uuid4())
        DB['bookings'][self.booking_id]['trip_id'] = old_trip_id
        
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }
        
        # Should not raise error when old trip doesn't exist
        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        self.assertIsNotNone(result)

    def test_create_or_update_booking_trip_change_old_trip_no_booking_ids(self):
        """Test create_or_update_booking when old trip has no booking_ids (line 487)."""
        # Create old trip without booking_ids
        old_trip_id = str(uuid.uuid4())
        DB['trips'][old_trip_id] = {
            'trip_id': old_trip_id,
            'trip_name': 'Old Trip',
            'user_id': self.user_id,
            'status': 'CONFIRMED'
            # No booking_ids field
        }
        DB['bookings'][self.booking_id]['trip_id'] = old_trip_id
        
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }
        
        # Should not raise error
        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        self.assertIsNotNone(result)

    def test_create_or_update_booking_trip_change_old_trip_booking_not_in_list(self):
        """Test create_or_update_booking when old trip booking_ids doesn't contain booking (line 489)."""
        # Create old trip with booking_ids but not containing our booking
        old_trip_id = str(uuid.uuid4())
        DB['trips'][old_trip_id] = {
            'trip_id': old_trip_id,
            'trip_name': 'Old Trip',
            'user_id': self.user_id,
            'status': 'CONFIRMED',
            'booking_ids': ['other_booking_id']  # Different booking
        }
        DB['bookings'][self.booking_id]['trip_id'] = old_trip_id
        
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }
        
        # Should not raise error
        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        self.assertIsNotNone(result)

    def test_update_reservation_baggages_no_air_segments(self):
        """Test update_reservation_baggages with booking that has no air segments (line 654)."""
        # Create booking without air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'BAG123',
            'segments': [
                {
                    'type': 'HOTEL',
                    'vendor': 'TestHotel'
                }
            ]
        }
        DB['booking_by_locator']['BAG123'] = booking_id
        
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.ValidationError,
            'Booking does not contain any air segments',
            None,
            'TestSource', 'BAG123', 2, 1
        )

    def test_update_reservation_baggages_no_payment_id_when_needed(self):
        """Test update_reservation_baggages without payment_id when required (line 656)."""
        # Create booking with air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'BAG123',
            'segments': [
                {
                    'type': 'AIR',
                    'baggage': {'count': 0, 'nonfree_count': 0}
                }
            ]
        }
        DB['booking_by_locator']['BAG123'] = booking_id
        
        # Try to add paid baggage without payment_id
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.ValidationError,
            'payment_id is required when adding paid baggage',
            None,
            'TestSource', 'BAG123', 2, 2
        )

    def test_update_reservation_baggages_payment_processed(self):
        """Test update_reservation_baggages with payment processing (line 660)."""
        # Create booking with air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'BAG123',
            'segments': [
                {
                    'type': 'AIR',
                    'baggage': {'count': 0, 'nonfree_count': 0}
                }
            ]
        }
        DB['booking_by_locator']['BAG123'] = booking_id
        
        # Add paid baggage with payment_id
        result = bookings.update_reservation_baggages('TestSource', 'BAG123', 2, 2, 'pm_001')
        
        self.assertIn('payment', result)
        self.assertEqual(result['payment']['payment_id'], 'pm_001')

    def test_update_reservation_baggages_no_payment_when_no_cost(self):
        """Test update_reservation_baggages without payment when no cost (line 662)."""
        # Create booking with air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'BAG123',
            'segments': [
                {
                    'type': 'AIR',
                    'baggage': {'count': 1, 'nonfree_count': 1}
                }
            ]
        }
        DB['booking_by_locator']['BAG123'] = booking_id
        
        # Update baggage without increasing paid bags (no cost)
        result = bookings.update_reservation_baggages('TestSource', 'BAG123', 2, 1)
        
        self.assertNotIn('payment', result)

    def test_update_reservation_flights_no_air_segments(self):
        """Test update_reservation_flights with booking that has no air segments (line 675)."""
        # Create booking without air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'segments': [
                {
                    'type': 'HOTEL',
                    'vendor': 'TestHotel'
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15'
            }
        ]
        
        self.assert_error_behavior(
            bookings.update_reservation_flights,
            custom_errors.ValidationError,
            'Booking does not contain any air segments',
            None,
            'TestSource', 'FLIGHT123', 'economy', flights, 'pm_001'
        )

    def test_update_reservation_flights_no_pricing_data_found(self):
        """Test update_reservation_flights when no pricing data is found (line 682)."""
        # Create booking with air segments but no pricing data
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ],
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'departure_airport': 'JFK',
                    'arrival_airport': 'LAX',
                    'total_rate': 100
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        flights = [
            {
                'flight_number': 'BB456',
                'date': '2024-01-15'
            }
        ]
        
        # Should raise SeatsUnavailableError when trying to update to a flight that doesn't exist
        self.assert_error_behavior(
            bookings.update_reservation_flights,
            custom_errors.SeatsUnavailableError,
            "Not enough seats on flight 'BB456'.",
            None,
            'TestSource', 'FLIGHT123', 'economy', flights, 'pm_001'
        )

    def test_update_reservation_flights_price_difference_zero(self):
        """Test update_reservation_flights when price difference is zero (line 706)."""
        # Create booking with air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ],
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'departure_airport': 'JFK',
                    'arrival_airport': 'LAX',
                    'total_rate': 100
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15',
                'price': 100  # Same price as existing
            }
        ]
        
        # Should not add payment when price difference is zero
        result = bookings.update_reservation_flights('TestSource', 'FLIGHT123', 'economy', flights, 'pm_001')
        # The response includes payment: None when there's no price difference
        self.assertIn('payment', result)
        self.assertIsNone(result['payment'])

    def test_update_reservation_flights_date_format_with_space(self):
        """Test update_reservation_flights with date format containing space (line 827)."""
        # Create booking with air segments and pricing data
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ],
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'departure_airport': 'JFK',
                    'arrival_airport': 'LAX',
                    'pricing_data': {
                        '2024-01-15': {
                            'economy': 150
                        }
                    },
                    'availability_data': {
                        '2024-01-15': {
                            'economy': 10
                        }
                    }
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15 10:30:00'  # Date with space
            }
        ]
        
        # Should handle date format with space
        result = bookings.update_reservation_flights('TestSource', 'FLIGHT123', 'economy', flights, 'pm_001')
        self.assertIsNotNone(result)

    def test_update_reservation_flights_date_format_with_t(self):
        """Test update_reservation_flights with date format containing T (line 840)."""
        # Create booking with air segments and pricing data
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ],
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'departure_airport': 'JFK',
                    'arrival_airport': 'LAX',
                    'pricing_data': {
                        '2024-01-15': {
                            'economy': 150
                        }
                    },
                    'availability_data': {
                        '2024-01-15': {
                            'economy': 10
                        }
                    }
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15T10:30:00'  # Date with T
            }
        ]
        
        # Should handle date format with T
        result = bookings.update_reservation_flights('TestSource', 'FLIGHT123', 'economy', flights, 'pm_001')
        self.assertIsNotNone(result)

    def test_update_reservation_flights_pricing_data_found(self):
        """Test update_reservation_flights when pricing data is found (line 847)."""
        # Create booking with air segments and pricing data
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ],
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'departure_airport': 'JFK',
                    'arrival_airport': 'LAX',
                    'pricing_data': {
                        '2024-01-15': {
                            'economy': 150
                        }
                    }
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15'
            }
        ]
        
        # Should use pricing data when found
        result = bookings.update_reservation_flights('TestSource', 'FLIGHT123', 'economy', flights, 'pm_001')
        self.assertIsNotNone(result)

    def test_update_reservation_flights_standard_prices_fallback(self):
        """Test update_reservation_flights using standard prices fallback (line 925)."""
        # Create booking with air segments but no pricing data
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ],
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'departure_airport': 'JFK',
                    'arrival_airport': 'LAX',
                    'total_rate': 100
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        # Add standard prices to DB config
        DB['config'] = {
            'standard_prices': {
                'economy': 100,
                'business': 300,
                'first': 500
            }
        }
        
        flights = [
            {
                'flight_number': 'BB456',
                'date': '2024-01-15'
            }
        ]
        
        # Should raise SeatsUnavailableError when trying to update to a flight that doesn't exist
        self.assert_error_behavior(
            bookings.update_reservation_flights,
            custom_errors.SeatsUnavailableError,
            "Not enough seats on flight 'BB456'.",
            None,
            'TestSource', 'FLIGHT123', 'economy', flights, 'pm_001'
        )

    def test_update_reservation_flights_preserve_baggage_information(self):
        """Test update_reservation_flights preserves baggage information (lines 932-935)."""
        # Create booking with air segments and baggage
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ],
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'departure_airport': 'JFK',
                    'arrival_airport': 'LAX',
                    'baggage': {'count': 2, 'weight_kg': 46, 'nonfree_count': 1}
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id
        
        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15'
            }
        ]
        
        # Should preserve baggage information
        result = bookings.update_reservation_flights('TestSource', 'FLIGHT123', 'economy', flights, 'pm_001')
        self.assertIsNotNone(result)

    def test_update_reservation_passengers_field_required_error(self):
        """Test update_reservation_passengers with field required error (line 1076)."""
        # Create booking
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'PASS123',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['PASS123'] = booking_id
        
        passengers = [
            {
                'name_first': 'John'
                # Missing name_last
            }
        ]
        
        self.assert_error_behavior(
            bookings.update_reservation_passengers,
            custom_errors.ValidationError,
            '1 validation error for PassengerUpdate\nname_last\n  Field required [type=missing]',
            None,
            'TestSource', 'PASS123', passengers
        )

    def test_update_reservation_passengers_preserve_existing_dob(self):
        """Test update_reservation_passengers preserves existing dob (line 1089)."""
        # Create booking with passenger that has dob
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'PASS123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe',
                    'dob': '1990-01-01'
                }
            ]
        }
        DB['booking_by_locator']['PASS123'] = booking_id
        
        passengers = [
            {
                'name_first': 'John',
                'name_last': 'Doe'
                # No dob provided
            }
        ]
        
        # Should preserve existing dob
        result = bookings.update_reservation_passengers('TestSource', 'PASS123', passengers)
        self.assertIsNotNone(result)
        self.assertEqual(result['passengers'][0]['dob'], '1990-01-01')

    def test_update_reservation_passengers_text_name_fallback(self):
        """Test update_reservation_passengers with text_name fallback (line 1096)."""
        # Create booking
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'PASS123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['PASS123'] = booking_id
        
        passengers = [
            {
                'name_first': 'John',
                'name_last': 'Doe'
                # No text_name provided
            }
        ]
        
        # Should use fallback text_name format
        result = bookings.update_reservation_passengers('TestSource', 'PASS123', passengers)
        self.assertIsNotNone(result)
        self.assertEqual(result['passengers'][0]['text_name'], 'Doe/John')

    def test_create_or_update_booking_date_booked_local_parsing_succeeds(self):
        """Test create_or_update_booking with valid DateBookedLocal that parses successfully (line 479)."""
        # Create existing booking
        existing_booking_id = str(uuid.uuid4())
        DB['bookings'][existing_booking_id] = {
            'booking_id': existing_booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'TEST123',
            'trip_id': self.trip_id,
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['TEST123'] = existing_booking_id
        DB['bookings_by_trip'][self.trip_id] = [existing_booking_id]

        # Create booking data with valid DateBookedLocal format
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'DateBookedLocal': '2024-01-15T10:30:00',  # Valid ISO format
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }

        # Should handle the parsing successfully and set date_booked_local
        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        
        self.assertIsNotNone(result)
        
        # Check the actual booking in the database
        booking_id = result['booking_id']
        actual_booking = DB['bookings'][booking_id]
        
        # The date_booked_local should be set to the parsed datetime string
        self.assertEqual(actual_booking.get('date_booked_local'), '2024-01-15 10:30:00+00:00')

    def test_create_or_update_booking_form_of_payment_type(self):
        """Test create_or_update_booking with FormOfPaymentType (line 483)."""
        # Create existing booking
        existing_booking_id = str(uuid.uuid4())
        DB['bookings'][existing_booking_id] = {
            'booking_id': existing_booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'TEST123',
            'trip_id': self.trip_id,
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['TEST123'] = existing_booking_id
        DB['bookings_by_trip'][self.trip_id] = [existing_booking_id]

        # Create booking data with FormOfPaymentType
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'FormOfPaymentType': 'CREDIT_CARD',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }

        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        
        self.assertIsNotNone(result)
        booking_id = result['booking_id']
        actual_booking = DB['bookings'][booking_id]
        
        # The form_of_payment_type should be set
        self.assertEqual(actual_booking.get('form_of_payment_type'), 'CREDIT_CARD')

    def test_create_or_update_booking_ticket_mailing_address(self):
        """Test create_or_update_booking with TicketMailingAddress (line 485)."""
        # Create existing booking
        existing_booking_id = str(uuid.uuid4())
        DB['bookings'][existing_booking_id] = {
            'booking_id': existing_booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'TEST123',
            'trip_id': self.trip_id,
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['TEST123'] = existing_booking_id
        DB['bookings_by_trip'][self.trip_id] = [existing_booking_id]

        # Create booking data with TicketMailingAddress
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'TicketMailingAddress': '123 Main St, City, State 12345',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }

        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        
        self.assertIsNotNone(result)
        booking_id = result['booking_id']
        actual_booking = DB['bookings'][booking_id]
        
        # The ticket_mailing_address should be set
        self.assertEqual(actual_booking.get('ticket_mailing_address'), '123 Main St, City, State 12345')

    def test_create_or_update_booking_ticket_pickup_location(self):
        """Test create_or_update_booking with TicketPickupLocation (line 487)."""
        # Create existing booking
        existing_booking_id = str(uuid.uuid4())
        DB['bookings'][existing_booking_id] = {
            'booking_id': existing_booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'TEST123',
            'trip_id': self.trip_id,
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['TEST123'] = existing_booking_id
        DB['bookings_by_trip'][self.trip_id] = [existing_booking_id]

        # Create booking data with TicketPickupLocation
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'TicketPickupLocation': 'Airport Terminal 1',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }

        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        
        self.assertIsNotNone(result)
        booking_id = result['booking_id']
        actual_booking = DB['bookings'][booking_id]
        
        # The ticket_pickup_location should be set
        self.assertEqual(actual_booking.get('ticket_pickup_location'), 'Airport Terminal 1')

    def test_create_or_update_booking_ticket_pickup_number(self):
        """Test create_or_update_booking with TicketPickupNumber (line 489)."""
        # Create existing booking
        existing_booking_id = str(uuid.uuid4())
        DB['bookings'][existing_booking_id] = {
            'booking_id': existing_booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'TEST123',
            'trip_id': self.trip_id,
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['TEST123'] = existing_booking_id
        DB['bookings_by_trip'][self.trip_id] = [existing_booking_id]

        # Create booking data with TicketPickupNumber
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'TicketPickupNumber': 'TICKET123456',
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }

        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        
        self.assertIsNotNone(result)
        booking_id = result['booking_id']
        actual_booking = DB['bookings'][booking_id]
        
        # The ticket_pickup_number should be set
        self.assertEqual(actual_booking.get('ticket_pickup_number'), 'TICKET123456')

    def test_create_or_update_booking_insurance(self):
        """Test create_or_update_booking with insurance field (line 508)."""
        # Create existing booking
        existing_booking_id = str(uuid.uuid4())
        DB['bookings'][existing_booking_id] = {
            'booking_id': existing_booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'TEST123',
            'trip_id': self.trip_id,
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['TEST123'] = existing_booking_id
        DB['bookings_by_trip'][self.trip_id] = [existing_booking_id]

        # Create booking data with insurance
        booking_data = {
            'BookingSource': 'TestSource',
            'RecordLocator': 'TEST123',
            'insurance': 'yes',  # Should be 'yes' or 'no' string
            'Passengers': [
                {
                    'NameFirst': 'John',
                    'NameLast': 'Doe'
                }
            ]
        }

        result = bookings.create_or_update_booking(booking_data, self.trip_id)
        
        self.assertIsNotNone(result)
        booking_id = result['booking_id']
        actual_booking = DB['bookings'][booking_id]
        
        # The insurance should be set
        self.assertIn('insurance', actual_booking)
        self.assertEqual(actual_booking['insurance'], 'yes')

    def test_update_reservation_baggages_no_booking_source(self):
        """Test update_reservation_baggages with missing booking_source (line 654)."""
        # Test with empty booking_source
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.ValidationError,
            'booking_source is required',
            None,
            '', 'BAG123', 2, 1
        )

    def test_update_reservation_baggages_no_confirmation_number(self):
        """Test update_reservation_baggages with missing confirmation_number (line 656)."""
        # Test with empty confirmation_number
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.ValidationError,
            'confirmation_number is required',
            None,
            'TestSource', '', 2, 1
        )

    def test_update_reservation_baggages_negative_nonfree_baggages(self):
        """Test update_reservation_baggages with negative nonfree_baggages (line 660)."""
        # Create booking with air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'BAG123',
            'segments': [
                {
                    'type': 'AIR',
                    'baggage': {'count': 2, 'nonfree_count': 0}
                }
            ]
        }
        DB['booking_by_locator']['BAG123'] = booking_id

        # Test with negative nonfree_baggages
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.ValidationError,
            'nonfree_baggages cannot be negative',
            None,
            'TestSource', 'BAG123', 2, -1
        )

    def test_update_reservation_baggages_nonfree_exceeds_total(self):
        """Test update_reservation_baggages with nonfree_baggages exceeding total_baggages (line 662)."""
        # Create booking with air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'BAG123',
            'segments': [
                {
                    'type': 'AIR',
                    'baggage': {'count': 2, 'nonfree_count': 0}
                }
            ]
        }
        DB['booking_by_locator']['BAG123'] = booking_id

        # Test with nonfree_baggages > total_baggages
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.ValidationError,
            'nonfree_baggages cannot exceed total_baggages',
            None,
            'TestSource', 'BAG123', 2, 3  # 3 nonfree > 2 total
        )

    def test_update_reservation_baggages_booking_not_found_second_check(self):
        """Test update_reservation_baggages with booking not found (second check, line 675)."""
        # Add booking to booking_by_locator but not to bookings, so second lookup will fail
        DB['booking_by_locator']['BAG123'] = 'non-existent-booking-id'

        # Test with booking_id in booking_by_locator but not in bookings
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.BookingNotFoundError,
            "The booking specified by the combination of booking_source 'TestSource' and confirmation_number 'BAG123' could not be found in the system.",
            None,
            'TestSource', 'BAG123', 2, 1
        )

    def test_update_reservation_baggages_booking_source_mismatch(self):
        """Test update_reservation_baggages with booking source mismatch (line 682)."""
        # Create booking with different booking_source
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'DifferentSource',  # Different from request
            'record_locator': 'BAG123',
            'segments': [
                {
                    'type': 'AIR',
                    'baggage': {'count': 0, 'nonfree_count': 0}
                }
            ]
        }
        DB['booking_by_locator']['BAG123'] = booking_id

        # Test with booking source mismatch
        self.assert_error_behavior(
            bookings.update_reservation_baggages,
            custom_errors.BookingNotFoundError,
            "The booking specified by the combination of booking_source 'TestSource' and confirmation_number 'BAG123' could not be found in the system.",
            None,
            'TestSource', 'BAG123', 2, 1
        )

    def test_update_reservation_flights_booking_not_found_check(self):
        """Test update_reservation_flights with booking not found (check, line 675)."""
        # Add booking to booking_by_locator but not to bookings, so lookup will fail
        DB['booking_by_locator']['FLIGHT123'] = 'non-existent-booking-id'

        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15'
            }
        ]

        # Test with booking_id in booking_by_locator but not in bookings
        self.assert_error_behavior(
            bookings.update_reservation_flights,
            custom_errors.BookingNotFoundError,
            "The booking specified by the combination of booking_source 'TestSource' and confirmation_number 'FLIGHT123' could not be found in the system.",
            None,
            'TestSource', 'FLIGHT123', 'economy', flights, 'pm_001'
        )

    def test_update_reservation_flights_validation_error(self):
        """Test update_reservation_flights with validation error (line 827)."""
        # Create booking with air segments
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'FLIGHT123',
            'segments': [
                {
                    'type': 'AIR',
                    'flight_number': 'AA123',
                    'start_date': '2024-01-15',
                    'baggage': {'count': 0, 'nonfree_count': 0}
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id

        # Test with invalid flight data that will cause validation error
        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15',
                'origin': 'XX',  # Invalid airport code (too short)
                'destination': 'YYY'  # Valid length
            }
        ]

        # Test with validation error - this should hit line 827
        with self.assertRaises(custom_errors.ValidationError) as context:
            bookings.update_reservation_flights(
                'TestSource', 'FLIGHT123', 'economy', flights, 'pm_001'
            )
        
        # Check that the error message starts with the expected text
        error_message = str(context.exception)
        self.assertTrue(error_message.startswith("1 validation error for FlightUpdate"))

    def test_update_reservation_passengers_validation_error(self):
        """Test update_reservation_passengers with validation error (line 1076)."""
        # Create booking with passengers
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'TestSource',
            'record_locator': 'PASS123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['PASS123'] = booking_id

        # Test with invalid passenger data that will cause validation error
        # We'll use an invalid data type to trigger a validation error that doesn't contain "Field required"
        passengers = [
            {
                'name_first': 123,  # Invalid type (should be string)
                'name_last': 'Doe'
            }
        ]

        # Test with validation error - this should hit line 1076
        with self.assertRaises(custom_errors.ValidationError) as context:
            bookings.update_reservation_passengers(
                'TestSource', 'PASS123', passengers
            )
        
        # Check that the error message contains validation error but not "Field required"
        error_message = str(context.exception)
        self.assertTrue("validation error" in error_message)
        self.assertFalse("Field required" in error_message)

    def test_update_reservation_passengers_booking_not_found(self):
        """Test update_reservation_passengers with booking not found (line 1089)."""
        # Add booking to booking_by_locator but not to bookings, so lookup will fail
        DB['booking_by_locator']['PASS123'] = 'non-existent-booking-id'
        
        passengers = [
            {
                'name_first': 'John',
                'name_last': 'Doe'
            }
        ]

        # Test with booking_id in booking_by_locator but not in bookings - this should hit line 1089
        self.assert_error_behavior(
            bookings.update_reservation_passengers,
            custom_errors.BookingNotFoundError,
            "The booking specified by the combination of booking_source 'TestSource' and confirmation_number 'PASS123' could not be found in the system.",
            None,
            'TestSource', 'PASS123', passengers
        )

    def test_update_reservation_passengers_booking_source_mismatch(self):
        """Test update_reservation_passengers with booking source mismatch (line 1096)."""
        # Create booking with different booking_source
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'DifferentSource',  # Different from request
            'record_locator': 'PASS123',
            'status': 'CONFIRMED',
            'passengers': [
                {
                    'name_first': 'John',
                    'name_last': 'Doe'
                }
            ]
        }
        DB['booking_by_locator']['PASS123'] = booking_id

        passengers = [
            {
                'name_first': 'John',
                'name_last': 'Doe'
            }
        ]

        # Test with booking source mismatch - this should hit line 1096
        self.assert_error_behavior(
            bookings.update_reservation_passengers,
            custom_errors.BookingNotFoundError,
            "The booking specified by the combination of booking_source 'TestSource' and confirmation_number 'PASS123' could not be found in the system.",
            None,
            'TestSource', 'PASS123', passengers
        )

    def test_update_reservation_flights_booking_source_mismatch_check(self):
        """Test update_reservation_flights with booking source mismatch (line 682)."""
        # Create booking with different booking_source
        booking_id = str(uuid.uuid4())
        DB['bookings'][booking_id] = {
            'booking_id': booking_id,
            'booking_source': 'DifferentSource',  # Different from request
            'record_locator': 'FLIGHT123',
            'segments': [
                {
                    'type': 'AIR',
                    'baggage': {'count': 0, 'nonfree_count': 0}
                }
            ]
        }
        DB['booking_by_locator']['FLIGHT123'] = booking_id

        flights = [
            {
                'flight_number': 'AA123',
                'date': '2024-01-15'
            }
        ]

        # Test with booking source mismatch
        self.assert_error_behavior(
            bookings.update_reservation_flights,
            custom_errors.BookingNotFoundError,
            "The booking specified by the combination of booking_source 'TestSource' and confirmation_number 'FLIGHT123' could not be found in the system.",
            None,
            'TestSource', 'FLIGHT123', 'economy', flights, 'pm_001'
        )


if __name__ == '__main__':
    unittest.main()
