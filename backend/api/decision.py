from flask import Blueprint, jsonify, request, Response, stream_with_context
from services.decision_service import DecisionService

decision_bp = Blueprint('decision', __name__)

@decision_bp.route('', methods=['POST'])
def make_decision():
    data = request.json
    if not data or 'report' not in data:
        return jsonify({"error": "Missing agent report data"}), 400
        
    try:
        # Return a streaming response
        return Response(
            stream_with_context(DecisionService.stream_verdict(data['report'])),
            content_type='text/plain' # Plain text stream of the JSON string
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
