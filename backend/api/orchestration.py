from flask import Blueprint, jsonify
from services.orchestrator import OrchestratorService

orchestrator_bp = Blueprint('orchestrator', __name__)

@orchestrator_bp.route('/orchestrate', methods=['POST'])
def run_orchestrator():
    try:
        result = OrchestratorService.run_cycle()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
