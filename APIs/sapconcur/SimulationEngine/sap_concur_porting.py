from common_utils.print_log import print_log
import json
import uuid
import sys
import os
import random
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, cast
from pathlib import Path

# For realistic coordinates and timezone handling
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
    import pytz
    GEOCODING_AVAILABLE = True
except ImportError:
    print_log("⚠️  geopy and/or pytz not available. Install with: pip install geopy pytz")
    print_log("Using fallback coordinates and timezones...")
    GEOCODING_AVAILABLE = False

# Add the SAP Concur models to path
sys.path.append('APIs/sapconcur/SimulationEngine')

try:
    from models import (
        User, Trip, Booking, AirSegment, Passenger, Location, Notification,
        ConcurAirlineDB, TripStatus, BookingStatus, SegmentStatus, SegmentType,
        PaymentMethod, Segment, PaymentHistory
    )
except ImportError as e:
    print_log(f"Error importing SAP Concur models: {e}")
    print_log("Please ensure the script is run from the project root directory")
    sys.exit(1)


class EnhancedLocationService:
    """Service for getting realistic airport coordinates and information"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="sapconcur_migration") if GEOCODING_AVAILABLE else None
        self.coordinate_cache = {}
        
        # Fallback airport data for when geocoding isn't available
        self.fallback_airports = {
            'JFK': {'name': 'John F. Kennedy International Airport', 'city': 'New York', 'state': 'NY', 'country': 'US', 'lat': 40.6413, 'lon': -73.7781, 'timezone': 'America/New_York', 'postal_code': '11430'},
            'LAX': {'name': 'Los Angeles International Airport', 'city': 'Los Angeles', 'state': 'CA', 'country': 'US', 'lat': 33.9425, 'lon': -118.4081, 'timezone': 'America/Los_Angeles', 'postal_code': '90045'},
            'DFW': {'name': 'Dallas/Fort Worth International Airport', 'city': 'Dallas', 'state': 'TX', 'country': 'US', 'lat': 32.8968, 'lon': -97.0380, 'timezone': 'America/Chicago', 'postal_code': '75261'},
            'ORD': {'name': "Chicago O'Hare International Airport", 'city': 'Chicago', 'state': 'IL', 'country': 'US', 'lat': 41.9742, 'lon': -87.9073, 'timezone': 'America/Chicago', 'postal_code': '60666'},
            'ATL': {'name': 'Hartsfield-Jackson Atlanta International Airport', 'city': 'Atlanta', 'state': 'GA', 'country': 'US', 'lat': 33.6407, 'lon': -84.4277, 'timezone': 'America/New_York', 'postal_code': '30320'},
            'LGA': {'name': 'LaGuardia Airport', 'city': 'New York', 'state': 'NY', 'country': 'US', 'lat': 40.7769, 'lon': -73.8740, 'timezone': 'America/New_York', 'postal_code': '11371'},
            'BOS': {'name': 'Logan International Airport', 'city': 'Boston', 'state': 'MA', 'country': 'US', 'lat': 42.3656, 'lon': -71.0096, 'timezone': 'America/New_York', 'postal_code': '02128'},
            'PHL': {'name': 'Philadelphia International Airport', 'city': 'Philadelphia', 'state': 'PA', 'country': 'US', 'lat': 39.8744, 'lon': -75.2424, 'timezone': 'America/New_York', 'postal_code': '19153'},
            'CLT': {'name': 'Charlotte Douglas International Airport', 'city': 'Charlotte', 'state': 'NC', 'country': 'US', 'lat': 35.2140, 'lon': -80.9431, 'timezone': 'America/New_York', 'postal_code': '28208'},
            'MCO': {'name': 'Orlando International Airport', 'city': 'Orlando', 'state': 'FL', 'country': 'US', 'lat': 28.4312, 'lon': -81.3081, 'timezone': 'America/New_York', 'postal_code': '32827'},
            'DEN': {'name': 'Denver International Airport', 'city': 'Denver', 'state': 'CO', 'country': 'US', 'lat': 39.8561, 'lon': -104.6737, 'timezone': 'America/Denver', 'postal_code': '80249'},
            'SEA': {'name': 'Seattle-Tacoma International Airport', 'city': 'Seattle', 'state': 'WA', 'country': 'US', 'lat': 47.4502, 'lon': -122.3088, 'timezone': 'America/Los_Angeles', 'postal_code': '98158'},
            'SFO': {'name': 'San Francisco International Airport', 'city': 'San Francisco', 'state': 'CA', 'country': 'US', 'lat': 37.6213, 'lon': -122.3790, 'timezone': 'America/Los_Angeles', 'postal_code': '94128'},
            'MIA': {'name': 'Miami International Airport', 'city': 'Miami', 'state': 'FL', 'country': 'US', 'lat': 25.7959, 'lon': -80.2870, 'timezone': 'America/New_York', 'postal_code': '33126'},
            'LAS': {'name': 'Harry Reid International Airport', 'city': 'Las Vegas', 'state': 'NV', 'country': 'US', 'lat': 36.0840, 'lon': -115.1537, 'timezone': 'America/Los_Angeles', 'postal_code': '89119'},
            'PHX': {'name': 'Phoenix Sky Harbor International Airport', 'city': 'Phoenix', 'state': 'AZ', 'country': 'US', 'lat': 33.4342, 'lon': -112.0116, 'timezone': 'America/Phoenix', 'postal_code': '85034'},
            'DTW': {'name': 'Detroit Metropolitan Wayne County Airport', 'city': 'Detroit', 'state': 'MI', 'country': 'US', 'lat': 42.2162, 'lon': -83.3554, 'timezone': 'America/New_York', 'postal_code': '48242'},
            'EWR': {'name': 'Newark Liberty International Airport', 'city': 'Newark', 'state': 'NJ', 'country': 'US', 'lat': 40.6895, 'lon': -74.1745, 'timezone': 'America/New_York', 'postal_code': '07114'},
            'IAH': {'name': 'George Bush Intercontinental Airport', 'city': 'Houston', 'state': 'TX', 'country': 'US', 'lat': 29.9902, 'lon': -95.3368, 'timezone': 'America/Chicago', 'postal_code': '77230'},
            'MSP': {'name': 'Minneapolis-Saint Paul International Airport', 'city': 'Minneapolis', 'state': 'MN', 'country': 'US', 'lat': 44.8848, 'lon': -93.2223, 'timezone': 'America/Chicago', 'postal_code': '55450'},
        }
    
    def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
        """Get comprehensive airport information with coordinates"""
        if airport_code in self.coordinate_cache:
            return self.coordinate_cache[airport_code]
        
        # Try fallback data first (faster and more reliable for common airports)
        if airport_code in self.fallback_airports:
            info = self.fallback_airports[airport_code]
            self.coordinate_cache[airport_code] = info
            return info
        
        # Try geocoding for unknown airports
        if GEOCODING_AVAILABLE and self.geolocator:
            try:
                # Search for airport
                search_query = f"{airport_code} Airport"
                location = self.geolocator.geocode(search_query, timeout=10)
                
                if location:
                    info = {
                        'name': f"{airport_code} Airport",
                        'city': airport_code,  # Simplified
                        'state': '',
                        'country': 'US',  # Assumption
                        'lat': location.latitude,
                        'lon': location.longitude,
                        'timezone': 'UTC',  # Default
                        'postal_code': '00000'  # Default
                    }
                    self.coordinate_cache[airport_code] = info
                    return info
                    
            except (GeocoderTimedOut, GeocoderUnavailable):
                pass  # Fall through to default
        
        # Default fallback
        default_info = {
            'name': f"{airport_code} Airport",
            'city': airport_code,
            'state': '',
            'country': 'US',
            'lat': 0.0,
            'lon': 0.0,
            'timezone': 'UTC',
            'postal_code': '00000'
        }
        self.coordinate_cache[airport_code] = default_info
        return default_info
    
    def get_user_timezone_from_state(self, state: str) -> str:
        """Get timezone from US state code"""
        state_timezones = {
            'CA': 'America/Los_Angeles', 'WA': 'America/Los_Angeles', 'OR': 'America/Los_Angeles', 'NV': 'America/Los_Angeles',
            'NY': 'America/New_York', 'FL': 'America/New_York', 'MA': 'America/New_York', 'PA': 'America/New_York',
            'NC': 'America/New_York', 'GA': 'America/New_York', 'VA': 'America/New_York', 'SC': 'America/New_York',
            'TX': 'America/Chicago', 'IL': 'America/Chicago', 'MN': 'America/Chicago', 'MO': 'America/Chicago',
            'CO': 'America/Denver', 'UT': 'America/Denver', 'WY': 'America/Denver', 'MT': 'America/Denver',
            'AZ': 'America/Phoenix', 'HI': 'Pacific/Honolulu', 'AK': 'America/Anchorage'
        }
        return state_timezones.get(state, 'America/New_York')


class FlightToSAPConcurMigrator:
    """Handles the migration from flight data to SAP Concur DB structure"""
    
    def __init__(self):
        self.user_uuid_mapping: Dict[str, str] = {}  # external_id -> uuid
        self.location_cache: Dict[str, str] = {}  # airport_code -> location_id
        self.location_service = EnhancedLocationService()
        self.errors: List[str] = []
        self.stats = {
            'users_migrated': 0,
            'trips_created': 0,
            'bookings_created': 0,
            'segments_created': 0,
            'validation_errors': 0
        }
    
    def load_source_data(self) -> Dict[str, Any]:
        """Load data directly from AirlineDefaultDB.json"""
        try:
            with open('DBs/AirlineDefaultDB.json', 'r') as f:
                airline_db = json.load(f)
            
            users_data = airline_db.get('users', {})
            flights_data = airline_db.get('flights', {})
            reservations_data = airline_db.get('reservations', {})
            
            print_log(f"✓ Loaded {len(users_data)} users from AirlineDefaultDB.json")
            print_log(f"✓ Loaded {len(flights_data)} flight definitions from AirlineDefaultDB.json")
            print_log(f"✓ Loaded {len(reservations_data)} reservations from AirlineDefaultDB.json")
            
            return {
                'users': users_data,
                'flights': flights_data,
                'reservations': reservations_data
            }
        except FileNotFoundError as e:
            print_log(f"Error loading AirlineDefaultDB.json: {e}")
            sys.exit(1)
    
    def create_locations_from_flights(self, flights_data: Dict) -> Dict[str, Location]:
        """Extract unique airports and create Location entities with realistic coordinates"""
        airports = set()
        
        # Extract all unique airport codes
        for flight in flights_data.values():
            airports.add(flight['origin'])
            airports.add(flight['destination'])
        
        locations = {}
        
        for airport_code in airports:
            location_id = str(uuid.uuid4())
            
            # Get comprehensive airport information
            airport_info = self.location_service.get_airport_info(airport_code)
            
            location = Location(
                id=str(location_id),
                name=airport_info['name'],
                address_line1=airport_info['name'],
                address_line2="Airport Terminal Complex",
                city=airport_info['city'],
                state_province=airport_info.get('state', ''),
                country_code=airport_info['country'],
                postal_code=airport_info.get('postal_code', '00000'),
                latitude=airport_info['lat'],
                longitude=airport_info['lon'],
                is_active=True,
                location_type="airport"
            )
            
            locations[str(location_id)] = location
            self.location_cache[airport_code] = location_id
        
        geocoded_count = sum(1 for code in airports if self.location_service.get_airport_info(code)['lat'] != 0.0)
        print_log(f"✓ Created {len(locations)} airport locations ({geocoded_count} with real coordinates)")
        return locations
    
    def migrate_users(self, users_data: Dict) -> Dict[str, User]:
        """Transform users.json to SAP Concur User entities with realistic timezones"""
        users = {}
        
        for external_id, user_data in users_data.items():
            try:
                user_uuid = uuid.uuid4()
                
                # Get timezone from user's state
                user_state = user_data.get('address', {}).get('state', 'NY')
                user_timezone = self.location_service.get_user_timezone_from_state(user_state)
                
                # Process payment methods to ensure they have required fields
                payment_methods = {}
                for payment_id, payment_data in user_data.get('payment_methods', {}).items():
                    source = payment_data.get('source', 'credit_card')
                    
                    # Create PaymentMethod instance with proper fields
                    if source == 'credit_card':
                        payment_method = PaymentMethod(
                            id=payment_id,
                            source=source,
                            brand=payment_data.get('brand', 'visa'),
                            last_four=payment_data.get('last_four', '0000'),
                            amount=None  # Credit cards don't have amounts
                        )
                    elif source == 'gift_card':
                        payment_method = PaymentMethod(
                            id=payment_id,
                            source=source,
                            brand='gift_card',
                            last_four=payment_id[-4:] if len(payment_id) >= 4 else '0000',
                            amount=payment_data.get('amount', 0)
                        )
                    elif source == 'certificate':
                        payment_method = PaymentMethod(
                            id=payment_id,
                            source=source,
                            brand='certificate',
                            last_four=payment_id[-4:] if len(payment_id) >= 4 else '0000',
                            amount=payment_data.get('amount', 0)
                        )
                    else:
                        payment_method = PaymentMethod(
                            id=payment_id,
                            source=source,
                            brand='unknown',
                            last_four='0000',
                            amount=None
                        )
                    
                    payment_methods[payment_id] = payment_method
                
                user = User(
                    id=str(user_uuid),
                    external_id=external_id,
                    user_name=external_id,
                    given_name=user_data['name']['first_name'],
                    family_name=user_data['name']['last_name'],
                    display_name=f"{user_data['name']['first_name']} {user_data['name']['last_name']}",
                    active=True,
                    email=user_data['email'],
                    locale="en-US",
                    timezone=user_timezone,
                    membership=user_data.get('membership'),
                    payment_methods=payment_methods,
                    created_at=str(datetime.now()),
                    last_modified=str(datetime.now()),
                    dob=user_data.get('dob', ''),
                    # Address fields from original data
                    address_line1=user_data.get('address', {}).get('address1'),
                    address_line2=user_data.get('address', {}).get('address2'),
                    city=user_data.get('address', {}).get('city'),
                    state=user_data.get('address', {}).get('state'),
                    country=user_data.get('address', {}).get('country'),
                    zip_code=user_data.get('address', {}).get('zip'),
                    # Saved passengers from user profile
                    saved_passengers=user_data.get('saved_passengers', [])
                )
                
                users[str(user_uuid)] = user
                self.user_uuid_mapping[external_id] = str(user_uuid)
                self.stats['users_migrated'] += 1
                
            except Exception as e:
                self.errors.append(f"Error migrating user {external_id}: {e}")
                self.stats['validation_errors'] += 1
        
        print_log(f"✓ Migrated {len(users)} users with realistic timezones")
        return users
    
    def get_airline_info(self, flight_number: str) -> Dict[str, str]:
        """Extract airline information from flight number"""
        airline_code = flight_number[:3]
        
        airline_mapping = {
            'HAT': {'name': 'HAT Airlines', 'iata': 'HAT'},
            'AA': {'name': 'American Airlines', 'iata': 'AA'},
            'DL': {'name': 'Delta Air Lines', 'iata': 'DL'},
            'UA': {'name': 'United Airlines', 'iata': 'UA'},
            'AS': {'name': 'Alaska Airlines', 'iata': 'AS'},
            'B6': {'name': 'JetBlue Airways', 'iata': 'B6'},
            'NK': {'name': 'Spirit Airlines', 'iata': 'NK'},
            'F9': {'name': 'Frontier Airlines', 'iata': 'F9'},
        }
        
        return airline_mapping.get(airline_code, {
            'name': f"{airline_code} Airlines", 
            'iata': airline_code
        })
    
    def get_realistic_flight_times(self, flight_data: Dict, flight_info: Dict) -> tuple[datetime, datetime]:
        """Get realistic flight departure and arrival times"""
        flight_date = datetime.strptime(flight_data['date'], '%Y-%m-%d')
        
        # Use actual times from flight_info if available
        if flight_info and flight_data['date'] in flight_info.get('dates', {}):
            date_info = flight_info['dates'][flight_data['date']]
            
            if 'actual_departure_time_est' in date_info:
                try:
                    # Clean up timezone suffixes that might cause issues
                    time_str = date_info['actual_departure_time_est']
                    # Handle malformed timezone suffixes
                    if '+' in time_str and time_str.count('+') == 1:
                        base_time, tz_part = time_str.split('+')
                        if len(tz_part) == 1:  # "+1" should be "+01:00"
                            time_str = f"{base_time}+{tz_part.zfill(2)}:00"
                        elif len(tz_part) == 2 and ':' not in tz_part:  # "+01" should be "+01:00"
                            time_str = f"{base_time}+{tz_part}:00"
                    start_time = datetime.fromisoformat(time_str)
                except ValueError:
                    # Fallback to scheduled time
                    if 'scheduled_departure_time_est' in flight_info:
                        scheduled = flight_info['scheduled_departure_time_est']
                        # Clean timezone suffixes from scheduled times
                        if '+' in scheduled:
                            scheduled = scheduled.split('+')[0]
                        hour, minute, second = map(int, scheduled.split(':'))
                        start_time = flight_date.replace(hour=hour, minute=minute, second=second)
                    else:
                        start_time = flight_date.replace(hour=8, minute=0, second=0)
            elif 'scheduled_departure_time_est' in flight_info:
                scheduled = flight_info['scheduled_departure_time_est']
                # Clean timezone suffixes from scheduled times
                if '+' in scheduled:
                    scheduled = scheduled.split('+')[0]
                hour, minute, second = map(int, scheduled.split(':'))
                start_time = flight_date.replace(hour=hour, minute=minute, second=second)
            else:
                start_time = flight_date.replace(hour=8, minute=0, second=0)
            
            if 'actual_arrival_time_est' in date_info:
                try:
                    # Clean up timezone suffixes that might cause issues
                    time_str = date_info['actual_arrival_time_est']
                    # Handle malformed timezone suffixes
                    if '+' in time_str and time_str.count('+') == 1:
                        base_time, tz_part = time_str.split('+')
                        if len(tz_part) == 1:  # "+1" should be "+01:00"
                            time_str = f"{base_time}+{tz_part.zfill(2)}:00"
                        elif len(tz_part) == 2 and ':' not in tz_part:  # "+01" should be "+01:00"
                            time_str = f"{base_time}+{tz_part}:00"
                    end_time = datetime.fromisoformat(time_str)
                except ValueError:
                    # Fallback to scheduled time
                    if 'scheduled_arrival_time_est' in flight_info:
                        scheduled = flight_info['scheduled_arrival_time_est']
                        # Clean timezone suffixes from scheduled times
                        if '+' in scheduled:
                            scheduled = scheduled.split('+')[0]
                        hour, minute, second = map(int, scheduled.split(':'))
                        end_time = flight_date.replace(hour=hour, minute=minute, second=second)
                    else:
                        end_time = start_time + timedelta(hours=2, minutes=30)
            elif 'scheduled_arrival_time_est' in flight_info:
                scheduled = flight_info['scheduled_arrival_time_est']
                # Clean timezone suffixes from scheduled times
                if '+' in scheduled:
                    scheduled = scheduled.split('+')[0]
                hour, minute, second = map(int, scheduled.split(':'))
                end_time = flight_date.replace(hour=hour, minute=minute, second=second)
            else:
                # Estimate based on departure time
                start_time = flight_date.replace(hour=8, minute=0, second=0)
                end_time = start_time + timedelta(hours=2, minutes=30)  # Default duration
        else:
            # Use scheduled times or reasonable defaults
            if flight_info:
                scheduled_dep = flight_info.get('scheduled_departure_time_est', '08:00:00')
                scheduled_arr = flight_info.get('scheduled_arrival_time_est', '11:00:00')
                
                # Clean timezone suffixes from scheduled times
                if '+' in scheduled_dep:
                    scheduled_dep = scheduled_dep.split('+')[0]
                if '+' in scheduled_arr:
                    scheduled_arr = scheduled_arr.split('+')[0]
                
                dep_hour, dep_min, dep_sec = map(int, scheduled_dep.split(':'))
                arr_hour, arr_min, arr_sec = map(int, scheduled_arr.split(':'))
                
                start_time = flight_date.replace(hour=dep_hour, minute=dep_min, second=dep_sec)
                end_time = flight_date.replace(hour=arr_hour, minute=arr_min, second=arr_sec)
            else:
                # Default times
                start_time = flight_date.replace(hour=8, minute=0, second=0)
                end_time = flight_date.replace(hour=11, minute=0, second=0)
        
        return start_time, end_time
    
    def map_cabin_to_fare_class(self, cabin: str) -> str:
        """Map cabin class to airline fare class codes"""
        mapping = {
            'basic_economy': 'N',
            'economy': 'Y',
            'premium_economy': 'W',
            'business': 'J',
            'first': 'F'
        }
        return mapping.get(cabin.lower(), 'Y')
    
    def get_payment_info(self, reservation_data: Dict, users_data: Dict) -> tuple[str, str]:
        """Extract payment information from reservation and user data"""
        user_id = reservation_data['user_id']
        payment_history = reservation_data.get('payment_history', [])
        
        if payment_history and user_id in users_data:
            payment_id = payment_history[0]['payment_id']
            user_payment_methods = users_data[user_id].get('payment_methods', {})
            
            if payment_id in user_payment_methods:
                payment_method = user_payment_methods[payment_id]
                source = payment_method.get('source', 'unknown')
                
                if source == 'credit_card':
                    brand = payment_method.get('brand', 'visa').title()
                    last_four = payment_method.get('last_four', '****')
                    return f"{brand} Card ****{last_four}", "CREDIT_CARD"
                elif source == 'gift_card':
                    return "Gift Card", "GIFT_CARD"
                elif source == 'certificate':
                    amount = payment_method.get('amount', 0)
                    return f"Travel Certificate (${amount})", "TRAVEL_CERTIFICATE"
        
        return "Corporate Card", "CREDIT_CARD"
    
    def create_booking_warnings(self, reservation_data: Dict) -> List[str]:
        """Create actual booking warnings (not data preservation)"""
        warnings = []
        
        # Only add actual warnings/issues that make sense for business logic
        total_bags = reservation_data.get('total_baggages')
        if total_bags and int(total_bags) > 5:
            warnings.append(f"High baggage count: {total_bags} bags")
        
        # No data preservation in warnings - that should be in proper fields
        return warnings
    
    def create_passenger_from_reservation(self, passenger_data: Dict) -> Passenger:
        """Convert reservation passenger to SAP Concur Passenger preserving original data"""
        first_name = passenger_data['first_name']
        last_name = passenger_data['last_name']
        
        # Use original DOB to determine passenger type
        passenger_dob = passenger_data.get('dob')
        pax_type = "ADT"  # Default adult
        
        if passenger_dob:
            try:
                birth_date = datetime.strptime(passenger_dob, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                
                if age < 2:
                    pax_type = "INF"  # Infant
                elif age < 12:
                    pax_type = "CHD"  # Child
                else:
                    pax_type = "ADT"  # Adult
            except (ValueError, KeyError):
                pax_type = "ADT"
        
        # Use original name format
        text_name = f"{last_name}/{first_name}"
        
        # Create passenger object
        passenger = Passenger(
            passenger_id=str(uuid.uuid4()),
            name_first=first_name,
            name_last=last_name,
            text_name=text_name,
            pax_type=pax_type,
            dob=passenger_dob
        )
        
        return passenger
    
    def create_trip_with_original_data(self, reservation_data: Dict, user_uuid: str, trip_uuid: str, start_date: date, end_date: date) -> Trip:
        """Create Trip with original data preserved as separate fields"""
        
        # Map original data to Trip fields
        original_created_at = reservation_data.get('created_at', str(datetime.now()))
        
        # Create simple trip name without merging original data
        trip_name = f"Trip from {reservation_data['origin']} to {reservation_data['destination']}"
        
        # Create destination summary without merging cabin data
        destination_summary = f"{reservation_data['destination']}"
        
        # Simple trip status
        trip_status = TripStatus.CONFIRMED
        
        # Create trip object
        trip = Trip(
            trip_id=str(trip_uuid),
            trip_name=trip_name,
            user_id=str(user_uuid),
            start_date=str(start_date),
            end_date=str(end_date),
            destination_summary=destination_summary,
            status=trip_status,
            created_date=original_created_at,
            last_modified_date=original_created_at,
            booking_type=SegmentType.AIR,
            is_virtual_trip=False,
            is_canceled=False,
            is_guest_booking=False,
            booking_ids=[str(uuid.uuid4())],  # Will be updated later
            flight_type=reservation_data.get('flight_type'),
            cabin=reservation_data.get('cabin'),
            insurance=reservation_data.get('insurance'),
            total_baggages=reservation_data.get('total_baggages'),
            nonfree_baggages=reservation_data.get('nonfree_baggages'),
            origin=reservation_data.get('origin'),
            destination=reservation_data.get('destination')
        )
        
        return trip
    
    def create_booking_with_original_data(self, reservation_data: Dict, trip_uuid: str, booking_uuid: str, passengers: List[Passenger], segments: List[Segment], users_data: Dict) -> Booking:
        """Create Booking with original data preserved as separate fields"""
        
        # Map original data to booking fields
        original_created_at = reservation_data.get('created_at', str(datetime.now()))
        
        # Get payment information
        payment_name, payment_type = self.get_payment_info(reservation_data, users_data)
        
        # Create payment history to preserve original amounts as separate objects
        payment_history_objects = []
        for payment_entry in reservation_data.get('payment_history', []):
            payment_history_obj = PaymentHistory(
                payment_id=payment_entry.get('payment_id', 'unknown'),
                amount=float(payment_entry.get('amount', 0)),
                timestamp=original_created_at,
                type='booking'
            )
            payment_history_objects.append(payment_history_obj)
        
        # Get booking source from first flight
        first_flight = reservation_data['flights'][0] if reservation_data['flights'] else {}
        booking_source = self.get_airline_info(first_flight.get('flight_number', 'HAT001'))['name']
        
        # Only create actual warnings (not data preservation)
        warnings = []
        total_bags = reservation_data.get('total_baggages')
        if total_bags and int(total_bags) > 5:
            warnings.append(f"High baggage count: {total_bags} bags")
        
        # Create booking object
        booking = Booking(
            booking_id=str(booking_uuid),
            booking_source=booking_source,
            record_locator=reservation_data.get('reservation_id', str(uuid.uuid4())[:6]),
            trip_id=str(trip_uuid),
            date_booked_local=original_created_at,
            form_of_payment_name=payment_name,
            form_of_payment_type=payment_type,
            delivery="Electronic",
            status=BookingStatus.CONFIRMED,
            passengers=passengers,
            segments=segments,
            warnings=warnings,  # Only actual warnings
            payment_history=payment_history_objects,  # Original payment amounts preserved
            created_at=original_created_at,
            last_modified=original_created_at,
            flight_type=reservation_data.get('flight_type'),
            cabin=reservation_data.get('cabin'),
            insurance=reservation_data.get('insurance'),
            total_baggages=reservation_data.get('total_baggages'),
            nonfree_baggages=reservation_data.get('nonfree_baggages'),
            origin=reservation_data.get('origin'),
            destination=reservation_data.get('destination')
        )
        
        return booking
    
    def create_air_segment_from_flight(self, flight_data: Dict, flight_info: Dict, cabin: str, reservation_data: Optional[Dict] = None) -> AirSegment:
        """Convert flight data to AirSegment with realistic timing and airline information"""
        segment_uuid = uuid.uuid4()
        
        # Get realistic flight times
        start_time, end_time = self.get_realistic_flight_times(flight_data, flight_info)
        
        # Get airline information
        airline_info = self.get_airline_info(flight_data['flight_number'])
        
        # Map cabin to fare class
        fare_class = self.map_cabin_to_fare_class(cabin)
        
        # Generate confirmation number based on airline and date
        flight_date_obj = datetime.strptime(flight_data['date'], '%Y-%m-%d')
        confirmation_number = f"{airline_info['iata']}{flight_date_obj.strftime('%m%d')}{flight_data['flight_number'][-3:]}"
        
        # Determine segment status from flight_info
        segment_status = SegmentStatus.CONFIRMED  # Default
        if flight_info and flight_data['date'] in flight_info.get('dates', {}):
            date_info = flight_info['dates'][flight_data['date']]
            if 'status' in date_info:
                if date_info['status'] == 'cancelled':
                    segment_status = SegmentStatus.CANCELLED
                elif date_info['status'] == 'landed':
                    segment_status = SegmentStatus.CONFIRMED  # Fix: COMPLETED doesn't exist
        
        # Create baggage information from reservation data
        baggage_info = {"count": 0, "weight_kg": 0, "nonfree_count": 0}
        if reservation_data:
            total_bags = reservation_data.get('total_baggages', 0)
            nonfree_bags = reservation_data.get('nonfree_baggages', 0)
            if total_bags:
                baggage_info["count"] = int(total_bags)
                baggage_info["weight_kg"] = int(total_bags) * 23  # Assume 23kg per bag
            if nonfree_bags:
                baggage_info["nonfree_count"] = int(nonfree_bags)
        
        # Extract detailed flight operational data from flight_info
        scheduled_departure = flight_info.get('scheduled_departure_time_est') if flight_info else None
        scheduled_arrival = flight_info.get('scheduled_arrival_time_est') if flight_info else None
        
        # Prepare complete flight schedule data (all dates with actual times)
        flight_schedule_data = {}
        availability_data = {}
        pricing_data = {}
        operational_status = {}
        estimated_departure_times = {}
        estimated_arrival_times = {}
        
        if flight_info and 'dates' in flight_info:
            for date_str, date_info in flight_info['dates'].items():
                # Schedule data
                if 'actual_departure_time_est' in date_info or 'actual_arrival_time_est' in date_info:
                    flight_schedule_data[date_str] = {
                        'actual_departure_time_est': date_info.get('actual_departure_time_est'),
                        'actual_arrival_time_est': date_info.get('actual_arrival_time_est'),
                        'scheduled_departure_time_est': scheduled_departure,
                        'scheduled_arrival_time_est': scheduled_arrival
                    }
                
                # Availability data
                if 'available_seats' in date_info:
                    availability_data[date_str] = date_info['available_seats']
                
                # Pricing data
                if 'prices' in date_info:
                    pricing_data[date_str] = date_info['prices']
                
                # Operational status
                if 'status' in date_info:
                    operational_status[date_str] = date_info['status']
                
                # Estimated times
                if 'estimated_departure_time_est' in date_info:
                    estimated_departure_times[date_str] = date_info['estimated_departure_time_est']
                
                if 'estimated_arrival_time_est' in date_info:
                    estimated_arrival_times[date_str] = date_info['estimated_arrival_time_est']
        
        return AirSegment(
            segment_id=str(segment_uuid),
            type=SegmentType.AIR,
            status=segment_status,
            confirmation_number=confirmation_number,
            start_date=str(start_time),
            end_date=str(end_time),
            vendor=airline_info['iata'],
            vendor_name=airline_info['name'],
            currency="USD",
            total_rate=float(flight_data['price']),
            departure_airport=flight_data['origin'],
            arrival_airport=flight_data['destination'],
            flight_number=flight_data['flight_number'],
            aircraft_type="Boeing 737",  # Could be enhanced with real aircraft data
            fare_class=fare_class,
            is_direct=True,  # Add missing required field
            baggage=baggage_info,  # Contains original total_baggages and nonfree_baggages
            
            # Enhanced fields with detailed operational data
            scheduled_departure_time=scheduled_departure,
            scheduled_arrival_time=scheduled_arrival,
            flight_schedule_data=flight_schedule_data,
            availability_data=availability_data,
            pricing_data=pricing_data,
            operational_status=operational_status,
            
            # Estimated time fields
            estimated_departure_times=estimated_departure_times,
            estimated_arrival_times=estimated_arrival_times
        )
    
    def migrate_reservations_to_trips_and_bookings(
        self, 
        reservations_data: Dict, 
        flights_data: Dict,
        users_data: Dict
    ) -> tuple[Dict[str, Trip], Dict[str, Booking]]:
        """Transform reservations to Trip and Booking entities"""
        trips = {}
        bookings = {}
        
        for reservation_id, reservation_data in reservations_data.items():
            try:
                # Get user UUID
                user_external_id = reservation_data['user_id']
                if user_external_id not in self.user_uuid_mapping:
                    self.errors.append(f"User {user_external_id} not found for reservation {reservation_id}")
                    continue
                
                user_uuid = self.user_uuid_mapping[user_external_id]
                
                # Create Trip and Booking UUIDs
                trip_uuid = uuid.uuid4()
                booking_uuid = uuid.uuid4()
                
                # Determine trip dates from flights
                flight_dates = [datetime.strptime(f['date'], '%Y-%m-%d').date() 
                              for f in reservation_data['flights']]
                start_date = min(flight_dates)
                end_date = max(flight_dates)
                
                # Create Trip with original data mapping including custom fields
                trip = self.create_trip_with_original_data(
                    reservation_data,
                    str(user_uuid),
                    str(trip_uuid),
                    start_date,
                    end_date
                )
                
                # Update Trip with correct booking_id
                trip.booking_ids = [str(booking_uuid)]
                
                # Create passengers
                passengers = [
                    self.create_passenger_from_reservation(p) 
                    for p in reservation_data['passengers']
                ]
                
                # Create enhanced AirSegment with original baggage and cabin data
                air_segments = []
                cabin = reservation_data.get('cabin', 'economy')
                for flight_data in reservation_data['flights']:
                    segment = self.create_air_segment_from_flight(
                        flight_data, 
                        flights_data.get(flight_data['flight_number'], {}),
                        cabin,
                        reservation_data  # Pass reservation data for baggage info
                    )
                    air_segments.append(segment)
                    self.stats['segments_created'] += 1
                
                # Cast segments to proper type
                segments: List[Segment] = cast(List[Segment], air_segments)
                
                # Create Booking with original data preserved in proper fields
                booking = self.create_booking_with_original_data(
                    reservation_data,
                    str(trip_uuid),
                    str(booking_uuid),
                    passengers,
                    segments,
                    users_data
                )
                
                # Fix the record_locator to use the reservation_id
                booking.record_locator = reservation_id
                
                trips[str(trip_uuid)] = trip
                bookings[str(booking_uuid)] = booking
                
                self.stats['trips_created'] += 1
                self.stats['bookings_created'] += 1
                
            except Exception as e:
                self.errors.append(f"Error migrating reservation {reservation_id}: {e}")
                self.stats['validation_errors'] += 1
        
        print_log(f"✓ Created {len(trips)} trips and {len(bookings)} bookings with realistic data")
        return trips, bookings
    
    def build_index_tables(
        self, 
        users: Dict[str, User],
        trips: Dict[str, Trip],
        bookings: Dict[str, Booking]
    ) -> Dict[str, Any]:
        """Build the relationship index tables"""
        user_by_external_id = {}
        booking_by_locator = {}
        trips_by_user: Dict[str, List[str]] = {}
        bookings_by_trip: Dict[str, List[str]] = {}
        
        # Build user external ID mapping
        for user_uuid, user in users.items():
            if user.external_id:
                user_by_external_id[user.external_id] = user_uuid
        
        # Build booking locator mapping
        for booking_uuid, booking in bookings.items():
            booking_by_locator[booking.record_locator] = booking_uuid
        
        # Build trips by user mapping
        for trip_uuid, trip in trips.items():
            user_uuid = trip.user_id
            if user_uuid not in trips_by_user:
                trips_by_user[user_uuid] = []
            trips_by_user[user_uuid].append(trip_uuid)
        
        # Build bookings by trip mapping
        for booking_uuid, booking in bookings.items():
            trip_uuid = booking.trip_id
            if trip_uuid not in bookings_by_trip:
                bookings_by_trip[trip_uuid] = []
            bookings_by_trip[trip_uuid].append(booking_uuid)
        
        print_log(f"✓ Built index tables:")
        print_log(f"  - {len(user_by_external_id)} external ID mappings")
        print_log(f"  - {len(booking_by_locator)} booking locators")
        print_log(f"  - {len(trips_by_user)} users with trips")
        print_log(f"  - {len(bookings_by_trip)} trips with bookings")
        
        return {
            'user_by_external_id': user_by_external_id,
            'booking_by_locator': booking_by_locator,
            'trips_by_user': trips_by_user,
            'bookings_by_trip': bookings_by_trip
        }
    
    def validate_with_pydantic(self, sapconcur_db: Dict[str, Any]) -> bool:
        """Validate the entire database structure against ConcurAirlineDB model"""
        print_log("\n=== PYDANTIC MODEL VALIDATION ===")
        
        try:
            # Attempt to create ConcurAirlineDB instance
            db_instance = ConcurAirlineDB(**sapconcur_db)
            
            print_log("✓ ConcurAirlineDB model validation: PASSED")
            
            # Validate individual entity counts
            print_log(f"✓ Users validated: {len(db_instance.users)}")
            print_log(f"✓ Locations validated: {len(db_instance.locations)}")
            print_log(f"✓ Trips validated: {len(db_instance.trips)}")
            print_log(f"✓ Bookings validated: {len(db_instance.bookings)}")
            print_log(f"✓ Notifications validated: {len(db_instance.notifications)}")
            
            # Validate index integrity
            print_log(f"✓ User external ID index: {len(db_instance.user_by_external_id)}")
            print_log(f"✓ Booking locator index: {len(db_instance.booking_by_locator)}")
            print_log(f"✓ Trips by user index: {len(db_instance.trips_by_user)}")
            print_log(f"✓ Bookings by trip index: {len(db_instance.bookings_by_trip)}")
            
            # Validate specific field types and relationships
            validation_checks = 0
            validation_passed = 0
            
            # Check user relationships
            for user_uuid, user in db_instance.users.items():
                validation_checks += 1
                if isinstance(user, User) and user.external_id:
                    validation_passed += 1
            
            # Check trip-booking relationships
            for trip_uuid, trip in db_instance.trips.items():
                validation_checks += 1
                if isinstance(trip, Trip) and trip.user_id in db_instance.users:
                    validation_passed += 1
            
            # Check booking-trip relationships
            for booking_uuid, booking in db_instance.bookings.items():
                validation_checks += 1
                if isinstance(booking, Booking) and booking.trip_id in db_instance.trips:
                    validation_passed += 1
            
            print_log(f"✓ Relationship validation: {validation_passed}/{validation_checks} passed")
            
            if validation_passed == validation_checks:
                print_log("\n🎉 ALL PYDANTIC VALIDATIONS PASSED!")
                return True
            else:
                print_log(f"\n⚠️  {validation_checks - validation_passed} validation issues found")
                return False
                
        except Exception as e:
            print_log(f"❌ Pydantic validation failed: {e}")
            return False
    
    def run_migration(self) -> Dict[str, Any]:
        """Execute the complete migration process"""
        print_log("=== FLIGHT DATA TO SAP CONCUR MIGRATION ===\n")
        
        # Load source data
        source_data = self.load_source_data()
        
        # Create locations from flight data
        locations = self.create_locations_from_flights(source_data['flights'])
        
        # Migrate users
        users = self.migrate_users(source_data['users'])
        
        # Migrate reservations to trips and bookings
        trips, bookings = self.migrate_reservations_to_trips_and_bookings(
            source_data['reservations'], 
            source_data['flights'],
            source_data['users']
        )
        
        # Build index tables
        indexes = self.build_index_tables(users, trips, bookings)
        
        # Create the complete SAP Concur DB structure
        sapconcur_db = {
            'users': users,
            'locations': locations,
            'trips': trips,
            'bookings': bookings,
            'notifications': {},  # Empty notifications for now
            **indexes
        }
        
        # Calculate statistics for enhanced features
        virtual_trips = sum(1 for trip in trips.values() if trip.is_virtual_trip)
        canceled_trips = sum(1 for trip in trips.values() if trip.is_canceled)
        guest_bookings = sum(1 for trip in trips.values() if trip.is_guest_booking)
        # Count passengers with DOB (the only enhanced field we kept)
        enhanced_passengers = sum(
            len([p for p in booking.passengers if p.dob])
            for booking in bookings.values()
        )
        
        # Print migration statistics
        print_log(f"\n=== ENHANCED MIGRATION STATISTICS ===")
        print_log(f"✓ Users migrated with real timezones: {self.stats['users_migrated']}")
        print_log(f"✓ Trips created: {self.stats['trips_created']}")
        
        if len(trips) > 0:
            print_log(f"  - Virtual trips: {virtual_trips} ({virtual_trips/len(trips)*100:.1f}%)")
            print_log(f"  - Canceled trips: {canceled_trips} ({canceled_trips/len(trips)*100:.1f}%)")
            print_log(f"  - Guest bookings: {guest_bookings} ({guest_bookings/len(trips)*100:.1f}%)")
        else:
            print_log(f"  - Virtual trips: {virtual_trips} (0%)")
            print_log(f"  - Canceled trips: {canceled_trips} (0%)")
            print_log(f"  - Guest bookings: {guest_bookings} (0%)")
            
        print_log(f"✓ Bookings created with real payment data: {self.stats['bookings_created']}")
        print_log(f"✓ Flight segments with real timing: {self.stats['segments_created']}")
        print_log(f"✓ Enhanced passengers with details: {enhanced_passengers}")
        print_log(f"⚠️  Validation errors: {self.stats['validation_errors']}")
        
        geocoding_status = "✓ Available" if GEOCODING_AVAILABLE else "⚠️ Not available (using fallback coordinates)"
        print_log(f"�� Geocoding service: {geocoding_status}")
        
        if self.errors:
            print_log(f"\n⚠️  {len(self.errors)} errors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                print_log(f"  - {error}")
            if len(self.errors) > 10:
                print_log(f"  ... and {len(self.errors) - 10} more errors")
        
        return sapconcur_db


def main():
    """Main migration execution"""
    print_log("--- Starting Migration ---")
    migrator = FlightToSAPConcurMigrator()
    
    # Run the migration
    sapconcur_db = migrator.run_migration()
    
    # Validate with Pydantic models
    validation_success = migrator.validate_with_pydantic(sapconcur_db)
    
    if validation_success:
        # Save the migrated database
        output_file = 'DBs/SAPConcurDefaultDB.json'
        
        # Convert UUIDs to strings for JSON serialization
        def uuid_to_str(obj):
            if isinstance(obj, dict):
                return {str(k) if isinstance(k, uuid.UUID) else k: uuid_to_str(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [uuid_to_str(item) for item in obj]
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            else:
                return obj
        
        # Convert the database for JSON serialization
        json_db = {}
        for key, value in sapconcur_db.items():
            if key in ['users', 'locations', 'trips', 'bookings', 'notifications']:
                # Convert entity dictionaries
                json_db[key] = {
                    str(entity_id): entity.model_dump() if hasattr(entity, 'model_dump') else (entity.dict() if hasattr(entity, 'dict') else entity)
                    for entity_id, entity in value.items()
                }
            else:
                # Convert index tables
                json_db[key] = uuid_to_str(value)
        
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(json_db, f, indent=2, default=str)
            
            print_log(f"\n✓ Migration completed successfully!")
            print_log(f"✓ Migrated database saved to: {output_file}")
            print_log(f"✓ Database ready for use with SAP Concur simulation engine")
            
        except Exception as e:
            print_log(f"\n❌ Error saving migrated database: {e}")
    else:
        print_log(f"\n❌ Migration completed with validation errors")
        print_log(f"Please review the errors above before using the migrated data")

if __name__ == "__main__":
    main()