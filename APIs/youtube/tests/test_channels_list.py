import unittest
from unittest.mock import patch, MagicMock
from youtube.Channels import list as list_channels
from youtube.SimulationEngine.custom_errors import MaxResultsOutOfRangeError
from common_utils.base_case import BaseTestCaseWithErrorHandler



class TestChannelsList(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self.mock_db = {
            "channels": {
                "channel1": {
                    "id": "channel1",
                    "categoryId": "cat1",
                    "forUsername": "user1",
                    "hl": "en",
                },
                "channel2": {
                    "id": "channel2",
                    "categoryId": "cat2",
                    "forUsername": "user2",
                    "hl": "fr",
                },
                "channel3": {
                    "id": "channel3",
                    "categoryId": "cat1",
                    "forUsername": "user3",
                    "hl": "en",
                },
            }
        }

    @patch("youtube.Channels.DB")
    def test_list_all_channels(self, mock_db_class):
        mock_db_instance = MagicMock()
        mock_db_instance.get.return_value = self.mock_db["channels"]
        mock_db_class.get.return_value = self.mock_db["channels"]

        result = list_channels()
        self.assertEqual(len(result["items"]), 3)

    @patch("youtube.Channels.DB")
    def test_list_filter_by_category_id(self, mock_db_class):
        mock_db_class.get.return_value = self.mock_db["channels"]
        result = list_channels(category_id="cat1")
        self.assertEqual(len(result["items"]), 2)
        self.assertTrue(all(item["categoryId"] == "cat1" for item in result["items"]))

    @patch("youtube.Channels.DB")
    def test_list_filter_by_channel_id(self, mock_db_class):
        mock_db_class.get.return_value = self.mock_db["channels"]
        result = list_channels(channel_id="channel1,channel3")
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["id"], "channel1")
        self.assertEqual(result["items"][1]["id"], "channel3")

    @patch("youtube.Channels.DB")
    def test_list_with_max_results(self, mock_db_class):
        mock_db_class.get.return_value = self.mock_db["channels"]
        result = list_channels(max_results=2)
        self.assertEqual(len(result["items"]), 2)

    def test_list_max_results_out_of_range(self):
        with self.assertRaises(MaxResultsOutOfRangeError):
            list_channels(max_results=0)
        with self.assertRaises(MaxResultsOutOfRangeError):
            list_channels(max_results=51)

    def test_list_invalid_parameter_type(self):
        with self.assertRaises(TypeError):
            list_channels(category_id=123)
        with self.assertRaises(TypeError):
            list_channels(for_username=123)
        with self.assertRaises(TypeError):
            list_channels(max_results="abc")

    def test_list_empty_string_parameter(self):
        with self.assertRaises(ValueError):
            list_channels(category_id=" ")
        with self.assertRaises(ValueError):
            list_channels(channel_id=" ")


if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
