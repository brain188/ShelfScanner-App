"""
Tests for file upload functionality.
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock, MagicMock
import tempfile
from pathlib import Path
from datetime import datetime, timezone


class TestImageUpload:
    """Test image upload for scanning"""
    
    def test_upload_image_success(self, client, auth_headers, mock_user, test_image_path):
        """Test successful image upload"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('app.db.supabase.supabase_ops.create_scan_result', new_callable=AsyncMock) as mock_create, \
             patch('app.api.v1.scan.process_scan_async') as mock_process:
            
            mock_get_user.return_value = mock_user
            mock_create.return_value = {
                "id": "scan-123",
                "user_id": mock_user["id"],
                "status": "pending",
                "scan_type": "image",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            with open(test_image_path, "rb") as f:
                response = client.post(
                    "/api/v1/scan/upload",
                    headers=auth_headers,
                    files={"file": ("test.jpg", f, "image/jpeg")}
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "scan_id" in data
        assert data["scan_id"] == "scan-123"
        assert data["status"] == "pending"
    
    def test_upload_file_too_large(self, client, auth_headers):
        """Test upload with file exceeding size limit"""
        # Create file larger than 10MB
        large_file = b"0" * (11 * 1024 * 1024)
        
        response = client.post(
            "/api/v1/scan/upload",
            headers=auth_headers,
            files={"file": ("large.jpg", large_file, "image/jpeg")}
        )
        
        assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        assert "too large" in response.json()["detail"].lower()
    
    def test_upload_invalid_file_type(self, client, auth_headers):
        """Test upload with invalid file type"""
        response = client.post(
            "/api/v1/scan/upload",
            headers=auth_headers,
            files={"file": ("test.txt", b"text content", "text/plain")}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "not supported" in response.json()["detail"].lower()
    
    def test_upload_pdf_success(self, client, auth_headers, mock_user, test_pdf_path):
        """Test successful PDF upload"""
        with patch('app.db.supabase.supabase_ops.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('app.db.supabase.supabase_ops.create_scan_result', new_callable=AsyncMock) as mock_create, \
             patch('app.api.v1.scan.process_scan_async') as mock_process:
            
            mock_get_user.return_value = mock_user
            mock_create.return_value = {
                "id": "scan-456",
                "user_id": mock_user["id"],
                "status": "pending",
                "scan_type": "pdf",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            with open(test_pdf_path, "rb") as f:
                response = client.post(
                    "/api/v1/scan/upload",
                    headers=auth_headers,
                    files={"file": ("test.pdf", f, "application/pdf")}
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "scan_id" in data
        assert data["scan_id"] == "scan-456"