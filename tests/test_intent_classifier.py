import pytest
from src.utils import IntentClassifier, IntentType


def test_research_intent_detection():
    """Test research intent classification."""
    classifier = IntentClassifier()
    
    queries = [
        "Research artificial intelligence trends",
        "What is machine learning?",
        "Tell me about quantum computing"
    ]
    
    for query in queries:
        result = classifier.classify(query)
        assert result.intent == IntentType.RESEARCH
        assert result.confidence > 0.3


def test_blog_intent_detection():
    """Test blog writing intent classification."""
    classifier = IntentClassifier()
    
    queries = [
        "Write a blog post about AI",
        "Create an article on climate change",
        "Blog about productivity tips"
    ]
    
    for query in queries:
        result = classifier.classify(query)
        assert result.intent == IntentType.BLOG
        assert len(result.topic) > 0


def test_linkedin_intent_detection():
    """Test LinkedIn post intent classification."""
    classifier = IntentClassifier()
    
    queries = [
        "Create a LinkedIn post about leadership",
        "Write a professional post on innovation",
        "Share on LinkedIn about team building"
    ]
    
    for query in queries:
        result = classifier.classify(query)
        assert result.intent == IntentType.LINKEDIN


def test_image_intent_detection():
    """Test image generation intent classification."""
    classifier = IntentClassifier()
    
    queries = [
        "Generate an image of a futuristic city",
        "Create a picture of mountains",
        "Draw an illustration of data flow"
    ]
    
    for query in queries:
        result = classifier.classify(query)
        assert result.intent == IntentType.IMAGE


def test_multi_format_intent():
    """Test multi-format content intent."""
    classifier = IntentClassifier()
    
    result = classifier.classify("Create complete content package about AI including blog and LinkedIn")
    assert result.intent == IntentType.MULTI_FORMAT


def test_topic_extraction():
    """Test topic extraction from queries."""
    classifier = IntentClassifier()
    
    result = classifier.classify("Write a blog about artificial intelligence and machine learning")
    assert "artificial intelligence" in result.topic.lower() or "machine learning" in result.topic.lower()


def test_requirements_extraction():
    """Test requirement extraction."""
    classifier = IntentClassifier()
    
    result = classifier.classify("Write a short professional blog with SEO optimization")
    assert "short_form" in result.requirements
    assert "professional_tone" in result.requirements
    assert "seo_optimized" in result.requirements


def test_confidence_scoring():
    """Test confidence scoring."""
    classifier = IntentClassifier()
    
    # Clear query should have higher confidence
    result1 = classifier.classify("Write a blog post about AI")
    
    # Ambiguous query should have lower confidence
    result2 = classifier.classify("something about technology")
    
    assert result1.confidence >= result2.confidence
