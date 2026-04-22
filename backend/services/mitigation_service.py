from datetime import datetime

class MitigationService:
    # Playbook Database (Heuristic-driven)
    PLAYBOOKS = {
        "MALICIOUS": {
            "DDOS_AGENT": {
                "title": "DDoS Containment Playbook",
                "actions": [
                    "Rate-limit Source IP at Edge Firewall.",
                    "Enable Geo-Blocking for suspicious high-traffic regions.",
                    "Trigger auto-scaling for impacted service cluster.",
                    "Notify ISP of ongoing volumetric attack."
                ],
                "priority": "P1 - CRITICAL"
            },
            "AUTH_AGENT": {
                "title": "Credential Protection Playbook",
                "actions": [
                    "Enforce 15-minute lockout for Source IP.",
                    "Invalidate active sessions for targeted accounts.",
                    "Trigger mandatory password reset on next login.",
                    "Audit sudo logs for successful elevations during the window."
                ],
                "priority": "P2 - HIGH"
            },
            "EXFIL_AGENT": {
                "title": "Data Loss Prevention Playbook",
                "actions": [
                    "Terminate outbound connection to Destination IP.",
                    "Freeze targeted database account/token.",
                    "Quarantine source machine for forensic imaging.",
                    "Review DLP alerts for sensitive file matches."
                ],
                "priority": "P1 - CRITICAL"
            },

        },
        "BENIGN": {
            "title": "Standard Monitoring",
            "actions": [
                "No immediate action required.",
                "Whitelist activity if it matches known maintenance window.",
                "Continue logging for baseline refinement."
            ],
            "priority": "P4 - LOW"
        }
    }

    @staticmethod
    def get_playbooks(agent_reports):
        """
        Selects playbooks based on multiple agent verdicts and types.
        Returns a list of unique playbooks.
        """
        playbooks = []
        seen_agents = set()
        
        # Consistent mapping for multiple reports
        reports_list = list(agent_reports.values()) if isinstance(agent_reports, dict) else [agent_reports]
        
        for report in reports_list:
            verdict = report.get('report', {}).get('verdict', 'BENIGN')
            agent_type = report.get('agent', 'UNKNOWN')
            
            if agent_type in seen_agents:
                continue
            
            if verdict == "MALICIOUS":
                pb = MitigationService.PLAYBOOKS["MALICIOUS"].get(agent_type)
                if pb:
                    playbooks.append(pb)
                    seen_agents.add(agent_type)
                else:
                    # Generic Malicious Fallback
                    playbooks.append({
                        "title": f"Investigative Response: {agent_type}",
                        "actions": [
                            "Investigate forensic artifacts flagged by agent.",
                            "Isolate source if behavior escalates.",
                            "Review alert context in Memory Store."
                        ],
                        "priority": "P3 - MEDIUM"
                    })
                    seen_agents.add(agent_type)

        # If no malicious playbooks found, return standard monitoring
        if not playbooks:
            return [MitigationService.PLAYBOOKS["BENIGN"]]
            
        return playbooks
