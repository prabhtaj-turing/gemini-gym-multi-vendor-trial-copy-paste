"""
Instagram Module Performance Test Suite

This test suite validates the performance characteristics of the Instagram API module,
including memory usage and execution time for key operations.
"""

import unittest
import time
import psutil
import os

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestInstagramPerformanceBase(BaseTestCaseWithErrorHandler):
    """Base class for Instagram performance tests with common utilities."""

    # Performance thresholds (documented and reasonable)
    MAX_MEMORY_INCREASE_MB = 50  # Maximum memory increase per operation in MB
    MAX_EXECUTION_TIME_SECONDS = 2.0  # Maximum execution time for single operations
    MAX_BULK_EXECUTION_TIME_SECONDS = 10.0  # Maximum execution time for bulk operations
    BULK_OPERATION_SIZE = 100  # Number of items for bulk operation tests

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Import required modules
        import instagram.User as User
        import instagram.Media as Media
        import instagram.Comment as Comment
        import instagram.SimulationEngine.db as db

        self.User = User
        self.Media = Media
        self.Comment = Comment
        self.db = db

        # Reset DB to clean state for consistent performance testing
        self.db.DB.clear()
        self.db.DB.update({"users": {}, "media": {}, "comments": {}})

        # Get current process for memory monitoring
        self.process = psutil.Process(os.getpid())

        # Force garbage collection before each test for more consistent results
        import gc

        gc.collect()

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function call."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage change during function execution."""
        import gc

        gc.collect()  # Clean up before measurement

        initial_memory = self.get_memory_usage_mb()
        result = func(*args, **kwargs)

        gc.collect()  # Clean up after execution
        final_memory = self.get_memory_usage_mb()

        memory_increase = final_memory - initial_memory
        return result, memory_increase


class TestInstagramUserPerformance(TestInstagramPerformanceBase):
    """Performance tests for Instagram User operations."""

    def test_user_creation_execution_time(self):
        """Test that user creation completes within reasonable time."""
        result, execution_time = self.measure_execution_time(
            self.User.create_user, "perf_user_1", "Performance User", "perfuser"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "perf_user_1")
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"User creation took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )

    def test_user_creation_memory_usage(self):
        """Test that user creation does not use excessive memory."""
        result, memory_increase = self.measure_memory_usage(
            self.User.create_user, "perf_user_2", "Performance User 2", "perfuser2"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "perf_user_2")
        self.assertLess(
            memory_increase,
            self.MAX_MEMORY_INCREASE_MB,
            f"User creation increased memory by {memory_increase:.2f}MB, "
            f"expected < {self.MAX_MEMORY_INCREASE_MB}MB",
        )

    def test_user_retrieval_performance(self):
        """Test that user retrieval is fast and memory-efficient."""
        # Setup: create a user first
        self.User.create_user("perf_user_3", "Performance User 3", "perfuser3")

        # Test retrieval time
        result, execution_time = self.measure_execution_time(
            self.User.get_user, "perf_user_3"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "perf_user_3")
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"User retrieval took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )

    def test_bulk_user_creation_performance(self):
        """Test performance of creating multiple users in sequence."""
        start_time = time.perf_counter()
        initial_memory = self.get_memory_usage_mb()

        created_users = []
        for i in range(self.BULK_OPERATION_SIZE):
            user_id = f"bulk_user_{i}"
            result = self.User.create_user(user_id, f"Bulk User {i}", f"bulkuser{i}")
            created_users.append(result)

        end_time = time.perf_counter()
        final_memory = self.get_memory_usage_mb()

        total_time = end_time - start_time
        memory_increase = final_memory - initial_memory

        # Assertions
        self.assertEqual(len(created_users), self.BULK_OPERATION_SIZE)
        self.assertLess(
            total_time,
            self.MAX_BULK_EXECUTION_TIME_SECONDS,
            f"Bulk user creation took {total_time:.4f}s, "
            f"expected < {self.MAX_BULK_EXECUTION_TIME_SECONDS}s",
        )

        # Memory usage should be reasonable for bulk operations
        max_bulk_memory = self.MAX_MEMORY_INCREASE_MB * 2  # Allow 2x for bulk ops
        self.assertLess(
            memory_increase,
            max_bulk_memory,
            f"Bulk user creation increased memory by {memory_increase:.2f}MB, "
            f"expected < {max_bulk_memory}MB",
        )

    def test_user_listing_performance(self):
        """Test performance of listing all users."""
        # Setup: create multiple users
        for i in range(50):  # Smaller dataset for listing test
            self.User.create_user(f"list_user_{i}", f"List User {i}", f"listuser{i}")

        # Test listing performance
        result, execution_time = self.measure_execution_time(self.User.list_users)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 50)
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"User listing took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )

    def test_user_deletion_performance(self):
        """Test performance of user deletion."""
        # Setup: create a user
        self.User.create_user("delete_user", "Delete User", "deleteuser")

        # Test deletion performance
        result, execution_time = self.measure_execution_time(
            self.User.delete_user, "delete_user"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("success"), True)
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"User deletion took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )


class TestInstagramMediaPerformance(TestInstagramPerformanceBase):
    """Performance tests for Instagram Media operations."""

    def setUp(self):
        """Set up test fixtures with a user for media operations."""
        super().setUp()
        # Create a user for media tests
        self.User.create_user("media_user", "Media User", "mediauser")

    def test_media_creation_execution_time(self):
        """Test that media creation completes within reasonable time."""
        result, execution_time = self.measure_execution_time(
            self.Media.create_media,
            "media_user",
            "http://example.com/performance_test.jpg",
            "Performance test media",
        )

        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertEqual(result["user_id"], "media_user")
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"Media creation took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )

    def test_media_creation_memory_usage(self):
        """Test that media creation does not use excessive memory."""
        result, memory_increase = self.measure_memory_usage(
            self.Media.create_media,
            "media_user",
            "http://example.com/memory_test.jpg",
            "Memory test media",
        )

        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertLess(
            memory_increase,
            self.MAX_MEMORY_INCREASE_MB,
            f"Media creation increased memory by {memory_increase:.2f}MB, "
            f"expected < {self.MAX_MEMORY_INCREASE_MB}MB",
        )

    def test_bulk_media_creation_performance(self):
        """Test performance of creating multiple media posts."""
        start_time = time.perf_counter()
        initial_memory = self.get_memory_usage_mb()

        created_media = []
        for i in range(self.BULK_OPERATION_SIZE):
            result = self.Media.create_media(
                "media_user",
                f"http://example.com/bulk_media_{i}.jpg",
                f"Bulk media post {i}",
            )
            created_media.append(result)

        end_time = time.perf_counter()
        final_memory = self.get_memory_usage_mb()

        total_time = end_time - start_time
        memory_increase = final_memory - initial_memory

        # Assertions
        self.assertEqual(len(created_media), self.BULK_OPERATION_SIZE)
        self.assertLess(
            total_time,
            self.MAX_BULK_EXECUTION_TIME_SECONDS,
            f"Bulk media creation took {total_time:.4f}s, "
            f"expected < {self.MAX_BULK_EXECUTION_TIME_SECONDS}s",
        )

        max_bulk_memory = self.MAX_MEMORY_INCREASE_MB * 2
        self.assertLess(
            memory_increase,
            max_bulk_memory,
            f"Bulk media creation increased memory by {memory_increase:.2f}MB, "
            f"expected < {max_bulk_memory}MB",
        )

    def test_media_listing_performance(self):
        """Test performance of listing all media posts."""
        # Setup: create multiple media posts
        for i in range(30):
            self.Media.create_media(
                "media_user",
                f"http://example.com/list_media_{i}.jpg",
                f"List media {i}",
            )

        # Test listing performance
        result, execution_time = self.measure_execution_time(self.Media.list_media)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 30)
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"Media listing took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )

    def test_media_deletion_performance(self):
        """Test performance of media deletion."""
        # Setup: create media
        media_result = self.Media.create_media(
            "media_user", "http://example.com/delete_media.jpg", "Delete test media"
        )
        media_id = media_result["id"]

        # Test deletion performance
        result, execution_time = self.measure_execution_time(
            self.Media.delete_media, media_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("success"), True)
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"Media deletion took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )


class TestInstagramCommentPerformance(TestInstagramPerformanceBase):
    """Performance tests for Instagram Comment operations."""

    def setUp(self):
        """Set up test fixtures with user and media for comment operations."""
        super().setUp()
        # Create user and media for comment tests
        self.User.create_user("comment_user", "Comment User", "commentuser")
        media_result = self.Media.create_media(
            "comment_user",
            "http://example.com/comment_media.jpg",
            "Media for comment tests",
        )
        self.media_id = media_result["id"]

    def test_comment_creation_execution_time(self):
        """Test that comment creation completes within reasonable time."""
        result, execution_time = self.measure_execution_time(
            self.Comment.add_comment,
            self.media_id,
            "comment_user",
            "Performance test comment",
        )

        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertEqual(result["media_id"], self.media_id)
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"Comment creation took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )

    def test_comment_creation_memory_usage(self):
        """Test that comment creation does not use excessive memory."""
        result, memory_increase = self.measure_memory_usage(
            self.Comment.add_comment,
            self.media_id,
            "comment_user",
            "Memory test comment",
        )

        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertLess(
            memory_increase,
            self.MAX_MEMORY_INCREASE_MB,
            f"Comment creation increased memory by {memory_increase:.2f}MB, "
            f"expected < {self.MAX_MEMORY_INCREASE_MB}MB",
        )

    def test_bulk_comment_creation_performance(self):
        """Test performance of creating multiple comments."""
        start_time = time.perf_counter()
        initial_memory = self.get_memory_usage_mb()

        created_comments = []
        for i in range(self.BULK_OPERATION_SIZE):
            result = self.Comment.add_comment(
                self.media_id, "comment_user", f"Bulk comment {i} - performance test"
            )
            created_comments.append(result)

        end_time = time.perf_counter()
        final_memory = self.get_memory_usage_mb()

        total_time = end_time - start_time
        memory_increase = final_memory - initial_memory

        # Assertions
        self.assertEqual(len(created_comments), self.BULK_OPERATION_SIZE)
        self.assertLess(
            total_time,
            self.MAX_BULK_EXECUTION_TIME_SECONDS,
            f"Bulk comment creation took {total_time:.4f}s, "
            f"expected < {self.MAX_BULK_EXECUTION_TIME_SECONDS}s",
        )

        max_bulk_memory = self.MAX_MEMORY_INCREASE_MB * 2
        self.assertLess(
            memory_increase,
            max_bulk_memory,
            f"Bulk comment creation increased memory by {memory_increase:.2f}MB, "
            f"expected < {max_bulk_memory}MB",
        )

    def test_comment_listing_performance(self):
        """Test performance of listing comments for a media post."""
        # Setup: create multiple comments
        for i in range(25):
            self.Comment.add_comment(
                self.media_id,
                "comment_user",
                f"List comment {i} for performance testing",
            )

        # Test listing performance
        result, execution_time = self.measure_execution_time(
            self.Comment.list_comments, self.media_id
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 25)
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"Comment listing took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )


class TestInstagramDatabasePerformance(TestInstagramPerformanceBase):
    """Performance tests for Instagram database operations."""

    def test_database_state_operations_performance(self):
        """Test performance of database state operations."""
        # Create some test data
        self.User.create_user("db_user", "DB User", "dbuser")
        media_result = self.Media.create_media(
            "db_user", "http://example.com/db_media.jpg", "DB media"
        )
        self.Comment.add_comment(media_result["id"], "db_user", "DB comment")

        # Test get_minified_state performance
        result, execution_time = self.measure_execution_time(self.db.get_minified_state)

        self.assertIsInstance(result, dict)
        self.assertIn("users", result)
        self.assertIn("media", result)
        self.assertIn("comments", result)
        self.assertLess(
            execution_time,
            self.MAX_EXECUTION_TIME_SECONDS,
            f"get_minified_state took {execution_time:.4f}s, expected < {self.MAX_EXECUTION_TIME_SECONDS}s",
        )

    def test_database_operations_memory_usage(self):
        """Test memory usage of database operations."""
        # Test memory usage for state retrieval
        result, memory_increase = self.measure_memory_usage(self.db.get_minified_state)

        self.assertIsInstance(result, dict)
        self.assertLess(
            memory_increase,
            self.MAX_MEMORY_INCREASE_MB,
            f"get_minified_state increased memory by {memory_increase:.2f}MB, "
            f"expected < {self.MAX_MEMORY_INCREASE_MB}MB",
        )


class TestInstagramComplexWorkflowPerformance(TestInstagramPerformanceBase):
    """Performance tests for complex Instagram workflows."""

    def test_complete_workflow_performance(self):
        """Test performance of a complete Instagram workflow."""
        start_time = time.perf_counter()
        initial_memory = self.get_memory_usage_mb()

        # Complete workflow: user -> media -> comments
        user_result = self.User.create_user(
            "workflow_user", "Workflow User", "workflowuser"
        )
        media_result = self.Media.create_media(
            "workflow_user",
            "http://example.com/workflow_media.jpg",
            "Workflow test media",
        )
        comment_result = self.Comment.add_comment(
            media_result["id"], "workflow_user", "Workflow test comment"
        )

        # Retrieve all data
        users = self.User.list_users()
        media = self.Media.list_media()
        comments = self.Comment.list_comments(media_result["id"])

        end_time = time.perf_counter()
        final_memory = self.get_memory_usage_mb()

        total_time = end_time - start_time
        memory_increase = final_memory - initial_memory

        # Assertions
        self.assertEqual(len(users), 1)
        self.assertEqual(len(media), 1)
        self.assertEqual(len(comments), 1)

        # Workflow should complete within reasonable time
        workflow_time_limit = (
            self.MAX_EXECUTION_TIME_SECONDS * 3
        )  # Allow 3x for complex workflow
        self.assertLess(
            total_time,
            workflow_time_limit,
            f"Complete workflow took {total_time:.4f}s, expected < {workflow_time_limit}s",
        )

        # Memory usage should be reasonable
        workflow_memory_limit = (
            self.MAX_MEMORY_INCREASE_MB * 1.5
        )  # Allow 1.5x for workflow
        self.assertLess(
            memory_increase,
            workflow_memory_limit,
            f"Complete workflow increased memory by {memory_increase:.2f}MB, "
            f"expected < {workflow_memory_limit}MB",
        )

    def test_concurrent_operations_simulation_performance(self):
        """Test performance when simulating concurrent-like operations."""
        start_time = time.perf_counter()
        initial_memory = self.get_memory_usage_mb()

        # Simulate multiple users creating content rapidly
        num_users = 10
        posts_per_user = 5
        comments_per_post = 3

        for user_i in range(num_users):
            user_id = f"concurrent_user_{user_i}"
            self.User.create_user(
                user_id, f"Concurrent User {user_i}", f"concurrentuser{user_i}"
            )

            for post_i in range(posts_per_user):
                media_result = self.Media.create_media(
                    user_id,
                    f"http://example.com/concurrent_media_{user_i}_{post_i}.jpg",
                    f"Concurrent post {post_i} by user {user_i}",
                )

                for comment_i in range(comments_per_post):
                    self.Comment.add_comment(
                        media_result["id"],
                        user_id,
                        f"Concurrent comment {comment_i} on post {post_i}",
                    )

        end_time = time.perf_counter()
        final_memory = self.get_memory_usage_mb()

        total_time = end_time - start_time
        memory_increase = final_memory - initial_memory

        # Verify all data was created
        users = self.User.list_users()
        media = self.Media.list_media()

        expected_users = num_users
        expected_media = num_users * posts_per_user

        self.assertEqual(len(users), expected_users)
        self.assertEqual(len(media), expected_media)

        # Performance assertions
        concurrent_time_limit = (
            self.MAX_BULK_EXECUTION_TIME_SECONDS * 2
        )  # Allow 2x for complex operations
        self.assertLess(
            total_time,
            concurrent_time_limit,
            f"Concurrent operations took {total_time:.4f}s, expected < {concurrent_time_limit}s",
        )

        concurrent_memory_limit = (
            self.MAX_MEMORY_INCREASE_MB * 5
        )  # Allow 5x for large dataset
        self.assertLess(
            memory_increase,
            concurrent_memory_limit,
            f"Concurrent operations increased memory by {memory_increase:.2f}MB, "
            f"expected < {concurrent_memory_limit}MB",
        )


if __name__ == "__main__":
    # Configure test runner for performance testing
    unittest.main(verbosity=2, buffer=True)
