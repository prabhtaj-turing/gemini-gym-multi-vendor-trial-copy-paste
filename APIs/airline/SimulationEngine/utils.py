"""
Utility functions for the Airline Service.
"""

from typing import Dict, List, Optional, Any

from .db import DB, reset_db
from .models import Flight, Reservation, User, Membership
from pydantic import ValidationError as PydanticValidationError

def get_flight(flight_number: str) -> Optional[Dict[str, Any]]:
    """Get flight by flight number.
    
    Args:
        flight_number (str): The unique flight number to search for.
    
    Returns:
        Optional[Dict[str, Any]]: The flight data if found, None otherwise.
            The flight dictionary contains:
            - flight_number (str): Unique identifier for the flight
            - origin (str): IATA code for the origin airport
            - destination (str): IATA code for the destination airport
            - scheduled_departure_time_est (str): Scheduled departure time
            - scheduled_arrival_time_est (str): Scheduled arrival time
            - dates (Dict[str, Dict[str, Any]]): Flight availability and pricing by date
    """
    return DB.get("flights", {}).get(flight_number)

def get_reservation(reservation_id: str) -> Optional[Dict[str, Any]]:
    """Get reservation by reservation ID.
    
    Args:
        reservation_id (str): The unique reservation ID to search for.
    
    Returns:
        Optional[Dict[str, Any]]: The reservation data if found, None otherwise.
            The reservation dictionary contains:
            - reservation_id (str): Unique identifier for the reservation
            - user_id (str): ID of the user who made the reservation
            - flights (List[Dict[str, Any]]): List of flight segments in the reservation
            - passengers (List[Dict[str, Any]]): List of passenger details
            - total_price (float): Total cost of the reservation
            - status (str): Current status of the reservation
    """
    return DB.get("reservations", {}).get(reservation_id)

def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by user ID.
    
    Args:
        user_id (str): The unique user ID to search for.
    
    Returns:
        Optional[Dict[str, Any]]: The user data if found, None otherwise.
            The user dictionary contains:
            - name (Dict[str, str]): A dictionary containing the user's name.
                - first_name (str): The user's first name (e.g., "Mia").
                - last_name (str): The user's last name (e.g., "Li").
            - address (Dict[str, str]): A dictionary containing the user's address.
                - address1 (str): The primary address line (e.g., "975 Sunset Drive").
                - address2 (str): The secondary address line, if applicable (e.g., "Suite 217").
                - city (str): The city name (e.g., "Austin").
                - state (str): The state code (e.g., "TX").
                - zip (str): The ZIP code (e.g., "78750").
                - country (str): The country name (e.g., "USA").
            - email (str): The user's email address (e.g., "mia.li3818@example.com").
            - dob (str): The user's date of birth in "YYYY-MM-DD" format (e.g., "1990-04-05").
            - payment_methods (Dict[str, Dict[str, Any]]): A mapping of payment method IDs
                to payment method details. Each payment method has the following structure:
                - source (str): The payment source type ("credit_card", "gift_card", or "certificate").
                - id (str): The unique payment method identifier.
                - brand (str, optional): The credit card brand (e.g., "visa") for credit cards.
                - last_four (str, optional): The last four digits of the card for credit cards.
                - amount (int, optional): The available balance for gift cards and certificates.
            - saved_passengers (List[Dict[str, str]]): A list of saved passenger profiles.
                Each passenger has the following structure:
                - first_name (str): The passenger's first name (e.g., "Amelia").
                - last_name (str): The passenger's last name (e.g., "Ahmed").
                - dob (str): The passenger's date of birth in "YYYY-MM-DD" format (e.g., "1957-03-21").
            - membership (str): The user's membership level ("gold", "silver", or "regular").
            - reservations (List[str]): A list of reservation IDs associated with the user
                (e.g., ["NO6JO3", "AIXC49", "HKEG34"]).

    """
    return DB.get("users", {}).get(user_id.strip())

def search_flights(origin: str, destination: str, date: str) -> List[Dict[str, Any]]:
    """Search for direct flights.
    
    Args:
        origin (str): IATA code for the origin airport (e.g., "SFO").
        destination (str): IATA code for the destination airport (e.g., "JFK").
        date (str): Date to search for flights in "YYYY-MM-DD" format.
    
    Returns:
        List[Dict[str, Any]]: A list of available direct flights. Each flight is a dictionary with the following keys:
            - flight_number(str): The flight number.
            - origin(str): The origin city airport in three letters, such as 'JFK'.
            - destination(str): The destination city airport in three letters, such as 'LAX'.
            - scheduled_departure_time_est(str): The scheduled departure time in EST. Date format is 'HH:MM:SS'.
            - scheduled_arrival_time_est(str): The scheduled arrival time in EST. Date format is 'HH:MM:SS'.
            - status(str): The status of the flight.
            - available_seats(Dict[str, int]): The number of available seats. It can have following keys:
                - basic_economy(int): The number of available basic economy seats.
                - economy(int): The number of available economy seats.
                - business(int): The number of available business seats.
            - prices(Dict[str, float]): The price of the flight. It can have following keys:
                - basic_economy(float): The price of the basic economy seat.
                - economy(float): The price of the economy seat.
                - business(float): The price of the business seat.
            - date(str): The specific date for this flight data in 'YYYY-MM-DD' format.
    """
    flights = DB.get("flights", {})
    results = []
    for flight in flights.values():
        if flight["origin"] == origin and flight["destination"] == destination:
            if date in flight["dates"] and flight["dates"][date]["status"] == "available":
                flight_info = {k: v for k, v in flight.items() if k != "dates"}
                flight_info.update(flight["dates"][date])
                results.append(flight_info)
    return results

from datetime import datetime, timedelta

def search_onestop_flights(origin: str, destination: str, date: str) -> List[List[Dict[str, Any]]]:
    """Search for one-stop flights.
    
    Args:
        origin (str): IATA code for the origin airport (e.g., "SFO").
        destination (str): IATA code for the destination airport (e.g., "JFK").
        date (str): Date to search for flights in "YYYY-MM-DD" format.
    
    Returns:
        List[List[Dict[str, Any]]]: List of one-stop flight combinations.
            Each combination is a list of two flight dictionaries representing the connecting flights.
            Each flight dictionary contains:
            - flight_number (str): Unique identifier for the flight
            - origin (str): IATA code for the origin airport
            - destination (str): IATA code for the destination airport
            - scheduled_departure_time_est (str): Scheduled departure time
            - scheduled_arrival_time_est (str): Scheduled arrival time
            - status (str): Flight status (e.g., "available")
            - actual_departure_time_est(Optional[str]): The actual departure time in EST. Date format is 'YYYY-MM-DDTHH:MM:SS'. This field is only present when the flight has actual times; for available flights, only scheduled times are provided.
            - actual_arrival_time_est(Optional[str]): The actual arrival time in EST. Date format is 'YYYY-MM-DDTHH:MM:SS'. This field is only present when the flight has actual times; for available flights, only scheduled times are provided.
            - available_seats(Dict[str, int]): The number of available seats. It can have following keys:
                    - basic_economy(int): The number of available basic economy seats.
                    - economy(int): The number of available economy seats.
                    - business(int): The number of available business seats.
            - prices(Dict[str, float]): The price of the flight. It can have following keys:
                - basic_economy(float): The price of the basic economy seat.
                - economy(float): The price of the economy seat.
                - business(float): The price of the business seat.
            - date (str): The date of the flight in the format 'YYYY-MM-DD'.
    """
    flights = DB.get("flights", {})
    results = []
    for flight1 in flights.values():
        if flight1["origin"] == origin:
            for flight2 in flights.values():
                if (
                    flight2["destination"] == destination
                    and flight1["destination"] == flight2["origin"]
                ):
                    date2 = date
                    if "+1" in flight1.get("scheduled_arrival_time_est", ""):
                        try:
                            current_date = datetime.strptime(date, "%Y-%m-%d")
                            next_day = current_date + timedelta(days=1)
                            date2 = next_day.strftime("%Y-%m-%d")
                        except ValueError:
                            # If date format is invalid, skip this flight pair
                            continue
                    
                    if (
                        flight1.get("scheduled_arrival_time_est", "").split("+")[0]
                        > flight2.get("scheduled_departure_time_est", "")
                    ):
                        continue
                    
                    flight1_date_data = flight1.get("dates", {}).get(date)
                    flight2_date_data = flight2.get("dates", {}).get(date2)

                    if (
                        flight1_date_data and flight1_date_data.get("status") == "available"
                        and flight2_date_data and flight2_date_data.get("status") == "available"
                    ):
                        result1 = {
                            k: v for k, v in flight1.items() if k != "dates"
                        }
                        result1.update(flight1_date_data)
                        result1["date"] = date
                        result2 = {
                            k: v for k, v in flight2.items() if k != "dates"
                        }
                        result2.update(flight2_date_data)
                        result2["date"] = date2
                        results.append([result1, result2])
    return results


def create_user(
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    dob: str,
    membership: Optional[str] = None,
    address: Optional[Dict[str, str]] = None,
    saved_passengers: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new user with detailed information and add it to the database.

    Args:
        user_id (str): The unique identifier for the user.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        email (str): The user's email address.
        dob (str): The user's date of birth in "YYYY-MM-DD" format.
        membership (Optional[str]): The user's membership status (e.g., "gold", "silver", or "regular"). Uses regular if not provided.
        address (Optional[Dict[str, str]]): A dictionary containing the user's
            address with keys like "address1", "city", "state", "zip", "country".
        saved_passengers (Optional[List[Dict[str, Any]]]): A list of pre-saved
            passenger details.

    Returns:
        Dict[str, Any]: The newly created user object containing:
            - user_id (str): Unique identifier for the user
            - name (str): Full name of the user
            - first_name (str): User's first name
            - last_name (str): User's last name
            - email (str): User's email address
            - dob (str): User's date of birth
            - membership (Optional[str]): User's membership status
            - address (Dict[str, str]): User's address information
            - saved_passengers (List[Dict[str, Any]]): List of saved passenger profiles
            - payment_methods (Dict[str, Any]): User's payment methods (initially empty)
            - reservations (List[str]): List of reservation IDs (initially empty)
    
    Raises:
        ValueError: If a user with the given user_id already exists.
    """
    users = DB.get("users", {})
    if user_id in users:
        raise ValueError(f"User with ID '{user_id}' already exists.")

    try:
        new_user = User(
            name={
                "first_name": first_name,
                "last_name": last_name,
            },
            email=email,
            dob=dob,
            membership=membership or "regular",
            address=address or {},
            saved_passengers=saved_passengers or [],
            payment_methods={},
            reservations=[]
        )
    except PydanticValidationError as e:
        raise e
    
    new_user = new_user.model_dump(mode="json")
    new_user['user_id'] = user_id
    users[user_id] = new_user
    return new_user


def add_flight(
    flight_number: str, 
    origin: str, 
    destination: str, 
    departure_time: str, 
    arrival_time: str, 
    dates: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Adds a new flight to the database.

    Args:
        flight_number (str): The unique identifier for the flight (e.g., "UA101").
        origin (str): The IATA code for the origin airport (e.g., "SFO").
        destination (str): The IATA code for the destination airport (e.g., "JFK").
        departure_time (str): The scheduled departure time in "HH:MM" format.
        arrival_time (str): The scheduled arrival time in "HH:MM" format.
        dates (Dict[str, Dict[str, Any]]): A dictionary where keys are dates in
            "YYYY-MM-DD" format and values are details for that date.
            Example:
            {
                "2024-01-01": {
                    "status": "available",
                    "prices": {"economy": 250, "business": 800, "first": 1500},
                    "available_seats": {"economy": 100, "business": 30, "first": 10}
                }
            }

    Returns:
        Dict[str, Any]: The newly created flight object containing:
            - flight_number (str): Unique identifier for the flight
            - origin (str): IATA code for the origin airport
            - destination (str): IATA code for the destination airport
            - scheduled_departure_time_est (str): Scheduled departure time
            - scheduled_arrival_time_est (str): Scheduled arrival time
            - dates (Dict[str, Dict[str, Any]]): Flight availability and pricing by date
    
    Raises:
        ValueError: If a flight with the given flight_number already exists.
    """
    flights = DB.get("flights", {})
    if flight_number in flights:
        raise ValueError(f"Flight with number '{flight_number}' already exists.")
    
    new_flight = {
        "flight_number": flight_number,
        "origin": origin,
        "destination": destination,
        "scheduled_departure_time_est": departure_time,
        "scheduled_arrival_time_est": arrival_time,
        "dates": dates
    }
    flights[flight_number] = new_flight
    return new_flight


def add_payment_method_to_user(
    user_id: str,
    payment_id: str,
    source: str,
    details: Dict[str, Any],
) -> Dict[str, Any]:
    """Adds a payment method to a user.

    Args:
        user_id (str): The ID of the user to add the payment method to.
        payment_id (str): The unique ID for the new payment method.
        source (str): The source of the payment method (e.g., "credit_card", "gift_card").
        details (Dict[str, Any]): A dictionary of details for the payment method.
            - For "credit_card": {"brand": str, "last_four": str}
            - For "gift_card" or "certificate": {"amount": int}

    Returns:
        Dict[str, Any]: The updated user object containing all user fields plus the new payment method.
            The payment_methods dictionary will include:
            - payment_id (str): Unique identifier for the payment method
            - source (str): Type of payment method
            - Additional fields from the details parameter (brand, last_four, amount, etc.)
    
    Raises:
        ValueError: If the user with the given user_id is not found. If a payment method with the given payment_id already exists for the user.
    """
    users = DB.get("users", {})
    user = users.get(user_id)
    if not user:
        raise ValueError(f"User with ID '{user_id}' not found.")
    
    if "payment_methods" not in user:
        user["payment_methods"] = {}
        
    if payment_id in user["payment_methods"]:
        raise ValueError(f"Payment method '{payment_id}' already exists for user '{user_id}'.")

    payment_method: Dict[str, Any] = {"id": payment_id, "source": source}
    payment_method.update(details)
    
    user["payment_methods"][payment_id] = payment_method
    return user
