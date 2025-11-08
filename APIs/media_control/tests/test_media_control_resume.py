import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, reset_db
from ..SimulationEngine.db_models import MediaItem, MediaPlayer, AndroidDB
from ..SimulationEngine.models import PlaybackState, MediaType
from ..SimulationEngine.custom_errors import NoMediaPlayerError, InvalidPlaybackStateError, NoMediaItemError
from .. import resume

class TestResume(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        self.media_item = MediaItem(
            id="track1", title="Song", artist="Artist", album="Album",
            duration_seconds=200, current_position_seconds=50,
            media_type=MediaType.TRACK, app_name="Spotify"
        )
        self.player = MediaPlayer(
            app_name="Spotify", current_media=self.media_item,
            playback_state=PlaybackState.PAUSED, playlist=[self.media_item], current_playlist_index=0
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

    def test_resume_success(self):
        result = resume()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["title"], "Song")
        
        # Validate database after changes
        self.validate_test_db()

    def test_resume_no_media(self):
        self.player.current_media = None
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: resume(),
            NoMediaItemError,
            "No media item loaded in app: Spotify"
        )

    def test_resume_no_active_player(self):
        DB["active_media_player"] = None
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: resume(),
            NoMediaPlayerError,
            "No active media player found"
        )

    def test_resume_no_player_found(self):
        DB["active_media_player"] = "NonExistentApp"
        self.validate_test_db()
        
        self.assert_error_behavior(
            lambda: resume(),
            NoMediaPlayerError,
            "No active media player found"
        )

    def test_resume_playing_media(self):
        self.player.playback_state = PlaybackState.PLAYING
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        # Should succeed as no-op - resume works from both PAUSED and PLAYING states
        result = resume()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["result"], "Success")
        self.assertEqual(result["title"], "Song")
        self.assertEqual(result["app_name"], "Spotify")
        self.assertEqual(result["media_type"], "TRACK")
        
        # Verify the DB state remains PLAYING (no change)
        updated_player_data = DB["media_players"]["Spotify"]
        self.assertEqual(updated_player_data["playback_state"], PlaybackState.PLAYING.value)

    def test_resume_stopped_media(self):
        self.player.playback_state = PlaybackState.STOPPED
        DB["media_players"]["Spotify"] = self.player.model_dump()
        self.validate_test_db()
        
        # Should fail - resume only works from PAUSED or PLAYING state, not STOPPED
        self.assert_error_behavior(
            lambda: resume(),
            InvalidPlaybackStateError,
            "Cannot resume media in app: Spotify. Media must be paused or already playing."
        )

if __name__ == "__main__":
    unittest.main() 