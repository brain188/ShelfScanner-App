"""
Text cleaning and normalization utilities.
"""
import re
from typing import List, Optional


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?;:\'-]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_isbn(isbn: str) -> Optional[str]:
    """
    Normalize ISBN by removing dashes and validating format.
    
    Args:
        isbn: ISBN string
    
    Returns:
        Normalized ISBN or None if invalid
    """
    # Remove all non-digit characters except X
    normalized = re.sub(r'[^\dX]', '', isbn.upper())
    
    # Validate length
    if len(normalized) == 10 or len(normalized) == 13:
        return normalized
    
    return None


def extract_title_from_text(text: str) -> Optional[str]:
    """
    Extract potential book title from text.
    
    Args:
        text: Text containing potential title
    
    Returns:
        Extracted title or None
    """
    # Look for title patterns
    lines = text.split('\n')
    
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        
        # Skip very short or very long lines
        if len(line) < 3 or len(line) > 100:
            continue
        
        # Look for title case or all caps
        if line.istitle() or (line.isupper() and len(line.split()) >= 2):
            return clean_text(line)
    
    return None


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into words.
    
    Args:
        text: Input text
    
    Returns:
        List of tokens
    """
    # Convert to lowercase and split
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def remove_stopwords(tokens: List[str], language: str = 'english') -> List[str]:
    """
    Remove common stopwords from tokens.
    
    Args:
        tokens: List of tokens
        language: Language for stopwords
    
    Returns:
        Filtered tokens
    """
    # Basic English stopwords
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
        'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
        'are', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did'
    }
    
    return [token for token in tokens if token not in stopwords]


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score (0-1)
    """
    tokens1 = set(tokenize_text(text1))
    tokens2 = set(tokenize_text(text2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union)