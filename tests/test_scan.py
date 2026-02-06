"""
Tests for scan endpoints and OCR functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.main import app
from app.models.scan_result import ScanStatus, ScanType, OCRConfidence, ExtractedText

client = TestClient(app)


@pytest.fixture
def mock_auth_token():
    """Mock authentication token"""
    return "Bearer test_token"


@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "role": "user"
    }


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
    
    @patch('app.api.v1.scan.get_current_active_user')
    @patch('app.services.ocr_service.ocr_service.extract_text_from_image')
    async def test_upload_image_success(
        self,
        mock_ocr,
        mock_auth,
        sample_image_file,
        mock_user
    ):
        """Test successful image upload"""
        mock_auth.return_value = mock_user
        mock_ocr.return_value = [
            ExtractedText(
                text="Test Book Title",
                confidence=95.0,
                confidence_level=OCRConfidence.HIGH,
                bounding_box={"x": 0, "y": 0, "width": 100, "height": 50}
            )
        ]
        
        response = client.post(
            "/api/v1/scan/upload",
            files={"file": sample_image_file},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert data["status"] in [ScanStatus.PENDING, ScanStatus.PROCESSING]
    
    @patch('app.api.v1.scan.get_current_active_user')
    def test_upload_invalid_file_type(self, mock_auth, mock_user):
        """Test upload with invalid file type"""
        mock_auth.return_value = mock_user
        
        response = client.post(
            "/api/v1/scan/upload",
            files={"file": ("test.txt", b"test content", "text/plain")},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
    
    @patch('app.api.v1.scan.get_current_active_user')
    def test_upload_file_too_large(self, mock_auth, mock_user):
        """Test upload with file exceeding size limit"""
        mock_auth.return_value = mock_user
        
        # Create large file (> 10MB)
        large_content = b"x" * (11 * 1024 * 1024)
        
        response = client.post(
            "/api/v1/scan/upload",
            files={"file": ("large.jpg", large_content, "image/jpeg")},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()
    
    def test_upload_unauthorized(self, sample_image_file):
        """Test upload without authentication"""
        response = client.post(
            "/api/v1/scan/upload",
            files={"file": sample_image_file}
        )
        
        assert response.status_code == 401


class TestScanResult:
    """Tests for scan result retrieval"""
    
    @patch('app.api.v1.scan.get_current_active_user')
    @patch('app.db.supabase.supabase_ops.get_user_scans')
    async def test_get_scan_result_success(self, mock_db, mock_auth, mock_user):
        """Test successful scan result retrieval"""
        mock_auth.return_value = mock_user
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
    
    @patch('app.api.v1.scan.get_current_active_user')
    @patch('app.db.supabase.supabase_ops.get_user_scans')
    async def test_get_scan_result_not_found(self, mock_db, mock_auth, mock_user):
        """Test scan result not found"""
        mock_auth.return_value = mock_user
        mock_db.return_value = []
        
        response = client.get(
            "/api/v1/scan/result/nonexistent",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 404


class TestScanHistory:
    """Tests for scan history endpoint"""
    
    @patch('app.api.v1.scan.get_current_active_user')
    @patch('app.db.supabase.supabase_ops.get_user_scans')
    async def test_get_scan_history(self, mock_db, mock_auth, mock_user):
        """Test retrieving scan history"""
        mock_auth.return_value = mock_user
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
        from app.services.ocr_service import ocr_service
        from PIL import Image
        import tempfile
        
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
        from app.models.scan_result import OCRConfidence
        
        assert ocr_service._get_confidence_level(95.0) == OCRConfidence.HIGH
        assert ocr_service._get_confidence_level(80.0) == OCRConfidence.MEDIUM
        assert ocr_service._get_confidence_level(60.0) == OCRConfidence.LOW


class TestRateLimiting:
    """Tests for rate limiting"""
    
    @patch('app.api.v1.scan.get_current_active_user')
    def test_rate_limit_exceeded(self, mock_auth, mock_user, sample_image_file):
        """Test rate limiting on upload endpoint"""
        mock_auth.return_value = mock_user
        
        # Make multiple requests rapidly
        for i in range(65):  # Exceed 60/min limit
            response = client.post(
                "/api/v1/scan/upload",
                files={"file": sample_image_file},
                headers={"Authorization": "Bearer test_token"}
            )
            
            if i > 60:
                assert response.status_code == 429  # Too Many Requests
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])