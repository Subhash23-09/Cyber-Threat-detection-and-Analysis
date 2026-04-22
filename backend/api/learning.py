from flask import Blueprint, jsonify, request
from services.learning_service import LearningService

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('', methods=['POST'])
def learn_incident():
    data = request.json
    if not data or 'case_file' not in data:
        return jsonify({"error": "Missing case file data"}), 400
        
    try:
        result = LearningService.learn_from_incident(data['case_file'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
