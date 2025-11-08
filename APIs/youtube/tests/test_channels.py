import unittest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from youtube.Channels import insert, update
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestChannelsInsert(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        self.mock_db = {
            "channels": {
                "channel1": {
                    "id": "channel1",
                    "categoryId": "1",
                    "forUsername": "user1",
                    "hl": "en",
                    "managedByMe": True,
                    "maxResults": 10,
                    "mine": True,
                    "mySubscribers": False,
                    "onBehalfOfContentOwner": "content_owner"
                }
            },
            "videoCategories": {
                "category1": {
                    "id": "1",
                    "snippet": {
                        "title": "Film & Animation",
                        "regionCode": "US"
                    }
                },
                "category2": {
                    "id": "2",
                    "snippet": {
                        "title": "Autos & Vehicles",
                        "regionCode": "US"
                    }
                },
                "category3": {
                    "id": "10",
                    "snippet": {
                        "title": "Music",
                        "regionCode": "CA"
                    }
                }
            }
        }

    # Test part parameter validation
    def test_insert_part_missing(self):
        """Test insert with missing part parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "part parameter is required",
            part=""
        )

    def test_insert_part_none(self):
        """Test insert with None part parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "part parameter is required",
            part=None
        )

    def test_insert_part_not_string(self):
        """Test insert with non-string part parameter"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "part must be a string",
            part=123
        )

    def test_insert_part_empty_string(self):
        """Test insert with empty string part parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "part cannot be an empty string",
            part="   "
        )

    def test_insert_part_invalid_value(self):
        """Test insert with invalid part parameter value"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Invalid part parameter value",
            part="invalid_part"
        )

    def test_insert_part_mixed_valid_invalid(self):
        """Test insert with mixed valid and invalid part values"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Invalid part parameter value",
            part="snippet,invalid_part"
        )

    # Test category_id parameter validation
    def test_insert_category_id_not_string(self):
        """Test insert with non-string category_id"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "category_id must be a string or None.",
            part="snippet",
            category_id=123
        )

    def test_insert_category_id_empty_string(self):
        """Test insert with empty string category_id"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "category_id cannot be an empty string.",
            part="snippet",
            category_id="   "
        )

    @patch("youtube.Channels.DB")
    def test_insert_category_id_not_in_database(self, mock_db):
        """Test insert with category_id not in database"""
        mock_db.get.return_value = self.mock_db["videoCategories"]
        self.assert_error_behavior(
            insert,
            ValueError,
            "Invalid category_id, category not found in the database.",
            part="snippet",
            category_id="999"
        )

    # Test for_username parameter validation
    def test_insert_for_username_not_string(self):
        """Test insert with non-string for_username"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "for_username must be a string or None.",
            part="snippet",
            for_username=123
        )

    def test_insert_for_username_empty_string(self):
        """Test insert with empty string for_username"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "for_username cannot be an empty string.",
            part="snippet",
            for_username="   "
        )

    # Test hl parameter validation
    def test_insert_hl_not_string(self):
        """Test insert with non-string hl"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "hl must be a string or None.",
            part="snippet",
            hl=123
        )

    def test_insert_hl_empty_string(self):
        """Test insert with empty string hl"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "hl cannot be an empty string.",
            part="snippet",
            hl="   "
        )

    def test_insert_hl_invalid_value(self):
        """Test insert with invalid hl value"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Invalid hl value, must be one of: af, az, id, ms, bs, ca, cs, da, de, et, en-IN, en-GB, en, es, es-419, es-US, eu, fil, fr, fr-CA, gl, hr, zu, is, it, sw, lv, lt, hu, nl, no, uz, pl, pt-PT, pt, ro, sq, sk, sl, sr-Latn, fi, sv, vi, tr, be, bg, ky, kk, mk, mn, ru, sr, uk, el, hy, iw, ur, ar, fa, ne, mr, hi, as, bn, pa, gu, or, ta, te, kn, ml, si, th, lo, my, ka, am, km",
            part="snippet",
            hl="invalid"
        )

    # Test channel_id parameter validation
    def test_insert_channel_id_not_string(self):
        """Test insert with non-string channel_id"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "channel_id must be a string or None.",
            part="snippet",
            channel_id=123
        )

    def test_insert_channel_id_empty_string(self):
        """Test insert with empty string channel_id"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "channel_id cannot be an empty string.",
            part="snippet",
            channel_id="   "
        )

    @patch("youtube.Channels.DB")
    def test_insert_channel_id_already_exists(self, mock_db):
        """Test insert with channel_id that already exists"""
        mock_db.get.return_value = self.mock_db["channels"]
        self.assert_error_behavior(
            insert,
            ValueError,
            "channel_id already exists in the database.",
            part="snippet",
            channel_id="channel1"
        )

    # Test managed_by_me parameter validation
    def test_insert_managed_by_me_not_bool(self):
        """Test insert with non-boolean managed_by_me"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "managed_by_me must be a boolean or None.",
            part="snippet",
            managed_by_me="true"
        )

    # Test max_results parameter validation
    def test_insert_max_results_not_int(self):
        """Test insert with non-integer max_results"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "max_results must be an integer or None.",
            part="snippet",
            max_results="10"
        )

    def test_insert_max_results_negative(self):
        """Test insert with negative max_results"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "max_results cannot be negative.",
            part="snippet",
            max_results=-1
        )

    # Test mine parameter validation
    def test_insert_mine_not_bool(self):
        """Test insert with non-boolean mine"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "mine must be a boolean or None.",
            part="snippet",
            mine="true"
        )

    # Test my_subscribers parameter validation
    def test_insert_my_subscribers_not_bool(self):
        """Test insert with non-boolean my_subscribers"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "my_subscribers must be a boolean or None.",
            part="snippet",
            my_subscribers="true"
        )

    # Test on_behalf_of_content_owner parameter validation
    def test_insert_on_behalf_of_content_owner_not_string(self):
        """Test insert with non-string on_behalf_of_content_owner"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "on_behalf_of_content_owner must be a string or None.",
            part="snippet",
            on_behalf_of_content_owner=123
        )

    def test_insert_on_behalf_of_content_owner_empty_string(self):
        """Test insert with empty string on_behalf_of_content_owner"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "on_behalf_of_content_owner cannot be an empty string.",
            part="snippet",
            on_behalf_of_content_owner="   "
        )

    # Test valid cases
    @patch("youtube.Channels.DB")
    @patch("youtube.Channels.generate_entity_id")
    def test_insert_valid_minimal(self, mock_generate_id, mock_db):
        """Test insert with valid minimal parameters"""
        mock_generate_id.return_value = "channel2"
        mock_db.get.return_value = {}
        mock_db.setdefault.return_value = {}

        result = insert(part="snippet")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["channel"]["id"], "channel2")
        mock_db.setdefault.assert_called_once_with("channels", {})

    @patch("youtube.Channels.DB")
    def test_insert_valid_all_parameters(self, mock_db):
        """Test insert with all valid parameters"""
        mock_db.get.side_effect = lambda key, default: {
            "videoCategories": self.mock_db["videoCategories"],
            "channels": {}
        }.get(key, default)
        mock_db.setdefault.return_value = {}

        result = insert(
            part="snippet,statistics",
            category_id="1",
            for_username="test_user",
            hl="en",
            channel_id="channel3",
            managed_by_me=True,
            max_results=25,
            mine=False,
            my_subscribers=True,
            on_behalf_of_content_owner="owner123"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["channel"]["id"], "channel3")
        self.assertEqual(result["channel"]["categoryId"], "1")
        self.assertEqual(result["channel"]["forUsername"], "test_user")
        self.assertEqual(result["channel"]["hl"], "en")
        self.assertEqual(result["channel"]["managedByMe"], True)
        self.assertEqual(result["channel"]["maxResults"], 25)
        self.assertEqual(result["channel"]["mine"], False)
        self.assertEqual(result["channel"]["mySubscribers"], True)
        self.assertEqual(result["channel"]["onBehalfOfContentOwner"], "owner123")

    @patch("youtube.Channels.DB")
    def test_insert_valid_multiple_parts(self, mock_db):
        """Test insert with multiple valid part values"""
        mock_db.get.return_value = {}
        mock_db.setdefault.return_value = {}

        result = insert(part="snippet,statistics,contentDetails")
        self.assertTrue(result["success"])

    @patch("youtube.Channels.DB")
    def test_insert_valid_all_hl_values(self, mock_db):
        """Test insert with all valid hl values"""
        mock_db.get.return_value = {}
        mock_db.setdefault.return_value = {}

        valid_hl_values = [
            "af", "az", "id", "ms", "bs", "ca", "cs", "da", "de", "et",
            "en-IN", "en-GB", "en", "es", "es-419", "es-US", "eu", "fil",
            "fr", "fr-CA", "gl", "hr", "zu", "is", "it", "sw", "lv", "lt",
            "hu", "nl", "no", "uz", "pl", "pt-PT", "pt", "ro", "sq", "sk",
            "sl", "sr-Latn", "fi", "sv", "vi", "tr", "be", "bg", "ky", "kk",
            "mk", "mn", "ru", "sr", "uk", "el", "hy", "iw", "ur", "ar", "fa",
            "ne", "mr", "hi", "as", "bn", "pa", "gu", "or", "ta", "te", "kn",
            "ml", "si", "th", "lo", "my", "ka", "am", "km"
        ]
        for hl_value in valid_hl_values:
            with self.subTest(hl=hl_value):
                result = insert("snippet", hl=hl_value)
                self.assertTrue(result["success"])
                self.assertEqual(result["channel"]["hl"], hl_value)

    @patch("youtube.Channels.DB")
    def test_insert_max_results_zero(self, mock_db):
        """Test insert with max_results = 0"""
        mock_db.get.return_value = {}
        mock_db.setdefault.return_value = {}

        result = insert("snippet", max_results=0)
        self.assertTrue(result["success"])
        self.assertEqual(result["channel"]["maxResults"], 0)


class TestChannelsUpdate(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        self.mock_db = {
            "channels": {
                "channel1": {
                    "id": "channel1",
                    "categoryId": "1",
                    "forUsername": "existing_user",
                    "hl": "en",
                    "managedByMe": True,
                    "maxResults": 10,
                    "mine": True,
                    "mySubscribers": False,
                    "onBehalfOfContentOwner": "content_owner"
                }
            },
            "videoCategories": {
                "category1": {
                    "id": "1",
                    "snippet": {
                        "title": "Film & Animation",
                        "regionCode": "US"
                    }
                },
                "category2": {
                    "id": "2",
                    "snippet": {
                        "title": "Autos & Vehicles",
                        "regionCode": "US"
                    }
                },
                "category3": {
                    "id": "10",
                    "snippet": {
                        "title": "Music",
                        "regionCode": "CA"
                    }
                }
            }
        }

    # Test channel_id parameter validation
    def test_update_channel_id_not_string(self):
        """Test update with non-string channel_id"""
        self.assert_error_behavior(
            update,
            TypeError,
            "channel_id must be a string",
            channel_id=123,
            properties={"categoryId": "1"}
        )

    def test_update_channel_id_empty_string(self):
        """Test update with empty string channel_id"""
        self.assert_error_behavior(
            update,
            ValueError,
            "channel_id cannot be an empty string",
            channel_id="   ",
            properties={"categoryId": "1"}
        )

    @patch("youtube.Channels.DB")
    def test_update_channel_id_not_found(self, mock_db):
        """Test update with channel_id not in database"""
        mock_db.get.return_value = {}
        self.assert_error_behavior(
            update,
            ValueError,
            "Channel ID: nonexistent_channel not found in the database.",
            channel_id="nonexistent_channel",
            properties={"categoryId": "1"}
        )

    @patch("youtube.Channels.DB")
    def test_update_no_parameters(self, mock_db):
        """Test update with no update parameters"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "No update parameters provided",
            channel_id="channel1",
            properties={}
        )

    @patch("youtube.Channels.DB")
    def test_update_none_properties(self, mock_db):
        """Test update with None properties"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "No update parameters provided",
            channel_id="channel1",
            properties=None
        )

    @patch("youtube.Channels.DB")
    def test_update_empty_properties_dict(self, mock_db):
        """Test update with empty properties dictionary"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "No update parameters provided",
            channel_id="channel1",
            properties={}
        )

    @patch("youtube.Channels.DB")
    def test_update_properties_not_dict(self, mock_db):
        """Test update with non-dictionary properties"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(TypeError) as context:
            update(channel_id="channel1", properties="not_a_dict")


    @patch("youtube.Channels.DB")
    def test_update_extra_fields_forbidden(self, mock_db):
        """Test update with extra fields not defined in the model"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"invalidField": "value"})

    # Test categoryId parameter validation
    @patch("youtube.Channels.DB")
    def test_update_category_id_not_string(self, mock_db):
        """Test update with non-string categoryId"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"categoryId": 123})

    @patch("youtube.Channels.DB")
    def test_update_category_id_empty_string(self, mock_db):
        """Test update with empty string categoryId"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "categoryId cannot be an empty string.",
            channel_id="channel1",
            properties={"categoryId": "   "}
        )

    @patch("youtube.Channels.DB")
    def test_update_category_id_not_in_database(self, mock_db):
        """Test update with categoryId not in database"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        
        self.assert_error_behavior(
            update,
            ValueError,
            "Invalid categoryId, category not found in the database.",
            channel_id="channel1",
            properties={"categoryId": "999"}
        )

    # Test forUsername parameter validation
    @patch("youtube.Channels.DB")
    def test_update_for_username_not_string(self, mock_db):
        """Test update with non-string forUsername"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"forUsername": 123})

    @patch("youtube.Channels.DB")
    def test_update_for_username_empty_string(self, mock_db):
        """Test update with empty string forUsername"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "forUsername cannot be an empty string.",
            channel_id="channel1",
            properties={"forUsername": "   "}
        )

    # Test hl parameter validation
    @patch("youtube.Channels.DB")
    def test_update_hl_not_string(self, mock_db):
        """Test update with non-string hl"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"hl": 123})

    @patch("youtube.Channels.DB")
    def test_update_hl_empty_string(self, mock_db):
        """Test update with empty string hl"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "hl cannot be an empty string.",
            channel_id="channel1",
            properties={"hl": "   "}
        )

    @patch("youtube.Channels.DB")
    def test_update_hl_invalid_value(self, mock_db):
        """Test update with invalid hl value"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "Invalid hl value, must be one of: af, az, id, ms, bs, ca, cs, da, de, et, en-IN, en-GB, en, es, es-419, es-US, eu, fil, fr, fr-CA, gl, hr, zu, is, it, sw, lv, lt, hu, nl, no, uz, pl, pt-PT, pt, ro, sq, sk, sl, sr-Latn, fi, sv, vi, tr, be, bg, ky, kk, mk, mn, ru, sr, uk, el, hy, iw, ur, ar, fa, ne, mr, hi, as, bn, pa, gu, or, ta, te, kn, ml, si, th, lo, my, ka, am, km",
            channel_id="channel1",
            properties={"hl": "invalid"}
        )

    # Test managedByMe parameter validation
    @patch("youtube.Channels.DB")
    def test_update_managed_by_me_not_bool(self, mock_db):
        """Test update with non-boolean managedByMe"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"managedByMe": "123"})

    # Test maxResults parameter validation
    @patch("youtube.Channels.DB")
    def test_update_max_results_not_int(self, mock_db):
        """Test update with non-integer maxResults"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"maxResults": "abc"})

    @patch("youtube.Channels.DB")
    def test_update_max_results_negative(self, mock_db):
        """Test update with negative maxResults"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "maxResults cannot be negative.",
            channel_id="channel1",
            properties={"maxResults": -1}
        )

    # Test mine parameter validation
    @patch("youtube.Channels.DB")
    def test_update_mine_not_bool(self, mock_db):
        """Test update with non-boolean mine"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"mine": "123"})

    # Test mySubscribers parameter validation
    @patch("youtube.Channels.DB")
    def test_update_my_subscribers_not_bool(self, mock_db):
        """Test update with non-boolean mySubscribers"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"mySubscribers": "123"})

    # Test onBehalfOfContentOwner parameter validation
    @patch("youtube.Channels.DB")
    def test_update_on_behalf_of_content_owner_not_string(self, mock_db):
        """Test update with non-string onBehalfOfContentOwner"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(channel_id="channel1", properties={"onBehalfOfContentOwner": 123})

    @patch("youtube.Channels.DB")
    def test_update_on_behalf_of_content_owner_empty_string(self, mock_db):
        """Test update with empty string onBehalfOfContentOwner"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "onBehalfOfContentOwner cannot be an empty string.",
            channel_id="channel1",
            properties={"onBehalfOfContentOwner": "   "}
        )

    # Test valid cases
    @patch("youtube.Channels.DB")
    def test_update_valid_single_parameter(self, mock_db):
        """Test update with single valid parameter"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)

        result = update(channel_id="channel1", properties={"categoryId": "2"})
        
        self.assertTrue(result["success"])
        self.assertEqual(result["channel"]["id"], "channel1")

    @patch("youtube.Channels.DB")
    def test_update_valid_multiple_parameters(self, mock_db):
        """Test update with multiple valid parameters"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)

        result = update(channel_id="channel1", properties={
            "categoryId": "2",
            "forUsername": "updated_user",
            "hl": "fr",
            "managedByMe": False,
            "maxResults": 20,
            "mine": False,
            "mySubscribers": True,
            "onBehalfOfContentOwner": "new_owner"
        })
        
        self.assertTrue(result["success"])
        self.assertEqual(result["channel"]["id"], "channel1")


    @patch("youtube.Channels.DB")
    def test_update_max_results_zero(self, mock_db):
        """Test update with maxResults = 0"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)

        result = update("channel1", {"maxResults": 0})
        self.assertTrue(result["success"])

    @patch("youtube.Channels.DB")
    def test_update_boolean_values(self, mock_db):
        """Test update with all boolean parameter combinations"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)

        boolean_combinations = [
            (True, True, True),
            (True, True, False),
            (True, False, True),
            (True, False, False),
            (False, True, True),
            (False, True, False),
            (False, False, True),
            (False, False, False)
        ]

        for managed_by_me, mine, my_subscribers in boolean_combinations:
            with self.subTest(managed_by_me=managed_by_me, mine=mine, my_subscribers=my_subscribers):
                result = update("channel1", {
                    "managedByMe": managed_by_me,
                    "mine": mine,
                    "mySubscribers": my_subscribers
                })
                self.assertTrue(result["success"])


    @patch("youtube.Channels.DB")
    def test_update_validation_order(self, mock_db):
        """Test that Pydantic validation happens before business logic validation"""
        mock_db.get.side_effect = lambda key, default: {
            "channels": self.mock_db["channels"],
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)
        
        # Test type validation (Pydantic) happens first
        with self.assertRaises(ValidationError):
            update(channel_id="channel1", properties={"categoryId": 123})
        
        # Test business logic validation (ValueError) happens after type validation passes
        with self.assertRaises(ValueError):
            update(channel_id="channel1", properties={"categoryId": "   "})

    @patch("youtube.Channels.DB") 
    def test_update_database_modification(self, mock_db):
        """Test that the database is correctly modified"""
        # Create a copy of the mock data that can be modified
        channels_copy = self.mock_db["channels"].copy()
        mock_db.get.side_effect = lambda key, default: {
            "channels": channels_copy,
            "videoCategories": self.mock_db["videoCategories"]
        }.get(key, default)

        original_channel = channels_copy["channel1"].copy()
        
        result = update("channel1", {
            "categoryId": "2",
            "forUsername": "new_user", 
            "hl": "fr"
        })
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["channel"]["id"], "channel1")
        self.assertEqual(result["channel"]["categoryId"], "2")
        self.assertEqual(result["channel"]["forUsername"], "new_user")
        self.assertEqual(result["channel"]["hl"], "fr")
        
        # Verify unchanged fields remain the same
        self.assertEqual(result["channel"]["managedByMe"], original_channel["managedByMe"])
        self.assertEqual(result["channel"]["mine"], original_channel["mine"])


if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
