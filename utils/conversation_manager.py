"""
Conversation Manager Module
Purpose: Manage session state and conversation history for multi-turn chat
Enables context-aware responses across multiple questions

Features:
* Session creation and management
* Conversation history tracking  
* Session expiration (TTL)
* Context retrieval for multi-turn
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation sessions and history
    """
    
    def __init__(self, session_ttl_minutes: int = 60):
        """
        Initialize conversation manager
        
        Args:
            session_ttl_minutes (int): Session lifetime in minutes (default 60)
        """
        self.sessions = {}  # In-memory storage (upgrade to database later)
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        logger.info(f"Conversation manager initialized (TTL: {session_ttl_minutes} min)")
    
    def create_session(
        self,
        chart_data: str,
        chart_factors: Dict,
        niche: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Create new conversation session
        
        Args:
            chart_data (str): Raw chart data as text
            chart_factors (Dict): Parsed 30 chart factors
            niche (str): Niche/domain (e.g., "Love & Relationships")
            user_id (Optional[str]): User identifier for tracking
        
        Returns:
            str: New session ID
        """
        
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "chart_data": chart_data,
            "chart_factors": chart_factors,
            "niche": niche,
            "history": [],  # Conversation turns
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "question_count": 0,
            "metadata": {}
        }
        
        logger.info(f"Session created: {session_id} (Niche: {niche})")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session by ID
        
        Args:
            session_id (str): Session ID
        
        Returns:
            Optional[Dict]: Session data if exists, None otherwise
        """
        
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        session = self.sessions[session_id]
        
        # Check if expired
        if self._is_session_expired(session):
            logger.info(f"Session expired: {session_id}")
            del self.sessions[session_id]
            return None
        
        return session
    
    def _is_session_expired(self, session: Dict) -> bool:
        """Check if session has expired"""
        time_since_update = datetime.now() - session["updated_at"]
        return time_since_update > self.session_ttl
    
    def add_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add user question and assistant response to history
        
        Args:
            session_id (str): Session ID
            user_message (str): User question
            assistant_response (str): Assistant answer
            metadata (Optional[Dict]): Additional metadata (latency, confidence, etc)
        
        Returns:
            Dict: Exchange record
        """
        
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Cannot add exchange to missing session: {session_id}")
            return {}
        
        exchange = {
            "turn": len(session["history"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "assistant_response": assistant_response,
            "metadata": metadata or {}
        }
        
        session["history"].append(exchange)
        session["updated_at"] = datetime.now()
        session["question_count"] += 1
        
        logger.info(
            f"Exchange added to {session_id}. "
            f"Turn: {exchange['turn']}, "
            f"Latency: {metadata.get('latency_ms', 'N/A')}ms"
        )
        
        return exchange
    
    def get_conversation_context(
        self,
        session_id: str,
        max_turns: int = 5
    ) -> List[Dict]:
        """
        Get recent conversation history for context
        
        Args:
            session_id (str): Session ID
            max_turns (int): Maximum recent turns to include (default 5)
        
        Returns:
            List[Dict]: Recent exchanges
        """
        
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Return last N exchanges
        history = session["history"]
        return history[-max_turns:] if history else []
    
    def format_context_for_prompt(
        self,
        session_id: str,
        max_turns: int = 3
    ) -> str:
        """
        Format conversation history as text for LLM prompt
        
        Args:
            session_id (str): Session ID
            max_turns (int): Max recent turns
        
        Returns:
            str: Formatted context
        """
        
        history = self.get_conversation_context(session_id, max_turns)
        
        if not history:
            return "No previous conversation."
        
        context_text = "PREVIOUS CONVERSATION CONTEXT:\n"
        context_text += "=" * 60 + "\n"
        
        for exchange in history:
            context_text += f"\nTurn {exchange['turn']} (at {exchange['timestamp'][:19]}):\n"
            context_text += f"User: {exchange['user_message'][:100]}...\n"
            context_text += f"Assistant: {exchange['assistant_response'][:200]}...\n"
        
        return context_text
    
    def get_session_summary(self, session_id: str) -> Dict:
        """
        Get session summary statistics
        
        Args:
            session_id (str): Session ID
        
        Returns:
            Dict: Session summary
        """
        
        session = self.get_session(session_id)
        if not session:
            return {}
        
        exchanges = session["history"]
        
        summary = {
            "session_id": session_id,
            "niche": session["niche"],
            "created_at": session["created_at"].isoformat(),
            "updated_at": session["updated_at"].isoformat(),
            "question_count": session["question_count"],
            "exchange_count": len(exchanges),
            "total_user_tokens": sum(len(e["user_message"].split()) for e in exchanges),
            "total_assistant_tokens": sum(len(e["assistant_response"].split()) for e in exchanges),
            "exchanges": exchanges[-3:]  # Last 3 for review
        }
        
        return summary
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id (str): Session ID
        
        Returns:
            bool: True if deleted, False if not found
        """
        
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session deleted: {session_id}")
            return True
        
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            int: Number of sessions deleted
        """
        
        expired_ids = []
        
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            del self.sessions[session_id]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
        
        return len(expired_ids)


# Usage example
if __name__ == "__main__":
    manager = ConversationManager(session_ttl_minutes=60)
    
    # Create session
    session_id = manager.create_session(
        chart_data="Asc: Cancer...",
        chart_factors={"7th_lord": "Saturn"},
        niche="Love & Relationships",
        user_id="user123"
    )
    
    # Add first exchange
    manager.add_exchange(
        session_id=session_id,
        user_message="How will my spouse look?",
        assistant_response="Your spouse will have a mature appearance...",
        metadata={"latency_ms": 9200, "confidence": 0.84}
    )
    
    # Add second exchange
    manager.add_exchange(
        session_id=session_id,
        user_message="What about their personality?",
        assistant_response="The personality will be...",
        metadata={"latency_ms": 8100}
    )
    
    # Get context
    context = manager.format_context_for_prompt(session_id, max_turns=2)
    print(context)
    
    # Get summary
    summary = manager.get_session_summary(session_id)
    print(json.dumps(summary, indent=2, default=str))
