from flask import Blueprint, jsonify, request
from services.agent_manager import AgentManager
from services.memory_store import MemoryService

agents_bp = Blueprint('agents', __name__)

@agents_bp.route('', methods=['GET'])
def list_agents():
    return jsonify(AgentManager.list_agents()), 200

@agents_bp.route('/<agent_name>/run', methods=['POST'])
def run_agent(agent_name):
    agent = AgentManager.get_agent(agent_name)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
        
    try:
        # Get context from Memory
        context = MemoryService.get_context()
        signals = [s for s in context['short_term']['active_context']]
        
        # Run Analysis
        report = agent.analyze(signals, context)
        
        return jsonify({
            "agent": agent.name,
            "report": report,
            "timestamp": "now"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
