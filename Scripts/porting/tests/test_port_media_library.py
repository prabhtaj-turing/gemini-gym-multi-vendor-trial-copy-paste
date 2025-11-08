"""
Test Cases for Media Library Porting System

This module contains critical test cases that verify core functionality and code sanity
for port_media_library.py and models.py. These tests ensure all existing functionality
works correctly.
"""

import json
import pytest
import uuid
from pathlib import Path
from unittest.mock import patch

# Setup path for imports
import sys

ROOT = Path(__file__).resolve().parents[0]
APIS_PATH = ROOT / "APIs"
SCRIPTS_PATH = ROOT / "Scripts" / "porting"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))

from generic_media.SimulationEngine.models import (
    GenericMediaDB,
    Provider,
    Track,
    Album,
    Artist,
    Playlist,
    PodcastShow,
    PodcastEpisode,
)
from Scripts.porting.port_media_library import (
    port_media_library,
    process_providers,
    process_tracks,
    process_podcasts,
    generate_artists,
    string_to_iso_datetime,
    validate_provider_data,
    validate_track_data,
    validate_complete_database,
)


class TestCoreFunctionality:
    """tests for core functionality and main function tests"""

    def test_port_media_library_with_complete_valid_json_data_returns_full_database(
        self,
    ):
        """Test port media library with complete valid JSON data returns full database"""
        source_data = {
            "providers": [{"name": "Spotify"}],
            "tracks": [
                {
                    "id": "track1",
                    "title": "Test Song",
                    "artist_name": "Test Artist",
                    "album_id": "album1",
                    "provider": "spotify",
                    "content_type": "TRACK",
                }
            ],
            "albums": [
                {
                    "id": "album1",
                    "title": "Test Album",
                    "artist_name": "Test Artist",
                    "track_ids": ["track1"],
                    "provider": "spotify",
                    "content_type": "ALBUM",
                }
            ],
            "playlists": [
                {
                    "id": "playlist1",
                    "name": "Test Playlist",
                    "track_ids": ["track1"],
                    "is_personal": True,
                    "provider": "spotify",
                    "content_type": "PLAYLIST",
                }
            ],
            "podcasts": [
                {
                    "id": "podcast1",
                    "title": "Test Podcast",
                    "episodes": [
                        {
                            "id": "episode1",
                            "title": "Test Episode",
                            "show_id": "podcast1",
                            "provider": "spotify",
                            "content_type": "PODCAST_EPISODE",
                        }
                    ],
                    "provider": "spotify",
                    "content_type": "PODCAST_SHOW",
                }
            ],
        }

        template_data = {
            "providers": [
                {
                    "name": "Apple Music",
                    "base_url": "https://music.apple.com"
                },
                {
                    "name": "Deezer", 
                    "base_url": "https://www.deezer.com"
                },
                {
                    "name": "Amazon Music",
                    "base_url": "https://music.amazon.com"
                },
                {
                    "name": "SoundCloud",
                    "base_url": "https://soundcloud.com"
                }
            ],
            "actions": [],
            "tracks": [
                {
                    "id": "track1",
                    "title": "Bohemian Rhapsody",
                    "artist_name": "Queen",
                    "album_id": "album1",
                    "rank": 1,
                    "release_timestamp": "1975-10-31T00:00:00Z",
                    "is_liked": True,
                    "provider": "applemusic",
                    "content_type": "TRACK"
                },
                {
                    "id": "track2",
                    "title": "Stairway to Heaven",
                    "artist_name": "Led Zeppelin",
                    "album_id": "album2",
                    "rank": 2,
                    "release_timestamp": "1971-11-08T00:00:00Z",
                    "is_liked": False,
                    "provider": "deezer",
                    "content_type": "TRACK"
                }
            ],
            "albums": [
                {
                    "id": "album1",
                    "title": "A Night at the Opera",
                    "artist_name": "Queen",
                    "track_ids": ["track1"],
                    "provider": "applemusic",
                    "content_type": "ALBUM"
                },
                {
                    "id": "album2",
                    "title": "Led Zeppelin IV",
                    "artist_name": "Led Zeppelin",
                    "track_ids": ["track2"],
                    "provider": "deezer",
                    "content_type": "ALBUM"
                }
            ],
            "artists": [
                {
                    "id": "artist1",
                    "name": "Queen",
                    "provider": "applemusic",
                    "content_type": "ARTIST"
                },
                {
                    "id": "artist2",
                    "name": "Led Zeppelin",
                    "provider": "deezer",
                    "content_type": "ARTIST"
                }
            ],
            "playlists": [
                {
                    "id": "playlist1",
                    "name": "My Rock Favorites",
                    "track_ids": ["track1", "track2"],
                    "is_personal": True,
                    "provider": "applemusic",
                    "content_type": "PLAYLIST"
                }
            ],
            "podcasts": [
                {
                    "id": "show1",
                    "title": "The Daily",
                    "episodes": [
                        {
                            "id": "episode1",
                            "title": "A Big Day for a Small Town",
                            "show_id": "show1",
                            "provider": "spotify",
                            "content_type": "PODCAST_EPISODE"
                        }
                    ],
                    "provider": "spotify",
                    "content_type": "PODCAST_SHOW"
                }
            ],
            "recently_played": []
        }

        with patch(
            "Scripts.porting.port_media_library.load_template_database",
            return_value=template_data,
        ):
            with patch(
                "Scripts.porting.port_media_library.save_ported_database"
            ) as mock_save:
                result = port_media_library(json.dumps(source_data))

                assert "providers" in result
                assert "tracks" in result
                assert "albums" in result
                assert "artists" in result
                assert "playlists" in result
                assert "podcasts" in result
                assert len(result["providers"]) == 1
                assert len(result["tracks"]) == 1
                assert len(result["albums"]) == 1
                assert len(result["playlists"]) == 1
                assert len(result["podcasts"]) == 1
                mock_save.assert_called_once()

    def test_port_media_library_with_only_providers_section_creates_empty_other_sections(
        self,
    ):
        """Test port media library with only providers section creates empty other sections"""
        source_data = {"providers": [{"name": "Spotify"}]}

        template_data = {
            "providers": [
                {
                    "name": "Apple Music",
                    "base_url": "https://music.apple.com"
                },
                {
                    "name": "Deezer",
                    "base_url": "https://www.deezer.com"
                },
                {
                    "name": "Amazon Music",
                    "base_url": "https://music.amazon.com"
                },
                {
                    "name": "SoundCloud",
                    "base_url": "https://soundcloud.com"
                }
            ],
            "actions": [],
            "tracks": [
                {
                    "id": "track1",
                    "title": "Bohemian Rhapsody",
                    "artist_name": "Queen",
                    "album_id": "album1",
                    "rank": 1,
                    "release_timestamp": "1975-10-31T00:00:00Z",
                    "is_liked": True,
                    "provider": "applemusic",
                    "content_type": "TRACK"
                },
                {
                    "id": "track2",
                    "title": "Stairway to Heaven",
                    "artist_name": "Led Zeppelin",
                    "album_id": "album2",
                    "rank": 2,
                    "release_timestamp": "1971-11-08T00:00:00Z",
                    "is_liked": False,
                    "provider": "deezer",
                    "content_type": "TRACK"
                }
            ],
            "albums": [
                {
                    "id": "album1",
                    "title": "A Night at the Opera",
                    "artist_name": "Queen",
                    "track_ids": ["track1"],
                    "provider": "applemusic",
                    "content_type": "ALBUM"
                },
                {
                    "id": "album2",
                    "title": "Led Zeppelin IV",
                    "artist_name": "Led Zeppelin",
                    "track_ids": ["track2"],
                    "provider": "deezer",
                    "content_type": "ALBUM"
                }
            ],
            "artists": [
                {
                    "id": "artist1",
                    "name": "Queen",
                    "provider": "applemusic",
                    "content_type": "ARTIST"
                },
                {
                    "id": "artist2",
                    "name": "Led Zeppelin",
                    "provider": "deezer",
                    "content_type": "ARTIST"
                }
            ],
            "playlists": [
                {
                    "id": "playlist1",
                    "name": "My Rock Favorites",
                    "track_ids": ["track1", "track2"],
                    "is_personal": True,
                    "provider": "applemusic",
                    "content_type": "PLAYLIST"
                }
            ],
            "podcasts": [
                {
                    "id": "show1",
                    "title": "The Daily",
                    "episodes": [
                        {
                            "id": "episode1",
                            "title": "A Big Day for a Small Town",
                            "show_id": "show1",
                            "provider": "spotify",
                            "content_type": "PODCAST_EPISODE"
                        }
                    ],
                    "provider": "spotify",
                    "content_type": "PODCAST_SHOW"
                }
            ],
            "recently_played": []
        }

        with patch(
            "Scripts.porting.port_media_library.load_template_database",
            return_value=template_data,
        ):
            with patch(
                "Scripts.porting.port_media_library.save_ported_database"
            ) as mock_save:
                result = port_media_library(json.dumps(source_data))

                assert len(result["providers"]) == 1
                assert len(result["tracks"]) == 0
                assert len(result["albums"]) == 0
                assert len(result["artists"]) == 0
                assert len(result["playlists"]) == 0
                assert len(result["podcasts"]) == 0

    def test_port_media_library_with_missing_albums_playlists_podcasts_defaults_to_empty_arrays(
        self,
    ):
        """Test port media library with missing albums playlists podcasts defaults to empty arrays"""
        source_data = {
            "providers": [{"name": "Spotify"}],
            "tracks": [
                {
                    "id": "track1",
                    "title": "Test Song",
                    "artist_name": "Test Artist",
                    "provider": "spotify",
                    "content_type": "TRACK",
                }
            ],
        }

        template_data = {
            "providers": [
                {
                    "name": "Apple Music",
                    "base_url": "https://music.apple.com"
                },
                {
                    "name": "Deezer",
                    "base_url": "https://www.deezer.com"
                },
                {
                    "name": "Amazon Music",
                    "base_url": "https://music.amazon.com"
                },
                {
                    "name": "SoundCloud",
                    "base_url": "https://soundcloud.com"
                }
            ],
            "actions": [],
            "tracks": [
                {
                    "id": "track1",
                    "title": "Bohemian Rhapsody",
                    "artist_name": "Queen",
                    "album_id": "album1",
                    "rank": 1,
                    "release_timestamp": "1975-10-31T00:00:00Z",
                    "is_liked": True,
                    "provider": "applemusic",
                    "content_type": "TRACK"
                },
                {
                    "id": "track2",
                    "title": "Stairway to Heaven",
                    "artist_name": "Led Zeppelin",
                    "album_id": "album2",
                    "rank": 2,
                    "release_timestamp": "1971-11-08T00:00:00Z",
                    "is_liked": False,
                    "provider": "deezer",
                    "content_type": "TRACK"
                }
            ],
            "albums": [
                {
                    "id": "album1",
                    "title": "A Night at the Opera",
                    "artist_name": "Queen",
                    "track_ids": ["track1"],
                    "provider": "applemusic",
                    "content_type": "ALBUM"
                },
                {
                    "id": "album2",
                    "title": "Led Zeppelin IV",
                    "artist_name": "Led Zeppelin",
                    "track_ids": ["track2"],
                    "provider": "deezer",
                    "content_type": "ALBUM"
                }
            ],
            "artists": [
                {
                    "id": "artist1",
                    "name": "Queen",
                    "provider": "applemusic",
                    "content_type": "ARTIST"
                },
                {
                    "id": "artist2",
                    "name": "Led Zeppelin",
                    "provider": "deezer",
                    "content_type": "ARTIST"
                }
            ],
            "playlists": [
                {
                    "id": "playlist1",
                    "name": "My Rock Favorites",
                    "track_ids": ["track1", "track2"],
                    "is_personal": True,
                    "provider": "applemusic",
                    "content_type": "PLAYLIST"
                }
            ],
            "podcasts": [
                {
                    "id": "show1",
                    "title": "The Daily",
                    "episodes": [
                        {
                            "id": "episode1",
                            "title": "A Big Day for a Small Town",
                            "show_id": "show1",
                            "provider": "spotify",
                            "content_type": "PODCAST_EPISODE"
                        }
                    ],
                    "provider": "spotify",
                    "content_type": "PODCAST_SHOW"
                }
            ],
            "recently_played": []
        }

        with patch(
            "Scripts.porting.port_media_library.load_template_database",
            return_value=template_data,
        ):
            with patch(
                "Scripts.porting.port_media_library.save_ported_database"
            ) as mock_save:
                result = port_media_library(json.dumps(source_data))

                assert len(result["providers"]) == 1
                assert len(result["tracks"]) == 1
                assert len(result["albums"]) == 0
                assert len(result["playlists"]) == 0
                assert len(result["podcasts"]) == 0


class TestDataProcessingFunctions:
    """tests for data processing functions"""

    def test_process_providers_with_known_names_maps_to_correct_base_urls(self):
        """Test process providers with known names maps to correct base URLs"""
        source_providers = [
            {"name": "Spotify"},
            {"name": "Apple Music"},
            {"name": "Deezer"},
        ]
        provider_template = {"name": "", "base_url": ""}

        result = process_providers(source_providers, provider_template)

        assert len(result) == 3
        assert result[0]["base_url"] == "https://spotify.com"
        assert result[1]["base_url"] == "https://music.apple.com"
        assert result[2]["base_url"] == "https://www.deezer.com"

    def test_process_providers_with_unknown_name_generates_lowercase_url(self):
        """Test process providers with unknown name generates lowercase URL"""
        source_providers = [{"name": "CustomMusicService"}]
        provider_template = {"name": "", "base_url": ""}

        result = process_providers(source_providers, provider_template)

        assert len(result) == 1
        assert result[0]["base_url"] == "https://custommusicservice.com"
        assert result[0]["name"] == "CustomMusicService"

    def test_process_tracks_without_rank_assigns_sequential_ranking_starting_from_one(
        self,
    ):
        """Test process tracks without rank assigns sequential ranking starting from one"""
        source_tracks = [
            {
                "id": "track1",
                "title": "Song 1",
                "artist_name": "Artist 1",
                "provider": "spotify",
                "content_type": "TRACK",
            },
            {
                "id": "track2",
                "title": "Song 2",
                "artist_name": "Artist 2",
                "provider": "spotify",
                "content_type": "TRACK",
            },
            {
                "id": "track3",
                "title": "Song 3",
                "artist_name": "Artist 3",
                "provider": "spotify",
                "content_type": "TRACK",
            },
        ]
        track_template = {
            "id": "",
            "title": "",
            "artist_name": "",
            "album_id": "",
            "rank": 0,
            "release_timestamp": "",
            "is_liked": False,
            "provider": "",
            "content_type": "TRACK",
        }

        result = process_tracks(source_tracks, track_template)

        assert len(result) == 3
        assert result[0]["rank"] == 1
        assert result[1]["rank"] == 2
        assert result[2]["rank"] == 3

    def test_process_tracks_without_release_timestamp_generates_deterministic_datetime_from_title(
        self,
    ):
        """Test process tracks without release timestamp generates deterministic datetime from title"""
        source_tracks = [
            {
                "id": "track1",
                "title": "Unique Song Title",
                "artist_name": "Artist 1",
                "provider": "spotify",
                "content_type": "TRACK",
            }
        ]
        track_template = {
            "id": "",
            "title": "",
            "artist_name": "",
            "album_id": "",
            "rank": 0,
            "release_timestamp": "",
            "is_liked": False,
            "provider": "",
            "content_type": "TRACK",
        }

        result = process_tracks(source_tracks, track_template)

        assert len(result) == 1
        assert result[0]["release_timestamp"] is not None
        assert "T" in result[0]["release_timestamp"]  # ISO format
        assert result[0]["release_timestamp"].endswith("+00:00")  # UTC timezone

    def test_process_tracks_without_is_liked_field_defaults_to_false(self):
        """Test process tracks without is liked field defaults to false"""
        source_tracks = [
            {
                "id": "track1",
                "title": "Song 1",
                "artist_name": "Artist 1",
                "provider": "spotify",
                "content_type": "TRACK",
            }
        ]
        track_template = {
            "id": "",
            "title": "",
            "artist_name": "",
            "album_id": "",
            "rank": 0,
            "release_timestamp": "",
            "is_liked": False,
            "provider": "",
            "content_type": "TRACK",
        }

        result = process_tracks(source_tracks, track_template)

        assert len(result) == 1
        assert result[0]["is_liked"] is False

    def test_process_podcasts_with_multiple_episodes_preserves_all_episode_data(self):
        """Test process podcasts with multiple episodes preserves all episode data"""
        source_podcasts = [
            {
                "id": "podcast1",
                "title": "Test Podcast",
                "episodes": [
                    {
                        "id": "ep1",
                        "title": "Episode 1",
                        "show_id": "podcast1",
                        "provider": "spotify",
                        "content_type": "PODCAST_EPISODE",
                    },
                    {
                        "id": "ep2",
                        "title": "Episode 2",
                        "show_id": "podcast1",
                        "provider": "spotify",
                        "content_type": "PODCAST_EPISODE",
                    },
                ],
                "provider": "spotify",
                "content_type": "PODCAST_SHOW",
            }
        ]
        podcast_template = {
            "id": "",
            "title": "",
            "episodes": [
                {
                    "id": "",
                    "title": "",
                    "show_id": "",
                    "provider": "",
                    "content_type": "PODCAST_EPISODE",
                }
            ],
            "provider": "",
            "content_type": "PODCAST_SHOW",
        }

        result = process_podcasts(source_podcasts, podcast_template)

        assert len(result) == 1
        assert len(result[0]["episodes"]) == 2
        assert result[0]["episodes"][0]["title"] == "Episode 1"
        assert result[0]["episodes"][1]["title"] == "Episode 2"


class TestArtistGeneration:
    """tests for artist generation functionality"""

    def test_generate_artists_from_tracks_only_creates_unique_artist_entries(self):
        """Test generate artists from tracks only creates unique artist entries"""
        ported_db = {
            "tracks": [
                {"artist_name": "Artist 1", "provider": "spotify", "content_type": "TRACK"},
                {"artist_name": "Artist 2", "provider": "spotify", "content_type": "TRACK"},
                {"artist_name": "Artist 1", "provider": "spotify", "content_type": "TRACK"},  # Duplicate
            ],
            "albums": [],
        }

        generate_artists(ported_db)

        assert "artists" in ported_db
        assert len(ported_db["artists"]) == 2
        artist_names = [artist["name"] for artist in ported_db["artists"]]
        assert "Artist 1" in artist_names
        assert "Artist 2" in artist_names

    def test_generate_artists_prevents_duplicates_for_same_name_and_provider(self):
        """Test generate artists prevents duplicates for same name and provider"""
        ported_db = {
            "tracks": [
                {"artist_name": "Same Artist", "provider": "spotify", "content_type": "TRACK"},
                {"artist_name": "Same Artist", "provider": "spotify", "content_type": "TRACK"},
            ],
            "albums": [{"artist_name": "Same Artist", "provider": "spotify", "content_type": "ALBUM"}],
        }

        generate_artists(ported_db)

        assert len(ported_db["artists"]) == 1
        assert ported_db["artists"][0]["name"] == "Same Artist"
        assert ported_db["artists"][0]["provider"] == "spotify"

    def test_generate_artists_assigns_sequential_ids_starting_with_artist_1(self):
        """Test generate artists assigns sequential IDs starting with artist_1"""
        ported_db = {
            "tracks": [
                {"artist_name": "Artist A", "provider": "spotify", "content_type": "TRACK"},
                {"artist_name": "Artist B", "provider": "spotify", "content_type": "TRACK"},
                {"artist_name": "Artist C", "provider": "spotify", "content_type": "TRACK"},
            ],
            "albums": [],
        }

        generate_artists(ported_db)

        assert len(ported_db["artists"]) == 3
        assert ported_db["artists"][0]["id"] == "artist_1"
        assert ported_db["artists"][1]["id"] == "artist_2"
        assert ported_db["artists"][2]["id"] == "artist_3"


class TestUtilityFunctions:
    """tests for utility functions"""

    def test_string_to_iso_datetime_with_same_input_returns_identical_datetime(self):
        """Test string to ISO datetime with same input returns identical datetime"""
        test_string = "Test Song Title"

        result1 = string_to_iso_datetime(test_string)
        result2 = string_to_iso_datetime(test_string)

        assert result1 == result2
        assert "T" in result1
        assert result1.endswith("+00:00")


class TestDataValidationFunctions:
    """tests for data validation functions"""

    def test_validate_provider_data_with_missing_name_raises_validation_error(self):
        """Test validate provider data with missing name raises validation error"""
        invalid_provider = {"base_url": "https://example.com"}

        with pytest.raises(ValueError, match="Provider validation failed"):
            validate_provider_data(invalid_provider)

    def test_validate_track_data_with_missing_title_or_artist_raises_validation_error(
        self,
    ):
        """Test validate track data with missing title or artist raises validation error"""
        invalid_track = {
            "id": "track1",
            "artist_name": "Artist",
            "rank": 1,
            "release_timestamp": "2023-01-01T00:00:00+00:00",
            "is_liked": False,
            "provider": "spotify",
            "content_type": "TRACK",
            # Missing title
        }

        with pytest.raises(ValueError, match="Track validation failed"):
            validate_track_data(invalid_track)

    def test_validate_complete_database_with_valid_structure_returns_validated_generic_media_db(
        self,
    ):
        """Test validate complete database with valid structure returns validated generic media DB"""
        valid_db = {
            "providers": [{"name": "Spotify", "base_url": "https://spotify.com"}],
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": [],
            "podcasts": [],
            "recently_played": [],
        }

        result = validate_complete_database(valid_db)

        assert isinstance(result, dict)
        assert "providers" in result
        assert "tracks" in result
        assert len(result["providers"]) == 1

    def test_validate_complete_database_with_invalid_provider_raises_validation_error(
        self,
    ):
        """Test validate complete database with invalid provider raises validation error"""
        invalid_db = {
            "providers": [{"base_url": "https://spotify.com"}],  # Missing name
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": [],
            "podcasts": [],
            "recently_played": [],
        }

        with pytest.raises(ValueError, match="Database validation failed"):
            validate_complete_database(invalid_db)


class TestPydanticModels:
    """tests for Pydantic model validation"""

    def test_provider_model_with_name_and_base_url_creates_valid_instance(self):
        """Test Provider model with name and base URL creates valid instance"""
        provider_data = {"name": "Spotify", "base_url": "https://spotify.com"}

        provider = Provider(**provider_data)

        assert provider.name == "Spotify"
        assert provider.base_url == "https://spotify.com"

    def test_track_model_with_all_required_fields_creates_valid_instance(self):
        """Test Track model with all required fields creates valid instance"""
        track_data = {
            "id": "track1",
            "title": "Test Song",
            "artist_name": "Test Artist",
            "rank": 1,
            "release_timestamp": "2023-01-01T00:00:00+00:00",
            "is_liked": True,
            "provider": "spotify",
        }

        track = Track(**track_data)

        assert track.title == "Test Song"
        assert track.artist_name == "Test Artist"
        assert track.rank == 1
        assert track.is_liked is True
        assert track.content_type == "TRACK"

    def test_track_model_without_id_field_auto_generates_uuid(self):
        """Test Track model without ID field auto generates UUID"""
        track_data = {
            "title": "Test Song",
            "artist_name": "Test Artist",
            "rank": 1,
            "release_timestamp": "2023-01-01T00:00:00+00:00",
            "is_liked": False,
            "provider": "spotify",
        }

        track = Track(**track_data)

        assert track.id is not None
        assert len(track.id) > 0
        # Verify it's a valid UUID format
        uuid.UUID(track.id)

    def test_track_model_with_null_album_id_accepts_optional_field(self):
        """Test Track model with null album ID accepts optional field"""
        track_data = {
            "title": "Test Song",
            "artist_name": "Test Artist",
            "album_id": None,
            "rank": 1,
            "release_timestamp": "2023-01-01T00:00:00+00:00",
            "is_liked": False,
            "provider": "spotify",
        }

        track = Track(**track_data)

        assert track.album_id is None

    def test_album_model_with_empty_track_ids_list_creates_valid_instance(self):
        """Test Album model with empty track IDs list creates valid instance"""
        album_data = {
            "title": "Test Album",
            "artist_name": "Test Artist",
            "track_ids": [],
            "provider": "spotify",
        }

        album = Album(**album_data)

        assert album.title == "Test Album"
        assert album.track_ids == []
        assert album.content_type == "ALBUM"

    def test_artist_model_without_id_field_auto_generates_uuid(self):
        """Test Artist model without ID field auto generates UUID"""
        artist_data = {"name": "Test Artist", "provider": "spotify"}

        artist = Artist(**artist_data)

        assert artist.id is not None
        assert len(artist.id) > 0
        # Verify it's a valid UUID format
        uuid.UUID(artist.id)
        assert artist.content_type == "ARTIST"

    def test_playlist_model_with_is_personal_true_creates_valid_instance(self):
        """Test Playlist model with is personal true creates valid instance"""
        playlist_data = {
            "name": "My Playlist",
            "track_ids": ["track1", "track2"],
            "is_personal": True,
            "provider": "spotify",
        }

        playlist = Playlist(**playlist_data)

        assert playlist.name == "My Playlist"
        assert playlist.is_personal is True
        assert playlist.content_type == "PLAYLIST"

    def test_podcast_episode_model_with_all_required_fields_creates_valid_instance(
        self,
    ):
        """Test PodcastEpisode model with all required fields creates valid instance"""
        episode_data = {
            "title": "Test Episode",
            "show_id": "show1",
            "provider": "spotify",
        }

        episode = PodcastEpisode(**episode_data)

        assert episode.title == "Test Episode"
        assert episode.show_id == "show1"
        assert episode.content_type == "PODCAST_EPISODE"

    def test_podcast_show_model_with_multiple_episodes_validates_nested_structure(self):
        """Test PodcastShow model with multiple episodes validates nested structure"""
        show_data = {
            "title": "Test Podcast",
            "episodes": [
                {"title": "Episode 1", "show_id": "show1", "provider": "spotify", "content_type": "PODCAST_EPISODE"},
                {"title": "Episode 2", "show_id": "show1", "provider": "spotify", "content_type": "PODCAST_EPISODE"},
            ],
            "provider": "spotify",
            "content_type": "PODCAST_SHOW",
        }

        show = PodcastShow(**show_data)

        assert show.title == "Test Podcast"
        assert len(show.episodes) == 2
        assert show.episodes[0].title == "Episode 1"
        assert show.episodes[1].title == "Episode 2"
        assert show.content_type == "PODCAST_SHOW"

    def test_generic_media_db_model_with_all_sections_populated_creates_valid_instance(
        self,
    ):
        """Test GenericMediaDB model with all sections populated creates valid instance"""
        db_data = {
            "providers": [{"name": "Spotify", "base_url": "https://spotify.com"}],
            "tracks": [
                {
                    "title": "Test Song",
                    "artist_name": "Test Artist",
                    "rank": 1,
                    "release_timestamp": "2023-01-01T00:00:00+00:00",
                    "is_liked": False,
                    "provider": "spotify",
                }
            ],
            "albums": [
                {
                    "title": "Test Album",
                    "artist_name": "Test Artist",
                    "track_ids": [],
                    "provider": "spotify",
                }
            ],
            "artists": [{"name": "Test Artist", "provider": "spotify"}],
            "playlists": [
                {
                    "name": "Test Playlist",
                    "track_ids": [],
                    "is_personal": True,
                    "provider": "spotify",
                }
            ],
            "podcasts": [
                {"title": "Test Podcast", "episodes": [], "provider": "spotify"}
            ],
        }

        db = GenericMediaDB(**db_data)

        assert len(db.providers) == 1
        assert len(db.tracks) == 1
        assert len(db.albums) == 1
        assert len(db.artists) == 1
        assert len(db.playlists) == 1
        assert len(db.podcasts) == 1


class TestFieldValidationSpecifics:
    """tests for field validation specifics"""

    def test_pydantic_models_auto_generate_uuid_for_id_fields_when_not_provided(self):
        """Test Pydantic models auto generate UUID for ID fields when not provided"""
        # Test Track
        track = Track(
            title="Test",
            artist_name="Artist",
            rank=1,
            release_timestamp="2023-01-01T00:00:00+00:00",
            is_liked=False,
            provider="spotify",
        )
        assert track.id is not None
        uuid.UUID(track.id)  # Validates UUID format

        # Test Artist
        artist = Artist(name="Artist", provider="spotify")
        assert artist.id is not None
        uuid.UUID(artist.id)  # Validates UUID format

        # Test Album
        album = Album(
            title="Album", artist_name="Artist", track_ids=[], provider="spotify"
        )
        assert album.id is not None
        uuid.UUID(album.id)  # Validates UUID format


class TestIntegrationAndEndToEnd:
    """tests for integration and end-to-end functionality"""

    def test_end_to_end_porting_workflow_with_sample_vendor_data_completes_successfully(
        self,
    ):
        """Test end to end porting workflow with sample vendor data completes successfully"""
        sample_vendor_data = {
            "providers": [{"name": "Spotify"}, {"name": "Apple Podcasts"}],
            "tracks": [
                {
                    "id": "track_spotify_01",
                    "title": "Test Song",
                    "artist_name": "Test Artist",
                    "provider": "spotify",
                    "content_type": "TRACK",
                }
            ],
            "albums": [
                {
                    "id": "album_spotify_01",
                    "title": "Test Album",
                    "artist_name": "Test Artist",
                    "track_ids": ["track_spotify_01"],
                    "provider": "spotify",
                    "content_type": "ALBUM",
                }
            ],
            "playlists": [
                {
                    "id": "playlist_spotify_01",
                    "name": "Test Playlist",
                    "track_ids": ["track_spotify_01"],
                    "is_personal": True,
                    "provider": "spotify",
                    "content_type": "PLAYLIST",
                }
            ],
            "podcasts": [
                {
                    "id": "podcast_01",
                    "title": "Test Podcast",
                    "episodes": [
                        {
                            "id": "episode_01",
                            "title": "Test Episode",
                            "show_id": "podcast_01",
                            "provider": "applepodcasts",
                            "content_type": "PODCAST_EPISODE",
                        }
                    ],
                    "provider": "applepodcasts",
                    "content_type": "PODCAST_SHOW",
                }
            ],
        }

        template_data = {
            "providers": [
                {
                    "name": "Apple Music",
                    "base_url": "https://music.apple.com"
                },
                {
                    "name": "Deezer",
                    "base_url": "https://www.deezer.com"
                },
                {
                    "name": "Amazon Music",
                    "base_url": "https://music.amazon.com"
                },
                {
                    "name": "SoundCloud",
                    "base_url": "https://soundcloud.com"
                }
            ],
            "actions": [],
            "tracks": [
                {
                    "id": "track1",
                    "title": "Bohemian Rhapsody",
                    "artist_name": "Queen",
                    "album_id": "album1",
                    "rank": 1,
                    "release_timestamp": "1975-10-31T00:00:00Z",
                    "is_liked": True,
                    "provider": "applemusic",
                    "content_type": "TRACK"
                },
                {
                    "id": "track2",
                    "title": "Stairway to Heaven",
                    "artist_name": "Led Zeppelin",
                    "album_id": "album2",
                    "rank": 2,
                    "release_timestamp": "1971-11-08T00:00:00Z",
                    "is_liked": False,
                    "provider": "deezer",
                    "content_type": "TRACK"
                }
            ],
            "albums": [
                {
                    "id": "album1",
                    "title": "A Night at the Opera",
                    "artist_name": "Queen",
                    "track_ids": ["track1"],
                    "provider": "applemusic",
                    "content_type": "ALBUM"
                },
                {
                    "id": "album2",
                    "title": "Led Zeppelin IV",
                    "artist_name": "Led Zeppelin",
                    "track_ids": ["track2"],
                    "provider": "deezer",
                    "content_type": "ALBUM"
                }
            ],
            "artists": [
                {
                    "id": "artist1",
                    "name": "Queen",
                    "provider": "applemusic",
                    "content_type": "ARTIST"
                },
                {
                    "id": "artist2",
                    "name": "Led Zeppelin",
                    "provider": "deezer",
                    "content_type": "ARTIST"
                }
            ],
            "playlists": [
                {
                    "id": "playlist1",
                    "name": "My Rock Favorites",
                    "track_ids": ["track1", "track2"],
                    "is_personal": True,
                    "provider": "applemusic",
                    "content_type": "PLAYLIST"
                }
            ],
            "podcasts": [
                {
                    "id": "show1",
                    "title": "The Daily",
                    "episodes": [
                        {
                            "id": "episode1",
                            "title": "A Big Day for a Small Town",
                            "show_id": "show1",
                            "provider": "spotify",
                            "content_type": "PODCAST_EPISODE"
                        }
                    ],
                    "provider": "spotify",
                    "content_type": "PODCAST_SHOW"
                }
            ],
            "recently_played": []
        }

        with patch(
            "Scripts.porting.port_media_library.load_template_database",
            return_value=template_data,
        ):
            with patch(
                "Scripts.porting.port_media_library.save_ported_database"
            ) as mock_save:
                result = port_media_library(json.dumps(sample_vendor_data))

                # Verify all sections are present and populated
                assert len(result["providers"]) == 2
                assert len(result["tracks"]) == 1
                assert len(result["albums"]) == 1
                assert len(result["playlists"]) == 1
                assert len(result["podcasts"]) == 1
                assert len(result["artists"]) > 0  # Generated from tracks/albums

                # Verify data transformation
                assert result["providers"][0]["base_url"] == "https://spotify.com"
                assert result["tracks"][0]["rank"] == 1
                assert result["tracks"][0]["is_liked"] is False
                assert "release_timestamp" in result["tracks"][0]

    def test_ported_database_loads_successfully_into_simulation_engine(self):
        """Test ported database loads successfully into simulation engine"""
        valid_db = {
            "providers": [{"name": "Spotify", "base_url": "https://spotify.com"}],
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": [],
            "podcasts": [],
            "recently_played": [],
        }

        # This tests that the database structure is valid for the simulation engine
        db_model = GenericMediaDB(**valid_db)

        assert db_model is not None
        assert len(db_model.providers) == 1
        assert db_model.providers[0].name == "Spotify"


class TestDataConsistencyAndReferentialIntegrity:
    """tests for data consistency and referential integrity"""

    def test_generated_artists_maintain_consistent_relationship_with_tracks_and_albums(
        self,
    ):
        """Test generated artists maintain consistent relationship with tracks and albums"""
        ported_db = {
            "tracks": [
                {"artist_name": "Artist One", "provider": "spotify", "content_type": "TRACK"},
                {"artist_name": "Artist Two", "provider": "spotify", "content_type": "TRACK"},
            ],
            "albums": [
                {"artist_name": "Artist One", "provider": "spotify", "content_type": "ALBUM"},
                {"artist_name": "Artist Three", "provider": "spotify", "content_type": "ALBUM"},
            ],
        }

        generate_artists(ported_db)

        # Verify all unique artist combinations are created
        assert len(ported_db["artists"]) == 3

        artist_names = {artist["name"] for artist in ported_db["artists"]}
        track_artists = {track["artist_name"] for track in ported_db["tracks"]}
        album_artists = {album["artist_name"] for album in ported_db["albums"]}

        # All track and album artists should be represented in generated artists
        assert track_artists.issubset(artist_names)
        assert album_artists.issubset(artist_names)

        # Verify artist data integrity
        for artist in ported_db["artists"]:
            assert artist["content_type"] == "ARTIST"
            assert artist["provider"] == "spotify"
            assert artist["id"].startswith("artist_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
