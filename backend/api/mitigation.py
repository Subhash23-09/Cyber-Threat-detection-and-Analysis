from flask import Blueprint, jsonify, request
from services.mitigation_service import MitigationService

mitigation_bp = Blueprint('mitigation', __name__)

@mitigation_bp.route('', methods=['POST'])
def get_mitigation():
    data = request.json
    if not data or 'agent_report' not in data:
        return jsonify({"error": "Missing agent report data"}), 400
        
    try:
        playbook = MitigationService.get_playbook(data['agent_report'])
        return jsonify(playbook), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
