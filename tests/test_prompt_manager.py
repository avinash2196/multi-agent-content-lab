import pytest
from src.utils.prompt_manager import PromptManager


def test_prompt_manager_initialization():
    """Test prompt manager loads default templates."""
    manager = PromptManager()
    
    templates = manager.list_templates()
    
    assert len(templates) > 0
    assert "query_classification" in templates
    assert "research_synthesis" in templates
    assert "blog_outline" in templates


def test_format_prompt():
    """Test prompt formatting with variables."""
    manager = PromptManager()
    
    formatted = manager.format_prompt(
        "query_classification",
        query="Write a blog about AI",
        context="None"
    )
    
    assert "Write a blog about AI" in formatted
    assert "intent" in formatted.lower()


def test_missing_variable_error():
    """Test error handling for missing variables."""
    manager = PromptManager()
    
    with pytest.raises(ValueError):
        manager.format_prompt("query_classification", query="Test")  # Missing 'context'
