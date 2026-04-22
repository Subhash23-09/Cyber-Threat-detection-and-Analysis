from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class AgentFinding(BaseModel):
    title: str
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    mitre_technique: Optional[str] = None

class AgentResult(BaseModel):
    agent_name: str
    verdict: Literal["MALICIOUS", "BENIGN", "SUSPICIOUS"]
    confidence: float = 0.0
    findings: List[AgentFinding]
    raw_artifacts: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LLMAgentResult(BaseModel):
    """Simplified model for LLM structured output to avoid schema complexity issues."""
    verdict: Literal["MALICIOUS", "BENIGN", "SUSPICIOUS"]
    confidence: float = Field(..., description="Level of confidence in the verdict (0.0 to 1.0)")
    findings: List[AgentFinding]
    reasoning: str = Field(..., description="Concise explanation for the verdict and findings")

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    @abstractmethod
    async def analyze(self, signals: List[dict], context: dict) -> AgentResult:
        """
        Core logic to analyze specific signals.
        Must return an AgentResult Pydantic model.
        """
        pass
    
    def log_execution(self, message: str):
        print(f"[{datetime.now()}] [AGENT: {self.name}] {message}")

    def get_llm(self):
        from services.llm_service import LLMService
        return LLMService.get_llm()

    def get_structured_llm(self, schema: Any):
        """
        Returns an LLM configured to output a specific Pydantic schema.
        This leverages LangChain's native with_structured_output.
        """
        llm = self.get_llm()
        if not llm:
            return None
        return llm.with_structured_output(schema)
