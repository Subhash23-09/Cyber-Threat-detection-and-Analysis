from .base_agent import BaseAgent, AgentResult, AgentFinding
import json
from typing import List

class ExfiltrationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="EXFIL_AGENT", description="Detects unauthorized data transfer")

    async def analyze(self, signals: List[dict], context: dict) -> AgentResult:
        from config import AgentConfig
        import re
        
        self.log_execution("Monitoring Data Exfiltration and C2 Activity...")
        findings = []
        is_malicious = False
        max_confidence = 0.0
        
        # 1. Broaden Filter for New Rules (C2, DGA, Beaconing)
        exfil_signals = [
            s for s in signals 
            if s.get('mitre_id') in ['T1048', 'T1567', 'T1071', 'T1568', 'T1020'] 
            or any(k in s.get('event_type', '') for k in ['Exfiltration', 'Transfer', 'DNS', 'Network', 'C2'])
        ]
        
        for signal in exfil_signals:
            ctx = signal.get('context', {})
            raw_details = str(ctx).lower() + str(signal.get('details', '')).lower()
            
            # ------------------------------------------------------------------
            # Rule 1: Volume-Based Detection
            # Logic: Size > Threshold
            # ------------------------------------------------------------------
            size_mb = ctx.get('size_bytes', 0) / (1024 * 1024)
            if size_mb > AgentConfig.EXFIL_VOLUME_THRESHOLD_MB:
                findings.append(AgentFinding(
                    title="Anomalous Data Volume",
                    description=f"High outbound volume ({size_mb:.2f} MB) detected from {signal.get('source_ip')}.",
                    severity="HIGH",
                    mitre_technique="T1048"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.85)
                
            # ------------------------------------------------------------------
            # Rule 2: Sensitive File Detection
            # Logic: Filename keywords or extensions
            # ------------------------------------------------------------------
            filename = ctx.get('file_name', '')
            if any(kw in filename.lower() for kw in AgentConfig.EXFIL_SENSITIVE_KEYWORDS) or \
               any(filename.endswith(ext) for ext in AgentConfig.EXFIL_SENSITIVE_EXTENSIONS):
                findings.append(AgentFinding(
                     title="Sensitive File Transfer",
                     description=f"Potential exfiltration of sensitive file: {filename}",
                     severity="CRITICAL",
                     mitre_technique="T1020"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.95)

            # ------------------------------------------------------------------
            # Rule 3: Unusual Protocol Usage
            # Logic: Sensitive data over DNS/ICMP
            # ------------------------------------------------------------------
            protocol = ctx.get('protocol', 'tcp').lower()
            if protocol in AgentConfig.EXFIL_SUSPICIOUS_PROTOCOLS and size_mb > 1:
                findings.append(AgentFinding(
                    title="Exfiltration over Alternate Protocol",
                    description=f"Significant data transfer via {protocol.upper()} detected.",
                    severity="HIGH",
                    mitre_technique="T1048.003"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.9)

            # ------------------------------------------------------------------
            # Rule 4: C2 Beaconing Detection (Heuristic)
            # Logic: Regular intervals (Simplified check here, robust check needs state)
            # ------------------------------------------------------------------
            if "beacon" in raw_details or "heartbeat" in raw_details:
                findings.append(AgentFinding(
                    title="C2 Beaconing Detected",
                    description="Periodic communication pattern matching C2 heartbeat.",
                    severity="HIGH",
                    mitre_technique="T1071.001"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.80)

            # ------------------------------------------------------------------
            # Rule 5: DGA Detection
            # Logic: High Entropy Domains (Simplified check)
            # ------------------------------------------------------------------
            domain = ctx.get('domain', '')
            if len(domain) > 15 and re.search(r'[a-z0-9]{15,}', domain): # Naive entropy heuristic
                 findings.append(AgentFinding(
                    title="DGA Domain Detected",
                    description=f"High entropy domain query: {domain}",
                    severity="MEDIUM",
                    mitre_technique="T1568.002"
                ))
                 is_malicious = True
                 max_confidence = max(max_confidence, 0.75)
                 
            # ------------------------------------------------------------------
            # Rule 7: User Agent Anomalies
            # ------------------------------------------------------------------
            ua = ctx.get('user_agent', '').lower()
            if any(bad in ua for bad in AgentConfig.EXFIL_SUSPICIOUS_USER_AGENTS):
                findings.append(AgentFinding(
                    title="Suspicious User-Agent",
                    description=f"Scripting User-Agent detected: {ua}",
                    severity="LOW",
                    mitre_technique="T1071.001"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.6)

        return AgentResult(
            agent_name=self.name,
            verdict="MALICIOUS" if is_malicious else "BENIGN",
            confidence=max_confidence,
            findings=findings,
            raw_artifacts={"exfil_count": len(exfil_signals)}
        )
