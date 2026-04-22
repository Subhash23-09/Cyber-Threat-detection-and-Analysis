from .base_agent import BaseAgent, AgentResult, AgentFinding
import json
from typing import List

class AuthAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AUTH_AGENT", description="Detects Brute Force and Auth Anomalies")
        
    async def analyze(self, signals: List[dict], context: dict) -> AgentResult:
        self.log_execution("Collaborating on Authentication Analysis...")
        
        findings = []
        is_malicious = False
        max_confidence = 0.0
        
        # 1. Filter relevant signals
        auth_signals = [
            s for s in signals 
            if s.get('mitre_id') in ['T1110', 'T1078'] 
            or 'Auth' in s.get('event_type', '') 
            or 'Brute Force' in s.get('event_type', '')
        ]
        
        # 2. Heuristic Pass (Deterministic)
        for signal in auth_signals:
            # Check metrics for event count
            attempts = signal.get('metrics', {}).get('failed_attempts', 0)
            if attempts > 5:
                # Extract location for finding description
                country = signal.get('context', {}).get('geoip', {}).get('country', 'Unknown')
                findings.append(AgentFinding(
                    title="High Auth Failure Count",
                    description=f"IP {signal.get('actor', {}).get('source_ip')} ({country}) exceeded failure threshold ({attempts} attempts).",
                    severity="HIGH",
                    mitre_technique="T1110.001"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.9)
        
        # 3. LLM Pass (Reasoning)
        from .base_agent import LLMAgentResult
        structured_llm = self.get_structured_llm(LLMAgentResult)
        if structured_llm and auth_signals:
            try:
                from langchain_core.prompts import ChatPromptTemplate
                
                # Truncate signals to last 3 to avoid payload bloat
                truncated_signals = auth_signals[-3:]
                # Simplify context
                simple_context = {
                    "short_term_count": len(context.get('short_term', {}).get('active_context', [])),
                    "long_term_count": len(context.get('long_term', {}).get('related_by_actor', []))
                }
                
                prompt = ChatPromptTemplate.from_template("""
                You are a specialized Cybersecurity Analyst: AUTH_AGENT.
                Analyze the following authentication signals and context.
                
                SIGNALS:
                {signals}
                
                CONTEXT_STATS:
                {context}
                
                Your task:
                1. Identify if this is MALICIOUS (brute force, credential stuffing), SUSPICIOUS (anomalous login), or BENIGN.
                2. Return the analysis in the specified structured format.
                
                CRITICAL: The 'verdict' MUST be one of: MALICIOUS, BENIGN, SUSPICIOUS.
                """)
                
                # Use structured LLM directly
                chain = prompt | structured_llm
                llm_result = await chain.ainvoke({
                    "signals": json.dumps(truncated_signals, default=str), 
                    "context": json.dumps(simple_context)
                })
                
                # Merge findings
                if llm_result:
                    findings.extend(llm_result.findings)
                    if llm_result.verdict == "MALICIOUS":
                        is_malicious = True
                    max_confidence = max(max_confidence, llm_result.confidence)
                
            except Exception as e:
                self.log_execution(f"LLM Reasoning failed: {e}")
                findings.append(AgentFinding(
                    title="LLM Analysis Error",
                    description=f"LangChain structured output failure: {str(e)}",
                    severity="LOW"
                ))
        # TODO: LangChain Refactor Tasks
        # [x] Research current agent implementations <!-- id: 0 -->
        # [x] Create implementation plan for LangChain refactor <!-- id: 1 -->
        # [x] Update `BaseAgent` with LangChain utilities (`with_structured_output`) <!-- id: 2 -->
        # [x] Refactor `AuthAgent` to use LangChain Patterns <!-- id: 3 -->

        return AgentResult(
            agent_name=self.name,
            verdict="MALICIOUS" if is_malicious else "BENIGN",
            confidence=max_confidence,
            findings=findings,
            raw_artifacts={"auth_signal_count": len(auth_signals)}
        )
