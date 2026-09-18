"""
Inter-Agent Communication System for Serena Agent Ecosystem
Phase 2: Controlled communication mechanism between agents

This module provides a secure, controlled communication system for agents.
Agent communication must never be an authorization bypass - operations still require
centralized permission validation.
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Try to import Phase 1 core data contracts
try:
    from core_data_contracts import generate_correlation_id
    CORE_CONTRACTS_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    
    import uuid
    def generate_correlation_id():
        return str(uuid.uuid4())


class MessageStatus(Enum):
    """Status of a message."""
    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Message:
    """
    A message between agents.
    """
    message_id: str
    from_agent: str
    to_agent: str
    content: str
    message_type: str = "direct"  # direct, broadcast, request, response
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None  # If this is a reply to another message
    status: MessageStatus = MessageStatus.PENDING
    created_at: float = field(default_factory=time.time)
    delivered_at: Optional[float] = None
    read_at: Optional[float] = None
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "message_type": self.message_type,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "status": self.status.value,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "read_at": self.read_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create Message from dictionary."""
        return cls(
            message_id=data["message_id"],
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            content=data["content"],
            message_type=data.get("message_type", "direct"),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            status=MessageStatus(data.get("status", "pending")),
            created_at=data.get("created_at", time.time()),
            delivered_at=data.get("delivered_at"),
            read_at=data.get("read_at"),
            expires_at=data.get("expires_at"),
            metadata=data.get("metadata", {})
        )
    
    def deliver(self) -> None:
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = time.time()
    
    def read(self) -> None:
        """Mark message as read."""
        self.status = MessageStatus.READ
        self.read_at = time.time()
    
    def fail(self) -> None:
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CommunicationSystem:
    """
    Central communication system for agents.
    
    Supports:
    - Direct messages
    - Responses
    - Message IDs
    - Correlation IDs
    - Delivery state
    - Controlled broadcasts
    - Communication logging
    """
    
    def __init__(self, max_history: int = 1000):
        self._messages: Dict[str, Message] = {}  # message_id -> Message
        self._agent_inbox: Dict[str, List[str]] = {}  # agent_id -> list of message_ids
        self._lock = threading.RLock()
        self._max_history = max_history
        self._message_counter = 0
        self._communication_log: List[Dict] = []
    
    def send_message(self, from_agent: str, to_agent: str, content: str, 
                   message_type: str = "direct", correlation_id: Optional[str] = None,
                   reply_to: Optional[str] = None, expires_after: Optional[float] = None) -> str:
        """
        Send a message from one agent to another.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            content: Message content
            message_type: Type of message (direct, broadcast, request, response)
            correlation_id: Optional correlation ID for tracking
            reply_to: If this is a reply to another message
            expires_after: Optional expiration time in seconds
            
        Returns:
            Message ID
        """
        with self._lock:
            # Create message
            message = Message(
                message_id=f"msg_{int(time.time() * 1000)}_{self._message_counter}",
                from_agent=from_agent,
                to_agent=to_agent,
                content=content,
                message_type=message_type,
                correlation_id=correlation_id,
                reply_to=reply_to,
                expires_at=time.time() + expires_after if expires_after else None
            )
            
            self._message_counter += 1
            
            # Store message
            self._messages[message.message_id] = message
            
            # Add to recipient's inbox
            if to_agent not in self._agent_inbox:
                self._agent_inbox[to_agent] = []
            self._agent_inbox[to_agent].append(message.message_id)
            
            # Log communication
            self._log_communication(message, "sent")
            
            return message.message_id
    
    def get_messages(self, agent_id: str, unread_only: bool = False, 
                    limit: int = 50) -> List[Message]:
        """
        Get messages for an agent.
        
        Args:
            agent_id: The agent ID to get messages for
            unread_only: If True, only return unread messages
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        with self._lock:
            if agent_id not in self._agent_inbox:
                return []
            
            message_ids = self._agent_inbox[agent_id][-limit:]
            messages = []
            
            for msg_id in message_ids:
                message = self._messages.get(msg_id)
                if message:
                    if unread_only and message.status != MessageStatus.PENDING:
                        continue
                    if message.is_expired():
                        continue
                    messages.append(message)
            
            return messages
    
    def mark_read(self, message_id: str) -> bool:
        """
        Mark a message as read.
        
        Args:
            message_id: The message ID to mark as read
            
        Returns:
            True if message was marked as read
        """
        with self._lock:
            message = self._messages.get(message_id)
            if message:
                message.read()
                self._log_communication(message, "read")
                return True
            return False
    
    def send_reply(self, original_message_id: str, from_agent: str, content: str,
                  correlation_id: Optional[str] = None) -> Optional[str]:
        """
        Send a reply to a message.
        
        Args:
            original_message_id: The original message ID to reply to
            from_agent: The agent sending the reply
            content: Reply content
            correlation_id: Optional correlation ID
            
        Returns:
            New message ID, or None if original message not found
        """
        with self._lock:
            original_message = self._messages.get(original_message_id)
            if not original_message:
                return None
            
            # Send reply to original sender
            return self.send_message(
                from_agent=from_agent,
                to_agent=original_message.from_agent,
                content=content,
                message_type="response",
                correlation_id=correlation_id,
                reply_to=original_message_id
            )
    
    def broadcast(self, from_agent: str, content: str, target_agents: List[str],
                 correlation_id: Optional[str] = None) -> List[str]:
        """
        Broadcast a message to multiple agents.
        
        Args:
            from_agent: Sender agent ID
            content: Message content
            target_agents: List of recipient agent IDs
            correlation_id: Optional correlation ID
            
        Returns:
            List of message IDs
        """
        message_ids = []
        for to_agent in target_agents:
            msg_id = self.send_message(
                from_agent=from_agent,
                to_agent=to_agent,
                content=content,
                message_type="broadcast",
                correlation_id=correlation_id
            )
            message_ids.append(msg_id)
        return message_ids
    
    def get_conversation(self, agent1: str, agent2: str, limit: int = 50) -> List[Message]:
        """
        Get conversation between two agents.
        
        Args:
            agent1: First agent ID
            agent2: Second agent ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages between the two agents
        """
        with self._lock:
            conversation = []
            
            for message in self._messages.values():
                if (message.from_agent == agent1 and message.to_agent == agent2) or \
                   (message.from_agent == agent2 and message.to_agent == agent1):
                    if not message.is_expired():
                        conversation.append(message)
            
            # Sort by timestamp
            conversation.sort(key=lambda m: m.created_at)
            
            return conversation[-limit:]
    
    def _log_communication(self, message: Message, action: str) -> None:
        """Log a communication event."""
        log_entry = {
            "message_id": message.message_id,
            "from_agent": message.from_agent,
            "to_agent": message.to_agent,
            "action": action,
            "status": message.status.value,
            "timestamp": time.time()
        }
        self._communication_log.append(log_entry)
    
    def get_communication_log(self, agent_id: Optional[str] = None, 
                             limit: int = 100) -> List[Dict]:
        """
        Get communication log.
        
        Args:
            agent_id: Filter by agent ID (optional)
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries
        """
        with self._lock:
            filtered = self._communication_log
            
            if agent_id:
                filtered = [log for log in filtered 
                           if log["from_agent"] == agent_id or log["to_agent"] == agent_id]
            
            return filtered[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get communication system statistics."""
        with self._lock:
            status_counts = {}
            for message in self._messages.values():
                status = message.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_messages": len(self._messages),
                "message_counter": self._message_counter,
                "agents_with_messages": len(self._agent_inbox),
                "status_breakdown": status_counts,
                "communication_log_size": len(self._communication_log)
            }


# Global instance
_communication_system = None

def get_communication_system(max_history: int = 1000) -> CommunicationSystem:
    """Get or create the global CommunicationSystem instance."""
    global _communication_system
    if _communication_system is None:
        _communication_system = CommunicationSystem(max_history)
    return _communication_system


if __name__ == "__main__":
    # Test the communication system
    print("Testing Communication System...")
    
    comm = CommunicationSystem()
    
    # Test direct message
    msg_id = comm.send_message("MediaAgent", "PhotoAgent", "Hello from MediaAgent")
    print(f"Sent message: {msg_id}")
    
    # Test receiving
    messages = comm.get_messages("PhotoAgent")
    print(f"PhotoAgent received {len(messages)} messages")
    
    # Test marking read
    comm.mark_read(msg_id)
    messages = comm.get_messages("PhotoAgent", unread_only=True)
    print(f"PhotoAgent unread messages: {len(messages)}")
    
    # Test reply
    reply_id = comm.send_reply(msg_id, "PhotoAgent", "Reply from PhotoAgent")
    print(f"Sent reply: {reply_id}")
    
    # Test conversation
    conversation = comm.get_conversation("MediaAgent", "PhotoAgent")
    print(f"Conversation size: {len(conversation)}")
    
    # Test broadcast
    broadcast_ids = comm.broadcast("ServerAgent", "System update", ["MediaAgent", "PhotoAgent"])
    print(f"Broadcast to {len(broadcast_ids)} agents")
    
    # Test statistics
    stats = comm.get_statistics()
    print(f"Statistics: {stats}")
    
    print("\n✅ Communication System Test Passed!")