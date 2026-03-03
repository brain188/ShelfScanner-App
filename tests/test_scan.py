"""
Tests for scan endpoints and OCR functionality.
"""
import pytest
import tempfile
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

from app.main import app
from app.services.ocr_service import ocr_service
from app.models.scan_result import ScanStatus, ScanType, OCRConfidence
from app.core.security import get_current_active_user


@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "role": "user"
    }


@pytest.fixture
def client(mock_user):
    """Test client with mocked authentication"""
    def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_file():
    """Sample image file for testing"""
    from io import BytesIO
    from PIL import Image
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return ("test.jpg", img_bytes, "image/jpeg")


class TestScanUpload:
    """Tests for scan upload endpoint"""
    
    @pytest.mark.asyncio
    @patch('app.db.supabase.supabase_ops.update_scan_result', new_callable=AsyncMock)  
    @patch('app.db.supabase.supabase_ops.create_scan_result', new_callable=AsyncMock)
    async def test_upload_image_success(
        self,
        mock_create_scan,
        mock_update_scan,
        client,
        sample_image_file
    ):
        """Test successful image upload"""
        mock_create_scan.return_value = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "test_user_123",
            "status": ScanStatus.PENDING
        }
        mock_update_scan.return_value = None
        
        response = client.post(
            "/api/v1/scan/upload",
            files={"file": sample_image_file},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert data["status"] in [ScanStatus.PENDING, ScanStatus.PROCESSING]
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        response = client.post(
            "/api/v1/scan/upload",
            files={"file": ("test.txt", b"test content", "text/plain")},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 422
        assert "not supported" in response.json()["detail"].lower()
    
    def test_upload_file_too_large(self, client):
        """Test upload with file exceeding size limit"""
        # Create large file (> 10MB)
        large_content = b"x" * (11 * 1024 * 1024)
        
        response = client.post(
            "/api/v1/scan/upload",
            files={"file": ("large.jpg", large_content, "image/jpeg")},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()
    
    def test_upload_unauthorized(self, sample_image_file):
        """Test upload without authentication"""
        test_client = TestClient(app)
        response = test_client.post(
            "/api/v1/scan/upload",
            files={"file": sample_image_file}
        )
        
        assert response.status_code == 401


class TestScanResult:
    """Tests for scan result retrieval"""
    
    @pytest.mark.asyncio
    @patch('app.db.supabase.supabase_ops.get_user_scans', new_callable=AsyncMock)
    async def test_get_scan_result_success(self, mock_db, client):
        """Test successful scan result retrieval"""
        mock_db.return_value = [{
            "id": "scan_123",
            "user_id": "test_user_123",
            "status": ScanStatus.COMPLETED,
            "scan_type": ScanType.IMAGE,
            "file_name": "test.jpg",
            "file_size": 1024,
            "extracted_texts": [],
            "detected_books": [],
            "processing_time_ms": 500,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }]
        
        response = client.get(
            "/api/v1/scan/result/scan_123",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "scan_123"
        assert data["status"] == ScanStatus.COMPLETED
    
    @pytest.mark.asyncio
    @patch('app.db.supabase.supabase_ops.get_user_scans', new_callable=AsyncMock)
    async def test_get_scan_result_not_found(self, mock_db, client):
        """Test scan result not found"""
        mock_db.return_value = []
        
        response = client.get(
            "/api/v1/scan/result/nonexistent",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 404


class TestScanHistory:
    """Tests for scan history endpoint"""
    
    @pytest.mark.asyncio
    @patch('app.db.supabase.supabase_ops.get_user_scans', new_callable=AsyncMock)
    async def test_get_scan_history(self, mock_db, client):
        """Test retrieving scan history"""
        mock_db.return_value = [
            {
                "id": f"scan_{i}",
                "user_id": "test_user_123",
                "status": ScanStatus.COMPLETED,
                "scan_type": ScanType.IMAGE,
                "file_name": f"test{i}.jpg",
                "file_size": 1024,
                "extracted_texts": [],
                "detected_books": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            for i in range(5)
        ]
        
        response = client.get(
            "/api/v1/scan/history?page=1&page_size=10",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scans" in data
        assert len(data["scans"]) == 5
        assert data["page"] == 1


class TestOCRService:
    """Tests for OCR service"""
    
    @pytest.mark.asyncio
    async def test_extract_text_from_image(self):
        """Test text extraction from image"""
        
        # Create test image
        img = Image.new('RGB', (200, 100), color='white')
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img.save(f, format='JPEG')
            temp_path = f.name
        
        # Extract text
        results = await ocr_service.extract_text_from_image(temp_path)
        
        assert isinstance(results, list)
        # Note: Actual text detection depends on image content
    
    @pytest.mark.asyncio
    async def test_extract_isbn(self):
        """Test ISBN extraction from text"""
        from app.services.ocr_service import ocr_service
        
        text = "This book's ISBN is ISBN-13: 978-0-123456-78-9"
        isbn = ocr_service._extract_isbn(text)
        
        assert isbn == "9780123456789"
    
    def test_get_confidence_level(self):
        """Test confidence level categorization"""
        from app.services.ocr_service import ocr_service
        
        assert ocr_service._get_confidence_level(95.0) == OCRConfidence.HIGH
        assert ocr_service._get_confidence_level(80.0) == OCRConfidence.MEDIUM
        assert ocr_service._get_confidence_level(60.0) == OCRConfidence.LOW


class TestRateLimiting:
    """Tests for rate limiting"""
    
    def test_rate_limit_exceeded(self, client, sample_image_file):
        """Test rate limiting on upload endpoint"""
        # Make multiple requests rapidly
        for i in range(65):  # Exceed 60/min limit
            response = client.post(
                "/api/v1/scan/upload",
                files={"file": sample_image_file},
                headers={"Authorization": "Bearer test_token"}
            )
            
            if i >= 60:
                assert response.status_code == 429  # Too Many Requests
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])