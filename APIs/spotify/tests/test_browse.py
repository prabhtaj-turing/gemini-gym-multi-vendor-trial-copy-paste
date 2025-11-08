import unittest
from unittest.mock import patch, MagicMock
from typing import Optional, List

from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import (
    InvalidInputError,
    NoResultsFoundError,
    InvalidMarketError
)

# Import the functions directly from the module
from ..browse import (
    get_new_releases,
    get_featured_playlists,
    get_categories,
    get_category,
    get_category_playlists,
    get_recommendations,
    get_available_genre_seeds
)


class TestBrowseFunctions(unittest.TestCase):
    """Test cases for browse.py functions."""

    def setUp(self):
        """Set up test data before each test."""
        # Mock the DB with test data
        self.test_db = {
            'albums': {
                '4kBp5iVByDSAUc0lb78jCZ': {
                    'id': '4kBp5iVByDSAUc0lb78jCZ',
                    'name': 'Test Album',
                    'artists': [{'id': 'W0e71GNltAWtwmOaMZcm1J', 'name': 'Test Artist'}],
                    'album_type': 'album',
                    'total_tracks': 10,
                    'available_markets': ['US', 'CA'],
                    'release_date': '2023-01-01',
                    'release_date_precision': 'day',
                    'images': [],
                    'popularity': 50
                },
                'gJIfNlJdPASNffy7UY2V6D': {
                    'id': 'gJIfNlJdPASNffy7UY2V6D',
                    'name': 'Second Test Album',
                    'artists': [{'id': 'W0e71GNltAWtwmOaMZcm1J', 'name': 'Test Artist'}],
                    'album_type': 'album',
                    'total_tracks': 8,
                    'available_markets': ['US', 'CA'],
                    'release_date': '2023-02-01',
                    'release_date_precision': 'day',
                    'images': [],
                    'popularity': 40
                }
            },
            'playlists': {
                'QDyH69WryQ7dPRXVOFmy2V': {
                    'id': 'QDyH69WryQ7dPRXVOFmy2V',
                    'name': 'Test Playlist',
                    'owner': {'id': 'user_123', 'display_name': 'Test User'},
                    'public': True,
                    'collaborative': False,
                    'description': 'A test playlist',
                    'images': [],
                    'tracks': {'total': 5},
                    'followers': {'total': 100}
                }
            },
            'categories': {
                '0ZUBhfQhoczohmoxWGZpxj': {
                    'id': '0ZUBhfQhoczohmoxWGZpxj',
                    'name': 'Test Category',
                    'icons': []
                }
            },
            'tracks': {
                'WSB9PMCMqpdEBFpMrMfS3h': {
                    'id': 'WSB9PMCMqpdEBFpMrMfS3h',
                    'name': 'Test Track',
                    'artists': [{'id': 'W0e71GNltAWtwmOaMZcm1J', 'name': 'Test Artist'}],
                    'album': {'id': '4kBp5iVByDSAUc0lb78jCZ', 'name': 'Test Album'},
                    'duration_ms': 180000,
                    'explicit': False,
                    'track_number': 1,
                    'disc_number': 1,
                    'available_markets': ['US', 'CA'],
                    'popularity': 60
                }
            },
            'genres': ['acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient'],
            "current_user": {
                "id": "smuqPNFPXrJKcEt943KrY8"
            }
        }
        
        # Set up test data in DB
        DB.clear()
        DB.update(self.test_db)

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()

    def test_get_new_releases_success(self):
        """Test successful retrieval of new releases."""
        result = get_new_releases()
        
        self.assertIn('albums', result)
        self.assertIn('items', result['albums'])
        self.assertIn('total', result['albums'])
        self.assertEqual(len(result['albums']['items']), 2)

    def test_get_new_releases_with_country_filter(self):
        """Test new releases with country filtering."""
        result = get_new_releases(country='US')
        
        self.assertIn('albums', result)
        self.assertIn('items', result['albums'])
        # Should return albums available in US market
        self.assertEqual(len(result['albums']['items']), 2)

    def test_get_new_releases_with_invalid_country(self):
        """Test new releases with invalid country code."""
        with self.assertRaises(InvalidMarketError):
            get_new_releases(country='INVALID')

    def test_get_new_releases_with_pagination(self):
        """Test new releases with pagination."""
        result = get_new_releases(limit=1, offset=0)
        
        self.assertIn('albums', result)
        self.assertEqual(len(result['albums']['items']), 1)
        self.assertEqual(result['albums']['limit'], 1)
        self.assertEqual(result['albums']['offset'], 0)

    def test_get_new_releases_with_invalid_limit(self):
        """Test new releases with invalid limit."""
        with self.assertRaises(InvalidInputError):
            get_new_releases(limit=0)

    def test_get_new_releases_with_invalid_offset(self):
        """Test new releases with negative offset."""
        with self.assertRaises(InvalidInputError):
            get_new_releases(offset=-1)

    def test_get_featured_playlists_success(self):
        """Test successful retrieval of featured playlists."""
        result = get_featured_playlists()
        
        self.assertIn('playlists', result)
        self.assertIn('items', result['playlists'])
        self.assertIn('total', result['playlists'])
        self.assertEqual(len(result['playlists']['items']), 1)

    def test_get_featured_playlists_with_country(self):
        """Test featured playlists with country parameter."""
        result = get_featured_playlists(country='US')
        
        self.assertIn('playlists', result)
        self.assertIn('items', result['playlists'])

    def test_get_featured_playlists_with_locale(self):
        """Test featured playlists with locale parameter."""
        result = get_featured_playlists(locale='en_US')
        
        self.assertIn('playlists', result)
        self.assertIn('items', result['playlists'])

    def test_get_featured_playlists_with_invalid_locale(self):
        """Test featured playlists with invalid locale format."""
        with self.assertRaises(InvalidInputError):
            get_featured_playlists(locale='invalid')

    def test_get_featured_playlists_with_timestamp(self):
        """Test featured playlists with timestamp."""
        result = get_featured_playlists(timestamp='2023-01-01T09:00:00')
        
        self.assertIn('playlists', result)
        self.assertIn('items', result['playlists'])

    def test_get_featured_playlists_with_invalid_timestamp(self):
        """Test featured playlists with invalid timestamp."""
        with self.assertRaises(InvalidInputError):
            get_featured_playlists(timestamp='invalid-timestamp')

    def test_get_categories_success(self):
        """Test successful retrieval of categories."""
        result = get_categories()
        
        self.assertIn('categories', result)
        self.assertIn('items', result['categories'])
        self.assertIn('total', result['categories'])
        self.assertEqual(len(result['categories']['items']), 1)

    def test_get_categories_with_country(self):
        """Test categories with country parameter."""
        result = get_categories(country='US')
        
        self.assertIn('categories', result)
        self.assertIn('items', result['categories'])

    def test_get_categories_with_locale(self):
        """Test categories with locale parameter."""
        result = get_categories(locale='en_US')
        
        self.assertIn('categories', result)
        self.assertIn('items', result['categories'])

    def test_get_categories_with_invalid_locale(self):
        """Test categories with invalid locale format."""
        with self.assertRaises(InvalidInputError):
            get_categories(locale='invalid')

    def test_get_category_success(self):
        """Test successful retrieval of a single category."""
        result = get_category('0ZUBhfQhoczohmoxWGZpxj')
        
        self.assertEqual(result['id'], '0ZUBhfQhoczohmoxWGZpxj')
        self.assertEqual(result['name'], 'Test Category')

    def test_get_category_with_country(self):
        """Test category retrieval with country parameter."""
        result = get_category('0ZUBhfQhoczohmoxWGZpxj', country='US')
        
        self.assertEqual(result['id'], '0ZUBhfQhoczohmoxWGZpxj')
        self.assertEqual(result['name'], 'Test Category')

    def test_get_category_with_locale(self):
        """Test category retrieval with locale parameter."""
        result = get_category('0ZUBhfQhoczohmoxWGZpxj', locale='en_US')
        
        self.assertEqual(result['id'], '0ZUBhfQhoczohmoxWGZpxj')
        self.assertEqual(result['name'], 'Test Category')

    def test_get_category_not_found(self):
        """Test category retrieval with non-existent category."""
        with self.assertRaises(NoResultsFoundError):
            get_category('non_existent_category')

    def test_get_category_with_invalid_id(self):
        """Test category retrieval with invalid ID."""
        with self.assertRaises(InvalidInputError):
            get_category('')

    def test_get_category_playlists_success(self):
        """Test successful retrieval of category playlists."""
        result = get_category_playlists('0ZUBhfQhoczohmoxWGZpxj')
        
        self.assertIn('playlists', result)
        self.assertIn('items', result['playlists'])
        self.assertIn('total', result['playlists'])
        self.assertEqual(len(result['playlists']['items']), 1)

    def test_get_category_playlists_with_country(self):
        """Test category playlists with country parameter."""
        result = get_category_playlists('0ZUBhfQhoczohmoxWGZpxj', country='US')
        
        self.assertIn('playlists', result)
        self.assertIn('items', result['playlists'])

    def test_get_category_playlists_with_pagination(self):
        """Test category playlists with pagination."""
        result = get_category_playlists('0ZUBhfQhoczohmoxWGZpxj', limit=1, offset=0)
        
        self.assertIn('playlists', result)
        self.assertEqual(len(result['playlists']['items']), 1)
        self.assertEqual(result['playlists']['limit'], 1)
        self.assertEqual(result['playlists']['offset'], 0)

    def test_get_category_playlists_category_not_found(self):
        """Test category playlists with non-existent category."""
        with self.assertRaises(NoResultsFoundError):
            get_category_playlists('non_existent_category')

    def test_get_category_playlists_with_invalid_id(self):
        """Test category playlists with invalid category ID."""
        with self.assertRaises(InvalidInputError):
            get_category_playlists('')

    def test_get_recommendations_with_artist_seeds(self):
        """Test recommendations with artist seeds."""
        result = get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'])
        
        self.assertIn('seeds', result)
        self.assertIn('tracks', result)
        self.assertEqual(len(result['seeds']), 1)
        self.assertEqual(result['seeds'][0]['type'], 'artist')

    def test_get_recommendations_with_genre_seeds(self):
        """Test recommendations with genre seeds."""
        result = get_recommendations(seed_genres=['rock'])
        
        self.assertIn('seeds', result)
        self.assertIn('tracks', result)
        self.assertEqual(len(result['seeds']), 1)
        self.assertEqual(result['seeds'][0]['type'], 'genre')

    def test_get_recommendations_with_track_seeds(self):
        """Test recommendations with track seeds."""
        result = get_recommendations(seed_tracks=['WSB9PMCMqpdEBFpMrMfS3h'])
        
        self.assertIn('seeds', result)
        self.assertIn('tracks', result)
        self.assertEqual(len(result['seeds']), 1)
        self.assertEqual(result['seeds'][0]['type'], 'track')

    def test_get_recommendations_with_multiple_seeds(self):
        """Test recommendations with multiple seed types."""
        result = get_recommendations(
            seed_artists=['W0e71GNltAWtwmOaMZcm1J'],
            seed_genres=['rock'],
            seed_tracks=['WSB9PMCMqpdEBFpMrMfS3h']
        )
        
        self.assertIn('seeds', result)
        self.assertIn('tracks', result)
        self.assertEqual(len(result['seeds']), 3)

    def test_get_recommendations_with_market_filter(self):
        """Test recommendations with market filtering."""
        result = get_recommendations(
            seed_artists=['W0e71GNltAWtwmOaMZcm1J'],
            market='US'
        )
        
        self.assertIn('seeds', result)
        self.assertIn('tracks', result)

    def test_get_recommendations_with_limit(self):
        """Test recommendations with custom limit."""
        result = get_recommendations(
            seed_artists=['W0e71GNltAWtwmOaMZcm1J'],
            limit=10
        )
        
        self.assertIn('seeds', result)
        self.assertIn('tracks', result)
        self.assertLessEqual(len(result['tracks']), 10)

    def test_get_recommendations_no_seeds(self):
        """Test recommendations with no seeds provided."""
        with self.assertRaises(InvalidInputError):
            get_recommendations()

    def test_get_recommendations_too_many_seeds(self):
        """Test recommendations with too many seeds."""
        with self.assertRaises(InvalidInputError):
            get_recommendations(
                seed_artists=['artist_1', 'artist_2', 'artist_3', 'artist_4', 'artist_5', 'artist_6']
            )

    def test_get_recommendations_invalid_limit(self):
        """Test recommendations with invalid limit."""
        with self.assertRaises(InvalidInputError):
            get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'], limit=0)

    def test_get_recommendations_invalid_market(self):
        """Test recommendations with invalid market."""
        with self.assertRaises(InvalidMarketError):
            get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'], market='INVALID')

    def test_get_available_genre_seeds_success(self):
        """Test successful retrieval of available genre seeds."""
        result = get_available_genre_seeds()
        
        self.assertIn('genres', result)
        self.assertIsInstance(result['genres'], list)
        self.assertGreater(len(result['genres']), 0)
        # Check that expected genres are present
        expected_genres = ['acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient']
        for genre in expected_genres:
            self.assertIn(genre, result['genres'])

    def test_get_available_genre_seeds_empty_list(self):
        """Test genre seeds when DB returns empty list."""
        # Temporarily modify the DB to return empty list
        DB.update({'genres': []})
        
        result = get_available_genre_seeds()
        
        self.assertIn('genres', result)
        self.assertEqual(result['genres'], [])

    def test_get_new_releases_sorted_by_release_date(self):
        """Test that new releases are sorted by release date (newest first)."""
        result = get_new_releases()
        
        self.assertIn('albums', result)
        self.assertIn('items', result['albums'])
        
        # Check that albums are sorted by release date (newest first)
        items = result['albums']['items']
        if len(items) >= 2:
            # gJIfNlJdPASNffy7UY2V6D has release_date '2023-02-01' (newer)
            # 4kBp5iVByDSAUc0lb78jCZ has release_date '2023-01-01' (older)
            self.assertEqual(items[0]['id'], 'gJIfNlJdPASNffy7UY2V6D')  # Newer album first
            self.assertEqual(items[1]['id'], '4kBp5iVByDSAUc0lb78jCZ')  # Older album second

    def test_get_new_releases_country_filtering(self):
        """Test that country filtering works correctly."""
        # Test with country that has available albums
        result = get_new_releases(country='US')
        self.assertIn('albums', result)
        self.assertIn('items', result['albums'])
        self.assertEqual(len(result['albums']['items']), 2)  # Both albums available in US
        
        # Test with country that has no available albums
        # We need to modify the test data temporarily
        original_albums = self.test_db['albums'].copy()
        self.test_db['albums']['4kBp5iVByDSAUc0lb78jCZ']['available_markets'] = ['CA']  # Remove US
        self.test_db['albums']['gJIfNlJdPASNffy7UY2V6D']['available_markets'] = ['CA']  # Remove US
        
        result = get_new_releases(country='US')
        self.assertIn('albums', result)
        self.assertIn('items', result['albums'])
        self.assertEqual(len(result['albums']['items']), 0)  # No albums available in US
        
        # Restore original data
        self.test_db['albums'] = original_albums

    def test_get_featured_playlists_pagination(self):
        """Test featured playlists pagination."""
        result = get_featured_playlists(limit=1, offset=0)
        
        self.assertIn('playlists', result)
        self.assertIn('items', result['playlists'])
        self.assertEqual(len(result['playlists']['items']), 1)
        self.assertEqual(result['playlists']['limit'], 1)
        self.assertEqual(result['playlists']['offset'], 0)

    def test_get_categories_pagination(self):
        """Test categories pagination."""
        result = get_categories(limit=1, offset=0)
        
        self.assertIn('categories', result)
        self.assertIn('items', result['categories'])
        self.assertEqual(len(result['categories']['items']), 1)
        self.assertEqual(result['categories']['limit'], 1)
        self.assertEqual(result['categories']['offset'], 0)

    def test_get_category_playlists_href_generation(self):
        """Test that category playlists response includes correct href."""
        result = get_category_playlists('0ZUBhfQhoczohmoxWGZpxj')
        
        self.assertIn('playlists', result)
        self.assertIn('href', result['playlists'])
        self.assertEqual(
            result['playlists']['href'],
            'https://api.spotify.com/v1/browse/categories/0ZUBhfQhoczohmoxWGZpxj/playlists'
        )

    def test_get_recommendations_seed_structure(self):
        """Test that recommendation seeds have correct structure."""
        result = get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'])
        
        self.assertIn('seeds', result)
        self.assertGreater(len(result['seeds']), 0)
        
        seed = result['seeds'][0]
        required_fields = ['afterFilteringSize', 'afterRelinkingSize', 'href', 'id', 'initialPoolSize', 'type']
        for field in required_fields:
            self.assertIn(field, seed)
        
        self.assertEqual(seed['type'], 'artist')
        self.assertEqual(seed['id'], 'W0e71GNltAWtwmOaMZcm1J')

    def test_get_recommendations_track_structure(self):
        """Test that recommendation tracks have correct structure."""
        result = get_recommendations(seed_tracks=['WSB9PMCMqpdEBFpMrMfS3h'])
        
        self.assertIn('tracks', result)
        self.assertGreater(len(result['tracks']), 0)
        
        track = result['tracks'][0]
        required_fields = ['id', 'name', 'artists', 'album', 'duration_ms', 'available_markets']
        for field in required_fields:
            self.assertIn(field, track)

    def test_get_recommendations_market_filtering(self):
        """Test that market filtering works in recommendations."""
        # Test with market that has available tracks
        result = get_recommendations(seed_tracks=['WSB9PMCMqpdEBFpMrMfS3h'], market='US')
        self.assertIn('tracks', result)
        self.assertGreater(len(result['tracks']), 0)
        
        # Test with market that has no available tracks
        # Temporarily modify test data
        original_tracks = self.test_db['tracks'].copy()
        self.test_db['tracks']['WSB9PMCMqpdEBFpMrMfS3h']['available_markets'] = ['CA']  # Remove US
        
        result = get_recommendations(seed_tracks=['WSB9PMCMqpdEBFpMrMfS3h'], market='US')
        self.assertIn('tracks', result)
        self.assertEqual(len(result['tracks']), 0)  # No tracks available in US
        
        # Restore original data
        self.test_db['tracks'] = original_tracks

    def test_get_recommendations_default_limit(self):
        """Test that recommendations use default limit when not specified."""
        result = get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'])
        
        self.assertIn('tracks', result)
        self.assertLessEqual(len(result['tracks']), 20)  # Default limit is 20

    def test_get_recommendations_custom_limit(self):
        """Test that recommendations respect custom limit."""
        result = get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'], limit=5)
        
        self.assertIn('tracks', result)
        self.assertLessEqual(len(result['tracks']), 5)

    def test_get_recommendations_max_limit(self):
        """Test that recommendations respect maximum limit."""
        result = get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'], limit=100)
        
        self.assertIn('tracks', result)
        self.assertLessEqual(len(result['tracks']), 100)

    def test_get_recommendations_invalid_limit_too_high(self):
        """Test recommendations with limit above maximum."""
        with self.assertRaises(InvalidInputError):
            get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'], limit=101)

    def test_get_recommendations_invalid_limit_too_low(self):
        """Test recommendations with limit below minimum."""
        with self.assertRaises(InvalidInputError):
            get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'], limit=0)

    def test_get_recommendations_invalid_limit_type(self):
        """Test recommendations with non-integer limit."""
        with self.assertRaises(InvalidInputError):
            get_recommendations(seed_artists=['W0e71GNltAWtwmOaMZcm1J'], limit="invalid")  # type: ignore

    def test_get_new_releases_invalid_limit_type(self):
        """Test new releases with non-integer limit."""
        with self.assertRaises(InvalidInputError):
            get_new_releases(limit="invalid")  # type: ignore

    def test_get_new_releases_invalid_offset_type(self):
        """Test new releases with non-integer offset."""
        with self.assertRaises(InvalidInputError):
            get_new_releases(offset="invalid")  # type: ignore

    def test_get_featured_playlists_invalid_limit_type(self):
        """Test featured playlists with non-integer limit."""
        with self.assertRaises(InvalidInputError):
            get_featured_playlists(limit="invalid")  # type: ignore

    def test_get_featured_playlists_invalid_offset_type(self):
        """Test featured playlists with non-integer offset."""
        with self.assertRaises(InvalidInputError):
            get_featured_playlists(offset="invalid")  # type: ignore

    def test_get_categories_invalid_limit_type(self):
        """Test categories with non-integer limit."""
        with self.assertRaises(InvalidInputError):
            get_categories(limit="invalid")  # type: ignore

    def test_get_categories_invalid_offset_type(self):
        """Test categories with non-integer offset."""
        with self.assertRaises(InvalidInputError):
            get_categories(offset="invalid")  # type: ignore

    def test_get_category_playlists_invalid_limit_type(self):
        """Test category playlists with non-integer limit."""
        with self.assertRaises(InvalidInputError):
            get_category_playlists('0ZUBhfQhoczohmoxWGZpxj', limit="invalid")  # type: ignore

    def test_get_category_playlists_invalid_offset_type(self):
        """Test category playlists with non-integer offset."""
        with self.assertRaises(InvalidInputError):
            get_category_playlists('0ZUBhfQhoczohmoxWGZpxj', offset="invalid")  # type: ignore


if __name__ == '__main__':
    unittest.main() 