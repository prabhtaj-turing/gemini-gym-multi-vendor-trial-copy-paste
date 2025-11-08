"""
Test suite for imports in the YouTube API simulation.
This is a comprehensive test for checking imports for all YouTube modules.
Along with this, we can check function imports and package structure.
"""
import importlib
import inspect
import sys
import unittest
from pathlib import Path

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestYouTubeImports(BaseTestCaseWithErrorHandler):
    """Test importing YouTube modules directly without complex dependencies."""

    @classmethod
    def setUpClass(cls):
        """Add the APIs directory to path for module discovery."""
        apis_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(apis_dir))
        print(f"📂 Added to sys.path: {apis_dir}")

    @classmethod
    def tearDownClass(cls):
        """Remove the APIs directory from path."""
        apis_dir = Path(__file__).parent.parent.parent
        if str(apis_dir) in sys.path:
            sys.path.remove(str(apis_dir))

    def test_direct_module_imports(self):
        """Test importing modules directly without complex dependencies."""
        print("🔍 Testing direct module imports...")

        modules_to_test = [
            ("youtube", "Main YouTube package"),
            ("youtube.Activities", "YouTube Activities module"),
            ("youtube.Caption", "YouTube Caption module"),
            ("youtube.ChannelBanners", "YouTube ChannelBanners module"),
            ("youtube.Channels", "YouTube Channels module"),
            ("youtube.ChannelSection", "YouTube ChannelSection module"),
            ("youtube.ChannelStatistics", "YouTube ChannelStatistics module"),
            ("youtube.Comment", "YouTube Comment module"),
            ("youtube.CommentThread", "YouTube CommentThread module"),
            ("youtube.Memberships", "YouTube Memberships module"),
            ("youtube.Playlists", "YouTube Playlists module"),
            ("youtube.Search", "YouTube Search module"),
            ("youtube.Subscriptions", "YouTube Subscriptions module"),
            ("youtube.VideoCategory", "YouTube VideoCategory module"),
            ("youtube.Videos", "YouTube Videos module"),
        ]

        import_results = {}

        for module_name, description in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "status": "success",
                    "module": module,
                    "attributes": dir(module)
                }
                self.assertIsNotNone(module, f"Module {module_name} imported but is None")
                print(f"✅ {description}: {module_name} - Success")
            except ImportError as e:
                import_results[module_name] = {
                    "status": "import_error",
                    "error": str(e)
                }
                self.fail(f"❌ {description}: Failed to import {module_name}: {e}")
            except Exception as e:
                import_results[module_name] = {
                    "status": "error",
                    "error": str(e)
                }
                self.fail(f"⚠️ {description}: {module_name} - Error: {e}")

        successful_imports = [name for name, result in import_results.items() 
                             if result["status"] == "success"]

        self.assertTrue(len(successful_imports) == len(modules_to_test),
                       f"Not all modules imported successfully. Results: {import_results}")

    def test_simulation_engine_imports(self):
        """Test importing SimulationEngine components."""
        print("🔧 Testing SimulationEngine imports...")

        simulation_modules = [
            ("youtube.SimulationEngine", "SimulationEngine package"),
            ("youtube.SimulationEngine.db", "Database module"),
            ("youtube.SimulationEngine.models", "Models module"),
            ("youtube.SimulationEngine.utils", "Utils module"),
            ("youtube.SimulationEngine.custom_errors", "Custom errors module"),
            ("youtube.SimulationEngine.error_handling", "Error handling module"),
        ]

        for module_name, description in simulation_modules:
            with self.subTest(module=module_name):
                try:
                    module = importlib.import_module(module_name)
                    self.assertIsNotNone(module, f"Module {module_name} imported but is None")
                    print(f"✅ {description}: {module_name}")
                except ImportError as e:
                    self.fail(f"❌ {description}: Failed to import {module_name}: {e}")

    def test_function_imports_from_modules(self):
        """Test importing specific functions from modules."""
        print("🔍 Testing function imports...")

        function_imports = [
            # Activities
            ("youtube.Activities", "list"),
            # Caption
            ("youtube.Caption", "delete"),
            ("youtube.Caption", "download"),
            ("youtube.Caption", "insert"),
            ("youtube.Caption", "list"),
            ("youtube.Caption", "update"),
            # ChannelBanners
            ("youtube.ChannelBanners", "insert"),
            # Channels
            ("youtube.Channels", "list"),
            ("youtube.Channels", "insert"),
            ("youtube.Channels", "update"),
            # ChannelSection
            ("youtube.ChannelSection", "list"),
            ("youtube.ChannelSection", "delete"),
            ("youtube.ChannelSection", "insert"),
            ("youtube.ChannelSection", "update"),
            # ChannelStatistics
            ("youtube.ChannelStatistics", "comment_count"),
            ("youtube.ChannelStatistics", "hidden_subscriber_count"),
            ("youtube.ChannelStatistics", "subscriber_count"),
            ("youtube.ChannelStatistics", "video_count"),
            ("youtube.ChannelStatistics", "view_count"),
            # Comment
            ("youtube.Comment", "set_moderation_status"),
            ("youtube.Comment", "delete"),
            ("youtube.Comment", "insert"),
            ("youtube.Comment", "list"),
            ("youtube.Comment", "mark_as_spam"),
            ("youtube.Comment", "update"),
            # CommentThread
            ("youtube.CommentThread", "insert"),
            ("youtube.CommentThread", "list"),
            ("youtube.CommentThread", "delete"),
            ("youtube.CommentThread", "update"),
            # Memberships
            ("youtube.Memberships", "list"),
            ("youtube.Memberships", "insert"),
            ("youtube.Memberships", "delete"),
            ("youtube.Memberships", "update"),
            # Playlists
            ("youtube.Playlists", "create"),
            ("youtube.Playlists", "list_playlists"),
            ("youtube.Playlists", "get"),
            ("youtube.Playlists", "update"),
            ("youtube.Playlists", "delete"),
            ("youtube.Playlists", "add_video"),
            ("youtube.Playlists", "delete_video"),
            ("youtube.Playlists", "reorder"),
            # Search
            ("youtube.Search", "list"),
            # Subscriptions
            ("youtube.Subscriptions", "insert"),
            ("youtube.Subscriptions", "delete"),
            ("youtube.Subscriptions", "list"),
            # VideoCategory
            ("youtube.VideoCategory", "list"),
            # Videos
            ("youtube.Videos", "list"),
            ("youtube.Videos", "rate"),
            ("youtube.Videos", "report_abuse"),
            ("youtube.Videos", "delete"),
            ("youtube.Videos", "update"),
            ("youtube.Videos", "upload"),
        ]

        failed_imports = []

        for module_name, function_name in function_imports:
            with self.subTest(module=module_name, function=function_name):
                try:
                    module = importlib.import_module(module_name)
                    func = getattr(module, function_name)
                    self.assertTrue(callable(func), 
                                  f"Function {function_name} in {module_name} is not callable")
                    print(f"✅ {module_name}.{function_name}")
                except ImportError as e:
                    failed_imports.append(f"Import error: {module_name}.{function_name}: {e}")
                except AttributeError as e:
                    failed_imports.append(f"Function not found: {module_name}.{function_name}: {e}")

        if failed_imports:
            self.fail(f"Failed function imports: {failed_imports}")

    def test_utility_function_imports(self):
        """Test importing utility functions from SimulationEngine."""
        print("🛠️ Testing utility function imports...")

        utility_imports = [
            ("youtube.SimulationEngine.utils", "generate_random_string"),
            ("youtube.SimulationEngine.utils", "generate_entity_id"),
            ("youtube.SimulationEngine.db", "save_state"),
            ("youtube.SimulationEngine.db", "load_state"),

        ]

        for module_name, function_name in utility_imports:
            with self.subTest(module=module_name, function=function_name):
                try:
                    module = importlib.import_module(module_name)
                    func = getattr(module, function_name)
                    self.assertTrue(callable(func), 
                                  f"Utility function {function_name} in {module_name} is not callable")
                    print(f"✅ {module_name}.{function_name}")
                except (ImportError, AttributeError) as e:
                    self.fail(f"Failed to import utility function {module_name}.{function_name}: {e}")

    def test_main_package_interface(self):
        """Test main package interface through __getattr__ functionality."""
        print("📦 Testing main package interface...")

        # Test importing the main package
        try:
            import youtube
            self.assertIsNotNone(youtube)
        except ImportError as e:
            self.fail(f"Failed to import main youtube package: {e}")

        # Test accessing functions through the main package interface
        # These are defined in the _function_map in __init__.py
        main_package_functions = [
            "list_activities",
            "list_video_categories", 
            "create_comment_thread",
            "list_comment_threads",
            "delete_comment_thread",
            "update_comment_thread",
            "list_searches",
            "list_channel_sections",
            "delete_channel_section",
            "insert_channel_section",
            "update_channel_section",
            "list_channels",
            "create_channel",
            "update_channel_metadata",
            "list_memberships",
            "create_membership",
            "delete_membership",
            "update_membership",
            "set_comment_moderation_status",
            "delete_comment",
            "add_comment",
            "list_comments",
            "mark_comment_as_spam",
            "update_comment",
            "delete_caption",
            "download_caption",
            "insert_caption",
            "list_captions",
            "update_caption",
            "list_videos",
            "rate_video",
            "report_video_abuse",
            "delete_video",
            "update_video_metadata",
            "upload_video",
            "manage_channel_comment_count",
            "manage_channel_subscriber_visibility",
            "manage_channel_subscriber_count",
            "manage_channel_video_count",
            "manage_channel_view_count",
            "insert_channel_banner",
            "create_subscription",
            "delete_subscription",
            "list_subscriptions",
            "list_playlists",
            "get_playlist",
            "create_playlist",
            "update_playlist",
            "delete_playlist",
            "add_video_to_playlist",
            "delete_video_from_playlist",
            "reorder_playlist_videos"
        ]

        failed_functions = []

        for func_name in main_package_functions:
            with self.subTest(function=func_name):
                try:
                    func = getattr(youtube, func_name)
                    self.assertTrue(callable(func), 
                                  f"Main package function {func_name} is not callable")
                    print(f"✅ youtube.{func_name}")
                except AttributeError as e:
                    failed_functions.append(f"{func_name}: {e}")

        if failed_functions:
            self.fail(f"Failed main package function access: {failed_functions}")

    def test_model_imports(self):
        """Test importing model classes from SimulationEngine.models."""
        print("📋 Testing model imports...")

        model_classes = [
            "SnippetInputModel",
            "ThumbnailObjectModel", 
            "ThumbnailInputModel",
            "TopLevelCommentInputModel",
            "ThumbnailRecordUploadModel",
            "ThumbnailsUploadModel",
            "SnippetUploadModel",
            "StatusUploadModel",
            "VideoUploadModel"
        ]

        try:
            from youtube.SimulationEngine import models
            
            for model_name in model_classes:
                with self.subTest(model=model_name):
                    try:
                        model_class = getattr(models, model_name)
                        self.assertTrue(inspect.isclass(model_class), 
                                      f"{model_name} is not a class")
                        print(f"✅ models.{model_name}")
                    except AttributeError as e:
                        self.fail(f"Model class {model_name} not found: {e}")
                        
        except ImportError as e:
            self.fail(f"Failed to import models module: {e}")

    def test_custom_error_imports(self):
        """Test importing custom error classes."""
        print("⚠️ Testing custom error imports...")

        error_classes = [
            "MissingPartParameterError",
            "InvalidMaxResultsError",
            "InvalidPartParameterError", 
            "MaxResultsOutOfRangeError"
        ]

        try:
            from youtube.SimulationEngine import custom_errors
            
            for error_name in error_classes:
                with self.subTest(error=error_name):
                    try:
                        error_class = getattr(custom_errors, error_name)
                        self.assertTrue(inspect.isclass(error_class), 
                                      f"{error_name} is not a class")
                        self.assertTrue(issubclass(error_class, Exception), 
                                      f"{error_name} is not an exception class")
                        print(f"✅ custom_errors.{error_name}")
                    except AttributeError as e:
                        self.fail(f"Error class {error_name} not found: {e}")
                        
        except ImportError as e:
            self.fail(f"Failed to import custom_errors module: {e}")

    def test_package_structure_integrity(self):
        """Test the overall package structure and module relationships."""
        print("🏗️ Testing package structure integrity...")

        # Test that main package has expected attributes
        import youtube
        
        expected_main_attributes = [
            'Activities', 'Caption', 'Channels', 'ChannelSection', 'ChannelStatistics',
            'ChannelBanners', 'Comment', 'CommentThread', 'Subscriptions', 'VideoCategory',
            'Memberships', 'Videos', 'Search', 'Playlists', 'SimulationEngine', 'DB'
        ]
        
        for attr in expected_main_attributes:
            with self.subTest(attribute=attr):
                self.assertTrue(hasattr(youtube, attr), 
                              f"Main package missing expected attribute: {attr}")

        # Test that SimulationEngine has expected submodules that are explicitly imported
        expected_simulation_attributes = [
            'db', 'models', 'utils', 'custom_errors'
        ]
        
        for attr in expected_simulation_attributes:
            with self.subTest(simulation_attr=attr):
                self.assertTrue(hasattr(youtube.SimulationEngine, attr),
                              f"SimulationEngine missing expected attribute: {attr}")

    def test_function_signatures(self):
        """Test that imported functions have expected signatures."""
        print("✍️ Testing function signatures...")

        # Test a sampling of key functions to ensure they have proper signatures
        signature_tests = [
            ("youtube.Videos", "upload", ["body"]),  # Should have body parameter
            ("youtube.Playlists", "create", ["ownerId", "title", "description", "privacyStatus", "list_of_videos", "thumbnails"]),  # Should have body parameter  
            ("youtube.Comment", "insert", ["part"]),  # Should have part parameter
            ("youtube.SimulationEngine.utils", "generate_entity_id", ["entity_type"]),  # Should have entity_type parameter
        ]

        for module_name, function_name, expected_params in signature_tests:
            with self.subTest(module=module_name, function=function_name):
                try:
                    module = importlib.import_module(module_name)
                    func = getattr(module, function_name)
                    sig = inspect.signature(func)
                    
                    param_names = list(sig.parameters.keys())
                    
                    for expected_param in expected_params:
                        self.assertIn(expected_param, param_names,
                                    f"Function {module_name}.{function_name} missing expected parameter: {expected_param}")
                    
                    print(f"✅ {module_name}.{function_name} signature: {sig}")
                    
                except (ImportError, AttributeError) as e:
                    self.fail(f"Failed to inspect {module_name}.{function_name}: {e}")


if __name__ == '__main__':
    unittest.main()
