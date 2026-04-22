from datetime import datetime
import uuid
from services.memory_store import MemoryService

class ReportingService:
    @staticmethod
    async def generate_case_file(agent_reports, decision):
        """
        Aggregates all system state into a final case file.
        """
        case_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6]}"
        
        # Get Context for Chain of Custody
        context = await MemoryService.get_context()
        signals = context['short_term']['active_context']
        
        # Extract entities from signals for long-term memory indexing
        actor_ips = list(set([s.get('actor', {}).get('source_ip') for s in signals if s.get('actor', {}).get('source_ip')]))
        target_users = list(set([s.get('target', {}).get('user') for s in signals if s.get('target', {}).get('user')]))
        attack_types = list(set([s.get('action') for s in signals if s.get('action')]))

        # Consolidation Logic for Multiple Agents
        all_reports = list(agent_reports.values()) if isinstance(agent_reports, dict) else [agent_reports]
        active_agents = [r.get('agent', 'Specialized Agent') for r in all_reports]
        verdicts = [r.get('report', {}).get('verdict', 'BENIGN') for r in all_reports]
        all_findings = []
        for r in all_reports:
            findings = r.get('report', {}).get('findings', [])
            if isinstance(findings, list):
                all_findings.extend(findings)
            else:
                all_findings.append(findings)

        report = {
            "case_id": case_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "status": "OPEN",
            
            "chain_of_custody": {
                "step_2_signals": {
                    "count": len(signals),
                    "types": list(set([s.get('event_type', 'unknown') for s in signals]))
                },
                "step_3_memory": {
                    "active_context_size": len(signals)
                },
                "step_4_orchestrator": {
                    "router_decision": ", ".join(active_agents) if active_agents else "Mesh Analysis"
                }

            },
            
            "investigation_details": {
                "agent_deployed": ", ".join(active_agents) if active_agents else "NONE",
                "agent_verdict": ", ".join(list(set(verdicts))) if verdicts else "BENIGN",
                "technical_findings": all_findings if all_findings else ["No specific indicators found."],
                # New: Specific entities for Memory Engine
                "involved_trace": actor_ips,
                "target_user": target_users[0] if target_users else "none",
                "attack_types": attack_types
            },

            "executive_verdict": decision
        }
        
        return report
