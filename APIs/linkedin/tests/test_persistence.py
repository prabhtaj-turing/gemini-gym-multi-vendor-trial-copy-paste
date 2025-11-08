import unittest
import os
import linkedin as LinkedinAPI
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestPersistence(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()

    def create_default_person(self):
        """
        Create a person and mark them as the current authenticated member.
        """
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
        # With next_person_id starting at 1, the new person gets id "1".
        person["id"] = "1"
        LinkedinAPI.DB["people"]["1"] = person
        LinkedinAPI.DB["current_person_id"] = "1"
        LinkedinAPI.DB["next_person_id"] = 2
        return person

    def test_state_persistence(self):
        # Create a default person then delete them.
        self.create_default_person()
        LinkedinAPI.Me.delete_me()
        # Create an organization.
        LinkedinAPI.Organizations.create_organization(
            {
                "vanityName": "persist-org",
                "name": {
                    "localized": {"en_US": "Persist Organization"},
                    "preferredLocale": {"country": "US", "language": "en"},
                },
                "primaryOrganizationType": "COMPANY",
            }
        )
        temp_filepath = "temp_state.json"
        LinkedinAPI.save_state(temp_filepath)
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
        LinkedinAPI.load_state(temp_filepath)
        self.assertTrue(len(LinkedinAPI.DB["organizations"]) > 0)
        os.remove(temp_filepath)
