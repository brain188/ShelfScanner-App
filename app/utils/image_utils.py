"""
Image processing utilities for OCR preprocessing.
"""
import cv2
import numpy as np
from typing import Tuple


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for better OCR results.
    
    Args:
        image: Input image array
    
    Returns:
        Preprocessed image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Noise removal
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Binarization using adaptive thresholding
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    
    # Dilation and erosion to remove noise
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return processed


def detect_orientation(image: np.ndarray) -> int:
    """
    Detect image orientation for correction.
    
    Args:
        image: Input image array
    
    Returns:
        Rotation angle (0, 90, 180, 270)
    """
    # Simple heuristic based on edge detection
    edges = cv2.Canny(image, 50, 150)
    
    # Count horizontal and vertical edges
    horizontal_edges = np.sum(edges, axis=1)
    vertical_edges = np.sum(edges, axis=0)
    
    h_score = np.max(horizontal_edges)
    v_score = np.max(vertical_edges)
    
    # If vertical edges dominate, might need rotation
    if v_score > h_score * 1.5:
        return 90
    
    return 0


def resize_image(
    image: np.ndarray,
    max_size: Tuple[int, int] = (1920, 1080)
) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: Input image
        max_size: Maximum dimensions (width, height)
    
    Returns:
        Resized image
    """
    h, w = image.shape[:2]
    max_w, max_h = max_size
    
    # Calculate scaling factor
    scale = min(max_w / w, max_h / h, 1.0)
    
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return image


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE.
    
    Args:
        image: Input image
    
    Returns:
        Enhanced image
    """
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        enhanced = cv2.merge((cl, a, b))
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)


def remove_shadows(image: np.ndarray) -> np.ndarray:
    """
    Remove shadows from image.
    
    Args:
        image: Input image
    
    Returns:
        Shadow-removed image
    """
    rgb_planes = cv2.split(image)
    
    result_planes = []
    for plane in rgb_planes:
        dilated = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg = cv2.medianBlur(dilated, 21)
        diff = 255 - cv2.absdiff(plane, bg)
        result_planes.append(diff)
    
    return cv2.merge(result_planes)


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew rotated image.
    
    Args:
        image: Input image
    
    Returns:
        Deskewed image
    """
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    return rotated