"""
Utility functions for input validation, formatting, and time helpers.
"""

import json
from datetime import datetime, date, timezone
from typing import Any, Optional, Dict
from .custom_errors import ValidationError

# Currency exchange rates with USD as base (1 USD = X units of target currency)
# All flight prices in the database are stored in USD
CURRENCY_EXCHANGE_RATES = {
    "USD": 1.00,      # United States Dollar (base)
    "EUR": 0.92,      # Euro
    "JPY": 156.12,    # Japanese Yen
    "GBP": 0.79,      # British Pound Sterling
    "CNY": 7.24,      # Chinese Renminbi
    "AUD": 1.50,      # Australian Dollar
    "CAD": 1.37,      # Canadian Dollar
    "CHF": 0.91,      # Swiss Franc
    "HKD": 7.81,      # Hong Kong Dollar
    "SGD": 1.35,      # Singapore Dollar
    "SEK": 10.46,     # Swedish Krona
    "KRW": 1377.11,   # South Korean Won
    "NOK": 10.51,     # Norwegian Krone
    "NZD": 1.63,      # New Zealand Dollar
    "INR": 83.54,     # Indian Rupee
    "MXN": 16.96,     # Mexican Peso
    "TWD": 32.33,     # New Taiwan Dollar
    "ZAR": 18.73,     # South African Rand
    "BRL": 5.14,      # Brazilian Real
    "DKK": 6.88,      # Danish Krone
}

# Supported currency codes for easy validation
SUPPORTED_CURRENCIES = set(CURRENCY_EXCHANGE_RATES.keys())


def is_valid_currency(currency_code: str) -> bool:
    """
    Check if a currency code is supported.
    
    Args:
        currency_code (str): The currency code to validate (e.g., "USD", "EUR").
        
    Returns:
        bool: True if the currency is supported, False otherwise.
    """
    return currency_code.upper() in SUPPORTED_CURRENCIES


def get_supported_currencies() -> list:
    """
    Get a list of all supported currency codes.
    
    Returns:
        list: Sorted list of supported currency codes.
    """
    return sorted(SUPPORTED_CURRENCIES)


def convert_price(amount_usd: float, target_currency: str) -> float:
    """
    Convert a price from USD to the target currency.
    
    All prices in the database are stored in USD. This function converts
    a USD price to the requested currency using the exchange rates.
    
    Args:
        amount_usd (float): The amount in USD to convert.
        target_currency (str): The target currency code (e.g., "EUR", "JPY").
        
    Returns:
        float: The converted amount in the target currency, rounded to 2 decimal places.
        
    Raises:
        ValidationError: If the target currency is not supported.
        
    """
    target_currency = target_currency.upper()
    
    if target_currency not in CURRENCY_EXCHANGE_RATES:
        raise ValidationError(
            f"Unsupported currency: {target_currency}. "
            f"Supported currencies: {', '.join(sorted(SUPPORTED_CURRENCIES))}"
        )
    
    # Get the exchange rate
    exchange_rate = CURRENCY_EXCHANGE_RATES[target_currency]
    
    # Convert and round to 2 decimal places
    converted_amount = amount_usd * exchange_rate
    return round(converted_amount, 2)


def convert_price_to_usd(amount: float, source_currency: str) -> float:
    """
    Convert a price from the source currency to USD.
    
    This is the inverse operation of convert_price().
    
    Args:
        amount (float): The amount in the source currency.
        source_currency (str): The source currency code (e.g., "EUR", "JPY").
        
    Returns:
        float: The converted amount in USD, rounded to 2 decimal places.
        
    Raises:
        ValidationError: If the source currency is not supported.
    """
    source_currency = source_currency.upper()
    
    if source_currency not in CURRENCY_EXCHANGE_RATES:
        raise ValidationError(
            f"Unsupported currency: {source_currency}. "
            f"Supported currencies: {', '.join(sorted(SUPPORTED_CURRENCIES))}"
        )
    
    # Get the exchange rate
    exchange_rate = CURRENCY_EXCHANGE_RATES[source_currency]
    
    # Convert back to USD and round to 2 decimal places
    if exchange_rate == 0:
        raise ValidationError(f"Invalid exchange rate for {source_currency}")
    
    usd_amount = amount / exchange_rate
    return round(usd_amount, 2)


def _get_current_date() -> str:
    """Return an ISO-8601 UTC timestamp with timezone information."""
    return datetime.now(timezone.utc).isoformat()

def current_timestamp() -> str:
    """Get current timestamp in ISO format with timezone information."""
    return datetime.now(timezone.utc).isoformat()


# Counter-based retry logic for DI compliance
class RetryCounter:
    """Manages retry counters for conversation flow with fallback states."""
    
    def __init__(self):
        self.counters = {}
        self.max_retries = 2  # Default max retries as per DI
    
    def increment_counter(self, counter_key: str) -> int:
        """Increment retry counter and return current count."""
        if counter_key not in self.counters:
            self.counters[counter_key] = 0
        self.counters[counter_key] += 1
        return self.counters[counter_key]
    
    def get_counter(self, counter_key: str) -> int:
        """Get current retry count for a specific counter."""
        return self.counters.get(counter_key, 0)
    
    def reset_counter(self, counter_key: str) -> None:
        """Reset retry counter to 0."""
        self.counters[counter_key] = 0
    
    def has_exceeded_max_retries(self, counter_key: str, max_retries: int = None) -> bool:
        """Check if retry count has exceeded maximum allowed retries."""
        max_retries = max_retries or self.max_retries
        return self.get_counter(counter_key) > max_retries
    
    def should_fallback(self, counter_key: str, max_retries: int = None) -> bool:
        """Check if should fallback to escalation state."""
        return self.has_exceeded_max_retries(counter_key, max_retries)


class ConversationStateManager:
    """Manages conversation state and retry logic according to DI requirements."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"session_{current_timestamp()}"
        self.current_state = "main"
        self.env_vars = {}
        self.retry_counter = RetryCounter()
        self.conversation_history = []
        
        # Initialize environment variable manager
        self.env_manager = FlightBookingEnvironmentManager()
        
        # Load existing state from database if available
        self._load_from_database()
    
    def transition_to(self, next_state: str, reason: str = None) -> None:
        """Transition to next conversation state."""
        previous_state = self.current_state
        self.current_state = next_state
        
        # Log state transition
        transition_log = {
            "timestamp": current_timestamp(),
            "from_state": previous_state,
            "to_state": next_state,
            "reason": reason
        }
        self.conversation_history.append(transition_log)
    
    def update_env_var(self, variable: str, value: any) -> None:
        """Update environment variable."""
        self.env_vars[variable] = value
    
    def get_env_var(self, variable: str, default: any = None) -> any:
        """Get environment variable value."""
        return self.env_vars.get(variable, default)
    
    def handle_retry_logic(self, action_key: str, max_retries: int = 2, fallback_state: str = "escalate_to_agent") -> tuple[bool, str]:
        """
        Handle counter-based retry logic as per DI requirements.
        
        Args:
            action_key: Unique identifier for the action being retried
            max_retries: Maximum number of retries allowed
            fallback_state: State to transition to if max retries exceeded
            
        Returns:
            tuple: (should_continue, next_state)
        """
        current_count = self.retry_counter.increment_counter(action_key)
        
        if self.retry_counter.should_fallback(action_key, max_retries):
            # Reset counter and transition to fallback state
            self.retry_counter.reset_counter(action_key)
            self.transition_to(fallback_state, f"Max retries ({max_retries}) exceeded for {action_key}")
            return False, fallback_state
        else:
            # Continue with current action
            return True, self.current_state
    
    def reset_retry_counter(self, action_key: str) -> None:
        """Reset retry counter for successful completion."""
        self.retry_counter.reset_counter(action_key)
    
    def get_retry_count(self, action_key: str) -> int:
        """Get current retry count for an action."""
        return self.retry_counter.get_counter(action_key)
    
    def is_first_attempt(self, action_key: str) -> bool:
        """Check if this is the first attempt for an action."""
        return self.get_retry_count(action_key) == 1
    
    def get_conversation_context(self) -> dict:
        """Get current conversation context."""
        return {
            "current_state": self.current_state,
            "env_vars": self.env_vars.copy(),
            "retry_counts": self.retry_counter.counters.copy(),
            "conversation_history": self.conversation_history.copy()
        }
    
    def _load_from_database(self) -> None:
        """Load conversation state and retry counters from database."""
        try:
            from . import db
            
            # Load conversation state
            saved_state = db.load_conversation_state(self.session_id)
            if saved_state:
                self.current_state = saved_state.get("current_state", "main")
                self.env_vars = saved_state.get("env_vars", {})
                self.conversation_history = saved_state.get("conversation_history", [])
                
                # Load environment variables
                env_vars_data = saved_state.get("env_vars_data", {})
                if env_vars_data:
                    self.env_manager.variables = env_vars_data.get("variables", {})
                    self.env_manager.variable_types = env_vars_data.get("variable_types", {})
                    self.env_manager.variable_descriptions = env_vars_data.get("variable_descriptions", {})
                    self.env_manager.variable_history = env_vars_data.get("variable_history", {})
            
            # Load retry counters
            saved_counters = db.load_retry_counters(self.session_id)
            if saved_counters:
                self.retry_counter.counters = saved_counters
                
        except Exception as e:
            # If loading fails, start with default state
            pass
    
    def _save_to_database(self) -> None:
        """Save conversation state and retry counters to database."""
        try:
            from . import db
            
            # Save conversation state
            state_data = {
                "current_state": self.current_state,
                "env_vars": self.env_vars,
                "conversation_history": self.conversation_history,
                "env_vars_data": {
                    "variables": self.env_manager.variables,
                    "variable_types": self.env_manager.variable_types,
                    "variable_descriptions": self.env_manager.variable_descriptions,
                    "variable_history": self.env_manager.variable_history
                },
                "last_updated": current_timestamp()
            }
            db.save_conversation_state(self.session_id, state_data)
            
            # Save retry counters
            db.save_retry_counters(self.session_id, self.retry_counter.counters)
            
        except Exception as e:
            # Log error but don't fail the conversation
            pass
    
    def transition_to(self, next_state: str, reason: str = None) -> None:
        """Transition to next conversation state and save to database."""
        previous_state = self.current_state
        self.current_state = next_state
        
        # Log state transition
        transition_log = {
            "timestamp": current_timestamp(),
            "from_state": previous_state,
            "to_state": next_state,
            "reason": reason
        }
        self.conversation_history.append(transition_log)
        
        # Save to database
        self._save_to_database()
    
    def update_env_var(self, variable: str, value: any) -> None:
        """Update environment variable and save to database."""
        self.env_vars[variable] = value
        # Also update the environment manager
        self.env_manager.update_flight_var(variable, value)
        self._save_to_database()
    
    def update_flight_env_var(self, variable: str, value: any) -> None:
        """Update flight-specific environment variable with validation."""
        self.env_manager.update_flight_var(variable, value)
        self.env_vars[variable] = value
        self._save_to_database()
    
    def get_flight_env_var(self, variable: str, default: any = None) -> any:
        """Get flight-specific environment variable."""
        return self.env_manager.get_env_var(variable, default)
    
    def is_flight_search_complete(self) -> bool:
        """Check if flight search information is complete."""
        return self.env_manager.is_flight_search_complete()
    
    def is_booking_ready(self) -> bool:
        """Check if booking is ready."""
        return self.env_manager.is_booking_ready()
    
    def get_missing_flight_info(self) -> list:
        """Get missing flight information."""
        return self.env_manager.get_missing_flight_info()
    
    def get_flight_search_params(self) -> dict:
        """Get flight search parameters from environment variables."""
        return self.env_manager.get_flight_search_params()
    
    def list_flight_env_vars(self) -> dict:
        """List all flight environment variables with metadata."""
        return self.env_manager.list_env_vars()
    
    def handle_retry_logic(self, action_key: str, max_retries: int = 2, fallback_state: str = "escalate_to_agent") -> tuple[bool, str]:
        """
        Handle counter-based retry logic as per DI requirements.
        
        Args:
            action_key: Unique identifier for the action being retried
            max_retries: Maximum number of retries allowed
            fallback_state: State to transition to if max retries exceeded
            
        Returns:
            tuple: (should_continue, next_state)
        """
        current_count = self.retry_counter.increment_counter(action_key)
        
        # Save updated counter to database
        self._save_to_database()
        
        if self.retry_counter.should_fallback(action_key, max_retries):
            # Reset counter and transition to fallback state
            self.retry_counter.reset_counter(action_key)
            self.transition_to(fallback_state, f"Max retries ({max_retries}) exceeded for {action_key}")
            return False, fallback_state
        else:
            # Continue with current action
            return True, self.current_state
    
    def reset_retry_counter(self, action_key: str) -> None:
        """Reset retry counter for successful completion and save to database."""
        self.retry_counter.reset_counter(action_key)
        self._save_to_database()


def validate_retry_logic(action_key: str, state_manager: ConversationStateManager, 
                        max_retries: int = 2, fallback_state: str = "escalate_to_agent") -> tuple[bool, str]:
    """
    Validate retry logic for DI compliance.
    
    This function implements the DI pattern:
    [type: 'counter', Repeat_count: 2, fallback_state: 'escalate_to_agent']
    
    Args:
        action_key: Unique identifier for the action
        state_manager: Conversation state manager instance
        max_retries: Maximum retries allowed (default: 2)
        fallback_state: State to fallback to if max retries exceeded
        
    Returns:
        tuple: (should_continue, next_state)
    """
    return state_manager.handle_retry_logic(action_key, max_retries, fallback_state)


def create_conversation_state_manager() -> ConversationStateManager:
    """Create a new conversation state manager instance."""
    return ConversationStateManager()


# Environment Variable Management for DI compliance
class EnvironmentVariableManager:
    """Manages environment variables for conversation state tracking."""
    
    def __init__(self):
        self.variables = {}
        self.variable_types = {}
        self.variable_descriptions = {}
        self.variable_history = {}
    
    def update_env_var(self, variable: str, value: any, var_type: str = None, description: str = None) -> None:
        """
        Update environment variable with value, type, and description.
        
        Args:
            variable: Variable name
            value: Variable value
            var_type: Variable type (str, int, float, bool, list, dict)
            description: Human-readable description of the variable
        """
        # Store previous value for history
        if variable in self.variables:
            if variable not in self.variable_history:
                self.variable_history[variable] = []
            self.variable_history[variable].append({
                "timestamp": current_timestamp(),
                "old_value": self.variables[variable],
                "new_value": value
            })
        
        # Update variable
        self.variables[variable] = value
        
        # Store type and description if provided
        if var_type:
            self.variable_types[variable] = var_type
        if description:
            self.variable_descriptions[variable] = description
    
    def get_env_var(self, variable: str, default: any = None) -> any:
        """Get environment variable value."""
        return self.variables.get(variable, default)
    
    def get_env_var_type(self, variable: str) -> str:
        """Get environment variable type."""
        return self.variable_types.get(variable, "unknown")
    
    def get_env_var_description(self, variable: str) -> str:
        """Get environment variable description."""
        return self.variable_descriptions.get(variable, "")
    
    def get_env_var_history(self, variable: str) -> list:
        """Get environment variable change history."""
        return self.variable_history.get(variable, [])
    
    def list_env_vars(self) -> dict:
        """List all environment variables with their metadata."""
        return {
            var: {
                "value": self.variables[var],
                "type": self.variable_types.get(var, "unknown"),
                "description": self.variable_descriptions.get(var, ""),
                "history_count": len(self.variable_history.get(var, []))
            }
            for var in self.variables
        }
    
    def validate_env_var(self, variable: str, expected_type: str = None) -> bool:
        """Validate environment variable exists and has correct type."""
        if variable not in self.variables:
            return False
        
        if expected_type:
            actual_type = self.variable_types.get(variable, type(self.variables[variable]).__name__)
            return actual_type == expected_type
        
        return True
    
    def clear_env_var(self, variable: str) -> None:
        """Clear an environment variable."""
        if variable in self.variables:
            del self.variables[variable]
        if variable in self.variable_types:
            del self.variable_types[variable]
        if variable in self.variable_descriptions:
            del self.variable_descriptions[variable]
    
    def clear_all_env_vars(self) -> None:
        """Clear all environment variables."""
        self.variables.clear()
        self.variable_types.clear()
        self.variable_descriptions.clear()
        self.variable_history.clear()


def update_env_var(variable: str, value: any, var_type: str = None, description: str = None) -> None:
    """
    Update environment variable - DI compliant function.
    
    This implements the DI pattern: UpdateEnvVar [variable: 'origin', value: 'New York, NY']
    
    Args:
        variable: Variable name
        value: Variable value
        var_type: Variable type (str, int, float, bool, list, dict)
        description: Human-readable description
    """
    # This would typically be called on a global or session-specific environment manager
    # For now, we'll create a simple implementation
    pass


# Flight-specific environment variable management
class FlightBookingEnvironmentManager(EnvironmentVariableManager):
    """Specialized environment manager for flight booking conversations."""
    
    # Define standard flight booking variables as per DI
    FLIGHT_VARIABLES = {
        "origin": {"type": "str", "description": "Departure city in 'City, State' format"},
        "destination": {"type": "str", "description": "Destination city in 'City, State' format"},
        "earliest_departure_date": {"type": "str", "description": "Earliest departure date in YYYY-MM-DD format"},
        "latest_departure_date": {"type": "str", "description": "Latest departure date in YYYY-MM-DD format"},
        "earliest_return_date": {"type": "str", "description": "Earliest return date in YYYY-MM-DD format"},
        "latest_return_date": {"type": "str", "description": "Latest return date in YYYY-MM-DD format"},
        "num_adult_passengers": {"type": "int", "description": "Number of adult passengers"},
        "num_child_passengers": {"type": "int", "description": "Number of child passengers"},
        "num_infant_in_lap_passengers": {"type": "int", "description": "Number of infant passengers (in lap)"},
        "num_infant_in_seat_passengers": {"type": "int", "description": "Number of infant passengers (in seat)"},
        "carry_on_bag_count": {"type": "int", "description": "Number of carry-on bags"},
        "checked_bag_count": {"type": "int", "description": "Number of checked bags"},
        "currency": {"type": "str", "description": "Price currency (e.g., USD, EUR)"},
        "depart_after_hour": {"type": "int", "description": "Departure after hour (1-23)"},
        "depart_before_hour": {"type": "int", "description": "Departure before hour (1-23)"},
        "include_airlines": {"type": "list", "description": "List of preferred airlines"},
        "max_stops": {"type": "int", "description": "Maximum number of stops/layovers"},
        "seating_classes": {"type": "list", "description": "Preferred seating classes"},
        "cheapest": {"type": "bool", "description": "Sort results by price (ascending)"},
        "selected_flight": {"type": "dict", "description": "Selected flight for booking"},
        "travelers": {"type": "list", "description": "List of traveler information"},
        "booking_confirmation": {"type": "str", "description": "Booking confirmation number"}
    }
    
    def __init__(self):
        super().__init__()
        self._initialize_flight_variables()
    
    def _initialize_flight_variables(self) -> None:
        """Initialize flight booking variables with default values."""
        for var_name, var_config in self.FLIGHT_VARIABLES.items():
            self.variable_types[var_name] = var_config["type"]
            self.variable_descriptions[var_name] = var_config["description"]
            
            # Set default values based on type
            if var_config["type"] == "str":
                self.variables[var_name] = ""
            elif var_config["type"] == "int":
                self.variables[var_name] = 0
            elif var_config["type"] == "bool":
                self.variables[var_name] = False
            elif var_config["type"] == "list":
                self.variables[var_name] = []
            elif var_config["type"] == "dict":
                self.variables[var_name] = {}
    
    def update_flight_var(self, variable: str, value: any) -> None:
        """Update flight-specific variable with validation."""
        if variable not in self.FLIGHT_VARIABLES:
            raise ValidationError(f"Unknown flight variable: {variable}")
        
        var_config = self.FLIGHT_VARIABLES[variable]
        expected_type = var_config["type"]
        
        # Validate type
        if not self._validate_value_type(value, expected_type):
            raise ValidationError(f"Invalid type for {variable}. Expected {expected_type}, got {type(value).__name__}")
        
        # Update with metadata
        self.update_env_var(variable, value, expected_type, var_config["description"])
    
    def _validate_value_type(self, value: any, expected_type: str) -> bool:
        """Validate value type matches expected type."""
        if expected_type == "str":
            return isinstance(value, str)
        elif expected_type == "int":
            return isinstance(value, int)
        elif expected_type == "float":
            return isinstance(value, (int, float))
        elif expected_type == "bool":
            return isinstance(value, bool)
        elif expected_type == "list":
            return isinstance(value, list)
        elif expected_type == "dict":
            return isinstance(value, dict)
        return False
    
    def get_flight_search_params(self) -> dict:
        """Get flight search parameters from environment variables."""
        search_params = {}
        
        for var_name in ["origin", "destination", "earliest_departure_date", 
                        "latest_departure_date", "earliest_return_date", "latest_return_date",
                        "num_adult_passengers", "num_child_passengers", "num_infant_in_lap_passengers",
                        "num_infant_in_seat_passengers", "carry_on_bag_count", "checked_bag_count",
                        "currency", "depart_after_hour", "depart_before_hour", "include_airlines",
                        "max_stops", "seating_classes", "cheapest"]:
            
            value = self.get_env_var(var_name)
            if value and value != "" and value != 0 and value != [] and value != {}:
                search_params[var_name] = value
        
        return search_params
    
    def is_flight_search_complete(self) -> bool:
        """Check if all required flight search parameters are collected."""
        required_vars = ["origin", "destination", "earliest_departure_date", 
                        "latest_departure_date", "earliest_return_date", "latest_return_date",
                        "num_adult_passengers", "num_child_passengers"]
        
        for var in required_vars:
            value = self.get_env_var(var)
            if not value or value == "" or value == 0:
                return False
        
        return True
    
    def is_booking_ready(self) -> bool:
        """Check if booking is ready (flight selected and travelers provided)."""
        selected_flight = self.get_env_var("selected_flight")
        travelers = self.get_env_var("travelers")
        
        return bool(selected_flight) and bool(travelers) and len(travelers) > 0
    
    def get_missing_flight_info(self) -> list:
        """Get list of missing required flight information."""
        missing = []
        
        required_vars = ["origin", "destination", "earliest_departure_date", 
                        "latest_departure_date", "earliest_return_date", "latest_return_date",
                        "num_adult_passengers", "num_child_passengers"]
        
        for var in required_vars:
            value = self.get_env_var(var)
            if not value or value == "" or value == 0:
                missing.append(var)
        
        return missing


def ensure_json_serializable(data: Any) -> Any:
    """Ensure an object can be safely converted to JSON."""
    try:
        json.dumps(data)
        return data
    except Exception as e:
        raise ValidationError(f"Data not serializable: {e}")


def validate_string(val: Optional[str], field: str, allow_empty: bool = False) -> Optional[str]:
    if val is None:
        return None
    if not isinstance(val, str):
        raise ValidationError(f"{field} must be a string")
    if not allow_empty and not val.strip():
        raise ValidationError(f"{field} cannot be empty")
    return val.strip()


def validate_date(val: Any, field: str) -> date:
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val))
    except Exception:
        raise ValidationError(f"{field} must be a valid YYYY-MM-DD date")


def convert_city_format(city: str) -> str:
    """
    Convert city name or IATA code to standardized format for flight searches.
    Supports both city names and IATA airport codes.
    
    Args:
        city (str): Input city name or IATA code
        
    Returns:
        str: Standardized city format or IATA code
    """
    if not city or not isinstance(city, str):
        return city
    
    # If the string is only whitespace, return as-is
    if city.isspace():
        return city
    
    city = city.strip().upper()
    
    # If it's already a 3-letter IATA code, return as-is
    if len(city) == 3 and city.isalpha():
        return city
    
    # IATA code mappings for major airports and cities
    iata_mappings = {
        # Major US Cities and Airports
        "NEW YORK": "JFK", "NYC": "JFK", "NEW YORK CITY": "JFK",
        "LOS ANGELES": "LAX", "LA": "LAX",
        "CHICAGO": "ORD", "CHICAGO O'HARE": "ORD",
        "HOUSTON": "IAH", "HOUSTON INTERCONTINENTAL": "IAH",
        "PHOENIX": "PHX", "PHOENIX SKY HARBOR": "PHX",
        "PHILADELPHIA": "PHL",
        "SAN ANTONIO": "SAT",
        "SAN DIEGO": "SAN",
        "DALLAS": "DFW", "DALLAS FORT WORTH": "DFW",
        "SAN JOSE": "SJC",
        "AUSTIN": "AUS",
        "JACKSONVILLE": "JAX",
        "FORT WORTH": "DFW",
        "COLUMBUS": "CMH",
        "CHARLOTTE": "CLT",
        "SAN FRANCISCO": "SFO",
        "INDIANAPOLIS": "IND",
        "SEATTLE": "SEA", "SEATTLE TACOMA": "SEA",
        "DENVER": "DEN", "DENVER INTERNATIONAL": "DEN",
        "WASHINGTON": "DCA", "WASHINGTON DC": "DCA", "WASHINGTON DULLES": "IAD",
        "BOSTON": "BOS", "BOSTON LOGAN": "BOS",
        "EL PASO": "ELP",
        "NASHVILLE": "BNA",
        "DETROIT": "DTW", "DETROIT METRO": "DTW",
        "OKLAHOMA CITY": "OKC",
        "PORTLAND": "PDX", "PORTLAND OREGON": "PDX",
        "LAS VEGAS": "LAS", "LAS VEGAS MCCARRAN": "LAS",
        "MEMPHIS": "MEM",
        "LOUISVILLE": "SDF",
        "BALTIMORE": "BWI", "BALTIMORE WASHINGTON": "BWI",
        "MILWAUKEE": "MKE",
        "ALBUQUERQUE": "ABQ",
        "TUCSON": "TUS",
        "FRESNO": "FAT",
        "SACRAMENTO": "SMF",
        "MESA": "PHX",  # Mesa uses Phoenix airport
        "KANSAS CITY": "MCI",
        "ATLANTA": "ATL", "ATLANTA HARTSFIELD": "ATL",
        "LONG BEACH": "LGB",
        "COLORADO SPRINGS": "COS",
        "RALEIGH": "RDU", "RALEIGH DURHAM": "RDU",
        "MIAMI": "MIA", "MIAMI INTERNATIONAL": "MIA",
        "VIRGINIA BEACH": "ORF", "NORFOLK": "ORF",
        "OMAHA": "OMA",
        "OAKLAND": "OAK",
        "MINNEAPOLIS": "MSP", "MINNEAPOLIS ST PAUL": "MSP",
        "TULSA": "TUL",
        "ARLINGTON": "DFW",  # Arlington uses Dallas airport
        "TAMPA": "TPA", "TAMPA INTERNATIONAL": "TPA",
        "NEW ORLEANS": "MSY", "NEW ORLEANS LOUIS ARMSTRONG": "MSY",
        "WICHITA": "ICT",
        "CLEVELAND": "CLE", "CLEVELAND HOPKINS": "CLE",
        "BAKERSFIELD": "BFL",
        "AURORA": "DEN",  # Aurora uses Denver airport
        "ANAHEIM": "SNA", "ORANGE COUNTY": "SNA",
        "HONOLULU": "HNL", "HONOLULU INTERNATIONAL": "HNL",
        "SANTA ANA": "SNA",
        "CORPUS CHRISTI": "CRP",
        "RIVERSIDE": "ONT", "ONTARIO": "ONT",
        "LEXINGTON": "LEX",
        "STOCKTON": "SCK",
        "TOLEDO": "TOL",
        "ST PAUL": "MSP",  # St. Paul uses Minneapolis airport
        "NEWARK": "EWR", "NEWARK LIBERTY": "EWR",
        "GREENSBORO": "GSO",
        "PLANO": "DFW",  # Plano uses Dallas airport
        "HENDERSON": "LAS",  # Henderson uses Las Vegas airport
        "LINCOLN": "LNK",
        "BUFFALO": "BUF", "BUFFALO NIAGARA": "BUF",
        "JERSEY CITY": "EWR",  # Jersey City uses Newark airport
        "CHULA VISTA": "SAN",  # Chula Vista uses San Diego airport
        "FORT WAYNE": "FWA",
        "ORLANDO": "MCO", "ORLANDO INTERNATIONAL": "MCO",
        "ST PETERSBURG": "TPA",  # St. Petersburg uses Tampa airport
        "CHANDLER": "PHX",  # Chandler uses Phoenix airport
        "LAREDO": "LRD",
        "NORFOLK": "ORF",
        "DURHAM": "RDU",  # Durham uses Raleigh airport
        "MADISON": "MSN",
        "LUBBOCK": "LBB",
        "IRVINE": "SNA",  # Irvine uses Orange County airport
        "WINSTON SALEM": "INT",
        "GLENDALE": "PHX",  # Glendale uses Phoenix airport
        "GARLAND": "DFW",  # Garland uses Dallas airport
        "HIALEAH": "MIA",  # Hialeah uses Miami airport
        "RENO": "RNO", "RENO TAHOE": "RNO",
        "CHESAPEAKE": "ORF",  # Chesapeake uses Norfolk airport
        "GILBERT": "PHX",  # Gilbert uses Phoenix airport
        "BATON ROUGE": "BTR",
        "IRVING": "DFW",  # Irving uses Dallas airport
        "SCOTTSDALE": "PHX",  # Scottsdale uses Phoenix airport
        "NORTH LAS VEGAS": "LAS",  # North Las Vegas uses Las Vegas airport
        "FREMONT": "SFO",  # Fremont uses San Francisco airport
        "BOISE": "BOI",
        "RICHMOND": "RIC",
        "SAN BERNARDINO": "ONT",  # San Bernardino uses Ontario airport
        "BIRMINGHAM": "BHM",
        "SPOKANE": "GEG",
        "ROCHESTER": "ROC",
        "DES MOINES": "DSM",
        "MODESTO": "MOD",
        "FAYETTEVILLE": "FAY",
        "TACOMA": "SEA",  # Tacoma uses Seattle airport
        "OXNARD": "OXR",
        "FONTANA": "ONT",  # Fontana uses Ontario airport
        "MONTGOMERY": "MGM",
        "MORENO VALLEY": "ONT",  # Moreno Valley uses Ontario airport
        "SHREVEPORT": "SHV",
        "YONKERS": "JFK",  # Yonkers uses JFK airport
        "AKRON": "CAK",
        "HUNTINGTON BEACH": "SNA",  # Huntington Beach uses Orange County airport
        "LITTLE ROCK": "LIT",
        "AUGUSTA": "AGS",
        "AMARILLO": "AMA",
        "MOBILE": "MOB",
        "GRAND RAPIDS": "GRR",
        "SALT LAKE CITY": "SLC", "SALT LAKE CITY INTERNATIONAL": "SLC",
        "TALLAHASSEE": "TLH",
        "HUNTSVILLE": "HSV",
        "GRAND PRAIRIE": "DFW",  # Grand Prairie uses Dallas airport
        "KNOXVILLE": "TYS",
        "WORCESTER": "BOS",  # Worcester uses Boston airport
        "NEWPORT NEWS": "ORF",  # Newport News uses Norfolk airport
        "BROWNSVILLE": "BRO",
        "OVERLAND PARK": "MCI",  # Overland Park uses Kansas City airport
        "SANTA CLARITA": "BUR", "BURBANK": "BUR",
        "PROVIDENCE": "PVD",
        "GARDEN GROVE": "SNA",  # Garden Grove uses Orange County airport
        "CHATTANOOGA": "CHA",
        "OCEANSIDE": "SAN",  # Oceanside uses San Diego airport
        "JACKSON": "JAN",
        "FORT LAUDERDALE": "FLL", "FORT LAUDERDALE HOLLYWOOD": "FLL",
        "SANTA ROSA": "STS",
        "RANCHO CUCAMONGA": "ONT",  # Rancho Cucamonga uses Ontario airport
        "PORT ST LUCIE": "PBI",  # Port St. Lucie uses West Palm Beach airport
        "TEMPE": "PHX",  # Tempe uses Phoenix airport
        "ONTARIO": "ONT",
        "SIOUX FALLS": "FSD",
        "SPRINGFIELD": "SGF",
        "PEORIA": "PIA",
        "PEMBROKE PINES": "FLL",  # Pembroke Pines uses Fort Lauderdale airport
        "ELK GROVE": "SMF",  # Elk Grove uses Sacramento airport
        "ROCKFORD": "RFD",
        "PALMDALE": "PMD",
        "CORONA": "ONT",  # Corona uses Ontario airport
        "SALINAS": "SNS",
        "POMONA": "ONT",  # Pomona uses Ontario airport
        "PASADENA": "BUR",  # Pasadena uses Burbank airport
        "JOLIET": "ORD",  # Joliet uses Chicago O'Hare airport
        "PATERSON": "EWR",  # Paterson uses Newark airport
        "TORRANCE": "LAX",  # Torrance uses Los Angeles airport
        "SYRACUSE": "SYR",
        "BRIDGEPORT": "BDL", "HARTFORD": "BDL",
        "HAYWARD": "OAK",  # Hayward uses Oakland airport
        "FORT COLLINS": "DEN",  # Fort Collins uses Denver airport
        "ESCONDIDO": "SAN",  # Escondido uses San Diego airport
        "LAKEWOOD": "DEN",  # Lakewood uses Denver airport
        "NAPERVILLE": "ORD",  # Naperville uses Chicago O'Hare airport
        "DAYTON": "DAY",
        "HOLLYWOOD": "FLL",  # Hollywood uses Fort Lauderdale airport
        "SUNNYVALE": "SJC",  # Sunnyvale uses San Jose airport
        "CARY": "RDU",  # Cary uses Raleigh airport
        "MESQUITE": "DFW",  # Mesquite uses Dallas airport
        "MIDLAND": "MAF",
        "MCKINNEY": "DFW",  # McKinney uses Dallas airport
        "EL MONTE": "LAX",  # El Monte uses Los Angeles airport
        "CLARKSVILLE": "BNA",  # Clarksville uses Nashville airport
        "ROCKY MOUNT": "RDU",  # Rocky Mount uses Raleigh airport
        
        # International Cities and Airports
        "LONDON": "LHR", "LONDON HEATHROW": "LHR",
        "PARIS": "CDG", "PARIS CHARLES DE GAULLE": "CDG",
        "TOKYO": "NRT", "TOKYO NARITA": "NRT",
        "SYDNEY": "SYD", "SYDNEY KINGSFORD SMITH": "SYD",
        "TORONTO": "YYZ", "TORONTO PEARSON": "YYZ",
        "VANCOUVER": "YVR",
        "MONTREAL": "YUL", "MONTREAL TRUDEAU": "YUL",
        "MEXICO CITY": "MEX", "MEXICO CITY INTERNATIONAL": "MEX",
        "MADRID": "MAD", "MADRID BARAJAS": "MAD",
        "ROME": "FCO", "ROME FIUMICINO": "FCO",
        "BERLIN": "TXL", "BERLIN TEGEL": "TXL",
        "AMSTERDAM": "AMS", "AMSTERDAM SCHIPHOL": "AMS",
        "ZURICH": "ZUR",
        "VIENNA": "VIE", "VIENNA INTERNATIONAL": "VIE",
        "PRAGUE": "PRG", "PRAGUE VACLAV HAVEL": "PRG",
        "BUDAPEST": "BUD", "BUDAPEST FERENC LISZT": "BUD",
        "WARSAW": "WAW", "WARSAW CHOPIN": "WAW",
        "MOSCOW": "SVO", "MOSCOW SHEREMETYEVO": "SVO",
        "ISTANBUL": "IST", "ISTANBUL AIRPORT": "IST",
        "DUBAI": "DXB", "DUBAI INTERNATIONAL": "DXB",
        "SINGAPORE": "SIN", "SINGAPORE CHANGI": "SIN",
        "HONG KONG": "HKG", "HONG KONG INTERNATIONAL": "HKG",
        "SEOUL": "ICN", "SEOUL INCHEON": "ICN",
        "BEIJING": "PEK", "BEIJING CAPITAL": "PEK",
        "SHANGHAI": "PVG", "SHANGHAI PUDONG": "PVG",
        "MUMBAI": "BOM", "MUMBAI CHHATRAPATI SHIVAJI": "BOM",
        "DELHI": "DEL", "DELHI INDIRA GANDHI": "DEL",
        "BANGALORE": "BLR", "BANGALORE KEMPEGOWDA": "BLR",
        "CHENNAI": "MAA", "CHENNAI INTERNATIONAL": "MAA",
        "KOLKATA": "CCU", "KOLKATA NETAJI SUBHAS CHANDRA BOSE": "CCU",
        "HYDERABAD": "HYD", "HYDERABAD RAJIV GANDHI": "HYD",
        "PUNE": "PNQ", "PUNE INTERNATIONAL": "PNQ",
        "AHMEDABAD": "AMD", "AHMEDABAD SARDAR VALLABHBHAI PATEL": "AMD",
        "JAIPUR": "JAI", "JAIPUR INTERNATIONAL": "JAI",
        "SURAT": "STV", "SURAT INTERNATIONAL": "STV",
        "LUCKNOW": "LKO", "LUCKNOW CHAUDHARY CHARAN SINGH": "LKO",
        "KANPUR": "KNU", "KANPUR CIVIL": "KNU",
        "NAGPUR": "NAG", "NAGPUR DR. BABASAHEB AMBEDKAR": "NAG",
        "INDORE": "IDR", "INDORE DEVI AHILYABAI HOLKAR": "IDR",
        "THANE": "BOM",  # Thane uses Mumbai airport
        "BHOPAL": "BHO", "BHOPAL RAJA BHOJ": "BHO",
        "VISAKHAPATNAM": "VTZ", "VISAKHAPATNAM INTERNATIONAL": "VTZ",
        "PIMPRI": "PNQ",  # Pimpri uses Pune airport
        "PATNA": "PAT", "PATNA JAYPRAKASH NARAYAN": "PAT",
        "VADODARA": "BDQ", "VADODARA CIVIL": "BDQ",
        "GHAZIABAD": "DEL",  # Ghaziabad uses Delhi airport
        "LUDHIANA": "LUH", "LUDHIANA SAHNEWAL": "LUH",
        "AGRA": "AGR", "AGRA KHERIA": "AGR",
        "NASHIK": "ISK", "NASHIK OZAR": "ISK",
        "FARIDABAD": "DEL",  # Faridabad uses Delhi airport
        "MEERUT": "DEL",  # Meerut uses Delhi airport
        "RAJKOT": "RAJ", "RAJKOT CIVIL": "RAJ",
        "KALYAN": "BOM",  # Kalyan uses Mumbai airport
        "VASAI": "BOM",  # Vasai uses Mumbai airport
        "VARANASI": "VNS", "VARANASI LAL BAHADUR SHASTRI": "VNS",
        "SRINAGAR": "SXR", "SRINAGAR INTERNATIONAL": "SXR",
        "AURANGABAD": "IXU", "AURANGABAD CHIKKALTHANA": "IXU",
        "NAVI MUMBAI": "BOM",  # Navi Mumbai uses Mumbai airport
        "SOLAPUR": "SSE", "SOLAPUR CIVIL": "SSE",
        "KOLHAPUR": "KLH", "KOLHAPUR CIVIL": "KLH",
        "AMRITSAR": "ATQ", "AMRITSAR SRI GURU RAM DAS JEE": "ATQ",
        "NOIDA": "DEL",  # Noida uses Delhi airport
        "RANCHI": "IXR", "RANCHI BIRSA MUNDA": "IXR",
        "HOWRAH": "CCU",  # Howrah uses Kolkata airport
        "COIMBATORE": "CJB", "COIMBATORE PEELAMEDU": "CJB",
        "RAIPUR": "RPR", "RAIPUR SWAMI VIVEKANANDA": "RPR",
        "JABALPUR": "JLR", "JABALPUR DUMNA": "JLR",
        "GWALIOR": "GWL", "GWALIOR RAJMAHAL": "GWL",
        "VIJAYAWADA": "VGA", "VIJAYAWADA CIVIL": "VGA",
        "JODHPUR": "JDH", "JODHPUR CIVIL": "JDH",
        "MADURAI": "IXM", "MADURAI INTERNATIONAL": "IXM",
        "KOTA": "KTU", "KOTA CIVIL": "KTU",
        "GUWAHATI": "GAU", "GUWAHATI LOKPRIYA GOPINATH BORDOLOI": "GAU",
        "CHANDIGARH": "IXC", "CHANDIGARH INTERNATIONAL": "IXC",
        "HUBLI": "HBX", "HUBLI CIVIL": "HBX",
        "TIRUCHIRAPPALLI": "TRZ", "TIRUCHIRAPPALLI INTERNATIONAL": "TRZ",
        "BAREILLY": "BEK", "BAREILLY CIVIL": "BEK",
        "MYSORE": "MYQ", "MYSORE MANDYA": "MYQ",
        "TIRUPPUR": "TIR", "TIRUPPUR CIVIL": "TIR",
        "GURGAON": "DEL",  # Gurgaon uses Delhi airport
        "ALIGARH": "DEL",  # Aligarh uses Delhi airport
        "MORADABAD": "DEL",  # Moradabad uses Delhi airport
        "JALANDHAR": "JUC", "JALANDHAR CIVIL": "JUC",
        "BHUBANESWAR": "BBI", "BHUBANESWAR BIJU PATNAIK": "BBI",
        "SALEM": "SXV", "SALEM CIVIL": "SXV",
        "WARANGAL": "WGC", "WARANGAL CIVIL": "WGC",
        "GUNTUR": "GNT", "GUNTUR CIVIL": "GNT",
        "BHIWANDI": "BOM",  # Bhiwandi uses Mumbai airport
        "SAHARANPUR": "DEL",  # Saharanpur uses Delhi airport
        "GORAKHPUR": "GOP", "GORAKHPUR CIVIL": "GOP",
        "BIKANER": "BKB", "BIKANER CIVIL": "BKB",
        "AMRAVATI": "AKD", "AMRAVATI CIVIL": "AKD",
        "JAMSHEDPUR": "IXW", "JAMSHEDPUR SONARI": "IXW",
        "BHILAI": "RPR",  # Bhilai uses Raipur airport
        "CUTTACK": "BBI",  # Cuttack uses Bhubaneswar airport
        "FIROZABAD": "DEL",  # Firozabad uses Delhi airport
        "KOCHI": "COK", "KOCHI COCHIN": "COK",
        "BHAVNAGAR": "BHU", "BHAVNAGAR CIVIL": "BHU"
    }
    
    # Convert to uppercase for case-insensitive matching
    city_upper = city.upper()
    
    # Check IATA mappings
    if city_upper in iata_mappings:
        return iata_mappings[city_upper]
    
    # If not found in mappings, return as-is (assume it's already properly formatted)
    return city


# Date validation helper functions
def validate_date_range(earliest: date, latest: date, date_type: str) -> None:
    """Validate that earliest date is not after latest date."""
    if earliest > latest:
        raise ValidationError(f"Earliest {date_type} date cannot be after latest {date_type} date")


def validate_booking_date_range(departure: date, return_date: date) -> None:
    """Validate that return date is not before departure date."""
    if return_date < departure:
        raise ValidationError("Return date cannot be before departure date")


def process_date_without_year(date_str: str) -> str:
    """
    Process date string and convert to YYYY-MM-DD format.
    According to DI, system should not take year as input from user.
    Automatically assigns current year or next year based on date.
    
    Args:
        date_str: Date string in MM-DD or YYYY-MM-DD format
        
    Returns:
        str: Full date string in YYYY-MM-DD format (always)
        
    Raises:
        ValidationError: If date format is invalid
    """
    today = date.today()
    
    # If already has year (YYYY-MM-DD format)
    if len(date_str.split('-')) == 3:
        return date_str
    
    # If only month-day (MM-DD format)
    if len(date_str.split('-')) == 2:
        try:
            month, day = date_str.split('-')
            month = int(month)
            day = int(day)
            
            # Validate month and day
            if month < 1 or month > 12:
                raise ValidationError(f"Invalid month: {month}. Must be 1-12.")
            if day < 1 or day > 31:
                raise ValidationError(f"Invalid day: {day}. Must be 1-31.")
            
            # Try to create date with current year first
            try:
                current_year_date = date(today.year, month, day)
                # If the date has already passed this year, use next year
                if current_year_date < today:
                    next_year_date = date(today.year + 1, month, day)
                    return next_year_date.isoformat()
                else:
                    return current_year_date.isoformat()
            except ValueError:
                # Invalid date (like Feb 30), try next year
                try:
                    next_year_date = date(today.year + 1, month, day)
                    return next_year_date.isoformat()
                except ValueError:
                    raise ValidationError(f"Invalid date: {month}-{day}")
                    
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_str}. Expected MM-DD or YYYY-MM-DD format.")
    
    # Invalid format
    raise ValidationError(f"Invalid date format: {date_str}. Expected MM-DD or YYYY-MM-DD format.")


def validate_date_in_range(check_date: date, field_name: str) -> None:
    """Validate that date is not in the past and within reasonable future range."""
    today = date.today()
    
    # Check if date is in the past
    if check_date < today:
        raise ValidationError(f"{field_name} cannot be in the past. Please provide a future date.")
    
    # Check if date is too far in the future (more than 1 year)
    max_future_date = date(today.year + 1, today.month, today.day)
    if check_date > max_future_date:
        raise ValidationError(f"{field_name} cannot be more than 1 year in the future.")


# Workflow state management for DI compliance
def validate_workflow_order(step: str, required_data: dict) -> None:
    """
    Validate that information is collected in the strict order required by DI.
    
    Args:
        step: The current step in the workflow
        required_data: Dictionary containing the data collected so far
        
    Raises:
        ValidationError: If the workflow order is violated
    """
    # Define the strict order as per DI requirements
    workflow_steps = [
        "origin_destination",  # (a) Origin and destination cities
        "dates",              # (b) Departure and return dates
        "passengers",         # (c) Number of passengers
        "preferences"         # (d) Additional preferences
    ]
    
    current_step_index = workflow_steps.index(step) if step in workflow_steps else -1
    
    # Check that all previous steps have been completed
    for i in range(current_step_index):
        previous_step = workflow_steps[i]
        if not _is_step_completed(previous_step, required_data):
            raise ValidationError(
                f"Cannot proceed to {step} step. "
                f"Please complete {previous_step} step first according to the required order."
            )


def _is_step_completed(step: str, data: dict) -> bool:
    """Check if a workflow step has been completed with required data."""
    if step == "origin_destination":
        return (data.get("origin") and data.get("destination") and 
                data.get("origin").strip() and data.get("destination").strip())
    
    elif step == "dates":
        return (data.get("earliest_departure_date") and 
                data.get("latest_departure_date") and
                data.get("earliest_return_date") and 
                data.get("latest_return_date"))
    
    elif step == "passengers":
        return (data.get("num_adult_passengers") is not None and 
                data.get("num_child_passengers") is not None and
                data.get("num_adult_passengers") >= 1)
    
    elif step == "preferences":
        # Preferences are optional, so this step is always considered complete
        return True
    
    return False


def validate_booking_readiness(flight_selected: bool, travelers_complete: bool) -> None:
    """
    Validate that booking can proceed only when all required information is collected.
    
    Args:
        flight_selected: Whether a flight has been selected from search results
        travelers_complete: Whether all traveler information is complete
        
    Raises:
        ValidationError: If booking requirements are not met
    """
    if not flight_selected:
        raise ValidationError(
            "Cannot proceed with booking. Please select a flight from the search results first."
        )
    
    if not travelers_complete:
        raise ValidationError(
            "Cannot proceed with booking. Please provide complete traveler information "
            "(first name, last name, date of birth) for all passengers."
        )


# CES Flights specific helper functions
def _simplify_airline_name(airline: str) -> str:
    """
    Simplify airline names for display.
    
    Args:
        airline (str): Full airline name to simplify.
        
    Returns:
        str: Simplified airline name for display.
    """
    name_map = {
        'American Airlines': 'American',
        'United Airlines': 'United',
        'Delta': 'Delta',
        'Southwest': 'Southwest',
        'JetBlue': 'JetBlue'
    }
    return name_map.get(airline, airline)


def _format_time(time_str: str) -> str:
    """
    Format time from HH:MM:SS to 12-hour format.
    
    Args:
        time_str (str): Time string in HH:MM:SS format.
        
    Returns:
        str: Formatted time in 12-hour format (e.g., "2:30 PM").
    """
    try:
        time_obj = datetime.strptime(time_str, '%H:%M:%S')
        return time_obj.strftime('%I:%M %p').lstrip('0')
    except:
        return time_str


def _validate_basic_inputs(origin: str, destination: str, num_adults: int) -> bool:
    """
    Basic validation for flight search inputs.
    
    Args:
        origin (str): Origin city name.
        destination (str): Destination city name.
        num_adults (int): Number of adult passengers.
        
    Returns:
        bool: True if inputs are valid, False otherwise.
    """
    if not origin or not destination:
        return False
    if num_adults < 1:
        return False
    return True


def get_end_of_conversation_status(function_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get the end of conversation status for terminal functions.
    
    This function retrieves the status data stored when terminal functions
    (done, escalate, fail, cancel) are called.
    
    Args:
        function_name (Optional[str]): The name of the terminal function to get status for.
            Valid values: "done", "escalate", "fail", "cancel".
            If None, returns all end of conversation statuses.
    
    Returns:
        Optional[Dict[str, Any]]: The status data for the specified function, 
            or all statuses if function_name is None. Returns None if no data exists.
    
    """
    from .db import DB
    
    data = DB.get("_end_of_conversation_status")
    if data is None:
        return None
    
    if function_name:
        return data.get(function_name)
    
    return data