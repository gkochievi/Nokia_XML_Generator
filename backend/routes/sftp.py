from flask import Blueprint, request, jsonify, send_file, after_this_request, current_app
import os
import re
import tempfile
import logging
import pandas as pd
import paramiko

logger = logging.getLogger(__name__)

bp = Blueprint('sftp', __name__)


@bp.route('/api/sftp-download', methods=['POST'])
def sftp_download():
    """Download backup XML from SFTP by ID or Name found in example_files/data.xlsx."""
    try:
        query = request.form.get('query') or (request.get_json(silent=True) or {}).get('query')
        if not query:
            return jsonify({'success': False, 'error': 'Missing parameter: query (ID or Name)'}), 400

        base_examples = current_app.config['EXAMPLE_FILES_FOLDER']
        candidates = [
            os.path.join(base_examples, 'BTSNaming', 'data.xlsx'),
            os.path.join(base_examples, 'data.xlsx'),
        ]
        excel_path = None
        for candidate in candidates:
            if os.path.exists(candidate):
                excel_path = candidate
                break
        if not excel_path:
            return jsonify({'success': False, 'error': 'Excel file not found in BTSNaming or example_files root'}), 404

        df = pd.read_excel(excel_path, engine='openpyxl')

        def normalize_name(value: str) -> str:
            text = str(value).strip().lower()
            text = text.replace('_', '-')
            text = re.sub(r'-+', '-', text)
            return text

        if 'Name' not in df.columns or 'ID' not in df.columns or 'Backup_Name' not in df.columns:
            return jsonify({'success': False, 'error': 'Excel must have columns: ID, Name, Backup_Name'}), 400
        df['_name_norm'] = df['Name'].apply(normalize_name)

        if str(query).isdigit():
            row = df[df['ID'] == int(query)]
        else:
            row = df[df['_name_norm'] == normalize_name(query)]

        if row.empty:
            return jsonify({'success': False, 'error': 'No match found in Excel for provided ID/Name'}), 404

        backup_name = str(row.iloc[0]['Backup_Name']).strip()
        base_name = str(row.iloc[0]['Name']).strip()
        base_id = str(row.iloc[0]['ID']).strip()
        if not backup_name:
            return jsonify({'success': False, 'error': 'Backup_Name missing for matched record'}), 404

        host = os.getenv('SFTP_HOST', '127.0.0.1')
        port = int(os.getenv('SFTP_PORT', '22'))
        username = os.getenv('SFTP_USERNAME', '')
        password = os.getenv('SFTP_PASSWORD', '')
        remote_dir = os.getenv('SFTP_REMOTE_DIR', '/')
        if not host or not username or not password:
            return jsonify({'success': False, 'error': 'SFTP credentials are not configured'}), 500

        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            remote_path = f"{remote_dir}/{backup_name}"
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
            except Exception as e:
                logger.debug(f"SFTP close error (non-critical): {e}")
            try:
                transport.close()
            except Exception as e:
                logger.debug(f"SFTP transport close error (non-critical): {e}")

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except OSError as e:
                logger.warning(f"Could not clean up temp file {tmp_path}: {e}")
            return response

        return send_file(tmp_path, as_attachment=True, download_name=download_filename)

    except FileNotFoundError:
        return jsonify({'success': False, 'error': f'Backup file {backup_name} not found on SFTP'}), 404
    except Exception as e:
        logger.error(f"SFTP download error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
