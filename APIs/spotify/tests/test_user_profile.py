import unittest
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import InvalidInputError, NoResultsFoundError, AuthenticationError
from .. import get_current_user_profile, get_user_top_artists_and_tracks, get_user_profile

class TestSpotifyUserProfileAPI(unittest.TestCase):
    def setUp(self):
        DB.clear()
        DB.update({
            "users": {
                "smuqPNFPXrJKcEt943KrY8": {
                    "id": "smuqPNFPXrJKcEt943KrY8",
                    "display_name": "Test User",
                    "external_urls": {"spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"},
                    "followers": {"total": 50},
                    "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
                    "images": [],
                    "type": "user",
                    "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8",
                    "country": "US",
                    "email": "test@example.com",
                    "product": "premium"
                },
                "SLvTb0e3Rp3oLJ8YXl0dC5": {
                    "id": "SLvTb0e3Rp3oLJ8YXl0dC5",
                    "display_name": "Another User",
                    "external_urls": {"spotify": "https://open.spotify.com/user/SLvTb0e3Rp3oLJ8YXl0dC5"},
                    "followers": {"total": 10},
                    "href": "https://api.spotify.com/v1/users/SLvTb0e3Rp3oLJ8YXl0dC5",
                    "images": [],
                    "type": "user",
                    "uri": "spotify:user:SLvTb0e3Rp3oLJ8YXl0dC5"
                }
            },
            "top_artists": {
                "smuqPNFPXrJKcEt943KrY8": {
                    "artists": [
                        {"id": "artist_1", "name": "Test Artist", "type": "artist", "uri": "spotify:artist:1", "href": "https://api.spotify.com/v1/artists/1", "external_urls": {"spotify": "https://open.spotify.com/artist/1"}, "images": [], "followers": {"total": 1000}, "genres": ["pop"], "popularity": 70}
                    ]
                }
            },
            "top_tracks": {
                "smuqPNFPXrJKcEt943KrY8": {
                    "tracks": [
                        {"id": "track_1", "name": "Test Track", "type": "track", "uri": "spotify:track:1", "href": "https://api.spotify.com/v1/tracks/1", "external_urls": {"spotify": "https://open.spotify.com/track/1"}, "artists": [{"id": "artist_1", "name": "Test Artist"}], "album": {"id": "album_1", "name": "Test Album"}, "duration_ms": 180000, "explicit": False, "popularity": 60}
                    ]
                }
            },
            "current_user": {
                "id": "smuqPNFPXrJKcEt943KrY8"
            }
        })

    def test_get_current_user_profile_success(self):
        result = get_current_user_profile()
        self.assertEqual(result["id"], "smuqPNFPXrJKcEt943KrY8")
        self.assertEqual(result["display_name"], "Test User")

    def test_get_current_user_profile_not_authenticated(self):
        DB["users"].pop("smuqPNFPXrJKcEt943KrY8")
        with self.assertRaises(AuthenticationError):
            get_current_user_profile()

    def test_get_user_profile_success(self):
        result = get_user_profile("SLvTb0e3Rp3oLJ8YXl0dC5")
        self.assertEqual(result["id"], "SLvTb0e3Rp3oLJ8YXl0dC5")
        self.assertEqual(result["display_name"], "Another User")

    def test_get_user_profile_invalid_input(self):
        with self.assertRaises(InvalidInputError):
            get_user_profile(123)
        with self.assertRaises(InvalidInputError):
            get_user_profile("")

    def test_get_user_profile_not_found(self):
        with self.assertRaises(NoResultsFoundError):
            get_user_profile("nonexistent_user")

    def test_get_user_top_artists_success(self):
        result = get_user_top_artists_and_tracks("artists")
        self.assertIn("items", result)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], "artist_1")

    def test_get_user_top_tracks_success(self):
        result = get_user_top_artists_and_tracks("tracks")
        self.assertIn("items", result)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], "track_1")

    def test_get_user_top_artists_pagination(self):
        # Add more artists for pagination
        DB["top_artists"]["smuqPNFPXrJKcEt943KrY8"]["artists"] += [
            {"id": f"artist_{i}", "name": f"Artist {i}", "type": "artist", "uri": f"spotify:artist:{i}", "href": f"https://api.spotify.com/v1/artists/{i}", "external_urls": {"spotify": f"https://open.spotify.com/artist/{i}"}, "images": [], "followers": {"total": 100}, "genres": ["pop"], "popularity": 50} for i in range(2, 22)
        ]
        result = get_user_top_artists_and_tracks("artists", limit=10, offset=10)
        self.assertEqual(result["limit"], 10)
        self.assertEqual(result["offset"], 10)
        self.assertEqual(len(result["items"]), 10)

    def test_get_user_top_tracks_pagination(self):
        # Add more tracks for pagination
        DB["top_tracks"]["smuqPNFPXrJKcEt943KrY8"]["tracks"] += [
            {"id": f"track_{i}", "name": f"Track {i}", "type": "track", "uri": f"spotify:track:{i}", "href": f"https://api.spotify.com/v1/tracks/{i}", "external_urls": {"spotify": f"https://open.spotify.com/track/{i}"}, "artists": [{"id": "artist_1", "name": "Test Artist"}], "album": {"id": "album_1", "name": "Test Album"}, "duration_ms": 180000, "explicit": False, "popularity": 60} for i in range(2, 22)
        ]
        result = get_user_top_artists_and_tracks("tracks", limit=10, offset=10)
        self.assertEqual(result["limit"], 10)
        self.assertEqual(result["offset"], 10)
        self.assertEqual(len(result["items"]), 10)

    def test_get_user_top_artists_invalid_type(self):
        with self.assertRaises(InvalidInputError):
            get_user_top_artists_and_tracks("invalidtype")

    def test_get_user_top_artists_invalid_limit(self):
        with self.assertRaises(InvalidInputError):
            get_user_top_artists_and_tracks("artists", limit=0)
        with self.assertRaises(InvalidInputError):
            get_user_top_artists_and_tracks("artists", limit=100)

    def test_get_user_top_artists_invalid_offset(self):
        with self.assertRaises(InvalidInputError):
            get_user_top_artists_and_tracks("artists", offset=-1)

    def test_get_user_top_artists_invalid_time_range(self):
        with self.assertRaises(InvalidInputError):
            get_user_top_artists_and_tracks("artists", time_range="invalid")

    def test_get_user_top_artists_no_results(self):
        DB["top_artists"]["smuqPNFPXrJKcEt943KrY8"]["artists"] = []
        result = get_user_top_artists_and_tracks("artists")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["total"], 0)

    def test_get_user_top_tracks_no_results(self):
        DB["top_tracks"]["smuqPNFPXrJKcEt943KrY8"]["tracks"] = []
        result = get_user_top_artists_and_tracks("tracks")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["total"], 0) 