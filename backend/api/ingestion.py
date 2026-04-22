from flask import Blueprint, request, jsonify
import os
import werkzeug

ingestion_bp = Blueprint('ingestion', __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@ingestion_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = werkzeug.utils.secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        print(f"Saving file to: {file_path}")
        file.save(file_path)
        print("File saved successfully, returning response...")
        
        # Placeholder for Step 2 trigger
        response_data = {
            "message": "File uploaded successfully",
            "filename": filename,
            "path": file_path,
            "size": os.path.getsize(file_path)
        }
        print(f"Response data: {response_data}")
        return jsonify(response_data), 201
