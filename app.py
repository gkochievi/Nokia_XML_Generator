from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
from modules.xml_parser import XMLParser
from modules.xml_viewer import XMLViewer
from modules.excel_parser import ExcelParser
from modules.modernization import ModernizationGenerator
from modules.rollout import RolloutGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
app.config['ALLOWED_EXTENSIONS'] = {'xml', 'xlsx', 'xls'}

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def main():
    """Main function for running the application"""
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/view-xml', methods=['POST'])
def view_xml():
    """Parse and view XML configuration file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only XML files are allowed'}), 400
        
        # Save temporary file
        temp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
            file.save(tmp.name)
            temp_path = tmp.name
        
        try:
            # Parse XML
            parser = XMLParser()
            viewer = XMLViewer()
            
            # Load and parse the XML
            tree = parser.parse_file(temp_path)
            
            # Extract configuration data
            config_data = viewer.extract_configuration_data(tree)
            
            # Format XML for display
            formatted_xml = viewer.format_xml_for_display(tree)
            
            return jsonify({
                'success': True,
                'data': config_data,
                'formatted': formatted_xml
            })
            
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Error viewing XML: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/modernization', methods=['POST'])
def modernization():
    """Handle 5G modernization request"""
    try:
        # Validate required files
        required_files = ['existingXml', 'reference5gXml', 'transmissionExcel']
        for file_key in required_files:
            if file_key not in request.files:
                return jsonify({'error': f'Missing required file: {file_key}'}), 400
        
        station_name = request.form.get('stationName')
        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400
        
        # Save uploaded files temporarily
        temp_files = {}
        try:
            for file_key in required_files:
                file = request.files[file_key]
                if file.filename == '':
                    return jsonify({'error': f'No file selected for {file_key}'}), 400
                
                if not allowed_file(file.filename):
                    return jsonify({'error': f'Invalid file type for {file_key}'}), 400
                
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(temp_path)
                temp_files[file_key] = temp_path
            
            # Process modernization
            generator = ModernizationGenerator()
            output_filename = generator.generate(
                station_name=station_name,
                existing_xml_path=temp_files['existingXml'],
                reference_5g_xml_path=temp_files['reference5gXml'],
                transmission_excel_path=temp_files['transmissionExcel'],
                output_folder=app.config['GENERATED_FOLDER']
            )
            
            return jsonify({
                'success': True,
                'filename': output_filename,
                'message': '5G modernization configuration generated successfully'
            })
            
        finally:
            # Clean up temporary files
            for path in temp_files.values():
                if os.path.exists(path):
                    os.unlink(path)
                    
    except Exception as e:
        logger.error(f"Error in modernization: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rollout', methods=['POST'])
def rollout():
    """Handle new rollout request"""
    try:
        # Validate required files
        required_files = ['referenceXml', 'radioExcel', 'transmissionExcel']
        for file_key in required_files:
            if file_key not in request.files:
                return jsonify({'error': f'Missing required file: {file_key}'}), 400
        
        station_name = request.form.get('stationName')
        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400
        
        # Save uploaded files temporarily
        temp_files = {}
        try:
            for file_key in required_files:
                file = request.files[file_key]
                if file.filename == '':
                    return jsonify({'error': f'No file selected for {file_key}'}), 400
                
                if not allowed_file(file.filename):
                    return jsonify({'error': f'Invalid file type for {file_key}'}), 400
                
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(temp_path)
                temp_files[file_key] = temp_path
            
            # Process rollout
            generator = RolloutGenerator()
            output_filename = generator.generate(
                station_name=station_name,
                reference_xml_path=temp_files['referenceXml'],
                radio_excel_path=temp_files['radioExcel'],
                transmission_excel_path=temp_files['transmissionExcel'],
                output_folder=app.config['GENERATED_FOLDER']
            )
            
            return jsonify({
                'success': True,
                'filename': output_filename,
                'message': 'New rollout configuration generated successfully'
            })
            
        finally:
            # Clean up temporary files
            for path in temp_files.values():
                if os.path.exists(path):
                    os.unlink(path)
                    
    except Exception as e:
        logger.error(f"Error in rollout: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated XML file"""
    try:
        file_path = os.path.join(app.config['GENERATED_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<filename>')
def preview_file(filename):
    """Preview generated XML file content"""
    try:
        file_path = os.path.join(app.config['GENERATED_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error previewing file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/modernization', methods=['GET', 'POST'])
def modernization_page():
    return render_template('modernization.html')

@app.route('/rollout', methods=['GET', 'POST'])
def rollout_page():
    return render_template('rollout.html')

@app.route('/xml-viewer', methods=['GET', 'POST'])
def xml_viewer_page():
    xml_tree = None
    config_data = None
    if request.method == 'POST':
        file = request.files.get('xml_file')
        if file and file.filename.endswith('.xml'):
            from modules.xml_viewer import XMLViewer
            import tempfile
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
                    file.save(tmp.name)
                    temp_path = tmp.name
                viewer = XMLViewer()
                xml_tree = viewer.html_tree_from_file(temp_path)
                # extract key info
                from modules.xml_parser import XMLParser
                parser = XMLParser()
                tree = parser.parse_file(temp_path)
                config_data = viewer.extract_configuration_data(tree)
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
    return render_template('xml_viewer.html', xml_tree=xml_tree, config_data=config_data)

@app.route('/api/upload-xmls', methods=['POST'])
def upload_xmls():
    """Upload multiple XML files to uploads/ directory"""
    if 'xmlFiles' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    files = request.files.getlist('xmlFiles')
    saved = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            saved.append(filename)
    return jsonify({'success': True, 'saved': saved})

@app.route('/api/list-xmls', methods=['GET'])
def list_xmls():
    """List all uploaded XML files"""
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.lower().endswith('.xml')]
    return jsonify({'files': files})

@app.route('/api/delete-xml/<filename>', methods=['DELETE'])
def delete_xml(filename):
    """Delete an uploaded XML file"""
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True, 'deleted': filename})
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/view-xml/<filename>', methods=['GET'])
def view_uploaded_xml(filename):
    """Parse and view an uploaded XML file by filename"""
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    try:
        parser = XMLParser()
        viewer = XMLViewer()
        tree = parser.parse_file(file_path)
        config_data = viewer.extract_configuration_data(tree)
        formatted_xml = viewer.format_xml_for_display(tree)
        html_tree = viewer.html_tree_from_file(file_path)
        return jsonify({
            'success': True,
            'data': config_data,
            'formatted': formatted_xml,
            'html_tree': html_tree
        })
    except Exception as e:
        logger.error(f"Error viewing uploaded XML: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    main()