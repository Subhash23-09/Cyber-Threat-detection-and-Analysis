from agents.auth_agent import AuthAgent
from agents.network_flood_agent import NetworkFloodAgent
from agents.exfiltration_agent import ExfiltrationAgent

from agents.system_agent import SystemAgent

class AgentManager:
    _agents = {}
    
    @classmethod
    def initialize(cls):
        """
        Registers all available agents.
        """
        cls._register(AuthAgent())
        cls._register(NetworkFloodAgent())
        cls._register(ExfiltrationAgent())

        cls._register(SystemAgent())
        print(f"[AgentManager] Initialized {len(cls._agents)} agents.")
        
    @classmethod
    def _register(cls, agent):
        cls._agents[agent.name] = agent
        
    @classmethod
    def get_agent(cls, agent_name):
        return cls._agents.get(agent_name)
    
    @classmethod
    def list_agents(cls):
        return [{"name": k, "description": v.description} for k, v in cls._agents.items()]
        
# Auto-initialize on import for MVP simplicity
AgentManager.initialize()
