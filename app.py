from flask import Flask, request, jsonify, send_file, render_template, after_this_request
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
from lxml import etree
import pandas as pd
import paramiko
import re
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

# --- Helpers ---
def resolve_example_xml_path(filename: str, region: str | None = None) -> str:
    """Resolve a reference XML path from example_files, trying region and fallbacks.
    Returns a path even if it may not exist (first candidate), so caller can handle errors.
    """
    base_dir = app.config['EXAMPLE_FILES_FOLDER']
    safe_name = secure_filename(filename)
    candidates = []
    if region in ['East', 'West']:
        candidates.append(os.path.join(base_dir, region, safe_name))
    candidates.append(os.path.join(base_dir, safe_name))
    # Fallbacks if region not provided or file not found at root
    candidates.append(os.path.join(base_dir, 'East', safe_name))
    candidates.append(os.path.join(base_dir, 'West', safe_name))
    # Return first existing, otherwise the first candidate
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

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

        # Mode and optional rollout overrides
        mode = (request.form.get('mode') or 'modernization').strip().lower()
        rollout_id_override = request.form.get('rolloutId')
        rollout_name_override = request.form.get('rolloutName')
        rollout_tac_override = request.form.get('rolloutTac')
        # Region for example_files (East/West) and Excel categories
        region = (request.form.get('region') or '').strip()

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
            # Use selected file from example_files; resolve with region and fallbacks
            file_paths['reference5gXml'] = resolve_example_xml_path(reference_5g_selection, region)
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
            # Use selected file from example_files/IP directory
            file_paths['transmissionExcel'] = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], 'IP', ip_plan_selection)
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
            existing_4g_rootseq = parser.extract_4g_rootseq(existing_tree)
            existing_5g_nrcells = parser.extract_5g_nrcells(existing_tree)
            logger.info(f"Existing station btsName: {existing_bts_name}")
            logger.info(f"Existing station BTS ID: {existing_bts_id}")
            logger.info(f"Existing station sctpPortMin: {existing_sctp_port}")
            logger.info(f"Existing station 2G params: {existing_2g_params}")
            logger.info(f"Existing station 4G cells: {existing_4g_cells}")
            logger.info(f"Existing station 4G rootSeq: {existing_4g_rootseq}")
            logger.info(f"Existing station 5G NRCells: {existing_5g_nrcells}")
            
            # Extract reference template data
            reference_tree = parser.parse_file(file_paths['reference5gXml'])
            reference_bts_name = parser.extract_bts_name(reference_tree)
            reference_bts_id = parser.extract_bts_id(reference_tree)
            reference_sctp_port = parser.extract_sctp_port_min(reference_tree)
            reference_2g_params = parser.extract_2g_parameters(reference_tree)
            reference_4g_cells = parser.extract_4g_cells(reference_tree)
            reference_4g_rootseq = parser.extract_4g_rootseq(reference_tree)
            reference_5g_nrcells = parser.extract_5g_nrcells(reference_tree)
            logger.info(f"Reference template btsName: {reference_bts_name}")
            logger.info(f"Reference template BTS ID: {reference_bts_id}")
            logger.info(f"Reference template sctpPortMin: {reference_sctp_port}")
            logger.info(f"Reference template 2G params: {reference_2g_params}")
            logger.info(f"Reference template 4G cells: {reference_4g_cells}")
            logger.info(f"Reference template 4G rootSeq: {reference_4g_rootseq}")
            logger.info(f"Reference template 5G NRCells: {reference_5g_nrcells}")
            
            if not existing_bts_name:
                return jsonify({'error': 'არსებული XML ფაილში btsName ვერ მოიძებნა'}), 400
            
            if not reference_bts_name:
                return jsonify({'error': 'Reference XML ფაილში btsName ვერ მოიძებნა'}), 400
                
        except Exception as e:
            logger.error(f"Error extracting station parameters: {str(e)}")
            return jsonify({'error': f'სადგურის პარამეტრების ამოღების შეცდომა: {str(e)}'}), 500
        
        output_filename, debug_log, extra = generator.generate(
            station_name=station_name,
            existing_xml_path=file_paths['existingXml'],
            reference_5g_xml_path=file_paths['reference5gXml'],
            transmission_excel_path=file_paths['transmissionExcel'],
            output_folder=app.config['GENERATED_FOLDER'],
            existing_bts_name=existing_bts_name,
            reference_bts_name=reference_bts_name,
            ip_plan_excel_path=file_paths['transmissionExcel'],
            mode=mode,
            rollout_overrides={
                'id': rollout_id_override,
                'name': rollout_name_override,
                'tac': rollout_tac_override
            } if mode == 'rollout' else None
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
        
        resp = {
            'success': True,
            'filename': output_filename,
            'message': '5G modernization configuration generated successfully',
            'details': {
                'mode': mode,
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
                'existing_4g_rootseq': existing_4g_rootseq,
                'reference_4g_rootseq': reference_4g_rootseq,
                'existing_5g_nrcells': existing_5g_nrcells,
                'reference_5g_nrcells': reference_5g_nrcells,
                'replacement_performed': bool(existing_bts_name and reference_bts_name),
                'bts_id_replacement_performed': bool(existing_bts_id and reference_bts_id),
                'sctp_port_replacement_performed': bool(existing_sctp_port and reference_sctp_port),
                'params_2g_replacement_performed': bool(existing_2g_params and reference_2g_params),
                'cells_4g_replacement_performed': bool(existing_4g_cells and reference_4g_cells),
                'rootseq_4g_replacement_performed': bool(existing_4g_rootseq and reference_4g_rootseq),
                'nrcells_5g_replacement_performed': bool(existing_4g_cells and reference_5g_nrcells),
                'ip_plan_lookup_station': (extra.get('ip_plan_lookup') if 'extra' in locals() else None),
                'ip_plan_found': (extra.get('ip_plan_found') if 'extra' in locals() else None),
                'rollout_overrides': {
                    'id': rollout_id_override,
                    'name': rollout_name_override,
                    'tac': rollout_tac_override
                } if mode == 'rollout' else None
            },
            'debug_log': debug_log
        }

        # Add IP Plan not found warning for visibility on frontend
        try:
            if extra and not extra.get('ip_plan_found', True):
                resp['warnings'] = {
                    'ip_plan': f"IP Plan not found for station '{extra.get('ip_plan_lookup','')}'. VLAN/IP/GW replacements were skipped."
                }
        except Exception:
            pass

        return jsonify(resp)
        
    except Exception as e:
        logger.error(f"Error in modernization: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/modernization/inspect', methods=['POST'])
def modernization_inspect():
    """Inspect uploaded existing XML to extract hardware/radio info and suggest a Reference 5G XML."""
    try:
        if 'existingXml' not in request.files or request.files['existingXml'].filename == '':
            return jsonify({'success': False, 'error': 'existingXml file is required'}), 400

        xml_file = request.files['existingXml']
        if not allowed_file(xml_file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type for existing XML'}), 400

        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(xml_file.filename))
        xml_file.save(temp_path)

        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(temp_path, parser)
            viewer = XMLViewer()
            info = viewer.extract_configuration_data(tree)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        # Gather summary
        station = info.get('stationInfo', {})
        radio = info.get('radioInfo', {})
        hardware = info.get('hardwareInfo', {})
        has2g = station.get('has2G', False)
        has3g = station.get('has3G', False)
        sector_count = radio.get('sectorCount', 0)
        model_codes = []
        models = []
        code_map = XMLViewer.MODEL_CODE_MAP if hasattr(XMLViewer, 'MODEL_CODE_MAP') else {}
        for m in hardware.get('modules', []):
            code = (m.get('productCode') or '').strip().upper()
            if not code:
                continue
            model_codes.append(code)
            mapped = code_map.get(code)
            if not mapped and '.' in code:
                base = code.split('.')[0]
                mapped = code_map.get(base)
            if not mapped:
                # fallback: prefix match
                for base, name in code_map.items():
                    if code.startswith(base):
                        mapped = name
                        break
            if mapped and mapped not in models:
                models.append(mapped)
        # fallback: if no mapped models, keep unique raw codes as models
        if not models and model_codes:
            models = list(dict.fromkeys(model_codes))

        # Suggest a Reference 5G XML based on naming convention in example_files
        examples_dir = app.config['EXAMPLE_FILES_FOLDER']
        try:
            files = [f for f in os.listdir(examples_dir) if f.startswith('5G') and f.endswith('.xml')]
        except Exception:
            files = []

        # Build desired tokens
        tokens = []
        tokens.append('no2G' if not has2g else '5G')
        if sector_count in [2, 3, 4]:
            tokens.append(f'S{sector_count}')
        # Prefer model token present in filename (AHEGA/AHEGB/AZQL/etc.) if any known from XMLViewer map
        model_candidates = set(models)
        preferred = None
        for fname in files:
            ok = True
            # Match sector tokens etc.
            for t in tokens:
                if t != '5G' and t not in fname:
                    ok = False
                    break
            # If station has 2G, avoid suggestions that contain 'no2G'
            if ok and has2g and 'no2G' in fname:
                ok = False
            # If station does NOT have 2G, prefer only no2G files
            if ok and (not has2g) and 'no2G' not in fname:
                ok = False
            if ok:
                if model_candidates:
                    if any(mc in fname for mc in model_candidates):
                        preferred = fname
                        break
                if not preferred:
                    preferred = fname
        suggestion = preferred or (files[0] if files else None)

        # Infer model from suggestion if none detected
        if (not models) and suggestion:
            try:
                model_tokens = set(XMLViewer.MODEL_CODE_MAP.values()) if hasattr(XMLViewer, 'MODEL_CODE_MAP') else set()
            except Exception:
                model_tokens = set()
            inferred = None
            for tok in model_tokens:
                if tok and tok in suggestion:
                    inferred = tok
                    break
            if inferred:
                models = [inferred]

        return jsonify({
            'success': True,
            'data': {
                'has2G': has2g,
                'has3G': has3g,
                'sectorCount': sector_count,
                'models': models or model_codes,
                'modelCodes': model_codes,
                'suggestedReference': suggestion,
                'availableReferences': files
            }
        })
    except Exception as e:
        logger.error(f"Error in modernization_inspect: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        target_dir = base_dir
        if region and region in ['East', 'West']:
            target_dir = os.path.join(base_dir, region)
        try:
            files = [f for f in os.listdir(target_dir) if f.lower().endswith('.xml')]
        except Exception:
            files = []
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        logger.error(f"Error listing example XML files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/example-files/excel', methods=['GET'])
def list_example_excel_files():
    """List all Excel files in example_files directory"""
    try:
        category = (request.args.get('category') or '').strip().lower()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        if category == 'ip':
            target_dir = os.path.join(base_dir, 'IP')
        elif category == 'data':
            target_dir = os.path.join(base_dir, 'Data')
        else:
            target_dir = base_dir
        try:
            files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.xlsx', '.xls'))]
        except Exception:
            files = []
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
        base_dir = app.config['EXAMPLE_FILES_FOLDER']

        # Optional targeting: region for XML; category for Excel
        region = (request.form.get('region') or '').strip()
        category = (request.form.get('category') or '').strip().lower()

        ext = filename.lower().rsplit('.', 1)[-1]
        target_dir = base_dir
        if ext == 'xml' and region in ['East', 'West']:
            target_dir = os.path.join(base_dir, region)
        elif ext in ['xlsx', 'xls']:
            if category == 'ip':
                target_dir = os.path.join(base_dir, 'IP')
            elif category == 'data':
                target_dir = os.path.join(base_dir, 'Data')

        os.makedirs(target_dir, exist_ok=True)
        save_path = os.path.join(target_dir, filename)
        # Ensure we can write the file and return error if not
        try:
            file.save(save_path)
        except Exception as write_err:
            logger.error(f"Upload write failed: {str(write_err)}")
            return jsonify({'success': False, 'error': f'Unable to save file to {save_path}'}), 500
        saved_rel = os.path.relpath(save_path, base_dir).replace('\\', '/')
        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'File uploaded successfully',
            'region': region if ext == 'xml' else None,
            'category': category if ext in ['xlsx','xls'] else None,
            'saved_to': saved_rel
        })
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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East','West'] else os.path.join(base_dir, filename)
        
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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East','West'] else os.path.join(base_dir, filename)
        
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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East','West'] else os.path.join(base_dir, filename)
        
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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East','West'] else os.path.join(base_dir, filename)
        
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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East','West'] else os.path.join(base_dir, filename)
        
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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East','West'] else os.path.join(base_dir, filename)
        
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
        region = (request.args.get('region') or '').strip()
        base_dir = app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East','West'] else os.path.join(base_dir, filename)
        
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

@app.route('/api/parse-ip-plan', methods=['POST'])
def parse_ip_plan():
    """Parse IP Plan Excel file for network parameters (debug endpoint)"""
    try:
        # Check if station name is provided
        station_name = request.form.get('stationName')
        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400
        
        # Check if IP Plan Excel file is provided
        if 'ipPlanFile' not in request.files:
            return jsonify({'error': 'IP Plan Excel file is required'}), 400
        
        ip_plan_file = request.files['ipPlanFile']
        if ip_plan_file.filename == '':
            return jsonify({'error': 'No IP Plan file selected'}), 400
        
        if not allowed_file(ip_plan_file.filename):
            return jsonify({'error': 'Invalid IP Plan file format'}), 400
        
        # Save uploaded IP Plan file temporarily
        ip_plan_temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                ip_plan_file.save(tmp.name)
                ip_plan_temp_path = tmp.name
            
            # Parse IP Plan Excel
            excel_parser = ExcelParser()
            ip_plan_data = excel_parser.parse_ip_plan_excel(ip_plan_temp_path, station_name)
            
            if ip_plan_data is None:
                return jsonify({
                    'success': False,
                    'error': f'Station "{station_name}" not found in IP Plan Excel file'
                }), 404
            
            # Log parsed data for debugging
            logger.info("=== IP PLAN PARSING DEBUG ===")
            logger.info(f"Station Name: {station_name}")
            logger.info(f"Found Station: {ip_plan_data.get('station_name')}")
            logger.info(f"Station Row: {ip_plan_data.get('station_row')}")
            
            # Log technology data
            technologies = ip_plan_data.get('technologies', {})
            for tech, data in technologies.items():
                logger.info(f"\n{tech} Technology:")
                logger.info(f"  VLAN ID: {data.get('vlanId')}")
                logger.info(f"  IP Address: {data.get('localIpAddr')}")
                logger.info(f"  Subnet Mask: {data.get('localIpPrefixLength')}")
                logger.info(f"  Gateway: {data.get('gateway')}")
            
            # Log routing rules
            routing_rules = ip_plan_data.get('routing_rules', {})
            logger.info("\nRouting Rules:")
            for iprt, rules in routing_rules.items():
                logger.info(f"  {iprt}:")
                for prefix, gateway in rules.items():
                    logger.info(f"    {prefix}.x.x -> {gateway}")
            
            logger.info("=== END IP PLAN DEBUG ===")
            
            if ip_plan_data.get('success', True):
                return jsonify({
                    'success': True,
                    'data': ip_plan_data,
                    'debug': {
                        'station_name': station_name,
                        'found_station': ip_plan_data.get('station_name'),
                        'station_row': ip_plan_data.get('station_row'),
                        'technologies_found': list(ip_plan_data.get('technologies', {}).keys()),
                        'routing_rules_count': len(ip_plan_data.get('routing_rules', {}))
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': ip_plan_data.get('error', 'Unknown error'),
                    'data': ip_plan_data,
                    'debug': {
                        'station_name': station_name,
                        'found_station': ip_plan_data.get('station_name'),
                        'station_row': ip_plan_data.get('station_row'),
                        'technologies_found': [],
                        'routing_rules_count': 0
                    }
                })
                
        finally:
            # Clean up temporary file
            if ip_plan_temp_path and os.path.exists(ip_plan_temp_path):
                os.unlink(ip_plan_temp_path)
    
    except Exception as e:
        logger.error(f"Error parsing IP Plan: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/parse-ip-plan-from-example', methods=['GET'])
def parse_ip_plan_from_example():
    """Parse IP Plan from example file (debug endpoint)"""
    try:
        station_name = request.args.get('station_name')
        filename = request.args.get('filename')
        
        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        # Find the file in example_files directory
        file_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': f'File {filename} not found in example files'}), 404
        
        # Parse IP Plan Excel
        excel_parser = ExcelParser()
        ip_plan_data = excel_parser.parse_ip_plan_excel(file_path, station_name)
        
        if ip_plan_data is None:
            return jsonify({
                'success': False,
                'error': f'Station "{station_name}" not found in IP Plan Excel file'
            }), 404
        
        # Log parsed data for debugging
        logger.info("=== IP PLAN PARSING DEBUG (Example File) ===")
        logger.info(f"File: {filename}")
        logger.info(f"Station Name: {station_name}")
        logger.info(f"Found Station: {ip_plan_data.get('station_name')}")
        logger.info(f"Station Row: {ip_plan_data.get('station_row')}")
        
        # Log technology data
        technologies = ip_plan_data.get('technologies', {})
        for tech, data in technologies.items():
            logger.info(f"\n{tech} Technology:")
            logger.info(f"  VLAN ID: {data.get('vlanId')}")
            logger.info(f"  IP Address: {data.get('localIpAddr')}")
            logger.info(f"  Subnet Mask: {data.get('localIpPrefixLength')}")
            logger.info(f"  Gateway: {data.get('gateway')}")
        
        # Log routing rules
        routing_rules = ip_plan_data.get('routing_rules', {})
        logger.info("\nRouting Rules:")
        for iprt, rules in routing_rules.items():
            logger.info(f"  {iprt}:")
            for prefix, gateway in rules.items():
                logger.info(f"    {prefix}.x.x -> {gateway}")
        
        logger.info("=== END IP PLAN DEBUG ===")
        
        return jsonify({
            'success': True,
            'data': ip_plan_data,
            'debug': {
                'filename': filename,
                'station_name': station_name,
                'found_station': ip_plan_data.get('station_name'),
                'station_row': ip_plan_data.get('station_row'),
                'technologies_found': list(technologies.keys()),
                'routing_rules_count': len(routing_rules)
            }
        })
        
    except Exception as e:
        logger.error(f"Error parsing IP Plan from example: {str(e)}")
        return jsonify({'error': str(e)}), 500

# --- SFTP backup download based on Excel mapping (ID/Name -> Backup_Name) ---
@app.route('/api/sftp-download', methods=['POST'])
def sftp_download():
    """Download backup XML from SFTP by ID or Name found in example_files/data.xlsx.
    Returns the file as an attachment so it is saved to the user's Downloads folder.
    """
    try:
        # Read query from form or JSON
        query = request.form.get('query') or (request.get_json(silent=True) or {}).get('query')
        if not query:
            return jsonify({'error': 'Missing parameter: query (ID or Name)'}), 400

        # Load Excel with mapping
        excel_path = os.path.join(app.config['EXAMPLE_FILES_FOLDER'], 'data.xlsx')
        if not os.path.exists(excel_path):
            return jsonify({'error': f'Excel file not found at {excel_path}'}), 404

        df = pd.read_excel(excel_path, engine='openpyxl')

        # Normalization helper: treat '_' and '-' as the same and ignore case/extra dashes
        def normalize_name(value: str) -> str:
            text = str(value).strip().lower()
            text = text.replace('_', '-')
            text = re.sub(r'-+', '-', text)
            return text

        # Prepare normalized name column
        if 'Name' not in df.columns or 'ID' not in df.columns or 'Backup_Name' not in df.columns:
            return jsonify({'error': 'Excel must have columns: ID, Name, Backup_Name'}), 400
        df['_name_norm'] = df['Name'].apply(normalize_name)

        # Find matching row
        if str(query).isdigit():
            row = df[df['ID'] == int(query)]
        else:
            row = df[df['_name_norm'] == normalize_name(query)]

        if row.empty:
            return jsonify({'error': 'No match found in Excel for provided ID/Name'}), 404

        backup_name = str(row.iloc[0]['Backup_Name']).strip()
        base_name = str(row.iloc[0]['Name']).strip()
        base_id = str(row.iloc[0]['ID']).strip()
        if not backup_name:
            return jsonify({'error': 'Backup_Name missing for matched record'}), 404

        # SFTP connection details (same as desktop script)
        host = os.getenv('SFTP_HOST', '127.0.0.1')
        port = int(os.getenv('SFTP_PORT', '22'))
        username = os.getenv('SFTP_USERNAME', '')
        password = os.getenv('SFTP_PASSWORD', '')
        remote_dir = os.getenv('SFTP_REMOTE_DIR', '/')
        if not host or not username or not password:
            return jsonify({'error': 'SFTP credentials are not configured'}), 500

        # Connect and download to temp file
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            remote_path = f"{remote_dir}/{backup_name}"
            # Desired local download filename
            file_ext = os.path.splitext(backup_name)[1] or '.xml'
            safe_base = ''.join('_' if c in '<>:"/\\|?*' else c for c in f"Config-{base_name}-{base_id}")
            download_filename = f"{safe_base}{file_ext}"

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            tmp_path = tmp.name
            tmp.close()
            sftp.get(remote_path, tmp_path)

        finally:
            try:
                sftp.close()
            except Exception:
                pass
            try:
                transport.close()
            except Exception:
                pass

        # Ensure temp file is removed after response is sent
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass
            return response

        return send_file(tmp_path, as_attachment=True, download_name=download_filename)

    except FileNotFoundError:
        return jsonify({'error': f'Backup file {backup_name} not found on SFTP'}), 404
    except Exception as e:
        logger.error(f"SFTP download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    main()