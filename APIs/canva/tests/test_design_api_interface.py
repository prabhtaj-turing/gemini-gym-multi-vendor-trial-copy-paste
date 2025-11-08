# test_design_api_interface.py
"""
Test the public API interface for Canva Design module.
This tests that all functions are accessible through the main canva module.
"""

import pytest
import base64
import sys
import os

# Add the APIs directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import canva
from canva.SimulationEngine.db import DB


class TestCanvaDesignAPI:
    """Test Canva Design functions through the main API interface"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB["Designs"] = {}
        DB["CommentThreads"] = {}
        DB["CommentReplies"] = {}
        DB["ExportJobs"] = {}
        DB["ImportJobs"] = {}
    
    def test_create_design_api(self):
        """Test create_design through main API"""
        result = canva.create_design(
            design_type={"type": "preset", "name": "doc"},
            asset_id="api_test_asset",
            title="API Test Design"
        )
        
        assert "id" in result
        assert result["title"] == "API Test Design"
        assert result["asset_id"] == "api_test_asset"
    
    def test_list_designs_api(self):
        """Test list_designs through main API"""
        # Create some test designs first
        canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Design 1")
        canva.create_design(design_type={"type": "preset", "name": "presentation"}, asset_id="asset2", title="Design 2")
        
        result = canva.list_designs()
        assert len(result) == 2
        
        # Test with query
        filtered = canva.list_designs(query="Design 1")
        assert len(filtered) == 1
        assert filtered[0]["title"] == "Design 1"
    
    def test_get_design_api(self):
        """Test get_design through main API"""
        # Create a design first
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Test Design")
        design_id = created["id"]
        
        result = canva.get_design(design_id)
        assert result is not None
        assert result["design"]["id"] == design_id
        assert result["design"]["title"] == "Test Design"
    
    def test_create_design_optional_params_api(self):
        """Test create_design with optional parameters through main API"""
        # Test with no parameters
        result1 = canva.create_design()
        assert "id" in result1
        assert result1["title"] == "Untitled Design"  # Default title
        
        # Test with only title
        result2 = canva.create_design(title="Only Title")
        assert result2["title"] == "Only Title"
        assert result2["asset_id"] is None

    def test_get_design_pages_api(self):
        """Test get_design_pages through main API"""
        # Create a design first
        created = canva.create_design(design_type={"type": "preset", "name": "presentation"}, asset_id="asset1", title="Multi-page Design")
        design_id = created["id"]
        
        # Add some mock pages to the design
        DB["Designs"][design_id]["pages"] = {
            "page1": {"index": 1, "thumbnail": {"width": 100, "height": 100, "url": "url1"}},
            "page2": {"index": 2, "thumbnail": {"width": 100, "height": 100, "url": "url2"}}
        }
        
        result = canva.get_design_pages(design_id)
        assert result is not None
        assert "pages" in result
        assert len(result["pages"]) == 2
    
    def test_create_design_export_job_api(self):
        """Test create_design_export_job through main API"""
        # Create a design first
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Export Test")
        design_id = created["id"]
        
        # Create export job
        result = canva.create_design_export_job(
            design_id,
            {"type": "pdf", "size": "a4"}
        )
        
        assert "job" in result
        assert result["job"]["design_id"] == design_id
        assert result["job"]["format"]["type"] == "pdf"
    
    def test_get_design_export_job_api(self):
        """Test get_design_export_job through main API"""
        # Create a design and export job first
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Export Test")
        design_id = created["id"]
        
        export_result = canva.create_design_export_job(design_id, {"type": "pdf"})
        job_id = export_result["job"]["id"]
        
        # Get export job status
        result = canva.get_design_export_job(job_id)
        assert "job" in result
        assert result["job"]["id"] == job_id
    
    def test_create_design_import_job_api(self):
        """Test create_design_import_job through main API"""
        title = "Imported Design"
        title_base64 = base64.b64encode(title.encode('utf-8')).decode('utf-8')
        import_metadata = {
            "title_base64": title_base64,
            "mime_type": "application/pdf"
        }
        
        result = canva.create_design_import_job(import_metadata)
        
        assert "job" in result
        assert result["job"]["import_metadata"] == import_metadata
    
    def test_get_design_import_job_api(self):
        """Test get_design_import_job through main API"""
        # Create import job first
        title_base64 = base64.b64encode("Test".encode('utf-8')).decode('utf-8')
        import_result = canva.create_design_import_job({"title_base64": title_base64})
        job_id = import_result["job"]["id"]
        
        # Get import job status
        result = canva.get_design_import_job(job_id)
        assert "job" in result
        assert result["job"]["id"] == job_id
    
    def test_create_url_design_import_job_api(self):
        """Test create_url_design_import_job through main API"""
        result = canva.create_url_design_import_job(
            "URL Import Test",
            "https://example.com/file.pdf",
            mime_type="application/pdf"
        )
        
        assert "job" in result
        assert result["job"]["title"] == "URL Import Test"
        assert result["job"]["url"] == "https://example.com/file.pdf"
        assert result["job"]["job_type"] == "url_import"
    
    def test_get_url_design_import_job_api(self):
        """Test get_url_design_import_job through main API"""
        # Create URL import job first
        import_result = canva.create_url_design_import_job(
            "Test", 
            "https://example.com/file.pdf"
        )
        job_id = import_result["job"]["id"]
        
        # Get URL import job status
        result = canva.get_url_design_import_job(job_id)
        assert "job" in result
        assert result["job"]["id"] == job_id
    
    def test_create_comment_thread_api(self):
        """Test create_comment_thread through main API"""
        # Create a design first
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Comment Test")
        design_id = created["id"]
        
        # Create comment thread
        result = canva.create_comment_thread(
            design_id,
            "This looks great! What do you think [user123:team456]?"
        )
        
        assert "thread" in result
        assert result["thread"]["design_id"] == design_id
        assert "user123:team456" in result["thread"]["content"]["mentions"]
    
    def test_create_comment_reply_api(self):
        """Test create_comment_reply through main API"""
        # Create a design and thread first
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Reply Test")
        design_id = created["id"]
        
        thread_result = canva.create_comment_thread(design_id, "Original comment")
        thread_id = thread_result["thread"]["id"]
        
        # Create reply
        result = canva.create_comment_reply(
            design_id,
            thread_id,
            "I agree with this comment!"
        )
        
        assert "reply" in result
        assert result["reply"]["design_id"] == design_id
        assert result["reply"]["thread_id"] == thread_id
    
    def test_get_comment_thread_api(self):
        """Test get_comment_thread through main API"""
        # Create a design and thread first
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Get Thread Test")
        design_id = created["id"]
        
        thread_result = canva.create_comment_thread(design_id, "Test thread")
        thread_id = thread_result["thread"]["id"]
        
        # Get the thread
        result = canva.get_comment_thread(design_id, thread_id)
        assert "thread" in result
        assert result["thread"]["id"] == thread_id
    
    def test_get_comment_reply_api(self):
        """Test get_comment_reply through main API"""
        # Create design, thread, and reply first
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="Get Reply Test")
        design_id = created["id"]
        
        thread_result = canva.create_comment_thread(design_id, "Test thread")
        thread_id = thread_result["thread"]["id"]
        
        reply_result = canva.create_comment_reply(design_id, thread_id, "Test reply")
        reply_id = reply_result["reply"]["id"]
        
        # Get the reply
        result = canva.get_comment_reply(design_id, thread_id, reply_id)
        assert "reply" in result
        assert result["reply"]["id"] == reply_id
    
    def test_list_comment_replies_api(self):
        """Test list_comment_replies through main API"""
        # Create design, thread, and multiple replies
        created = canva.create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset1", title="List Replies Test")
        design_id = created["id"]
        
        thread_result = canva.create_comment_thread(design_id, "Test thread")
        thread_id = thread_result["thread"]["id"]
        
        # Create multiple replies
        for i in range(3):
            canva.create_comment_reply(design_id, thread_id, f"Reply {i+1}")
        
        # List all replies
        result = canva.list_comment_replies(design_id, thread_id)
        assert "items" in result
        assert len(result["items"]) == 3
        
        # Test with limit
        limited_result = canva.list_comment_replies(design_id, thread_id, limit=2)
        assert len(limited_result["items"]) == 2
        assert "continuation" in limited_result
    
    def test_api_function_availability(self):
        """Test that all expected functions are available in the main canva module"""
        expected_functions = [
            # Core design functions
            "create_design",
            "list_designs", 
            "get_design",

            "get_design_pages",
            
            # Export functions
            "create_design_export_job",
            "get_design_export_job",
            
            # Import functions
            "create_design_import_job",
            "get_design_import_job",
            "create_url_design_import_job",
            "get_url_design_import_job",
            
            # Comment functions
            "create_comment_thread",
            "create_comment_reply",
            "get_comment_thread", 
            "get_comment_reply",
            "list_comment_replies"
        ]
        
        for func_name in expected_functions:
            assert hasattr(canva, func_name), f"Function {func_name} not available in canva module"
            func = getattr(canva, func_name)
            assert callable(func), f"{func_name} is not callable"
    
    def test_end_to_end_api_workflow(self):
        """Test complete workflow using only the public API"""
        # 1. Create design
        design = canva.create_design(
            {"type": "preset", "name": "presentation"},
            "workflow_asset",
            "API Workflow Test"
        )
        design_id = design["id"]
        
        # 2. Create comment thread with assignee
        thread = canva.create_comment_thread(
            design_id,
            "Please review this presentation [reviewer:team]",
            assignee_id="reviewer"
        )
        thread_id = thread["thread"]["id"]
        
        # 3. Add reply
        reply = canva.create_comment_reply(
            design_id,
            thread_id,
            "Looks good to me!"
        )
        
        # 4. Create export job
        export_job = canva.create_design_export_job(
            design_id,
            {"type": "pptx", "export_quality": "pro"}
        )
        
        # 5. Create URL import job
        url_import = canva.create_url_design_import_job(
            "External Design",
            "https://example.com/external.pptx"
        )
        
        # 6. List all designs
        all_designs = canva.list_designs()
        design_ids = [d["id"] for d in all_designs]
        assert design_id in design_ids



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
