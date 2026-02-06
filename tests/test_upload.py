"""
Tests for file upload functionality.
"""
import pytest
from fastapi import status
from unittest.mock import patch
import tempfile


class TestImageUpload:
    """Test image upload for scanning"""
    
    def test_upload_image_success(self, client, auth_headers, mock_user, test_image_path):
        """Test successful image upload"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get, \
             patch('app.services.storage_service.upload_scan_image') as mock_upload, \
             patch('app.tasks.ocr_tasks.process_scan.delay') as mock_task:
            
            mock_get.return_value = mock_user
            mock_upload.return_value = "https://storage/scan.jpg"
            mock_task.return_value.id = "task-123"
            
            with open(test_image_path, "rb") as f:
                response = client.post(
                    "/api/v1/scan/upload",
                    headers=auth_headers,
                    files={"file": ("test.jpg", f, "image/jpeg")}
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "scan_id" in data
    
    def test_upload_file_too_large(self, client, auth_headers):
        """Test upload with file exceeding size limit"""
        # Create file larger than 10MB
        large_file = b"0" * (11 * 1024 * 1024)
        
        response = client.post(
            "/api/v1/scan/upload",
            headers=auth_headers,
            files={"file": ("large.jpg", large_file, "image/jpeg")}
        )
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    def test_upload_invalid_file_type(self, client, auth_headers):
        """Test upload with invalid file type"""
        response = client.post(
            "/api/v1/scan/upload",
            headers=auth_headers,
            files={"file": ("test.txt", b"text content", "text/plain")}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_upload_pdf_success(self, client, auth_headers, mock_user, test_pdf_path):
        """Test successful PDF upload"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id') as mock_get, \
             patch('app.services.storage_service.upload_scan_image') as mock_upload, \
             patch('app.tasks.ocr_tasks.process_scan.delay') as mock_task:
            
            mock_get.return_value = mock_user
            mock_upload.return_value = "https://storage/scan.pdf"
            mock_task.return_value.id = "task-123"
            
            with open(test_pdf_path, "rb") as f:
                response = client.post(
                    "/api/v1/scan/upload",
                    headers=auth_headers,
                    files={"file": ("test.pdf", f, "application/pdf")}
                )
        
        assert response.status_code == status.HTTP_200_OK