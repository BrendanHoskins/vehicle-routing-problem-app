from flask import Blueprint, jsonify, request
from server.services.csv.handle_excel_file import ExcelWorkbookProcessor

excel_bp = Blueprint('excel', __name__)

@excel_bp.route('/upload', methods=['POST'])
def upload_excel_file_route():
    try:
        excel_sheets_and_columns_to_be_mapped = ExcelWorkbookProcessor.parse_excel_files_and_return_sheets_and_columns(request.body.file)

        return jsonify({
            'excelSheetsAndColumns': excel_sheets_and_columns_to_be_mapped
        }), 200
    except Exception as error:
        return jsonify({
            'error': str(error)
            }), 500
