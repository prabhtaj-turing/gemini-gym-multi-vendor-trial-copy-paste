import unittest
from linkedin import Me
import linkedin as LinkedinAPI
from .common import reset_db
from linkedin.SimulationEngine.custom_errors import UserNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestMeEndpoints(BaseTestCaseWithErrorHandler):
    def setUp(self):
        LinkedinAPI.DB.clear()
        LinkedinAPI.DB.update(
            {
                "people": {},
                "organizations": {},
                "organizationAcls": {},
                "posts": {},
                "next_person_id": 1,
                "next_org_id": 1,
                "next_acl_id": 1,
                "next_post_id": 1,
                "current_person_id": None,
            }
        )

    def create_default_person(self):
        """Create a person and mark them as the current authenticated member."""
        person = {
            "firstName": {
                "localized": {"en_US": "Example"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedFirstName": "Example",
            "lastName": {
                "localized": {"en_US": "User"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedLastName": "User",
            "vanityName": "example-user",
        }
        person["id"] = "1"
        LinkedinAPI.DB["people"]["1"] = person
        LinkedinAPI.DB["current_person_id"] = "1"
        LinkedinAPI.DB["next_person_id"] = 2
        return person

    def test_get_me_success(self):
        self.create_default_person()
        response = Me.get_me()
        self.assertIn("data", response)
        self.assertEqual(response["data"]["id"], "1")

    def test_get_me_with_projection_success(self):
        self.create_default_person()
        projection = "(id,localizedFirstName)"
        response = Me.get_me(projection=projection)
        self.assertIn("data", response)
        data = response["data"]
        self.assertEqual(set(data.keys()), {"id", "localizedFirstName"})
        self.assertEqual(data["id"], "1")
        self.assertEqual(data["localizedFirstName"], "Example")

    def test_get_me_with_projection_success(self):
        self.create_default_person()
        projection = ""
        response = Me.get_me(projection=projection)
        self.assertIn("data", response)
        self.assertEqual(response["data"]["id"], "1")

    def test_get_me_with_projection_missing_field(self):
        self.create_default_person()
        projection = "(id,nonexistentField)"
        response = Me.get_me(projection=projection)
        self.assertIn("data", response)
        data = response["data"]
        self.assertEqual(set(data.keys()), {"id"})
        self.assertEqual(data["id"], "1")

    def test_get_me_projection_without_parentheses(self):
        self.create_default_person()
        projection = "id, localizedFirstName"
        with self.assertRaises(ValueError):
            response = Me.get_me(projection=projection)
            self.assertIn("data", response)
            data = response["data"]
            self.assertEqual(set(data.keys()), {"id", "localizedFirstName"})
            self.assertEqual(data["id"], "1")
            self.assertEqual(data["localizedFirstName"], "Example")

    def test_get_me_empty_projection(self):
        self.create_default_person()
        with self.assertRaises(ValueError):
            Me.get_me(projection="()")

    def test_get_me_blank_projection(self):
        self.create_default_person()
        with self.assertRaises(ValueError):
            Me.get_me(projection="   ")

    def test_get_me_duplicate_fields_in_projection(self):
        self.create_default_person()
        projection = "(id,id,localizedFirstName)"
        response = Me.get_me(projection=projection)
        self.assertIn("data", response)
        data = response["data"]
        self.assertEqual(set(data.keys()), {"id", "localizedFirstName"})
        self.assertEqual(data["id"], "1")
        self.assertEqual(data["localizedFirstName"], "Example")

    def test_get_me_no_authenticated_member(self):
        with self.assertRaises(UserNotFoundError):
            Me.get_me()

    def test_get_me_authenticated_person_not_found(self):
        LinkedinAPI.DB["current_person_id"] = "999"
        with self.assertRaises(UserNotFoundError):
            Me.get_me()

    def test_create_me_failure_when_authenticated_exists(self):
        new_person = self.create_default_person()
        self.assert_error_behavior( 
            Me.create_me,
            ValueError,
            "Authenticated member already exists.",
            person_data=new_person,
        )

    def test_create_me_success_when_no_authenticated_member(self):
        LinkedinAPI.DB["current_person_id"] = None
        new_person = {
            "firstName": {
                "localized": {"en_US": "Alice"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedFirstName": "Alice",
            "lastName": {
                "localized": {"en_US": "Smith"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedLastName": "Smith",
            "vanityName": "alice-smith",
        }
        response = Me.create_me(new_person)
        self.assertIn("data", response)
        self.assertEqual(LinkedinAPI.DB["current_person_id"], response["data"]["id"])
        self.assertEqual(response["data"]["id"], "1")

    def test_create_me_failure_when_invalid_person_data(self):
        new_person = {
            "firstName": {
                "localized": {"en_US": "Alice"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
        }
        self.assert_error_behavior(
            Me.create_me,
            ValueError,
            "Input Validation Failed for localizedFirstName",
            person_data=new_person,
        )

    def test_create_me_failure_when_invalid_person_data_localized_first_name(self):
        new_person = {
            "localizedFirstName": "",
            "localizedLastName": "Smith",
            "vanityName": "alice-smith",
            "firstName": {
                "localized": {"en_US": "Alice"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "lastName": {
                "localized": {"en_US": "Smith"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
        }
        self.assert_error_behavior(
            Me.create_me,
            ValueError,
            "Input Validation Failed for localizedFirstName",
            person_data=new_person,
        )

    def test_update_me_failure_when_no_authenticated_member(self):
        LinkedinAPI.DB["current_person_id"] = None
        updated_person = {
            "firstName": {
                "localized": {"en_US": "Alicia"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedFirstName": "Alicia",
            "lastName": {
                "localized": {"en_US": "Smith"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedLastName": "Smith",
            "vanityName": "alice-smith",
        }
        self.assert_error_behavior(
            Me.update_me,
            ValueError,
            "Authenticated member not found.",
            person_data=updated_person,
        )

    def test_update_me_success(self):
        self.create_default_person()
        updated_person = {
            "firstName": {
                "localized": {"en_US": "Alicia"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedFirstName": "Alicia",
            "lastName": {
                "localized": {"en_US": "Smith"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedLastName": "Smith",
            "vanityName": "alice-smith",
        }
        response = Me.update_me(updated_person)
        self.assertIn("data", response)
        self.assertEqual(response["data"]["firstName"]["localized"]["en_US"], "Alicia")

    def test_delete_me_success(self):
        self.create_default_person()
        response = Me.delete_me()
        self.assertIn("status", response)
        with self.assertRaises(UserNotFoundError):
            Me.get_me()

    def test_delete_me_no_authenticated_member(self):
        """Test delete_me when no authenticated member exists."""
        self.assert_error_behavior(
            Me.delete_me,
            ValueError,
            "Authenticated member not found."
        )

    def test_delete_me_authenticated_member_not_found(self):
        """Test delete_me when authenticated member ID exists but profile is not found."""
        LinkedinAPI.DB["current_person_id"] = "999"
        self.assert_error_behavior(
            Me.delete_me,
            ValueError,
            "Authenticated member not found."
        )

    def test_update_me_failure_when_invalid_person_data(self):
        self.create_default_person()
        updated_person = {
            "firstName": {
                "localized": {"en_US": "Alicia"},
                "preferredLocale": {"country": "US", "language": "en"},
            },  
            "localizedFirstName": "",
            "lastName": {
                "localized": {"en_US": "Smith"},
                "preferredLocale": {"country": "US", "language": "en"},
            },
            "localizedLastName": "Smith",
            "vanityName": "alice-smith",
        }   
        self.assert_error_behavior(
            Me.update_me,
            ValueError,
            "Input Validation Failed for localizedFirstName",
            person_data=updated_person,
        )
        
if __name__ == "__main__":
    unittest.main()
