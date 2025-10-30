"""
Agent-to-Agent Communication Protocol
====================================
Defines the communication interfaces and message formats for A2A architecture.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid
import json


class MessageType(Enum):
    """Types of messages that can be sent between agents."""
    QUERY_UNDERSTANDING_REQUEST = "query_understanding_request"
    QUERY_UNDERSTANDING_RESPONSE = "query_understanding_response"
    SEARCH_REQUEST = "search_request"
    SEARCH_RESPONSE = "search_response"
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"
    RESPONSE_REQUEST = "response_request"
    RESPONSE_RESPONSE = "response_response"
    SOURCE_LINKING_REQUEST = "source_linking_request"
    SOURCE_LINKING_RESPONSE = "source_linking_response"
    CATEGORIZATION_REQUEST = "categorization_request"
    CATEGORIZATION_RESPONSE = "categorization_response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    COORDINATION = "coordination"


class AgentType(Enum):
    """Types of agents in the system."""
    QUERY_UNDERSTANDER = "query_understander"
    HYBRID_SEARCH_AGENT = "hybrid_search_agent"
    ANSWER_GENERATION_AGENT = "answer_generation_agent"
    SOURCE_LINKING_AGENT = "source_linking_agent"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentMessage:
    """Standard message format for agent-to-agent communication."""
    id: str
    sender: AgentType
    recipient: AgentType
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 1  # 1=low, 5=high
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['sender'] = self.sender.value
        data['recipient'] = self.recipient.value
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['sender'] = AgentType(data['sender'])
        data['recipient'] = AgentType(data['recipient'])
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Deserialize message from JSON."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class SearchRequest:
    """Payload for search requests."""
    query: str
    normalized_query: Optional[str] = None
    expanded_keywords: Optional[List[str]] = None
    is_broad_subject: Optional[bool] = None
    max_results: int = 100
    search_filters: Optional[Dict[str, Any]] = None
    # Additional fields for different agent types
    documents: Optional[List[Dict[str, Any]]] = None
    search_results: Optional[List[Dict[str, Any]]] = None


@dataclass
class SearchResponse:
    """Payload for search responses."""
    results: List[Dict[str, Any]]
    total_found: int
    search_time: float
    sources_used: List[str]  # e.g., ["database", "google_drive"]


@dataclass
class AnalysisRequest:
    """Payload for analysis requests."""
    documents: List[Dict[str, Any]]
    query: str
    analysis_type: str  # "content", "relevance", "categorization"
    context: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResponse:
    """Payload for analysis responses."""
    analysis: Dict[str, Any]
    confidence_score: float
    insights: List[str]
    recommendations: List[str]


@dataclass
class ResponseRequest:
    """Payload for response generation requests."""
    query: str
    search_results: List[Dict[str, Any]]
    analysis: Optional[Dict[str, Any]] = None
    response_type: str = "comprehensive"  # "brief", "comprehensive", "detailed"


@dataclass
class ResponseResponse:
    """Payload for response generation responses."""
    answer: str
    sources: List[Dict[str, Any]]
    grouped_sources: Optional[Dict[str, Any]] = None
    confidence: float = 1.0


@dataclass
class CategorizationRequest:
    """Payload for categorization requests."""
    documents: List[Dict[str, Any]]
    categorization_type: str = "smart"  # "smart", "simple", "custom"


@dataclass
class CategorizationResponse:
    """Payload for categorization responses."""
    categories: Dict[str, List[Dict[str, Any]]]
    category_metadata: Dict[str, Dict[str, Any]]


@dataclass
class QueryUnderstandingRequest:
    """Payload for query understanding requests."""
    query: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class QueryUnderstandingResponse:
    """Payload for query understanding responses."""
    normalized_query: str
    expanded_keywords: List[str]
    is_broad_subject: bool
    intent: str
    confidence: float
    processing_time: float


@dataclass
class SourceLinkingRequest:
    """Payload for source linking requests."""
    documents: List[Dict[str, Any]]
    query: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class SourceLinkingResponse:
    """Payload for source linking responses."""
    sources: List[Dict[str, Any]]
    grouped_sources: Dict[str, List[Dict[str, Any]]]
    source_categories: List[Dict[str, Any]]
    processing_time: float


class AgentCommunicationError(Exception):
    """Exception raised for agent communication errors."""
    pass


class MessageTimeoutError(AgentCommunicationError):
    """Exception raised when message times out."""
    pass


class AgentUnavailableError(AgentCommunicationError):
    """Exception raised when target agent is unavailable."""
    pass


def create_message(
    sender: AgentType,
    recipient: AgentType,
    message_type: MessageType,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
    priority: int = 1
) -> AgentMessage:
    """Helper function to create agent messages."""
    return AgentMessage(
        id=str(uuid.uuid4()),
        sender=sender,
        recipient=recipient,
        message_type=message_type,
        payload=payload,
        timestamp=datetime.now(),
        correlation_id=correlation_id,
        priority=priority
    )


def create_search_request(
    query: str,
    normalized_query: str,
    expanded_keywords: List[str],
    is_broad_subject: bool,
    max_results: int = 100
) -> AgentMessage:
    """Create a search request message."""
    payload = SearchRequest(
        query=query,
        normalized_query=normalized_query,
        expanded_keywords=expanded_keywords,
        is_broad_subject=is_broad_subject,
        max_results=max_results
    )
    return create_message(
        sender=AgentType.ORCHESTRATOR,
        recipient=AgentType.HYBRID_SEARCH_AGENT,
        message_type=MessageType.SEARCH_REQUEST,
        payload=asdict(payload)
    )


def create_analysis_request(
    documents: List[Dict[str, Any]],
    query: str,
    analysis_type: str = "content"
) -> AgentMessage:
    """Create an analysis request message."""
    payload = AnalysisRequest(
        documents=documents,
        query=query,
        analysis_type=analysis_type
    )
    return create_message(
        sender=AgentType.ORCHESTRATOR,
        recipient=AgentType.QUERY_UNDERSTANDER,
        message_type=MessageType.ANALYSIS_REQUEST,
        payload=asdict(payload)
    )


def create_response_request(
    query: str,
    search_results: List[Dict[str, Any]],
    analysis: Optional[Dict[str, Any]] = None
) -> AgentMessage:
    """Create a response generation request message."""
    payload = ResponseRequest(
        query=query,
        search_results=search_results,
        analysis=analysis
    )
    return create_message(
        sender=AgentType.ORCHESTRATOR,
        recipient=AgentType.ANSWER_GENERATION_AGENT,
        message_type=MessageType.RESPONSE_REQUEST,
        payload=asdict(payload)
    )


def create_categorization_request(
    documents: List[Dict[str, Any]],
    categorization_type: str = "smart"
) -> AgentMessage:
    """Create a categorization request message."""
    payload = CategorizationRequest(
        documents=documents,
        categorization_type=categorization_type
    )
    return create_message(
        sender=AgentType.ORCHESTRATOR,
        recipient=AgentType.SOURCE_LINKING_AGENT,
        message_type=MessageType.CATEGORIZATION_REQUEST,
        payload=asdict(payload)
    )
