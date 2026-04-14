from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from lxml import etree
from modules.xml_parser import XMLParser
from modules.xml_viewer import XMLViewer
from modules.modernization import ModernizationGenerator
import os
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('modernization', __name__)


def _resolve_example_xml_path(filename: str, region: str | None = None) -> str:
    base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
    safe_name = secure_filename(filename)
    candidates = []
    if region in ['East', 'West']:
        candidates.append(os.path.join(base_dir, region, safe_name))
    candidates.append(os.path.join(base_dir, safe_name))
    candidates.append(os.path.join(base_dir, 'East', safe_name))
    candidates.append(os.path.join(base_dir, 'West', safe_name))
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@bp.route('/api/modernization', methods=['POST'])
def modernization():
    """Handle modernization request"""
    try:
        station_name = request.form.get('stationName')
        if not station_name:
            return jsonify({'success': False, 'error': 'Station name is required'}), 400

        mode = (request.form.get('mode') or 'modernization').strip().lower()
        rollout_id_override = request.form.get('rolloutId')
        rollout_name_override = request.form.get('rolloutName')
        rollout_tac_override = request.form.get('rolloutTac')
        region = (request.form.get('region') or '').strip()

        file_paths = {}

        # Handle existing XML
        existing_xml_selection = request.form.get('existingXmlSelection')
        if existing_xml_selection:
            file_paths['existingXml'] = _resolve_example_xml_path(existing_xml_selection, region)
        elif 'existingXml' in request.files and request.files['existingXml'].filename != '':
            existing_xml_file = request.files['existingXml']
            if not _allowed_file(existing_xml_file.filename):
                return jsonify({'success': False, 'error': 'არასწორი ფაილის ტიპი არსებული XML-ისთვის'}), 400
            temp_existing_xml = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(existing_xml_file.filename))
            existing_xml_file.save(temp_existing_xml)
            file_paths['existingXml'] = temp_existing_xml
        else:
            return jsonify({'success': False, 'error': 'არსებული სადგურის XML ფაილი აუცილებელია'}), 400

        # Handle Reference 5G XML
        reference_5g_selection = request.form.get('reference5gXmlSelection')
        if reference_5g_selection and reference_5g_selection != 'upload':
            file_paths['reference5gXml'] = _resolve_example_xml_path(reference_5g_selection, region)
        else:
            if 'reference5gXmlUpload' not in request.files or request.files['reference5gXmlUpload'].filename == '':
                return jsonify({'success': False, 'error': 'Reference 5G XML ფაილი აუცილებელია'}), 400
            ref_xml_file = request.files['reference5gXmlUpload']
            if not _allowed_file(ref_xml_file.filename):
                return jsonify({'success': False, 'error': 'არასწორი ფაილის ტიპი Reference XML-ისთვის'}), 400
            temp_ref_xml = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(ref_xml_file.filename))
            ref_xml_file.save(temp_ref_xml)
            file_paths['reference5gXml'] = temp_ref_xml

        # Handle IP Plan Excel
        ip_plan_selection = request.form.get('ipPlanSelection')
        if ip_plan_selection and ip_plan_selection != 'upload':
            file_paths['transmissionExcel'] = os.path.join(current_app.config['EXAMPLE_FILES_FOLDER'], 'IP', ip_plan_selection)
        else:
            if 'ipPlanUpload' not in request.files or request.files['ipPlanUpload'].filename == '':
                return jsonify({'success': False, 'error': 'IP Plan Excel ფაილი აუცილებელია'}), 400
            excel_file = request.files['ipPlanUpload']
            if not _allowed_file(excel_file.filename):
                return jsonify({'success': False, 'error': 'არასწორი ფაილის ტიპი Excel-ისთვის'}), 400
            temp_excel = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(excel_file.filename))
            excel_file.save(temp_excel)
            file_paths['transmissionExcel'] = temp_excel

        # Extract parameters from both XMLs
        try:
            parser = XMLParser()

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
                return jsonify({'success': False, 'error': 'არსებული XML ფაილში btsName ვერ მოიძებნა'}), 400
            if not reference_bts_name:
                return jsonify({'success': False, 'error': 'Reference XML ფაილში btsName ვერ მოიძებნა'}), 400

        except Exception as e:
            logger.error(f"Error extracting station parameters: {str(e)}")
            return jsonify({'success': False, 'error': f'სადგურის პარამეტრების ამოღების შეცდომა: {str(e)}'}), 500

        generator = ModernizationGenerator()
        output_filename, debug_log, extra = generator.generate(
            station_name=station_name,
            existing_xml_path=file_paths['existingXml'],
            reference_5g_xml_path=file_paths['reference5gXml'],
            transmission_excel_path=file_paths['transmissionExcel'],
            output_folder=current_app.config['GENERATED_FOLDER'],
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

        # Clean up temporary files
        if 'existingXml' in file_paths and file_paths['existingXml'].startswith(current_app.config['UPLOAD_FOLDER']):
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
            'message': 'Modernization configuration generated successfully',
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
                'ip_plan_lookup_station': (extra.get('ip_plan_lookup') if extra else None),
                'ip_plan_found': (extra.get('ip_plan_found') if extra else None),
                'rollout_overrides': {
                    'id': rollout_id_override,
                    'name': rollout_name_override,
                    'tac': rollout_tac_override
                } if mode == 'rollout' else None
            },
            'debug_log': debug_log
        }

        try:
            if extra and not extra.get('ip_plan_found', True):
                resp['warnings'] = {
                    'ip_plan': f"IP Plan not found for station '{extra.get('ip_plan_lookup','')}'. VLAN/IP/GW replacements were skipped."
                }
        except Exception as e:
            logger.warning(f"Could not build IP Plan warning: {e}")

        return jsonify(resp)

    except Exception as e:
        logger.error(f"Error in modernization: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/modernization/inspect', methods=['POST'])
def modernization_inspect():
    """Inspect uploaded existing XML to extract hardware/radio info and suggest a Reference 5G XML."""
    try:
        if 'existingXml' not in request.files or request.files['existingXml'].filename == '':
            return jsonify({'success': False, 'error': 'existingXml file is required'}), 400

        xml_file = request.files['existingXml']
        if not _allowed_file(xml_file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type for existing XML'}), 400

        region = (request.form.get('region') or '').strip()
        if region not in ['East', 'West']:
            region = 'East'

        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(xml_file.filename))
        xml_file.save(temp_path)

        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(temp_path, parser)
            viewer = XMLViewer()
            info = viewer.extract_configuration_data(tree)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        station = info.get('stationInfo', {})
        radio = info.get('radioInfo', {})
        hardware = info.get('hardwareInfo', {})
        has2g = station.get('has2G', False)
        has3g = station.get('has3G', False)
        has4g = station.get('has4G', False)
        has5g = station.get('has5G', False)
        sector_count = radio.get('sectorCount', 0)

        radio_modules = hardware.get('radioModules', [])
        radio_summary = hardware.get('radioModuleSummary', '')
        radio_code_set = getattr(XMLViewer, 'RADIO_MODULE_CODES', {'AHEGA', 'AHEGB', 'AWHQA'})

        models = []
        for rm in radio_modules:
            m = rm.get('model', '')
            if m and m not in models:
                models.append(m)

        model_codes = []
        code_map = XMLViewer.MODEL_CODE_MAP if hasattr(XMLViewer, 'MODEL_CODE_MAP') else {}
        for m in hardware.get('modules', []):
            code = (m.get('productCode') or '').strip()
            mapped = code_map.get(code, '')
            if mapped in radio_code_set and code not in model_codes:
                model_codes.append(code)

        # Collect reference XMLs from region folder
        base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
        target_dir = os.path.join(base_dir, region)
        files = []
        try:
            for f in os.listdir(target_dir):
                if f.lower().endswith('.xml') and not f.startswith('.') and not f.startswith('~'):
                    path = os.path.join(target_dir, f)
                    if os.path.isfile(path):
                        files.append(f)
        except OSError as e:
            logger.warning(f"Could not list reference XMLs in {target_dir}: {e}")
        if not files:
            for fallback in ['East', 'West']:
                if fallback == region:
                    continue
                try:
                    for f in os.listdir(os.path.join(base_dir, fallback)):
                        if f.lower().endswith('.xml') and not f.startswith('.') and not f.startswith('~'):
                            path = os.path.join(base_dir, fallback, f)
                            if os.path.isfile(path):
                                files.append(f)
                    if files:
                        break
                except OSError as e:
                    logger.warning(f"Could not list fallback region {fallback}: {e}")

        # Match by sector, model
        sector_token = f'S{sector_count}' if sector_count in [2, 3, 4] else None
        model_candidates = {m.upper() for m in models}
        model_tokens = {'AHEGA', 'AHEGB', 'AZQL', 'AKQJ'}
        if model_candidates:
            model_tokens = model_tokens | model_candidates

        def score(fname):
            upper = fname.upper()
            s = 0
            if sector_token and sector_token.upper() in upper:
                s += 50
            for m in model_tokens:
                if m in upper and (not model_candidates or m in model_candidates):
                    s += 20
                    break
            return s

        scored = [(f, score(f)) for f in files]
        scored.sort(key=lambda x: -x[1])
        suggestion = scored[0][0] if scored and scored[0][1] >= 0 else (files[0] if files else None)

        if (not models) and suggestion:
            try:
                known = set(XMLViewer.MODEL_CODE_MAP.values()) if hasattr(XMLViewer, 'MODEL_CODE_MAP') else set()
            except Exception as e:
                logger.warning(f"Could not read MODEL_CODE_MAP: {e}")
                known = set()
            for tok in known:
                if tok and tok.upper() in (suggestion or '').upper():
                    models = [tok]
                    break

        return jsonify({
            'success': True,
            'data': {
                'has2G': has2g,
                'has3G': has3g,
                'has4G': has4g,
                'has5G': has5g,
                'sectorCount': sector_count,
                'models': models or model_codes,
                'modelCodes': model_codes,
                'radioModules': radio_modules,
                'radioModuleSummary': radio_summary,
                'suggestedReference': suggestion,
                'availableReferences': files
            }
        })
    except Exception as e:
        logger.error(f"Error in modernization_inspect: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/rollout', methods=['POST'])
def rollout():
    """Handle new rollout request — delegates to ModernizationGenerator in rollout mode"""
    try:
        station_name = request.form.get('stationName')
        if not station_name:
            return jsonify({'success': False, 'error': 'Station name is required'}), 400

        required_files = ['referenceXml', 'radioExcel', 'transmissionExcel']
        for file_key in required_files:
            if file_key not in request.files:
                return jsonify({'success': False, 'error': f'Missing required file: {file_key}'}), 400

        bts_id = request.form.get('btsId', '')
        temp_files = {}
        try:
            for file_key in required_files:
                file = request.files[file_key]
                if file.filename == '':
                    return jsonify({'success': False, 'error': f'No file selected for {file_key}'}), 400
                if not _allowed_file(file.filename):
                    return jsonify({'success': False, 'error': f'Invalid file type for {file_key}'}), 400
                temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(temp_path)
                temp_files[file_key] = temp_path

            ref_xml_path = temp_files['referenceXml']
            trans_excel_path = temp_files['transmissionExcel']

            parser = XMLParser()
            ref_tree = parser.parse_file(ref_xml_path)
            ref_bts_name = parser.extract_bts_name(ref_tree)

            generator = ModernizationGenerator()
            output_filename, debug_log, extra = generator.generate(
                station_name=station_name,
                existing_xml_path=ref_xml_path,
                reference_5g_xml_path=ref_xml_path,
                transmission_excel_path=trans_excel_path,
                output_folder=current_app.config['GENERATED_FOLDER'],
                existing_bts_name=ref_bts_name,
                reference_bts_name=ref_bts_name,
                ip_plan_excel_path=trans_excel_path,
                mode='rollout',
                rollout_overrides={
                    'id': bts_id or None,
                    'name': station_name or None,
                    'tac': None
                }
            )
            return jsonify({
                'success': True,
                'filename': output_filename,
                'message': 'New rollout configuration generated successfully',
                'debug_log': debug_log
            })
        finally:
            for path in temp_files.values():
                if os.path.exists(path):
                    os.unlink(path)
    except Exception as e:
        logger.error(f"Error in rollout: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
