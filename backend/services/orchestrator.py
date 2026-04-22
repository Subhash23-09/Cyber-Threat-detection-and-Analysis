import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from services.memory_store import MemoryService
from services.llm_service import LLMService
from agents.auth_agent import AuthAgent
from agents.system_agent import SystemAgent
from agents.exfiltration_agent import ExfiltrationAgent

from agents.network_flood_agent import NetworkFloodAgent

class OrchestratorService:
    @staticmethod
    async def orchestrate(signals: list, context: dict) -> Dict[str, Any]:
        """
        Runs the full multi-agent pipeline and returns synthesized results.
        """
        results = []
        
        # 1. Deployment
        auth_res = await AuthAgent().analyze(signals, context)
        sys_res = await SystemAgent().analyze(signals, context)
        exfil_res = await ExfiltrationAgent().analyze(signals, context)

        flood_res = await NetworkFloodAgent().analyze(signals, context)
        
        results = [auth_res, sys_res, exfil_res, flood_res]
        
        # 3. Synthesis
        synthesized_plan = await OrchestratorService.synthesize_plan(signals, results)
        
        return {
            "agents_analyzed": results,
            "synthesized_plan": synthesized_plan
        }

    @staticmethod
    async def stream_agent_updates(signals: list, context: dict) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator for SSE (thoughts + answer mesh).
        """
        # Step 1: Initial Thought
        yield {
            "type": "thought",
            "content": f"Orchestrator received {len(signals)} raw security signals. Initializing multi-agent triage..."
        }
        await asyncio.sleep(1)

        # Parallelize for performance in stream
        agents = [AuthAgent(), SystemAgent(), ExfiltrationAgent(), NetworkFloodAgent()]
        agent_names = ["AUTH", "SYSTEM", "EXFIL", "DDOS"]
        
        agent_results = []
        for agent, display_name in zip(agents, agent_names):
            yield {
                "type": "thought",
                "content": f"Deploying {display_name}_AGENT for deep forensic analysis..."
            }
            res = await agent.analyze(signals, context)
            agent_results.append(res)
            
            # Assuming agent.analyze returns an object with a 'verdict' attribute
            # If it returns a dict, use res['verdict']
            verdict_value = res.verdict if hasattr(res, 'verdict') else res.get('verdict', 'UNKNOWN')
            
            yield {
                "type": "thought",
                "content": f"{display_name}_AGENT investigation complete. Verdict: {verdict_value}."
            }
            await asyncio.sleep(0.3)

        # Step 4: Synthesis Thought
        yield {
            "type": "thought",
            "content": "Consolidating agent findings into a master defense plan..."
        }
        
        # Step 5: Streaming the Synthesis (Answer)
        synthesized_plan = await OrchestratorService.synthesize_plan(signals, agent_results)
        
        # Stream the synthesis token by token or in chunks
        for chunk in synthesized_plan.split(' '):
            await asyncio.sleep(0.05)
            yield {
                "type": "answer",
                "content": chunk + " "
            }

        yield {
            "type": "thought",
            "content": "Autonomous Defense Plan delivered. Monitoring for perimeter deviations."
        }

    @staticmethod
    async def synthesize_plan(signals: list, agent_results: list) -> str:
        """
        Uses LLM to combine all findings into a Markdown defense plan.
        """
        llm = LLMService.get_llm()
        if not llm:
            return "## Defense Plan (Heuristic Mode)\n- Monitor flagged patterns.\n- Isolate suspicious IPs found by agents."

        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template("""
            You are the "Narrative Synthesizer" for an Autonomous Cyber Defense system.
            Combine the findings from multiple specialized agents into one comprehensive defense plan.
            
            AGENT FINDINGS:
            {findings}
            
            SIGNALS:
            {signals}
            
            Structure the response in Markdown:
            ### 1. Executive Summary
            ### 2. Detailed Technical Findings
            ### 3. Mitigation & Response Playbook
            ### 4. Continuous Monitoring Strategy
            
            Tone: Professional, urgent, security-first.
            """)
            
            chain = prompt | llm | StrOutputParser()
            # Use async invoke (ainvoke) to prevent blocking the event loop
            return await chain.ainvoke({
                "findings": json.dumps([r.model_dump() if hasattr(r, 'model_dump') else r for r in agent_results], default=str), 
                "signals": json.dumps(signals[:5], default=str)
            })
        except Exception as e:
            return f"Synthesis failed: {str(e)}. Please review individual agent findings."

    @staticmethod
    async def run_cycle():
        """
        Asynchronous wrapper for the new orchestration flow to support the existing UI.
        """
        from services.memory_store import MemoryService
        
        # Run the async orchestration
        try:
            # Fetch context asynchronously
            context = await MemoryService.get_context()
            signals = context['short_term']['active_context']
            
            if not signals:
                return {
                    "status": "idle",
                    "plan": {
                        "decision": "IGNORE",
                        "reasoning": "No active signals found in memory.",
                        "confidence": "HIGH"
                    }
                }

            result = await OrchestratorService.orchestrate(signals, context)
            
            # Map the new results to the old "plan" structure
            # We collect all malicious agents to define the 'decision'
            malicious_agents = [r for r in result['agents_analyzed'] if r.verdict == 'MALICIOUS']
            # Join multiple agents if found, e.g., "DDOS, AUTH"
            decision = ", ".join([r.agent_name for r in malicious_agents]) if malicious_agents else "IGNORE"
            
            return {
                "status": "active",
                "plan": {
                    "decision": decision,
                    "reasoning": result['synthesized_plan'], 
                    "confidence": "HIGH"
                }
            }
        except Exception as e:
            print(f"Error in run_cycle: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "plan": {
                    "decision": "ERROR",
                    "reasoning": str(e),
                    "confidence": "LOW"
                }
            }

