from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from modules.xml_parser import XMLParser
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('extraction', __name__)

# Maps URL param names to (parser_method, response_key, error_label)
EXTRACTORS = {
    'bts-name':    ('extract_bts_name',       'btsName',      'btsName'),
    'bts-id':      ('extract_bts_id',         'btsId',        'BTS ID'),
    'sctp-port':   ('extract_sctp_port_min',  'sctpPortMin',  'sctpPortMin'),
    '2g-params':   ('extract_2g_parameters',  'params2g',     '2G parameters'),
    '4g-cells':    ('extract_4g_cells',       'cells4g',      '4G cell parameters'),
    '4g-rootseq':  ('extract_4g_rootseq',     'rootseq4g',    '4G rootSeqIndex parameters'),
    '5g-nrcells':  ('extract_5g_nrcells',     'nrcells5g',    '5G NRCELL physCellId parameters'),
}


def _build_debug_info(tree):
    root = tree.getroot()
    debug_info = {
        'root_tag': root.tag,
        'root_attributes': dict(root.attrib),
        'namespaces': dict(root.nsmap) if hasattr(root, 'nsmap') else {},
        'managed_objects': [],
        'xpath_tests': {}
    }
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
    return debug_info


@bp.route('/api/extract-<param_type>', methods=['POST'])
def extract_from_upload(param_type):
    """Generic extraction from uploaded XML file.
    Handles: bts-name, bts-id, sctp-port, 2g-params, 4g-cells, 4g-rootseq, 5g-nrcells
    """
    if param_type not in EXTRACTORS:
        return jsonify({'error': f'Unknown extraction type: {param_type}'}), 404

    method_name, response_key, error_label = EXTRACTORS[param_type]

    try:
        if 'xmlFile' not in request.files:
            return jsonify({'error': 'No XML file provided'}), 400
        file = request.files['xmlFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name

        try:
            parser = XMLParser()
            tree = parser.parse_file(temp_path)
            debug_info = _build_debug_info(tree)
            result = getattr(parser, method_name)(tree)

            if result:
                return jsonify({'success': True, response_key: result, 'debug': debug_info})
            else:
                return jsonify({'success': False, 'error': f'{error_label} not found in XML file', 'debug': debug_info})
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error extracting {error_label}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/example-files/extract-<param_type>/<filename>', methods=['GET'])
def extract_from_example(param_type, filename):
    """Generic extraction from example_files XML.
    Handles: bts-name, bts-id, sctp-port, 2g-params, 4g-cells, 4g-rootseq, 5g-nrcells
    """
    if param_type not in EXTRACTORS:
        return jsonify({'error': f'Unknown extraction type: {param_type}'}), 404

    method_name, response_key, error_label = EXTRACTORS[param_type]

    try:
        filename = secure_filename(filename)
        region = (request.args.get('region') or '').strip()
        base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
        file_path = os.path.join(base_dir, region, filename) if region in ['East', 'West'] else os.path.join(base_dir, filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        if not filename.lower().endswith('.xml'):
            return jsonify({'error': 'File must be an XML file'}), 400

        parser = XMLParser()
        tree = parser.parse_file(file_path)
        result = getattr(parser, method_name)(tree)

        if result:
            return jsonify({'success': True, response_key: result, 'filename': filename})
        else:
            return jsonify({'success': False, 'error': f'{error_label} not found in XML file', 'filename': filename})

    except Exception as e:
        logger.error(f"Error extracting {error_label} from example file: {str(e)}")
        return jsonify({'error': str(e)}), 500
