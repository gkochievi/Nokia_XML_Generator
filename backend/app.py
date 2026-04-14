from flask import Flask
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
from constants import ALLOWED_EXTENSIONS, DEFAULT_MAX_UPLOAD_MB, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration — override via environment variables
max_upload_mb = int(os.environ.get('MAX_UPLOAD_MB', DEFAULT_MAX_UPLOAD_MB))
app.config['MAX_CONTENT_LENGTH'] = max_upload_mb * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['GENERATED_FOLDER'] = os.environ.get('GENERATED_FOLDER', 'generated')
app.config['EXAMPLE_FILES_FOLDER'] = os.environ.get('EXAMPLE_FILES_FOLDER', 'example_files')
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXAMPLE_FILES_FOLDER'], exist_ok=True)

# Load environment variables (for SFTP, etc.)
load_dotenv()

# Register blueprints
from routes.modernization import bp as modernization_bp
from routes.extraction import bp as extraction_bp
from routes.xml_viewer import bp as xml_viewer_bp
from routes.files import bp as files_bp
from routes.ip_plan import bp as ip_plan_bp
from routes.sftp import bp as sftp_bp

app.register_blueprint(modernization_bp)
app.register_blueprint(extraction_bp)
app.register_blueprint(xml_viewer_bp)
app.register_blueprint(files_bp)
app.register_blueprint(ip_plan_bp)
app.register_blueprint(sftp_bp)


def main():
    """Main function for running the application"""
    host = os.environ.get('FLASK_HOST', DEFAULT_SERVER_HOST)
    port = int(os.environ.get('FLASK_PORT', DEFAULT_SERVER_PORT))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes')
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
