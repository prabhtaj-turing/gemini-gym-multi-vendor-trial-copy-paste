# test_design_export.py
import pytest
import time
from unittest.mock import patch, MagicMock
from canva.Canva.Design.DesignExport import create_design_export_job, get_design_export_job
from canva.SimulationEngine.custom_errors import InvalidAssetIDError, InvalidTitleError, InvalidDesignIDError
from canva.SimulationEngine.db import DB


class TestCreateDesignExportJob:
    """Test cases for create_design_export_job function"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB["Designs"] = {
            "design1": {
                "id": "design1",
                "title": "Test Design",
                "page_count": 3
            }
        }
        DB["ExportJobs"] = {}
    
    def test_create_export_job_pdf_success(self):
        """Test successful PDF export job creation"""
        format_config = {"type": "pdf", "size": "a4"}
        
        result = create_design_export_job("design1", format_config)
        
        assert "job" in result
        job = result["job"]
        assert "id" in job
        assert job["status"] in ["in_progress", "success", "failed"]
        assert job["design_id"] == "design1"
        assert job["format"] == format_config
    
    def test_create_export_job_jpg_with_quality(self):
        """Test JPG export with quality parameter"""
        format_config = {"type": "jpg", "quality": 85}
        
        result = create_design_export_job("design1", format_config)
        assert result["job"]["format"]["quality"] == 85
    
    def test_create_export_job_mp4_with_quality(self):
        """Test MP4 export with quality parameter"""
        format_config = {"type": "mp4", "quality": 75}
        
        result = create_design_export_job("design1", format_config)
        assert result["job"]["format"]["quality"] == 75
    
    def test_create_export_job_png_with_options(self):
        """Test PNG export with transparency options"""
        format_config = {
            "type": "png", 
            "lossless": True, 
            "transparent_background": True,
            "width": 800,
            "height": 600
        }
        
        result = create_design_export_job("design1", format_config)
        job = result["job"]
        assert job["format"]["lossless"] is True
        assert job["format"]["transparent_background"] is True
    
    def test_create_export_job_success_status_includes_urls(self):
        """Test that successful jobs include download URLs"""
        format_config = {"type": "pdf"}
        
        with patch('random.choice', return_value="success"):
            result = create_design_export_job("design1", format_config)
            job = result["job"]
            if job["status"] == "success":
                assert "urls" in job
                assert len(job["urls"]) > 0
    
    def test_create_export_job_failed_status_includes_error(self):
        """Test that failed jobs include error information"""
        format_config = {"type": "pdf"}
        
        with patch('random.choice', return_value="failed"):
            result = create_design_export_job("design1", format_config)
            job = result["job"]
            if job["status"] == "failed":
                assert "error" in job
                assert "code" in job["error"]
                assert "message" in job["error"]
    
    def test_create_export_job_invalid_design_id(self):
        """Test export job creation with invalid design_id"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            create_design_export_job(123, {"type": "pdf"})
    
    def test_create_export_job_empty_design_id(self):
        """Test export job creation with empty design_id"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            create_design_export_job("", {"type": "pdf"})
    
    def test_create_export_job_design_not_found(self):
        """Test export job creation with non-existent design"""
        with pytest.raises(ValueError, match="Design with ID nonexistent not found"):
            create_design_export_job("nonexistent", {"type": "pdf"})
    
    def test_create_export_job_invalid_format_not_dict(self):
        """Test export job creation with non-dict format"""
        with pytest.raises(ValueError, match="format must be a dictionary"):
            create_design_export_job("design1", "invalid")
    
    def test_create_export_job_missing_type(self):
        """Test export job creation without type in format"""
        with pytest.raises(ValueError, match="format must contain 'type' field"):
            create_design_export_job("design1", {"size": "a4"})
    
    def test_create_export_job_invalid_type(self):
        """Test export job creation with invalid type"""
        with pytest.raises(ValueError, match="format.type must be one of"):
            create_design_export_job("design1", {"type": "invalid"})
    
    def test_create_export_job_invalid_jpg_quality(self):
        """Test export job creation with invalid JPG quality"""
        with pytest.raises(ValueError, match="Quality must be an integer between 1 and 100"):
            create_design_export_job("design1", {"type": "jpg", "quality": 150})
    
    def test_create_export_job_invalid_mp4_quality(self):
        """Test export job creation with invalid MP4 quality"""
        with pytest.raises(ValueError, match="Quality must be an integer between 1 and 100"):
            create_design_export_job("design1", {"type": "mp4", "quality": "invalid"})
    
    def test_create_export_job_invalid_export_quality(self):
        """Test export job creation with invalid export_quality"""
        with pytest.raises(ValueError, match="export_quality must be 'regular' or 'pro'"):
            create_design_export_job("design1", {"type": "pdf", "export_quality": "invalid"})
    
    def test_create_export_job_invalid_size(self):
        """Test export job creation with invalid size"""
        with pytest.raises(ValueError, match="size must be one of: a4, a3, letter, legal"):
            create_design_export_job("design1", {"type": "pdf", "size": "invalid"})
    
    def test_create_export_job_invalid_dimensions(self):
        """Test export job creation with invalid dimensions"""
        with pytest.raises(ValueError, match="height must be an integer between 40 and 25000"):
            create_design_export_job("design1", {"type": "png", "height": 30})
        
        with pytest.raises(ValueError, match="width must be an integer between 40 and 25000"):
            create_design_export_job("design1", {"type": "png", "width": 30000})


class TestGetDesignExportJob:
    """Test cases for get_design_export_job function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["ExportJobs"] = {
            "job1": {
                "id": "job1",
                "status": "success",
                "design_id": "design1",
                "format": {"type": "pdf"},
                "urls": ["http://example.com/file1.pdf"],
                "created_at": int(time.time()) - 100,
                "updated_at": int(time.time())
            },
            "job2": {
                "id": "job2", 
                "status": "failed",
                "design_id": "design2",
                "format": {"type": "jpg"},
                "error": {"code": "internal_failure", "message": "Export failed"},
                "created_at": int(time.time()) - 100,
                "updated_at": int(time.time())
            },
            "job3": {
                "id": "job3",
                "status": "in_progress",
                "design_id": "design3", 
                "format": {"type": "png"},
                "created_at": int(time.time()) - 20,  # Recent job
                "updated_at": int(time.time()) - 20
            }
        }
    
    def test_get_export_job_success_status(self):
        """Test retrieving successful export job"""
        result = get_design_export_job("job1")
        
        assert "job" in result
        job = result["job"]
        assert job["id"] == "job1"
        assert job["status"] == "success"
        assert "urls" in job
        # Internal fields should be removed
        assert "design_id" not in job
        assert "format" not in job
        assert "created_at" not in job
    
    def test_get_export_job_failed_status(self):
        """Test retrieving failed export job"""
        result = get_design_export_job("job2")
        
        job = result["job"]
        assert job["status"] == "failed"
        assert "error" in job
        assert job["error"]["code"] == "internal_failure"
    
    def test_get_export_job_in_progress_completion(self):
        """Test in-progress job that should complete"""
        # Create an old in-progress job
        old_job_id = "old_job"
        # Ensure Designs table exists
        if "Designs" not in DB:
            DB["Designs"] = {}
        DB["Designs"]["design1"] = {"id": "design1", "page_count": 1}
        
        DB["ExportJobs"][old_job_id] = {
            "id": old_job_id,
            "status": "in_progress",
            "design_id": "design1",
            "format": {"type": "pdf"},
            "created_at": int(time.time()) - 100,  # Old enough to complete
            "updated_at": int(time.time()) - 100
        }
        
        result = get_design_export_job(old_job_id)
        job = result["job"]
        
        # Should have been updated to success or failed
        assert job["status"] in ["success", "failed"]
    
    def test_get_export_job_invalid_id(self):
        """Test retrieving export job with invalid ID"""
        with pytest.raises(ValueError, match="job_id must be a non-empty string"):
            get_design_export_job("")
    
    def test_get_export_job_not_found(self):
        """Test retrieving non-existent export job"""
        with pytest.raises(ValueError, match="Export job with ID nonexistent not found"):
            get_design_export_job("nonexistent")





if __name__ == "__main__":
    pytest.main([__file__])
