from flask import Blueprint, jsonify, request, Response, stream_with_context
from services.narrative_service import NarrativeService
from services.memory_store import MemoryService

narrative_bp = Blueprint('narrative', __name__)

@narrative_bp.route('', methods=['POST'])
def get_narrative():
    data = request.json
    if not data or 'agent_report' not in data or 'decision' not in data:
        return jsonify({"error": "Missing components for narrative generation"}), 400
        
    try:
        # Get full context for the storyline
        context = MemoryService.get_context()
        
        return Response(
            stream_with_context(NarrativeService.generate_storyline(
                data['agent_report'],
                data['decision'],
                context
            )),
            content_type='text/plain'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
