"""Unit tests for modules/xml_parser.py — core XML parsing logic."""
import pytest
from modules.xml_parser import XMLParser


class TestParseFile:
    def test_parse_valid_xml(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        assert tree is not None
        root = tree.getroot()
        assert root.tag == '{raml21.xsd}raml' or root.tag == 'raml'

    def test_parse_no_namespace_xml(self, sample_xml_no_ns_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_no_ns_file)
        assert tree is not None

    def test_parse_nonexistent_file(self):
        parser = XMLParser()
        with pytest.raises(Exception):
            parser.parse_file('/nonexistent/path.xml')

    def test_parse_invalid_xml(self, tmp_path):
        bad = tmp_path / "bad.xml"
        bad.write_text("this is not xml at all", encoding='utf-8')
        parser = XMLParser()
        with pytest.raises(Exception):
            parser.parse_file(str(bad))


class TestExtractBtsName:
    def test_extract_from_standard_xml(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        name = parser.extract_bts_name(tree)
        assert name == 'Test_Station_Alpha'

    def test_extract_from_no_namespace(self, sample_xml_no_ns_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_no_ns_file)
        name = parser.extract_bts_name(tree)
        assert name == 'NoNS_Station'

    def test_extract_returns_none_when_missing(self, tmp_path):
        xml = tmp_path / "empty.xml"
        xml.write_text(
            '<?xml version="1.0"?><raml><cmData><header/></cmData></raml>',
            encoding='utf-8',
        )
        parser = XMLParser()
        tree = parser.parse_file(str(xml))
        assert parser.extract_bts_name(tree) is None


class TestExtractBtsId:
    def test_extract_bts_id(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        bts_id = parser.extract_bts_id(tree)
        assert bts_id == '12345'

    def test_extract_bts_id_no_namespace(self, sample_xml_no_ns_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_no_ns_file)
        bts_id = parser.extract_bts_id(tree)
        assert bts_id == '99999'


class TestExtractSctpPortMin:
    def test_extract_sctp_port(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        port = parser.extract_sctp_port_min(tree)
        assert port == '2905'


class TestExtract4gCells:
    def test_extract_4g_cells(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        cells = parser.extract_4g_cells(tree)
        # Should find 2 LNCELs with physCellId
        assert cells is not None
        assert isinstance(cells, (list, dict))

    def test_extract_4g_rootseq(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        rootseq = parser.extract_4g_rootseq(tree)
        assert rootseq is not None


class TestExtract5gNrcells:
    def test_extract_5g_nrcells(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        nrcells = parser.extract_5g_nrcells(tree)
        assert nrcells is not None
        assert isinstance(nrcells, (list, dict))


class TestGetManagedObjects:
    """get_managed_objects uses simple XPath (no namespace handling),
    so it only works with namespace-free XML."""

    def test_get_all_objects(self, sample_xml_no_ns_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_no_ns_file)
        objects = parser.get_managed_objects(tree)
        assert len(objects) == 1  # no-ns fixture has 1 MRBTS

    def test_get_filtered_objects(self, sample_xml_no_ns_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_no_ns_file)
        objects = parser.get_managed_objects(tree, class_filter='com.nokia.srbts:MRBTS')
        assert len(objects) == 1
        assert objects[0].get('distName') == 'MRBTS-99999'

    def test_find_managed_objects_with_namespace(self, sample_xml_file):
        """_find_managed_objects handles namespace — use for namespaced XML."""
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        found = parser._find_managed_objects(tree, 'MRBTS')
        assert len(found) >= 1


class TestGetParameterValue:
    def test_get_existing_param(self, sample_xml_no_ns_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_no_ns_file)
        mrbts = parser.get_managed_objects(tree, class_filter='com.nokia.srbts:MRBTS')[0]
        assert parser.get_parameter_value(mrbts, 'btsName') == 'NoNS_Station'

    def test_get_missing_param(self, sample_xml_no_ns_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_no_ns_file)
        mrbts = parser.get_managed_objects(tree, class_filter='com.nokia.srbts:MRBTS')[0]
        assert parser.get_parameter_value(mrbts, 'nonExistentParam') is None


class TestHelperMethods:
    def test_find_managed_objects(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        found = parser._find_managed_objects(tree, 'MRBTS')
        assert len(found) >= 1

    def test_find_param(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        mrbts = parser._find_managed_objects(tree, 'MRBTS')[0]
        p = parser._find_param(mrbts, 'btsName')
        assert p is not None
        assert p.text.strip() == 'Test_Station_Alpha'

    def test_find_param_missing(self, sample_xml_file):
        parser = XMLParser()
        tree = parser.parse_file(sample_xml_file)
        mrbts = parser._find_managed_objects(tree, 'MRBTS')[0]
        assert parser._find_param(mrbts, 'doesNotExist') is None
