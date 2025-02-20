from flask import Blueprint, jsonify, request
import json
from services.vrp.solve_vrp import solve_vrp

vrp_bp = Blueprint('vrp', __name__)

@vrp_bp.route('/solve', methods=['POST'])
def solve_vrp_route():
    try:
        # Handle both FormData and JSON requests
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = {
                'num_vehicles': int(request.form.get('num_vehicles')),
                'csv_data': {
                    'content': request.files['csv'].read().decode('utf-8'),
                    'selectedColumns': json.loads(request.form.get('selectedColumns')),
                    'columnMappings': json.loads(request.form.get('columnMappings')),
                    'delimiter': request.form.get('delimiter')
                }
            }
        else:
            data = request.json

        if not data.get('num_vehicles'):
            return jsonify({'error': 'Missing number of vehicles'}), 400
            
        result = solve_vrp(data)
        if result is None:
            return jsonify({'error': 'No solution found'}), 400
            
        return jsonify({'success': True, **result})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
