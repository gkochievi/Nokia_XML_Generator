"""API tests for routes/files.py — file listing, upload, download, delete."""
import io
import os
import pytest
from conftest import MINIMAL_NOKIA_XML


class TestListExampleXmlFiles:
    def test_list_empty(self, client):
        resp = client.get('/api/example-files/xml?region=East')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['files'] == []

    def test_list_with_files(self, client, example_dir):
        east = os.path.join(example_dir, 'East')
        for name in ['ref1.xml', 'ref2.xml', 'notes.txt']:
            with open(os.path.join(east, name), 'w') as f:
                f.write('<xml/>')
        resp = client.get('/api/example-files/xml?region=East')
        data = resp.get_json()
        assert data['success'] is True
        assert sorted(data['files']) == ['ref1.xml', 'ref2.xml']

    def test_list_without_region(self, client, example_dir):
        with open(os.path.join(example_dir, 'root.xml'), 'w') as f:
            f.write('<xml/>')
        resp = client.get('/api/example-files/xml')
        data = resp.get_json()
        assert data['success'] is True
        assert 'root.xml' in data['files']


class TestListExampleExcelFiles:
    def test_list_ip_category(self, client, example_dir):
        ip_dir = os.path.join(example_dir, 'IP')
        with open(os.path.join(ip_dir, 'plan.xlsx'), 'w') as f:
            f.write('fake')
        resp = client.get('/api/example-files/excel?category=ip')
        data = resp.get_json()
        assert data['success'] is True
        assert 'plan.xlsx' in data['files']

    def test_list_empty_category(self, client):
        resp = client.get('/api/example-files/excel?category=ip')
        data = resp.get_json()
        assert data['success'] is True
        assert data['files'] == []


class TestUploadExampleFile:
    def test_upload_xml_east(self, client, example_dir):
        data = {
            'file': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml'),
            'region': 'East',
        }
        resp = client.post('/api/example-files/upload', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True
        assert result['filename'] == 'test.xml'
        assert os.path.exists(os.path.join(example_dir, 'East', 'test.xml'))

    def test_upload_no_file(self, client):
        resp = client.post('/api/example-files/upload')
        assert resp.status_code == 400

    def test_upload_invalid_extension(self, client):
        data = {'file': (io.BytesIO(b'data'), 'bad.exe')}
        resp = client.post('/api/example-files/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400


class TestDeleteExampleFile:
    def test_delete_existing(self, client, example_dir):
        east = os.path.join(example_dir, 'East')
        path = os.path.join(east, 'todelete.xml')
        with open(path, 'w') as f:
            f.write('<xml/>')
        resp = client.post('/api/example-files/delete', json={
            'filename': 'todelete.xml', 'region': 'East'
        })
        data = resp.get_json()
        assert data['success'] is True
        assert not os.path.exists(path)

    def test_delete_nonexistent(self, client):
        resp = client.post('/api/example-files/delete', json={
            'filename': 'nope.xml', 'region': 'East'
        })
        assert resp.status_code == 404


class TestGeneratedFiles:
    def test_list_generated_empty(self, client):
        resp = client.get('/api/generated-files')
        data = resp.get_json()
        assert data['success'] is True
        assert data['files'] == []

    def test_list_generated_with_files(self, client, generated_dir):
        for name in ['out1.xml', 'out2.xml', 'readme.txt']:
            with open(os.path.join(generated_dir, name), 'w') as f:
                f.write('<xml/>')
        resp = client.get('/api/generated-files')
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['files']) == 2
        assert len(data['filesWithMtime']) == 2

    def test_delete_generated(self, client, generated_dir):
        path = os.path.join(generated_dir, 'del.xml')
        with open(path, 'w') as f:
            f.write('<xml/>')
        resp = client.post('/api/generated-files/delete', json={'filename': 'del.xml'})
        data = resp.get_json()
        assert data['success'] is True
        assert not os.path.exists(path)

    def test_clear_generated(self, client, generated_dir):
        for name in ['a.xml', 'b.xml']:
            with open(os.path.join(generated_dir, name), 'w') as f:
                f.write('<xml/>')
        resp = client.post('/api/generated-files/clear')
        data = resp.get_json()
        assert data['success'] is True
        assert data['count'] == 2


class TestDownloadAndPreview:
    def test_download_existing(self, client, generated_dir):
        path = os.path.join(generated_dir, 'dl.xml')
        with open(path, 'w') as f:
            f.write('<hello/>')
        resp = client.get('/api/download/dl.xml')
        assert resp.status_code == 200
        assert b'<hello/>' in resp.data

    def test_download_missing(self, client):
        resp = client.get('/api/download/nope.xml')
        assert resp.status_code == 404

    def test_preview_existing(self, client, generated_dir):
        path = os.path.join(generated_dir, 'pv.xml')
        with open(path, 'w') as f:
            f.write('<preview/>')
        resp = client.get('/api/preview/pv.xml')
        data = resp.get_json()
        assert data['success'] is True
        assert '<preview/>' in data['content']

    def test_preview_missing(self, client):
        resp = client.get('/api/preview/nope.xml')
        data = resp.get_json()
        assert data['success'] is False
