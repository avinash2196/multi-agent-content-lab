import pytest
from src.memory import ConversationMemory
from pathlib import Path
import tempfile
import shutil


def test_conversation_creation():
    """Test creating a new conversation."""
    memory = ConversationMemory()
    
    conv = memory.create_conversation("test-123")
    
    assert conv["session_id"] == "test-123"
    assert "created_at" in conv
    assert len(conv["messages"]) == 0


def test_add_message():
    """Test adding messages to conversation."""
    memory = ConversationMemory()
    memory.create_conversation("test-456")
    
    memory.add_message("test-456", "user", "Hello!")
    memory.add_message("test-456", "assistant", "Hi there!")
    
    messages = memory.get_messages("test-456")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_context_management():
    """Test setting and getting context."""
    memory = ConversationMemory()
    memory.create_conversation("test-789")
    
    memory.set_context("test-789", "topic", "AI")
    memory.set_context("test-789", "intent", "research")
    
    topic = memory.get_context("test-789", "topic")
    all_context = memory.get_context("test-789")
    
    assert topic == "AI"
    assert all_context["intent"] == "research"


def test_routing_history():
    """Test routing history tracking."""
    memory = ConversationMemory()
    memory.create_conversation("test-routing")
    
    memory.add_routing_event("test-routing", "query_handler", "research_agent", "User requested research")
    memory.add_routing_event("test-routing", "research_agent", "blog_writer", "Research complete, generating blog")
    
    history = memory.get_routing_history("test-routing")
    
    assert len(history) == 2
    assert history[0]["from_agent"] == "query_handler"
    assert history[1]["to_agent"] == "blog_writer"


def test_conversation_summary():
    """Test conversation summary generation."""
    memory = ConversationMemory()
    memory.create_conversation("test-summary")
    
    memory.add_message("test-summary", "user", "Research AI")
    memory.add_message("test-summary", "assistant", "Starting research...")
    memory.set_context("test-summary", "topic", "AI")
    
    summary = memory.get_conversation_summary("test-summary")
    
    assert summary["message_count"] == 2
    assert summary["user_messages"] == 1
    assert summary["current_topic"] == "AI"


def test_context_window():
    """Test getting context window."""
    memory = ConversationMemory()
    memory.create_conversation("test-window")
    
    for i in range(10):
        memory.add_message("test-window", "user", f"Message {i}")
    
    window = memory.get_context_window("test-window", window_size=3)
    
    # Should contain only last 3 messages
    assert "Message 9" in window
    assert "Message 8" in window
    assert "Message 0" not in window


def test_persistence():
    """Test saving and loading conversations."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create memory with storage
        memory = ConversationMemory(storage_path=temp_dir)
        memory.create_conversation("test-persist")
        memory.add_message("test-persist", "user", "Test message")
        memory.set_context("test-persist", "topic", "Testing")
        
        # Create new memory instance and load
        memory2 = ConversationMemory(storage_path=temp_dir)
        loaded = memory2.load_conversation("test-persist")
        
        assert loaded is not None
        assert len(loaded["messages"]) == 1
        assert loaded["context"]["topic"] == "Testing"
        
    finally:
        shutil.rmtree(temp_dir)


def test_clear_conversation():
    """Test clearing a conversation."""
    memory = ConversationMemory()
    memory.create_conversation("test-clear")
    memory.add_message("test-clear", "user", "Message")
    
    memory.clear_conversation("test-clear")
    
    messages = memory.get_messages("test-clear")
    assert len(messages) == 0
