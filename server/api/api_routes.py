from flask import Blueprint, jsonify, request
from server.services.csv.handle_excel_file import ExcelFileProcessor
from server.services.vrp.enter_vrp import enter_vrp_flow
from server.db.db_utils import store_excel_file

api_bp = Blueprint('api', __name__)

@api_bp.route('/upload', methods=['POST'])
def upload_excel_file_route():
    try:
        excel_file = request.files['file']
        excel_sheets_and_columns_to_be_mapped = ExcelFileProcessor.parse_excel_file_and_return_sheets_and_columns(excel_file)
        file_id = store_excel_file(excel_file)
        return jsonify({
            'file_id': file_id,
            'excel_sheets_and_columns_to_be_mapped': excel_sheets_and_columns_to_be_mapped
        }), 200
    except Exception:
        return jsonify({
            'error': 'Something went wrong while uploading and parsing excel file for columns/sheets'
            }), 500

@api_bp.route('/solve', methods=['POST'])
def solve_vrp_route():
    try:
        mappings = request.form['mappings']
        file_id = request.form['file_id']
        
        result = enter_vrp_flow(mappings, file_id)

        if result is None or not result.get('success'):
            return jsonify({'error': result.get('error', 'No solution found')}), 400
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
