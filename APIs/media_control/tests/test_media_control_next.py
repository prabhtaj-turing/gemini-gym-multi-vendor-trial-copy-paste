import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, reset_db
from ..SimulationEngine.db_models import MediaItem, MediaPlayer, AndroidDB
from ..SimulationEngine.models import PlaybackState, MediaType
from ..SimulationEngine.custom_errors import ValidationError, NoMediaPlayerError, NoPlaylistError, NoMediaItemError, InvalidPlaybackStateError
from .. import next

class TestNext(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        self.media_item1 = MediaItem(
            id="track1", title="Song1", artist="Artist1", album="Album1",
            duration_seconds=200, current_position_seconds=50,
            media_type=MediaType.TRACK, app_name="Spotify"
        )
        self.media_item2 = MediaItem(
            id="track2", title="Song2", artist="Artist2", album="Album2",
            duration_seconds=180, current_position_seconds=0,
            media_type=MediaType.TRACK, app_name="Spotify"
        )
        self.player = MediaPlayer(
            app_name="Spotify", current_media=self.media_item1,
            playback_state=PlaybackState.PLAYING, playlist=[self.media_item1, self.media_item2], current_playlist_index=0
        )
        DB["media_players"] = {"Spotify": self.player.model_dump()}
        # Set active media player
        DB["active_media_player"] = "Spotify"
        
        # Validate the test data conforms to the model
        self.validate_test_db()

    def tearDown(self):
        reset_db()

    def validate_test_db(self):
        """Validate that the current database state conforms to the AndroidDB model"""
        try:
            validated_db = AndroidDB(**DB)
            self.assertIsInstance(validated_db, AndroidDB)
        except Exception as e:
            self.fail(f"Test database validation failed: {e}")

    def test_next_success(self):
        result = next()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song2")
        
        # Validate database after changes
        self.validate_test_db()

    def test_next_no_playlist(self):
        self.player.playlist = []
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: next(),
            NoPlaylistError,
            "No playlist available in app: Spotify"
        )

    def test_next_no_media(self):
        self.player.current_media = None
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: next(),
            NoMediaItemError,
            "No media item loaded in app: Spotify"
        )

    def test_next_no_active_player(self):
        DB["active_media_player"] = None
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: next(),
            NoMediaPlayerError,
            "No active media player found"
        )

    def test_next_no_player_found(self):
        DB["active_media_player"] = "NonExistentApp"
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: next(),
            NoMediaPlayerError,
            "No active media player found"
        )

    def test_next_last_track(self):
        # Set to last track
        self.player.current_playlist_index = 1
        self.player.current_media = self.media_item2
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: next(),
            InvalidPlaybackStateError,
            "Already at the last item in playlist"
        )

if __name__ == "__main__":
    unittest.main() 