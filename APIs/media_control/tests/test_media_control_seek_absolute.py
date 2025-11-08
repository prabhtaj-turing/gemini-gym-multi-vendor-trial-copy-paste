import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, reset_db
from ..SimulationEngine.db_models import MediaItem, MediaPlayer, AndroidDB
from ..SimulationEngine.models import PlaybackState, MediaType
from ..SimulationEngine.custom_errors import ValidationError, NoMediaPlayerError, NoMediaItemError
from .. import seek_absolute

class TestSeekAbsolute(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        self.media_item = MediaItem(
            id="track1", title="Song", artist="Artist", album="Album",
            duration_seconds=200, current_position_seconds=50,
            media_type=MediaType.TRACK, app_name="Spotify"
        )
        self.player = MediaPlayer(
            app_name="Spotify", current_media=self.media_item,
            playback_state=PlaybackState.PLAYING, playlist=[self.media_item], current_playlist_index=0
        )
        DB["media_players"] = {"Spotify": self.player.model_dump()}
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

    def test_seek_absolute_success(self):
        result = seek_absolute(100)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_absolute_no_media(self):
        self.player.current_media = None
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: seek_absolute(100),
            NoMediaItemError,
            "No media item loaded in app: Spotify"
        )

    def test_seek_absolute_no_player_found(self):
        DB["active_media_player"] = "NonExistentApp"
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: seek_absolute(100),
            NoMediaPlayerError,
            "No active media player found"
        )

    def test_seek_absolute_invalid_position(self):
        self.assert_error_behavior(
            lambda: seek_absolute("invalid"),
            ValidationError,
            "position must be an integer, got str"
        )

    def test_seek_absolute_beyond_duration(self):
        # Should succeed with clamping to duration
        result = seek_absolute(250)  # Beyond duration
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_absolute_negative_position(self):
        # Should succeed with clamping to 0
        result = seek_absolute(-10)  # Negative position
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_absolute_zero_position(self):
        result = seek_absolute(0)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_absolute_float_position(self):
        self.assert_error_behavior(
            lambda: seek_absolute(100.5),
            ValidationError,
            "position must be an integer, got float"
        )

    def test_seek_absolute_exact_duration(self):
        result = seek_absolute(200)  # Exact duration
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        
        # Validate database after changes
        self.validate_test_db()

if __name__ == "__main__":
    unittest.main() 