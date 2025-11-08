import unittest


class ImportTest(unittest.TestCase):
    def test_import_zendesk_package(self):
        """Test that the main zendesk package can be imported."""
        try:
            import APIs.zendesk
        except ImportError:
            self.fail("Failed to import APIs.zendesk package")

    def test_import_public_functions(self):
        """Test that the public functions are imported."""
        try:
            from APIs.zendesk.Attachments import (
                create_attachment,
                delete_attachment,
                show_attachment,
            )
            from APIs.zendesk.Audit import list_audits_for_ticket, show_audit
            from APIs.zendesk.Comments import list_ticket_comments
            from APIs.zendesk.Organizations import (
                create_organization,
                delete_organization,
                list_organizations,
                show_organization,
                update_organization,
            )
            from APIs.zendesk.Search import list_search_results
            from APIs.zendesk.Tickets import (
                create_ticket,
                delete_ticket,
                list_tickets,
                show_ticket,
                update_ticket,
            )
            from APIs.zendesk.Users import (
                create_user,
                delete_user,
                list_users,
                show_user,
                update_user,
            )
        except ImportError:
            self.fail("Failed to import public functions from APIs.zendesk")

    def test_public_functions_are_callable(self):
        """Test that the public functions are callable."""
        from APIs.zendesk.Attachments import (
            create_attachment,
            delete_attachment,
            show_attachment,
        )
        from APIs.zendesk.Audit import list_audits_for_ticket, show_audit
        from APIs.zendesk.Comments import list_ticket_comments
        from APIs.zendesk.Organizations import (
            create_organization,
            delete_organization,
            list_organizations,
            show_organization,
            update_organization,
        )
        from APIs.zendesk.Search import list_search_results
        from APIs.zendesk.Tickets import (
            create_ticket,
            delete_ticket,
            list_tickets,
            show_ticket,
            update_ticket,
        )
        from APIs.zendesk.Users import (
            create_user,
            delete_user,
            list_users,
            show_user,
            update_user,
        )

        self.assertTrue(callable(create_attachment))
        self.assertTrue(callable(delete_attachment))
        self.assertTrue(callable(show_attachment))
        self.assertTrue(callable(list_audits_for_ticket))
        self.assertTrue(callable(show_audit))
        self.assertTrue(callable(list_ticket_comments))
        self.assertTrue(callable(create_organization))
        self.assertTrue(callable(delete_organization))
        self.assertTrue(callable(list_organizations))
        self.assertTrue(callable(show_organization))
        self.assertTrue(callable(update_organization))
        self.assertTrue(callable(list_search_results))
        self.assertTrue(callable(create_ticket))
        self.assertTrue(callable(delete_ticket))
        self.assertTrue(callable(list_tickets))
        self.assertTrue(callable(show_ticket))
        self.assertTrue(callable(update_ticket))
        self.assertTrue(callable(create_user))
        self.assertTrue(callable(delete_user))
        self.assertTrue(callable(list_users))
        self.assertTrue(callable(show_user))
        self.assertTrue(callable(update_user))

    def test_import_simulation_engine_components(self):
        """Test that the simulation engine components are imported."""
        try:
            from APIs.zendesk.SimulationEngine import utils
            from APIs.zendesk.SimulationEngine.custom_errors import (
                OrganizationAlreadyExistsError,
                UserNotFoundError,
                UserAlreadyExistsError,
                OrganizationNotFoundError,
                TicketNotFoundError,
                TicketAuditNotFoundError,
            )
            from APIs.zendesk.SimulationEngine.db import DB
            from APIs.zendesk.SimulationEngine.models import (
                OrganizationCreateInputData,
                UserCreateInputData,
                UserUpdateInputData,
                UserResponseData,
                TicketCreateInputData,
                TicketUpdateInputData,
            )
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine components: {e}")

    def test_simulation_engine_components_are_usable(self):
        """Test that imported SimulationEngine components are usable."""
        from APIs.zendesk.SimulationEngine import utils
        from APIs.zendesk.SimulationEngine.custom_errors import (
            OrganizationAlreadyExistsError,
            UserNotFoundError,
            UserAlreadyExistsError,
            OrganizationNotFoundError,
            TicketNotFoundError,
            TicketAuditNotFoundError,
        )
        from APIs.zendesk.SimulationEngine.db import DB
        from APIs.zendesk.SimulationEngine.models import (
            OrganizationCreateInputData,
            UserCreateInputData,
            UserUpdateInputData,
            UserResponseData,
            TicketCreateInputData,
            TicketUpdateInputData,
        )

        self.assertTrue(hasattr(utils, "generate_upload_token"))
        self.assertTrue(issubclass(OrganizationAlreadyExistsError, Exception))
        self.assertTrue(issubclass(UserNotFoundError, Exception))
        self.assertTrue(issubclass(UserAlreadyExistsError, Exception))
        self.assertTrue(issubclass(OrganizationNotFoundError, Exception))
        self.assertTrue(issubclass(TicketNotFoundError, Exception))
        self.assertTrue(issubclass(TicketAuditNotFoundError, Exception))
        self.assertIsInstance(DB, dict)
        self.assertTrue(hasattr(OrganizationCreateInputData, "model_validate"))
        self.assertTrue(hasattr(UserCreateInputData, "model_validate"))
        self.assertTrue(hasattr(UserUpdateInputData, "model_validate"))
        self.assertTrue(hasattr(UserResponseData, "model_validate"))
        self.assertTrue(hasattr(TicketCreateInputData, "model_validate"))
        self.assertTrue(hasattr(TicketUpdateInputData, "model_validate"))

    def test_function_map_import(self):
        """Test that the function map is imported."""
        try:
            from APIs.zendesk import _function_map
            self.assertTrue("create_organization" in _function_map)
            self.assertTrue("list_organizations" in _function_map)
            self.assertTrue("get_organization_details" in _function_map)
            self.assertTrue("update_organization" in _function_map)
            self.assertTrue("delete_organization" in _function_map)
            self.assertTrue("create_ticket" in _function_map)
            self.assertTrue("list_tickets" in _function_map)
            self.assertTrue("get_ticket_details" in _function_map)
            self.assertTrue("update_ticket" in _function_map)
            self.assertTrue("delete_ticket" in _function_map)
            self.assertTrue("create_user" in _function_map)
            self.assertTrue("list_users" in _function_map)
            self.assertTrue("get_user_details" in _function_map)
            self.assertTrue("update_user" in _function_map)
            self.assertTrue("delete_user" in _function_map)
            self.assertTrue("search" in _function_map)
            self.assertTrue("list_ticket_comments" in _function_map)
            self.assertTrue("delete_attachment" in _function_map)
            self.assertTrue("show_attachment" in _function_map)
            self.assertTrue("create_attachment" in _function_map)
            self.assertTrue("list_audits_for_ticket" in _function_map)
            self.assertTrue("show_audit" in _function_map)
        except ImportError:
            self.fail("Failed to import function map from APIs.zendesk")

if __name__ == "__main__":
    unittest.main()
