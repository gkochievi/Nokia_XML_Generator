"""API tests for routes/extraction.py — parameter extraction endpoints."""
import io
import os
import pytest
from conftest import MINIMAL_NOKIA_XML


class TestExtractFromUpload:
    def test_extract_bts_name(self, client):
        data = {'xmlFile': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml')}
        resp = client.post('/api/extract-bts-name', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True
        assert result['btsName'] == 'Test_Station_Alpha'

    def test_extract_bts_id(self, client):
        data = {'xmlFile': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml')}
        resp = client.post('/api/extract-bts-id', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True
        assert result['btsId'] == '12345'

    def test_extract_sctp_port(self, client):
        data = {'xmlFile': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml')}
        resp = client.post('/api/extract-sctp-port', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True
        assert result['sctpPortMin'] == '2905'

    def test_extract_4g_cells(self, client):
        data = {'xmlFile': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml')}
        resp = client.post('/api/extract-4g-cells', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True
        assert result['cells4g'] is not None

    def test_extract_4g_rootseq(self, client):
        data = {'xmlFile': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml')}
        resp = client.post('/api/extract-4g-rootseq', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True

    def test_extract_5g_nrcells(self, client):
        data = {'xmlFile': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml')}
        resp = client.post('/api/extract-5g-nrcells', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True

    def test_extract_unknown_type(self, client):
        data = {'xmlFile': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml')}
        resp = client.post('/api/extract-bogus-type', data=data, content_type='multipart/form-data')
        assert resp.status_code == 404

    def test_extract_no_file(self, client):
        resp = client.post('/api/extract-bts-name')
        result = resp.get_json()
        assert result['success'] is False

    def test_extract_non_xml(self, client):
        data = {'xmlFile': (io.BytesIO(b'not xml'), 'test.txt')}
        resp = client.post('/api/extract-bts-name', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is False


class TestExtractFromExample:
    def test_extract_from_example(self, client, example_dir):
        east = os.path.join(example_dir, 'East')
        with open(os.path.join(east, 'sample.xml'), 'w') as f:
            f.write(MINIMAL_NOKIA_XML)
        resp = client.get('/api/example-files/extract-bts-name/sample.xml?region=East')
        result = resp.get_json()
        assert result['success'] is True
        assert result['btsName'] == 'Test_Station_Alpha'

    def test_extract_from_missing_example(self, client):
        resp = client.get('/api/example-files/extract-bts-name/nope.xml?region=East')
        assert resp.status_code == 404
