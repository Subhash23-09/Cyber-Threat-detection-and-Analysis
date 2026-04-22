from flask import Blueprint, jsonify
from services.memory_store import MemoryService

memory_bp = Blueprint('memory', __name__)

@memory_bp.route('/context', methods=['GET'])
def get_context():
    try:
        context = MemoryService.get_context()
        return jsonify(context), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
