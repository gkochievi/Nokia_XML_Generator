"""
Basic tests for Nokia WebEM Generator
"""

import unittest
import os
import tempfile
from modules.excel_parser import ExcelParser
from modules.xml_parser import XMLParser


class TestExcelParser(unittest.TestCase):
    """Test cases for Excel parser functionality"""
    
    def setUp(self):
        self.parser = ExcelParser()
    
    def test_parser_initialization(self):
        """Test that ExcelParser can be initialized"""
        self.assertIsNotNone(self.parser)
    
    def test_transmission_excel_parsing_empty_file(self):
        """Test parsing empty transmission Excel file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Create a minimal Excel file for testing
            import pandas as pd
            df = pd.DataFrame({
                'Station_Name': [],
                'OM_IP': [],
                '2G_IP': [],
                '3G_IP': [],
                '4G_IP': [],
                '5G_IP': [],
                'Gateway': [],
                'VLAN': [],
                'Subnet_Mask': []
            })
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            result = self.parser.parse_transmission_excel(tmp_path)
            self.assertEqual(result, {})
        finally:
            os.unlink(tmp_path)


class TestXMLParser(unittest.TestCase):
    """Test cases for XML parser functionality"""
    
    def setUp(self):
        self.parser = XMLParser()
    
    def test_parser_initialization(self):
        """Test that XMLParser can be initialized"""
        self.assertIsNotNone(self.parser)


if __name__ == '__main__':
    unittest.main()
