from flask import Blueprint, jsonify, request, Response
from services.reporting_service import ReportingService
import json

reporting_bp = Blueprint('reporting', __name__)

@reporting_bp.route('/download', methods=['POST'])
def download_report():
    data = request.json
    if not data or 'agent_report' not in data or 'decision' not in data:
        return jsonify({"error": "Missing report data components"}), 400
        
    try:
        case_file = ReportingService.generate_case_file(
            data['agent_report'],
            data['decision']
        )
        
        # Return as downloadable JSON file
        return Response(
            json.dumps(case_file, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename={case_file["case_id"]}.json'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
