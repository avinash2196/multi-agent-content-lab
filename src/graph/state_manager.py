from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime


class StateManager:
    """Manages conversation state and memory across agent interactions."""
    
    def __init__(self):
        self.logger = logging.getLogger("state_manager")
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        """Create a new session with initial state."""
        initial_state = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "context": {},
            "history": [],
        }
        self.sessions[session_id] = initial_state
        self.logger.info(f"Created session: {session_id}")
        return initial_state
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session state."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update session state with new data."""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.sessions[session_id].update(updates)
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        
        self.logger.info(f"Updated session: {session_id}")
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session history."""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.sessions[session_id]["messages"].append(message)
        self.logger.debug(f"Added message to session {session_id}: {role}")
    
    def get_context(self, session_id: str, key: str) -> Optional[Any]:
        """Get a specific context value from session."""
        session = self.get_session(session_id)
        if session:
            return session.get("context", {}).get(key)
        return None
    
    def set_context(self, session_id: str, key: str, value: Any) -> None:
        """Set a context value in session."""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        if "context" not in self.sessions[session_id]:
            self.sessions[session_id]["context"] = {}
        
        self.sessions[session_id]["context"][key] = value
        self.logger.debug(f"Set context in session {session_id}: {key}")
    
    def clear_session(self, session_id: str) -> None:
        """Clear a session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Cleared session: {session_id}")
    
    def get_conversation_history(self, session_id: str, max_messages: int = 10) -> list:
        """Get recent conversation history."""
        session = self.get_session(session_id)
        if session and "messages" in session:
            return session["messages"][-max_messages:]
        return []
