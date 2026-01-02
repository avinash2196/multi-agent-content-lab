import pytest
from src.utils.text_processor import TextProcessor


def test_clean_text():
    """Test text cleaning."""
    processor = TextProcessor()
    
    text = "  This   has   extra    spaces  "
    cleaned = processor.clean_text(text)
    
    assert cleaned == "This has extra spaces"


def test_word_count():
    """Test word counting."""
    processor = TextProcessor()
    
    text = "This is a test sentence with eight words"
    count = processor.count_words(text)
    
    assert count == 8


def test_slug_generation():
    """Test URL slug generation."""
    processor = TextProcessor()
    
    text = "This is My Test Article!"
    slug = processor.generate_slug(text)
    
    assert slug == "this-is-my-test-article"


def test_readability_score():
    """Test readability scoring."""
    processor = TextProcessor()
    
    text = "This is a simple sentence. It is easy to read."
    score = processor.calculate_readability_score(text)
    
    assert 0 <= score <= 100
