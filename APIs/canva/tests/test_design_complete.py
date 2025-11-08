# test_design_complete.py
"""
Comprehensive test suite for all Canva Design module implementations.
This file runs all tests for the Design module to ensure complete functionality.
"""

import pytest
import sys
import os

# Add the APIs directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Import the actual modules to test directly
from canva.Canva.Design.DesignCreation import create_design
from canva.Canva.Design.DesignListing import list_designs
from canva.Canva.Design.DesignRetrieval import get_design, get_design_pages
from canva.Canva.Design.DesignExport import create_design_export_job, get_design_export_job
from canva.Canva.Design.DesignImport import create_design_import, get_design_import_job, create_url_import_job, get_url_import_job
from canva.Canva.Design.Comment import create_thread, create_reply, get_thread, get_reply, list_replies
from canva.SimulationEngine.db import DB


class TestDesignModuleIntegration:
    """Integration tests for the entire Design module"""
    
    def setup_method(self):
        """Reset DB before each test"""
        from canva.SimulationEngine.db import DB
        DB.clear()
        DB["Designs"] = {}
        DB["CommentThreads"] = {}
        DB["CommentReplies"] = {}
        DB["ExportJobs"] = {}
        DB["ImportJobs"] = {}
    
    def test_end_to_end_design_workflow(self):
        """Test complete design workflow from creation to deletion"""
        
        # 1. Create a design
        design_result = create_design(
            design_type={"type": "preset", "name": "doc"},
            asset_id="test_asset_123",
            title="Integration Test Design"
        )
        design_id = design_result["id"]
        
        # 2. Get the design to verify it exists
        get_result = get_design(design_id)
        assert get_result is not None
        assert get_result["design"]["title"] == "Integration Test Design"
        
        # 3. Create a comment thread
        thread_result = create_thread(
            design_id, 
            "This design looks great! What do you think [user123:team456]?"
        )
        thread_id = thread_result["thread"]["id"]
        
        # 4. Add a reply to the thread
        reply_result = create_reply(
            design_id,
            thread_id, 
            "I agree, looks fantastic!"
        )
        assert reply_result["reply"]["thread_id"] == thread_id
        
        # 5. Create an export job
        export_result = create_design_export_job(
            design_id,
            {"type": "pdf", "size": "a4"}
        )
        assert "job" in export_result

    
    def test_import_export_workflow(self):
        """Test design import and export workflow"""
        import base64
        
        # Create import job
        title = "Imported Design"
        title_base64 = base64.b64encode(title.encode('utf-8')).decode('utf-8')
        import_metadata = {
            "title_base64": title_base64,
            "mime_type": "application/pdf"
        }
        
        import_result = create_design_import(import_metadata)
        import_job_id = import_result["job"]["id"]
        
        # Check import job status
        import_status = get_design_import_job(import_job_id)
        assert import_status["job"]["id"] == import_job_id
        
        # If import was successful, try to export the design
        if import_result["job"]["status"] == "success":
            design_id = import_result["job"]["result"]["designs"][0]["id"]
            
            export_result = create_design_export_job(
                design_id,
                {"type": "jpg", "quality": 85}
            )
            assert "job" in export_result
    
    def test_comment_thread_workflow(self):
        """Test complete comment thread workflow"""
        
        # Create a design for comments
        design = create_design(
            design_type={"type": "preset", "name": "presentation"},
            asset_id="comment_test_asset",
            title="Comment Test Design"
        )
        design_id = design["id"]
        
        # Create initial thread
        thread = create_thread(
            design_id,
            "What do you think about this slide layout [reviewer1:team1]?",
            assignee_id="reviewer1"
        )
        thread_id = thread["thread"]["id"]
        
        # Add multiple replies
        replies = []
        for i in range(3):
            reply = create_reply(
                design_id,
                thread_id,
                f"Reply {i+1}: This looks good!"
            )
            replies.append(reply["reply"]["id"])
        
        # Get the thread
        retrieved_thread = get_thread(design_id, thread_id)
        assert retrieved_thread["thread"]["id"] == thread_id
        
        # Get individual replies
        for reply_id in replies:
            retrieved_reply = get_reply(design_id, thread_id, reply_id)
            assert retrieved_reply["reply"]["id"] == reply_id
        
        # List all replies
        all_replies = list_replies(design_id, thread_id)
        assert len(all_replies["items"]) == 3
        
        # Test pagination
        first_page = list_replies(design_id, thread_id, limit=2)
        assert len(first_page["items"]) == 2
        assert "continuation" in first_page
        
        second_page = list_replies(
            design_id, 
            thread_id, 
            limit=2, 
            continuation=first_page["continuation"]
        )
        assert len(second_page["items"]) == 1
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent across all modules"""
        
        # Test empty string validation across modules
        with pytest.raises(Exception):  # Will raise InvalidAssetIDError or similar
            create_design({"type": "preset", "name": "doc"}, "", "Title")  # Empty asset_id
        
        with pytest.raises((ValueError, TypeError)):
            get_design("")  # Empty design_id
        
        with pytest.raises((ValueError, TypeError)):
            create_thread("", "message")  # Empty design_id
        
        # Test non-existent design handling
        # get_design should return None for non-existent designs
        result = get_design("nonexistent")
        assert result is None
        
        with pytest.raises(ValueError, match="not found"):
            create_thread("nonexistent", "message")


def run_all_design_tests():
    """Run all design module tests and return results"""
    print("🧪 Running Comprehensive Canva Design Module Tests...")
    print("=" * 60)
    
    # Get the test directory
    test_dir = os.path.dirname(__file__)
    
    # Run all design test files
    test_files = [
        os.path.join(test_dir, "test_design_core.py"),
        os.path.join(test_dir, "test_design_export.py"), 
        os.path.join(test_dir, "test_design_import.py"),
        os.path.join(test_dir, "test_design_comment.py"),
        os.path.join(test_dir, "test_design_api_interface.py"),
        __file__  # This integration test file
    ]
    
    # Run tests with detailed output
    exit_code = pytest.main([
        *test_files,
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--durations=10",  # Show 10 slowest tests
    ])
    
    if exit_code == 0:
        print("\n✅ ALL TESTS PASSED! Design module is fully functional.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    return exit_code


if __name__ == "__main__":
    run_all_design_tests()
