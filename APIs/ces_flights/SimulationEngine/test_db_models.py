import pytest
from pydantic import ValidationError
from .db_models import (
    SeatingClass,
    ConversationState,
    FlightInfo,
    TravelerInfo,
    ConversationHistoryItem,
    EnvVarsData,
    SearchParams,
    SelectedFlight,
    BookingStorage,
    FlightDataStorage,
    ConversationStateStorage,
    SessionStorage,
    CesFlightsDB
)


class TestSeatingClass:
    """Tests for SeatingClass enum."""
    
    def test_valid_economy_class(self):
        """Test that ECONOMY_CLASS is a valid seating class."""
        assert SeatingClass.ECONOMY_CLASS == "ECONOMY_CLASS"
    
    def test_valid_business_class(self):
        """Test that BUSINESS_CLASS is a valid seating class."""
        assert SeatingClass.BUSINESS_CLASS == "BUSINESS_CLASS"
    
    def test_valid_first_class(self):
        """Test that FIRST_CLASS is a valid seating class."""
        assert SeatingClass.FIRST_CLASS == "FIRST_CLASS"


class TestConversationState:
    """Tests for ConversationState enum."""
    
    def test_valid_main_state(self):
        """Test that 'main' is a valid conversation state."""
        assert ConversationState.MAIN == "main"
    
    def test_valid_escalate_state(self):
        """Test that 'escalate_to_agent' is a valid conversation state."""
        assert ConversationState.ESCALATE_TO_AGENT == "escalate_to_agent"


class TestFlightInfo:
    """Tests for FlightInfo model."""
    
    def test_valid_flight_info(self):
        """Test creating a valid flight info."""
        flight = FlightInfo(
            airline="American Airlines",
            depart_date="2025-12-25",
            depart_time="10:00:00",
            arrival_date="2025-12-25",
            arrival_time="18:30:00",
            price=550.0,
            stops=0,
            origin="Los Angeles, CA",
            destination="New York, NY",
            seating_class="ECONOMY_CLASS",
            carry_on_bags=1,
            checked_bags=1,
            currency="USD"
        )
        assert flight.airline == "American Airlines"
        assert flight.price == 550.0
        assert flight.stops == 0
    
    def test_flight_info_with_default_currency(self):
        """Test creating flight info with default currency."""
        flight = FlightInfo(
            airline="Delta",
            depart_date="2025-12-25",
            depart_time="12:00:00",
            arrival_date="2025-12-25",
            arrival_time="20:00:00",
            price=600.0,
            stops=1,
            origin="Los Angeles, CA",
            destination="New York, NY",
            seating_class="ECONOMY_CLASS",
            carry_on_bags=1,
            checked_bags=1
        )
        assert flight.currency == "USD"
    
    def test_flight_info_with_stops(self):
        """Test creating flight info with stops."""
        flight = FlightInfo(
            airline="United Airlines",
            depart_date="2025-12-25",
            depart_time="14:00:00",
            arrival_date="2025-12-25",
            arrival_time="22:30:00",
            price=580.0,
            stops=2,
            origin="Los Angeles, CA",
            destination="New York, NY",
            seating_class="BUSINESS_CLASS",
            carry_on_bags=2,
            checked_bags=2,
            currency="USD"
        )
        assert flight.stops == 2
        assert flight.currency == "USD"
    
    def test_flight_info_currency_usd_case_insensitive(self):
        """Test that currency accepts lowercase 'usd' and converts to uppercase."""
        flight = FlightInfo(
            airline="Delta",
            depart_date="2025-12-25",
            depart_time="12:00:00",
            arrival_date="2025-12-25",
            arrival_time="20:00:00",
            price=600.0,
            stops=1,
            origin="Los Angeles, CA",
            destination="New York, NY",
            seating_class="ECONOMY_CLASS",
            carry_on_bags=1,
            checked_bags=1,
            currency="usd"
        )
        assert flight.currency == "USD"
    
    def test_flight_info_currency_non_usd_raises_error(self):
        """Test that FlightInfo rejects non-USD currency."""
        with pytest.raises(ValueError) as exc_info:
            FlightInfo(
                airline="Delta",
                depart_date="2025-12-25",
                depart_time="12:00:00",
                arrival_date="2025-12-25",
                arrival_time="20:00:00",
                price=600.0,
                stops=1,
                origin="Los Angeles, CA",
                destination="New York, NY",
                seating_class="ECONOMY_CLASS",
                carry_on_bags=1,
                checked_bags=1,
                currency="EUR"
            )
        assert "Database currency must be 'USD'" in str(exc_info.value)
        assert "EUR" in str(exc_info.value)
    
    def test_flight_info_currency_jpy_raises_error(self):
        """Test that FlightInfo rejects JPY currency."""
        with pytest.raises(ValueError) as exc_info:
            FlightInfo(
                airline="Delta",
                depart_date="2025-12-25",
                depart_time="12:00:00",
                arrival_date="2025-12-25",
                arrival_time="20:00:00",
                price=600.0,
                stops=1,
                origin="Los Angeles, CA",
                destination="New York, NY",
                seating_class="ECONOMY_CLASS",
                carry_on_bags=1,
                checked_bags=1,
                currency="JPY"
            )
        assert "Database currency must be 'USD'" in str(exc_info.value)
    
    def test_flight_info_currency_gbp_raises_error(self):
        """Test that FlightInfo rejects GBP currency."""
        with pytest.raises(ValueError) as exc_info:
            FlightInfo(
                airline="Delta",
                depart_date="2025-12-25",
                depart_time="12:00:00",
                arrival_date="2025-12-25",
                arrival_time="20:00:00",
                price=600.0,
                stops=1,
                origin="Los Angeles, CA",
                destination="New York, NY",
                seating_class="ECONOMY_CLASS",
                carry_on_bags=1,
                checked_bags=1,
                currency="GBP"
            )
        assert "Database currency must be 'USD'" in str(exc_info.value)


class TestTravelerInfo:
    """Tests for TravelerInfo model."""
    
    def test_valid_traveler_info(self):
        """Test creating a valid traveler info."""
        traveler = TravelerInfo(
            first_name="John",
            last_name="Doe",
            date_of_birth="1985-05-15",
            known_traveler_number="12345678"
        )
        assert traveler.first_name == "John"
        assert traveler.last_name == "Doe"
        assert traveler.known_traveler_number == "12345678"
    
    def test_traveler_info_without_known_traveler_number(self):
        """Test creating traveler info without known traveler number."""
        traveler = TravelerInfo(
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1990-08-20"
        )
        assert traveler.known_traveler_number is None


class TestConversationHistoryItem:
    """Tests for ConversationHistoryItem model."""
    
    def test_valid_conversation_history_item(self):
        """Test creating a valid conversation history item."""
        item = ConversationHistoryItem(
            timestamp="2025-10-01T03:21:52.419446",
            from_state="main",
            to_state="escalate_to_agent",
            reason="Max retries exceeded"
        )
        assert item.timestamp == "2025-10-01T03:21:52.419446"
        assert item.from_state == "main"
        assert item.to_state == "escalate_to_agent"
    
    def test_conversation_history_item_without_reason(self):
        """Test creating conversation history item without reason."""
        item = ConversationHistoryItem(
            timestamp="2025-10-01T03:21:52.419446",
            from_state="main",
            to_state="done"
        )
        assert item.reason is None


class TestEnvVarsData:
    """Tests for EnvVarsData model."""
    
    def test_valid_env_vars_data(self):
        """Test creating valid environment variables data."""
        env_vars = EnvVarsData(
            variables={"origin_city": "New York, NY", "num_adult_passengers": 2},
            variable_types={"origin_city": "str", "num_adult_passengers": "int"},
            variable_descriptions={"origin_city": "Departure city", "num_adult_passengers": "Number of adults"},
            variable_history={}
        )
        assert env_vars.variables["origin_city"] == "New York, NY"
        assert env_vars.variable_types["num_adult_passengers"] == "int"
    
    def test_env_vars_data_with_defaults(self):
        """Test creating environment variables data with default values."""
        env_vars = EnvVarsData()
        assert env_vars.variables == {}
        assert env_vars.variable_types == {}
        assert env_vars.variable_descriptions == {}
        assert env_vars.variable_history == {}


class TestSearchParams:
    """Tests for SearchParams model."""
    
    def test_valid_search_params(self):
        """Test creating valid search parameters."""
        params = SearchParams(
            origin_city="New York, NY",
            destination_city="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-26",
            num_adult_passengers=2,
            num_child_passengers=1,
            currency="USD",
            cheapest=True
        )
        assert params.origin_city == "New York, NY"
        assert params.num_adult_passengers == 2
        assert params.cheapest is True
    
    def test_search_params_with_defaults(self):
        """Test creating search parameters with default values."""
        params = SearchParams()
        assert params.num_adult_passengers == 1
        assert params.num_child_passengers == 0
        assert params.cheapest is False
        assert params.include_airlines == []


class TestSelectedFlight:
    """Tests for SelectedFlight model."""
    
    def test_valid_selected_flight(self):
        """Test creating a valid selected flight."""
        flight = SelectedFlight(
            flight_id="AA101",
            airline="American Airlines",
            origin="New York, NY",
            destination="Los Angeles, CA",
            depart_date="2025-12-25",
            depart_time="10:00:00",
            arrival_date="2025-12-25",
            arrival_time="18:30:00",
            price=550.0
        )
        assert flight.flight_id == "AA101"
        assert flight.price == 550.0
    
    def test_selected_flight_with_optional_fields(self):
        """Test creating selected flight with optional fields."""
        flight = SelectedFlight()
        assert flight.flight_id is None
        assert flight.airline is None
        assert flight.price is None


class TestBookingStorage:
    """Tests for BookingStorage model."""
    
    def test_valid_booking_storage(self):
        """Test creating a valid booking storage."""
        booking = BookingStorage(
            booking_id="BOOK123",
            flight_id="AA101",
            travelers=[
                TravelerInfo(
                    first_name="John",
                    last_name="Doe",
                    date_of_birth="1985-05-15"
                )
            ],
            confirmation_number="A3F7B2",
            booking_date="2025-10-01T10:00:00",
            status="confirmed"
        )
        assert booking.booking_id == "BOOK123"
        assert len(booking.travelers) == 1
        assert booking.status == "confirmed"
    
    def test_booking_storage_with_defaults(self):
        """Test creating booking storage with default values."""
        booking = BookingStorage(
            booking_id="BOOK456",
            flight_id="DL202"
        )
        assert booking.travelers == []
        assert booking.status == "confirmed"


class TestFlightDataStorage:
    """Tests for FlightDataStorage model."""
    
    def test_valid_flight_data_storage(self):
        """Test creating valid flight data storage."""
        flight_data = FlightDataStorage(
            search_id="SEARCH123",
            search_params=SearchParams(
                origin_city="New York, NY",
                destination_city="Los Angeles, CA",
                earliest_departure_date="2025-12-25",
                num_adult_passengers=2
            ),
            results=[{"flight_id": "AA101", "price": 550.0}],
            timestamp="2025-10-01T10:00:00"
        )
        assert flight_data.search_id == "SEARCH123"
        assert len(flight_data.results) == 1
    
    def test_flight_data_storage_with_empty_results(self):
        """Test creating flight data storage with empty results."""
        flight_data = FlightDataStorage(
            search_id="SEARCH456",
            search_params=SearchParams()
        )
        assert flight_data.results == []
        assert flight_data.timestamp is None


class TestConversationStateStorage:
    """Tests for ConversationStateStorage model."""
    
    def test_valid_conversation_state_storage(self):
        """Test creating valid conversation state storage."""
        state = ConversationStateStorage(
            current_state="main",
            env_vars={"origin_city": "New York, NY"},
            conversation_history=[
                ConversationHistoryItem(
                    timestamp="2025-10-01T03:21:52",
                    from_state="main",
                    to_state="escalate_to_agent",
                    reason="Max retries"
                )
            ],
            env_vars_data=EnvVarsData(
                variables={"origin_city": "New York, NY"},
                variable_types={"origin_city": "str"},
                variable_descriptions={"origin_city": "Departure city"}
            ),
            last_updated="2025-10-01T03:21:52"
        )
        assert state.current_state == "main"
        assert len(state.conversation_history) == 1
    
    def test_conversation_state_storage_with_defaults(self):
        """Test creating conversation state storage with default values."""
        state = ConversationStateStorage(
            current_state="main",
            env_vars_data=EnvVarsData(),
            last_updated="2025-10-01T03:21:52"
        )
        assert state.env_vars == {}
        assert state.conversation_history == []


class TestSessionStorage:
    """Tests for SessionStorage model."""
    
    def test_valid_session_storage(self):
        """Test creating valid session storage."""
        session = SessionStorage(
            session_id="SESSION123",
            created_at="2025-10-01T10:00:00",
            last_activity="2025-10-01T10:30:00",
            metadata={"user_agent": "Chrome"}
        )
        assert session.session_id == "SESSION123"
        assert session.metadata["user_agent"] == "Chrome"
    
    def test_session_storage_with_defaults(self):
        """Test creating session storage with default values."""
        session = SessionStorage(
            session_id="SESSION456"
        )
        assert session.created_at is None
        assert session.metadata == {}


class TestCesFlightsDB:
    """Tests for complete CesFlightsDB model."""
    
    def test_minimal_valid_ces_flights_db(self):
        """Test creating a minimal valid CES Flights database."""
        db = CesFlightsDB(
            sample_flights={},
            flight_bookings={},
            flight_data={},
            end_of_conversation_status={},
            conversation_states={},
            retry_counters={},
            sessions={},
            sample_travelers={},
            sample_bookings={},
            use_real_datastore=False
        )
        assert len(db.sample_flights) == 0
        assert db.use_real_datastore is False
    
    def test_complete_ces_flights_db(self):
        """Test creating a complete CES Flights database with all entities."""
        db = CesFlightsDB(
            sample_flights={
                "AA101": FlightInfo(
                    airline="American Airlines",
                    depart_date="2025-12-25",
                    depart_time="10:00:00",
                    arrival_date="2025-12-25",
                    arrival_time="18:30:00",
                    price=550.0,
                    stops=0,
                    origin="Los Angeles, CA",
                    destination="New York, NY",
                    seating_class="ECONOMY_CLASS",
                    carry_on_bags=1,
                    checked_bags=1
                )
            },
            flight_bookings={
                "BOOK123": BookingStorage(
                    booking_id="BOOK123",
                    flight_id="AA101",
                    travelers=[
                        TravelerInfo(
                            first_name="John",
                            last_name="Doe",
                            date_of_birth="1985-05-15"
                        )
                    ],
                    confirmation_number="B4E8C3"
                )
            },
            flight_data={
                "SEARCH123": FlightDataStorage(
                    search_id="SEARCH123",
                    search_params=SearchParams(),
                    results=[]
                )
            },
            end_of_conversation_status={},
            conversation_states={
                "SESSION123": ConversationStateStorage(
                    current_state="main",
                    env_vars_data=EnvVarsData(),
                    last_updated="2025-10-01T03:21:52"
                )
            },
            retry_counters={"SESSION123": {"collect_origin": 0}},
            sessions={
                "SESSION123": SessionStorage(session_id="SESSION123")
            },
            sample_travelers={},
            sample_bookings={},
            use_real_datastore=False
        )
        
        assert len(db.sample_flights) == 1
        assert "AA101" in db.sample_flights
        assert db.sample_flights["AA101"].airline == "American Airlines"
        assert len(db.flight_bookings) == 1
        assert db.flight_bookings["BOOK123"].confirmation_number == "B4E8C3"
        assert len(db.conversation_states) == 1
    
    def test_ces_flights_db_with_default_factories(self):
        """Test that default factories work correctly."""
        db = CesFlightsDB()
        assert db.sample_flights == {}
        assert db.flight_bookings == {}
        assert db.flight_data == {}
        assert db.end_of_conversation_status == {}
        assert db.conversation_states == {}
        assert db.retry_counters == {}
        assert db.sessions == {}
        assert db.sample_travelers == {}
        assert db.sample_bookings == {}
        assert db.use_real_datastore is False
    
    def test_ces_flights_db_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CesFlightsDB(
                sample_flights={},
                unknown_field="should_fail"
            )
        assert "unknown_field" in str(exc_info.value)
    
    def test_flight_info_validation_in_db(self):
        """Test that flight info is validated when part of the database."""
        with pytest.raises(ValidationError):
            CesFlightsDB(
                sample_flights={
                    "INVALID": {
                        # Missing required fields
                        "airline": "Test Airline"
                    }
                }
            )
    
    def test_booking_storage_validation_in_db(self):
        """Test that booking storage is validated when part of the database."""
        db = CesFlightsDB(
            flight_bookings={
                "BOOK123": BookingStorage(
                    booking_id="BOOK123",
                    flight_id="AA101",
                    travelers=[],
                    status="confirmed"
                )
            }
        )
        assert db.flight_bookings["BOOK123"].status == "confirmed"
    
    def test_conversation_state_nested_validation(self):
        """Test nested validation of conversation state."""
        db = CesFlightsDB(
            conversation_states={
                "SESSION123": ConversationStateStorage(
                    current_state="main",
                    conversation_history=[
                        ConversationHistoryItem(
                            timestamp="2025-10-01T03:21:52",
                            from_state="main",
                            to_state="escalate_to_agent"
                        )
                    ],
                    env_vars_data=EnvVarsData(
                        variables={"origin_city": "New York, NY"}
                    ),
                    last_updated="2025-10-01T03:21:52"
                )
            }
        )
        assert db.conversation_states["SESSION123"].conversation_history[0].to_state == "escalate_to_agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

