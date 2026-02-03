"""
OCR service for text extraction from images and PDFs.
Implements asynchronous processing with error handling and confidence scoring.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.logging import get_logger
from app.models.scan_result import ExtractedText, OCRConfidence
from app.utils.image_utils import preprocess_image, detect_orientation

logger = get_logger(__name__)


class OCRService:
    """
    OCR service for extracting text from images and PDFs.
    Implements preprocessing, text extraction, and confidence scoring.
    """
    
    def __init__(self):
        """Initialize OCR service"""
        self.tesseract_path = settings.tesseract_path
        self.ocr_lang = settings.ocr_lang
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Set Tesseract path
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        logger.info("OCR service initialized", language=self.ocr_lang)
    
    async def extract_text_from_image(
        self,
        image_path: str,
        preprocess: bool = True
    ) -> List[ExtractedText]:
        """
        Extract text from a single image.
        
        Args:
            image_path: Path to image file
            preprocess: Whether to apply preprocessing
        
        Returns:
            List of extracted text blocks
        """
        try:
            logger.info("Starting OCR extraction", image_path=image_path)
            
            # Load image
            image = Image.open(image_path)
            
            # Preprocess if enabled
            if preprocess:
                image = await self._preprocess_image(image)
            
            # Run OCR in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            ocr_data = await loop.run_in_executor(
                self.executor,
                self._run_tesseract,
                image
            )
            
            # Parse OCR results
            extracted_texts = self._parse_ocr_data(ocr_data)
            
            logger.info(
                "OCR extraction completed",
                image_path=image_path,
                blocks_found=len(extracted_texts)
            )
            
            return extracted_texts
            
        except Exception as e:
            logger.error("OCR extraction failed", image_path=image_path, error=str(e))
            raise
    
    async def extract_text_from_pdf(
        self,
        pdf_path: str,
        max_pages: int = 10
    ) -> List[List[ExtractedText]]:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process
        
        Returns:
            List of extracted text blocks per page
        """
        try:
            logger.info("Starting PDF OCR extraction", pdf_path=pdf_path)
            
            # Convert PDF to images
            loop = asyncio.get_event_loop()
            images = await loop.run_in_executor(
                self.executor,
                convert_from_path,
                pdf_path,
                dpi=300,
                first_page=1,
                last_page=max_pages
            )
            
            # Process each page
            results = []
            for idx, image in enumerate(images):
                logger.debug(f"Processing PDF page {idx + 1}/{len(images)}")
                
                # Preprocess
                processed_image = await self._preprocess_image(image)
                
                # Run OCR
                ocr_data = await loop.run_in_executor(
                    self.executor,
                    self._run_tesseract,
                    processed_image
                )
                
                # Parse results
                page_texts = self._parse_ocr_data(ocr_data)
                results.append(page_texts)
            
            logger.info(
                "PDF OCR extraction completed",
                pdf_path=pdf_path,
                pages_processed=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("PDF OCR extraction failed", pdf_path=pdf_path, error=str(e))
            raise
    
    def _run_tesseract(self, image: Image.Image) -> Dict[str, Any]:
        """
        Run Tesseract OCR on image.
        
        Args:
            image: PIL Image object
        
        Returns:
            OCR data dictionary
        """
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image,
                lang=self.ocr_lang,
                output_type=pytesseract.Output.DICT
            )
            return data
            
        except Exception as e:
            logger.error("Tesseract execution failed", error=str(e))
            raise
    
    async def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: Input PIL Image
        
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            # Apply preprocessing
            processed = preprocess_image(img_array)
            
            # Detect and correct orientation
            orientation = detect_orientation(processed)
            if orientation != 0:
                processed = self._rotate_image(processed, orientation)
                logger.debug("Image rotated", degrees=orientation)
            
            # Convert back to PIL Image
            return Image.fromarray(processed)
            
        except Exception as e:
            logger.warning("Image preprocessing failed, using original", error=str(e))
            return image
    
    def _rotate_image(self, image: np.ndarray, angle: int) -> np.ndarray:
        """
        Rotate image by specified angle.
        
        Args:
            image: Image array
            angle: Rotation angle in degrees
        
        Returns:
            Rotated image
        """
        if angle == 0:
            return image
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Calculate rotation matrix
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Perform rotation
        rotated = cv2.warpAffine(image, matrix, (width, height))
        
        return rotated
    
    def _parse_ocr_data(self, ocr_data: Dict[str, Any]) -> List[ExtractedText]:
        """
        Parse Tesseract OCR output into structured data.
        
        Args:
            ocr_data: Raw OCR data from Tesseract
        
        Returns:
            List of ExtractedText objects
        """
        extracted_texts = []
        
        n_boxes = len(ocr_data['text'])
        
        for i in range(n_boxes):
            # Skip empty text
            text = ocr_data['text'][i].strip()
            if not text:
                continue
            
            # Get confidence
            conf = float(ocr_data['conf'][i])
            if conf < 0:  # Tesseract returns -1 for no confidence
                continue
            
            # Get bounding box
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            
            bounding_box = {
                "x": x,
                "y": y,
                "width": w,
                "height": h
            }
            
            # Determine confidence level
            confidence_level = self._get_confidence_level(conf)
            
            extracted_text = ExtractedText(
                text=text,
                confidence=conf,
                confidence_level=confidence_level,
                bounding_box=bounding_box
            )
            
            extracted_texts.append(extracted_text)
        
        return extracted_texts
    
    def _get_confidence_level(self, confidence: float) -> OCRConfidence:
        """
        Categorize confidence score.
        
        Args:
            confidence: Confidence score (0-100)
        
        Returns:
            OCRConfidence category
        """
        if confidence >= 90:
            return OCRConfidence.HIGH
        elif confidence >= 70:
            return OCRConfidence.MEDIUM
        else:
            return OCRConfidence.LOW
    
    async def extract_book_metadata(
        self,
        extracted_texts: List[ExtractedText]
    ) -> Dict[str, Any]:
        """
        Extract book metadata from OCR text.
        Attempts to identify title, author, ISBN from extracted text.
        
        Args:
            extracted_texts: List of extracted text blocks
        
        Returns:
            Dictionary with potential book metadata
        """
        try:
            # Combine all high-confidence text
            high_conf_texts = [
                et.text for et in extracted_texts
                if et.confidence_level == OCRConfidence.HIGH
            ]
            
            combined_text = " ".join(high_conf_texts)
            
            # Extract potential metadata
            metadata = {
                "full_text": combined_text,
                "isbn": self._extract_isbn(combined_text),
                "potential_titles": self._extract_potential_titles(high_conf_texts),
                "potential_authors": self._extract_potential_authors(combined_text)
            }
            
            return metadata
            
        except Exception as e:
            logger.error("Failed to extract book metadata", error=str(e))
            return {}
    
    def _extract_isbn(self, text: str) -> Optional[str]:
        """
        Extract ISBN from text using regex patterns.
        
        Args:
            text: Text to search
        
        Returns:
            ISBN if found, None otherwise
        """
        import re
        
        # ISBN-13 pattern
        isbn13_pattern = r'ISBN(?:-13)?:?\s*(\d{3}-?\d{1,5}-?\d{1,7}-?\d{1,7}-?\d{1})'
        
        # ISBN-10 pattern
        isbn10_pattern = r'ISBN(?:-10)?:?\s*(\d{1,5}-?\d{1,7}-?\d{1,7}-?[\dX])'
        
        # Try ISBN-13 first
        match = re.search(isbn13_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace('-', '')
        
        # Try ISBN-10
        match = re.search(isbn10_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace('-', '')
        
        return None
    
    def _extract_potential_titles(self, text_blocks: List[str]) -> List[str]:
        """
        Extract potential book titles from text blocks.
        Uses heuristics like capitalization and position.
        
        Args:
            text_blocks: List of text blocks
        
        Returns:
            List of potential titles
        """
        potential_titles = []
        
        for block in text_blocks[:5]:  # Check first 5 blocks
            # Look for title case text
            if block.istitle() and len(block.split()) >= 2:
                potential_titles.append(block)
            # Look for all caps (common for titles)
            elif block.isupper() and 3 <= len(block.split()) <= 10:
                potential_titles.append(block.title())
        
        return potential_titles[:3]  # Return top 3
    
    def _extract_potential_authors(self, text: str) -> List[str]:
        """
        Extract potential author names from text.
        
        Args:
            text: Text to search
        
        Returns:
            List of potential author names
        """
        import re
        
        # Pattern for "by Author Name"
        by_pattern = r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})'
        
        matches = re.findall(by_pattern, text)
        return matches[:3]  # Return up to 3 potential authors
    
    async def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        logger.info("OCR service cleaned up")


# Global instance
ocr_service = OCRService()

__all__ = ["OCRService", "ocr_service"]