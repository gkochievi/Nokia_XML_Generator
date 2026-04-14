from flask import Blueprint, request, jsonify, current_app
from modules.excel_parser import ExcelParser
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('ip_plan', __name__)


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def _log_ip_plan_data(station_name, ip_plan_data, source_label=''):
    logger.info(f"=== IP PLAN PARSING DEBUG {source_label}===")
    logger.info(f"Station Name: {station_name}")
    logger.info(f"Found Station: {ip_plan_data.get('station_name')}")
    logger.info(f"Station Row: {ip_plan_data.get('station_row')}")

    technologies = ip_plan_data.get('technologies', {})
    for tech, data in technologies.items():
        logger.info(f"\n{tech} Technology:")
        logger.info(f"  VLAN ID: {data.get('vlanId')}")
        logger.info(f"  IP Address: {data.get('localIpAddr')}")
        logger.info(f"  Subnet Mask: {data.get('localIpPrefixLength')}")
        logger.info(f"  Gateway: {data.get('gateway')}")

    routing_rules = ip_plan_data.get('routing_rules', {})
    logger.info("\nRouting Rules:")
    for iprt, rules in routing_rules.items():
        logger.info(f"  {iprt}:")
        for prefix, gateway in rules.items():
            logger.info(f"    {prefix}.x.x -> {gateway}")

    logger.info(f"=== END IP PLAN DEBUG {source_label}===")


@bp.route('/api/parse-ip-plan', methods=['POST'])
def parse_ip_plan():
    """Parse IP Plan Excel file for network parameters (debug endpoint)"""
    try:
        station_name = request.form.get('stationName')
        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400

        if 'ipPlanFile' not in request.files:
            return jsonify({'error': 'IP Plan Excel file is required'}), 400

        ip_plan_file = request.files['ipPlanFile']
        if ip_plan_file.filename == '':
            return jsonify({'error': 'No IP Plan file selected'}), 400
        if not _allowed_file(ip_plan_file.filename):
            return jsonify({'error': 'Invalid IP Plan file format'}), 400

        ip_plan_temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                ip_plan_file.save(tmp.name)
                ip_plan_temp_path = tmp.name

            excel_parser = ExcelParser()
            ip_plan_data = excel_parser.parse_ip_plan_excel(ip_plan_temp_path, station_name)

            if ip_plan_data is None:
                return jsonify({
                    'success': False,
                    'error': f'Station "{station_name}" not found in IP Plan Excel file'
                }), 404

            _log_ip_plan_data(station_name, ip_plan_data)

            technologies = ip_plan_data.get('technologies', {})
            routing_rules = ip_plan_data.get('routing_rules', {})

            if ip_plan_data.get('success', True):
                return jsonify({
                    'success': True,
                    'data': ip_plan_data,
                    'debug': {
                        'station_name': station_name,
                        'found_station': ip_plan_data.get('station_name'),
                        'station_row': ip_plan_data.get('station_row'),
                        'technologies_found': list(technologies.keys()),
                        'routing_rules_count': len(routing_rules)
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
            if ip_plan_temp_path and os.path.exists(ip_plan_temp_path):
                os.unlink(ip_plan_temp_path)

    except Exception as e:
        logger.error(f"Error parsing IP Plan: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/parse-ip-plan-from-example', methods=['GET'])
def parse_ip_plan_from_example():
    """Parse IP Plan from example file (debug endpoint)"""
    try:
        station_name = request.args.get('station_name')
        filename = request.args.get('filename')

        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

        base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
        candidates = [
            os.path.join(base_dir, filename),
            os.path.join(base_dir, 'IP', filename),
            os.path.join(base_dir, 'Data', filename),
        ]
        file_path = None
        for candidate in candidates:
            if os.path.exists(candidate):
                file_path = candidate
                break
        if not file_path:
            return jsonify({'error': f'File {filename} not found in example files'}), 404

        excel_parser = ExcelParser()
        ip_plan_data = excel_parser.parse_ip_plan_excel(file_path, station_name)

        if ip_plan_data is None:
            return jsonify({
                'success': False,
                'error': f'Station "{station_name}" not found in IP Plan Excel file'
            }), 404

        _log_ip_plan_data(station_name, ip_plan_data, '(Example File) ')

        technologies = ip_plan_data.get('technologies', {})
        routing_rules = ip_plan_data.get('routing_rules', {})

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
