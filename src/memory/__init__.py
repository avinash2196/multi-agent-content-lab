from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime
from pathlib import Path


class ConversationMemory:
    """Enhanced conversation memory with persistence and context management."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.logger = logging.getLogger("conversation_memory")
        self.storage_path = Path(storage_path) if storage_path else None
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_conversation(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new conversation session."""
        conversation = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": [],
            "context": {},
            "routing_history": [],
            "metadata": metadata or {}
        }
        
        self.conversations[session_id] = conversation
        self.logger.info(f"Created conversation: {session_id}")
        return conversation
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the conversation."""
        if session_id not in self.conversations:
            self.create_conversation(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[session_id]["messages"].append(message)
        self.conversations[session_id]["updated_at"] = datetime.now().isoformat()
        
        # Auto-save if storage configured
        if self.storage_path:
            self._save_conversation(session_id)
        
        self.logger.debug(f"Added {role} message to {session_id}")
    
    def get_messages(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        role_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation."""
        if session_id not in self.conversations:
            return []
        
        messages = self.conversations[session_id]["messages"]
        
        # Filter by role if specified
        if role_filter:
            messages = [m for m in messages if m["role"] == role_filter]
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_context_window(self, session_id: str, window_size: int = 5) -> str:
        """Get recent conversation context as formatted string."""
        messages = self.get_messages(session_id, limit=window_size)
        
        context_lines = []
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"][:200]  # Truncate long messages
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def set_context(self, session_id: str, key: str, value: Any) -> None:
        """Set a context value for the conversation."""
        if session_id not in self.conversations:
            self.create_conversation(session_id)
        
        self.conversations[session_id]["context"][key] = value
        self.conversations[session_id]["updated_at"] = datetime.now().isoformat()
        
        if self.storage_path:
            self._save_conversation(session_id)
    
    def get_context(self, session_id: str, key: Optional[str] = None) -> Any:
        """Get context value(s) from the conversation."""
        if session_id not in self.conversations:
            return None if key else {}
        
        context = self.conversations[session_id]["context"]
        
        if key:
            return context.get(key)
        return context
    
    def add_routing_event(self, session_id: str, from_agent: str, to_agent: str, reason: str) -> None:
        """Track routing decisions in conversation history."""
        if session_id not in self.conversations:
            self.create_conversation(session_id)
        
        routing_event = {
            "timestamp": datetime.now().isoformat(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "reason": reason
        }
        
        self.conversations[session_id]["routing_history"].append(routing_event)
    
    def get_routing_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get routing history for a conversation."""
        if session_id not in self.conversations:
            return []
        
        return self.conversations[session_id].get("routing_history", [])
    
    def clear_conversation(self, session_id: str) -> None:
        """Clear a conversation from memory."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            
            # Delete saved file if exists
            if self.storage_path:
                file_path = self.storage_path / f"{session_id}.json"
                if file_path.exists():
                    file_path.unlink()
            
            self.logger.info(f"Cleared conversation: {session_id}")
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        if session_id not in self.conversations:
            return {}
        
        conv = self.conversations[session_id]
        messages = conv["messages"]
        
        return {
            "session_id": session_id,
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"],
            "message_count": len(messages),
            "user_messages": len([m for m in messages if m["role"] == "user"]),
            "assistant_messages": len([m for m in messages if m["role"] == "assistant"]),
            "routing_events": len(conv.get("routing_history", [])),
            "current_topic": conv["context"].get("topic", "N/A"),
            "last_intent": conv["context"].get("last_intent", "N/A")
        }
    
    def _save_conversation(self, session_id: str) -> None:
        """Save conversation to disk."""
        if not self.storage_path or session_id not in self.conversations:
            return
        
        file_path = self.storage_path / f"{session_id}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversations[session_id], f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save conversation {session_id}: {e}")
    
    def load_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation from disk."""
        if not self.storage_path:
            return None
        
        file_path = self.storage_path / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
                self.conversations[session_id] = conversation
                self.logger.info(f"Loaded conversation: {session_id}")
                return conversation
        except Exception as e:
            self.logger.error(f"Failed to load conversation {session_id}: {e}")
            return None
    
    def list_conversations(self) -> List[str]:
        """List all active conversation IDs."""
        return list(self.conversations.keys())
