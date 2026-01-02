"""Tests for State Manager"""
from src.graph.state_manager import StateManager


def test_state_manager_create_session():
    """Test creating a new session."""
    manager = StateManager()
    session_id = "test-123"
    
    session = manager.create_session(session_id)
    
    assert session is not None
    assert session["session_id"] == session_id
    assert "created_at" in session
    assert "messages" in session
    assert isinstance(session["messages"], list)


def test_state_manager_get_session():
    """Test retrieving a session."""
    manager = StateManager()
    session_id = "test-456"
    
    # Create first
    manager.create_session(session_id)
    
    # Then retrieve
    session = manager.get_session(session_id)
    
    assert session is not None
    assert session["session_id"] == session_id


def test_state_manager_update_context():
    """Test updating session context."""
    manager = StateManager()
    session_id = "test-789"
    
    manager.create_session(session_id)
    manager.update_session(session_id, {"context": {"topic": "AI"}})
    
    session = manager.get_session(session_id)
    assert session["context"]["topic"] == "AI"


def test_state_manager_add_message():
    """Test adding messages to session."""
    manager = StateManager()
    session_id = "test-msg"
    
    manager.create_session(session_id)
    manager.add_message(session_id, "user", "Hello")
    
    session = manager.get_session(session_id)
    assert len(session["messages"]) == 1
    assert session["messages"][0]["content"] == "Hello"
