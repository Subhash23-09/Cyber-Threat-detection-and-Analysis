from flask import Blueprint, jsonify, send_from_directory, current_app
from services.preprocessor import PreprocessorService
from models import Signal
import os
import json
import time

processing_bp = Blueprint('processing', __name__)

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@processing_bp.route('/process/<filename>', methods=['POST'])
def process_log(filename):
    file_path = os.path.join(os.getcwd(), 'uploads', filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
        
    try:
        # 1. Process
        signals, stats = PreprocessorService.process_file(file_path)
        
        # 2. Save Signals to File (Server Side) to avoid Browser Crash
        output_filename = f"signals_{filename}_{int(time.time())}.json"
        output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
        
        with open(output_path, 'w') as f:
            json.dump(signals, f, indent=2)
            
        return jsonify({
            "message": "Processing complete",
            "signals_count": len(signals),
            "download_url": f"/api/v1/download/{output_filename}", # Return URL
            "stats": stats
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@processing_bp.route('/download/<filename>', methods=['GET'])
def download_results(filename):
    # Ensure security check here in prod (path traversal), for now simple send
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@processing_bp.route('/signals', methods=['GET'])
def get_all_signals():
    try:
        # Limit this too for safety?
        signals = Signal.query.order_by(Signal.created_at.desc()).limit(100).all()
        return jsonify([s.to_dict() for s in signals]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
