from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class LogEntry(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    raw_message: str
    metadata: Optional[Dict[str, Any]] = {}

class LogBatch(BaseModel):
    source_system: str = Field(..., description="Name of the source system (e.g., firewall-01)")
    source_type: str = Field(..., description="Type of source (e.g., syslog, filebeat, api)")
    logs: List[LogEntry]
