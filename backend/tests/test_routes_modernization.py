"""API tests for routes/modernization.py — inspect endpoint."""
import io
import os
import pytest
from conftest import MINIMAL_NOKIA_XML


class TestModernizationInspect:
    def test_inspect_valid_xml(self, client, example_dir):
        # Put a reference XML in East so suggestion logic has something to match
        ref_path = os.path.join(example_dir, 'East', '8T8R-AHEGA-AZQL-S2.xml')
        with open(ref_path, 'w') as f:
            f.write(MINIMAL_NOKIA_XML)

        data = {
            'existingXml': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'existing.xml'),
            'region': 'East',
        }
        resp = client.post('/api/modernization/inspect', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True
        assert 'data' in result
        d = result['data']
        assert 'sectorCount' in d
        assert 'has4G' in d
        assert 'has5G' in d
        assert isinstance(d.get('availableReferences'), list)

    def test_inspect_no_file(self, client):
        resp = client.post('/api/modernization/inspect')
        result = resp.get_json()
        assert result['success'] is False

    def test_inspect_invalid_extension(self, client):
        data = {
            'existingXml': (io.BytesIO(b'fake'), 'bad.txt'),
            'region': 'East',
        }
        resp = client.post('/api/modernization/inspect', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is False

    def test_inspect_defaults_region_to_east(self, client):
        data = {
            'existingXml': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'test.xml'),
        }
        resp = client.post('/api/modernization/inspect', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True


class TestModernizationGenerate:
    def _setup_files(self, example_dir):
        """Put reference XML and a fake IP plan in place."""
        ref_path = os.path.join(example_dir, 'East', 'ref.xml')
        with open(ref_path, 'w') as f:
            f.write(MINIMAL_NOKIA_XML)

        ip_dir = os.path.join(example_dir, 'IP')
        ip_path = os.path.join(ip_dir, 'plan.xlsx')
        # Create minimal valid xlsx using openpyxl
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['Station_Name', 'OM_IP', '2G_IP', 'Gateway', 'VLAN', 'Subnet_Mask'])
        ws.append(['Test_Station_Alpha', '10.0.0.1', '10.0.0.2', '10.0.0.254', '100', '255.255.255.0'])
        wb.save(ip_path)

        return ref_path, ip_path

    def test_generate_missing_station_name(self, client, example_dir):
        resp = client.post('/api/modernization', data={}, content_type='multipart/form-data')
        assert resp.status_code == 400
        result = resp.get_json()
        assert result['success'] is False

    def test_generate_missing_existing_xml(self, client, example_dir):
        data = {'stationName': 'Test', 'mode': 'modernization', 'region': 'East'}
        resp = client.post('/api/modernization', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_generate_modernization_with_uploads(self, client, example_dir, generated_dir):
        self._setup_files(example_dir)
        data = {
            'stationName': 'New_Station',
            'mode': 'modernization',
            'region': 'East',
            'existingXml': (io.BytesIO(MINIMAL_NOKIA_XML.encode()), 'existing.xml'),
            'reference5gXmlSelection': 'ref.xml',
            'ipPlanSelection': 'plan.xlsx',
        }
        resp = client.post('/api/modernization', data=data, content_type='multipart/form-data')
        result = resp.get_json()
        assert result['success'] is True
        assert 'filename' in result
        assert 'details' in result
        # Verify file was actually created
        assert os.path.exists(os.path.join(generated_dir, result['filename']))


class TestRolloutEndpoint:
    def test_rollout_missing_station(self, client):
        resp = client.post('/api/rollout', data={}, content_type='multipart/form-data')
        assert resp.status_code == 400
