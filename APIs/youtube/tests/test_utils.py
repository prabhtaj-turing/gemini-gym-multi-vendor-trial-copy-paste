"""
Test suite for utility functions in the YouTube API simulation.
Covers utilities from SimulationEngine/utils.py with comprehensive unit tests.
"""
import copy
import unittest
import string
import re

from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube.SimulationEngine import utils
from youtube.SimulationEngine.db import DB


class TestUtilityFunctions(BaseTestCaseWithErrorHandler):
    """Test suite for utility functions from SimulationEngine/utils.py"""

    @classmethod
    def setUpClass(cls):
        """Save original DB state."""
        cls.original_db_state = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Set up test environment for each test."""
        # Reset DB to a known test state
        DB.clear()
        DB.update({
            "channels": {},
            "videos": {},
            "playlists": {},
            "comments": {},
            "subscriptions": {},
            "activities": {}
        })

    def test_generate_random_string_default_length(self):
        """Test generate_random_string with default length."""
        result = utils.generate_random_string(10)
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 10)
        
        # Test that it contains only alphanumeric characters
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in result))

    def test_generate_random_string_various_lengths(self):
        """Test generate_random_string with various lengths."""
        test_lengths = [1, 5, 10, 20, 50, 100]
        
        for length in test_lengths:
            with self.subTest(length=length):
                result = utils.generate_random_string(length)
                self.assertEqual(len(result), length)
                self.assertIsInstance(result, str)

    def test_generate_random_string_zero_length(self):
        """Test generate_random_string with zero length."""
        result = utils.generate_random_string(0)
        self.assertEqual(result, "")
        self.assertEqual(len(result), 0)

    def test_generate_random_string_uniqueness(self):
        """Test that generate_random_string produces unique results."""
        # Generate multiple strings and check they're different
        results = set()
        for _ in range(100):
            result = utils.generate_random_string(10)
            results.add(result)
        
        # With 10 character random strings, we should get many unique values
        self.assertGreater(len(results), 90, 
                          "Random string generator not producing sufficiently unique results")

    def test_generate_random_string_character_distribution(self):
        """Test that generate_random_string uses expected character set."""
        # Generate a longer string to test character distribution
        result = utils.generate_random_string(1000)
        
        # Check that it contains both letters and digits
        has_letter = any(c.isalpha() for c in result)
        has_digit = any(c.isdigit() for c in result)
        
        self.assertTrue(has_letter, "Random string should contain letters")
        self.assertTrue(has_digit, "Random string should contain digits")
        
        # Check that it only contains alphanumeric characters
        self.assertTrue(all(c.isalnum() for c in result),
                       "Random string should only contain alphanumeric characters")

    def test_generate_entity_id_channel(self):
        """Test generate_entity_id for channel type."""
        result = utils.generate_entity_id("channel")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("UC"), 
                       f"Channel ID should start with 'UC', got: {result}")
        
        # Test total length (UC + 8 random characters = 10)
        self.assertEqual(len(result), 10)
        
        # Test that the random part contains only alphanumeric characters
        random_part = result[2:]
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in random_part))

    def test_generate_entity_id_video(self):
        """Test generate_entity_id for video type."""
        result = utils.generate_entity_id("video")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("VID"), 
                       f"Video ID should start with 'VID', got: {result}")
        self.assertEqual(len(result), 13, 
                        f"Video ID should be 13 characters (VID + 10), got length: {len(result)}")
        
        # Test that the random part contains only alphanumeric characters
        random_part = result[3:]
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in random_part),
                       f"Video ID random part contains invalid characters: {random_part}")

    def test_generate_entity_id_playlist(self):
        """Test generate_entity_id for playlist type."""
        result = utils.generate_entity_id("playlist")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("PL"), 
                       f"Playlist ID should start with 'PL', got: {result}")
        
        # Test total length (PL + 10 random characters = 12)
        self.assertEqual(len(result), 12)
        
        # Test that the random part contains only alphanumeric characters
        random_part = result[2:]
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in random_part))

    def test_generate_entity_id_comment(self):
        """Test generate_entity_id for comment type."""
        result = utils.generate_entity_id("comment")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("CMT"), 
                       f"Comment ID should start with 'CMT', got: {result}")
        # CMT + 7 random characters = 10
        self.assertEqual(len(result), 10, 
                        f"Comment ID should be 10 characters, got: {len(result)}")
        
        # Test that the random part contains only alphanumeric characters
        random_part = result[3:]
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in random_part))

    def test_generate_entity_id_subscription(self):
        """Test generate_entity_id for subscription type."""
        result = utils.generate_entity_id("subscription")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("SUBsub"), 
                       f"Subscription ID should start with 'SUBsub', got: {result}")
        # SUBsub + 3 random characters = 9
        self.assertEqual(len(result), 9, 
                        f"Subscription ID should be 9 characters, got: {len(result)}")

    def test_generate_entity_id_caption(self):
        """Test generate_entity_id for caption type."""
        result = utils.generate_entity_id("caption")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("CPT"), 
                       f"Caption ID should start with 'CPT', got: {result}")
        # CPT + 9 random characters = 12
        self.assertEqual(len(result), 12)

    def test_generate_entity_id_channel_section(self):
        """Test generate_entity_id for channelSection type."""
        result = utils.generate_entity_id("channelSection")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("CHsec"), 
                       f"ChannelSection ID should start with 'CHsec', got: {result}")
        # CHsec + 6 random characters = 11
        self.assertEqual(len(result), 11)

    def test_generate_entity_id_comment_thread(self):
        """Test generate_entity_id for commentthread type."""
        result = utils.generate_entity_id("commentthread")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("CMTTHTR"), 
                       f"CommentThread ID should start with 'CMTTHTR', got: {result}")
        # CMTTHTR + 5 random characters = 12
        self.assertEqual(len(result), 12)

    def test_generate_entity_id_member(self):
        """Test generate_entity_id for member type."""
        result = utils.generate_entity_id("member")
        
        # Test basic properties
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("MBR"), 
                       f"Member ID should start with 'MBR', got: {result}")
        # MBR + 6 random characters = 9
        self.assertEqual(len(result), 9)

    def test_generate_entity_id_unknown_type(self):
        """Test generate_entity_id with unknown entity type."""
        with self.assertRaises(ValueError) as cm:
            utils.generate_entity_id("unknown_type")
        
        self.assertIn("Unknown entity type", str(cm.exception))

    def test_generate_entity_id_case_sensitivity(self):
        """Test generate_entity_id with different case inputs."""
        # Test that the function requires exact case matching (based on implementation)
        test_cases = [
            ("Channel", ValueError),  # Should raise error as it's case-sensitive
            ("VIDEO", ValueError),    # Should raise error as it's case-sensitive
            ("PlayList", ValueError), # Should raise error as it's case-sensitive
            ("COMMENT", ValueError)   # Should raise error as it's case-sensitive
        ]
        
        for input_case, expected_exception in test_cases:
            with self.subTest(input_case=input_case):
                with self.assertRaises(expected_exception):
                    utils.generate_entity_id(input_case)

    def test_generate_entity_id_uniqueness(self):
        """Test that generate_entity_id produces unique results."""
        entity_types = ["channel", "video", "playlist", "comment", "subscription", "caption", "channelSection", "commentthread", "member"]
        
        for entity_type in entity_types:
            with self.subTest(entity_type=entity_type):
                # Generate multiple IDs of the same type
                ids = set()
                for _ in range(50):
                    result = utils.generate_entity_id(entity_type)
                    ids.add(result)
                
                # Should generate unique IDs
                self.assertEqual(len(ids), 50, 
                               f"Entity ID generator not producing unique {entity_type} IDs")

    def test_generate_entity_id_empty_string(self):
        """Test generate_entity_id with empty string."""
        with self.assertRaises(ValueError) as cm:
            utils.generate_entity_id("")
        
        self.assertIn("Unknown entity type", str(cm.exception))

    def test_generate_entity_id_none_input(self):
        """Test generate_entity_id with None input."""
        with self.assertRaises((ValueError, TypeError, AttributeError)):
            utils.generate_entity_id(None)

    def test_generate_entity_id_consistency_check(self):
        """Test that IDs follow expected format patterns."""
        # Test multiple generations to ensure consistency
        for _ in range(10):
            # Channel IDs should always start with UC and be 10 chars
            channel_id = utils.generate_entity_id("channel")
            self.assertTrue(channel_id.startswith("UC"))
            self.assertEqual(len(channel_id), 10)
            
            # Video IDs should always start with VID and be 13 chars
            video_id = utils.generate_entity_id("video")
            self.assertTrue(video_id.startswith("VID"))
            self.assertEqual(len(video_id), 13)
            
            # Playlist IDs should always start with PL and be 12 chars
            playlist_id = utils.generate_entity_id("playlist")
            self.assertTrue(playlist_id.startswith("PL"))
            self.assertEqual(len(playlist_id), 12)

    def test_generate_entity_id_valid_format(self):
        """Test that generated IDs match expected format patterns."""
        # Test channel ID format
        channel_id = utils.generate_entity_id("channel")
        channel_pattern = r'^UC[a-zA-Z0-9]{8}$'
        self.assertTrue(re.match(channel_pattern, channel_id),
                       f"Channel ID doesn't match expected pattern: {channel_id}")
        
        # Test video ID format  
        video_id = utils.generate_entity_id("video")
        video_pattern = r'^VID[a-zA-Z0-9]{10}$'
        self.assertTrue(re.match(video_pattern, video_id),
                       f"Video ID doesn't match expected pattern: {video_id}")
        
        # Test playlist ID format
        playlist_id = utils.generate_entity_id("playlist")
        playlist_pattern = r'^PL[a-zA-Z0-9]{10}$'
        self.assertTrue(re.match(playlist_pattern, playlist_id),
                       f"Playlist ID doesn't match expected pattern: {playlist_id}")
        
        # Test comment ID format
        comment_id = utils.generate_entity_id("comment")
        comment_pattern = r'^CMT[a-zA-Z0-9]{7}$'
        self.assertTrue(re.match(comment_pattern, comment_id),
                       f"Comment ID doesn't match expected pattern: {comment_id}")

    def test_utility_functions_integration(self):
        """Test utility functions working together."""
        # Test that the utility functions can work together to create realistic data
        
        # Generate various IDs
        channel_id = utils.generate_entity_id("channel")
        video_id = utils.generate_entity_id("video")
        playlist_id = utils.generate_entity_id("playlist")
        
        # Generate random strings for various purposes
        random_title = utils.generate_random_string(50)
        random_description = utils.generate_random_string(200)
        
        # Verify they all work as expected
        self.assertTrue(channel_id.startswith("UC"))
        self.assertEqual(len(channel_id), 10)
        self.assertTrue(video_id.startswith("VID"))
        self.assertEqual(len(video_id), 13)
        self.assertTrue(playlist_id.startswith("PL"))
        self.assertEqual(len(playlist_id), 12)
        self.assertEqual(len(random_title), 50)
        self.assertEqual(len(random_description), 200)
        
        # Test that they're all different
        all_generated = [channel_id, video_id, playlist_id, random_title, random_description]
        self.assertEqual(len(set(all_generated)), 5, 
                        "Generated values should all be unique")

    def test_performance_characteristics(self):
        """Test performance characteristics of utility functions."""
        import time
        
        # Test that functions complete reasonably quickly
        start_time = time.time()
        
        # Generate many IDs to test performance
        for _ in range(1000):
            utils.generate_random_string(10)
            utils.generate_entity_id("video")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete 1000 generations in reasonable time (less than 1 second)
        self.assertLess(execution_time, 1.0, 
                       f"Utility functions too slow: {execution_time:.3f} seconds for 1000 generations")

    def test_edge_cases_and_boundaries(self):
        """Test edge cases and boundary conditions."""
        # Test very large length for random string
        large_string = utils.generate_random_string(10000)
        self.assertEqual(len(large_string), 10000)
        
        # Test entity ID generation with unknown type names (should raise ValueError)
        with self.assertRaises(ValueError) as cm:
            utils.generate_entity_id("unknown_long_type_name")
        self.assertIn("Unknown entity type", str(cm.exception))
        
        # Test with special characters in entity type (should raise ValueError)
        with self.assertRaises(ValueError) as cm:
            utils.generate_entity_id("test_type-with-special.chars")
        self.assertIn("Unknown entity type", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
