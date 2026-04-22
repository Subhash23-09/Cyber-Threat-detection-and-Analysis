from .base_agent import BaseAgent, AgentResult, AgentFinding
from typing import List

class NetworkFloodAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DDOS_AGENT", description="Detects volumetric network anomalies")

    async def analyze(self, signals: List[dict], context: dict) -> AgentResult:
        from config import AgentConfig
        
        self.log_execution("Checking traffic volumes and Resource Exhaustion...")
        findings = []
        is_malicious = False
        max_confidence = 0.0
        
        # 1. Broaden Filter
        flood_signals = [
            s for s in signals 
            if s.get('mitre_id') in ['T1498', 'T1595', 'T1499', 'T1498.002'] 
            or any(k in s.get('event_type', '') for k in ['Volumetric', 'Flood', 'DoS', 'Resource', 'Traffic'])
        ]
        
        for signal in flood_signals:
            req_count = signal.get('metrics', {}).get('rate', 0)
            bandwidth = signal.get('metrics', {}).get('bandwidth_percent', 0)
            ctx = signal.get('context', {})
            details = str(ctx.get('details', '')).lower()
            
            # ------------------------------------------------------------------
            # Rule 1: Volumetric Attack Detection
            # Logic: Req rate > 10,000 OR Bandwidth > 80%
            # ------------------------------------------------------------------
            if req_count > AgentConfig.DDOS_RATE_LIMIT_RPS:
                 country = ctx.get('geoip', {}).get('country', 'Unknown')
                 findings.append(AgentFinding(
                     title="Massive Volumetric Flood",
                     description=f"Request rate critical ({req_count} reqs/sec) from {signal.get('actor', {}).get('source_ip')} ({country}).",
                     severity="CRITICAL",
                     mitre_technique="T1498"
                 ))
                 is_malicious = True
                 max_confidence = max(max_confidence, 0.99)
            
            if bandwidth > AgentConfig.DDOS_BANDWIDTH_THRESHOLD_PERCENT:
                findings.append(AgentFinding(
                    title="Network Bandwidth Saturation",
                    description=f"Bandwidth utilization at {bandwidth}% (Threshold: {AgentConfig.DDOS_BANDWIDTH_THRESHOLD_PERCENT}%).",
                    severity="HIGH",
                    mitre_technique="T1498"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.90)

            # ------------------------------------------------------------------
            # Rule 2: Application Layer Attack
            # Logic: Excessive POSTs or API spam
            # ------------------------------------------------------------------
            if "post" in details and "excessive" in details:
                 findings.append(AgentFinding(
                     title="Application Layer Flood (HTTP POST)",
                     description=f"Abnormal POST request volume detected against {ctx.get('target_url', 'unknown')}.",
                     severity="HIGH",
                     mitre_technique="T1499.001"
                 ))
                 is_malicious = True
                 max_confidence = max(max_confidence, 0.85)

            # ------------------------------------------------------------------
            # Rule 3: Amplification Attack
            # Logic: DNS/NTP reflection patterns
            # ------------------------------------------------------------------
            if "amplification" in details or ("dns" in details and "response_size" in details):
                findings.append(AgentFinding(
                    title="Amplification Attack Detected",
                    description="Traffic pattern consistent with DNS/NTP amplification reflection.",
                    severity="CRITICAL",
                    mitre_technique="T1498.002"
                ))
                is_malicious = True
                max_confidence = max(max_confidence, 0.95)

            # ------------------------------------------------------------------
            # Rule 4: Resource Exhaustion
            # Logic: High CPU/Mem on services
            # ------------------------------------------------------------------
            if "cpu_saturation" in details or "memory_exhaustion" in details:
                 findings.append(AgentFinding(
                    title="Service Resource Exhaustion",
                    description="Critical service resource depletion detected (CPU/RAM). Possible DoS.",
                    severity="HIGH",
                    mitre_technique="T1499"
                ))
                 is_malicious = True
                 max_confidence = max(max_confidence, 0.90)

        return AgentResult(
            agent_name=self.name,
            verdict="MALICIOUS" if is_malicious else "BENIGN",
            confidence=max_confidence,
            findings=findings,
            raw_artifacts={"flood_signal_count": len(flood_signals)}
        )
