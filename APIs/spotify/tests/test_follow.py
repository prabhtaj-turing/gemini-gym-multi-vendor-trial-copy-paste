from datetime import datetime

from ..SimulationEngine.db import DB, save_state, load_state
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    InvalidInputError,
    NoResultsFoundError
)

# Import the follow functions
from ..follow import (
    follow_playlist,
    unfollow_playlist,
    follow_artists_or_users,
    unfollow_artists_or_users,
    check_user_follows_artists_or_users
)


class TestFollowPlaylistFunctions(BaseTestCaseWithErrorHandler):
    """Test cases for follow_playlist and unfollow_playlist functions."""

    def setUp(self):
        """Set up test environment before each test."""
        DB.clear()

        # Initialize with test data
        DB.update({
            "playlists": {
                "playlist_1": {
                    "id": "playlist_1",
                    "name": "Test Playlist 1",
                    "owner": {"id": "user_123", "display_name": "Test User"},
                    "public": True,
                    "collaborative": False,
                    "description": "A test playlist",
                    "images": [],
                    "tracks": {"total": 5},
                    "followers": {"total": 100}
                },
                "playlist_2": {
                    "id": "playlist_2",
                    "name": "Test Playlist 2",
                    "owner": {"id": "user_456", "display_name": "Another User"},
                    "public": False,
                    "collaborative": True,
                    "description": "Another test playlist",
                    "images": [],
                    "tracks": {"total": 10},
                    "followers": {"total": 50}
                },
                "37i9dQZF1DXcBWIGoYBM5M": {
                    "id": "37i9dQZF1DXcBWIGoYBM5M",
                    "name": "Real Spotify Playlist",
                    "owner": {"id": "spotify", "display_name": "Spotify"},
                    "public": True,
                    "collaborative": False,
                    "description": "A real Spotify playlist",
                    "images": [],
                    "tracks": {"total": 20},
                    "followers": {"total": 1000}
                }
            },
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
                }
            },
            "current_user": {
                "id": "smuqPNFPXrJKcEt943KrY8"
            },
            "followed_playlists": {
                "smuqPNFPXrJKcEt943KrY8": {
                    "existing_playlist": {
                        "public": True,
                        "followed_at": "2023-01-01T00:00:00Z"
                    }
                }
            }
        })

    def test_follow_playlist_success_default_public(self):
        """Test successful playlist following with default public=True."""
        result = follow_playlist("playlist_1")

        self.assertIn("message", result)
        self.assertIn("Successfully followed playlist", result["message"])
        self.assertIn("playlist_1", result["message"])

        # Verify playlist was added to followed playlists
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertIn("playlist_1", followed_playlists)
        self.assertTrue(followed_playlists["playlist_1"]["public"])
        self.assertIn("followed_at", followed_playlists["playlist_1"])

    def test_follow_playlist_success_public_true(self):
        """Test successful playlist following with public=True."""
        result = follow_playlist("playlist_1", public=True)

        self.assertIn("message", result)
        self.assertIn("Successfully followed playlist", result["message"])

        # Verify playlist was added with public=True
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertIn("playlist_1", followed_playlists)
        self.assertTrue(followed_playlists["playlist_1"]["public"])

    def test_follow_playlist_success_public_false(self):
        """Test successful playlist following with public=False."""
        result = follow_playlist("playlist_1", public=False)

        self.assertIn("message", result)
        self.assertIn("Successfully followed playlist", result["message"])

        # Verify playlist was added with public=False
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertIn("playlist_1", followed_playlists)
        self.assertFalse(followed_playlists["playlist_1"]["public"])

    def test_follow_playlist_success_real_spotify_id(self):
        """Test successful playlist following with real Spotify playlist ID."""
        result = follow_playlist("37i9dQZF1DXcBWIGoYBM5M")

        self.assertIn("message", result)
        self.assertIn("Successfully followed playlist", result["message"])
        self.assertIn("37i9dQZF1DXcBWIGoYBM5M", result["message"])

    def test_follow_playlist_already_followed(self):
        """Test following a playlist that's already followed (should update metadata)."""
        # First follow
        follow_playlist("playlist_1", public=True)

        # Follow again with different public setting
        result = follow_playlist("playlist_1", public=False)

        self.assertIn("message", result)
        self.assertIn("Successfully followed playlist", result["message"])

        # Verify the public setting was updated
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertIn("playlist_1", followed_playlists)
        self.assertFalse(followed_playlists["playlist_1"]["public"])

    def test_follow_playlist_invalid_playlist_id_empty(self):
        """Test follow_playlist with empty playlist_id."""
        self.assert_error_behavior(
            func_to_call=follow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="playlist_id cannot be empty.",
            playlist_id=""
        )

    def test_follow_playlist_invalid_playlist_id_none(self):
        """Test follow_playlist with None playlist_id."""
        self.assert_error_behavior(
            func_to_call=follow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="playlist_id must be a string.",
            playlist_id=None
        )

    def test_follow_playlist_invalid_playlist_id_not_string(self):
        """Test follow_playlist with non-string playlist_id."""
        self.assert_error_behavior(
            func_to_call=follow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="playlist_id must be a string.",
            playlist_id=123
        )

    def test_follow_playlist_invalid_public_not_boolean(self):
        """Test follow_playlist with non-boolean public parameter."""
        self.assert_error_behavior(
            func_to_call=follow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="public must be a boolean.",
            playlist_id="playlist_1",
            public="true"
        )

    def test_follow_playlist_invalid_public_none(self):
        """Test follow_playlist with None public parameter."""
        self.assert_error_behavior(
            func_to_call=follow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="public must be a boolean.",
            playlist_id="playlist_1",
            public=None
        )

    def test_follow_playlist_playlist_not_found(self):
        """Test follow_playlist with non-existent playlist."""
        self.assert_error_behavior(
            func_to_call=follow_playlist,
            expected_exception_type=NoResultsFoundError,
            expected_message="Playlist with ID 'nonexistent_playlist' not found.",
            playlist_id="nonexistent_playlist"
        )

    def test_unfollow_playlist_success(self):
        """Test successful playlist unfollowing."""
        # First follow the playlist
        follow_playlist("playlist_1")

        # Then unfollow it
        result = unfollow_playlist("playlist_1")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed playlist", result["message"])
        self.assertIn("playlist_1", result["message"])

        # Verify playlist was removed from followed playlists
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertNotIn("playlist_1", followed_playlists)

    def test_unfollow_playlist_success_real_spotify_id(self):
        """Test successful playlist unfollowing with real Spotify playlist ID."""
        # First follow the playlist
        follow_playlist("37i9dQZF1DXcBWIGoYBM5M")

        # Then unfollow it
        result = unfollow_playlist("37i9dQZF1DXcBWIGoYBM5M")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed playlist", result["message"])
        self.assertIn("37i9dQZF1DXcBWIGoYBM5M", result["message"])

    def test_unfollow_playlist_not_followed(self):
        """Test unfollowing a playlist that's not followed (should succeed silently)."""
        result = unfollow_playlist("playlist_1")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed playlist", result["message"])

    def test_unfollow_playlist_invalid_playlist_id_empty(self):
        """Test unfollow_playlist with empty playlist_id."""
        self.assert_error_behavior(
            func_to_call=unfollow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="playlist_id cannot be empty.",
            playlist_id=""
        )

    def test_unfollow_playlist_invalid_playlist_id_none(self):
        """Test unfollow_playlist with None playlist_id."""
        self.assert_error_behavior(
            func_to_call=unfollow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="playlist_id must be a string.",
            playlist_id=None
        )

    def test_unfollow_playlist_invalid_playlist_id_not_string(self):
        """Test unfollow_playlist with non-string playlist_id."""
        self.assert_error_behavior(
            func_to_call=unfollow_playlist,
            expected_exception_type=InvalidInputError,
            expected_message="playlist_id must be a string.",
            playlist_id=123
        )

    def test_unfollow_playlist_playlist_not_found(self):
        """Test unfollow_playlist with non-existent playlist."""
        self.assert_error_behavior(
            func_to_call=unfollow_playlist,
            expected_exception_type=NoResultsFoundError,
            expected_message="Playlist with ID 'nonexistent_playlist' not found.",
            playlist_id="nonexistent_playlist"
        )

    def test_follow_unfollow_cycle(self):
        """Test complete follow/unfollow cycle."""
        # Follow playlist
        follow_result = follow_playlist("playlist_1", public=False)
        self.assertIn("Successfully followed playlist", follow_result["message"])

        # Verify it's in followed playlists
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertIn("playlist_1", followed_playlists)
        self.assertFalse(followed_playlists["playlist_1"]["public"])

        # Unfollow playlist
        unfollow_result = unfollow_playlist("playlist_1")
        self.assertIn("Successfully unfollowed playlist", unfollow_result["message"])

        # Verify it's removed from followed playlists
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertNotIn("playlist_1", followed_playlists)

    def test_follow_playlist_metadata_storage(self):
        """Test that follow metadata is properly stored."""
        # Follow playlist with specific public setting
        follow_playlist("playlist_1", public=False)

        # Check metadata
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        playlist_data = followed_playlists["playlist_1"]

        self.assertFalse(playlist_data["public"])
        self.assertIn("followed_at", playlist_data)

        # Verify timestamp is in ISO format
        try:
            datetime.fromisoformat(playlist_data["followed_at"].replace('Z', '+00:00'))
        except ValueError:
            self.fail("followed_at timestamp is not in valid ISO format")

    def test_follow_playlist_multiple_playlists(self):
        """Test following multiple playlists."""
        # Follow first playlist
        follow_playlist("playlist_1", public=True)

        # Follow second playlist
        follow_playlist("playlist_2", public=False)

        # Verify both are in followed playlists
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertIn("playlist_1", followed_playlists)
        self.assertIn("playlist_2", followed_playlists)
        self.assertTrue(followed_playlists["playlist_1"]["public"])
        self.assertFalse(followed_playlists["playlist_2"]["public"])

    def test_unfollow_playlist_multiple_playlists(self):
        """Test unfollowing multiple playlists."""
        # Follow multiple playlists
        follow_playlist("playlist_1")
        follow_playlist("playlist_2")

        # Unfollow first playlist
        unfollow_playlist("playlist_1")

        # Verify first is removed but second remains
        followed_playlists = DB.get("followed_playlists", {}).get("smuqPNFPXrJKcEt943KrY8", {})
        self.assertNotIn("playlist_1", followed_playlists)
        self.assertIn("playlist_2", followed_playlists)

    def test_follow_playlist_edge_case_very_long_id(self):
        """Test follow_playlist with very long playlist ID."""
        long_id = "a" * 1000
        DB["playlists"][long_id] = {
            "id": long_id,
            "name": "Long ID Playlist",
            "owner": {"id": "user_123", "display_name": "Test User"},
            "public": True,
            "collaborative": False,
            "description": "A playlist with very long ID",
            "images": [],
            "tracks": {"total": 1},
            "followers": {"total": 1}
        }

        result = follow_playlist(long_id)
        self.assertIn("Successfully followed playlist", result["message"])

    def test_follow_playlist_edge_case_special_characters(self):
        """Test follow_playlist with playlist ID containing special characters."""
        special_id = "playlist-with-special-chars_123!@#"
        DB["playlists"][special_id] = {
            "id": special_id,
            "name": "Special Chars Playlist",
            "owner": {"id": "user_123", "display_name": "Test User"},
            "public": True,
            "collaborative": False,
            "description": "A playlist with special characters",
            "images": [],
            "tracks": {"total": 1},
            "followers": {"total": 1}
        }

        result = follow_playlist(special_id)
        self.assertIn("Successfully followed playlist", result["message"])

    def test_follow_playlist_edge_case_unicode_id(self):
        """Test follow_playlist with Unicode playlist ID."""
        unicode_id = "playlist_🎵🎶🎼"
        DB["playlists"][unicode_id] = {
            "id": unicode_id,
            "name": "Unicode Playlist",
            "owner": {"id": "user_123", "display_name": "Test User"},
            "public": True,
            "collaborative": False,
            "description": "A playlist with Unicode characters",
            "images": [],
            "tracks": {"total": 1},
            "followers": {"total": 1}
        }

        result = follow_playlist(unicode_id)
        self.assertIn("Successfully followed playlist", result["message"])


class TestFollowArtists(BaseTestCaseWithErrorHandler):
    """Comprehensive tests for follow_artists and unfollow_artists endpoints."""

    def setUp(self):
        """Set up test environment before each test."""
        DB.clear()
        # Initialize with test data
        DB.update({
            "artists": {
                "W0e71GNltAWtwmOaMZcm1J": {
                    "id": "W0e71GNltAWtwmOaMZcm1J",
                    "name": "Test Artist",
                    "type": "artist",
                    "uri": "spotify:artist:W0e71GNltAWtwmOaMZcm1J",
                    "href": "https://api.spotify.com/v1/artists/W0e71GNltAWtwmOaMZcm1J",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/artist/W0e71GNltAWtwmOaMZcm1J"
                    },
                    "genres": ["pop"],
                    "popularity": 70,
                    "images": [],
                    "followers": {
                        "href": None,
                        "total": 1000
                    }
                },
                "DqJ4SeZM7iQuxSkKOdQvTB": {
                    "id": "DqJ4SeZM7iQuxSkKOdQvTB",
                    "name": "Popular Band",
                    "type": "artist",
                    "uri": "spotify:artist:DqJ4SeZM7iQuxSkKOdQvTB",
                    "href": "https://api.spotify.com/v1/artists/DqJ4SeZM7iQuxSkKOdQvTB",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/artist/DqJ4SeZM7iQuxSkKOdQvTB"
                    },
                    "genres": ["rock", "alternative"],
                    "popularity": 90,
                    "images": [],
                    "followers": {
                        "href": None,
                        "total": 50000
                    }
                },
                "y82ZzcqBIAnXg3vFWFfr12": {
                    "id": "y82ZzcqBIAnXg3vFWFfr12",
                    "name": "Jazz Ensemble",
                    "type": "artist",
                    "uri": "spotify:artist:y82ZzcqBIAnXg3vFWFfr12",
                    "href": "https://api.spotify.com/v1/artists/y82ZzcqBIAnXg3vFWFfr12",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/artist/y82ZzcqBIAnXg3vFWFfr12"
                    },
                    "genres": ["jazz", "instrumental"],
                    "popularity": 45,
                    "images": [],
                    "followers": {
                        "href": None,
                        "total": 2500
                    }
                },
                "SuH6qRaVTBzA7atfOOP9nY": {
                    "id": "SuH6qRaVTBzA7atfOOP9nY",
                    "name": "New Artist",
                    "type": "artist",
                    "uri": "spotify:artist:SuH6qRaVTBzA7atfOOP9nY",
                    "href": "https://api.spotify.com/v1/artists/SuH6qRaVTBzA7atfOOP9nY",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/artist/SuH6qRaVTBzA7atfOOP9nY"
                    },
                    "genres": ["pop", "indie"],
                    "popularity": 60,
                    "images": [],
                    "followers": {
                        "href": None,
                        "total": 5000
                    }
                }
            },
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
                }
            },
            "followed_artists": {
                "smuqPNFPXrJKcEt943KrY8": [
                    "W0e71GNltAWtwmOaMZcm1J"  # Already following one artist
                ]
            },
            "followed_users": {
                "smuqPNFPXrJKcEt943KrY8": []  # Empty list for followed users
            },
            "current_user": {
                "id": "smuqPNFPXrJKcEt943KrY8"
            }
        })

    def test_follow_artists_success_single_artist(self):
        """Test successfully following a single artist."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB"]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 1 artist(s)", result["message"])

        # Verify the artist was added to followed_artists
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertIn("DqJ4SeZM7iQuxSkKOdQvTB", followed_artists)

        # Verify existing followed artists are preserved
        self.assertIn("W0e71GNltAWtwmOaMZcm1J", followed_artists)

    def test_follow_artists_success_multiple_artists(self):
        """Test successfully following multiple artists."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB", "y82ZzcqBIAnXg3vFWFfr12", "SuH6qRaVTBzA7atfOOP9nY"]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 3 artist(s)", result["message"])

        # Verify all artists were added to followed_artists
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        for artist_id in artist_ids:
            self.assertIn(artist_id, followed_artists)

        # Verify existing followed artists are preserved
        self.assertIn("W0e71GNltAWtwmOaMZcm1J", followed_artists)

    def test_follow_artists_duplicate_artists(self):
        """Test following artists that are already being followed (should not create duplicates)."""
        artist_ids = ["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB"]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 2 artist(s)", result["message"])

        # Verify no duplicates were created
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertEqual(followed_artists.count("W0e71GNltAWtwmOaMZcm1J"), 1)
        self.assertEqual(followed_artists.count("DqJ4SeZM7iQuxSkKOdQvTB"), 1)

    def test_follow_artists_empty_list(self):
        """Test following artists with empty list."""
        self.assert_error_behavior(
            follow_artists_or_users,
            InvalidInputError,
            "ids cannot be empty.",
            ids=[],
            type="artist"
        )

    def test_follow_artists_not_list(self):
        """Test following artists with non-list input."""
        self.assert_error_behavior(
            follow_artists_or_users,
            InvalidInputError,
            "ids must be a list.",
            ids="not_a_list",
            type="artist"
        )

    def test_follow_artists_too_many_ids(self):
        """Test following artists with more than 50 IDs."""
        artist_ids = [f"artist_{i}" for i in range(51)]

        self.assert_error_behavior(
            follow_artists_or_users,
            InvalidInputError,
            "ids cannot contain more than 50 IDs.",
            ids=artist_ids,
            type="artist"
        )

    def test_follow_artists_invalid_id_types(self):
        """Test following artists with invalid ID types."""
        test_cases = [
            ([None], "All IDs must be non-empty strings."),
            ([123], "All IDs must be non-empty strings."),
            ([""], "All IDs must be non-empty strings."),
            (["artist_1", None, "artist_3"], "All IDs must be non-empty strings."),
            (["artist_1", 123, "artist_3"], "All IDs must be non-empty strings."),
        ]

        for artist_ids, expected_message in test_cases:
            with self.subTest(artist_ids=artist_ids):
                self.assert_error_behavior(
                    follow_artists_or_users,
                    InvalidInputError,
                    expected_message,
                    ids=artist_ids,
                    type="artist"
                )

    def test_follow_artists_nonexistent_artist(self):
        """Test following a non-existent artist."""
        artist_ids = ["nonexistent_artist_id"]

        self.assert_error_behavior(
            follow_artists_or_users,
            NoResultsFoundError,
            "Artist with ID 'nonexistent_artist_id' not found.",
            ids=artist_ids,
            type="artist"
        )

    def test_follow_artists_mixed_existent_nonexistent(self):
        """Test following a mix of existent and non-existent artists."""
        artist_ids = ["W0e71GNltAWtwmOaMZcm1J", "nonexistent_artist_id"]

        self.assert_error_behavior(
            follow_artists_or_users,
            NoResultsFoundError,
            "Artist with ID 'nonexistent_artist_id' not found.",
            ids=artist_ids,
            type="artist"
        )

    def test_follow_artists_maximum_limit(self):
        """Test following exactly 50 artists (maximum limit)."""
        # Add 50 test artists to the database
        for i in range(50):
            artist_id = f"test_artist_{i:02d}"
            DB["artists"][artist_id] = {
                "id": artist_id,
                "name": f"Test Artist {i}",
                "type": "artist",
                "uri": f"spotify:artist:{artist_id}",
                "href": f"https://api.spotify.com/v1/artists/{artist_id}",
                "external_urls": {"spotify": f"https://open.spotify.com/artist/{artist_id}"},
                "genres": ["pop"],
                "popularity": 50,
                "images": [],
                "followers": {"href": None, "total": 1000}
            }

        artist_ids = [f"test_artist_{i:02d}" for i in range(50)]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 50 artist(s)", result["message"])

        # Verify all artists were added
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        for artist_id in artist_ids:
            self.assertIn(artist_id, followed_artists)

    def test_unfollow_artists_success_single_artist(self):
        """Test successfully unfollowing a single artist."""
        artist_ids = ["W0e71GNltAWtwmOaMZcm1J"]

        result = unfollow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed 1 artist(s)", result["message"])

        # Verify the artist was removed from followed_artists
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertNotIn("W0e71GNltAWtwmOaMZcm1J", followed_artists)

    def test_unfollow_artists_success_multiple_artists(self):
        """Test successfully unfollowing multiple artists."""
        # First follow some artists
        follow_artists_or_users(["DqJ4SeZM7iQuxSkKOdQvTB", "y82ZzcqBIAnXg3vFWFfr12"], "artist")

        # Then unfollow them
        artist_ids = ["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB", "y82ZzcqBIAnXg3vFWFfr12"]

        result = unfollow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed 3 artist(s)", result["message"])

        # Verify all artists were removed from followed_artists
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        for artist_id in artist_ids:
            self.assertNotIn(artist_id, followed_artists)

    def test_unfollow_artists_not_following(self):
        """Test unfollowing artists that are not being followed."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB"]

        result = unfollow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed 1 artist(s)", result["message"])

        # Verify the artist is still not in followed_artists
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertNotIn("DqJ4SeZM7iQuxSkKOdQvTB", followed_artists)

    def test_unfollow_artists_empty_list(self):
        """Test unfollowing artists with empty list."""
        self.assert_error_behavior(
            unfollow_artists_or_users,
            InvalidInputError,
            "ids cannot be empty.",
            ids=[],
            type="artist"
        )

    def test_unfollow_artists_not_list(self):
        """Test unfollowing artists with non-list input."""
        self.assert_error_behavior(
            unfollow_artists_or_users,
            InvalidInputError,
            "ids must be a list.",
            ids="not_a_list",
            type="artist"
        )

    def test_unfollow_artists_too_many_ids(self):
        """Test unfollowing artists with more than 50 IDs."""
        artist_ids = [f"artist_{i}" for i in range(51)]

        self.assert_error_behavior(
            unfollow_artists_or_users,
            InvalidInputError,
            "ids cannot contain more than 50 IDs.",
            ids=artist_ids,
            type="artist"
        )

    def test_unfollow_artists_invalid_id_types(self):
        """Test unfollowing artists with invalid ID types."""
        test_cases = [
            ([None], "All IDs must be non-empty strings."),
            ([123], "All IDs must be non-empty strings."),
            ([""], "All IDs must be non-empty strings."),
            (["artist_1", None, "artist_3"], "All IDs must be non-empty strings."),
            (["artist_1", 123, "artist_3"], "All IDs must be non-empty strings."),
        ]

        for artist_ids, expected_message in test_cases:
            with self.subTest(artist_ids=artist_ids):
                self.assert_error_behavior(
                    unfollow_artists_or_users,
                    InvalidInputError,
                    expected_message,
                    ids=artist_ids,
                    type="artist"
                )

    def test_unfollow_artists_nonexistent_artist(self):
        """Test unfollowing a non-existent artist."""
        artist_ids = ["nonexistent_artist_id"]

        self.assert_error_behavior(
            unfollow_artists_or_users,
            NoResultsFoundError,
            "Artist with ID 'nonexistent_artist_id' not found.",
            ids=artist_ids,
            type="artist"
        )

    def test_unfollow_artists_mixed_existent_nonexistent(self):
        """Test unfollowing a mix of existent and non-existent artists."""
        artist_ids = ["W0e71GNltAWtwmOaMZcm1J", "nonexistent_artist_id"]

        self.assert_error_behavior(
            unfollow_artists_or_users,
            NoResultsFoundError,
            "Artist with ID 'nonexistent_artist_id' not found.",
            ids=artist_ids,
            type="artist"
        )

    def test_follow_unfollow_cycle(self):
        """Test the complete cycle of following and then unfollowing artists."""
        # Follow artists
        follow_artists_or_users(["DqJ4SeZM7iQuxSkKOdQvTB", "y82ZzcqBIAnXg3vFWFfr12"], "artist")

        # Verify they are followed
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertIn("DqJ4SeZM7iQuxSkKOdQvTB", followed_artists)
        self.assertIn("y82ZzcqBIAnXg3vFWFfr12", followed_artists)
        self.assertIn("W0e71GNltAWtwmOaMZcm1J", followed_artists)  # Original

        # Unfollow some artists
        unfollow_artists_or_users(["DqJ4SeZM7iQuxSkKOdQvTB", "W0e71GNltAWtwmOaMZcm1J"], "artist")

        # Verify the correct state
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertNotIn("DqJ4SeZM7iQuxSkKOdQvTB", followed_artists)
        self.assertNotIn("W0e71GNltAWtwmOaMZcm1J", followed_artists)
        self.assertIn("y82ZzcqBIAnXg3vFWFfr12", followed_artists)

    def test_follow_artists_new_user(self):
        """Test following artists for a user who has no followed artists yet."""
        # Clear the followed_artists for the current user
        DB["followed_artists"]["smuqPNFPXrJKcEt943KrY8"] = []

        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB", "y82ZzcqBIAnXg3vFWFfr12"]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 2 artist(s)", result["message"])

        # Verify the artists were added
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        for artist_id in artist_ids:
            self.assertIn(artist_id, followed_artists)

    def test_unfollow_artists_empty_followed_list(self):
        """Test unfollowing artists when user has no followed artists."""
        # Clear the followed_artists for the current user
        DB["followed_artists"]["smuqPNFPXrJKcEt943KrY8"] = []

        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB"]

        result = unfollow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed 1 artist(s)", result["message"])

        # Verify the list remains empty
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertEqual(len(followed_artists), 0)

    def test_follow_artists_with_check_user_follows(self):
        """Test that follow_artists works correctly with check_user_follows_artists."""
        # Initially not following
        follow_status = check_user_follows_artists_or_users(["DqJ4SeZM7iQuxSkKOdQvTB"], "artist")
        self.assertEqual(follow_status, [False])

        # Follow the artist
        follow_artists_or_users(["DqJ4SeZM7iQuxSkKOdQvTB"], "artist")

        # Check follow status again
        follow_status = check_user_follows_artists_or_users(["DqJ4SeZM7iQuxSkKOdQvTB"], "artist")
        self.assertEqual(follow_status, [True])

    def test_unfollow_artists_with_check_user_follows(self):
        """Test that unfollow_artists works correctly with check_user_follows_artists."""
        # Initially following
        follow_status = check_user_follows_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        self.assertEqual(follow_status, [True])

        # Unfollow the artist
        unfollow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")

        # Check follow status again
        follow_status = check_user_follows_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        self.assertEqual(follow_status, [False])

    def test_follow_artists_edge_case_single_character_id(self):
        """Test following artists with single character IDs."""
        # Add a test artist with single character ID
        DB["artists"]["A"] = {
            "id": "A",
            "name": "Single Char Artist",
            "type": "artist",
            "uri": "spotify:artist:A",
            "href": "https://api.spotify.com/v1/artists/A",
            "external_urls": {"spotify": "https://open.spotify.com/artist/A"},
            "genres": ["pop"],
            "popularity": 50,
            "images": [],
            "followers": {"href": None, "total": 1000}
        }

        artist_ids = ["A"]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 1 artist(s)", result["message"])

        # Verify the artist was added
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertIn("A", followed_artists)

    def test_follow_artists_edge_case_very_long_id(self):
        """Test following artists with very long IDs."""
        # Add a test artist with very long ID
        long_id = "A" * 100
        DB["artists"][long_id] = {
            "id": long_id,
            "name": "Long ID Artist",
            "type": "artist",
            "uri": f"spotify:artist:{long_id}",
            "href": f"https://api.spotify.com/v1/artists/{long_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/artist/{long_id}"},
            "genres": ["pop"],
            "popularity": 50,
            "images": [],
            "followers": {"href": None, "total": 1000}
        }

        artist_ids = [long_id]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 1 artist(s)", result["message"])

        # Verify the artist was added
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertIn(long_id, followed_artists)

    def test_follow_artists_special_characters_in_id(self):
        """Test following artists with special characters in IDs."""
        # Add a test artist with special characters in ID
        special_id = "artist-with-dashes_123"
        DB["artists"][special_id] = {
            "id": special_id,
            "name": "Special Char Artist",
            "type": "artist",
            "uri": f"spotify:artist:{special_id}",
            "href": f"https://api.spotify.com/v1/artists/{special_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/artist/{special_id}"},
            "genres": ["pop"],
            "popularity": 50,
            "images": [],
            "followers": {"href": None, "total": 1000}
        }

        artist_ids = [special_id]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 1 artist(s)", result["message"])

        # Verify the artist was added
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertIn(special_id, followed_artists)

    # Tests for unified follow/unfollow functions
    def test_follow_artists_or_users_artists_success(self):
        """Test successfully following artists using the unified function."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB", "y82ZzcqBIAnXg3vFWFfr12"]

        result = follow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 2 artist(s)", result["message"])

        # Verify the artists were added to followed_artists
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        for artist_id in artist_ids:
            self.assertIn(artist_id, followed_artists)

        # Verify existing followed artists are preserved
        self.assertIn("W0e71GNltAWtwmOaMZcm1J", followed_artists)

    def test_follow_artists_or_users_users_success(self):
        """Test successfully following users using the unified function."""
        # Add another test user to the database
        DB["users"]["SLvTb0e3Rp3oLJ8YXl0dC5"] = {
            "id": "SLvTb0e3Rp3oLJ8YXl0dC5",
            "display_name": "Another User",
            "external_urls": {"spotify": "https://open.spotify.com/user/SLvTb0e3Rp3oLJ8YXl0dC5"},
            "followers": {"total": 30},
            "href": "https://api.spotify.com/v1/users/SLvTb0e3Rp3oLJ8YXl0dC5",
            "images": [],
            "type": "user",
            "uri": "spotify:user:SLvTb0e3Rp3oLJ8YXl0dC5",
            "country": "US",
            "email": "another@example.com",
            "product": "free"
        }

        user_ids = ["SLvTb0e3Rp3oLJ8YXl0dC5"]

        result = follow_artists_or_users(user_ids, "user")

        self.assertIn("message", result)
        self.assertIn("Successfully followed 1 user(s)", result["message"])

        # Verify the user was added to followed_users
        followed_users = DB.get("followed_users", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertIn("SLvTb0e3Rp3oLJ8YXl0dC5", followed_users)

    def test_follow_artists_or_users_invalid_type(self):
        """Test following with invalid type parameter."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB"]

        self.assert_error_behavior(
            follow_artists_or_users,
            InvalidInputError,
            "type must be either 'artist' or 'user'.",
            ids=artist_ids,
            type="invalid_type"
        )

    def test_unfollow_artists_or_users_artists_success(self):
        """Test successfully unfollowing artists using the unified function."""
        artist_ids = ["W0e71GNltAWtwmOaMZcm1J"]

        result = unfollow_artists_or_users(artist_ids, "artist")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed 1 artist(s)", result["message"])

        # Verify the artist was removed from followed_artists
        followed_artists = DB.get("followed_artists", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertNotIn("W0e71GNltAWtwmOaMZcm1J", followed_artists)

    def test_unfollow_artists_or_users_users_success(self):
        """Test successfully unfollowing users using the unified function."""
        # First follow a user
        DB["users"]["SLvTb0e3Rp3oLJ8YXl0dC5"] = {
            "id": "SLvTb0e3Rp3oLJ8YXl0dC5",
            "display_name": "Another User",
            "external_urls": {"spotify": "https://open.spotify.com/user/SLvTb0e3Rp3oLJ8YXl0dC5"},
            "followers": {"total": 30},
            "href": "https://api.spotify.com/v1/users/SLvTb0e3Rp3oLJ8YXl0dC5",
            "images": [],
            "type": "user",
            "uri": "spotify:user:SLvTb0e3Rp3oLJ8YXl0dC5",
            "country": "US",
            "email": "another@example.com",
            "product": "free"
        }

        # Add user to followed_users
        DB["followed_users"]["smuqPNFPXrJKcEt943KrY8"] = ["SLvTb0e3Rp3oLJ8YXl0dC5"]

        user_ids = ["SLvTb0e3Rp3oLJ8YXl0dC5"]

        result = unfollow_artists_or_users(user_ids, "user")

        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed 1 user(s)", result["message"])

        # Verify the user was removed from followed_users
        followed_users = DB.get("followed_users", {}).get("smuqPNFPXrJKcEt943KrY8", [])
        self.assertNotIn("SLvTb0e3Rp3oLJ8YXl0dC5", followed_users)

    def test_unfollow_artists_or_users_invalid_type(self):
        """Test unfollowing with invalid type parameter."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB"]

        self.assert_error_behavior(
            unfollow_artists_or_users,
            InvalidInputError,
            "type must be either 'artist' or 'user'.",
            ids=artist_ids,
            type="invalid_type"
        )

    def test_check_user_follows_artists_or_users_artists_success(self):
        """Test checking follow status for artists using the unified function."""
        artist_ids = ["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB"]

        result = check_user_follows_artists_or_users(artist_ids, "artist")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [True, False])  # First is followed, second is not

    def test_check_user_follows_artists_or_users_users_success(self):
        """Test checking follow status for users using the unified function."""
        # Add another test user to the database
        DB["users"]["SLvTb0e3Rp3oLJ8YXl0dC5"] = {
            "id": "SLvTb0e3Rp3oLJ8YXl0dC5",
            "display_name": "Another User",
            "external_urls": {"spotify": "https://open.spotify.com/user/SLvTb0e3Rp3oLJ8YXl0dC5"},
            "followers": {"total": 30},
            "href": "https://api.spotify.com/v1/users/SLvTb0e3Rp3oLJ8YXl0dC5",
            "images": [],
            "type": "user",
            "uri": "spotify:user:SLvTb0e3Rp3oLJ8YXl0dC5",
            "country": "US",
            "email": "another@example.com",
            "product": "free"
        }

        # Add user to followed_users
        DB["followed_users"]["smuqPNFPXrJKcEt943KrY8"] = ["SLvTb0e3Rp3oLJ8YXl0dC5"]

        user_ids = ["SLvTb0e3Rp3oLJ8YXl0dC5", "smuqPNFPXrJKcEt943KrY8"]

        result = check_user_follows_artists_or_users(user_ids, "user")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [True, False])  # First is followed, second is not

    def test_check_user_follows_artists_or_users_invalid_type(self):
        """Test checking follow status with invalid type parameter."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB"]

        self.assert_error_behavior(
            check_user_follows_artists_or_users,
            InvalidInputError,
            "type must be either 'artist' or 'user'.",
            ids=artist_ids,
            type="invalid_type"
        )

    def test_unified_functions_consistency(self):
        """Test that the unified functions work consistently."""
        artist_ids = ["DqJ4SeZM7iQuxSkKOdQvTB"]

        # Test follow
        result1 = follow_artists_or_users(artist_ids, "artist")
        self.assertIn("Successfully followed 1 artist(s)", result1["message"])

        # Test unfollow
        result2 = unfollow_artists_or_users(artist_ids, "artist")
        self.assertIn("Successfully unfollowed 1 artist(s)", result2["message"])

        # Test check
        result3 = check_user_follows_artists_or_users(artist_ids, "artist")
        self.assertEqual(result3, [False])

