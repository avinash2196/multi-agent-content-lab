import re
from typing import List, Optional
import logging


class TextProcessor:
    """Utility class for text processing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("text_processor")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract potential keywords from text (simple implementation)."""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                     'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words and count frequency
        filtered_words = [w for w in words if w not in stop_words]
        
        # Simple frequency count
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]
    
    def truncate_text(self, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length - len(suffix)].rsplit(' ', 1)[0]
        return truncated + suffix
    
    def count_words(self, text: str) -> int:
        """Count words in text."""
        return len(re.findall(r'\b\w+\b', text))
    
    def estimate_reading_time(self, text: str, words_per_minute: int = 200) -> int:
        """Estimate reading time in minutes."""
        word_count = self.count_words(text)
        return max(1, round(word_count / words_per_minute))
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        return re.findall(r'#\w+', text)
    
    def generate_slug(self, text: str) -> str:
        """Generate URL-friendly slug from text."""
        # Convert to lowercase
        slug = text.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug
    
    def format_as_markdown_list(self, items: List[str], ordered: bool = False) -> str:
        """Format items as markdown list."""
        if ordered:
            return '\n'.join([f"{i+1}. {item}" for i, item in enumerate(items)])
        else:
            return '\n'.join([f"- {item}" for item in items])
    
    def extract_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def calculate_readability_score(self, text: str) -> float:
        """Calculate simple readability score (simplified Flesch Reading Ease)."""
        sentences = self.extract_sentences(text)
        if not sentences:
            return 0.0
        
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return 0.0
        
        # Count syllables (simplified - count vowel groups)
        syllable_count = sum(len(re.findall(r'[aeiou]+', word.lower())) for word in words)
        
        # Flesch Reading Ease formula (simplified)
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllable_count / len(words)
        
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        
        # Normalize to 0-100
        return max(0, min(100, score))
