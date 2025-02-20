from flask import Blueprint, jsonify, request
from services.csv.parse_csv_file import parse_csv_files

csv_bp = Blueprint('csv', __name__)

@csv_bp.route('/upload', methods=['POST'])
def upload_csv_route():
    try:
        if 'csv' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        files = {'file1': request.files['csv']}
        parsed_files = parse_csv_files(files)

        if not parsed_files:
            return jsonify({'error': 'Failed to parse CSV file'}), 400

        return jsonify({
            'success': True,
            'columns': parsed_files[0]['parsedColumns'],
            'delimiter': parsed_files[0]['delimiter']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
