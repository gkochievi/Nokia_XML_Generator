from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('files', __name__)


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


# --- Example files ---

@bp.route('/api/example-files/xml', methods=['GET'])
def list_example_xml_files():
    """List all XML files in example_files directory"""
    try:
        region = (request.args.get('region') or '').strip()
        base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
        target_dir = base_dir
        if region in ['East', 'West']:
            target_dir = os.path.join(base_dir, region)
        try:
            files = [f for f in os.listdir(target_dir) if f.lower().endswith('.xml')]
        except OSError as e:
            logger.warning(f"Could not list XML files in {target_dir}: {e}")
            files = []
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        logger.error(f"Error listing example XML files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/example-files/excel', methods=['GET'])
def list_example_excel_files():
    """List all Excel files in example_files directory"""
    try:
        category = (request.args.get('category') or '').strip().lower()
        base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
        if category == 'ip':
            target_dir = os.path.join(base_dir, 'IP')
        elif category == 'data':
            target_dir = os.path.join(base_dir, 'Data')
        else:
            target_dir = base_dir
        try:
            files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.xlsx', '.xls'))]
        except OSError as e:
            logger.warning(f"Could not list Excel files in {target_dir}: {e}")
            files = []
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        logger.error(f"Error listing example Excel files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/example-files/upload', methods=['POST'])
def upload_example_file():
    """Upload a file to example_files directory"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    if not _allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. Only XML and Excel files are allowed.'}), 400

    try:
        filename = secure_filename(file.filename)
        base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
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
            'category': category if ext in ['xlsx', 'xls'] else None,
            'saved_to': saved_rel
        })
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/example-files/delete', methods=['POST'])
def delete_example_file_post():
    try:
        data = request.get_json(silent=True) or request.form
        filename = secure_filename((data.get('filename') or '').strip())
        region = (data.get('region') or '').strip()
        category = (data.get('category') or '').strip().lower()
        if not filename:
            return jsonify({'success': False, 'error': 'filename required'}), 400
        base_dir = current_app.config['EXAMPLE_FILES_FOLDER']
        if category in ['ip', 'data']:
            target_dir = os.path.join(base_dir, 'IP' if category == 'ip' else 'Data')
        elif region in ['East', 'West']:
            target_dir = os.path.join(base_dir, region)
        else:
            target_dir = base_dir
        file_path = os.path.join(target_dir, filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        os.remove(file_path)
        return jsonify({'success': True, 'deleted': filename})
    except Exception as e:
        logger.error(f"Error deleting example file (POST): {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Generated files ---

@bp.route('/api/generated-files', methods=['GET'])
def list_generated_files():
    try:
        gen_dir = current_app.config['GENERATED_FOLDER']
        files = []
        for f in os.listdir(gen_dir):
            if f.lower().endswith('.xml'):
                fpath = os.path.join(gen_dir, f)
                mtime = os.path.getmtime(fpath)
                size = os.path.getsize(fpath)
                files.append({'name': f, 'mtime': mtime, 'size': size})
        files.sort(key=lambda x: x['mtime'], reverse=True)
        return jsonify({'success': True, 'files': [f['name'] for f in files], 'filesWithMtime': files})
    except Exception as e:
        logger.error(f"Error listing generated files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/generated-files/delete', methods=['POST'])
def delete_generated_file_post():
    try:
        data = request.get_json(silent=True) or request.form
        filename = secure_filename((data.get('filename') or '').strip())
        if not filename:
            return jsonify({'success': False, 'error': 'filename required'}), 400
        gen_dir = current_app.config['GENERATED_FOLDER']
        path = os.path.join(gen_dir, filename)
        if not os.path.exists(path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        os.remove(path)
        return jsonify({'success': True, 'deleted': filename})
    except Exception as e:
        logger.error(f"Error deleting generated file (POST): {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/generated-files/clear', methods=['POST'])
def clear_generated_files():
    """Delete all generated XML files."""
    try:
        gen_dir = current_app.config['GENERATED_FOLDER']
        deleted = []
        for f in os.listdir(gen_dir):
            if not f.lower().endswith('.xml'):
                continue
            path = os.path.join(gen_dir, f)
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted.append(f)
            except Exception as e:
                logger.error(f"Error deleting generated file {f}: {str(e)}")
        return jsonify({'success': True, 'count': len(deleted), 'deleted': deleted})
    except Exception as e:
        logger.error(f"Error clearing generated files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Upload/download/preview ---

@bp.route('/api/download/<filename>')
def download_file(filename):
    """Download generated XML file"""
    try:
        file_path = os.path.join(current_app.config['GENERATED_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/preview/<filename>')
def preview_file(filename):
    """Preview generated XML file content"""
    try:
        file_path = os.path.join(current_app.config['GENERATED_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'success': True, 'content': content})
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error previewing file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/upload-xmls', methods=['POST'])
def upload_xmls():
    """Upload multiple XML files to uploads/ directory"""
    if 'xmlFiles' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400
    files = request.files.getlist('xmlFiles')
    saved = []
    for file in files:
        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            saved.append(filename)
    return jsonify({'success': True, 'saved': saved})


@bp.route('/api/list-xmls', methods=['GET'])
def list_xmls():
    """List all uploaded XML files"""
    files = [f for f in os.listdir(current_app.config['UPLOAD_FOLDER']) if f.lower().endswith('.xml')]
    return jsonify({'success': True, 'files': files})


@bp.route('/api/delete-xml/<filename>', methods=['DELETE'])
def delete_xml(filename):
    """Delete an uploaded XML file"""
    filename = secure_filename(filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True, 'deleted': filename})
    else:
        return jsonify({'success': False, 'error': 'File not found'}), 404
