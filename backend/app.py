from flask import Flask
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
app.config['EXAMPLE_FILES_FOLDER'] = 'example_files'
app.config['ALLOWED_EXTENSIONS'] = {'xml', 'xlsx', 'xls'}

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
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
