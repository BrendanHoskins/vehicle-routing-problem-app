from flask import Blueprint, jsonify, request
import json
from server.services.vrp.enter_vrp import enter_vrp_flow

vrp_bp = Blueprint('vrp', __name__)

@vrp_bp.route('/solve', methods=['POST'])
def solve_vrp_route():
    try:
        data = request.json['csv_data']
        
        result = enter_vrp_flow(data)

        if result is None or not result.get('success'):
            return jsonify({'error': result.get('error', 'No solution found')}), 400
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
