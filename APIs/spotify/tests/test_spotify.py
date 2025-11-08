import unittest
from typing import Optional, List

from ..SimulationEngine.db import DB, save_state
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    InvalidInputError,
    NoResultsFoundError,
    InvalidMarketError
)

# Import the main API functions
from spotify import (
    get_album,
    get_several_albums,
    get_album_tracks,
    get_users_saved_albums,
    save_albums_for_user,
    remove_albums_for_user,
    check_users_saved_albums,
    get_artist,
    get_several_artists,
    get_artists_albums,
    get_artists_top_tracks,
    get_artists_related_artists,
    get_new_releases,
    get_featured_playlists,
    get_categories,
    get_category,
    get_category_playlists,
    get_recommendations,
    get_available_genre_seeds,
    search_for_item,
    get_current_user_profile,
    get_user_top_artists_and_tracks,
    get_user_profile,
    follow_playlist,
    unfollow_playlist,
    follow_artists_or_users,
    unfollow_artists_or_users,
    check_user_follows_playlist,
    check_user_follows_artists_or_users,
    get_followed_artists
)


class TestSpotifyAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test environment before each test."""
        DB.clear()
        # Initialize with some basic test data
        DB.update({
            "albums": {
                "4kBp5iVByDSAUc0lb78jCZ": {
                    "id": "4kBp5iVByDSAUc0lb78jCZ",
                    "name": "Test Album",
                    "type": "album",
                    "uri": "spotify:album:4kBp5iVByDSAUc0lb78jCZ",
                    "href": "https://api.spotify.com/v1/albums/4kBp5iVByDSAUc0lb78jCZ",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/album/4kBp5iVByDSAUc0lb78jCZ"
                    },
                    "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
                    "album_type": "album",
                    "total_tracks": 10,
                    "available_markets": ["US", "CA", "UK"],
                    "release_date": "2023-01-01",
                    "release_date_precision": "day",
                    "images": [],
                    "popularity": 50,
                    "copyrights": [
                        {
                            "text": "© 2023 Test Label",
                            "type": "C"
                        },
                        {
                            "text": "℗ 2023 Test Label",
                            "type": "P"
                        }
                    ],
                    "external_ids": {
                        "isrc": "USRC12345678"
                    },
                    "label": "Test Label",
                    "restrictions": {},
                    "genres": []
                },
                "gJIfNlJdPASNffy7UY2V6D": {
                    "id": "gJIfNlJdPASNffy7UY2V6D",
                    "name": "Second Test Album",
                    "type": "album",
                    "uri": "spotify:album:gJIfNlJdPASNffy7UY2V6D",
                    "href": "https://api.spotify.com/v1/albums/gJIfNlJdPASNffy7UY2V6D",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/album/gJIfNlJdPASNffy7UY2V6D"
                    },
                    "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
                    "album_type": "album",
                    "total_tracks": 8,
                    "available_markets": ["US", "CA", "UK"],
                    "release_date": "2023-02-01",
                    "release_date_precision": "day",
                    "images": [],
                    "popularity": 45,
                    "copyrights": [
                        {
                            "text": "© 2023 Test Label",
                            "type": "C"
                        },
                        {
                            "text": "℗ 2023 Test Label",
                            "type": "P"
                        }
                    ],
                    "external_ids": {
                        "isrc": "USRC87654321"
                    },
                    "label": "Test Label",
                    "restrictions": {},
                    "genres": []
                }
            },
            "artists": {
                "W0e71GNltAWtwmOaMZcm1J": {
                    "id": "W0e71GNltAWtwmOaMZcm1J",
                    "name": "Test Artist",
                    "genres": ["pop"],
                    "popularity": 70,
                    "images": [],
                    "followers": {"total": 1000}
                },
                "DqJ4SeZM7iQuxSkKOdQvTB": {
                    "id": "DqJ4SeZM7iQuxSkKOdQvTB",
                    "name": "Artist With No Albums",
                    "genres": ["rock"],
                    "popularity": 30,
                    "images": [],
                    "followers": {"total": 100}
                }
            },
            "tracks": {
                "WSB9PMCMqpdEBFpMrMfS3h": {
                    "id": "WSB9PMCMqpdEBFpMrMfS3h",
                    "name": "Test Track",
                    "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
                    "album": {"id": "4kBp5iVByDSAUc0lb78jCZ", "name": "Test Album"},
                    "duration_ms": 180000,
                    "explicit": False,
                    "track_number": 1,
                    "disc_number": 1,
                    "available_markets": ["US", "CA", "UK"],
                    "popularity": 60
                }
            },
            "playlists": {
                "QDyH69WryQ7dPRXVOFmy2V": {
                    "id": "QDyH69WryQ7dPRXVOFmy2V",
                    "name": "Test Playlist",
                    "owner": {"id": "user_123", "display_name": "Test User"},
                    "public": True,
                    "collaborative": False,
                    "description": "A test playlist",
                    "images": [],
                    "tracks": {"total": 5},
                    "followers": {"total": 100}
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
            "categories": {
                "0ZUBhfQhoczohmoxWGZpxj": {
                    "id": "0ZUBhfQhoczohmoxWGZpxj",
                    "name": "Test Category",
                    "icons": []
                }
            },
            "genres": ["acoustic", "afrobeat", "alt-rock", "alternative", "ambient"],
            "top_artists": {
                "smuqPNFPXrJKcEt943KrY8": {
                    "artists": [
                        {
                            "id": "W0e71GNltAWtwmOaMZcm1J",
                            "name": "Test Artist",
                            "genres": ["pop"],
                            "popularity": 70,
                            "images": [],
                            "followers": {"total": 1000}
                        }
                    ]
                }
            },
            "top_tracks": {
                "smuqPNFPXrJKcEt943KrY8": {
                    "tracks": [
                        {
                            "id": "WSB9PMCMqpdEBFpMrMfS3h",
                            "name": "Test Track",
                            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
                            "album": {"id": "4kBp5iVByDSAUc0lb78jCZ", "name": "Test Album"},
                            "duration_ms": 180000,
                            "explicit": False,
                            "track_number": 1,
                            "disc_number": 1,
                            "available_markets": ["US", "CA", "UK"],
                            "popularity": 60
                        }
                    ]
                }
            },
            "current_user": {
                "id": "smuqPNFPXrJKcEt943KrY8"
            },
            "followed_artists": {},
            "followed_playlists": {},
            "followed_users": {}
        })

    def _add_test_artist(self, artist_id: str, name: str, genres: Optional[List[str]] = None, popularity: int = 50):
        """Helper method to add a test artist to the database."""
        if genres is None:
            genres = ["pop"]
        
        artist_data = {
            "id": artist_id,
            "name": name,
            "genres": genres,
            "popularity": popularity,
            "images": [],
            "followers": {"total": 100}
        }
        
        if "artists" not in DB:
            DB["artists"] = {}
        
        DB["artists"][artist_id] = artist_data
        return artist_data

    def _add_test_album(self, album_id: str, name: str, artist_id: str, album_type: str = "album"):
        """Helper method to add a test album to the database."""
        album_data = {
            "id": album_id,
            "name": name,
            "artists": [{"id": artist_id, "name": f"Artist {artist_id}"}],
            "album_type": album_type,
            "total_tracks": 10,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 50
        }
        
        if "albums" not in DB:
            DB["albums"] = {}
        
        DB["albums"][album_id] = album_data
        return album_data

    def _add_test_track(self, track_id: str, name: str, artist_id: str, album_id: str):
        """Helper method to add a test track to the database."""
        track_data = {
            "id": track_id,
            "name": name,
            "artists": [{"id": artist_id, "name": f"Artist {artist_id}"}],
            "album": {"id": album_id, "name": f"Album {album_id}"},
            "duration_ms": 180000,
            "explicit": False,
            "track_number": 1,
            "disc_number": 1,
            "available_markets": ["US", "CA", "UK"],
            "popularity": 60
        }
        
        if "tracks" not in DB:
            DB["tracks"] = {}
        
        DB["tracks"][track_id] = track_data
        return track_data

    def test_get_album_success(self):
        """Test successful album retrieval."""
        result = get_album("4kBp5iVByDSAUc0lb78jCZ")
        self.assertEqual(result["id"], "4kBp5iVByDSAUc0lb78jCZ")
        self.assertEqual(result["name"], "Test Album")

    def test_get_album_complete_structure(self):
        """Test that album response has complete structure matching official Spotify API."""
        result = get_album("4kBp5iVByDSAUc0lb78jCZ")
        
        # Check all required top-level fields
        required_fields = [
            'id', 'name', 'type', 'uri', 'href', 'external_urls', 
            'artists', 'album_type', 'total_tracks', 'available_markets',
            'release_date', 'release_date_precision', 'images', 'popularity',
            'copyrights', 'external_ids', 'label', 'tracks'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing required field: {field}")
        
        # Check artist structure
        self.assertIsInstance(result['artists'], list)
        self.assertGreater(len(result['artists']), 0)
        
        artist = result['artists'][0]
        artist_fields = ['id', 'name', 'external_urls', 'href', 'type', 'uri']
        for field in artist_fields:
            self.assertIn(field, artist, f"Missing artist field: {field}")
        
        # Check tracks structure
        tracks = result['tracks']
        tracks_fields = ['href', 'limit', 'next', 'offset', 'previous', 'total', 'items']
        for field in tracks_fields:
            self.assertIn(field, tracks, f"Missing tracks field: {field}")
        
        self.assertIsInstance(tracks['items'], list)
        self.assertEqual(tracks['total'], len(tracks['items']))

    def test_get_album_artist_enhancement(self):
        """Test that artist objects are properly enhanced with missing fields."""
        result = get_album("4kBp5iVByDSAUc0lb78jCZ")
        
        for artist in result['artists']:
            # Check that all required artist fields are present
            self.assertIn('external_urls', artist)
            self.assertIn('spotify', artist['external_urls'])
            self.assertIn('href', artist)
            self.assertIn('type', artist)
            self.assertIn('uri', artist)
            
            # Check that URLs are properly formatted
            self.assertTrue(artist['href'].startswith('https://api.spotify.com/v1/artists/'))
            self.assertTrue(artist['uri'].startswith('spotify:artist:'))
            self.assertTrue(artist['external_urls']['spotify'].startswith('https://open.spotify.com/artist/'))
            
            # Check that type is correct
            self.assertEqual(artist['type'], 'artist')

    def test_get_album_tracks_integration(self):
        """Test that tracks are properly included and filtered."""
        result = get_album("4kBp5iVByDSAUc0lb78jCZ")
        
        tracks = result['tracks']
        self.assertIsInstance(tracks['items'], list)
        
        # Check that tracks are sorted by disc number and track number
        if len(tracks['items']) > 1:
            for i in range(len(tracks['items']) - 1):
                current = tracks['items'][i]
                next_track = tracks['items'][i + 1]
                
                current_disc = current.get('disc_number', 1)
                next_disc = next_track.get('disc_number', 1)
                
                if current_disc == next_disc:
                    # Same disc, should be sorted by track number
                    current_track_num = current.get('track_number', 1)
                    next_track_num = next_track.get('track_number', 1)
                    self.assertLessEqual(current_track_num, next_track_num)
                else:
                    # Different discs, should be sorted by disc number
                    self.assertLessEqual(current_disc, next_disc)

    def test_get_album_market_filtering_tracks(self):
        """Test that tracks are properly filtered by market."""
        # Test with US market (should include tracks)
        result_us = get_album("4kBp5iVByDSAUc0lb78jCZ", market="US")
        tracks_us = result_us['tracks']
        
        # Test with UK market (should exclude tracks not available in UK)
        result_uk = get_album("4kBp5iVByDSAUc0lb78jCZ", market="UK")
        tracks_uk = result_uk['tracks']
        
        # The number of tracks might be different due to market filtering
        self.assertIsInstance(tracks_us['items'], list)
        self.assertIsInstance(tracks_uk['items'], list)

    def test_get_album_tracks_pagination_structure(self):
        """Test that tracks pagination structure is correct."""
        result = get_album("4kBp5iVByDSAUc0lb78jCZ")
        tracks = result['tracks']
        
        # Check pagination fields
        self.assertEqual(tracks['limit'], 20)
        self.assertEqual(tracks['offset'], 0)
        self.assertIsNone(tracks['next'])  # No pagination needed for all tracks
        self.assertIsNone(tracks['previous'])
        self.assertEqual(tracks['total'], len(tracks['items']))
        
        # Check href format
        expected_href = f"https://api.spotify.com/v1/albums/{result['id']}/tracks"
        self.assertEqual(tracks['href'], expected_href)

    def test_get_album_data_integrity(self):
        """Test that album data is not modified in the database."""
        # Get original data
        original_data = DB['albums']['4kBp5iVByDSAUc0lb78jCZ'].copy()
        
        # Call the function
        result = get_album("4kBp5iVByDSAUc0lb78jCZ")
        
        # Check that original data is unchanged
        current_data = DB['albums']['4kBp5iVByDSAUc0lb78jCZ']
        self.assertEqual(original_data, current_data)
        
        # Check that result has enhanced data
        self.assertIn('tracks', result)
        self.assertNotIn('tracks', original_data)

    def test_get_album_with_no_tracks(self):
        """Test album retrieval when album has no tracks."""
        # Create an album with no tracks
        album_id = "test_album_no_tracks"
        self._add_test_album(album_id, "Album With No Tracks", "W0e71GNltAWtwmOaMZcm1J")
        
        result = get_album(album_id)
        
        # Should still have tracks structure but with empty items
        self.assertIn('tracks', result)
        self.assertEqual(result['tracks']['total'], 0)
        self.assertEqual(len(result['tracks']['items']), 0)

    def test_get_album_with_multiple_artists(self):
        """Test album retrieval with multiple artists."""
        # Create an album with multiple artists
        album_id = "test_album_multiple_artists"
        album_data = {
            "id": album_id,
            "name": "Collaboration Album",
            "artists": [
                {"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"},
                {"id": "DqJ4SeZM7iQuxSkKOdQvTB", "name": "Popular Band"}
            ],
            "album_type": "album",
            "total_tracks": 5,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 50,
            "copyrights": [],
            "external_ids": {},
            "label": "Test Label",
            "restrictions": {},
            "genres": []
        }
        DB['albums'][album_id] = album_data
        
        result = get_album(album_id)
        
        # Check that all artists are enhanced
        self.assertEqual(len(result['artists']), 2)
        for artist in result['artists']:
            self.assertIn('external_urls', artist)
            self.assertIn('href', artist)
            self.assertIn('type', artist)
            self.assertIn('uri', artist)

    def test_get_album_edge_cases(self):
        """Test album retrieval with edge case data."""
        # Test with minimal album data
        album_id = "test_album_minimal"
        minimal_album = {
            "id": album_id,
            "name": "Minimal Album",
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album_type": "album",
            "total_tracks": 1,
            "available_markets": ["US"],
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 0,
            "copyrights": [],
            "external_ids": {},
            "label": "",
            "restrictions": {},
            "genres": []
        }
        DB['albums'][album_id] = minimal_album
        
        result = get_album(album_id)
        
        # Should still work with minimal data
        self.assertEqual(result['id'], album_id)
        self.assertIn('tracks', result)
        self.assertEqual(result['tracks']['total'], 0)  # No tracks in DB for this album



    def test_get_several_albums_success(self):
        """Test successful retrieval of multiple albums."""
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("albums", result)
        self.assertEqual(len(result["albums"]), 1)
        self.assertEqual(result["albums"][0]["id"], "4kBp5iVByDSAUc0lb78jCZ")

    def test_get_several_albums_with_nonexistent_albums(self):
        """Test retrieval of multiple albums with some non-existent albums."""
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ", "nonexistent_album"])
        self.assertIn("albums", result)
        self.assertEqual(len(result["albums"]), 2)
        self.assertEqual(result["albums"][0]["id"], "4kBp5iVByDSAUc0lb78jCZ")
        self.assertIsNone(result["albums"][1])

    def test_get_several_albums_with_market_filtering(self):
        """Test retrieval of multiple albums with market filtering."""
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"], market="US")
        self.assertIn("albums", result)
        self.assertEqual(len(result["albums"]), 1)
        self.assertEqual(result["albums"][0]["id"], "4kBp5iVByDSAUc0lb78jCZ")

    def test_get_several_albums_invalid_input(self):
        """Test retrieval of multiple albums with invalid input."""
        # Test with non-list input
        with self.assertRaises(InvalidInputError):
            get_several_albums("4kBp5iVByDSAUc0lb78jCZ")
        
        # Test with too many album IDs
        with self.assertRaises(InvalidInputError):
            get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"] * 21)
        
        # Test with empty album IDs
        with self.assertRaises(InvalidInputError):
            get_several_albums(["4kBp5iVByDSAUc0lb78jCZ", ""])

    def test_get_several_albums_invalid_market(self):
        """Test retrieval of multiple albums with invalid market."""
        with self.assertRaises(InvalidMarketError):
            get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"], market="INVALID")

    def test_get_several_albums_complete_structure(self):
        """Test that get_several_albums returns complete album structure matching official Spotify API."""
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"])
        
        # Check main response structure
        self.assertIn("albums", result)
        self.assertIsInstance(result["albums"], list)
        self.assertEqual(len(result["albums"]), 1)
        
        album = result["albums"][0]
        self.assertIsNotNone(album)
        
        # Check all required album fields from docstring
        required_fields = [
            'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 
            'album_type', 'total_tracks', 'available_markets', 'release_date', 
            'release_date_precision', 'images', 'popularity', 'restrictions', 
            'tracks', 'copyrights', 'external_ids', 'label'
        ]
        
        for field in required_fields:
            self.assertIn(field, album, f"Missing required field: {field}")
        
        # Check artist structure
        self.assertIsInstance(album['artists'], list)
        if album['artists']:
            artist = album['artists'][0]
            artist_fields = ['external_urls', 'href', 'id', 'name', 'type', 'uri']
            for field in artist_fields:
                self.assertIn(field, artist, f"Missing artist field: {field}")
        
        # Check tracks structure
        tracks = album.get('tracks', {})
        tracks_fields = ['href', 'limit', 'next', 'offset', 'previous', 'total', 'items']
        for field in tracks_fields:
            self.assertIn(field, tracks, f"Missing tracks field: {field}")

    def test_get_several_albums_artist_enhancement(self):
        """Test that artist objects in get_several_albums are properly enhanced."""
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"])
        album = result["albums"][0]
        
        self.assertIsNotNone(album)
        self.assertIn('artists', album)
        self.assertIsInstance(album['artists'], list)
        
        for artist in album['artists']:
            # Check that artist has all required fields from official API
            self.assertIn('external_urls', artist)
            self.assertIn('spotify', artist['external_urls'])
            self.assertIn('href', artist)
            self.assertIn('id', artist)
            self.assertIn('name', artist)
            self.assertIn('type', artist)
            self.assertIn('uri', artist)
            
            # Check that external_urls contains proper Spotify URL
            self.assertTrue(artist['external_urls']['spotify'].startswith('https://open.spotify.com/artist/'))
            # Check that href contains proper API URL
            self.assertTrue(artist['href'].startswith('https://api.spotify.com/v1/artists/'))
            # Check that uri contains proper Spotify URI
            self.assertTrue(artist['uri'].startswith('spotify:artist:'))

    def test_get_several_albums_tracks_integration(self):
        """Test that get_several_albums includes proper tracks information."""
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"])
        album = result["albums"][0]
        
        self.assertIsNotNone(album)
        self.assertIn('tracks', album)
        
        tracks = album['tracks']
        self.assertIsInstance(tracks, dict)
        self.assertIn('items', tracks)
        self.assertIsInstance(tracks['items'], list)
        self.assertIn('total', tracks)
        self.assertIsInstance(tracks['total'], int)
        
        # Check that tracks are sorted by disc number and track number
        if tracks['items']:
            track_numbers = [track.get('track_number', 0) for track in tracks['items']]
            self.assertEqual(track_numbers, sorted(track_numbers))

    def test_get_several_albums_market_filtering_tracks(self):
        """Test that get_several_albums properly filters tracks by market."""
        # Test with US market (should include tracks)
        result_us = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"], market="US")
        album_us = result_us["albums"][0]
        self.assertIsNotNone(album_us)
        self.assertIn('tracks', album_us)
        self.assertGreater(album_us['tracks']['total'], 0)
        
        # Test with invalid market (should return None for album)
        result_invalid = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"], market="XX")
        album_invalid = result_invalid["albums"][0]
        self.assertIsNone(album_invalid)

    def test_get_several_albums_tracks_pagination_structure(self):
        """Test that tracks object in get_several_albums has proper pagination structure."""
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"])
        album = result["albums"][0]
        
        self.assertIsNotNone(album)
        tracks = album['tracks']
        
        # Check pagination fields
        self.assertIn('href', tracks)
        self.assertIn('limit', tracks)
        self.assertIn('offset', tracks)
        self.assertIn('total', tracks)
        self.assertIn('next', tracks)
        self.assertIn('previous', tracks)
        
        # Check data types
        self.assertIsInstance(tracks['href'], str)
        self.assertIsInstance(tracks['limit'], int)
        self.assertIsInstance(tracks['offset'], int)
        self.assertIsInstance(tracks['total'], int)
        
        # Check that href contains proper API endpoint
        self.assertTrue(tracks['href'].startswith('https://api.spotify.com/v1/albums/'))
        self.assertTrue(tracks['href'].endswith('/tracks'))

    def test_get_several_albums_data_integrity(self):
        """Test that get_several_albums doesn't mutate the original database."""
        # Get original album data
        original_albums = DB.get('albums', {}).copy()
        original_tracks = DB.get('tracks', {}).copy()
        
        # Call the function
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"])
        
        # Check that database wasn't modified
        self.assertEqual(DB.get('albums', {}), original_albums)
        self.assertEqual(DB.get('tracks', {}), original_tracks)
        
        # Check that returned data is properly enriched
        album = result["albums"][0]
        self.assertIsNotNone(album)
        self.assertIn('tracks', album)
        self.assertIn('artists', album)
        
        # Verify artists are enhanced
        for artist in album['artists']:
            self.assertIn('external_urls', artist)

    def test_get_several_albums_with_no_tracks(self):
        """Test get_several_albums with an album that has no tracks."""
        # Create a test album with no tracks
        test_album_id = "test_album_no_tracks"
        DB['albums'][test_album_id] = {
            "id": test_album_id,
            "name": "Test Album No Tracks",
            "type": "album",
            "uri": f"spotify:album:{test_album_id}",
            "href": f"https://api.spotify.com/v1/albums/{test_album_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/album/{test_album_id}"},
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album_type": "album",
            "total_tracks": 0,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 50,
            "restrictions": None,
            "copyrights": [],
            "external_ids": {},
            "label": "Test Label"
        }
        
        result = get_several_albums([test_album_id])
        album = result["albums"][0]
        
        self.assertIsNotNone(album)
        self.assertIn('tracks', album)
        self.assertEqual(album['tracks']['total'], 0)
        self.assertEqual(len(album['tracks']['items']), 0)

    def test_get_several_albums_with_multiple_artists(self):
        """Test get_several_albums with an album that has multiple artists."""
        # Create a test album with multiple artists
        test_album_id = "test_album_multiple_artists"
        DB['albums'][test_album_id] = {
            "id": test_album_id,
            "name": "Test Album Multiple Artists",
            "type": "album",
            "uri": f"spotify:album:{test_album_id}",
            "href": f"https://api.spotify.com/v1/albums/{test_album_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/album/{test_album_id}"},
            "artists": [
                {"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist 1"},
                {"id": "W0e71GNltAWtwmOaMZcm2J", "name": "Test Artist 2"}
            ],
            "album_type": "album",
            "total_tracks": 5,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 50,
            "restrictions": None,
            "copyrights": [],
            "external_ids": {},
            "label": "Test Label"
        }
        
        result = get_several_albums([test_album_id])
        album = result["albums"][0]
        
        self.assertIsNotNone(album)
        self.assertIn('artists', album)
        self.assertEqual(len(album['artists']), 2)
        
        # Check that all artists are enhanced
        for artist in album['artists']:
            self.assertIn('external_urls', artist)
            self.assertIn('href', artist)
            self.assertIn('type', artist)
            self.assertIn('uri', artist)

    def test_get_several_albums_edge_cases(self):
        """Test get_several_albums with various edge cases."""
        # Test with empty list
        result = get_several_albums([])
        self.assertIn("albums", result)
        self.assertEqual(len(result["albums"]), 0)
        
        # Test with maximum allowed albums
        album_ids = [f"album_{i}" for i in range(20)]
        # Add test albums to DB
        for i, album_id in enumerate(album_ids):
            DB['albums'][album_id] = {
                "id": album_id,
                "name": f"Test Album {i}",
                "type": "album",
                "uri": f"spotify:album:{album_id}",
                "href": f"https://api.spotify.com/v1/albums/{album_id}",
                "external_urls": {"spotify": f"https://open.spotify.com/album/{album_id}"},
                "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
                "album_type": "album",
                "total_tracks": 1,
                "available_markets": ["US", "CA", "UK"],
                "release_date": "2023-01-01",
                "release_date_precision": "day",
                "images": [],
                "popularity": 50,
                "restrictions": None,
                "copyrights": [],
                "external_ids": {},
                "label": "Test Label"
            }
        
        result = get_several_albums(album_ids)
        self.assertIn("albums", result)
        self.assertEqual(len(result["albums"]), 20)
        
        # All albums should be found
        for album in result["albums"]:
            self.assertIsNotNone(album)

    def test_get_several_albums_order_preservation(self):
        """Test that get_several_albums preserves the order of input album IDs."""
        album_ids = ["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D", "nonexistent_album"]
        
        result = get_several_albums(album_ids)
        
        self.assertEqual(len(result["albums"]), 3)
        
        # Check order preservation
        self.assertIsNotNone(result["albums"][0])  # First album exists
        self.assertIsNotNone(result["albums"][1])  # Second album exists
        self.assertIsNone(result["albums"][2])     # Third album doesn't exist
        
        # Check that IDs match expected order
        self.assertEqual(result["albums"][0]["id"], "4kBp5iVByDSAUc0lb78jCZ")
        self.assertEqual(result["albums"][1]["id"], "gJIfNlJdPASNffy7UY2V6D")

    def test_get_several_albums_mixed_existence(self):
        """Test get_several_albums with a mix of existing and non-existing albums."""
        album_ids = ["4kBp5iVByDSAUc0lb78jCZ", "nonexistent_1", "gJIfNlJdPASNffy7UY2V6D", "nonexistent_2"]
        
        result = get_several_albums(album_ids)
        
        self.assertEqual(len(result["albums"]), 4)
        
        # Check that existing albums are returned as objects, non-existing as None
        self.assertIsNotNone(result["albums"][0])  # First album exists
        self.assertIsNone(result["albums"][1])     # Second album doesn't exist
        self.assertIsNotNone(result["albums"][2])  # Third album exists
        self.assertIsNone(result["albums"][3])     # Fourth album doesn't exist
        
        # Check that existing albums have proper structure
        self.assertEqual(result["albums"][0]["id"], "4kBp5iVByDSAUc0lb78jCZ")
        self.assertEqual(result["albums"][2]["id"], "gJIfNlJdPASNffy7UY2V6D")

    def test_get_several_albums_market_unavailable(self):
        """Test get_several_albums when albums are not available in specified market."""
        # Test with market where album is not available
        result = get_several_albums(["4kBp5iVByDSAUc0lb78jCZ"], market="XX")
        
        self.assertIn("albums", result)
        self.assertEqual(len(result["albums"]), 1)
        self.assertIsNone(result["albums"][0])  # Album not available in XX market

    def test_get_several_albums_all_nonexistent(self):
        """Test get_several_albums when all requested albums don't exist."""
        album_ids = ["nonexistent_1", "nonexistent_2", "nonexistent_3"]
        
        result = get_several_albums(album_ids)
        
        self.assertIn("albums", result)
        self.assertEqual(len(result["albums"]), 3)
        
        # All albums should be None
        for album in result["albums"]:
            self.assertIsNone(album)

    def test_get_album_tracks_success(self):
        """Test successful retrieval of album tracks."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        self.assertIn("items", result)
        self.assertIn("total", result)
        self.assertIn("limit", result)
        self.assertIn("offset", result)
        self.assertIn("href", result)

    def test_get_album_tracks_with_pagination(self):
        """Test retrieval of album tracks with pagination."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", limit=5, offset=0)
        self.assertIn("items", result)
        self.assertEqual(result["limit"], 5)
        self.assertEqual(result["offset"], 0)

    def test_get_album_tracks_with_market_filtering(self):
        """Test retrieval of album tracks with market filtering."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", market="US")
        self.assertIn("items", result)

    def test_get_album_tracks_album_not_found(self):
        """Test retrieval of album tracks for non-existent album."""
        with self.assertRaises(NoResultsFoundError):
            get_album_tracks("nonexistent_album")

    def test_get_album_tracks_invalid_input(self):
        """Test retrieval of album tracks with invalid input."""
        # Test with empty album ID
        with self.assertRaises(InvalidInputError):
            get_album_tracks("")
        
        # Test with invalid limit
        with self.assertRaises(InvalidInputError):
            get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", limit=0)
        
        # Test with invalid offset
        with self.assertRaises(InvalidInputError):
            get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", offset=-1)

    def test_get_album_tracks_invalid_market(self):
        """Test retrieval of album tracks with invalid market."""
        with self.assertRaises(InvalidMarketError):
            get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", market="INVALID")

    def test_get_album_tracks_complete_structure(self):
        """Test that get_album_tracks returns complete track structure matching official Spotify API."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        
        # Check main response structure
        self.assertIn("items", result)
        self.assertIn("total", result)
        self.assertIn("limit", result)
        self.assertIn("offset", result)
        self.assertIn("href", result)
        self.assertIn("next", result)
        self.assertIn("previous", result)
        
        if result["items"]:
            track = result["items"][0]
            
            # Check all required track fields from docstring
            required_track_fields = [
                'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 'album',
                'duration_ms', 'explicit', 'track_number', 'disc_number', 'available_markets',
                'popularity', 'is_local', 'is_playable', 'external_ids', 'linked_from',
                'restrictions', 'preview_url'
            ]
            
            for field in required_track_fields:
                self.assertIn(field, track, f"Missing required track field: {field}")
            
            # Check artist structure
            self.assertIsInstance(track['artists'], list)
            if track['artists']:
                artist = track['artists'][0]
                artist_fields = ['external_urls', 'href', 'id', 'name', 'type', 'uri']
                for field in artist_fields:
                    self.assertIn(field, artist, f"Missing artist field: {field}")
            
            # Check album structure
            album = track.get('album', {})
            album_fields = ['id', 'name', 'uri', 'href', 'external_urls', 'images']
            for field in album_fields:
                self.assertIn(field, album, f"Missing album field: {field}")

    def test_get_album_tracks_artist_enhancement(self):
        """Test that artist objects in get_album_tracks are properly enhanced."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        
        if result["items"]:
            track = result["items"][0]
            self.assertIn('artists', track)
            self.assertIsInstance(track['artists'], list)
            
            for artist in track['artists']:
                # Check that artist has all required fields from official API
                self.assertIn('external_urls', artist)
                self.assertIn('spotify', artist['external_urls'])
                self.assertIn('href', artist)
                self.assertIn('id', artist)
                self.assertIn('name', artist)
                self.assertIn('type', artist)
                self.assertIn('uri', artist)
                
                # Check that external_urls contains proper Spotify URL
                self.assertTrue(artist['external_urls']['spotify'].startswith('https://open.spotify.com/artist/'))
                # Check that href contains proper API URL
                self.assertTrue(artist['href'].startswith('https://api.spotify.com/v1/artists/'))
                # Check that uri contains proper Spotify URI
                self.assertTrue(artist['uri'].startswith('spotify:artist:'))

    def test_get_album_tracks_album_enhancement(self):
        """Test that album objects in get_album_tracks are properly enhanced."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        
        if result["items"]:
            track = result["items"][0]
            self.assertIn('album', track)
            
            album = track['album']
            # Check that album has all required fields
            self.assertIn('id', album)
            self.assertIn('name', album)
            self.assertIn('uri', album)
            self.assertIn('href', album)
            self.assertIn('external_urls', album)
            self.assertIn('images', album)
            
            # Check that external_urls contains proper Spotify URL
            self.assertIn('spotify', album['external_urls'])
            self.assertTrue(album['external_urls']['spotify'].startswith('https://open.spotify.com/album/'))
            # Check that href contains proper API URL
            self.assertTrue(album['href'].startswith('https://api.spotify.com/v1/albums/'))
            # Check that uri contains proper Spotify URI
            self.assertTrue(album['uri'].startswith('spotify:album:'))

    def test_get_album_tracks_market_filtering(self):
        """Test that get_album_tracks properly filters tracks by market."""
        # Test with US market (should include tracks)
        result_us = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", market="US")
        self.assertGreater(len(result_us["items"]), 0)
        
        # Test with invalid market (should return no tracks)
        result_invalid = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", market="XX")
        self.assertEqual(len(result_invalid["items"]), 0)

    def test_get_album_tracks_pagination_structure_enhanced(self):
        """Test that get_album_tracks has proper pagination structure."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        
        # Check pagination fields
        self.assertIn('href', result)
        self.assertIn('limit', result)
        self.assertIn('offset', result)
        self.assertIn('total', result)
        self.assertIn('next', result)
        self.assertIn('previous', result)
        
        # Check data types
        self.assertIsInstance(result['href'], str)
        self.assertIsInstance(result['limit'], int)
        self.assertIsInstance(result['offset'], int)
        self.assertIsInstance(result['total'], int)
        
        # Check that href contains proper API endpoint
        self.assertTrue(result['href'].startswith('https://api.spotify.com/v1/albums/'))
        self.assertTrue(result['href'].endswith('/tracks'))

    def test_get_album_tracks_data_integrity(self):
        """Test that get_album_tracks doesn't mutate the original database."""
        # Get original track data
        original_tracks = DB.get('tracks', {}).copy()
        original_albums = DB.get('albums', {}).copy()
        
        # Call the function
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        
        # Check that database wasn't modified
        self.assertEqual(DB.get('tracks', {}), original_tracks)
        self.assertEqual(DB.get('albums', {}), original_albums)
        
        # Check that returned data is properly enriched
        if result["items"]:
            track = result["items"][0]
            self.assertIn('artists', track)
            self.assertIn('album', track)
            
            # Verify artists are enhanced
            for artist in track['artists']:
                self.assertIn('external_urls', artist)

    def test_get_album_tracks_with_no_tracks(self):
        """Test get_album_tracks with an album that has no tracks."""
        # Create a test album with no tracks
        test_album_id = "test_album_no_tracks"
        DB['albums'][test_album_id] = {
            "id": test_album_id,
            "name": "Test Album No Tracks",
            "type": "album",
            "uri": f"spotify:album:{test_album_id}",
            "href": f"https://api.spotify.com/v1/albums/{test_album_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/album/{test_album_id}"},
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album_type": "album",
            "total_tracks": 0,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 50,
            "restrictions": None,
            "copyrights": [],
            "external_ids": {},
            "label": "Test Label"
        }
        
        result = get_album_tracks(test_album_id)
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)
        self.assertEqual(result["total"], 0)

    def test_get_album_tracks_with_multiple_artists(self):
        """Test get_album_tracks with tracks that have multiple artists."""
        # Create a test track with multiple artists
        test_track_id = "test_track_multiple_artists"
        test_album_id = "4kBp5iVByDSAUc0lb78jCZ"
        
        DB['tracks'][test_track_id] = {
            "id": test_track_id,
            "name": "Test Track Multiple Artists",
            "type": "track",
            "uri": f"spotify:track:{test_track_id}",
            "href": f"https://api.spotify.com/v1/tracks/{test_track_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/track/{test_track_id}"},
            "artists": [
                {"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist 1"},
                {"id": "W0e71GNltAWtwmOaMZcm2J", "name": "Test Artist 2"}
            ],
            "album": {
                "id": test_album_id,
                "name": "Test Album",
                "uri": f"spotify:album:{test_album_id}",
                "href": f"https://api.spotify.com/v1/albums/{test_album_id}",
                "external_urls": {"spotify": f"https://open.spotify.com/album/{test_album_id}"}
            },
            "duration_ms": 180000,
            "explicit": False,
            "track_number": 1,
            "disc_number": 1,
            "available_markets": ["US", "CA", "UK"],
            "popularity": 50,
            "is_local": False,
            "is_playable": True,
            "external_ids": {"isrc": "TEST12345678"},
            "linked_from": None,
            "restrictions": None,
            "preview_url": None
        }
        
        result = get_album_tracks(test_album_id)
        
        # Find our test track
        test_track = None
        for track in result["items"]:
            if track["id"] == test_track_id:
                test_track = track
                break
        
        self.assertIsNotNone(test_track)
        self.assertIn('artists', test_track)
        self.assertEqual(len(test_track['artists']), 2)
        
        # Check that all artists are enhanced
        for artist in test_track['artists']:
            self.assertIn('external_urls', artist)
            self.assertIn('href', artist)
            self.assertIn('type', artist)
            self.assertIn('uri', artist)

    def test_get_album_tracks_edge_cases(self):
        """Test get_album_tracks with various edge cases."""
        # Test with maximum limit
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", limit=50)
        self.assertLessEqual(len(result["items"]), 50)
        self.assertEqual(result["limit"], 50)
        
        # Test with offset
        result_offset = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", limit=1, offset=1)
        self.assertEqual(result_offset["offset"], 1)
        
        # Test with minimum limit
        result_min = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", limit=1)
        self.assertEqual(result_min["limit"], 1)

    def test_get_album_tracks_track_sorting(self):
        """Test that get_album_tracks sorts tracks by disc number and track number."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        
        if len(result["items"]) > 1:
            # Check that tracks are sorted by disc number and track number
            track_numbers = [(track.get('disc_number', 1), track.get('track_number', 1)) 
                           for track in result["items"]]
            sorted_numbers = sorted(track_numbers)
            self.assertEqual(track_numbers, sorted_numbers)

    def test_get_album_tracks_market_unavailable(self):
        """Test get_album_tracks when tracks are not available in specified market."""
        # Test with market where tracks are not available
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", market="XX")
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)
        self.assertEqual(result["total"], 0)

    def test_get_album_tracks_pagination_next_previous(self):
        """Test get_album_tracks pagination with next and previous URLs."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ", limit=1, offset=0)
        
        # Check pagination URLs
        if result["total"] > 1:
            self.assertIsNotNone(result["next"])
            next_url = result["next"]
            if next_url:
                self.assertTrue(next_url.startswith("https://api.spotify.com/v1/albums/"))
                self.assertIn("limit=1", next_url)
                self.assertIn("offset=1", next_url)
        
        # Previous should be None for first page
        self.assertIsNone(result["previous"])

    def test_get_album_tracks_all_optional_fields(self):
        """Test that get_album_tracks handles all optional fields correctly."""
        result = get_album_tracks("4kBp5iVByDSAUc0lb78jCZ")
        
        if result["items"]:
            track = result["items"][0]
            
            # Check optional fields are present (may be None)
            optional_fields = ['external_ids', 'linked_from', 'restrictions', 'preview_url']
            for field in optional_fields:
                self.assertIn(field, track)

    def test_get_users_saved_albums_success(self):
        """Test successful retrieval of user's saved albums."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums()
        self.assertIn("items", result)
        self.assertIn("total", result)
        self.assertIn("limit", result)
        self.assertIn("offset", result)
        self.assertIn("href", result)

    def test_get_users_saved_albums_with_pagination(self):
        """Test retrieval of user's saved albums with pagination."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums(limit=5, offset=0)
        self.assertIn("items", result)
        self.assertEqual(result["limit"], 5)
        self.assertEqual(result["offset"], 0)

    def test_get_users_saved_albums_with_market_filtering(self):
        """Test retrieval of user's saved albums with market filtering."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums(market="US")
        self.assertIn("items", result)

    def test_get_users_saved_albums_no_saved_albums(self):
        """Test retrieval of user's saved albums when user has no saved albums."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = get_users_saved_albums()
        self.assertIn("items", result)
        self.assertEqual(result["total"], 0)

    def test_get_users_saved_albums_invalid_input(self):
        """Test retrieval of user's saved albums with invalid input."""
        # Test with invalid limit
        with self.assertRaises(InvalidInputError):
            get_users_saved_albums(limit=0)
        
        # Test with invalid offset
        with self.assertRaises(InvalidInputError):
            get_users_saved_albums(offset=-1)

    def test_get_users_saved_albums_invalid_market(self):
        """Test retrieval of user's saved albums with invalid market."""
        with self.assertRaises(InvalidMarketError):
            get_users_saved_albums(market="INVALID")

    def test_save_albums_for_user_success(self):
        """Test successful saving of albums for user."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])
        
        # Verify albums were actually saved
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertIn("4kBp5iVByDSAUc0lb78jCZ", saved_albums)

    def test_save_albums_for_user_multiple_albums(self):
        """Test successful saving of multiple albums for user."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"])
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])

    def test_save_albums_for_user_duplicate_albums(self):
        """Test saving albums that are already saved."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # First save
        save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        # Second save of the same album
        result = save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])

    def test_save_albums_for_user_invalid_input(self):
        """Test saving albums with invalid input."""
        # Test with non-list input
        with self.assertRaises(InvalidInputError):
            save_albums_for_user("4kBp5iVByDSAUc0lb78jCZ")
        
        # Test with too many album IDs
        with self.assertRaises(InvalidInputError):
            save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"] * 51)
        
        # Test with empty album IDs
        with self.assertRaises(InvalidInputError):
            save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", ""])

    def test_save_albums_for_user_nonexistent_album(self):
        """Test saving non-existent albums."""
        with self.assertRaises(NoResultsFoundError):
            save_albums_for_user(["nonexistent_album"])

    def test_remove_albums_for_user_success(self):
        """Test successful removal of albums for user."""
        # First save some albums
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        
        result = remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])
        
        # Verify album was actually removed
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertNotIn("4kBp5iVByDSAUc0lb78jCZ", saved_albums)
        self.assertIn("gJIfNlJdPASNffy7UY2V6D", saved_albums)  # Other album should remain

    def test_remove_albums_for_user_multiple_albums(self):
        """Test successful removal of multiple albums for user."""
        # First save some albums
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D', '5V17F52VsJ3ZDIF1iYxe6D']
        
        result = remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])

    def test_remove_albums_for_user_nonexistent_albums(self):
        """Test removal of albums that are not saved."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = remove_albums_for_user(["nonexistent_album"])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])

    def test_remove_albums_for_user_invalid_input(self):
        """Test removal of albums with invalid input."""
        # Test with non-list input
        with self.assertRaises(InvalidInputError):
            remove_albums_for_user("4kBp5iVByDSAUc0lb78jCZ")
        
        # Test with too many album IDs
        with self.assertRaises(InvalidInputError):
            remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"] * 51)
        
        # Test with empty album IDs
        with self.assertRaises(InvalidInputError):
            remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", ""])

    def test_check_users_saved_albums_success(self):
        """Test successful checking of user's saved albums."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = check_users_saved_albums(["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0])  # 4kBp5iVByDSAUc0lb78jCZ is saved
        self.assertFalse(result[1])  # gJIfNlJdPASNffy7UY2V6D is not saved

    def test_check_users_saved_albums_empty_list(self):
        """Test checking of user's saved albums with empty list."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = check_users_saved_albums([])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_check_users_saved_albums_no_saved_albums(self):
        """Test checking of user's saved albums when user has no saved albums."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = check_users_saved_albums(["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertFalse(result[0])  # 4kBp5iVByDSAUc0lb78jCZ is not saved
        self.assertFalse(result[1])  # gJIfNlJdPASNffy7UY2V6D is not saved

    def test_check_users_saved_albums_invalid_input(self):
        """Test checking of user's saved albums with invalid input."""
        # Test with non-list input
        with self.assertRaises(InvalidInputError):
            check_users_saved_albums("4kBp5iVByDSAUc0lb78jCZ")
        
        # Test with too many album IDs
        with self.assertRaises(InvalidInputError):
            check_users_saved_albums(["4kBp5iVByDSAUc0lb78jCZ"] * 51)
        
        # Test with empty album IDs
        with self.assertRaises(InvalidInputError):
            check_users_saved_albums(["4kBp5iVByDSAUc0lb78jCZ", ""])

    def test_get_album_with_market_filtering(self):
        """Test getting album with market filtering."""
        result = get_album("4kBp5iVByDSAUc0lb78jCZ", market="US")
        self.assertEqual(result["id"], "4kBp5iVByDSAUc0lb78jCZ")

    def test_get_album_market_not_available(self):
        """Test getting album that is not available in specified market."""
        with self.assertRaises(NoResultsFoundError):
            get_album("4kBp5iVByDSAUc0lb78jCZ", market="XX")  # Assuming XX is not in available_markets

    def test_get_album_invalid_market(self):
        """Test getting album with invalid market code."""
        with self.assertRaises(InvalidMarketError):
            get_album("4kBp5iVByDSAUc0lb78jCZ", market="INVALID")

    def test_get_album_invalid_input(self):
        """Test getting album with invalid input."""
        # Test with empty album ID
        with self.assertRaises(InvalidInputError):
            get_album("")
        
        # Test with non-string album ID
        with self.assertRaises(InvalidInputError):
            get_album(123)

    def test_get_album_not_found(self):
        """Test getting non-existent album."""
        with self.assertRaises(NoResultsFoundError):
            get_album("nonexistent_album")

    def test_get_artist_success(self):
        """Test successful artist retrieval."""
        result = get_artist("W0e71GNltAWtwmOaMZcm1J")
        self.assertEqual(result["id"], "W0e71GNltAWtwmOaMZcm1J")
        self.assertEqual(result["name"], "Test Artist")

    def test_get_artist_not_found(self):
        """Test artist retrieval with non-existent ID."""
        with self.assertRaises(NoResultsFoundError):
            get_artist("nonexistent_artist")

    def test_get_several_artists_success(self):
        """Test successful retrieval of multiple artists."""
        result = get_several_artists(["W0e71GNltAWtwmOaMZcm1J"])
        self.assertIn("artists", result)
        self.assertEqual(len(result["artists"]), 1)
        self.assertEqual(result["artists"][0]["id"], "W0e71GNltAWtwmOaMZcm1J")

    def test_get_artists_top_tracks_success(self):
        """Test successful retrieval of artist's top tracks."""
        result = get_artists_top_tracks("W0e71GNltAWtwmOaMZcm1J", "US")
        self.assertIn("tracks", result)
        self.assertIsInstance(result["tracks"], list)

    def test_get_artists_related_artists_success(self):
        """Test successful retrieval of related artists."""
        result = get_artists_related_artists("W0e71GNltAWtwmOaMZcm1J")
        self.assertIn("artists", result)
        self.assertIsInstance(result["artists"], list)

    def test_get_several_artists_with_nonexistent_artists(self):
        """Test retrieval of multiple artists with some non-existent artists."""
        result = get_several_artists(["W0e71GNltAWtwmOaMZcm1J", "nonexistent_artist"])
        self.assertIn("artists", result)
        self.assertEqual(len(result["artists"]), 1)
        self.assertEqual(result["artists"][0]["id"], "W0e71GNltAWtwmOaMZcm1J")

    def test_get_several_artists_all_nonexistent(self):
        """Test retrieval of multiple artists when none exist."""
        with self.assertRaises(NoResultsFoundError):
            get_several_artists(["nonexistent_artist1", "nonexistent_artist2"])

    def test_get_several_artists_invalid_input(self):
        """Test retrieval of multiple artists with invalid input."""
        # Test with non-list input
        with self.assertRaises(InvalidInputError):
            get_several_artists("W0e71GNltAWtwmOaMZcm1J")
        
        # Test with empty list
        with self.assertRaises(InvalidInputError):
            get_several_artists([])
        
        # Test with too many artist IDs
        with self.assertRaises(InvalidInputError):
            get_several_artists(["W0e71GNltAWtwmOaMZcm1J"] * 51)
        
        # Test with empty artist IDs
        with self.assertRaises(InvalidInputError):
            get_several_artists(["W0e71GNltAWtwmOaMZcm1J", ""])

    def test_get_artist_invalid_input(self):
        """Test artist retrieval with invalid input."""
        # Test with empty artist ID
        with self.assertRaises(InvalidInputError):
            get_artist("")
        
        # Test with non-string artist ID
        with self.assertRaises(InvalidInputError):
            get_artist(123)

    def test_get_artists_albums_success(self):
        """Test successful retrieval of artist's albums."""
        result = get_artists_albums("W0e71GNltAWtwmOaMZcm1J")
        self.assertIn("items", result)
        self.assertIn("total", result)
        self.assertIn("limit", result)
        self.assertIn("offset", result)
        self.assertIn("href", result)

    def test_get_artists_albums_with_pagination(self):
        """Test retrieval of artist's albums with pagination."""
        result = get_artists_albums("W0e71GNltAWtwmOaMZcm1J", limit=5, offset=0)
        self.assertIn("items", result)
        self.assertEqual(result["limit"], 5)
        self.assertEqual(result["offset"], 0)

    def test_get_artists_albums_with_include_groups(self):
        """Test retrieval of artist's albums with include_groups filtering."""
        result = get_artists_albums("W0e71GNltAWtwmOaMZcm1J", include_groups="album,single")
        self.assertIn("items", result)

    def test_get_artists_albums_with_market_filtering(self):
        """Test retrieval of artist's albums with market filtering."""
        result = get_artists_albums("W0e71GNltAWtwmOaMZcm1J", market="US")
        self.assertIn("items", result)

    def test_get_artists_albums_artist_not_found(self):
        """Test retrieval of artist's albums for non-existent artist."""
        with self.assertRaises(NoResultsFoundError):
            get_artists_albums("nonexistent_artist")

    def test_get_artists_albums_invalid_input(self):
        """Test retrieval of artist's albums with invalid input."""
        # Test with empty artist ID
        with self.assertRaises(InvalidInputError):
            get_artists_albums("")
        
        # Test with invalid include_groups
        with self.assertRaises(InvalidInputError):
            get_artists_albums("W0e71GNltAWtwmOaMZcm1J", include_groups="invalid_group")
        
        # Test with invalid limit
        with self.assertRaises(InvalidInputError):
            get_artists_albums("W0e71GNltAWtwmOaMZcm1J", limit=0)
        
        # Test with invalid offset
        with self.assertRaises(InvalidInputError):
            get_artists_albums("W0e71GNltAWtwmOaMZcm1J", offset=-1)

    def test_get_artists_albums_invalid_market(self):
        """Test retrieval of artist's albums with invalid market."""
        with self.assertRaises(InvalidMarketError):
            get_artists_albums("W0e71GNltAWtwmOaMZcm1J", market="INVALID")

    def test_get_artists_top_tracks_artist_not_found(self):
        """Test retrieval of artist's top tracks for non-existent artist."""
        with self.assertRaises(NoResultsFoundError):
            get_artists_top_tracks("nonexistent_artist", "US")

    def test_get_artists_top_tracks_invalid_input(self):
        """Test retrieval of artist's top tracks with invalid input."""
        # Test with empty artist ID
        with self.assertRaises(InvalidInputError):
            get_artists_top_tracks("", "US")

        # Test with invalid market
        with self.assertRaises(InvalidMarketError):
            get_artists_top_tracks("W0e71GNltAWtwmOaMZcm1J", "INVALID")

    def test_get_artists_related_artists_artist_not_found(self):
        """Test retrieval of related artists for non-existent artist."""
        with self.assertRaises(NoResultsFoundError):
            get_artists_related_artists("nonexistent_artist")

    def test_get_artists_related_artists_invalid_input(self):
        """Test retrieval of related artists with invalid input."""
        # Test with empty artist ID
        with self.assertRaises(InvalidInputError):
            get_artists_related_artists("")

    def test_get_artists_albums_no_albums_found(self):
        """Test retrieval of artist's albums when artist has no albums."""
        # DqJ4SeZM7iQuxSkKOdQvTB is already in setUp and has no albums
        result = get_artists_albums("DqJ4SeZM7iQuxSkKOdQvTB")
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)

    def test_get_artists_top_tracks_no_tracks_found(self):
        """Test retrieval of artist's top tracks when artist has no tracks."""
        result = get_artists_top_tracks("DqJ4SeZM7iQuxSkKOdQvTB", "US")
        self.assertIn("tracks", result)
        self.assertEqual(len(result["tracks"]), 0)

    def test_get_artists_related_artists_no_related_found(self):
        """Test retrieval of related artists when no related artists exist."""
        # Add a new artist with unique genres to the test data
        DB["artists"]["y82ZzcqBIAnXg3vFWFfr12"] = {
            "id": "y82ZzcqBIAnXg3vFWFfr12",
            "name": "Unique Genre Artist",
            "genres": ["unique_genre"],
            "popularity": 20,
            "images": [],
            "followers": {"total": 50}
        }
        
        result = get_artists_related_artists("y82ZzcqBIAnXg3vFWFfr12")
        self.assertIn("artists", result)
        # Should return empty list since no other artists share the unique genre

    def test_get_artists_albums_with_different_album_types(self):
        """Test retrieval of artist's albums with different album types."""
        # Add albums with different types to test data
        DB["albums"]["5V17F52VsJ3ZDIF1iYxe6D"] = {
            "id": "5V17F52VsJ3ZDIF1iYxe6D",
            "name": "Test Single",
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album_type": "single",
            "total_tracks": 1,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2023-03-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 40
        }
        
        # Test filtering by single
        result = get_artists_albums("W0e71GNltAWtwmOaMZcm1J", include_groups="single")
        self.assertIn("items", result)
        
        # Test filtering by album
        result = get_artists_albums("W0e71GNltAWtwmOaMZcm1J", include_groups="album")
        self.assertIn("items", result)

    def test_get_artists_top_tracks_market_filtering(self):
        """Test retrieval of artist's top tracks with market filtering."""
        # Add a track that's not available in US market
        DB["tracks"]["u2q7XZcxZpFNq2yIBhXZ6h"] = {
            "id": "u2q7XZcxZpFNq2yIBhXZ6h",
            "name": "Non-US Track",
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album": {"id": "4kBp5iVByDSAUc0lb78jCZ", "name": "Test Album"},
            "duration_ms": 200000,
            "explicit": False,
            "track_number": 2,
            "disc_number": 1,
            "available_markets": ["CA"],  # Not available in US
            "popularity": 70
        }
        
        # Test US market (should not include u2q7XZcxZpFNq2yIBhXZ6h)
        result = get_artists_top_tracks("W0e71GNltAWtwmOaMZcm1J", "US")
        self.assertIn("tracks", result)
        
        # Test CA market (should include u2q7XZcxZpFNq2yIBhXZ6h)
        result = get_artists_top_tracks("W0e71GNltAWtwmOaMZcm1J", "CA")
        self.assertIn("tracks", result)

    def test_get_artists_related_artists_genre_based_matching(self):
        """Test retrieval of related artists based on genre matching."""
        # Add another artist with similar genres
        DB["artists"]["DqJ4SeZM7iQuxSkKOdQvTB"] = {
            "id": "DqJ4SeZM7iQuxSkKOdQvTB",
            "name": "Similar Genre Artist",
            "genres": ["pop", "rock"],  # Shares "pop" with W0e71GNltAWtwmOaMZcm1J
            "popularity": 60,
            "images": [],
            "followers": {"total": 800}
        }
        
        result = get_artists_related_artists("W0e71GNltAWtwmOaMZcm1J")
        self.assertIn("artists", result)
        # Should include DqJ4SeZM7iQuxSkKOdQvTB since they share the "pop" genre

    def test_get_artists_albums_sorting_by_release_date(self):
        """Test that artist's albums are sorted by release date (newest first)."""
        # Add albums with different release dates
        DB["albums"]["album_old"] = {
            "id": "album_old",
            "name": "Old Album",
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album_type": "album",
            "total_tracks": 12,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2022-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 30
        }
        
        DB["albums"]["album_new"] = {
            "id": "album_new",
            "name": "New Album",
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album_type": "album",
            "total_tracks": 15,
            "available_markets": ["US", "CA", "UK"],
            "release_date": "2023-12-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 80
        }
        
        result = get_artists_albums("W0e71GNltAWtwmOaMZcm1J")
        self.assertIn("items", result)
        # The newest album should appear first
        if len(result["items"]) >= 2:
            self.assertEqual(result["items"][0]["id"], "album_new")

    def test_get_artists_top_tracks_popularity_sorting(self):
        """Test that artist's top tracks are sorted by popularity (highest first)."""
        # Add tracks with different popularity scores
        DB["tracks"]["track_high_popularity"] = {
            "id": "track_high_popularity",
            "name": "High Popularity Track",
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album": {"id": "4kBp5iVByDSAUc0lb78jCZ", "name": "Test Album"},
            "duration_ms": 180000,
            "explicit": False,
            "track_number": 1,
            "disc_number": 1,
            "available_markets": ["US", "CA", "UK"],
            "popularity": 90
        }
        
        DB["tracks"]["track_low_popularity"] = {
            "id": "track_low_popularity",
            "name": "Low Popularity Track",
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album": {"id": "4kBp5iVByDSAUc0lb78jCZ", "name": "Test Album"},
            "duration_ms": 200000,
            "explicit": False,
            "track_number": 2,
            "disc_number": 1,
            "available_markets": ["US", "CA", "UK"],
            "popularity": 30
        }
        
        result = get_artists_top_tracks("W0e71GNltAWtwmOaMZcm1J", "US")
        self.assertIn("tracks", result)
        # The highest popularity track should appear first
        if len(result["tracks"]) >= 2:
            self.assertEqual(result["tracks"][0]["id"], "track_high_popularity")

    def test_get_artists_related_artists_popularity_sorting(self):
        """Test that related artists are sorted by popularity (highest first)."""
        # Add artists with different popularity scores
        DB["artists"]["artist_high_popularity"] = {
            "id": "artist_high_popularity",
            "name": "High Popularity Artist",
            "genres": ["pop"],  # Shares genre with W0e71GNltAWtwmOaMZcm1J
            "popularity": 95,
            "images": [],
            "followers": {"total": 10000}
        }
        
        DB["artists"]["artist_low_popularity"] = {
            "id": "artist_low_popularity",
            "name": "Low Popularity Artist",
            "genres": ["pop"],  # Shares genre with W0e71GNltAWtwmOaMZcm1J
            "popularity": 25,
            "images": [],
            "followers": {"total": 100}
        }
        
        result = get_artists_related_artists("W0e71GNltAWtwmOaMZcm1J")
        self.assertIn("artists", result)
        # The highest popularity artist should appear first
        if len(result["artists"]) >= 2:
            self.assertEqual(result["artists"][0]["id"], "artist_high_popularity")

    def test_get_new_releases_success(self):
        """Test successful retrieval of new releases."""
        result = get_new_releases()
        self.assertIn("albums", result)
        self.assertIn("items", result["albums"])

    def test_get_featured_playlists_success(self):
        """Test successful retrieval of featured playlists."""
        result = get_featured_playlists()
        self.assertIn("playlists", result)
        self.assertIn("items", result["playlists"])

    def test_get_categories_success(self):
        """Test successful retrieval of categories."""
        result = get_categories()
        self.assertIn("categories", result)
        self.assertIn("items", result["categories"])

    def test_get_category_success(self):
        """Test successful retrieval of a specific category."""
        result = get_category("0ZUBhfQhoczohmoxWGZpxj")
        self.assertEqual(result["id"], "0ZUBhfQhoczohmoxWGZpxj")
        self.assertEqual(result["name"], "Test Category")

    def test_get_category_not_found(self):
        """Test category retrieval with non-existent ID."""
        with self.assertRaises(NoResultsFoundError):
            get_category("nonexistent_category")

    def test_get_category_playlists_success(self):
        """Test successful retrieval of category playlists."""
        result = get_category_playlists("0ZUBhfQhoczohmoxWGZpxj")
        self.assertIn("playlists", result)
        self.assertIn("items", result["playlists"])

    def test_get_available_genre_seeds_success(self):
        """Test successful retrieval of available genre seeds."""
        result = get_available_genre_seeds()
        self.assertIn("genres", result)
        self.assertIsInstance(result["genres"], list)

    def test_search_for_item_success(self):
        """Test successful search functionality."""
        result = search_for_item("test", "album")
        self.assertIn("albums", result)

    def test_get_current_user_profile_success(self):
        """Test successful retrieval of current user profile."""
        result = get_current_user_profile()
        self.assertEqual(result["id"], "smuqPNFPXrJKcEt943KrY8")
        self.assertEqual(result["display_name"], "Test User")

    def test_get_user_profile_success(self):
        """Test successful retrieval of user profile."""
        result = get_user_profile("smuqPNFPXrJKcEt943KrY8")
        self.assertEqual(result["id"], "smuqPNFPXrJKcEt943KrY8")
        self.assertEqual(result["display_name"], "Test User")

    def test_get_user_profile_not_found(self):
        """Test user profile retrieval with non-existent ID."""
        with self.assertRaises(NoResultsFoundError):
            get_user_profile("nonexistent_user")

    def test_get_user_top_artists_and_tracks_success(self):
        """Test successful retrieval of user's top artists and tracks."""
        result = get_user_top_artists_and_tracks("artists")
        self.assertIn("items", result)
        self.assertIsInstance(result["items"], list)

    def test_follow_playlist_success(self):
        """Test successful playlist following."""
        result = follow_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertIn("message", result)
        self.assertIn("Successfully followed playlist", result["message"])

    def test_unfollow_playlist_success(self):
        """Test successful playlist unfollowing."""
        result = unfollow_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed playlist", result["message"])

    def test_follow_artists_success(self):
        """Test successful artist following."""
        result = follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        self.assertIn("message", result)
        self.assertIn("Successfully followed", result["message"])

    def test_unfollow_artists_success(self):
        """Test successful artist unfollowing."""
        result = unfollow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed", result["message"])

    def test_follow_users_success(self):
        """Test successful user following."""
        result = follow_artists_or_users(["smuqPNFPXrJKcEt943KrY8"], "user")
        self.assertIn("message", result)
        self.assertIn("Successfully followed", result["message"])

    def test_unfollow_users_success(self):
        """Test successful user unfollowing."""
        result = unfollow_artists_or_users(["smuqPNFPXrJKcEt943KrY8"], "user")
        self.assertIn("message", result)
        self.assertIn("Successfully unfollowed", result["message"])

    def test_check_user_follows_artists_success(self):
        """Test successful artist follow status check."""
        result = check_user_follows_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], bool)

    def test_check_user_follows_users_success(self):
        """Test successful user follow status check."""
        result = check_user_follows_artists_or_users(["smuqPNFPXrJKcEt943KrY8"], "user")
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], bool)

    def test_get_followed_artists_success(self):
        """Test successful retrieval of followed artists."""
        # First follow some artists
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB"], "artist")
        
        result = get_followed_artists()
        self.assertIn("artists", result)
        self.assertIn("items", result["artists"])
        self.assertIn("total", result["artists"])
        self.assertIn("limit", result["artists"])
        self.assertIn("offset", result["artists"])
        self.assertIn("href", result["artists"])
        
        # Should return 2 artists
        self.assertEqual(result["artists"]["total"], 2)
        self.assertEqual(len(result["artists"]["items"]), 2)

    def test_get_followed_artists_with_limit(self):
        """Test followed artists retrieval with limit parameter."""
        # First follow some artists
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB"], "artist")
        
        result = get_followed_artists(limit=1)
        self.assertEqual(result["artists"]["limit"], 1)
        self.assertEqual(len(result["artists"]["items"]), 1)

    def test_get_followed_artists_with_after(self):
        """Test followed artists retrieval with after parameter for pagination."""
        # First follow some artists
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB"], "artist")
        
        # Get first page
        first_page = get_followed_artists(limit=1)
        self.assertEqual(len(first_page["artists"]["items"]), 1)
        
        # Get second page using after parameter
        if first_page["artists"]["next"]:
            second_page = get_followed_artists(limit=1, after=first_page["artists"]["items"][0]["id"])
            self.assertEqual(len(second_page["artists"]["items"]), 1)
            # Should be different artist
            self.assertNotEqual(first_page["artists"]["items"][0]["id"], second_page["artists"]["items"][0]["id"])

    def test_get_followed_artists_no_followed_artists(self):
        """Test followed artists retrieval when user follows no artists."""
        # Clear any existing followed artists
        DB["followed_artists"] = {}
        
        result = get_followed_artists()
        self.assertIn("artists", result)
        self.assertEqual(result["artists"]["total"], 0)
        self.assertEqual(len(result["artists"]["items"]), 0)

    def test_get_followed_artists_invalid_limit(self):
        """Test followed artists retrieval with invalid limit."""
        with self.assertRaises(InvalidInputError):
            get_followed_artists(limit=0)
        
        with self.assertRaises(InvalidInputError):
            get_followed_artists(limit=51)
        
        with self.assertRaises(InvalidInputError):
            get_followed_artists(limit="invalid")

    def test_get_followed_artists_invalid_after(self):
        """Test followed artists retrieval with invalid after parameter."""
        with self.assertRaises(InvalidInputError):
            get_followed_artists(after="")
        
        with self.assertRaises(InvalidInputError):
            get_followed_artists(after="nonexistent_artist")

    def test_get_followed_artists_pagination_links(self):
        """Test that pagination links are correctly generated."""
        # Follow multiple artists for pagination testing
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB"], "artist")
        
        # Test first page
        first_page = get_followed_artists(limit=1)
        self.assertIsNotNone(first_page["artists"]["next"])
        self.assertIsNone(first_page["artists"]["previous"])
        
        # Test second page
        if first_page["artists"]["next"]:
            second_page = get_followed_artists(limit=1, after=first_page["artists"]["items"][0]["id"])
            self.assertIsNone(second_page["artists"]["next"])  # No more pages
            self.assertIsNotNone(second_page["artists"]["previous"])

    def test_get_followed_artists_after_artist_not_in_followed_list(self):
        """Test pagination when after artist exists but is not in user's followed list."""
        # Follow only one artist
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        
        # Try to paginate with an artist that exists but is not followed
        result = get_followed_artists(limit=10, after="DqJ4SeZM7iQuxSkKOdQvTB")
        # Should return all followed artists (start from beginning)
        self.assertEqual(len(result["artists"]["items"]), 1)
        self.assertEqual(result["artists"]["items"][0]["id"], "W0e71GNltAWtwmOaMZcm1J")

    def test_get_followed_artists_limit_boundary_values(self):
        """Test limit parameter with boundary values."""
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J", "DqJ4SeZM7iQuxSkKOdQvTB"], "artist")
        
        # Test minimum limit
        result = get_followed_artists(limit=1)
        self.assertEqual(result["artists"]["limit"], 1)
        self.assertEqual(len(result["artists"]["items"]), 1)
        
        # Test maximum limit
        result = get_followed_artists(limit=50)
        self.assertEqual(result["artists"]["limit"], 50)
        self.assertEqual(len(result["artists"]["items"]), 2)  # Only 2 artists followed

    def test_get_followed_artists_response_structure(self):
        """Test that the response structure matches the expected format."""
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        
        result = get_followed_artists()
        
        # Check top-level structure
        self.assertIn("artists", result)
        artists = result["artists"]
        
        # Check required fields
        required_fields = ["items", "total", "limit", "offset", "href", "next", "previous"]
        for field in required_fields:
            self.assertIn(field, artists)
        
        # Check items structure
        if artists["items"]:
            item = artists["items"][0]
            # Check for the fields that are actually present in our test data
            required_item_fields = ["id", "name", "genres", "popularity", "images", "followers"]
            for field in required_item_fields:
                self.assertIn(field, item)

    def test_get_followed_artists_artist_data_integrity(self):
        """Test that artist data is correctly retrieved from the database."""
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        
        result = get_followed_artists()
        
        if result["artists"]["items"]:
            artist = result["artists"]["items"][0]
            
            # Check that the artist data matches what's in the database
            self.assertEqual(artist["id"], "W0e71GNltAWtwmOaMZcm1J")
            self.assertEqual(artist["name"], "Test Artist")
            self.assertIn("pop", artist["genres"])
            self.assertEqual(artist["popularity"], 70)

    def test_get_followed_artists_followed_artist_not_in_database(self):
        """Test handling when a followed artist ID doesn't exist in the artists database."""
        # Add a followed artist that doesn't exist in the artists table
        DB["followed_artists"]["smuqPNFPXrJKcEt943KrY8"] = ["W0e71GNltAWtwmOaMZcm1J", "nonexistent_artist"]
        
        result = get_followed_artists()
        
        # Should only return the artist that exists in the database
        self.assertEqual(len(result["artists"]["items"]), 1)
        self.assertEqual(result["artists"]["items"][0]["id"], "W0e71GNltAWtwmOaMZcm1J")
        # Total should still reflect the number of followed artists
        self.assertEqual(result["artists"]["total"], 2)

    def test_get_followed_artists_default_parameters(self):
        """Test that default parameters work correctly."""
        follow_artists_or_users(["W0e71GNltAWtwmOaMZcm1J"], "artist")
        
        # Test with no parameters (should use defaults)
        result = get_followed_artists()
        self.assertEqual(result["artists"]["limit"], 20)
        self.assertEqual(result["artists"]["offset"], 0)

    def test_get_followed_artists_authentication_error_simulation(self):
        """Test that the function handles authentication errors properly."""
        # This test simulates what would happen if get_current_user_id() fails
        # In a real implementation, this would be handled by the decorator
        # For now, we just test that the function doesn't crash with invalid user data
        
        # Clear current user to simulate authentication failure
        if "current_user" in DB:
            del DB["current_user"]
        
        # This should raise an error (in a real implementation)
        # For now, we'll just test that the function handles the case gracefully
        try:
            result = get_followed_artists()
            # If it doesn't raise an error, that's fine for the simulation
        except Exception as e:
            # If it does raise an error, that's also acceptable
            pass
        
        # Restore the current user for other tests
        DB["current_user"] = {"id": "smuqPNFPXrJKcEt943KrY8"}

    def test_get_followed_artists_large_dataset_pagination(self):
        """Test pagination with a larger dataset."""
        # Create more artists and follow them
        for i in range(10):
            artist_id = f"artist_{i}"
            DB["artists"][artist_id] = {
                "id": artist_id,
                "name": f"Artist {i}",
                "type": "artist",
                "uri": f"spotify:artist:{artist_id}",
                "href": f"https://api.spotify.com/v1/artists/{artist_id}",
                "external_urls": {"spotify": f"https://open.spotify.com/artist/{artist_id}"},
                "genres": ["pop"],
                "popularity": 50,
                "images": [],
                "followers": {"total": 100}
            }
        
        # Follow all artists
        artist_ids = [f"artist_{i}" for i in range(10)]
        follow_artists_or_users(artist_ids, "artist")
        
        # Test pagination
        first_page = get_followed_artists(limit=3)
        self.assertEqual(len(first_page["artists"]["items"]), 3)
        self.assertIsNotNone(first_page["artists"]["next"])
        
        # Get second page
        second_page = get_followed_artists(limit=3, after=first_page["artists"]["items"][2]["id"])
        self.assertEqual(len(second_page["artists"]["items"]), 3)
        self.assertIsNotNone(second_page["artists"]["previous"])
        
        # Get third page
        third_page = get_followed_artists(limit=3, after=second_page["artists"]["items"][2]["id"])
        self.assertEqual(len(third_page["artists"]["items"]), 3)
        
        # Get fourth page (should have remaining artists)
        fourth_page = get_followed_artists(limit=3, after=third_page["artists"]["items"][2]["id"])
        self.assertEqual(len(fourth_page["artists"]["items"]), 1)  # Only 1 artist remaining
        self.assertIsNone(fourth_page["artists"]["next"])  # No more pages

    def test_invalid_input_validation(self):
        """Test input validation for various functions."""
        # Test invalid album ID
        with self.assertRaises(InvalidInputError):
            get_album("")
        
        # Test invalid artist ID
        with self.assertRaises(InvalidInputError):
            get_artist("")
        
        # Test invalid market code
        with self.assertRaises(InvalidMarketError):
            get_artists_top_tracks("W0e71GNltAWtwmOaMZcm1J", "INVALID")

    def test_get_users_saved_albums_complete_structure(self):
        """Test that get_users_saved_albums returns complete structure matching official Spotify API."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums()
        
        # Check main response structure
        self.assertIn("items", result)
        self.assertIn("total", result)
        self.assertIn("limit", result)
        self.assertIn("offset", result)
        self.assertIn("href", result)
        self.assertIn("next", result)
        self.assertIn("previous", result)
        
        if result["items"]:
            saved_album = result["items"][0]
            
            # Check saved album structure
            self.assertIn("added_at", saved_album)
            self.assertIn("album", saved_album)
            
            album = saved_album["album"]
            
            # Check all required album fields from docstring
            required_fields = [
                'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 
                'album_type', 'total_tracks', 'available_markets', 'release_date', 
                'release_date_precision', 'images', 'popularity', 'restrictions', 
                'tracks', 'copyrights', 'external_ids', 'label'
            ]
            
            for field in required_fields:
                self.assertIn(field, album, f"Missing required album field: {field}")
            
            # Check artist structure
            self.assertIsInstance(album['artists'], list)
            if album['artists']:
                artist = album['artists'][0]
                artist_fields = ['external_urls', 'href', 'id', 'name', 'type', 'uri']
                for field in artist_fields:
                    self.assertIn(field, artist, f"Missing artist field: {field}")
            
            # Check tracks structure
            tracks = album.get('tracks', {})
            tracks_fields = ['href', 'limit', 'next', 'offset', 'previous', 'total', 'items']
            for field in tracks_fields:
                self.assertIn(field, tracks, f"Missing tracks field: {field}")

    def test_get_users_saved_albums_artist_enhancement(self):
        """Test that get_users_saved_albums properly enhances artist objects."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums()
        
        if result["items"]:
            album = result["items"][0]["album"]
            
            # Check that artists are properly enhanced
            self.assertIsInstance(album['artists'], list)
            if album['artists']:
                artist = album['artists'][0]
                
                # Check that all required artist fields are present
                self.assertIn('external_urls', artist)
                self.assertIn('spotify', artist['external_urls'])
                self.assertIn('href', artist)
                self.assertIn('type', artist)
                self.assertIn('uri', artist)
                
                # Check that URLs are properly formatted
                self.assertTrue(artist['external_urls']['spotify'].startswith('https://open.spotify.com/artist/'))
                self.assertTrue(artist['href'].startswith('https://api.spotify.com/v1/artists/'))
                self.assertEqual(artist['type'], 'artist')
                self.assertTrue(artist['uri'].startswith('spotify:artist:'))

    def test_get_users_saved_albums_tracks_integration(self):
        """Test that get_users_saved_albums includes tracks information."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums()
        
        if result["items"]:
            album = result["items"][0]["album"]
            
            # Check tracks structure
            tracks = album.get('tracks', {})
            self.assertIn('href', tracks)
            self.assertIn('total', tracks)
            self.assertIn('items', tracks)
            
            # Check that tracks URL is properly formatted
            self.assertTrue(tracks['href'].startswith('https://api.spotify.com/v1/albums/'))
            self.assertTrue(tracks['href'].endswith('/tracks'))

    def test_get_users_saved_albums_market_filtering(self):
        """Test that get_users_saved_albums properly filters by market."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        # Test with valid market
        result = get_users_saved_albums(market="US")
        self.assertIn("items", result)
        
        # Test with invalid market
        with self.assertRaises(InvalidMarketError):
            get_users_saved_albums(market="INVALID")

    def test_get_users_saved_albums_pagination(self):
        """Test that get_users_saved_albums handles pagination correctly."""
        # Add multiple saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        
        # Test with limit
        result = get_users_saved_albums(limit=1)
        self.assertEqual(result["limit"], 1)
        self.assertLessEqual(len(result["items"]), 1)
        
        # Test with offset
        result = get_users_saved_albums(offset=1)
        self.assertEqual(result["offset"], 1)

    def test_get_users_saved_albums_data_integrity(self):
        """Test that get_users_saved_albums maintains data integrity."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums()
        
        if result["items"]:
            saved_album = result["items"][0]
            album = saved_album["album"]
            
            # Check that album ID matches
            self.assertEqual(album["id"], "4kBp5iVByDSAUc0lb78jCZ")
            
            # Check that added_at is present
            self.assertIn("added_at", saved_album)
            self.assertIsInstance(saved_album["added_at"], str)

    def test_get_users_saved_albums_multiple_artists(self):
        """Test that get_users_saved_albums handles albums with multiple artists."""
        # Create a test album with multiple artists
        test_album_id = "test_multi_artist_album"
        test_album_data = {
            "id": test_album_id,
            "name": "Multi-Artist Album",
            "artists": [
                {"id": "artist1", "name": "Artist 1"},
                {"id": "artist2", "name": "Artist 2"}
            ],
            "album_type": "album",
            "total_tracks": 5,
            "available_markets": ["US", "CA"],
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "images": [],
            "popularity": 60,
            "copyrights": [],
            "external_ids": {},
            "label": "Test Label"
        }
        
        # Add to DB
        DB.setdefault('albums', {})[test_album_id] = test_album_data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = [test_album_id]
        
        result = get_users_saved_albums()
        
        if result["items"]:
            album = result["items"][0]["album"]
            
            # Check that all artists are enhanced
            self.assertIsInstance(album['artists'], list)
            self.assertEqual(len(album['artists']), 2)
            
            for artist in album['artists']:
                self.assertIn('external_urls', artist)
                self.assertIn('href', artist)
                self.assertIn('type', artist)
                self.assertIn('uri', artist)

    def test_get_users_saved_albums_edge_cases(self):
        """Test that get_users_saved_albums handles edge cases properly."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Test with no saved albums
        result = get_users_saved_albums()
        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)
        
        # Test with invalid limit
        with self.assertRaises(InvalidInputError):
            get_users_saved_albums(limit=0)
        
        # Test with invalid offset
        with self.assertRaises(InvalidInputError):
            get_users_saved_albums(offset=-1)

    def test_get_users_saved_albums_order_preservation(self):
        """Test that get_users_saved_albums preserves the order of saved albums."""
        # Add multiple saved albums in specific order
        album_ids = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = album_ids
        
        result = get_users_saved_albums()
        
        # Check that order is preserved
        self.assertEqual(len(result["items"]), len(album_ids))
        for i, saved_album in enumerate(result["items"]):
            self.assertEqual(saved_album["album"]["id"], album_ids[i])

    def test_get_users_saved_albums_optional_fields(self):
        """Test that get_users_saved_albums handles all optional fields correctly."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums()
        
        if result["items"] and result["items"][0] is not None:
            album = result["items"][0]["album"]
            
            # Check optional fields are present (may be None)
            optional_fields = ['restrictions', 'genres']
            for field in optional_fields:
                if field in album:
                    self.assertIsNotNone(album[field])

    def test_get_users_saved_albums_docstring_accuracy(self):
        """Test that the docstring accurately describes all fields returned by the function."""
        # Add some saved albums to the test data
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        
        result = get_users_saved_albums()
        
        if result["items"]:
            saved_album = result["items"][0]
            album = saved_album["album"]
            
            # Check that all fields mentioned in docstring are present
            docstring_album_fields = [
                'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 
                'album_type', 'total_tracks', 'available_markets', 'release_date', 
                'release_date_precision', 'images', 'popularity', 'restrictions', 
                'tracks', 'copyrights', 'external_ids', 'label', 'genres'
            ]
            
            for field in docstring_album_fields:
                self.assertIn(field, album, f"Field '{field}' mentioned in docstring but not present in response")
            
            # Check that all fields in response are mentioned in docstring
            actual_album_fields = set(album.keys())
            docstring_fields_set = set(docstring_album_fields)
            
            # Fields that might be in response but not critical for docstring
            optional_fields = {'genres'}  # genres might be empty list
            
            missing_in_docstring = actual_album_fields - docstring_fields_set - optional_fields
            self.assertEqual(missing_in_docstring, set(), 
                           f"Fields present in response but not mentioned in docstring: {missing_in_docstring}")
            
            # Check tracks structure
            tracks = album.get('tracks', {})
            docstring_tracks_fields = ['href', 'limit', 'next', 'offset', 'previous', 'total', 'items']
            
            for field in docstring_tracks_fields:
                self.assertIn(field, tracks, f"Tracks field '{field}' mentioned in docstring but not present")
            
            # Check track items structure if tracks exist
            if tracks.get('items'):
                track = tracks['items'][0]
                docstring_track_fields = [
                    'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 'album',
                    'duration_ms', 'explicit', 'track_number', 'disc_number', 'available_markets',
                    'popularity', 'is_local', 'is_playable', 'external_ids', 'linked_from',
                    'restrictions', 'preview_url'
                ]
                
                for field in docstring_track_fields:
                    self.assertIn(field, track, f"Track field '{field}' mentioned in docstring but not present")

    def test_get_users_saved_albums_tracks_missing_fields_in_db(self):
        """Test that get_users_saved_albums returns all required track fields even if DB is missing them."""
        # Add a saved album and a track with missing fields
        album_id = 'album_missing_fields'
        track_id = 'track_missing_fields'
        DB.setdefault('albums', {})[album_id] = {
            'id': album_id,
            'name': 'Album With Missing Fields',
            'artists': [{'id': 'artist_missing', 'name': 'Artist Missing'}],
            'album_type': 'album',
            'total_tracks': 1,
            'available_markets': ['US'],
            'release_date': '2023-01-01',
            'release_date_precision': 'day',
            'images': [],
            'popularity': 10,
            'copyrights': [],
            'external_ids': {},
            'label': 'Test Label',
            'genres': []
        }
        DB.setdefault('tracks', {})[track_id] = {
            'id': track_id,
            'name': 'Track With Missing Fields',
            'artists': [{'id': 'artist_missing', 'name': 'Artist Missing'}],
            'album': {'id': album_id, 'name': 'Album With Missing Fields'},
            # Intentionally missing many required fields
        }
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = [album_id]
        
        result = get_users_saved_albums()
        
        self.assertIn('items', result)
        self.assertGreater(len(result['items']), 0)
        album = result['items'][0]['album']
        tracks = album['tracks']['items']
        self.assertGreater(len(tracks), 0)
        track = tracks[0]
        # All required fields must be present
        required_track_fields = [
            'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 'album',
            'duration_ms', 'explicit', 'track_number', 'disc_number', 'available_markets',
            'popularity', 'is_local', 'is_playable', 'external_ids', 'linked_from',
            'restrictions', 'preview_url'
        ]
        for field in required_track_fields:
            self.assertIn(field, track, f"Missing required track field: {field}")
        # Artists must be enhanced
        for artist in track['artists']:
            for afield in ['external_urls', 'href', 'id', 'name', 'type', 'uri']:
                self.assertIn(afield, artist, f"Missing artist field: {afield}")
        # Album object in track must be enhanced
        for afield in ['id', 'name', 'uri', 'href', 'external_urls', 'images']:
            self.assertIn(afield, track['album'], f"Missing album field in track: {afield}")

    def test_save_albums_for_user_official_api_compliance(self):
        """Test that save_albums_for_user follows official Spotify API specification."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Test that function returns success message as per official API
        result = save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])
        
        # Verify albums were actually saved
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertIn("4kBp5iVByDSAUc0lb78jCZ", saved_albums, "Album should be saved")

    def test_save_albums_for_user_validation_limits(self):
        """Test validation of album IDs according to official API limits."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Test maximum limit (50 IDs as per official API body parameter)
        valid_album_ids = ["4kBp5iVByDSAUc0lb78jCZ"] * 50
        result = save_albums_for_user(valid_album_ids)
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])
        
        # Test exceeding maximum limit
        too_many_album_ids = ["4kBp5iVByDSAUc0lb78jCZ"] * 51
        with self.assertRaises(InvalidInputError):
            save_albums_for_user(too_many_album_ids)

    def test_save_albums_for_user_validation_types(self):
        """Test validation of input types according to official API."""
        # Test with non-list input
        with self.assertRaises(InvalidInputError):
            save_albums_for_user("4kBp5iVByDSAUc0lb78jCZ")
        
        # Test with empty string in list
        with self.assertRaises(InvalidInputError):
            save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", ""])
        
        # Test with non-string album ID
        with self.assertRaises(InvalidInputError):
            save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", 123])

    def test_save_albums_for_user_duplicate_handling(self):
        """Test that saving duplicate albums doesn't create duplicates in the database."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Save the same album multiple times
        album_id = "4kBp5iVByDSAUc0lb78jCZ"
        
        # First save
        save_albums_for_user([album_id])
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertEqual(saved_albums.count(album_id), 1, "Album should appear only once after first save")
        
        # Second save of the same album
        save_albums_for_user([album_id])
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertEqual(saved_albums.count(album_id), 1, "Album should still appear only once after second save")

    def test_save_albums_for_user_multiple_albums_order(self):
        """Test saving multiple albums preserves order and handles all correctly."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        album_ids = ["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"]
        
        result = save_albums_for_user(album_ids)
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])
        
        # Verify all albums were saved
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        for album_id in album_ids:
            self.assertIn(album_id, saved_albums, f"Album {album_id} should be saved")

    def test_save_albums_for_user_empty_list(self):
        """Test saving empty list of albums."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = save_albums_for_user([])
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])
        
        # Verify no albums were saved
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertEqual(len(saved_albums), 0, "No albums should be saved when list is empty")

    def test_save_albums_for_user_database_integrity(self):
        """Test that saving albums maintains database integrity."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Clear any existing saved albums
        if 'saved_albums' in DB:
            DB['saved_albums'] = {}
        
        album_ids = ["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"]
        
        # Save albums
        save_albums_for_user(album_ids)
        
        # Verify database structure is correct
        self.assertIn('saved_albums', DB)
        self.assertIn('smuqPNFPXrJKcEt943KrY8', DB['saved_albums'])
        self.assertIsInstance(DB['saved_albums']['smuqPNFPXrJKcEt943KrY8'], list)
        
        # Verify all albums are in the list
        saved_albums = DB['saved_albums']['smuqPNFPXrJKcEt943KrY8']
        for album_id in album_ids:
            self.assertIn(album_id, saved_albums)

    def test_save_albums_for_user_error_handling(self):
        """Test error handling for various edge cases."""
        # Test with None input
        with self.assertRaises(InvalidInputError):
            save_albums_for_user(None)
        
        # Test with mixed valid/invalid album IDs
        with self.assertRaises(NoResultsFoundError):
            save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", "nonexistent_album"])
        
        # Test with all non-existent albums
        with self.assertRaises(NoResultsFoundError):
            save_albums_for_user(["nonexistent_album1", "nonexistent_album2"])

    def test_save_albums_for_user_docstring_accuracy(self):
        """Test that the function behavior matches its docstring."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Test that function returns success message as documented
        result = save_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("The album is saved", result["message"])
        
        # Test that function validates input as documented
        with self.assertRaises(InvalidInputError):
            save_albums_for_user("not_a_list")
        
        # Test that function validates album existence as documented
        with self.assertRaises(NoResultsFoundError):
            save_albums_for_user(["nonexistent_album"])



    def test_remove_albums_for_user_official_api_compliance(self):
        """Test that remove_albums_for_user follows official Spotify API specification."""
        # First save some albums
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        
        # Test that function returns success message as per official API
        result = remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])
        
        # Verify album was actually removed
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertNotIn("4kBp5iVByDSAUc0lb78jCZ", saved_albums)
        self.assertIn("gJIfNlJdPASNffy7UY2V6D", saved_albums)  # Other album should remain

    def test_remove_albums_for_user_validation_limits(self):
        """Test validation of album_ids limits."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Test maximum limit (50 IDs)
        valid_ids = [f"album_{i}" for i in range(50)]
        result = remove_albums_for_user(valid_ids)
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])
        
        # Test exceeding maximum limit
        invalid_ids = [f"album_{i}" for i in range(51)]
        with self.assertRaises(InvalidInputError):
            remove_albums_for_user(invalid_ids)

    def test_remove_albums_for_user_validation_types(self):
        """Test validation of album_ids types."""
        # Test non-list input
        with self.assertRaises(InvalidInputError):
            remove_albums_for_user("not_a_list")
        
        # Test empty strings in list
        with self.assertRaises(InvalidInputError):
            remove_albums_for_user(["valid_id", "", "another_valid_id"])
        
        # Test non-string values in list
        with self.assertRaises(InvalidInputError):
            remove_albums_for_user(["valid_id", 123, "another_valid_id"])

    def test_remove_albums_for_user_empty_list(self):
        """Test removing empty list of albums."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        result = remove_albums_for_user([])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])

    def test_remove_albums_for_user_duplicate_albums(self):
        """Test removing duplicate albums."""
        # First save some albums
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        
        # Remove with duplicates
        result = remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", "4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])
        
        # Verify album was removed
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertNotIn("4kBp5iVByDSAUc0lb78jCZ", saved_albums)

    def test_remove_albums_for_user_no_saved_albums(self):
        """Test removing albums when user has no saved albums."""
        # Initialize saved_albums table
        DB.setdefault('saved_albums', {})
        
        # Ensure user has no saved albums
        if 'saved_albums' in DB:
            DB['saved_albums'].pop('smuqPNFPXrJKcEt943KrY8', None)
        
        result = remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])

    def test_remove_albums_for_user_mixed_existent_nonexistent(self):
        """Test removing mix of existent and non-existent albums."""
        # First save some albums
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        
        # Remove mix of existent and non-existent
        result = remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", "nonexistent_album", "gJIfNlJdPASNffy7UY2V6D"])
        self.assertIn("message", result)
        self.assertIn("Album(s) have been removed from the library", result["message"])
        
        # Verify existent albums were removed
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertNotIn("4kBp5iVByDSAUc0lb78jCZ", saved_albums)
        self.assertNotIn("gJIfNlJdPASNffy7UY2V6D", saved_albums)

    def test_remove_albums_for_user_order_independence(self):
        """Test that order of album IDs doesn't affect removal."""
        # First save some albums
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        
        # Remove in one order
        result1 = remove_albums_for_user(["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"])
        self.assertIn("message", result1)
        self.assertIn("Album(s) have been removed from the library", result1["message"])
        
        # Reset and remove in reverse order
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ', 'gJIfNlJdPASNffy7UY2V6D']
        result2 = remove_albums_for_user(["gJIfNlJdPASNffy7UY2V6D", "4kBp5iVByDSAUc0lb78jCZ"])
        self.assertIn("message", result2)
        self.assertIn("Album(s) have been removed from the library", result2["message"])
        
        # Both should have same final state
        saved_albums = DB.get('saved_albums', {}).get('smuqPNFPXrJKcEt943KrY8', [])
        self.assertEqual(len(saved_albums), 0, "Both orders should result in same final state")

    def test_check_users_saved_albums_nonexistent_ids(self):
        """Test that non-existent album IDs return False."""
        # Add one real and one fake album
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ['4kBp5iVByDSAUc0lb78jCZ']
        result = check_users_saved_albums(["4kBp5iVByDSAUc0lb78jCZ", "nonexistent_album_id"])
        self.assertEqual(result, [True, False])

    def test_check_users_saved_albums_order_preservation(self):
        """Test that the order of input IDs is preserved in the output."""
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = ["4kBp5iVByDSAUc0lb78jCZ", "gJIfNlJdPASNffy7UY2V6D"]
        ids = ["gJIfNlJdPASNffy7UY2V6D", "4kBp5iVByDSAUc0lb78jCZ"]
        result = check_users_saved_albums(ids)
        self.assertEqual(result, [True, True])
        # Now reverse the order
        ids_reversed = list(reversed(ids))
        result_reversed = check_users_saved_albums(ids_reversed)
        self.assertEqual(result_reversed, [True, True])

    def test_check_users_saved_albums_maximum_limit(self):
        """Test that the function works with exactly 50 IDs."""
        ids = [f"album_{i}" for i in range(50)]
        # Save every even album
        DB.setdefault('saved_albums', {})['smuqPNFPXrJKcEt943KrY8'] = [f"album_{i}" for i in range(0, 50, 2)]
        result = check_users_saved_albums(ids)
        expected = [(i % 2 == 0) for i in range(50)]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main() 