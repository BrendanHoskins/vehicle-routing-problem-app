from flask import Flask, send_from_directory
from server.api.api_routes import api_bp
import os
from server.db.init_db import init_app

app = Flask(import_name=__name__, instance_path=os.path.join(os.path.dirname(__file__), 'instance'))
app.config.from_mapping(DATABASE=os.path.join(app.instance_path, 'db.sqlite'))

try:
    os.makedirs(app.instance_path)
except OSError:
    pass

app.register_blueprint(api_bp, url_prefix='/api')

# Get the absolute path to the client directory
CLIENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client'))

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
    return send_from_directory(os.path.join(CLIENT_DIR, 'css'), filename)

# Serve JavaScript files
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(CLIENT_DIR, 'js'), filename)

init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
