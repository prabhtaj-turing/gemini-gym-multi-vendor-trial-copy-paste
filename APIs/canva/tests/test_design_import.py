# test_design_import.py
import pytest
import time
import base64
from unittest.mock import patch, MagicMock
from canva.Canva.Design.DesignImport import create_design_import, get_design_import_job, create_url_import_job, get_url_import_job
from canva.SimulationEngine.db import DB


class TestCreateDesignImport:
    """Test cases for create_design_import function"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB["ImportJobs"] = {}
        DB["Designs"] = {}
    
    def test_create_import_job_success(self):
        """Test successful import job creation"""
        title = "Test Design"
        title_base64 = base64.b64encode(title.encode('utf-8')).decode('utf-8')
        import_metadata = {
            "title_base64": title_base64,
            "mime_type": "application/pdf"
        }
        
        result = create_design_import(import_metadata)
        
        assert "job" in result
        job = result["job"]
        assert "id" in job
        assert job["status"] in ["in_progress", "success", "failed"]
        assert job["import_metadata"] == import_metadata
        assert "created_at" in job
        assert "updated_at" in job
    
    def test_create_import_job_success_status_creates_design(self):
        """Test that successful import creates design in DB"""
        title = "Test Design"
        title_base64 = base64.b64encode(title.encode('utf-8')).decode('utf-8')
        import_metadata = {"title_base64": title_base64}
        
        with patch('random.choice', return_value="success"):
            result = create_design_import(import_metadata)
            job = result["job"]
            
            if job["status"] == "success":
                assert "result" in job
                assert "designs" in job["result"]
                design = job["result"]["designs"][0]
                assert design["title"] == title
                assert "id" in design
                assert "urls" in design
                assert "page_count" in design
                
                # Check design was added to main DB
                assert design["id"] in DB["Designs"]
    
    def test_create_import_job_failed_status_includes_error(self):
        """Test that failed import includes error info"""
        title_base64 = base64.b64encode("Test".encode('utf-8')).decode('utf-8')
        import_metadata = {"title_base64": title_base64}
        
        with patch('random.choice', return_value="failed"):
            result = create_design_import(import_metadata)
            job = result["job"]
            
            if job["status"] == "failed":
                assert "error" in job
                assert "code" in job["error"]
                assert "message" in job["error"]
    
    def test_create_import_job_all_mime_types(self):
        """Test import with all valid mime types"""
        valid_mime_types = [
            "application/pdf",
            "image/png", 
            "image/jpeg",
            "image/jpg",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ]
        
        title_base64 = base64.b64encode("Test".encode('utf-8')).decode('utf-8')
        
        for mime_type in valid_mime_types:
            import_metadata = {
                "title_base64": title_base64,
                "mime_type": mime_type
            }
            result = create_design_import(import_metadata)
            assert "job" in result
    
    def test_create_import_job_invalid_metadata_not_dict(self):
        """Test import with non-dict metadata"""
        with pytest.raises(ValueError, match="import_metadata must be a dictionary"):
            create_design_import("invalid")
    
    def test_create_import_job_missing_title_base64(self):
        """Test import without title_base64"""
        with pytest.raises(ValueError, match="import_metadata must contain 'title_base64' field"):
            create_design_import({"mime_type": "application/pdf"})
    
    def test_create_import_job_invalid_title_base64_not_string(self):
        """Test import with non-string title_base64"""
        with pytest.raises(ValueError, match="title_base64 must be a non-empty string"):
            create_design_import({"title_base64": 123})
    
    def test_create_import_job_empty_title_base64(self):
        """Test import with empty title_base64"""
        with pytest.raises(ValueError, match="title_base64 must be a non-empty string"):
            create_design_import({"title_base64": ""})
    
    def test_create_import_job_invalid_base64(self):
        """Test import with invalid base64 encoding"""
        with pytest.raises(ValueError, match="title_base64 must be valid base64 encoded string"):
            create_design_import({"title_base64": "invalid_base64!!!"})
    
    def test_create_import_job_title_too_long(self):
        """Test import with decoded title too long"""
        long_title = "a" * 51  # Max is 50 characters
        title_base64 = base64.b64encode(long_title.encode('utf-8')).decode('utf-8')
        
        with pytest.raises(ValueError, match="Decoded title must not exceed 50 characters"):
            create_design_import({"title_base64": title_base64})
    
    def test_create_import_job_invalid_mime_type_not_string(self):
        """Test import with non-string mime_type"""
        title_base64 = base64.b64encode("Test".encode('utf-8')).decode('utf-8')
        
        with pytest.raises(ValueError, match="mime_type must be a string"):
            create_design_import({
                "title_base64": title_base64,
                "mime_type": 123
            })
    
    def test_create_import_job_invalid_mime_type(self):
        """Test import with invalid mime_type"""
        title_base64 = base64.b64encode("Test".encode('utf-8')).decode('utf-8')
        
        with pytest.raises(ValueError, match="mime_type must be one of"):
            create_design_import({
                "title_base64": title_base64,
                "mime_type": "invalid/type"
            })


class TestGetDesignImportJob:
    """Test cases for get_design_import_job function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        title_base64 = base64.b64encode("Test Design".encode('utf-8')).decode('utf-8')
        DB["ImportJobs"] = {
            "job1": {
                "id": "job1",
                "status": "success",
                "import_metadata": {"title_base64": title_base64},
                "result": {
                    "designs": [{
                        "id": "design1",
                        "title": "Test Design",
                        "urls": {"edit_url": "edit", "view_url": "view"}
                    }]
                },
                "created_at": int(time.time()) - 100,
                "updated_at": int(time.time())
            },
            "job2": {
                "id": "job2",
                "status": "failed",
                "import_metadata": {"title_base64": title_base64},
                "error": {"code": "invalid_file", "message": "Import failed"},
                "created_at": int(time.time()) - 100,
                "updated_at": int(time.time())
            },
            "job3": {
                "id": "job3",
                "status": "in_progress", 
                "import_metadata": {"title_base64": title_base64},
                "created_at": int(time.time()) - 20,  # Recent job
                "updated_at": int(time.time()) - 20
            }
        }
        DB["Designs"] = {}
    
    def test_get_import_job_success_status(self):
        """Test retrieving successful import job"""
        result = get_design_import_job("job1")
        
        assert "job" in result
        job = result["job"]
        assert job["id"] == "job1"
        assert job["status"] == "success"
        assert "result" in job
        # Internal fields should be removed
        assert "import_metadata" not in job
        assert "created_at" not in job
    
    def test_get_import_job_failed_status(self):
        """Test retrieving failed import job"""
        result = get_design_import_job("job2")
        
        job = result["job"]
        assert job["status"] == "failed"
        assert "error" in job
        assert job["error"]["code"] == "invalid_file"
    
    def test_get_import_job_in_progress_completion(self):
        """Test in-progress job that should complete"""
        # Create an old in-progress job
        old_job_id = "old_job"
        title_base64 = base64.b64encode("Old Job".encode('utf-8')).decode('utf-8')
        DB["ImportJobs"][old_job_id] = {
            "id": old_job_id,
            "status": "in_progress",
            "import_metadata": {"title_base64": title_base64},
            "created_at": int(time.time()) - 100,  # Old enough to complete
            "updated_at": int(time.time()) - 100
        }
        
        result = get_design_import_job(old_job_id)
        job = result["job"]
        
        # Should have been updated to success or failed
        assert job["status"] in ["success", "failed"]
    
    def test_get_import_job_invalid_id(self):
        """Test retrieving import job with invalid ID"""
        with pytest.raises(ValueError, match="job_id must be a non-empty string"):
            get_design_import_job("")
    
    def test_get_import_job_not_found(self):
        """Test retrieving non-existent import job"""
        with pytest.raises(ValueError, match="Import job with ID nonexistent not found"):
            get_design_import_job("nonexistent")


class TestCreateUrlImportJob:
    """Test cases for create_url_import_job function"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB["ImportJobs"] = {}
        DB["Designs"] = {}
    
    def test_create_url_import_job_success(self):
        """Test successful URL import job creation"""
        title = "URL Import Test"
        url = "https://example.com/file.pdf"
        
        result = create_url_import_job(title, url)
        
        assert "job" in result
        job = result["job"]
        assert "id" in job
        assert job["status"] in ["in_progress", "success", "failed"]
        assert job["title"] == title
        assert job["url"] == url
        assert job["job_type"] == "url_import"
    
    def test_create_url_import_job_with_mime_type(self):
        """Test URL import with mime_type specified"""
        result = create_url_import_job(
            "Test", 
            "https://example.com/file.pdf",
            mime_type="application/pdf"
        )
        
        job = result["job"]
        assert job["mime_type"] == "application/pdf"
    
    def test_create_url_import_job_success_creates_design(self):
        """Test that successful URL import creates design"""
        with patch('random.choice', return_value="success"):
            result = create_url_import_job("Test", "https://example.com/file.pdf")
            job = result["job"]
            
            if job["status"] == "success":
                assert "result" in job
                design = job["result"]["designs"][0]
                assert design["title"] == "Test"
                assert design["id"] in DB["Designs"]
    
    def test_create_url_import_job_failed_includes_error(self):
        """Test that failed URL import includes error"""
        with patch('random.choice', side_effect=["failed", "fetch_failed"]):
            result = create_url_import_job("Test", "https://example.com/file.pdf")
            job = result["job"]
            
            # Since we patched random.choice to return "failed" for status, "fetch_failed" for error code
            assert job["status"] == "failed"
            assert "error" in job
            assert job["error"]["code"] in ["duplicate_import", "fetch_failed", "invalid_url", "unsupported_format"]
    
    def test_create_url_import_job_invalid_title_not_string(self):
        """Test URL import with non-string title"""
        with pytest.raises(ValueError, match="title must be a non-empty string"):
            create_url_import_job(123, "https://example.com/file.pdf")
    
    def test_create_url_import_job_title_too_short(self):
        """Test URL import with title too short"""
        with pytest.raises(ValueError, match="title must be a non-empty string"):
            create_url_import_job("", "https://example.com/file.pdf")
    
    def test_create_url_import_job_title_too_long(self):
        """Test URL import with title too long"""
        long_title = "a" * 256
        with pytest.raises(ValueError, match="title must be between 1 and 255 characters"):
            create_url_import_job(long_title, "https://example.com/file.pdf")
    
    def test_create_url_import_job_invalid_url_not_string(self):
        """Test URL import with non-string URL"""
        with pytest.raises(ValueError, match="url must be a non-empty string"):
            create_url_import_job("Test", 123)
    
    def test_create_url_import_job_url_too_long(self):
        """Test URL import with URL too long"""
        long_url = "https://example.com/" + "a" * 2048
        with pytest.raises(ValueError, match="url must be between 1 and 2048 characters"):
            create_url_import_job("Test", long_url)
    
    def test_create_url_import_job_invalid_url_format(self):
        """Test URL import with invalid URL format"""
        with pytest.raises(ValueError, match="url must be a valid HTTP or HTTPS URL"):
            create_url_import_job("Test", "not-a-url")
    
    def test_create_url_import_job_valid_url_formats(self):
        """Test URL import with various valid URL formats"""
        valid_urls = [
            "https://example.com/file.pdf",
            "http://example.com/file.pdf",
            "https://subdomain.example.com/path/file.pdf",
            "https://localhost:8080/file.pdf",
            "https://192.168.1.1/file.pdf"
        ]
        
        for url in valid_urls:
            result = create_url_import_job("Test", url)
            assert "job" in result
    
    def test_create_url_import_job_invalid_mime_type(self):
        """Test URL import with invalid mime_type"""
        with pytest.raises(ValueError, match="mime_type must be one of"):
            create_url_import_job(
                "Test", 
                "https://example.com/file.pdf",
                mime_type="invalid/type"
            )


class TestGetUrlImportJob:
    """Test cases for get_url_import_job function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["ImportJobs"] = {
            "url_job1": {
                "id": "url_job1",
                "status": "success",
                "title": "URL Test",
                "url": "https://example.com/file.pdf",
                "job_type": "url_import",
                "result": {
                    "designs": [{
                        "id": "design1",
                        "title": "URL Test",
                        "urls": {"edit_url": "edit", "view_url": "view"}
                    }]
                },
                "created_at": int(time.time()) - 100,
                "updated_at": int(time.time())
            },
            "url_job2": {
                "id": "url_job2",
                "status": "in_progress",
                "title": "In Progress",
                "url": "https://example.com/file2.pdf", 
                "job_type": "url_import",
                "created_at": int(time.time()) - 20,
                "updated_at": int(time.time()) - 20
            },
            "regular_job": {
                "id": "regular_job",
                "status": "success",
                "job_type": "file_import",  # Not a URL import
                "created_at": int(time.time()) - 100,
                "updated_at": int(time.time())
            }
        }
        DB["Designs"] = {}
    
    def test_get_url_import_job_success(self):
        """Test retrieving successful URL import job"""
        result = get_url_import_job("url_job1")
        
        assert "job" in result
        job = result["job"]
        assert job["id"] == "url_job1"
        assert job["status"] == "success"
        assert "result" in job
        # Internal fields should be removed
        assert "title" not in job
        assert "url" not in job
        assert "job_type" not in job
        assert "created_at" not in job
    
    def test_get_url_import_job_in_progress_completion(self):
        """Test in-progress URL job that should complete"""
        # Create an old in-progress job
        old_job_id = "old_url_job"
        DB["ImportJobs"][old_job_id] = {
            "id": old_job_id,
            "status": "in_progress",
            "title": "Old Job",
            "url": "https://example.com/old.pdf",
            "job_type": "url_import",
            "created_at": int(time.time()) - 100,  # Old enough to complete
            "updated_at": int(time.time()) - 100
        }
        
        result = get_url_import_job(old_job_id)
        job = result["job"]
        
        # Should have been updated to success or failed
        assert job["status"] in ["success", "failed"]
    
    def test_get_url_import_job_invalid_id(self):
        """Test retrieving URL import job with invalid ID"""
        with pytest.raises(ValueError, match="job_id must be a non-empty string"):
            get_url_import_job("")
    
    def test_get_url_import_job_not_found(self):
        """Test retrieving non-existent URL import job"""
        with pytest.raises(ValueError, match="Import job with ID nonexistent not found"):
            get_url_import_job("nonexistent")
    
    def test_get_url_import_job_wrong_type(self):
        """Test retrieving regular import job with URL function"""
        with pytest.raises(ValueError, match="Job regular_job is not a URL import job"):
            get_url_import_job("regular_job")


if __name__ == "__main__":
    pytest.main([__file__])
