import unittest
from pydantic import ValidationError
from .airline_base_exception import AirlineBaseTestCase
from ..SimulationEngine.models import AirlineDB, Reservation, Flight, User 
from ..SimulationEngine.models import FlightDateDetails, PaymentMethodInReservation, FlightInReservation, PaymentMethod, SeatInfo, Membership
from ..SimulationEngine.db import DB
from ..SimulationEngine.models import FlightType, CabinType, Passenger, FlightDateDetails, FlightStatus


class TestImports(AirlineBaseTestCase):
    """
    Test suite for validating the Pydantic models.
    """

    def test_import_airline_package(self):
        """
        Test that the airline package can be imported successfully.
        """
        try:
            import APIs.airline
        except ImportError:
            self.fail("Failed to import APIs.airline package")

    def test_import_public_functions(self):
        """
        Test that the public functions can be imported successfully.
        """
        try:
            from APIs.airline.airline import book_reservation
            from APIs.airline.airline import cancel_reservation
            from APIs.airline.airline import search_direct_flight
            from APIs.airline.airline import search_onestop_flight
            from APIs.airline.airline import get_user_details
            from APIs.airline.airline import get_reservation_details
            from APIs.airline.airline import calculate
            from APIs.airline.airline import send_certificate
            from APIs.airline.airline import think
            from APIs.airline.airline import transfer_to_human_agents
            from APIs.airline.airline import update_reservation_passengers
            from APIs.airline.airline import update_reservation_baggages
            from APIs.airline.airline import update_reservation_flights
            from APIs.airline.airline import list_all_airports
        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")


    def test_public_functions_callable(self):
        """
        Test that the public functions are callable.
        """
        from APIs.airline.airline import book_reservation
        from APIs.airline.airline import cancel_reservation
        from APIs.airline.airline import search_direct_flight
        from APIs.airline.airline import search_onestop_flight
        from APIs.airline.airline import get_user_details
        from APIs.airline.airline import get_reservation_details
        from APIs.airline.airline import calculate
        from APIs.airline.airline import send_certificate
        from APIs.airline.airline import think
        from APIs.airline.airline import transfer_to_human_agents
        from APIs.airline.airline import update_reservation_passengers
        from APIs.airline.airline import update_reservation_baggages
        from APIs.airline.airline import update_reservation_flights
        from APIs.airline.airline import list_all_airports

        # test that the functions are callable
        self.assertTrue(callable(book_reservation))
        self.assertTrue(callable(cancel_reservation))
        self.assertTrue(callable(search_direct_flight))
        self.assertTrue(callable(search_onestop_flight))
        self.assertTrue(callable(get_user_details))
        self.assertTrue(callable(get_reservation_details))
        self.assertTrue(callable(calculate))
        self.assertTrue(callable(send_certificate))
        self.assertTrue(callable(think))
        self.assertTrue(callable(transfer_to_human_agents))
        self.assertTrue(callable(update_reservation_passengers))
        self.assertTrue(callable(update_reservation_baggages))
        self.assertTrue(callable(update_reservation_flights))
        self.assertTrue(callable(list_all_airports))

    def test_simulation_engine_imports(self):
        """
        Test that the simulation engine can be imported successfully.
        """
        try:
            from APIs.airline.SimulationEngine import models
            from APIs.airline.SimulationEngine import db
            from APIs.airline.SimulationEngine import custom_errors
            from APIs.airline.SimulationEngine import utils
        except ImportError as e:
            self.fail(f"Failed to import simulation engine: {e}")

    def test_simulation_engine_functions_callable(self):
        """
        Test that the simulation engine functions are callable.
        """
        from APIs.airline.SimulationEngine import models
        from APIs.airline.SimulationEngine import db
        from APIs.airline.SimulationEngine import custom_errors
        from APIs.airline.SimulationEngine import utils

        # test that the functions are callable
        self.assertTrue(callable(models.AirlineDB))
        self.assertTrue(callable(utils.search_flights))
        self.assertTrue(callable(utils.get_flight))
        self.assertTrue(callable(utils.get_reservation))
        self.assertTrue(callable(utils.get_user))
        self.assertTrue(callable(utils.search_onestop_flights))

        # test usability of the simulation engine
        self.assertTrue(type(DB) == dict)
        self.assertTrue(hasattr(utils, 'get_flight'))
        self.assertTrue(hasattr(utils, 'get_reservation'))
        self.assertTrue(hasattr(utils, 'get_user'))
        self.assertTrue(hasattr(utils, 'search_flights'))
        self.assertTrue(hasattr(utils, 'search_onestop_flights'))
        self.assertTrue(hasattr(utils, 'create_user'))
        self.assertTrue(hasattr(utils, 'add_flight'))
        self.assertTrue(hasattr(utils, 'add_payment_method_to_user'))
        

if __name__ == '__main__':
    unittest.main()