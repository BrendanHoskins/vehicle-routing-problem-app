from flask import Flask, send_from_directory
from api.vrp_route import vrp_bp
from api.csv_route import csv_bp
import os

app = Flask(__name__)

app.register_blueprint(vrp_bp, url_prefix='/api/vrp')
app.register_blueprint(csv_bp, url_prefix='/api/csv')

# Serve index.html
@app.route('/')
def serve_index():
    # Remove the leading '../' since we're already at root
    with open('client/html/index.html', 'r') as file:
        content = file.read()
        
    # Replace the placeholder with the actual API key
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    content = content.replace('%GOOGLE_MAPS_API_KEY%', api_key)
    
    return content

# Serve CSS files
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('../client/css', filename)

# Serve JavaScript files
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('../client/js', filename)

if __name__ == '__main__':
    app.run(debug=True)
