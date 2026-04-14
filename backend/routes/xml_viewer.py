from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from modules.xml_parser import XMLParser
from modules.xml_viewer import XMLViewer
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('xml_viewer', __name__)


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@bp.route('/api/view-xml', methods=['POST'])
def view_xml():
    """Parse and view XML configuration file (uploaded)"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400

        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not _allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only XML files are allowed'}), 400

        temp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
            file.save(tmp.name)
            temp_path = tmp.name

        try:
            parser = XMLParser()
            viewer = XMLViewer()
            tree = parser.parse_file(temp_path)
            config_data = viewer.extract_configuration_data(tree)
            formatted_xml = viewer.format_xml_for_display(tree)

            return jsonify({
                'success': True,
                'data': config_data,
                'formatted': formatted_xml
            })
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error viewing XML: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/view-xml/<filename>', methods=['GET'])
def view_uploaded_xml(filename):
    """Parse and view an uploaded XML file by filename"""
    filename = secure_filename(filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    try:
        parser = XMLParser()
        viewer = XMLViewer()
        tree = parser.parse_file(file_path)
        config_data = viewer.extract_configuration_data(tree)
        formatted_xml = viewer.format_xml_for_display(tree)
        return jsonify({
            'success': True,
            'data': config_data,
            'formatted': formatted_xml
        })
    except Exception as e:
        logger.error(f"Error viewing uploaded XML: {str(e)}")
        return jsonify({'error': str(e)}), 500
