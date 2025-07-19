from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
from modules.xml_parser import XMLParser
from modules.xml_viewer import XMLViewer
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
app.config['EXAMPLE_FILES_FOLDER'] = 'example_files'
app.config['ALLOWED_EXTENSIONS'] = {'xml', 'xlsx', 'xls'}

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXAMPLE_FILES_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Helper for file validation and saving ---
def validate_and_save_files(request, required_files, upload_folder):
    # Check required files
    for file_key in required_files:
        if file_key not in request.files:
            return None, jsonify({'error': f'Missing required file: {file_key}'}), 400

    station_name = request.form.get('stationName')
    if not station_name:
        return None, jsonify({'error': 'Station name is required'}), 400

    temp_files = {}
    for file_key in required_files:
        file = request.files[file_key]
        if file.filename == '':
            return None, jsonify({'error': f'No file selected for {file_key}'}), 400
        if not allowed_file(file.filename):
            return None, jsonify({'error': f'Invalid file type for {file_key}'}), 400
        temp_path = os.path.join(upload_folder, secure_filename(file.filename))
        file.save(temp_path)
        temp_files[file_key] = temp_path

    return {'station_name': station_name, 'temp_files': temp_files}, None, None

def main():
    """Main function for running the application"""
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/modernization')
def show_modernization():
    return render_template('modernization.html')

@app.route('/rollout')
def show_rollout():
    return render_template('rollout.html')

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
            # Clean up a temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Error viewing XML: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/modernization', methods=['POST'])
def modernization():
    """Handle 5G modernization request"""
    try:
        station_name = request.form.get('stationName')
        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400

        # Get file paths - either from uploads or example_files selections
        file_paths = {}
        
        # Handle existing XML (always uploaded)
        if 'existingXml' not in request.files or request.files['existingXml'].filename == '':
            return jsonify({'error': 'არსებული სადგურის XML ფაილი აუცილებელია'}), 400
        
        existing_xml_file = request.files['existingXml']
        if not allowed_file(existing_xml_file.filename):
            return jsonify({'error': 'არასწორი ფაილის ტიპი არსებული XML-ისთვის'}), 400
        
        # Save existing XML to temp location
        temp_existing_xml = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(existing_xml_file.filename))
        existing_xml_file.save(temp_existing_xml)
        file_paths['existingXml'] = temp_existing_xml
        
        # Handle Reference 5G XML (dropdown selection or upload)
        reference_5g_selection = request.form.get('reference5gXmlSelection')
        if reference_5g_selection and reference_5g_selection != 'upload':
            # Use selected file from example_files
            file_paths['reference5gXml'] = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], reference_5g_selection)
        else:
            # Handle upload
            if 'reference5gXmlUpload' not in request.files or request.files['reference5gXmlUpload'].filename == '':
                return jsonify({'error': 'Reference 5G XML ფაილი აუცილებელია'}), 400
            
            ref_xml_file = request.files['reference5gXmlUpload']
            if not allowed_file(ref_xml_file.filename):
                return jsonify({'error': 'არასწორი ფაილის ტიპი Reference XML-ისთვის'}), 400
            
            temp_ref_xml = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(ref_xml_file.filename))
            ref_xml_file.save(temp_ref_xml)
            file_paths['reference5gXml'] = temp_ref_xml
        
        # Handle IP Plan Excel (dropdown selection or upload)
        ip_plan_selection = request.form.get('ipPlanSelection')
        if ip_plan_selection and ip_plan_selection != 'upload':
            # Use selected file from example_files
            file_paths['transmissionExcel'] = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], ip_plan_selection)
        else:
            # Handle upload
            if 'ipPlanUpload' not in request.files or request.files['ipPlanUpload'].filename == '':
                return jsonify({'error': 'IP Plan Excel ფაილი აუცილებელია'}), 400
            
            excel_file = request.files['ipPlanUpload']
            if not allowed_file(excel_file.filename):
                return jsonify({'error': 'არასწორი ფაილის ტიპი Excel-ისთვის'}), 400
            
            temp_excel = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(excel_file.filename))
            excel_file.save(temp_excel)
            file_paths['transmissionExcel'] = temp_excel
        
        # Process modernization
        generator = ModernizationGenerator()
        
        # Extract all parameters from both XMLs for logging
        try:
            parser = XMLParser()
            
            # Extract existing station data
            existing_tree = parser.parse_file(file_paths['existingXml'])
            existing_bts_name = parser.extract_bts_name(existing_tree)
            existing_bts_id = parser.extract_bts_id(existing_tree)
            existing_sctp_port = parser.extract_sctp_port_min(existing_tree)
            existing_2g_params = parser.extract_2g_parameters(existing_tree)
            existing_4g_cells = parser.extract_4g_cells(existing_tree)
            logger.info(f"Existing station btsName: {existing_bts_name}")
            logger.info(f"Existing station BTS ID: {existing_bts_id}")
            logger.info(f"Existing station sctpPortMin: {existing_sctp_port}")
            logger.info(f"Existing station 2G params: {existing_2g_params}")
            logger.info(f"Existing station 4G cells: {existing_4g_cells}")
            
            # Extract reference template data
            reference_tree = parser.parse_file(file_paths['reference5gXml'])
            reference_bts_name = parser.extract_bts_name(reference_tree)
            reference_bts_id = parser.extract_bts_id(reference_tree)
            reference_sctp_port = parser.extract_sctp_port_min(reference_tree)
            reference_2g_params = parser.extract_2g_parameters(reference_tree)
            reference_4g_cells = parser.extract_4g_cells(reference_tree)
            logger.info(f"Reference template btsName: {reference_bts_name}")
            logger.info(f"Reference template BTS ID: {reference_bts_id}")
            logger.info(f"Reference template sctpPortMin: {reference_sctp_port}")
            logger.info(f"Reference template 2G params: {reference_2g_params}")
            logger.info(f"Reference template 4G cells: {reference_4g_cells}")
            
            if not existing_bts_name:
                return jsonify({'error': 'არსებული XML ფაილში btsName ვერ მოიძებნა'}), 400
            
            if not reference_bts_name:
                return jsonify({'error': 'Reference XML ფაილში btsName ვერ მოიძებნა'}), 400
                
        except Exception as e:
            logger.error(f"Error extracting station parameters: {str(e)}")
            return jsonify({'error': f'სადგურის პარამეტრების ამოღების შეცდომა: {str(e)}'}), 500
        
        output_filename = generator.generate(
            station_name=station_name,
            existing_xml_path=file_paths['existingXml'],
            reference_5g_xml_path=file_paths['reference5gXml'],
            transmission_excel_path=file_paths['transmissionExcel'],
            output_folder=app.config['GENERATED_FOLDER'],
            existing_bts_name=existing_bts_name,
            reference_bts_name=reference_bts_name
        )
        
        # Clean up temporary files (only the ones we created)
        if 'existingXml' in file_paths and file_paths['existingXml'].startswith(app.config['UPLOAD_FOLDER']):
            if os.path.exists(file_paths['existingXml']):
                os.unlink(file_paths['existingXml'])
        if reference_5g_selection == 'upload' and 'reference5gXml' in file_paths:
            if os.path.exists(file_paths['reference5gXml']):
                os.unlink(file_paths['reference5gXml'])
        if ip_plan_selection == 'upload' and 'transmissionExcel' in file_paths:
            if os.path.exists(file_paths['transmissionExcel']):
                os.unlink(file_paths['transmissionExcel'])
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'message': '5G modernization configuration generated successfully',
            'details': {
                'existing_bts_name': existing_bts_name,
                'reference_bts_name': reference_bts_name,
                'existing_bts_id': existing_bts_id,
                'reference_bts_id': reference_bts_id,
                'existing_sctp_port': existing_sctp_port,
                'reference_sctp_port': reference_sctp_port,
                'existing_2g_params': existing_2g_params,
                'reference_2g_params': reference_2g_params,
                'existing_4g_cells': existing_4g_cells,
                'reference_4g_cells': reference_4g_cells,
                'replacement_performed': bool(existing_bts_name and reference_bts_name),
                'bts_id_replacement_performed': bool(existing_bts_id and reference_bts_id),
                'sctp_port_replacement_performed': bool(existing_sctp_port and reference_sctp_port),
                'params_2g_replacement_performed': bool(existing_2g_params and reference_2g_params),
                'cells_4g_replacement_performed': bool(existing_4g_cells and reference_4g_cells)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in modernization: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rollout', methods=['POST'])
def rollout():
    """Handle new rollout request"""
    try:
        required_files = ['referenceXml', 'radioExcel', 'transmissionExcel']
        data, error_resp, status = validate_and_save_files(request, required_files, app.config['UPLOAD_FOLDER'])
        if error_resp:
            return error_resp, status
        if data is not None:
            station_name = data['station_name']
            temp_files = data['temp_files']
            try:
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
                for path in temp_files.values():
                    if os.path.exists(path):
                        os.unlink(path)
    except Exception as e:
        logger.error(f"Error in rollout: {str(e)}")
        return jsonify({'error': str(e)}), 500

# --- New API endpoints for example_files management ---

@app.route('/api/extract-bts-name', methods=['POST'])
def extract_bts_name():
    """Extract btsName from uploaded XML file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Parse XML and extract btsName
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            
            # Get debugging info
            root = tree.getroot()
            debug_info = {
                'root_tag': root.tag,
                'root_attributes': dict(root.attrib),
                'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
                'managed_objects': [],
                'xpath_tests': {}
            }
            
            # Test different XPath patterns for debugging
            xpath_tests = [
                "//managedObject",
                "//*[local-name()='managedObject']"
            ]
            
            for xpath in xpath_tests:
                try:
                    found = tree.xpath(xpath)
                    debug_info['xpath_tests'][xpath] = len(found)
                except Exception as e:
                    debug_info['xpath_tests'][xpath] = f"Error: {str(e)}"
            
            # Find all managedObject elements for debugging (try both patterns)
            all_managed_objects = tree.xpath("//*[local-name()='managedObject']")
            if not all_managed_objects:
                all_managed_objects = tree.xpath("//managedObject")
            
            for obj in all_managed_objects:
                debug_info['managed_objects'].append({
                    'class': obj.get('class'),
                    'distName': obj.get('distName'),
                    'operation': obj.get('operation'),
                    'tag': obj.tag
                })
            
            bts_name = parser.extract_bts_name(tree)
            
            if bts_name:
                return jsonify({
                    'success': True, 
                    'btsName': bts_name,
                    'debug': debug_info
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'btsName not found in XML file',
                    'debug': debug_info
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error extracting btsName: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-bts-id', methods=['POST'])
def extract_bts_id():
    """Extract BTS ID from uploaded XML file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Parse XML and extract BTS ID
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            
            # Get debugging info
            root = tree.getroot()
            debug_info = {
                'root_tag': root.tag,
                'root_attributes': dict(root.attrib),
                'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
                'managed_objects': [],
                'xpath_tests': {}
            }
            
            # Test different XPath patterns for debugging
            xpath_tests = [
                "//managedObject",
                "//*[local-name()='managedObject']"
            ]
            
            for xpath in xpath_tests:
                try:
                    found = tree.xpath(xpath)
                    debug_info['xpath_tests'][xpath] = len(found)
                except Exception as e:
                    debug_info['xpath_tests'][xpath] = f"Error: {str(e)}"
            
            # Find all managedObject elements for debugging (try both patterns)
            all_managed_objects = tree.xpath("//*[local-name()='managedObject']")
            if not all_managed_objects:
                all_managed_objects = tree.xpath("//managedObject")
            
            for obj in all_managed_objects:
                debug_info['managed_objects'].append({
                    'class': obj.get('class'),
                    'distName': obj.get('distName'),
                    'operation': obj.get('operation'),
                    'tag': obj.tag
                })
            
            bts_id = parser.extract_bts_id(tree)
            
            if bts_id:
                return jsonify({
                    'success': True, 
                    'btsId': bts_id,
                    'debug': debug_info
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'BTS ID not found in XML file',
                    'debug': debug_info
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error extracting BTS ID: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-sctp-port', methods=['POST'])
def extract_sctp_port():
    """Extract sctpPortMin from uploaded XML file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Parse XML and extract sctpPortMin
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            
            # Get debugging info
            root = tree.getroot()
            debug_info = {
                'root_tag': root.tag,
                'root_attributes': dict(root.attrib),
                'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
                'managed_objects': [],
                'xpath_tests': {}
            }
            
            # Test different XPath patterns for debugging
            xpath_tests = [
                "//managedObject",
                "//*[local-name()='managedObject']"
            ]
            
            for xpath in xpath_tests:
                try:
                    found = tree.xpath(xpath)
                    debug_info['xpath_tests'][xpath] = len(found)
                except Exception as e:
                    debug_info['xpath_tests'][xpath] = f"Error: {str(e)}"
            
            # Find all managedObject elements for debugging (try both patterns)
            all_managed_objects = tree.xpath("//*[local-name()='managedObject']")
            if not all_managed_objects:
                all_managed_objects = tree.xpath("//managedObject")
            
            for obj in all_managed_objects:
                debug_info['managed_objects'].append({
                    'class': obj.get('class'),
                    'distName': obj.get('distName'),
                    'operation': obj.get('operation'),
                    'tag': obj.tag
                })
            
            sctp_port = parser.extract_sctp_port_min(tree)
            
            if sctp_port:
                return jsonify({
                    'success': True, 
                    'sctpPortMin': sctp_port,
                    'debug': debug_info
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'sctpPortMin not found in XML file',
                    'debug': debug_info
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error extracting sctpPortMin: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-2g-params', methods=['POST'])
def extract_2g_params():
    """Extract 2G parameters from uploaded XML file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Parse XML and extract 2G parameters
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            
            # Get debugging info
            root = tree.getroot()
            debug_info = {
                'root_tag': root.tag,
                'root_attributes': dict(root.attrib),
                'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
                'managed_objects': [],
                'xpath_tests': {}
            }
            
            # Test different XPath patterns for debugging
            xpath_tests = [
                "//managedObject",
                "//*[local-name()='managedObject']"
            ]
            
            for xpath in xpath_tests:
                try:
                    found = tree.xpath(xpath)
                    debug_info['xpath_tests'][xpath] = len(found)
                except Exception as e:
                    debug_info['xpath_tests'][xpath] = f"Error: {str(e)}"
            
            # Find all managedObject elements for debugging (try both patterns)
            all_managed_objects = tree.xpath("//*[local-name()='managedObject']")
            if not all_managed_objects:
                all_managed_objects = tree.xpath("//managedObject")
            
            for obj in all_managed_objects:
                debug_info['managed_objects'].append({
                    'class': obj.get('class'),
                    'distName': obj.get('distName'),
                    'operation': obj.get('operation'),
                    'tag': obj.tag
                })
            
            params_2g = parser.extract_2g_parameters(tree)
            
            if params_2g:
                return jsonify({
                    'success': True, 
                    'params2g': params_2g,
                    'debug': debug_info
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': '2G parameters not found in XML file',
                    'debug': debug_info
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error extracting 2G parameters: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-4g-cells', methods=['POST'])
def extract_4g_cells():
    """Extract 4G cell parameters from uploaded XML file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Parse XML and extract 4G cell parameters
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            
            # Get debugging info
            root = tree.getroot()
            debug_info = {
                'root_tag': root.tag,
                'root_attributes': dict(root.attrib),
                'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
                'managed_objects': [],
                'xpath_tests': {}
            }
            
            # Test different XPath patterns for debugging
            xpath_tests = [
                "//managedObject",
                "//*[local-name()='managedObject']"
            ]
            
            for xpath in xpath_tests:
                try:
                    found = tree.xpath(xpath)
                    debug_info['xpath_tests'][xpath] = len(found)
                except Exception as e:
                    debug_info['xpath_tests'][xpath] = f"Error: {str(e)}"
            
            # Find all managedObject elements for debugging (try both patterns)
            all_managed_objects = tree.xpath("//*[local-name()='managedObject']")
            if not all_managed_objects:
                all_managed_objects = tree.xpath("//managedObject")
            
            for obj in all_managed_objects:
                debug_info['managed_objects'].append({
                    'class': obj.get('class'),
                    'distName': obj.get('distName'),
                    'operation': obj.get('operation'),
                    'tag': obj.tag
                })
            
            cells_4g = parser.extract_4g_cells(tree)
            
            if cells_4g:
                return jsonify({
                    'success': True, 
                    'cells4g': cells_4g,
                    'debug': debug_info
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': '4G cell parameters not found in XML file',
                    'debug': debug_info
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error extracting 4G cell parameters: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-4g-rootseq', methods=['POST'])
def extract_4g_rootseq():
    """Extract 4G rootSeqIndex parameters from uploaded XML file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Parse XML and extract 4G rootSeqIndex parameters
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            
            # Get debugging info
            root = tree.getroot()
            debug_info = {
                'root_tag': root.tag,
                'root_attributes': dict(root.attrib),
                'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
                'managed_objects': [],
                'xpath_tests': {}
            }
            
            # Test different XPath patterns for debugging
            xpath_tests = [
                "//managedObject[@class='NOKLTE:LNCEL_FDD']",
                "//*[local-name()='managedObject'][@class='NOKLTE:LNCEL_FDD']"
            ]
            
            for xpath in xpath_tests:
                try:
                    found = tree.xpath(xpath)
                    debug_info['xpath_tests'][xpath] = len(found)
                except Exception as e:
                    debug_info['xpath_tests'][xpath] = f"Error: {str(e)}"
            
            # Find all LNCEL_FDD managedObject elements for debugging
            all_managed_objects = tree.xpath("//*[local-name()='managedObject'][contains(@class, 'LNCEL_FDD')]")
            if not all_managed_objects:
                all_managed_objects = tree.xpath("//managedObject[contains(@class, 'LNCEL_FDD')]")
            
            for obj in all_managed_objects:
                debug_info['managed_objects'].append({
                    'class': obj.get('class'),
                    'distName': obj.get('distName'),
                    'operation': obj.get('operation'),
                    'tag': obj.tag
                })
            
            rootseq_4g = parser.extract_4g_rootseq(tree)
            
            if rootseq_4g:
                return jsonify({
                    'success': True, 
                    'rootseq4g': rootseq_4g,
                    'debug': debug_info
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': '4G rootSeqIndex parameters not found in XML file',
                    'debug': debug_info
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error extracting 4G rootSeqIndex parameters: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-5g-nrcells', methods=['POST'])
def extract_5g_nrcells():
    """Extract 5G NRCELL physCellId parameters from uploaded XML file"""
    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Parse XML and extract 5G NRCELL parameters
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            
            # Get debugging info
            root = tree.getroot()
            debug_info = {
                'root_tag': root.tag,
                'root_attributes': dict(root.attrib),
                'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
                'managed_objects': [],
                'xpath_tests': {}
            }
            
            # Test different XPath patterns for debugging
            xpath_tests = [
                "//managedObject[@class='com.nokia.srbts.nrbts:NRCELL']",
                "//*[local-name()='managedObject'][@class='com.nokia.srbts.nrbts:NRCELL']"
            ]
            
            for xpath in xpath_tests:
                try:
                    found = tree.xpath(xpath)
                    debug_info['xpath_tests'][xpath] = len(found)
                except Exception as e:
                    debug_info['xpath_tests'][xpath] = f"Error: {str(e)}"
            
            # Find all NRCELL managedObject elements for debugging
            all_managed_objects = tree.xpath("//*[local-name()='managedObject'][contains(@class, 'NRCELL')]")
            if not all_managed_objects:
                all_managed_objects = tree.xpath("//managedObject[contains(@class, 'NRCELL')]")
            
            for obj in all_managed_objects:
                debug_info['managed_objects'].append({
                    'class': obj.get('class'),
                    'distName': obj.get('distName'),
                    'operation': obj.get('operation'),
                    'tag': obj.tag
                })
            
            nrcells_5g = parser.extract_5g_nrcells(tree)
            
            if nrcells_5g:
                return jsonify({
                    'success': True, 
                    'nrcells5g': nrcells_5g,
                    'debug': debug_info
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': '5G NRCELL physCellId parameters not found in XML file',
                    'debug': debug_info
                })
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error extracting 5G NRCELL parameters: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/xml', methods=['GET'])
def list_example_xml_files():
    """List all XML files in example_files directory"""
    try:
        files = [f for f in os.listdir(app.config['EXAMPLE_FILES_FOLDER']) 
                if f.lower().endswith('.xml')]
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        logger.error(f"Error listing example XML files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/excel', methods=['GET'])
def list_example_excel_files():
    """List all Excel files in example_files directory"""
    try:
        files = [f for f in os.listdir(app.config['EXAMPLE_FILES_FOLDER']) 
                if f.lower().endswith(('.xlsx', '.xls'))]
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        logger.error(f"Error listing example Excel files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/upload', methods=['POST'])
def upload_example_file():
    """Upload a file to example_files directory"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only XML and Excel files are allowed.'}), 400
    
    try:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        file.save(save_path)
        return jsonify({'success': True, 'filename': filename, 'message': 'File uploaded successfully'})
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/delete/<filename>', methods=['DELETE'])
def delete_example_file(filename):
    """Delete a file from example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        os.remove(file_path)
        return jsonify({'success': True, 'deleted': filename, 'message': 'File deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/extract-bts-name/<filename>', methods=['GET'])
def extract_bts_name_from_example_file(filename):
    """Extract btsName from a file in example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Parse XML and extract btsName
        parser = XMLParser()
        tree = parser.parse_file(file_path)
        bts_name = parser.extract_bts_name(tree)
        
        if bts_name:
            return jsonify({'success': True, 'btsName': bts_name, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': 'btsName not found in XML file', 'filename': filename})
            
    except Exception as e:
        logger.error(f"Error extracting btsName from example file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/extract-bts-id/<filename>', methods=['GET'])
def extract_bts_id_from_example_file(filename):
    """Extract BTS ID from a file in example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Parse XML and extract BTS ID
        parser = XMLParser()
        tree = parser.parse_file(file_path)
        bts_id = parser.extract_bts_id(tree)
        
        if bts_id:
            return jsonify({'success': True, 'btsId': bts_id, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': 'BTS ID not found in XML file', 'filename': filename})
            
    except Exception as e:
        logger.error(f"Error extracting BTS ID from example file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/extract-sctp-port/<filename>', methods=['GET'])
def extract_sctp_port_from_example_file(filename):
    """Extract sctpPortMin from a file in example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Parse XML and extract sctpPortMin
        parser = XMLParser()
        tree = parser.parse_file(file_path)
        sctp_port = parser.extract_sctp_port_min(tree)
        
        if sctp_port:
            return jsonify({'success': True, 'sctpPortMin': sctp_port, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': 'sctpPortMin not found in XML file', 'filename': filename})
            
    except Exception as e:
        logger.error(f"Error extracting sctpPortMin from example file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/extract-2g-params/<filename>', methods=['GET'])
def extract_2g_params_from_example_file(filename):
    """Extract 2G parameters from a file in example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Parse XML and extract 2G parameters
        parser = XMLParser()
        tree = parser.parse_file(file_path)
        params_2g = parser.extract_2g_parameters(tree)
        
        if params_2g:
            return jsonify({'success': True, 'params2g': params_2g, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': '2G parameters not found in XML file', 'filename': filename})
            
    except Exception as e:
        logger.error(f"Error extracting 2G parameters from example file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/extract-4g-cells/<filename>', methods=['GET'])
def extract_4g_cells_from_example_file(filename):
    """Extract 4G cell parameters from a file in example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Parse XML and extract 4G cell parameters
        parser = XMLParser()
        tree = parser.parse_file(file_path)
        cells_4g = parser.extract_4g_cells(tree)
        
        if cells_4g:
            return jsonify({'success': True, 'cells4g': cells_4g, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': '4G cell parameters not found in XML file', 'filename': filename})
            
    except Exception as e:
        logger.error(f"Error extracting 4G cell parameters from example file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/extract-4g-rootseq/<filename>', methods=['GET'])
def extract_4g_rootseq_from_example_file(filename):
    """Extract 4G rootSeqIndex parameters from a file in example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Parse XML and extract 4G rootSeqIndex parameters
        parser = XMLParser()
        tree = parser.parse_file(file_path)
        rootseq_4g = parser.extract_4g_rootseq(tree)
        
        if rootseq_4g:
            return jsonify({'success': True, 'rootseq4g': rootseq_4g, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': '4G rootSeqIndex parameters not found in XML file', 'filename': filename})
            
    except Exception as e:
        logger.error(f"Error extracting 4G rootSeqIndex parameters from example file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/extract-5g-nrcells/<filename>', methods=['GET'])
def extract_5g_nrcells_from_example_file(filename):
    """Extract 5G NRCELL physCellId parameters from a file in example_files directory"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400
        
        # Parse XML and extract 5G NRCELL parameters
        parser = XMLParser()
        tree = parser.parse_file(file_path)
        nrcells_5g = parser.extract_5g_nrcells(tree)
        
        if nrcells_5g:
            return jsonify({'success': True, 'nrcells5g': nrcells_5g, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': '5G NRCELL physCellId parameters not found in XML file', 'filename': filename})
            
    except Exception as e:
        logger.error(f"Error extracting 5G NRCELL parameters from example file: {str(e)}")
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