"""
Comprehensive tests for the improved Spaces.setup function.

Tests cover:
- Input validation and error handling
- Pydantic model validation
- Space creation scenarios
- Membership creation scenarios
- Edge cases and error conditions
- Business rule validation
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from google_chat.SimulationEngine.db import DB, CURRENT_USER_ID
from google_chat.SimulationEngine.custom_errors import (
    InvalidSetupBodyError, SpaceCreationFailedError, SelfMembershipError, MissingDisplayNameError
)
from google_chat.Spaces import setup as spaces_setup
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError


class TestSpacesSetup(BaseTestCaseWithErrorHandler):
    """Test suite for the improved Spaces.setup function."""

    def setUp(self):
        """Reset test state before each test."""
        DB.clear()
        DB.update({
            "User": [
                {"name": "users/test_user", "displayName": "Test User"},
                {"name": "users/other_user", "displayName": "Other User"},
                {"name": "users/bot_user", "displayName": "Bot User"}
            ],
            "Space": [],
            "Membership": [],
            "Message": [],
            "Reaction": [],
            "Attachment": []
        })
        CURRENT_USER_ID.clear()
        CURRENT_USER_ID.update({"id": "users/test_user"})

    def test_valid_setup_minimal_space(self):
        """Test successful setup with minimal space configuration."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            }
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)
        self.assertEqual(result["spaceType"], "GROUP_CHAT")
        self.assertIn("createTime", result)
        
        # Verify space was added to DB
        self.assertEqual(len(DB["Space"]), 1)
        self.assertEqual(DB["Space"][0]["spaceType"], "GROUP_CHAT")

    def test_valid_setup_space_with_display_name(self):
        """Test successful setup with SPACE type and required displayName."""
        setup_body = {
            "space": {
                "spaceType": "SPACE",
                "displayName": "Test Space",
                "externalUserAllowed": True
            }
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["spaceType"], "SPACE")
        self.assertEqual(result["displayName"], "Test Space")
        self.assertTrue(result["externalUserAllowed"])

    def test_valid_setup_with_memberships(self):
        """Test successful setup with memberships."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN",
                        "displayName": "Other User"
                    },
                    "role": "ROLE_MEMBER",
                    "state": "JOINED"
                }
            ]
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)
        
        # Verify membership was created
        memberships = [m for m in DB["Membership"] if m["name"] != f"{result['name']}/members/users/test_user"]
        self.assertEqual(len(memberships), 1)
        self.assertEqual(memberships[0]["role"], "ROLE_MEMBER")
        self.assertEqual(memberships[0]["state"], "JOINED")
        self.assertEqual(memberships[0]["member"]["name"], "users/other_user")

    def test_valid_setup_with_complex_configuration(self):
        """Test setup with complex space configuration."""
        setup_body = {
            "space": {
                "spaceType": "SPACE",
                "displayName": "Complex Space",
                "externalUserAllowed": True,
                "importMode": False,
                "spaceDetails": {
                    "description": "A test space with complex configuration",
                    "guidelines": "Be nice to each other"
                },
                "predefinedPermissionSettings": "COLLABORATION_SPACE",
                "accessSettings": {
                    "audience": "audiences/default"
                }
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN",
                        "displayName": "Other User"
                    },
                    "role": "ROLE_MANAGER"
                },
                {
                    "member": {
                        "name": "users/bot_user",
                        "type": "BOT",
                        "displayName": "Bot User"
                    },
                    "role": "ROLE_MEMBER",
                    "state": "INVITED"
                }
            ]
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["displayName"], "Complex Space")
        self.assertTrue(result["externalUserAllowed"])
        self.assertEqual(result["spaceDetails"]["description"], "A test space with complex configuration")
        self.assertEqual(result["predefinedPermissionSettings"], "COLLABORATION_SPACE")
        
        # Verify both memberships were created
        non_creator_memberships = [m for m in DB["Membership"] if m["name"] != f"{result['name']}/members/users/test_user"]
        self.assertEqual(len(non_creator_memberships), 2)

    # --- Input Validation Tests ---

    def test_invalid_setup_body_type(self):
        """Test that non-dict setup_body raises TypeError."""
        with self.assertRaises(TypeError) as cm:
            spaces_setup("not a dict")
        self.assertIn("setup_body must be a dictionary", str(cm.exception))

    def test_invalid_setup_body_none(self):
        """Test that None setup_body raises TypeError."""
        with self.assertRaises(TypeError) as cm:
            spaces_setup(None)
        self.assertIn("setup_body must be a dictionary", str(cm.exception))

    def test_empty_setup_body(self):
        """Test that empty setup_body raises InvalidSetupBodyError."""
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup({})
        self.assertIn("Invalid setup_body structure", str(cm.exception))

    def test_missing_space_configuration(self):
        """Test that missing space configuration raises InvalidSetupBodyError."""
        setup_body = {
            "memberships": []
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("Invalid setup_body structure", str(cm.exception))

    def test_invalid_space_type(self):
        """Test that invalid spaceType raises InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "INVALID_TYPE"
            }
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("Invalid setup_body structure", str(cm.exception))

    def test_missing_display_name_for_space(self):
        """Test that missing displayName for SPACE type raises InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "SPACE"
            }
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("displayName is required", str(cm.exception))

    def test_empty_display_name_for_space(self):
        """Test that empty displayName for SPACE type raises InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "SPACE",
                "displayName": "   "
            }
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("displayName is required", str(cm.exception))

    def test_invalid_member_name_format(self):
        """Test that invalid member name format raises InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "invalid_member_name",
                        "type": "HUMAN"
                    }
                }
            ]
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("Invalid setup_body structure", str(cm.exception))

    def test_duplicate_member_names(self):
        """Test that duplicate member names raise InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    }
                },
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    }
                }
            ]
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("Duplicate member name", str(cm.exception))

    def test_invalid_member_type(self):
        """Test that invalid member type raises InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "INVALID_TYPE"
                    }
                }
            ]
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("Invalid setup_body structure", str(cm.exception))

    def test_invalid_member_role(self):
        """Test that invalid member role raises InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    },
                    "role": "INVALID_ROLE"
                }
            ]
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("Invalid setup_body structure", str(cm.exception))

    def test_invalid_member_state(self):
        """Test that invalid member state raises InvalidSetupBodyError."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    },
                    "state": "INVALID_STATE"
                }
            ]
        }
        
        with self.assertRaises(InvalidSetupBodyError) as cm:
            spaces_setup(setup_body)
        self.assertIn("Invalid setup_body structure", str(cm.exception))

    # --- Business Logic Tests ---

    def test_duplicate_display_name_returns_empty_dict(self):
        """Test that duplicate displayName raises an error."""
        # First, create a space with the same displayName
        DB["Space"].append({
            "name": "spaces/existing",
            "displayName": "Test Space",
            "spaceType": "SPACE",
            "createTime": datetime.utcnow().isoformat() + "Z"
        })
        
        setup_body = {
            "space": {
                "spaceType": "SPACE",
                "displayName": "Test Space"
            }
        }
        
        # Should raise SpaceCreationFailedError when create() raises DuplicateDisplayNameError
        with self.assertRaises(SpaceCreationFailedError) as context:
            spaces_setup(setup_body)
        
        self.assertIn("Failed to create space: A space with displayName 'Test Space' already exists.", str(context.exception))

    def test_membership_creation_partial_failure(self):
        """Test that space is created even if some memberships fail."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/invalid_user",  # User doesn't exist in test DB
                        "type": "HUMAN"
                    },
                    "role": "ROLE_MEMBER"
                }
            ]
        }
        
        # This should succeed creating the space even though the membership might have issues
        result = spaces_setup(setup_body)
        
        # Space should still be created successfully
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)

    def test_empty_memberships_list(self):
        """Test that empty memberships list is handled correctly."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": []
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)
        
        # Should only have creator membership
        creator_memberships = [m for m in DB["Membership"] if m["name"] == f"{result['name']}/members/users/test_user"]
        self.assertEqual(len(creator_memberships), 1)

    def test_default_values_applied(self):
        """Test that default values are applied correctly."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    }
                    # role and state not specified - should use defaults
                }
            ]
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        
        # Check that defaults were applied
        non_creator_memberships = [m for m in DB["Membership"] if m["name"] != f"{result['name']}/members/users/test_user"]
        self.assertEqual(len(non_creator_memberships), 1)
        self.assertEqual(non_creator_memberships[0]["role"], "ROLE_MEMBER")
        self.assertEqual(non_creator_memberships[0]["state"], "INVITED")

    def test_existing_membership_skipped(self):
        """Test that existing memberships are skipped gracefully."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    }
                }
            ]
        }
        
        result = spaces_setup(setup_body)
        
        # Add the same membership again
        second_result = spaces_setup(setup_body)
        
        # Both should succeed
        self.assertIsInstance(result, dict)
        self.assertIsInstance(second_result, dict)

    def test_no_current_user_id(self):
        """Test behavior when CURRENT_USER_ID is not set."""
        CURRENT_USER_ID.clear()
        
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    }
                }
            ]
        }
        
        result = spaces_setup(setup_body)
        
        # Should still work, just no self-membership validation
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)

    def test_space_with_all_optional_fields(self):
        """Test space creation with all optional fields."""
        setup_body = {
            "space": {
                "spaceType": "SPACE",
                "displayName": "Full Feature Space",
                "externalUserAllowed": True,
                "importMode": False,
                "singleUserBotDm": False,
                "spaceDetails": {
                    "description": "A comprehensive test space",
                    "guidelines": "Test guidelines"
                },
                "predefinedPermissionSettings": "ANNOUNCEMENT_SPACE",
                "accessSettings": {
                    "audience": "audiences/test"
                }
            }
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["displayName"], "Full Feature Space")
        self.assertTrue(result["externalUserAllowed"])
        self.assertFalse(result["importMode"])
        self.assertFalse(result["singleUserBotDm"])
        self.assertEqual(result["spaceDetails"]["description"], "A comprehensive test space")
        self.assertEqual(result["predefinedPermissionSettings"], "ANNOUNCEMENT_SPACE")
        self.assertEqual(result["accessSettings"]["audience"], "audiences/test")

    def test_membership_with_custom_create_time(self):
        """Test membership creation with custom createTime."""
        custom_time = "2023-12-25T10:00:00Z"
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    },
                    "createTime": custom_time
                }
            ]
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        
        # Verify custom createTime was used
        non_creator_memberships = [m for m in DB["Membership"] if m["name"] != f"{result['name']}/members/users/test_user"]
        self.assertEqual(len(non_creator_memberships), 1)
        self.assertEqual(non_creator_memberships[0]["createTime"], custom_time)

    def test_bot_member_setup(self):
        """Test setup with bot members."""
        setup_body = {
            "space": {
                "spaceType": "GROUP_CHAT"
            },
            "memberships": [
                {
                    "member": {
                        "name": "users/app",
                        "type": "BOT",
                        "displayName": "Test Bot"
                    },
                    "role": "ROLE_MEMBER"
                }
            ]
        }
        
        result = spaces_setup(setup_body)
        
        self.assertIsInstance(result, dict)
        
        # Verify bot membership was created
        non_creator_memberships = [m for m in DB["Membership"] if m["name"] != f"{result['name']}/members/users/test_user"]
        self.assertEqual(len(non_creator_memberships), 1)
        self.assertEqual(non_creator_memberships[0]["member"]["type"], "BOT")
        self.assertEqual(non_creator_memberships[0]["member"]["name"], "users/app")

    def test_import_mode_true_no_self_membership(self):
        """Space in import mode should not auto-create caller membership."""
        setup_body = {
            "space": {
                "spaceType": "SPACE",
                "displayName": "Imported Space",
                "importMode": True
            }
        }

        result = spaces_setup(setup_body)

        # Space created
        self.assertIsInstance(result, dict)
        self.assertTrue(result["importMode"])

        # No memberships should be auto-created when importMode is True
        caller_memberships = [m for m in DB["Membership"] if CURRENT_USER_ID.get("id") in m["name"]]
        self.assertEqual(len(caller_memberships), 0)

    def test_single_user_bot_dm_no_self_membership(self):
        """singleUserBotDm direct-message spaces should not auto-create caller membership."""
        setup_body = {
            "space": {
                "spaceType": "DIRECT_MESSAGE",
                "singleUserBotDm": True
            }
        }

        result = spaces_setup(setup_body)

        self.assertIsInstance(result, dict)
        self.assertTrue(result["singleUserBotDm"])

        # Ensure no caller membership created
        caller_memberships = [m for m in DB["Membership"] if CURRENT_USER_ID.get("id") in m["name"]]
        self.assertEqual(len(caller_memberships), 0)

    def test_membership_with_group_member_and_delete_time(self):
        """Validate creation of membership containing groupMember and deleteTime fields."""
        custom_delete_time = "2024-01-01T00:00:00Z"
        setup_body = {
            "space": {"spaceType": "GROUP_CHAT"},
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    },
                    "groupMember": {
                        "name": "groups/test-group"
                    },
                    "deleteTime": custom_delete_time,
                    "role": "ROLE_MANAGER",
                    "state": "JOINED"
                }
            ]
        }

        result = spaces_setup(setup_body)
        self.assertIsInstance(result, dict)

        # Retrieve the created membership (excluding implicit creator membership)
        created_memberships = [
            m for m in DB["Membership"]
            if m["name"].startswith(result["name"]) and "other_user" in m["name"]
        ]
        self.assertEqual(len(created_memberships), 1)
        membership = created_memberships[0]
        # groupMember stored
        self.assertIn("groupMember", membership)
        self.assertEqual(membership["groupMember"].get("name"), "groups/test-group")
        # deleteTime preserved
        self.assertEqual(membership["deleteTime"], custom_delete_time)

    def test_invalid_group_member_format_raises_error(self):
        """Invalid groupMember name should raise InvalidSetupBodyError due to Pydantic validation."""
        setup_body = {
            "space": {"spaceType": "GROUP_CHAT"},
            "memberships": [
                {
                    "member": {
                        "name": "users/other_user",
                        "type": "HUMAN"
                    },
                    "groupMember": {
                        "name": "invalid_group_name"
                    }
                }
            ]
        }

        with self.assertRaises(InvalidSetupBodyError):
            spaces_setup(setup_body)


if __name__ == '__main__':
    unittest.main() 