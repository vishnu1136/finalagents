from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import uuid


class A2AMessage(BaseModel):
    type: str = Field(default="agent_message")
    sender: str
    recipient: str
    payload: Dict[str, Any]
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class Citation(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None


class PipelineResult(BaseModel):
    answer: str
    sources: List[Citation] = []


