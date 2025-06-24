import xml.etree.ElementTree as ET
from lxml import etree
import logging

logger = logging.getLogger(__name__)

class XMLParser:
    """Parser for Nokia WebEM XML configuration files"""
    
    def __init__(self):
        self.namespaces = {
            'default': 'raml21.xsd',
            'nokia': 'com.nokia.srbts',
            'noklte': 'NOKLTE',
            'nrbts': 'com.nokia.srbts.nrbts',
            'eqm': 'com.nokia.srbts.eqm'
        }
    
    def parse_file(self, file_path):
        """Parse XML file and return tree"""
        try:
            # Use lxml for better namespace handling
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(file_path, parser)
            return tree
        except Exception as e:
            logger.error(f"Error parsing XML file: {str(e)}")
            raise
    
    def get_managed_objects(self, tree, class_filter=None):
        """Get all managedObject elements, optionally filtered by class"""
        xpath = "//managedObject"
        if class_filter:
            xpath += f"[@class='{class_filter}']"
        
        return tree.xpath(xpath)
    
    def get_parameter_value(self, managed_object, param_name):
        """Get parameter value from managedObject"""
        param = managed_object.find(f".//p[@name='{param_name}']")
        if param is not None:
            return param.text
        return None
    
    def get_list_values(self, managed_object, list_name):
        """Get list values from managedObject"""
        list_elem = managed_object.find(f".//list[@name='{list_name}']")
        if list_elem is not None:
            items = []
            for item in list_elem.findall(".//item"):
                item_data = {}
                for p in item.findall(".//p"):
                    item_data[p.get('name')] = p.text
                items.append(item_data)
            return items
        return []