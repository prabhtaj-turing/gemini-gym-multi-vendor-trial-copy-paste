import unittest
from pydantic import ValidationError
from ..SimulationEngine.db_models import MediaItem, MediaPlayer, AndroidDB
from ..SimulationEngine.models import (
    PlaybackTargetState, PlaybackPositionChangeType, MediaAttributeType, MediaRating, MediaType,
    ActionSummary, PlaybackState
)
from ..SimulationEngine.custom_errors import (
    NoMediaItemError, InvalidPlaybackStateError, NoPlaylistError
)


class TestEnums(unittest.TestCase):
    """Test all enum classes."""
    
    def test_playback_target_state(self):
        """Test PlaybackTargetState enum values."""
        self.assertEqual(PlaybackTargetState.STOP, "STOP")
        self.assertEqual(PlaybackTargetState.PAUSE, "PAUSE")
        self.assertEqual(PlaybackTargetState.RESUME, "RESUME")
        
    def test_playback_position_change_type(self):
        """Test PlaybackPositionChangeType enum values."""
        self.assertEqual(PlaybackPositionChangeType.SEEK_TO_POSITION, "SEEK_TO_POSITION")
        self.assertEqual(PlaybackPositionChangeType.SEEK_RELATIVE, "SEEK_RELATIVE")
        self.assertEqual(PlaybackPositionChangeType.SKIP_TO_NEXT, "SKIP_TO_NEXT")
        self.assertEqual(PlaybackPositionChangeType.SKIP_TO_PREVIOUS, "SKIP_TO_PREVIOUS")
        self.assertEqual(PlaybackPositionChangeType.REPLAY, "REPLAY")
        
    def test_media_attribute_type(self):
        """Test MediaAttributeType enum values."""
        self.assertEqual(MediaAttributeType.RATING, "RATING")
        
    def test_media_rating(self):
        """Test MediaRating enum values."""
        self.assertEqual(MediaRating.POSITIVE, "POSITIVE")
        self.assertEqual(MediaRating.NEGATIVE, "NEGATIVE")
        
    def test_media_type(self):
        """Test MediaType enum values."""
        self.assertEqual(MediaType.TRACK, "TRACK")
        self.assertEqual(MediaType.ALBUM, "ALBUM")
        self.assertEqual(MediaType.PLAYLIST, "PLAYLIST")
        self.assertEqual(MediaType.VIDEO, "VIDEO")
        self.assertEqual(MediaType.MOVIE, "MOVIE")
        self.assertEqual(MediaType.OTHER, "OTHER")
        
    def test_playback_state(self):
        """Test PlaybackState enum values."""
        self.assertEqual(PlaybackState.PLAYING, "PLAYING")
        self.assertEqual(PlaybackState.PAUSED, "PAUSED")
        self.assertEqual(PlaybackState.STOPPED, "STOPPED")


class TestActionSummary(unittest.TestCase):
    """Test ActionSummary model."""
    
    def test_action_summary_creation(self):
        """Test creating an ActionSummary."""
        action = ActionSummary(
            result="Success",
            title="Test Song",
            app_name="Spotify",
            media_type=MediaType.TRACK
        )
        
        self.assertEqual(action.result, "Success")
        self.assertEqual(action.title, "Test Song")
        self.assertEqual(action.app_name, "Spotify")
        self.assertEqual(action.media_type, MediaType.TRACK)
        
    def test_action_summary_model_dump(self):
        """Test ActionSummary model_dump method."""
        action = ActionSummary(
            result="Success",
            title="Test Song",
            app_name="Spotify",
            media_type=MediaType.TRACK
        )
        
        data = action.model_dump()
        self.assertEqual(data["result"], "Success")
        self.assertEqual(data["title"], "Test Song")
        self.assertEqual(data["app_name"], "Spotify")
        self.assertEqual(data["media_type"], "TRACK")


class TestMediaItem(unittest.TestCase):
    """Test MediaItem model."""
    
    def test_media_item_creation_minimal(self):
        """Test creating a MediaItem with minimal required fields."""
        media = MediaItem(
            id="track1",
            title="Test Song",
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        
        self.assertEqual(media.id, "track1")
        self.assertEqual(media.title, "Test Song")
        self.assertEqual(media.media_type, MediaType.TRACK)
        self.assertEqual(media.app_name, "Spotify")
        self.assertIsNone(media.artist)
        self.assertIsNone(media.album)
        self.assertIsNone(media.duration_seconds)
        self.assertEqual(media.current_position_seconds, 0)
        self.assertIsNone(media.rating)
        
    def test_media_item_validation_duration_negative(self):
        """Test that negative duration is not allowed."""
        with self.assertRaises(ValidationError):
            MediaItem(
                id="track1",
                title="Test Song",
                duration_seconds=-10,
                media_type=MediaType.TRACK,
                app_name="Spotify"
            )
            
    def test_media_item_validation_position_negative(self):
        """Test that negative position is not allowed."""
        with self.assertRaises(ValidationError):
            MediaItem(
                id="track1",
                title="Test Song",
                current_position_seconds=-10,
                media_type=MediaType.TRACK,
                app_name="Spotify"
            )
            
    def test_media_item_creation_full(self):
        """Test creating a MediaItem with all fields."""
        media = MediaItem(
            id="track1",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            duration_seconds=200,
            current_position_seconds=50,
            media_type=MediaType.TRACK,
            rating=MediaRating.POSITIVE,
            app_name="Spotify"
        )
        
        self.assertEqual(media.id, "track1")
        self.assertEqual(media.title, "Test Song")
        self.assertEqual(media.artist, "Test Artist")
        self.assertEqual(media.album, "Test Album")
        self.assertEqual(media.duration_seconds, 200)
        self.assertEqual(media.current_position_seconds, 50)
        self.assertEqual(media.media_type, MediaType.TRACK)
        self.assertEqual(media.rating, MediaRating.POSITIVE)
        self.assertEqual(media.app_name, "Spotify")
        
    def test_media_item_model_dump(self):
        """Test MediaItem model_dump method."""
        media = MediaItem(
            id="track1",
            title="Test Song",
            artist="Test Artist",
            duration_seconds=200,
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        
        data = media.model_dump()
        self.assertEqual(data["id"], "track1")
        self.assertEqual(data["title"], "Test Song")
        self.assertEqual(data["artist"], "Test Artist")
        self.assertEqual(data["duration_seconds"], 200)
        self.assertEqual(data["media_type"], MediaType.TRACK)
        self.assertEqual(data["app_name"], "Spotify")


class TestMediaPlayer(unittest.TestCase):
    """Test MediaPlayer model and its methods."""
    
    def setUp(self):
        """Set up test data."""
        self.media_item1 = MediaItem(
            id="track1",
            title="Song1",
            artist="Artist1",
            duration_seconds=200,
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        self.media_item2 = MediaItem(
            id="track2",
            title="Song2",
            artist="Artist2",
            duration_seconds=180,
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        self.player = MediaPlayer(
            app_name="Spotify",
            current_media=self.media_item1,
            playback_state=PlaybackState.PLAYING,
            playlist=[self.media_item1, self.media_item2],
            current_playlist_index=0
        )
        
    def test_media_player_creation(self):
        """Test creating a MediaPlayer."""
        player = MediaPlayer(app_name="Spotify")
        
        self.assertEqual(player.app_name, "Spotify")
        self.assertIsNone(player.current_media)
        self.assertEqual(player.playback_state, PlaybackState.STOPPED)
        self.assertEqual(player.playlist, [])
        self.assertEqual(player.current_playlist_index, 0)
        
    def test_play_media(self):
        """Test play_media method."""
        player = MediaPlayer(app_name="Spotify")
        media = MediaItem(
            id="track1",
            title="Test Song",
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        
        player.play_media(media)
        
        self.assertEqual(player.current_media, media)
        self.assertEqual(player.playback_state, PlaybackState.PLAYING)
        self.assertEqual(player.current_media.current_position_seconds, 0)
        
    def test_pause_media_success(self):
        """Test pause_media method when playing."""
        result = self.player.pause_media()
        
        self.assertEqual(self.player.playback_state, PlaybackState.PAUSED)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_pause_media_already_paused(self):
        """Test pause_media method when already paused."""
        self.player.playback_state = PlaybackState.PAUSED
        
        # Should succeed as no-op
        result = self.player.pause_media()
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
    
    def test_pause_media_stopped_state(self):
        """Test pause_media method when media is stopped."""
        self.player.playback_state = PlaybackState.STOPPED
        
        with self.assertRaises(InvalidPlaybackStateError) as cm:
            self.player.pause_media()
        
        self.assertIn("Cannot pause media in PlaybackState.STOPPED state", str(cm.exception))
            
    def test_resume_media_success(self):
        """Test resume_media method when paused."""
        self.player.playback_state = PlaybackState.PAUSED
        
        result = self.player.resume_media()
        
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_resume_media_no_media(self):
        """Test resume_media method when no media is loaded."""
        player = MediaPlayer(app_name="Spotify")
        player.playback_state = PlaybackState.PAUSED
        
        with self.assertRaises(NoMediaItemError):
            player.resume_media()
            
    def test_resume_media_not_paused(self):
        """Test resume_media method when not paused."""
        # Should succeed as no-op - resume works from both PAUSED and PLAYING states
        result = self.player.resume_media()
        
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
        # Verify the state remains PLAYING (no change)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
    
    def test_resume_media_invalid_state(self):
        """Test resume_media method when in invalid state (not PAUSED)."""
        # Set to an invalid state by directly assigning a string that's not a valid PlaybackState
        # This bypasses the enum validation to test the error condition
        self.player.playback_state = "INVALID_STATE"
        
        # This should raise an error because "INVALID_STATE" is not PAUSED
        with self.assertRaises(InvalidPlaybackStateError) as cm:
            self.player.resume_media()
        
        self.assertIn("Cannot resume media in app: Spotify. Media must be paused or already playing.", str(cm.exception))
            
    def test_stop_media_success(self):
        """Test stop_media method."""
        result = self.player.stop_media()
        
        self.assertEqual(self.player.playback_state, PlaybackState.STOPPED)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_stop_media_already_stopped(self):
        """Test stop_media method when already stopped."""
        self.player.playback_state = PlaybackState.STOPPED
        
        # Should succeed as no-op
        result = self.player.stop_media()
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
            
    def test_next_media_success(self):
        """Test next_media method."""
        result = self.player.next_media()
        
        self.assertEqual(self.player.current_playlist_index, 1)
        self.assertEqual(self.player.current_media, self.media_item2)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song2")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_next_media_no_playlist(self):
        """Test next_media method when no playlist."""
        player = MediaPlayer(app_name="Spotify")
        player.current_media = self.media_item1
        
        with self.assertRaises(NoPlaylistError):
            player.next_media()
            
    def test_next_media_no_current_media(self):
        """Test next_media method when no current media."""
        player = MediaPlayer(app_name="Spotify")
        player.playlist = [self.media_item1, self.media_item2]
        
        with self.assertRaises(NoMediaItemError):
            player.next_media()
            
    def test_next_media_last_item(self):
        """Test next_media method when at last item."""
        self.player.current_playlist_index = 1
        self.player.current_media = self.media_item2
        
        with self.assertRaises(InvalidPlaybackStateError):
            self.player.next_media()
            
    def test_previous_media_success(self):
        """Test previous_media method."""
        self.player.current_playlist_index = 1
        self.player.current_media = self.media_item2
        
        result = self.player.previous_media()
        
        self.assertEqual(self.player.current_playlist_index, 0)
        self.assertEqual(self.player.current_media, self.media_item1)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_previous_media_no_playlist(self):
        """Test previous_media method when no playlist."""
        player = MediaPlayer(app_name="Spotify")
        player.current_media = self.media_item1
        
        with self.assertRaises(NoPlaylistError):
            player.previous_media()
            
    def test_previous_media_no_current_media(self):
        """Test previous_media method when no current media."""
        player = MediaPlayer(app_name="Spotify")
        player.playlist = [self.media_item1, self.media_item2]
        
        with self.assertRaises(NoMediaItemError):
            player.previous_media()
            
    def test_previous_media_first_item(self):
        """Test previous_media method when at first item."""
        # Should restart the current track from the beginning
        result = self.player.previous_media()
        
        self.assertEqual(self.player.current_media.current_position_seconds, 0)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
            
    def test_seek_relative_success(self):
        """Test seek_relative method."""
        result = self.player.seek_relative(30)
        
        self.assertEqual(self.player.current_media.current_position_seconds, 30)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_seek_relative_no_media(self):
        """Test seek_relative method when no media."""
        player = MediaPlayer(app_name="Spotify")
        
        with self.assertRaises(NoMediaItemError):
            player.seek_relative(30)
            
    def test_seek_relative_no_duration(self):
        """Test seek_relative method when no duration."""
        media_no_duration = MediaItem(
            id="track1",
            title="Test Song",
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        player = MediaPlayer(app_name="Spotify", current_media=media_no_duration)
        
        with self.assertRaises(InvalidPlaybackStateError):
            player.seek_relative(30)
            
    def test_seek_absolute_success(self):
        """Test seek_absolute method."""
        result = self.player.seek_absolute(100)
        
        self.assertEqual(self.player.current_media.current_position_seconds, 100)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_seek_absolute_no_media(self):
        """Test seek_absolute method when no media."""
        player = MediaPlayer(app_name="Spotify")
        
        with self.assertRaises(NoMediaItemError):
            player.seek_absolute(100)
            
    def test_seek_absolute_no_duration(self):
        """Test seek_absolute method when no duration."""
        media_no_duration = MediaItem(
            id="track1",
            title="Test Song",
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        player = MediaPlayer(app_name="Spotify", current_media=media_no_duration)
        
        with self.assertRaises(InvalidPlaybackStateError):
            player.seek_absolute(100)
            
    def test_replay_media_success(self):
        """Test replay_media method."""
        self.player.current_media.current_position_seconds = 100
        
        result = self.player.replay_media()
        
        self.assertEqual(self.player.current_media.current_position_seconds, 0)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_replay_media_no_media(self):
        """Test replay_media method when no media."""
        player = MediaPlayer(app_name="Spotify")
        
        with self.assertRaises(NoMediaItemError):
            player.replay_media()
            
    def test_like_media_success(self):
        """Test like_media method."""
        result = self.player.like_media()
        
        self.assertEqual(self.player.current_media.rating, MediaRating.POSITIVE)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_like_media_no_media(self):
        """Test like_media method when no media."""
        player = MediaPlayer(app_name="Spotify")
        
        with self.assertRaises(NoMediaItemError):
            player.like_media()
            
    def test_dislike_media_success(self):
        """Test dislike_media method."""
        result = self.player.dislike_media()
        
        self.assertEqual(self.player.current_media.rating, MediaRating.NEGATIVE)
        self.assertIsInstance(result, ActionSummary)
        self.assertEqual(result.result, "Success")
        self.assertEqual(result.title, "Song1")
        self.assertEqual(result.app_name, "Spotify")
        self.assertEqual(result.media_type, MediaType.TRACK)
        
    def test_dislike_media_no_media(self):
        """Test dislike_media method when no media."""
        player = MediaPlayer(app_name="Spotify")
        
        with self.assertRaises(NoMediaItemError):
            player.dislike_media()
            
    def test_media_player_model_dump(self):
        """Test MediaPlayer model_dump method."""
        data = self.player.model_dump()
        
        self.assertEqual(data["app_name"], "Spotify")
        self.assertEqual(data["playback_state"], PlaybackState.PLAYING)
        self.assertEqual(data["current_playlist_index"], 0)
        self.assertIsInstance(data["current_media"], dict)
        self.assertIsInstance(data["playlist"], list)
        self.assertEqual(len(data["playlist"]), 2)
        
    def test_seek_relative_beyond_duration(self):
        """Test seek_relative method beyond duration."""
        result = self.player.seek_relative(200)
        
        self.assertEqual(self.player.current_media.current_position_seconds, 200)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        
    def test_seek_relative_before_start(self):
        """Test seek_relative method before start."""
        result = self.player.seek_relative(-100)
        
        self.assertEqual(self.player.current_media.current_position_seconds, 0)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        
    def test_seek_absolute_beyond_duration(self):
        """Test seek_absolute method beyond duration."""
        result = self.player.seek_absolute(300)
        
        self.assertEqual(self.player.current_media.current_position_seconds, 200)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
        
    def test_seek_absolute_negative_position(self):
        """Test seek_absolute method with negative position."""
        result = self.player.seek_absolute(-10)
        
        self.assertEqual(self.player.current_media.current_position_seconds, 0)
        self.assertEqual(self.player.playback_state, PlaybackState.PLAYING)
    
    def test_persistence_to_playlist(self):
        """Test that changes to current_media are synced to playlist."""
        # Initial state
        self.assertEqual(self.player.current_media.current_position_seconds, 0)
        self.assertEqual(self.player.playlist[0].current_position_seconds, 0)
        self.assertIsNone(self.player.current_media.rating)
        self.assertIsNone(self.player.playlist[0].rating)
        
        # Make changes
        self.player.seek_relative(50)
        self.player.like_media()
        
        # Check that changes are synced to playlist
        self.assertEqual(self.player.current_media.current_position_seconds, 50)
        self.assertEqual(self.player.playlist[0].current_position_seconds, 50)
        self.assertEqual(self.player.current_media.rating, MediaRating.POSITIVE)
        self.assertEqual(self.player.playlist[0].rating, MediaRating.POSITIVE)
        
        # Navigate away and back to verify persistence
        self.player.next_media()
        self.player.previous_media()
        
        # Check that changes are preserved
        self.assertEqual(self.player.current_media.current_position_seconds, 50)
        self.assertEqual(self.player.current_media.rating, MediaRating.POSITIVE)
        self.assertEqual(self.player.playlist[0].current_position_seconds, 50)
        self.assertEqual(self.player.playlist[0].rating, MediaRating.POSITIVE)


class TestAndroidDB(unittest.TestCase):
    """Test AndroidDB model."""
    
    def setUp(self):
        """Set up test data."""
        self.media_item = MediaItem(
            id="track1",
            title="Test Song",
            media_type=MediaType.TRACK,
            app_name="Spotify"
        )
        self.player = MediaPlayer(
            app_name="Spotify",
            current_media=self.media_item,
            playback_state=PlaybackState.PLAYING
        )
        
    def test_android_db_creation(self):
        """Test creating an AndroidDB."""
        db = AndroidDB()
        
        self.assertEqual(db.media_players, {})
        
    def test_get_media_player_existing(self):
        """Test get_media_player method with existing player."""
        db = AndroidDB(media_players={"Spotify": self.player})
        
        player = db.get_media_player("Spotify")
        self.assertEqual(player, self.player)
        
    def test_get_media_player_nonexistent(self):
        """Test get_media_player method with nonexistent player."""
        db = AndroidDB()
        
        player = db.get_media_player("NonexistentApp")
        self.assertIsNone(player)
        
    def test_android_db_with_players(self):
        """Test AndroidDB with media players."""
        db = AndroidDB(media_players={"Spotify": self.player})
        
        self.assertEqual(len(db.media_players), 1)
        self.assertIn("Spotify", db.media_players)
        self.assertEqual(db.media_players["Spotify"], self.player)
        
    def test_android_db_model_dump(self):
        """Test AndroidDB model_dump method."""
        db = AndroidDB(media_players={"Spotify": self.player})
        
        data = db.model_dump()
        self.assertIn("media_players", data)
        self.assertEqual(len(data["media_players"]), 1)
        self.assertIn("Spotify", data["media_players"])


if __name__ == "__main__":
    unittest.main() 