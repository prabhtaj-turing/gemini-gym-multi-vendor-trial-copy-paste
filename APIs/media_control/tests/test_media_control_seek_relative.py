import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, reset_db
from ..SimulationEngine.db_models import MediaItem, MediaPlayer, AndroidDB
from ..SimulationEngine.models import PlaybackState, MediaType
from ..SimulationEngine.custom_errors import ValidationError, NoMediaPlayerError, NoMediaItemError
from .. import seek_relative

class TestSeekRelative(BaseTestCaseWithErrorHandler):
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

    def test_seek_relative_forward_success(self):
        result = seek_relative(30)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_relative_backward_success(self):
        result = seek_relative(-20)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_relative_no_media(self):
        self.player.current_media = None
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: seek_relative(30),
            NoMediaItemError,
            "No media item loaded in app: Spotify"
        )

    def test_seek_relative_no_player_found(self):
        DB["active_media_player"] = "NonExistentApp"
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: seek_relative(30),
            NoMediaPlayerError,
            "No active media player found"
        )

    def test_seek_relative_invalid_seconds(self):
        self.assert_error_behavior(
            lambda: seek_relative("invalid"),
            ValidationError,
            "offset must be an integer, got str"
        )

    def test_seek_relative_beyond_duration(self):
        # Should succeed with clamping to duration
        result = seek_relative(200)  # Seek beyond duration
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_relative_before_start(self):
        # Should succeed with clamping to 0
        result = seek_relative(-100)  # Seek before start
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_relative_zero_seconds(self):
        result = seek_relative(0)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        
        # Validate database after changes
        self.validate_test_db()

    def test_seek_relative_float_seconds(self):
        self.assert_error_behavior(
            lambda: seek_relative(30.5),
            ValidationError,
            "offset must be an integer, got float"
        )

    def test_seek_relative_negative_float(self):
        self.assert_error_behavior(
            lambda: seek_relative(-15.5),
            ValidationError,
            "offset must be an integer, got float"
        )

if __name__ == "__main__":
    unittest.main() 