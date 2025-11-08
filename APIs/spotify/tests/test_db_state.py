import unittest
import os


from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, load_state, save_state, DEFAULT_DB_PATH
from ..SimulationEngine import utils
import json

class TestDBStateManagement(BaseTestCaseWithErrorHandler):
    """Test the load_state and save_state functions of the spotify DB."""

    def setUp(self):
        """Set up test environment."""
        DB.clear()
        # Initialize with some basic test data

        # Save the original DB state to restore after tests
        self.original_db = DB.copy()

        load_state(DEFAULT_DB_PATH)
        self.DB = DB.copy()
        self.temp_db_file = DEFAULT_DB_PATH + ".temp"

        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
        else:
            temp_db = {
                    "artists": [],
                    "albums": [],
                    "tracks": [],
                    "playlists": [],
                    "users": [],
                    "categories": [],
                    "shows": [],
                    "episodes": [],
                    "audiobooks": [],
                    "chapters": [],
                    "devices": [],
                    "playback_states": [],
                    "currently_playing": [],
                    "user_settings": [],
                    "user_explicit_content_settings": [],
                    "top_artists": [],
                    "top_tracks": [],
                    "enhanced_playlist_tracks": [],
                    "enhanced_devices": [],
                    "enhanced_playback_states": [],
                    "enhanced_currently_playing": [],
                    "user_settings": [],
                    "user_explicit_content_settings": [],
                    "top_artists": [],
                    "top_tracks": [],
                    "enhanced_playlist_tracks": [],
                    "enhanced_devices": [],
                    "enhanced_playback_states": [],
                    "enhanced_currently_playing": [],
                    "user_settings": [],
                    "user_explicit_content_settings": [],
                    "top_artists": [],
                    "top_tracks": [],
                    "enhanced_playlist_tracks": [],
                    "enhanced_devices": [],
                    "enhanced_playback_states": [],
                    "enhanced_currently_playing": [],
                    "user_settings": [],
                    "user_explicit_content_settings": [],
                    "top_artists": [],
                    "top_tracks": [],
                    "enhanced_playlist_tracks": [],
                    "enhanced_devices": [],
                    "enhanced_playback_states": [],
                    "enhanced_currently_playing": [],
            }
            with open(self.temp_db_file, 'w') as f:
                json.dump(temp_db, f)  


    def tearDown(self):
        super().tearDown()
        DB.clear()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)

    def test_load_db_from_file(self):
        """
        Test that the database can be loaded from a file.
        """
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['artists']), 0)
        self.assertEqual(len(DB['albums']), 0)
        self.assertEqual(len(DB['tracks']), 0)
        self.assertEqual(len(DB['playlists']), 0)
        self.assertEqual(len(DB['users']), 0)
        self.assertEqual(len(DB['categories']), 0)
        self.assertEqual(len(DB['shows']), 0)
        self.assertEqual(len(DB['episodes']), 0)

    def test_save_db_to_file(self):
        """
        Test that the database can be saved to a file.
        """
        load_state(self.temp_db_file)
        DB["artists"] = [
            {
                "id": "123",
                "name": "Artist 1",
                "type": "artist",
                "uri": "spotify:artist:123",
                "href": "https://api.spotify.com/v1/artists/123",
                "external_urls": {
                    "spotify": "https://open.spotify.com/artist/123"
                },
                "genres": ["rock", "pop"],
                "popularity": 50,
                "images": [
                    {
                        "url": "https://via.placeholder.com/150",
                        "height": 150,
                        "width": 150
                    }
                ],
                "followers": {
                    "href": None,
                    "total": 1000
                }
            }
        ]
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['artists']), 1)
        self.assertEqual(DB['artists'][0]['name'], "Artist 1")
        self.assertEqual(DB['artists'][0]['type'], "artist")
        self.assertEqual(DB['artists'][0]['uri'], "spotify:artist:123")
        self.assertEqual(DB['artists'][0]['href'], "https://api.spotify.com/v1/artists/123")
        self.assertEqual(DB['artists'][0]['external_urls']['spotify'], "https://open.spotify.com/artist/123")
        self.assertEqual(DB['artists'][0]['genres'], ["rock", "pop"])
        self.assertEqual(DB['artists'][0]['popularity'], 50)
    
if __name__ == '__main__':
    unittest.main() 