"""
Base Agent Class
===============
Base class for all agents in the A2A architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
import asyncio
import logging
from datetime import datetime, timedelta
import uuid

from .protocol.agent_communication import (
    AgentMessage, MessageType, AgentType, 
    AgentCommunicationError, MessageTimeoutError, AgentUnavailableError
)


class BaseAgent(ABC):
    """Base class for all agents in the A2A system."""
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        max_concurrent_tasks: int = 10,
        timeout_seconds: int = 30
    ):
        self.agent_type = agent_type
        self.name = name
        self.max_concurrent_tasks = max_concurrent_tasks
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"agent.{name}")
        self.is_running = False
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_messages: Dict[str, asyncio.Future] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
    async def start(self) -> None:
        """Start the agent."""
        self.logger.info(f"Starting agent {self.name}")
        self.is_running = True
        
        # Start message processing loop
        asyncio.create_task(self._message_processing_loop())
        
        # Start heartbeat
        asyncio.create_task(self._heartbeat_loop())
        
        self.logger.info(f"Agent {self.name} started successfully")
    
    async def stop(self) -> None:
        """Stop the agent."""
        self.logger.info(f"Stopping agent {self.name}")
        self.is_running = False
        
        # Cancel all pending messages
        for future in self.pending_messages.values():
            if not future.done():
                future.cancel()
        
        self.logger.info(f"Agent {self.name} stopped")
    
    async def send_message(
        self,
        recipient: AgentType,
        message_type: MessageType,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        priority: int = 1,
        timeout: Optional[int] = None
    ) -> AgentMessage:
        """Send a message to another agent and wait for response."""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_type,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            priority=priority
        )
        
        # Create future for response
        response_future = asyncio.Future()
        self.pending_messages[message.id] = response_future
        
        try:
            # Send message (this would be implemented by the orchestrator)
            await self._send_message_to_orchestrator(message)
            
            # Wait for response
            timeout = timeout or self.timeout_seconds
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            self.pending_messages.pop(message.id, None)
            raise MessageTimeoutError(f"Message {message.id} timed out after {timeout} seconds")
        except Exception as e:
            self.pending_messages.pop(message.id, None)
            raise AgentCommunicationError(f"Failed to send message: {e}")
    
    async def receive_message(self, message: AgentMessage) -> None:
        """Receive a message from another agent."""
        self.logger.debug(f"Received message {message.id} from {message.sender.value}")
        
        # Check if this is a response to a pending message
        if message.correlation_id and message.correlation_id in self.pending_messages:
            future = self.pending_messages.pop(message.correlation_id)
            if not future.done():
                future.set_result(message)
            return
        
        # Handle the message
        await self._handle_message(message)
    
    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages."""
        try:
            # Get handler for message type
            handler = self.message_handlers.get(message.message_type)
            if not handler:
                self.logger.warning(f"No handler for message type {message.message_type.value}")
                return
            
            # Process message with semaphore to limit concurrency
            async with self.task_semaphore:
                await handler(message)
                
        except Exception as e:
            self.logger.error(f"Error handling message {message.id}: {e}")
            # Send error response
            await self._send_error_response(message, str(e))
    
    async def _message_processing_loop(self) -> None:
        """Main message processing loop."""
        while self.is_running:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                if self.is_running:
                    await self._send_heartbeat()
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
    
    async def _send_heartbeat(self) -> None:
        """Send heartbeat message."""
        heartbeat = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_type,
            recipient=AgentType.ORCHESTRATOR,
            message_type=MessageType.HEARTBEAT,
            payload={"status": "healthy", "timestamp": datetime.now().isoformat()},
            timestamp=datetime.now()
        )
        await self._send_message_to_orchestrator(heartbeat)
    
    async def _send_error_response(self, original_message: AgentMessage, error: str) -> None:
        """Send error response to original sender."""
        error_response = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_type,
            recipient=original_message.sender,
            message_type=MessageType.ERROR,
            payload={"error": error, "original_message_id": original_message.id},
            timestamp=datetime.now(),
            correlation_id=original_message.id
        )
        await self._send_message_to_orchestrator(error_response)
    
    @abstractmethod
    async def _send_message_to_orchestrator(self, message: AgentMessage) -> None:
        """Send message to orchestrator. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task. Must be implemented by subclasses."""
        pass
    
    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register a message handler."""
        self.message_handlers[message_type] = handler
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_type": self.agent_type.value,
            "name": self.name,
            "is_running": self.is_running,
            "pending_messages": len(self.pending_messages),
            "queue_size": self.message_queue.qsize(),
            "active_tasks": self.max_concurrent_tasks - self.task_semaphore._value
        }
