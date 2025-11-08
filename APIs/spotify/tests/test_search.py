import unittest
from typing import Optional, List
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import InvalidInputError
from .. import search_for_item

class TestSpotifySearchAPI(unittest.TestCase):
    def setUp(self):
        DB.clear()
        DB.update({
            "tracks": {
                "track_1": {
                    "id": "track_1",
                    "name": "Test Track",
                    "artists": [{"id": "artist_1", "name": "Test Artist"}],
                    "album": {"id": "album_1", "name": "Test Album"},
                    "duration_ms": 180000,
                    "explicit": False,
                    "track_number": 1,
                    "disc_number": 1,
                    "available_markets": ["US", "CA"],
                    "popularity": 60
                },
                "track_2": {
                    "id": "track_2",
                    "name": "Another Track",
                    "artists": [{"id": "artist_2", "name": "Another Artist"}],
                    "album": {"id": "album_2", "name": "Another Album"},
                    "duration_ms": 200000,
                    "explicit": False,
                    "track_number": 2,
                    "disc_number": 1,
                    "available_markets": ["CA"],
                    "popularity": 50
                }
            },
            "artists": {
                "artist_1": {
                    "id": "artist_1",
                    "name": "Test Artist",
                    "genres": ["pop"],
                    "popularity": 70,
                    "images": [],
                    "followers": {"total": 1000}
                },
                "artist_2": {
                    "id": "artist_2",
                    "name": "Another Artist",
                    "genres": ["rock"],
                    "popularity": 50,
                    "images": [],
                    "followers": {"total": 500}
                }
            },
            "albums": {
                "album_1": {
                    "id": "album_1",
                    "name": "Test Album",
                    "artists": [{"id": "artist_1", "name": "Test Artist"}],
                    "album_type": "album",
                    "total_tracks": 10,
                    "available_markets": ["US", "CA"],
                    "release_date": "2023-01-01",
                    "release_date_precision": "day",
                    "images": [],
                    "popularity": 50
                },
                "album_2": {
                    "id": "album_2",
                    "name": "Another Album",
                    "artists": [{"id": "artist_2", "name": "Another Artist"}],
                    "album_type": "album",
                    "total_tracks": 8,
                    "available_markets": ["CA"],
                    "release_date": "2023-02-01",
                    "release_date_precision": "day",
                    "images": [],
                    "popularity": 40
                }
            },
            "playlists": {
                "playlist_1": {
                    "id": "playlist_1",
                    "name": "Test Playlist",
                    "owner": {"id": "user_1", "display_name": "Test User"},
                    "public": True,
                    "collaborative": False,
                    "description": "A test playlist",
                    "images": [],
                    "tracks": {"total": 5},
                    "followers": {"total": 100}
                }
            },
            "shows": {
                "show_1": {
                    "id": "show_1",
                    "name": "Test Show",
                    "available_markets": ["US", "CA"],
                    "publisher": "Test Publisher",
                    "images": [],
                    "total_episodes": 10
                }
            },
            "episodes": {
                "episode_1": {
                    "id": "episode_1",
                    "name": "Test Episode",
                    "show": {"id": "show_1", "name": "Test Show"},
                    "available_markets": ["US", "CA"],
                    "duration_ms": 3600000,
                    "release_date": "2023-01-01",
                    "images": []
                }
            },
            "audiobooks": {
                "audiobook_1": {
                    "id": "audiobook_1",
                    "name": "Test Audiobook",
                    "available_markets": ["US", "CA"],
                    "authors": ["Test Author"],
                    "images": []
                }
            },
            "current_user": {
                "id": "smuqPNFPXrJKcEt943KrY8"
            }
        })

    def test_search_tracks(self):
        result = search_for_item("Test", "track")
        self.assertIn("tracks", result)
        self.assertGreaterEqual(result["tracks"]["total"], 1)
        self.assertTrue(any("Test Track" in t["name"] for t in result["tracks"]["items"]))

    def test_search_artists(self):
        result = search_for_item("Test", "artist")
        self.assertIn("artists", result)
        self.assertGreaterEqual(result["artists"]["total"], 1)
        self.assertTrue(any("Test Artist" in a["name"] for a in result["artists"]["items"]))

    def test_search_albums(self):
        result = search_for_item("Test", "album")
        self.assertIn("albums", result)
        self.assertGreaterEqual(result["albums"]["total"], 1)
        self.assertTrue(any("Test Album" in a["name"] for a in result["albums"]["items"]))

    def test_search_playlists(self):
        result = search_for_item("Test", "playlist")
        self.assertIn("playlists", result)
        self.assertGreaterEqual(result["playlists"]["total"], 1)
        self.assertTrue(any("Test Playlist" in p["name"] for p in result["playlists"]["items"]))

    def test_search_shows(self):
        result = search_for_item("Test", "show")
        self.assertIn("shows", result)
        self.assertGreaterEqual(result["shows"]["total"], 1)
        self.assertTrue(any("Test Show" in s["name"] for s in result["shows"]["items"]))

    def test_search_episodes(self):
        result = search_for_item("Test", "episode")
        self.assertIn("episodes", result)
        self.assertGreaterEqual(result["episodes"]["total"], 1)
        self.assertTrue(any("Test Episode" in e["name"] for e in result["episodes"]["items"]))

    def test_search_audiobooks(self):
        result = search_for_item("Test", "audiobook")
        self.assertIn("audiobooks", result)
        self.assertGreaterEqual(result["audiobooks"]["total"], 1)
        self.assertTrue(any("Test Audiobook" in a["name"] for a in result["audiobooks"]["items"]))

    def test_search_with_market_filtering(self):
        result = search_for_item("Another", "track", market="CA")
        self.assertIn("tracks", result)
        self.assertTrue(any(t["id"] == "track_2" for t in result["tracks"]["items"]))
        # Should not return for US market
        result_us = search_for_item("Another", "track", market="US")
        self.assertEqual(result_us["tracks"]["total"], 0)

    def test_search_pagination(self):
        # Add more tracks for pagination
        for i in range(30):
            DB["tracks"][f"track_extra_{i}"] = {
                "id": f"track_extra_{i}",
                "name": f"Test Track Extra {i}",
                "artists": [{"id": "artist_1", "name": "Test Artist"}],
                "album": {"id": "album_1", "name": "Test Album"},
                "duration_ms": 180000,
                "explicit": False,
                "track_number": 1,
                "disc_number": 1,
                "available_markets": ["US", "CA"],
                "popularity": 60
            }
        result = search_for_item("Test Track Extra", "track", limit=10, offset=10)
        self.assertIn("tracks", result)
        self.assertEqual(result["tracks"]["limit"], 10)
        self.assertEqual(result["tracks"]["offset"], 10)
        self.assertEqual(len(result["tracks"]["items"]), 10)

    def test_search_invalid_type(self):
        with self.assertRaises(InvalidInputError):
            search_for_item("Test", "invalidtype")

    def test_search_invalid_limit(self):
        with self.assertRaises(InvalidInputError):
            search_for_item("Test", "track", limit=0)
        with self.assertRaises(InvalidInputError):
            search_for_item("Test", "track", limit=100)

    def test_search_invalid_offset(self):
        with self.assertRaises(InvalidInputError):
            search_for_item("Test", "track", offset=-1)

    def test_search_invalid_market(self):
        with self.assertRaises(InvalidInputError):
            search_for_item("Test", "track", market="INVALID")

    def test_search_invalid_include_external(self):
        with self.assertRaises(InvalidInputError):
            search_for_item("Test", "track", include_external="video")

    def test_search_empty_query(self):
        with self.assertRaises(InvalidInputError):
            search_for_item("", "track")

    def test_search_non_string_query(self):
        with self.assertRaises(InvalidInputError):
            search_for_item(123, "track")

    def test_search_non_string_type(self):
        with self.assertRaises(InvalidInputError):
            search_for_item("Test", 123) 