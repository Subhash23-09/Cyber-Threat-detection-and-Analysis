from fastapi import APIRouter, HTTPException
import asyncio

router = APIRouter()

@router.post("/{agent_name}/run")
async def run_agent(agent_name: str):
    from services.agent_manager import AgentManager
    from services.memory_store import MemoryService
    
    # 1. Get the actual agent instance
    agent = AgentManager.get_agent(agent_name)
    if not agent:
        # Fallback mapping for frontend display names
        name_map = {
            "AUTH": "AUTH_AGENT",
            "SYSTEM": "SYSTEM_AGENT",
            "EXFIL": "EXFIL_AGENT",

            "DDOS": "DDOS_AGENT"
        }
        real_name = name_map.get(agent_name, agent_name)
        agent = AgentManager.get_agent(real_name)
        
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    try:
        # 2. Get real context and signals
        context = await MemoryService.get_context()
        signals = context['short_term']['active_context']
        
        # 3. Running the actual analysis
        result = await agent.analyze(signals, context)
        
        # 4. Format for Frontend
        return {
            "agent": agent.name,
            "report": {
                "verdict": result.verdict,
                "findings": [f.description for f in result.findings],
                "severity": "HIGH" if result.verdict == "MALICIOUS" else "LOW",
                "raw_findings": [f.model_dump() for f in result.findings]
            },
            "timestamp": "now"
        }
    except Exception as e:
        print(f"Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
