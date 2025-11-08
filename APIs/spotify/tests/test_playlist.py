import unittest
from datetime import datetime
import copy
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from ..playlist import (
    add_items_to_playlist, remove_tracks_from_playlist, create_playlist,
    get_user_playlists, get_current_users_playlists, get_playlist_cover_image, add_custom_playlist_cover_image
)

import base64

class TestAddCustomPlaylistCoverImage(unittest.TestCase):
    def setUp(self):
        self._orig_db = copy.deepcopy(DB)
        self.playlist_id = "QDyH69WryQ7dPRXVOFmy2V"
        self.playlist = {
            "id": self.playlist_id,
            "name": "Test Playlist",
            "type": "playlist",
            "uri": f"spotify:playlist:{self.playlist_id}",
            "href": f"https://api.spotify.com/v1/playlists/{self.playlist_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/playlist/{self.playlist_id}"},
            "owner": {"id": "user1", "display_name": "User 1"},
            "public": True,
            "collaborative": False,
            "description": "A test playlist",
            "images": [],
            "tracks": {"total": 0},
            "followers": {"total": 0},
            "snapshot_id": "snapshot_0"
        }
        DB.clear()
        DB['playlists'] = {self.playlist_id: self.playlist}
        DB['playlist_cover_images'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(copy.deepcopy(self._orig_db))

    def test_upload_valid_jpeg(self):
        # Minimal valid JPEG: 0xFFD8 ... 0xFFD9
        jpeg_bytes = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        image_data = base64.b64encode(jpeg_bytes).decode()
        
        add_custom_playlist_cover_image(self.playlist_id, image_data)
        imgs = DB['playlist_cover_images'][self.playlist_id]
        self.assertEqual(len(imgs), 1)
        self.assertEqual(imgs[0]['url'], f"https://images.spotify.com/playlist/{self.playlist_id}/cover.jpg")
        self.assertEqual(imgs[0]['height'], 300)
        self.assertEqual(imgs[0]['width'], 300)
        self.assertEqual(DB['playlists'][self.playlist_id]['images'], imgs)

    def test_overwrite_existing_cover_image(self):
        jpeg_bytes = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        image_data = base64.b64encode(jpeg_bytes).decode()
        
        # First upload
        add_custom_playlist_cover_image(self.playlist_id, image_data)
        # Overwrite
        add_custom_playlist_cover_image(self.playlist_id, image_data)
        imgs = DB['playlist_cover_images'][self.playlist_id]
        self.assertEqual(len(imgs), 1)

    def test_invalid_playlist_id(self):
        jpeg_bytes = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        image_data = base64.b64encode(jpeg_bytes).decode()
        
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image(12345, image_data)
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image("", image_data)
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image("nonexistent", image_data)

    def test_invalid_image_data(self):
        
        # Not a string
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image(self.playlist_id, 12345)
        # Empty string
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image(self.playlist_id, "")
        # Not base64
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image(self.playlist_id, "notbase64!!")
        # Not JPEG (wrong header)
        not_jpeg = base64.b64encode(b'\x00' * 102).decode()
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image(self.playlist_id, not_jpeg)
        # Not JPEG (wrong footer)
        not_jpeg2 = base64.b64encode(b'\xff\xd8' + b'\x00' * 100 + b'\x00\x00').decode()
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image(self.playlist_id, not_jpeg2)
        # Too large
        big_jpeg = b'\xff\xd8' + b'\x00' * (256 * 1024) + b'\xff\xd9'
        big_image_data = base64.b64encode(big_jpeg).decode()
        with self.assertRaises(Exception):
            add_custom_playlist_cover_image(self.playlist_id, big_image_data)

    def test_playlist_with_no_previous_images(self):
        jpeg_bytes = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        image_data = base64.b64encode(jpeg_bytes).decode()
        
        add_custom_playlist_cover_image(self.playlist_id, image_data)
        self.assertEqual(DB['playlist_cover_images'][self.playlist_id][0]['url'], f"https://images.spotify.com/playlist/{self.playlist_id}/cover.jpg")

    def test_playlist_with_previous_images(self):
        jpeg_bytes = b'\xff\xd8' + b'\x00' * 100 + b'\xff\xd9'
        image_data = base64.b64encode(jpeg_bytes).decode()
        
        DB['playlist_cover_images'][self.playlist_id] = [{"url": "old", "height": 100, "width": 100}]
        add_custom_playlist_cover_image(self.playlist_id, image_data)
        imgs = DB['playlist_cover_images'][self.playlist_id]
        self.assertEqual(len(imgs), 1)
        self.assertEqual(imgs[0]['url'], f"https://images.spotify.com/playlist/{self.playlist_id}/cover.jpg")


class TestAddItemsToPlaylist(unittest.TestCase):
    def setUp(self):
        # Save original DB and set up minimal test data
        self._orig_db = copy.deepcopy(DB)
        self.user = {
            "id": "smuqPNFPXrJKcEt943KrY8",
            "display_name": "Test User",
            "type": "user",
            "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8",
            "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
            "external_urls": {"spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"},
        }
        self.playlist = {
            "id": "QDyH69WryQ7dPRXVOFmy2V",
            "name": "Test Playlist",
            "type": "playlist",
            "uri": "spotify:playlist:QDyH69WryQ7dPRXVOFmy2V",
            "href": "https://api.spotify.com/v1/playlists/QDyH69WryQ7dPRXVOFmy2V",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/QDyH69WryQ7dPRXVOFmy2V"},
            "owner": {"id": self.user['id'], "display_name": self.user['display_name']},
            "public": True,
            "collaborative": False,
            "description": "A test playlist",
            "images": [],
            "tracks": {"total": 0},
            "followers": {"total": 0},
            "snapshot_id": "snapshot_0"
        }
        self.track = {
            "id": "WSB9PMCMqpdEBFpMrMfS3h",
            "name": "Test Track",
            "type": "track",
            "uri": "spotify:track:WSB9PMCMqpdEBFpMrMfS3h",
            "href": "https://api.spotify.com/v1/tracks/WSB9PMCMqpdEBFpMrMfS3h",
            "external_urls": {"spotify": "https://open.spotify.com/track/WSB9PMCMqpdEBFpMrMfS3h"},
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album": {"id": "4kBp5iVByDSAUc0lb78jCZ", "name": "Test Album"},
            "duration_ms": 180000,
            "explicit": False,
            "track_number": 1,
            "disc_number": 1,
            "available_markets": ["US", "CA"],
            "popularity": 60,
            "is_local": False,
            "is_playable": True
        }
        self.episode = {
            "id": "6xYt8hztD8Mo9QUM7jTNVw",
            "name": "Test Episode",
            "type": "episode",
            "uri": "spotify:episode:6xYt8hztD8Mo9QUM7jTNVw",
            "href": "https://api.spotify.com/v1/episodes/6xYt8hztD8Mo9QUM7jTNVw",
            "external_urls": {"spotify": "https://open.spotify.com/episode/6xYt8hztD8Mo9QUM7jTNVw"},
            "show": {"id": "rIXYSewNRnkAGFfGVpvE5e", "name": "Test Show"},
            "description": "A test episode",
            "duration_ms": 3600000,
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "explicit": False,
            "images": [],
            "is_externally_hosted": False,
            "is_playable": True,
            "language": "en",
            "languages": ["en"],
            "audio_preview_url": None,
            "resume_point": {"fully_played": False, "resume_position_ms": 0},
            "restrictions": {}
        }
        DB.clear()
        DB['users'] = {self.user['id']: self.user}
        DB['current_user'] = {"id": self.user['id']}
        DB['playlists'] = {self.playlist['id']: self.playlist}
        DB['playlist_tracks'] = {self.playlist['id']: []}
        DB['tracks'] = {self.track['id']: self.track}
        DB['episodes'] = {self.episode['id']: self.episode}

    def tearDown(self):
        DB.clear()
        DB.update(copy.deepcopy(self._orig_db))

    def test_add_tracks_to_playlist_append(self):
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertIn("snapshot_id", result)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][-1]['track']['id'], self.track['id'])
        self.assertEqual(DB['playlists'][self.playlist['id']]['tracks']['total'], 1)
        self.assertEqual(DB['playlists'][self.playlist['id']]['snapshot_id'], result['snapshot_id'])

    def test_add_tracks_to_playlist_insert_position(self):
        uris1 = [f"spotify:track:{self.track['id']}"]
        add_items_to_playlist(self.playlist['id'], uris1)
        track2 = copy.deepcopy(self.track)
        track2['id'] = 'NEWTRACKID1234567890'
        DB['tracks'][track2['id']] = track2
        uris2 = [f"spotify:track:{track2['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris2, position=0)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['id'], track2['id'])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][1]['track']['id'], self.track['id'])
        self.assertEqual(DB['playlists'][self.playlist['id']]['tracks']['total'], 2)
        self.assertEqual(DB['playlists'][self.playlist['id']]['snapshot_id'], result['snapshot_id'])

    def test_add_episodes_to_playlist(self):
        uris = [f"spotify:episode:{self.episode['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][-1]['track']['id'], self.episode['id'])
        self.assertEqual(DB['playlists'][self.playlist['id']]['tracks']['total'], 1)
        self.assertEqual(DB['playlists'][self.playlist['id']]['snapshot_id'], result['snapshot_id'])

    def test_invalid_playlist_id(self):
        with self.assertRaises(custom_errors.NoResultsFoundError):
            add_items_to_playlist("nonexistent", [f"spotify:track:{self.track['id']}"])

    def test_invalid_track_uri(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], ["not-a-spotify-uri"])

    def test_nonexistent_track(self):
        with self.assertRaises(custom_errors.NoResultsFoundError):
            add_items_to_playlist(self.playlist['id'], ["spotify:track:DOESNOTEXIST123"])

    def test_nonexistent_episode(self):
        with self.assertRaises(custom_errors.NoResultsFoundError):
            add_items_to_playlist(self.playlist['id'], ["spotify:episode:DOESNOTEXIST123"])

    def test_position_out_of_bounds(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], [f"spotify:track:{self.track['id']}"], position=5)

    def test_more_than_100_uris(self):
        uris = [f"spotify:track:{self.track['id']}"] * 101
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], uris)

    def test_empty_uri_list(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], [])

    def test_invalid_uri_format(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], ["spotify:album:123456"])

    def test_authentication_error(self):
        DB['current_user'] = {"id": "nonexistent"}
        with self.assertRaises(custom_errors.AuthenticationError):
            add_items_to_playlist(self.playlist['id'], [f"spotify:track:{self.track['id']}"])

    def test_position_negative(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], [f"spotify:track:{self.track['id']}"], position=-1)

    def test_uri_not_string(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], [12345])

    def test_position_not_integer(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            add_items_to_playlist(self.playlist['id'], [f"spotify:track:{self.track['id']}"], position="zero")

    def test_add_multiple_tracks_and_episodes(self):
        """Test adding multiple tracks and episodes in one call."""
        track2 = copy.deepcopy(self.track)
        track2['id'] = 'TRACK2ID1234567890'
        DB['tracks'][track2['id']] = track2
        episode2 = copy.deepcopy(self.episode)
        episode2['id'] = 'EPISODE2ID1234567890'
        DB['episodes'][episode2['id']] = episode2
        uris = [f"spotify:track:{self.track['id']}", f"spotify:episode:{self.episode['id']}", f"spotify:track:{track2['id']}", f"spotify:episode:{episode2['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(len(DB['playlist_tracks'][self.playlist['id']]), 4)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['id'], self.track['id'])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][1]['track']['id'], self.episode['id'])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][2]['track']['id'], track2['id'])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][3]['track']['id'], episode2['id'])

    def test_add_at_end_position(self):
        """Test adding at the end (position == len(playlist_tracks))."""
        uris = [f"spotify:track:{self.track['id']}"]
        add_items_to_playlist(self.playlist['id'], uris)
        uris2 = [f"spotify:episode:{self.episode['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris2, position=1)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][1]['track']['id'], self.episode['id'])

    def test_add_to_playlist_with_existing_tracks(self):
        """Test adding to a playlist with existing tracks."""
        uris = [f"spotify:track:{self.track['id']}"]
        add_items_to_playlist(self.playlist['id'], uris)
        uris2 = [f"spotify:episode:{self.episode['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris2)
        self.assertEqual(len(DB['playlist_tracks'][self.playlist['id']]), 2)

    def test_add_with_missing_user(self):
        """Test adding with missing user in DB."""
        DB['users'].pop(self.user['id'])
        with self.assertRaises(custom_errors.AuthenticationError):
            add_items_to_playlist(self.playlist['id'], [f"spotify:track:{self.track['id']}"])

    def test_add_with_missing_playlist_tracks(self):
        """Test adding with missing playlist_tracks in DB."""
        # Initialize playlist_tracks table since we assume it always exists
        DB['playlist_tracks'] = {}
        result = add_items_to_playlist(self.playlist['id'], [f"spotify:track:{self.track['id']}"])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_missing_tracks_in_db(self):
        """Test adding with missing tracks in DB."""
        DB['tracks'].pop(self.track['id'])
        with self.assertRaises(custom_errors.NoResultsFoundError):
            add_items_to_playlist(self.playlist['id'], [f"spotify:track:{self.track['id']}"])

    def test_add_with_missing_episodes_in_db(self):
        """Test adding with missing episodes in DB."""
        DB['episodes'].pop(self.episode['id'])
        with self.assertRaises(custom_errors.NoResultsFoundError):
            add_items_to_playlist(self.playlist['id'], [f"spotify:episode:{self.episode['id']}"])

    def test_add_with_optional_fields_missing_in_episode(self):
        """Test adding with all optional fields missing in episode."""
        episode = copy.deepcopy(self.episode)
        for key in list(episode.keys()):
            if key not in ['id', 'name', 'type', 'uri', 'href', 'external_urls', 'show', 'duration_ms', 'explicit', 'is_playable', 'release_date', 'release_date_precision', 'description', 'language', 'languages', 'resume_point']:
                episode.pop(key)
        episode['id'] = 'EPISODEOPTIONALMISSING'
        DB['episodes'][episode['id']] = episode
        uris = [f"spotify:episode:{episode['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][-1]['track']['id'], episode['id'])

    def test_add_with_mix_of_valid_and_invalid_uris(self):
        """Test adding with a mix of valid and invalid URIs (should fail)."""
        uris = [f"spotify:track:{self.track['id']}", "spotify:track:DOESNOTEXIST"]
        with self.assertRaises(custom_errors.NoResultsFoundError):
            add_items_to_playlist(self.playlist['id'], uris)

    def test_add_with_duplicate_uris(self):
        """Test adding with duplicate URIs."""
        uris = [f"spotify:track:{self.track['id']}", f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['id'], self.track['id'])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][1]['track']['id'], self.track['id'])

    def test_add_with_not_playable(self):
        """Test adding with a track/episode that is not playable."""
        track = copy.deepcopy(self.track)
        track['id'] = 'NOTPLAYABLETRACK'
        track['is_playable'] = False
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertFalse(DB['playlist_tracks'][self.playlist['id']][0]['track']['is_playable'])

    def test_add_with_local(self):
        """Test adding with a track/episode that is local."""
        track = copy.deepcopy(self.track)
        track['id'] = 'LOCALTRACK'
        track['is_local'] = True
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertTrue(DB['playlist_tracks'][self.playlist['id']][0]['track']['is_local'])

    def test_add_with_restrictions(self):
        """Test adding with a track/episode with restrictions."""
        track = copy.deepcopy(self.track)
        track['id'] = 'RESTRICTEDTRACK'
        track['restrictions'] = {'reason': 'market'}
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertIn('reason', DB['playlist_tracks'][self.playlist['id']][0]['track']['restrictions'])

    def test_add_with_preview_url(self):
        """Test adding with a track/episode with preview_url."""
        track = copy.deepcopy(self.track)
        track['id'] = 'PREVIEWTRACK'
        track['preview_url'] = 'http://example.com/preview.mp3'
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['preview_url'], 'http://example.com/preview.mp3')

    def test_add_with_popularity(self):
        """Test adding with a track/episode with popularity."""
        track = copy.deepcopy(self.track)
        track['id'] = 'POPULARTRACK'
        track['popularity'] = 99
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['popularity'], 99)

    def test_add_with_external_ids(self):
        """Test adding with a track/episode with external_ids."""
        track = copy.deepcopy(self.track)
        track['id'] = 'EXTERNALIDTRACK'
        track['external_ids'] = {'isrc': 'USRC12345678'}
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertIn('isrc', DB['playlist_tracks'][self.playlist['id']][0]['track']['external_ids'])

    def test_add_with_linked_from(self):
        """Test adding with a track/episode with linked_from."""
        track = copy.deepcopy(self.track)
        track['id'] = 'LINKEDFROMTRACK'
        track['linked_from'] = {'id': 'originaltrackid'}
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertIn('id', DB['playlist_tracks'][self.playlist['id']][0]['track']['linked_from'])

    def test_add_with_missing_required_fields(self):
        """Test adding with a track/episode with missing required fields (should fail)."""
        track = copy.deepcopy(self.track)
        track['id'] = 'MISSINGFIELDS'
        del track['name']
        DB['tracks'][track['id']] = track
        uris = [f"spotify:track:{track['id']}"]
        with self.assertRaises(Exception):
            add_items_to_playlist(self.playlist['id'], uris)

    def test_add_with_playlist_no_tracks_key(self):
        """Test adding with a playlist that has no tracks key (should fail)."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTRACKSKEY'
        del playlist['tracks']
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        with self.assertRaises(Exception):
            add_items_to_playlist(playlist['id'], uris)

    def test_add_with_playlist_no_snapshot_id(self):
        """Test adding with a playlist that has no snapshot_id (should still work)."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOSNAPSHOTID'
        if 'snapshot_id' in playlist:
            del playlist['snapshot_id']
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_add_with_playlist_missing_optional_fields(self):
        """Test adding with a playlist that has no images, description, or followers."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOOPTIONALFIELDS'
        for key in ['images', 'description', 'followers']:
            if key in playlist:
                del playlist[key]
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_collaborative_private(self):
        """Test adding with a playlist that is collaborative or private."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'COLLABPRIVATE'
        playlist['collaborative'] = True
        playlist['public'] = False
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_public(self):
        """Test adding with a playlist that is public."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'PUBLIC'
        playlist['public'] = True
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_not_public(self):
        """Test adding with a playlist that is not public."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTPUBLIC'
        playlist['public'] = False
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_not_collaborative(self):
        """Test adding with a playlist that is not collaborative."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTCOLLAB'
        playlist['collaborative'] = False
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_not_owned_by_user(self):
        """Test adding with a playlist that is not owned by the user."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTOWNED'
        playlist['owner'] = {'id': 'otheruser', 'display_name': 'Other User'}
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_owned_by_user(self):
        """Test adding with a playlist that is owned by the user."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'OWNEDBYUSER'
        playlist['owner'] = {'id': self.user['id'], 'display_name': self.user['display_name']}
        DB['playlists'][playlist['id']] = playlist
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_followed_by_user(self):
        """Test adding with a playlist that is followed by the user."""
        if 'followed_playlists' not in DB:
            DB['followed_playlists'] = {}
        DB['followed_playlists'][self.user['id']] = {self.playlist['id']: {'public': True, 'followed_at': '2023-01-01T00:00:00Z'}}
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['id'], self.track['id'])

    def test_add_with_playlist_not_followed_by_user(self):
        """Test adding with a playlist that is not followed by the user."""
        if 'followed_playlists' in DB and self.user['id'] in DB['followed_playlists']:
            DB['followed_playlists'][self.user['id']] = {}
        uris = [f"spotify:track:{self.track['id']}"]
        result = add_items_to_playlist(self.playlist['id'], uris)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['id'], self.track['id'])

class TestRemoveTracksFromPlaylist(unittest.TestCase):
    def setUp(self):
        self._orig_db = copy.deepcopy(DB)
        self.user = {
            "id": "smuqPNFPXrJKcEt943KrY8",
            "display_name": "Test User",
            "type": "user",
            "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8",
            "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
            "external_urls": {"spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"},
        }
        self.playlist = {
            "id": "QDyH69WryQ7dPRXVOFmy2V",
            "name": "Test Playlist",
            "type": "playlist",
            "uri": "spotify:playlist:QDyH69WryQ7dPRXVOFmy2V",
            "href": "https://api.spotify.com/v1/playlists/QDyH69WryQ7dPRXVOFmy2V",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/QDyH69WryQ7dPRXVOFmy2V"},
            "owner": {"id": self.user['id'], "display_name": self.user['display_name']},
            "public": True,
            "collaborative": False,
            "description": "A test playlist",
            "images": [],
            "tracks": {"total": 0},
            "followers": {"total": 0},
            "snapshot_id": "snapshot_0"
        }
        self.track = {
            "id": "WSB9PMCMqpdEBFpMrMfS3h",
            "name": "Test Track",
            "type": "track",
            "uri": "spotify:track:WSB9PMCMqpdEBFpMrMfS3h",
            "href": "https://api.spotify.com/v1/tracks/WSB9PMCMqpdEBFpMrMfS3h",
            "external_urls": {"spotify": "https://open.spotify.com/track/WSB9PMCMqpdEBFpMrMfS3h"},
            "artists": [{"id": "W0e71GNltAWtwmOaMZcm1J", "name": "Test Artist"}],
            "album": {"id": "4kBp5iVByDSAUc0lb78jCZ", "name": "Test Album"},
            "duration_ms": 180000,
            "explicit": False,
            "track_number": 1,
            "disc_number": 1,
            "available_markets": ["US", "CA"],
            "popularity": 60,
            "is_local": False,
            "is_playable": True
        }
        self.episode = {
            "id": "6xYt8hztD8Mo9QUM7jTNVw",
            "name": "Test Episode",
            "type": "episode",
            "uri": "spotify:episode:6xYt8hztD8Mo9QUM7jTNVw",
            "href": "https://api.spotify.com/v1/episodes/6xYt8hztD8Mo9QUM7jTNVw",
            "external_urls": {"spotify": "https://open.spotify.com/episode/6xYt8hztD8Mo9QUM7jTNVw"},
            "show": {"id": "rIXYSewNRnkAGFfGVpvE5e", "name": "Test Show"},
            "description": "A test episode",
            "duration_ms": 3600000,
            "release_date": "2023-01-01",
            "release_date_precision": "day",
            "explicit": False,
            "images": [],
            "is_externally_hosted": False,
            "is_playable": True,
            "language": "en",
            "languages": ["en"],
            "audio_preview_url": None,
            "resume_point": {"fully_played": False, "resume_position_ms": 0},
            "restrictions": {}
        }
        DB.clear()
        DB['users'] = {self.user['id']: self.user}
        DB['current_user'] = {"id": self.user['id']}
        DB['playlists'] = {self.playlist['id']: self.playlist}
        DB['playlist_tracks'] = {self.playlist['id']: []}
        DB['tracks'] = {self.track['id']: self.track}
        DB['episodes'] = {self.episode['id']: self.episode}

    def tearDown(self):
        DB.clear()
        DB.update(copy.deepcopy(self._orig_db))

    def test_remove_single_track(self):
        """Test removing a single track from playlist."""
        add_items_to_playlist(self.playlist['id'], [self.track['uri']])
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']], [])
        self.assertIn('snapshot_id', result)

    def test_remove_multiple_tracks_and_episodes(self):
        """Test removing multiple tracks and episodes from playlist."""
        track2 = copy.deepcopy(self.track)
        track2['id'] = 'TRACK2ID1234567890'
        track2['uri'] = f"spotify:track:{track2['id']}"
        DB['tracks'][track2['id']] = track2
        episode2 = copy.deepcopy(self.episode)
        episode2['id'] = 'EPISODE2ID1234567890'
        episode2['uri'] = f"spotify:episode:{episode2['id']}"
        DB['episodes'][episode2['id']] = episode2
        add_items_to_playlist(self.playlist['id'], [self.track['uri'], self.episode['uri'], track2['uri'], episode2['uri']])
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}, {"uri": self.episode['uri']}])
        self.assertEqual(len(DB['playlist_tracks'][self.playlist['id']]), 2)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][0]['track']['id'], track2['id'])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']][1]['track']['id'], episode2['id'])

    def test_remove_all_occurrences(self):
        """Test removing all occurrences of a track."""
        add_items_to_playlist(self.playlist['id'], [self.track['uri'], self.track['uri'], self.track['uri']])
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']], [])

    def test_remove_with_snapshot_id(self):
        """Test removing with correct snapshot_id."""
        add_items_to_playlist(self.playlist['id'], [self.track['uri']])
        old_snapshot = DB['playlists'][self.playlist['id']]['snapshot_id']
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}], snapshot_id=old_snapshot)
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']], [])
        self.assertNotEqual(DB['playlists'][self.playlist['id']]['snapshot_id'], old_snapshot)

    def test_remove_with_invalid_snapshot_id(self):
        """Test removing with invalid snapshot_id (should error)."""
        add_items_to_playlist(self.playlist['id'], [self.track['uri']])
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}], snapshot_id="invalid_snapshot")

    def test_remove_with_missing_playlist(self):
        """Test removing with missing playlist (should error)."""
        with self.assertRaises(Exception):
            remove_tracks_from_playlist("nonexistent", [{"uri": self.track['uri']}])

    def test_remove_with_missing_playlist_tracks(self):
        """Test removing with missing playlist_tracks (should error)."""
        DB.pop('playlist_tracks')
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}])

    def test_remove_with_invalid_input(self):
        """Test removing with invalid input (not a list, empty list, invalid uri, etc.)."""
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], "notalist")
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], [])
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], [{"uri": "not-a-spotify-uri"}])
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], [{"noturi": self.track['uri']}])

    def test_remove_track_not_in_playlist(self):
        """Test removing a track/episode not in playlist (should not error)."""
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']], [])

    def test_remove_from_empty_playlist(self):
        """Test removing from an empty playlist (should not error)."""
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']], [])

    def test_remove_with_mix_of_valid_and_invalid_uris(self):
        """Test removing with a mix of valid and invalid uris (should error)."""
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}, {"uri": "not-a-spotify-uri"}])

    def test_remove_with_duplicate_uris_in_request(self):
        """Test removing with duplicate uris in request."""
        add_items_to_playlist(self.playlist['id'], [self.track['uri'], self.track['uri']])
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}, {"uri": self.track['uri']}])
        self.assertEqual(DB['playlist_tracks'][self.playlist['id']], [])

    def test_remove_with_more_than_100_uris(self):
        """Test removing with more than 100 uris (should error)."""
        uris = [{"uri": self.track['uri']}] * 101
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(self.playlist['id'], uris)

    def test_remove_with_playlist_no_tracks_key(self):
        """Test removing with a playlist that has no tracks key (should error)."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTRACKSKEY'
        del playlist['tracks']
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        with self.assertRaises(Exception):
            remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])

    def test_remove_with_playlist_no_snapshot_id(self):
        """Test removing with a playlist that has no snapshot_id (should still work)."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOSNAPSHOTID'
        if 'snapshot_id' in playlist:
            del playlist['snapshot_id']
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        result = remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_remove_with_playlist_collaborative_private(self):
        """Test removing with a playlist that is collaborative or private."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'COLLABPRIVATE'
        playlist['collaborative'] = True
        playlist['public'] = False
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        result = remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_remove_with_playlist_public(self):
        """Test removing with a playlist that is public."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'PUBLIC'
        playlist['public'] = True
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        result = remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_remove_with_playlist_not_public(self):
        """Test removing with a playlist that is not public."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTPUBLIC'
        playlist['public'] = False
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        result = remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_remove_with_playlist_not_collaborative(self):
        """Test removing with a playlist that is not collaborative."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTCOLLAB'
        playlist['collaborative'] = False
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        result = remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_remove_with_playlist_not_owned_by_user(self):
        """Test removing with a playlist that is not owned by the user."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'NOTOWNED'
        playlist['owner'] = {'id': 'otheruser', 'display_name': 'Other User'}
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        result = remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_remove_with_playlist_owned_by_user(self):
        """Test removing with a playlist that is owned by the user."""
        playlist = copy.deepcopy(self.playlist)
        playlist['id'] = 'OWNEDBYUSER'
        playlist['owner'] = {'id': self.user['id'], 'display_name': self.user['display_name']}
        DB['playlists'][playlist['id']] = playlist
        DB['playlist_tracks'][playlist['id']] = []
        result = remove_tracks_from_playlist(playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][playlist['id']])

    def test_remove_with_playlist_followed_by_user(self):
        """Test removing with a playlist that is followed by the user."""
        if 'followed_playlists' not in DB:
            DB['followed_playlists'] = {}
        DB['followed_playlists'][self.user['id']] = {self.playlist['id']: {'public': True, 'followed_at': '2023-01-01T00:00:00Z'}}
        DB['playlist_tracks'][self.playlist['id']] = []
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][self.playlist['id']])

    def test_remove_with_playlist_not_followed_by_user(self):
        """Test removing with a playlist that is not followed by the user."""
        if 'followed_playlists' in DB and self.user['id'] in DB['followed_playlists']:
            DB['followed_playlists'][self.user['id']] = {}
        DB['playlist_tracks'][self.playlist['id']] = []
        result = remove_tracks_from_playlist(self.playlist['id'], [{"uri": self.track['uri']}])
        self.assertIn('snapshot_id', DB['playlists'][self.playlist['id']])

class TestGetCurrentUsersPlaylists(unittest.TestCase):
    def setUp(self):
        self._orig_db = copy.deepcopy(DB)
        self.user = {
            "id": "smuqPNFPXrJKcEt943KrY8",
            "display_name": "Test User",
            "type": "user",
            "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8",
            "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
            "external_urls": {"spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"},
        }
        self.playlist1 = {
            "id": "QDyH69WryQ7dPRXVOFmy2V",
            "name": "Test Playlist",
            "type": "playlist",
            "uri": "spotify:playlist:QDyH69WryQ7dPRXVOFmy2V",
            "href": "https://api.spotify.com/v1/playlists/QDyH69WryQ7dPRXVOFmy2V",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/QDyH69WryQ7dPRXVOFmy2V"},
            "owner": {"id": self.user['id'], "display_name": self.user['display_name']},
            "public": True,
            "collaborative": False,
            "description": "A test playlist",
            "images": [],
            "tracks": {"total": 0},
            "followers": {"total": 0},
            "snapshot_id": "snapshot_0"
        }
        self.playlist2 = {
            "id": "UgsCJJwpTgHzXvFg3QW3yQ",
            "name": "Workout Mix",
            "type": "playlist",
            "uri": "spotify:playlist:UgsCJJwpTgHzXvFg3QW3yQ",
            "href": "https://api.spotify.com/v1/playlists/UgsCJJwpTgHzXvFg3QW3yQ",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/UgsCJJwpTgHzXvFg3QW3yQ"},
            "owner": {"id": self.user['id'], "display_name": self.user['display_name']},
            "public": True,
            "collaborative": False,
            "description": "High energy tracks for workouts",
            "images": [],
            "tracks": {"total": 12},
            "followers": {"total": 250},
            "snapshot_id": "snapshot_456"
        }
        DB.clear()
        DB['users'] = {self.user['id']: self.user}
        DB['current_user'] = {"id": self.user['id']}
        DB['playlists'] = {self.playlist1['id']: self.playlist1, self.playlist2['id']: self.playlist2}
        DB['user_playlists'] = {self.user['id']: [self.playlist1['id'], self.playlist2['id']]}

    def tearDown(self):
        DB.clear()
        DB.update(copy.deepcopy(self._orig_db))

    def test_get_playlists_basic(self):
        
        result = get_current_users_playlists()
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['items'][0]['id'], self.playlist1['id'])
        self.assertEqual(result['items'][1]['id'], self.playlist2['id'])
        self.assertEqual(result['limit'], 20)
        self.assertEqual(result['offset'], 0)
        self.assertIn('href', result)
        self.assertIsNone(result['next'])
        self.assertIsNone(result['previous'])

    def test_get_playlists_pagination(self):
        
        result = get_current_users_playlists(limit=1, offset=0)
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['id'], self.playlist1['id'])
        self.assertEqual(result['next'], 'https://api.spotify.com/v1/me/playlists?limit=1&offset=1')
        self.assertIsNone(result['previous'])
        result2 = get_current_users_playlists(limit=1, offset=1)
        self.assertEqual(result2['items'][0]['id'], self.playlist2['id'])
        self.assertIsNone(result2['next'])
        self.assertEqual(result2['previous'], 'https://api.spotify.com/v1/me/playlists?limit=1&offset=0')

    def test_get_playlists_offset_beyond_total(self):
        
        result = get_current_users_playlists(limit=1, offset=2)
        self.assertEqual(result['items'], [])
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['limit'], 1)
        self.assertEqual(result['offset'], 2)
        self.assertIsNone(result['next'])
        self.assertEqual(result['previous'], 'https://api.spotify.com/v1/me/playlists?limit=1&offset=1')

    def test_get_playlists_no_playlists(self):
        
        DB['user_playlists'][self.user['id']] = []
        result = get_current_users_playlists()
        self.assertEqual(result['items'], [])
        self.assertEqual(result['total'], 0)

    def test_get_playlists_invalid_limit(self):
        
        with self.assertRaises(Exception):
            get_current_users_playlists(limit=0)
        with self.assertRaises(Exception):
            get_current_users_playlists(limit=51)
        with self.assertRaises(Exception):
            get_current_users_playlists(limit='twenty')

    def test_get_playlists_invalid_offset(self):
        
        with self.assertRaises(Exception):
            get_current_users_playlists(offset=-1)
        with self.assertRaises(Exception):
            get_current_users_playlists(offset='zero')

    def test_get_playlists_authentication_error(self):
        
        DB['current_user'] = {"id": "nonexistent"}
        with self.assertRaises(Exception):
            get_current_users_playlists()
        DB.pop('current_user')
        with self.assertRaises(Exception):
            get_current_users_playlists()

    def test_get_playlists_missing_optional_fields(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'NOOPTIONALFIELDS'
        for key in ['images', 'description', 'followers', 'snapshot_id']:
            if key in playlist:
                del playlist[key]
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_current_users_playlists()
        self.assertTrue(any(p['id'] == 'NOOPTIONALFIELDS' for p in result['items']))

    def test_get_playlists_various_owners(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'OTHEROWNER'
        playlist['owner'] = {'id': 'otheruser', 'display_name': 'Other User'}
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_current_users_playlists()
        self.assertTrue(any(p['id'] == 'OTHEROWNER' for p in result['items']))

    def test_get_playlists_collaborative_and_public(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'COLLABPUBLIC'
        playlist['collaborative'] = True
        playlist['public'] = True
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_current_users_playlists()
        self.assertTrue(any(p['id'] == 'COLLABPUBLIC' for p in result['items']))

    def test_get_playlists_private(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'PRIVATE'
        playlist['public'] = False
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_current_users_playlists()
        self.assertTrue(any(p['id'] == 'PRIVATE' for p in result['items']))

class TestGetUserPlaylists(unittest.TestCase):
    def setUp(self):
        self._orig_db = copy.deepcopy(DB)
        self.user = {
            "id": "smuqPNFPXrJKcEt943KrY8",
            "display_name": "Test User",
            "type": "user",
            "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8",
            "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
            "external_urls": {"spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"},
        }
        self.playlist1 = {
            "id": "QDyH69WryQ7dPRXVOFmy2V",
            "name": "Test Playlist",
            "type": "playlist",
            "uri": "spotify:playlist:QDyH69WryQ7dPRXVOFmy2V",
            "href": "https://api.spotify.com/v1/playlists/QDyH69WryQ7dPRXVOFmy2V",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/QDyH69WryQ7dPRXVOFmy2V"},
            "owner": {"id": self.user['id'], "display_name": self.user['display_name']},
            "public": True,
            "collaborative": False,
            "description": "A test playlist",
            "images": [],
            "tracks": {"total": 0},
            "followers": {"total": 0},
            "snapshot_id": "snapshot_0"
        }
        self.playlist2 = {
            "id": "UgsCJJwpTgHzXvFg3QW3yQ",
            "name": "Workout Mix",
            "type": "playlist",
            "uri": "spotify:playlist:UgsCJJwpTgHzXvFg3QW3yQ",
            "href": "https://api.spotify.com/v1/playlists/UgsCJJwpTgHzXvFg3QW3yQ",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/UgsCJJwpTgHzXvFg3QW3yQ"},
            "owner": {"id": self.user['id'], "display_name": self.user['display_name']},
            "public": True,
            "collaborative": False,
            "description": "High energy tracks for workouts",
            "images": [],
            "tracks": {"total": 12},
            "followers": {"total": 250},
            "snapshot_id": "snapshot_456"
        }
        DB.clear()
        DB['users'] = {self.user['id']: self.user}
        DB['playlists'] = {self.playlist1['id']: self.playlist1, self.playlist2['id']: self.playlist2}
        DB['user_playlists'] = {self.user['id']: [self.playlist1['id'], self.playlist2['id']]}

    def tearDown(self):
        DB.clear()
        DB.update(copy.deepcopy(self._orig_db))

    def test_get_user_playlists_basic(self):
        
        result = get_user_playlists(self.user['id'])
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['items'][0]['id'], self.playlist1['id'])
        self.assertEqual(result['items'][1]['id'], self.playlist2['id'])
        self.assertEqual(result['limit'], 20)
        self.assertEqual(result['offset'], 0)
        self.assertIn('href', result)
        self.assertIsNone(result['next'])
        self.assertIsNone(result['previous'])

    def test_get_user_playlists_pagination(self):
        
        result = get_user_playlists(self.user['id'], limit=1, offset=0)
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['id'], self.playlist1['id'])
        self.assertEqual(result['next'], f'https://api.spotify.com/v1/users/{self.user["id"]}/playlists?limit=1&offset=1')
        self.assertIsNone(result['previous'])
        result2 = get_user_playlists(self.user['id'], limit=1, offset=1)
        self.assertEqual(result2['items'][0]['id'], self.playlist2['id'])
        self.assertIsNone(result2['next'])
        self.assertEqual(result2['previous'], f'https://api.spotify.com/v1/users/{self.user["id"]}/playlists?limit=1&offset=0')

    def test_get_user_playlists_offset_beyond_total(self):
        
        result = get_user_playlists(self.user['id'], limit=1, offset=2)
        self.assertEqual(result['items'], [])
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['limit'], 1)
        self.assertEqual(result['offset'], 2)
        self.assertIsNone(result['next'])
        self.assertEqual(result['previous'], f'https://api.spotify.com/v1/users/{self.user["id"]}/playlists?limit=1&offset=1')

    def test_get_user_playlists_no_playlists(self):
        
        DB['user_playlists'][self.user['id']] = []
        result = get_user_playlists(self.user['id'])
        self.assertEqual(result['items'], [])
        self.assertEqual(result['total'], 0)

    def test_get_user_playlists_invalid_user_id(self):
        
        with self.assertRaises(Exception):
            get_user_playlists(12345)
        with self.assertRaises(Exception):
            get_user_playlists("")

    def test_get_user_playlists_invalid_limit(self):
        
        with self.assertRaises(Exception):
            get_user_playlists(self.user['id'], limit=0)
        with self.assertRaises(Exception):
            get_user_playlists(self.user['id'], limit=51)
        with self.assertRaises(Exception):
            get_user_playlists(self.user['id'], limit='twenty')

    def test_get_user_playlists_invalid_offset(self):
        
        with self.assertRaises(Exception):
            get_user_playlists(self.user['id'], offset=-1)
        with self.assertRaises(Exception):
            get_user_playlists(self.user['id'], offset='zero')

    def test_get_user_playlists_no_results_found(self):
        
        with self.assertRaises(Exception):
            get_user_playlists('nonexistent')

    def test_get_user_playlists_missing_optional_fields(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'NOOPTIONALFIELDS'
        for key in ['images', 'description', 'followers', 'snapshot_id']:
            if key in playlist:
                del playlist[key]
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_user_playlists(self.user['id'])
        self.assertTrue(any(p['id'] == 'NOOPTIONALFIELDS' for p in result['items']))

    def test_get_user_playlists_various_owners(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'OTHEROWNER'
        playlist['owner'] = {'id': 'otheruser', 'display_name': 'Other User'}
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_user_playlists(self.user['id'])
        self.assertTrue(any(p['id'] == 'OTHEROWNER' for p in result['items']))

    def test_get_user_playlists_collaborative_and_public(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'COLLABPUBLIC'
        playlist['collaborative'] = True
        playlist['public'] = True
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_user_playlists(self.user['id'])
        self.assertTrue(any(p['id'] == 'COLLABPUBLIC' for p in result['items']))

    def test_get_user_playlists_private(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'PRIVATE'
        playlist['public'] = False
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_user_playlists(self.user['id'])
        self.assertTrue(any(p['id'] == 'PRIVATE' for p in result['items']))

    def test_user_playlists_some_missing_in_db(self):
        
        # Add a playlist ID that doesn't exist in DB['playlists']
        DB['user_playlists'][self.user['id']].append('MISSINGID')
        result = get_user_playlists(self.user['id'])
        self.assertTrue(all(p['id'] != 'MISSINGID' for p in result['items']))

    def test_user_playlists_db_playlists_empty(self):
        
        DB['playlists'] = {}
        result = get_user_playlists(self.user['id'])
        self.assertEqual(result['items'], [])

    def test_user_playlists_db_user_playlists_missing(self):
        
        # Initialize user_playlists table since we assume it always exists
        DB['user_playlists'] = {}
        result = get_user_playlists(self.user['id'])
        self.assertEqual(result['items'], [])

    def test_user_playlists_missing_optional_fields_in_playlist(self):
        
        playlist = dict(self.playlist1)
        playlist['id'] = 'NOOPTIONAL'
        for key in ['images', 'description', 'followers', 'snapshot_id']:
            if key in playlist:
                del playlist[key]
        DB['playlists'][playlist['id']] = playlist
        DB['user_playlists'][self.user['id']].append(playlist['id'])
        result = get_user_playlists(self.user['id'])
        self.assertTrue(any(p['id'] == 'NOOPTIONAL' for p in result['items']))

class TestCreatePlaylist(unittest.TestCase):
    def setUp(self):
        self._orig_db = copy.deepcopy(DB)
        self.user = {
            "id": "smuqPNFPXrJKcEt943KrY8",
            "display_name": "Test User",
            "type": "user",
            "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8",
            "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
            "external_urls": {"spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"},
        }
        DB.clear()
        DB['users'] = {self.user['id']: self.user}
        DB['playlists'] = {}
        DB['user_playlists'] = {self.user['id']: []}
        DB['playlist_tracks'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(copy.deepcopy(self._orig_db))

    def test_create_playlist_all_fields(self):
        
        result = create_playlist(
            user_id=self.user['id'],
            name="My Playlist",
            public=False,
            collaborative=True,
            description="A cool playlist"
        )
        self.assertEqual(result['name'], "My Playlist")
        self.assertFalse(result['public'])
        self.assertTrue(result['collaborative'])
        self.assertEqual(result['description'], "A cool playlist")
        self.assertEqual(result['owner']['id'], self.user['id'])
        self.assertIn(result['id'], DB['playlists'])
        self.assertIn(result['id'], DB['user_playlists'][self.user['id']])
        self.assertIn(result['id'], DB['playlist_tracks'])
        self.assertEqual(DB['playlist_tracks'][result['id']], [])
        self.assertEqual(result['tracks']['total'], 0)
        self.assertEqual(result['followers']['total'], 0)
        self.assertEqual(result['type'], 'playlist')
        self.assertTrue(result['uri'].startswith('spotify:playlist:'))
        self.assertTrue(result['href'].startswith('https://api.spotify.com/v1/playlists/'))
        self.assertTrue(result['external_urls']['spotify'].startswith('https://open.spotify.com/playlist/'))
        self.assertIn('snapshot_id', result)

    def test_create_playlist_required_fields_only(self):
        
        result = create_playlist(
            user_id=self.user['id'],
            name="Just Name"
        )
        self.assertEqual(result['name'], "Just Name")
        self.assertTrue(result['public'])
        self.assertFalse(result['collaborative'])
        self.assertIsNone(result['description'])
        self.assertEqual(result['owner']['id'], self.user['id'])
        self.assertIn(result['id'], DB['playlists'])
        self.assertIn(result['id'], DB['user_playlists'][self.user['id']])
        self.assertIn(result['id'], DB['playlist_tracks'])
        self.assertEqual(DB['playlist_tracks'][result['id']], [])

    def test_create_playlist_invalid_user_id(self):
        
        with self.assertRaises(Exception):
            create_playlist(user_id=12345, name="Test")
        with self.assertRaises(Exception):
            create_playlist(user_id="", name="Test")
        with self.assertRaises(Exception):
            create_playlist(user_id="nonexistent", name="Test")

    def test_create_playlist_invalid_name(self):
        
        with self.assertRaises(Exception):
            create_playlist(user_id=self.user['id'], name="")
        with self.assertRaises(Exception):
            create_playlist(user_id=self.user['id'], name=12345)

    def test_create_playlist_invalid_public_collaborative(self):
        
        with self.assertRaises(Exception):
            create_playlist(user_id=self.user['id'], name="Test", public="yes")
        with self.assertRaises(Exception):
            create_playlist(user_id=self.user['id'], name="Test", collaborative="no")

    def test_create_playlist_invalid_description(self):
        
        with self.assertRaises(Exception):
            create_playlist(user_id=self.user['id'], name="Test", description=123)

    def test_create_multiple_playlists(self):
        
        p1 = create_playlist(user_id=self.user['id'], name="Playlist 1")
        p2 = create_playlist(user_id=self.user['id'], name="Playlist 2")
        self.assertIn(p1['id'], DB['user_playlists'][self.user['id']])
        self.assertIn(p2['id'], DB['user_playlists'][self.user['id']])
        self.assertNotEqual(p1['id'], p2['id'])
        self.assertEqual(DB['playlists'][p1['id']]['name'], "Playlist 1")
        self.assertEqual(DB['playlists'][p2['id']]['name'], "Playlist 2")

    def test_create_playlist_missing_db_structures(self):
        
        # Initialize all required tables since we assume they always exist
        DB['playlists'] = {}
        DB['user_playlists'] = {}
        DB['playlist_tracks'] = {}
        result = create_playlist(user_id=self.user['id'], name="Missing DBs")
        self.assertIn(result['id'], DB['playlists'])
        self.assertIn(result['id'], DB['user_playlists'][self.user['id']])
        self.assertIn(result['id'], DB['playlist_tracks'])

    def test_create_playlist_long_name_description(self):
        
        long_name = "A" * 300
        long_desc = "D" * 1000
        result = create_playlist(user_id=self.user['id'], name=long_name, description=long_desc)
        self.assertEqual(result['name'], long_name)
        self.assertEqual(result['description'], long_desc)

    def test_create_playlist_special_characters(self):
        
        name = "My Playlist!@#$%^&*()_+-=[]{}|;':,.<>/?"
        desc = "Description with emoji 🚀🎵"
        result = create_playlist(user_id=self.user['id'], name=name, description=desc)
        self.assertEqual(result['name'], name)
        self.assertEqual(result['description'], desc)

    def test_create_playlist_for_user_with_no_playlists(self):
        
        DB['user_playlists'][self.user['id']] = []
        result = create_playlist(user_id=self.user['id'], name="First Playlist")
        self.assertIn(result['id'], DB['user_playlists'][self.user['id']])

class TestGetPlaylistCoverImage(unittest.TestCase):
    def setUp(self):
        self._orig_db = copy.deepcopy(DB)
        self.playlist_id = "QDyH69WryQ7dPRXVOFmy2V"
        self.playlist = {
            "id": self.playlist_id,
            "name": "Test Playlist",
            "type": "playlist",
            "uri": f"spotify:playlist:{self.playlist_id}",
            "href": f"https://api.spotify.com/v1/playlists/{self.playlist_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/playlist/{self.playlist_id}"},
            "owner": {"id": "user1", "display_name": "User 1"},
            "public": True,
            "collaborative": False,
            "description": "A test playlist",
            "images": [],
            "tracks": {"total": 0},
            "followers": {"total": 0},
            "snapshot_id": "snapshot_0"
        }
        DB.clear()
        DB['playlists'] = {self.playlist_id: self.playlist}
        DB['playlist_cover_images'] = {}
        DB['playlist_images'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(copy.deepcopy(self._orig_db))

    def test_cover_image_from_playlist_cover_images(self):
        
        img = {"url": "http://cover.com/1.jpg", "height": 300, "width": 300}
        DB['playlist_cover_images'][self.playlist_id] = [img]
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, [img])

    def test_cover_image_from_playlist_images(self):
        
        img = {"url": "http://cover.com/2.jpg", "height": 200, "width": 200}
        DB['playlist_images'][self.playlist_id] = [img]
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, [img])

    def test_cover_image_from_playlist_images_field(self):
        
        img = {"url": "http://cover.com/3.jpg", "height": 100, "width": 100}
        DB['playlists'][self.playlist_id]['images'] = [img]
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, [img])

    def test_no_cover_image(self):
        
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, [])

    def test_invalid_playlist_id(self):
        
        with self.assertRaises(Exception):
            get_playlist_cover_image(12345)
        with self.assertRaises(Exception):
            get_playlist_cover_image("")

    def test_nonexistent_playlist(self):
        
        with self.assertRaises(Exception):
            get_playlist_cover_image("nonexistent")

    def test_multiple_images_in_each_source(self):
        
        imgs = [
            {"url": "http://cover.com/1.jpg", "height": 300, "width": 300},
            {"url": "http://cover.com/2.jpg", "height": 200, "width": 200}
        ]
        DB['playlist_cover_images'][self.playlist_id] = imgs
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, imgs)
        DB['playlist_cover_images'].pop(self.playlist_id)
        DB['playlist_images'][self.playlist_id] = imgs
        result2 = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result2, imgs)
        DB['playlist_images'].pop(self.playlist_id)
        DB['playlists'][self.playlist_id]['images'] = imgs
        result3 = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result3, imgs)

    def test_images_varying_sizes(self):
        
        imgs = [
            {"url": "http://cover.com/large.jpg", "height": 1000, "width": 1000},
            {"url": "http://cover.com/small.jpg", "height": 50, "width": 50}
        ]
        DB['playlist_cover_images'][self.playlist_id] = imgs
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, imgs)

    def test_images_none_or_invalid_types(self):
        
        DB['playlist_cover_images'][self.playlist_id] = None
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, [])
        DB['playlist_cover_images'][self.playlist_id] = [None, {}, {"url": None}]
        result2 = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result2, [None, {}, {"url": None}])

    def test_images_empty_dicts_or_missing_keys(self):
        
        DB['playlist_cover_images'][self.playlist_id] = [{}, {"height": 100}]
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, [{}, {"height": 100}])

    def test_images_mixed_valid_invalid(self):
        
        imgs = [
            {"url": "http://cover.com/ok.jpg", "height": 100, "width": 100},
            {},
            None,
            {"url": None}
        ]
        DB['playlist_cover_images'][self.playlist_id] = imgs
        result = get_playlist_cover_image(self.playlist_id)
        self.assertEqual(result, imgs)

if __name__ == '__main__':
    unittest.main()
import unittest
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import InvalidInputError, NoResultsFoundError, AuthenticationError, InvalidMarketError
from .. import get_playlist, change_playlist_details, get_playlist_items, update_playlist_items
from ..SimulationEngine import utils


class TestSpotifyPlaylistAPI(unittest.TestCase):
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
            "tracks": {
                "WSB9PMCMqpdEBFpMrMfS3h": {
                    "id": "WSB9PMCMqpdEBFpMrMfS3h",
                    "name": "Test Track",
                    "type": "track",
                    "uri": "spotify:track:WSB9PMCMqpdEBFpMrMfS3h",
                    "href": "https://api.spotify.com/v1/tracks/WSB9PMCMqpdEBFpMrMfS3h",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/WSB9PMCMqpdEBFpMrMfS3h"
                    },
                    "artists": [
                        {
                            "id": "W0e71GNltAWtwmOaMZcm1J",
                            "name": "Test Artist"
                        }
                    ],
                    "album": {
                        "id": "4kBp5iVByDSAUc0lb78jCZ",
                        "name": "Test Album"
                    },
                    "duration_ms": 180000,
                    "explicit": False,
                    "track_number": 1,
                    "disc_number": 1,
                    "available_markets": ["US", "CA"],
                    "popularity": 60,
                    "is_local": False,
                    "is_playable": True,
                    "external_ids": {},
                    "linked_from": None,
                    "restrictions": {},
                    "preview_url": None
                },
                "u2q7XZcxZpFNq2yIBhXZ6h": {
                    "id": "u2q7XZcxZpFNq2yIBhXZ6h",
                    "name": "Rock Anthem",
                    "type": "track",
                    "uri": "spotify:track:u2q7XZcxZpFNq2yIBhXZ6h",
                    "href": "https://api.spotify.com/v1/tracks/u2q7XZcxZpFNq2yIBhXZ6h",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/u2q7XZcxZpFNq2yIBhXZ6h"
                    },
                    "artists": [
                        {
                            "id": "DqJ4SeZM7iQuxSkKOdQvTB",
                            "name": "Popular Band"
                        }
                    ],
                    "album": {
                        "id": "5V17F52VsJ3ZDIF1iYxe6D",
                        "name": "Greatest Hits"
                    },
                    "duration_ms": 240000,
                    "explicit": True,
                    "track_number": 3,
                    "disc_number": 1,
                    "available_markets": ["US", "CA", "UK", "DE"],
                    "popularity": 85,
                    "is_local": False,
                    "is_playable": True,
                    "external_ids": {},
                    "linked_from": None,
                    "restrictions": {},
                    "preview_url": None
                }
            },
            "playlists": {
                "QDyH69WryQ7dPRXVOFmy2V": {
                    "id": "QDyH69WryQ7dPRXVOFmy2V",
                    "name": "Test Playlist",
                    "type": "playlist",
                    "uri": "spotify:playlist:QDyH69WryQ7dPRXVOFmy2V",
                    "href": "https://api.spotify.com/v1/playlists/QDyH69WryQ7dPRXVOFmy2V",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/playlist/QDyH69WryQ7dPRXVOFmy2V"
                    },
                    "owner": {
                        "id": "smuqPNFPXrJKcEt943KrY8",
                        "display_name": "Test User"
                    },
                    "public": True,
                    "collaborative": False,
                    "description": "A test playlist",
                    "images": [],
                    "tracks": {
                        "total": 2
                    },
                    "followers": {
                        "total": 100
                    },
                    "snapshot_id": "snapshot_123"
                },
                "UgsCJJwpTgHzXvFg3QW3yQ": {
                    "id": "UgsCJJwpTgHzXvFg3QW3yQ",
                    "name": "Another User's Playlist",
                    "type": "playlist",
                    "uri": "spotify:playlist:UgsCJJwpTgHzXvFg3QW3yQ",
                    "href": "https://api.spotify.com/v1/playlists/UgsCJJwpTgHzXvFg3QW3yQ",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/playlist/UgsCJJwpTgHzXvFg3QW3yQ"
                    },
                    "owner": {
                        "id": "SLvTb0e3Rp3oLJ8YXl0dC5",
                        "display_name": "Another User"
                    },
                    "public": True,
                    "collaborative": False,
                    "description": "Another user's playlist",
                    "images": [],
                    "tracks": {
                        "total": 1
                    },
                    "followers": {
                        "total": 50
                    },
                    "snapshot_id": "snapshot_456"
                }
            },
            "playlist_tracks": {
                "QDyH69WryQ7dPRXVOFmy2V": [
                    {
                        "added_at": "2023-01-01T00:00:00Z",
                        "added_by": {
                            "id": "smuqPNFPXrJKcEt943KrY8",
                            "display_name": "Test User",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"
                            },
                            "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
                            "type": "user",
                            "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8"
                        },
                        "is_local": False,
                        "track": {
                            "id": "WSB9PMCMqpdEBFpMrMfS3h",
                            "name": "Test Track",
                            "type": "track",
                            "uri": "spotify:track:WSB9PMCMqpdEBFpMrMfS3h"
                        }
                    },
                    {
                        "added_at": "2023-01-02T00:00:00Z",
                        "added_by": {
                            "id": "smuqPNFPXrJKcEt943KrY8",
                            "display_name": "Test User",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/user/smuqPNFPXrJKcEt943KrY8"
                            },
                            "href": "https://api.spotify.com/v1/users/smuqPNFPXrJKcEt943KrY8",
                            "type": "user",
                            "uri": "spotify:user:smuqPNFPXrJKcEt943KrY8"
                        },
                        "is_local": False,
                        "track": {
                            "id": "u2q7XZcxZpFNq2yIBhXZ6h",
                            "name": "Rock Anthem",
                            "type": "track",
                            "uri": "spotify:track:u2q7XZcxZpFNq2yIBhXZ6h"
                        }
                    }
                ],
                "UgsCJJwpTgHzXvFg3QW3yQ": [
                    {
                        "added_at": "2023-01-01T00:00:00Z",
                        "added_by": {
                            "id": "SLvTb0e3Rp3oLJ8YXl0dC5",
                            "display_name": "Another User",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/user/SLvTb0e3Rp3oLJ8YXl0dC5"
                            },
                            "href": "https://api.spotify.com/v1/users/SLvTb0e3Rp3oLJ8YXl0dC5",
                            "type": "user",
                            "uri": "spotify:user:SLvTb0e3Rp3oLJ8YXl0dC5"
                        },
                        "is_local": False,
                        "track": {
                            "id": "WSB9PMCMqpdEBFpMrMfS3h",
                            "name": "Test Track",
                            "type": "track",
                            "uri": "spotify:track:WSB9PMCMqpdEBFpMrMfS3h"
                        }
                    }
                ]
            },
            "current_user": {
                "id": "smuqPNFPXrJKcEt943KrY8"
            }
        })
        
        # Set current user after database is populated
        utils.set_current_user("smuqPNFPXrJKcEt943KrY8")

    # Test get_playlist function
    def test_get_playlist_success(self):
        result = get_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(result["id"], "QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(result["name"], "Test Playlist")
        self.assertEqual(result["type"], "playlist")
        self.assertTrue("tracks" in result)
        self.assertEqual(result["tracks"]["total"], 2)

    def test_get_playlist_with_market_filtering(self):
        result = get_playlist("QDyH69WryQ7dPRXVOFmy2V", market="US")
        self.assertEqual(result["id"], "QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(result["tracks"]["total"], 2)  # Both tracks available in US

    def test_get_playlist_with_market_filtering_no_results(self):
        result = get_playlist("QDyH69WryQ7dPRXVOFmy2V", market="JP")
        self.assertEqual(result["id"], "QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(result["tracks"]["total"], 0)  # No tracks available in JP

    def test_get_playlist_invalid_playlist_id(self):
        with self.assertRaises(InvalidInputError):
            get_playlist("")
        with self.assertRaises(InvalidInputError):
            get_playlist(123)

    def test_get_playlist_invalid_market(self):
        with self.assertRaises(InvalidMarketError):
            get_playlist("QDyH69WryQ7dPRXVOFmy2V", market="INVALID")

    def test_get_playlist_not_found(self):
        with self.assertRaises(NoResultsFoundError):
            get_playlist("nonexistent_playlist")

    def test_get_playlist_invalid_fields(self):
        with self.assertRaises(InvalidInputError):
            get_playlist("QDyH69WryQ7dPRXVOFmy2V", fields=123)

    # Test change_playlist_details function
    def test_change_playlist_details_success(self):
        result = change_playlist_details(
            "QDyH69WryQ7dPRXVOFmy2V",
            name="Updated Playlist Name",
            public=False,
            collaborative=True,
            description="Updated description"
        )
        self.assertEqual(result, {})
        
        # Verify changes were applied
        playlist = get_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(playlist["name"], "Updated Playlist Name")
        self.assertFalse(playlist["public"])
        self.assertTrue(playlist["collaborative"])
        self.assertEqual(playlist["description"], "Updated description")

    def test_change_playlist_details_partial_update(self):
        result = change_playlist_details("QDyH69WryQ7dPRXVOFmy2V", name="New Name Only")
        self.assertEqual(result, {})
        
        playlist = get_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(playlist["name"], "New Name Only")
        # Other fields should remain unchanged
        self.assertTrue(playlist["public"])
        self.assertFalse(playlist["collaborative"])

    def test_change_playlist_details_invalid_playlist_id(self):
        with self.assertRaises(InvalidInputError):
            change_playlist_details("", name="Test")

    def test_change_playlist_details_not_found(self):
        with self.assertRaises(NoResultsFoundError):
            change_playlist_details("nonexistent_playlist", name="Test")

    def test_change_playlist_details_unauthorized(self):
        with self.assertRaises(AuthenticationError):
            change_playlist_details("UgsCJJwpTgHzXvFg3QW3yQ", name="Test")

    def test_change_playlist_details_invalid_name(self):
        with self.assertRaises(InvalidInputError):
            change_playlist_details("QDyH69WryQ7dPRXVOFmy2V", name=123)
        with self.assertRaises(InvalidInputError):
            change_playlist_details("QDyH69WryQ7dPRXVOFmy2V", name="a" * 101)

    def test_change_playlist_details_invalid_public(self):
        with self.assertRaises(InvalidInputError):
            change_playlist_details("QDyH69WryQ7dPRXVOFmy2V", public="true")

    def test_change_playlist_details_invalid_collaborative(self):
        with self.assertRaises(InvalidInputError):
            change_playlist_details("QDyH69WryQ7dPRXVOFmy2V", collaborative="true")

    def test_change_playlist_details_invalid_description(self):
        with self.assertRaises(InvalidInputError):
            change_playlist_details("QDyH69WryQ7dPRXVOFmy2V", description=123)
        with self.assertRaises(InvalidInputError):
            change_playlist_details("QDyH69WryQ7dPRXVOFmy2V", description="a" * 301)

    # Test get_playlist_items function
    def test_get_playlist_items_success(self):
        result = get_playlist_items("QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["limit"], 20)
        self.assertEqual(result["offset"], 0)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["track"]["name"], "Test Track")
        self.assertEqual(result["items"][1]["track"]["name"], "Rock Anthem")

    def test_get_playlist_items_with_pagination(self):
        result = get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", limit=1, offset=1)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["offset"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["track"]["name"], "Rock Anthem")

    def test_get_playlist_items_with_market_filtering(self):
        result = get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", market="US")
        self.assertEqual(result["total"], 2)  # Both tracks available in US

    def test_get_playlist_items_with_market_filtering_no_results(self):
        result = get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", market="JP")
        self.assertEqual(result["total"], 0)  # No tracks available in JP

    def test_get_playlist_items_invalid_playlist_id(self):
        with self.assertRaises(InvalidInputError):
            get_playlist_items("")

    def test_get_playlist_items_not_found(self):
        with self.assertRaises(NoResultsFoundError):
            get_playlist_items("nonexistent_playlist")

    def test_get_playlist_items_invalid_limit(self):
        with self.assertRaises(InvalidInputError):
            get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", limit=0)
        with self.assertRaises(InvalidInputError):
            get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", limit=51)

    def test_get_playlist_items_invalid_offset(self):
        with self.assertRaises(InvalidInputError):
            get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", offset=-1)

    def test_get_playlist_items_invalid_market(self):
        with self.assertRaises(InvalidMarketError):
            get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", market="INVALID")

    def test_get_playlist_items_invalid_additional_types(self):
        with self.assertRaises(InvalidInputError):
            get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", additional_types=123)
        with self.assertRaises(InvalidInputError):
            get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", additional_types="invalid_type")

    def test_get_playlist_items_valid_additional_types(self):
        result = get_playlist_items("QDyH69WryQ7dPRXVOFmy2V", additional_types="track,episode")
        self.assertEqual(result["total"], 2)

    # Test update_playlist_items function
    def test_update_playlist_items_replace_tracks_success(self):
        result = update_playlist_items(
            "QDyH69WryQ7dPRXVOFmy2V",
            uris=["spotify:track:WSB9PMCMqpdEBFpMrMfS3h"]
        )
        self.assertIn("snapshot_id", result)
        
        # Verify tracks were replaced
        playlist = get_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(playlist["tracks"]["total"], 1)
        self.assertEqual(playlist["tracks"]["items"][0]["track"]["name"], "Test Track")

    def test_update_playlist_items_reorder_tracks_success(self):
        result = update_playlist_items(
            "QDyH69WryQ7dPRXVOFmy2V",
            range_start=0,
            insert_before=2,
            range_length=1
        )
        self.assertIn("snapshot_id", result)
        
        # Verify tracks were reordered (moved first track to end)
        playlist = get_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(playlist["tracks"]["total"], 2)
        # First track should now be "Rock Anthem", second should be "Test Track"
        self.assertEqual(playlist["tracks"]["items"][0]["track"]["name"], "Rock Anthem")
        self.assertEqual(playlist["tracks"]["items"][1]["track"]["name"], "Test Track")

    def test_update_playlist_items_with_snapshot_id(self):
        playlist = get_playlist("QDyH69WryQ7dPRXVOFmy2V")
        current_snapshot = playlist["snapshot_id"]
        
        result = update_playlist_items(
            "QDyH69WryQ7dPRXVOFmy2V",
            uris=["spotify:track:WSB9PMCMqpdEBFpMrMfS3h"],
            snapshot_id=current_snapshot
        )
        self.assertIn("snapshot_id", result)

    def test_update_playlist_items_invalid_playlist_id(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("", uris=["spotify:track:test"])

    def test_update_playlist_items_not_found(self):
        with self.assertRaises(NoResultsFoundError):
            update_playlist_items("nonexistent_playlist", uris=["spotify:track:test"])

    def test_update_playlist_items_unauthorized(self):
        with self.assertRaises(AuthenticationError):
            update_playlist_items("UgsCJJwpTgHzXvFg3QW3yQ", uris=["spotify:track:test"])

    def test_update_playlist_items_invalid_uris(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", uris="not_a_list")
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", uris=[""] * 101)  # Too many URIs
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", uris=[123])  # Invalid URI type

    def test_update_playlist_items_invalid_range_start(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=-1, insert_before=1)
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start="0", insert_before=1)

    def test_update_playlist_items_invalid_insert_before(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=0, insert_before=-1)
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=0, insert_before="1")

    def test_update_playlist_items_invalid_range_length(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=0, insert_before=1, range_length=0)
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=0, insert_before=1, range_length="1")

    def test_update_playlist_items_invalid_snapshot_id(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", uris=["spotify:track:test"], snapshot_id=123)

    def test_update_playlist_items_mismatched_snapshot_id(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", uris=["spotify:track:test"], snapshot_id="wrong_snapshot")

    def test_update_playlist_items_range_start_out_of_bounds(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=10, insert_before=1)

    def test_update_playlist_items_insert_before_out_of_bounds(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=0, insert_before=10)

    def test_update_playlist_items_no_operation_specified(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V")

    def test_update_playlist_items_incomplete_reorder_params(self):
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", range_start=0)  # Missing insert_before
        with self.assertRaises(InvalidInputError):
            update_playlist_items("QDyH69WryQ7dPRXVOFmy2V", insert_before=1)  # Missing range_start

    def test_update_playlist_items_default_range_length(self):
        result = update_playlist_items(
            "QDyH69WryQ7dPRXVOFmy2V",
            range_start=0,
            insert_before=2
            # range_length defaults to 1
        )
        self.assertIn("snapshot_id", result)
        
        playlist = get_playlist("QDyH69WryQ7dPRXVOFmy2V")
        self.assertEqual(playlist["tracks"]["total"], 2)

    def test_get_playlist_with_additional_types_track(self):
        # Only 'track' type is present, so should return all
        result = get_playlist("QDyH69WryQ7dPRXVOFmy2V", additional_types="track")
        self.assertEqual(result["tracks"]["total"], 2)

    def test_get_playlist_with_additional_types_episode(self):
        # No 'episode' type in test data, should return 0
        result = get_playlist("QDyH69WryQ7dPRXVOFmy2V", additional_types="episode")
        self.assertEqual(result["tracks"]["total"], 0)

    def test_get_playlist_with_additional_types_both(self):
        # Only 'track' type is present, so should return all
        result = get_playlist("QDyH69WryQ7dPRXVOFmy2V", additional_types="track,episode")
        self.assertEqual(result["tracks"]["total"], 2)

    def test_get_playlist_invalid_additional_types(self):
        with self.assertRaises(InvalidInputError):
            get_playlist("QDyH69WryQ7dPRXVOFmy2V", additional_types=123)
        with self.assertRaises(InvalidInputError):
            get_playlist("QDyH69WryQ7dPRXVOFmy2V", additional_types="invalid_type")


if __name__ == '__main__':
    unittest.main()
