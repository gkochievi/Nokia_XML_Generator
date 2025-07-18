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
    
    def extract_bts_name(self, tree):
        """Extract btsName from MRBTS managedObject"""
        try:
            logger.info("Starting btsName extraction...")
            
            # Debug: Print root element info
            root = tree.getroot()
            logger.info(f"Root element: {root.tag}, attributes: {root.attrib}")
            logger.info(f"Root namespaces: {root.nsmap if hasattr(root, 'nsmap') else 'N/A'}")
            
            # Get the default namespace
            default_ns = None
            if hasattr(root, 'nsmap') and root.nsmap:
                default_ns = root.nsmap.get(None)
                logger.info(f"Default namespace: {default_ns}")
            
            # Debug: Find all managedObject elements first (with and without namespace)
            xpath_patterns_for_finding = [
                "//managedObject",  # Without namespace
                "//*[local-name()='managedObject']"  # With any namespace
            ]
            
            all_managed_objects = []
            for pattern in xpath_patterns_for_finding:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} elements")
                if found:
                    all_managed_objects = found
                    break
            
            logger.info(f"Found {len(all_managed_objects)} managedObject elements total")
            
            for i, obj in enumerate(all_managed_objects):
                class_attr = obj.get('class')
                dist_name = obj.get('distName')
                logger.info(f"ManagedObject {i+1}: class='{class_attr}', distName='{dist_name}'")
            
            # Try different XPath patterns for MRBTS (with namespace handling)
            xpath_patterns = [
                "//managedObject[@class='com.nokia.srbts:MRBTS']",  # Standard
                "//*[local-name()='managedObject'][@class='com.nokia.srbts:MRBTS']",  # Namespace-agnostic
                "//managedObject[contains(@class, 'MRBTS')]",  # Contains MRBTS
                "//*[local-name()='managedObject'][contains(@class, 'MRBTS')]",  # Namespace-agnostic contains
                "//managedObject[contains(@distName, 'MRBTS')]",  # DistName contains MRBTS
                "//*[local-name()='managedObject'][contains(@distName, 'MRBTS')]"  # Namespace-agnostic distName
            ]
            
            mrbts_objects = []
            for pattern in xpath_patterns:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} elements")
                if found:
                    mrbts_objects = found
                    logger.info(f"Successfully found MRBTS objects using pattern: {pattern}")
                    break
            
            if not mrbts_objects:
                logger.warning("No MRBTS managedObject found with any pattern")
                return None
                
            # Get the first MRBTS object
            mrbts = mrbts_objects[0]
            logger.info(f"Using MRBTS object: class='{mrbts.get('class')}', distName='{mrbts.get('distName')}'")
            
            # Debug: Find all p elements in this MRBTS (with namespace handling)
            p_patterns = [
                ".//p",  # Standard
                ".//*[local-name()='p']"  # Namespace-agnostic
            ]
            
            all_p_elements = []
            for p_pattern in p_patterns:
                found_p = mrbts.xpath(p_pattern)
                logger.info(f"Pattern '{p_pattern}' found {len(found_p)} <p> elements in MRBTS")
                if found_p:
                    all_p_elements = found_p
                    break
            
            logger.info(f"Found {len(all_p_elements)} <p> elements in MRBTS total")
            
            for p in all_p_elements:
                name_attr = p.get('name')
                text_value = p.text
                logger.info(f"Parameter: name='{name_attr}', value='{text_value}'")
            
            # Find btsName parameter (with namespace handling)
            bts_name_patterns = [
                ".//p[@name='btsName']",  # Standard
                ".//*[local-name()='p'][@name='btsName']"  # Namespace-agnostic
            ]
            
            bts_name_param = None
            for bts_pattern in bts_name_patterns:
                found_bts = mrbts.xpath(bts_pattern)
                logger.info(f"btsName pattern '{bts_pattern}' found {len(found_bts)} elements")
                if found_bts:
                    bts_name_param = found_bts[0]
                    break
            
            if bts_name_param is not None and bts_name_param.text:
                logger.info(f"Found btsName: '{bts_name_param.text.strip()}'")
                return bts_name_param.text.strip()
            else:
                logger.warning("btsName parameter not found or empty")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting btsName: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_bts_id(self, tree):
        """Extract BTS ID from MRBTS managedObject distName attribute"""
        try:
            logger.info("Starting BTS ID extraction...")
            
            # Debug: Print root element info
            root = tree.getroot()
            logger.info(f"Root element: {root.tag}, attributes: {root.attrib}")
            
            # Try different XPath patterns for MRBTS (with namespace handling)
            xpath_patterns = [
                "//managedObject[@class='com.nokia.srbts:MRBTS']",  # Standard
                "//*[local-name()='managedObject'][@class='com.nokia.srbts:MRBTS']",  # Namespace-agnostic
                "//managedObject[contains(@class, 'MRBTS')]",  # Contains MRBTS
                "//*[local-name()='managedObject'][contains(@class, 'MRBTS')]",  # Namespace-agnostic contains
                "//managedObject[contains(@distName, 'MRBTS')]",  # DistName contains MRBTS
                "//*[local-name()='managedObject'][contains(@distName, 'MRBTS')]"  # Namespace-agnostic distName
            ]
            
            mrbts_objects = []
            for pattern in xpath_patterns:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} elements")
                if found:
                    mrbts_objects = found
                    logger.info(f"Successfully found MRBTS objects using pattern: {pattern}")
                    break
            
            if not mrbts_objects:
                logger.warning("No MRBTS managedObject found with any pattern")
                return None
                
            # Get the first MRBTS object
            mrbts = mrbts_objects[0]
            dist_name = mrbts.get('distName')
            logger.info(f"Using MRBTS object: class='{mrbts.get('class')}', distName='{dist_name}'")
            
            if dist_name:
                # Extract BTS ID from distName like "MRBTS-90217"
                import re
                match = re.search(r'MRBTS-(\d+)', dist_name)
                if match:
                    bts_id = match.group(1)
                    logger.info(f"Found BTS ID: '{bts_id}'")
                    return bts_id
                else:
                    logger.warning(f"Could not extract BTS ID from distName: '{dist_name}'")
                    return None
            else:
                logger.warning("distName attribute not found in MRBTS object")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting BTS ID: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_sctp_port_min(self, tree):
        """Extract sctpPortMin from WNBTS managedObject cPlaneList"""
        try:
            logger.info("Starting sctpPortMin extraction...")
            
            # Debug: Print root element info
            root = tree.getroot()
            logger.info(f"Root element: {root.tag}, attributes: {root.attrib}")
            
            # Try different XPath patterns for WNBTS (with namespace handling)
            xpath_patterns = [
                "//managedObject[@class='com.nokia.srbts.wcdma:WNBTS']",  # Standard
                "//*[local-name()='managedObject'][@class='com.nokia.srbts.wcdma:WNBTS']",  # Namespace-agnostic
                "//managedObject[contains(@class, 'WNBTS')]",  # Contains WNBTS
                "//*[local-name()='managedObject'][contains(@class, 'WNBTS')]",  # Namespace-agnostic contains
                "//managedObject[contains(@distName, 'WNBTS')]",  # DistName contains WNBTS
                "//*[local-name()='managedObject'][contains(@distName, 'WNBTS')]"  # Namespace-agnostic distName
            ]
            
            wnbts_objects = []
            for pattern in xpath_patterns:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} elements")
                if found:
                    wnbts_objects = found
                    logger.info(f"Successfully found WNBTS objects using pattern: {pattern}")
                    break
            
            if not wnbts_objects:
                logger.info("No WNBTS managedObject found - this is normal for 5G-only stations")
                return None
                
            # Get the first WNBTS object
            wnbts = wnbts_objects[0]
            dist_name = wnbts.get('distName')
            logger.info(f"Using WNBTS object: class='{wnbts.get('class')}', distName='{dist_name}'")
            
            # Find cPlaneList (with namespace handling)
            cplane_patterns = [
                ".//list[@name='cPlaneList']",  # Standard
                ".//*[local-name()='list'][@name='cPlaneList']"  # Namespace-agnostic
            ]
            
            cplane_list = None
            for cplane_pattern in cplane_patterns:
                found_cplane = wnbts.xpath(cplane_pattern)
                logger.info(f"cPlaneList pattern '{cplane_pattern}' found {len(found_cplane)} elements")
                if found_cplane:
                    cplane_list = found_cplane[0]
                    break
            
            if cplane_list is None:
                logger.info("cPlaneList not found in WNBTS object - may not have 3G configuration")
                return None
            
            # Find items in cPlaneList (with namespace handling)
            item_patterns = [
                ".//item",  # Standard
                ".//*[local-name()='item']"  # Namespace-agnostic
            ]
            
            items = []
            for item_pattern in item_patterns:
                found_items = cplane_list.xpath(item_pattern)
                logger.info(f"Item pattern '{item_pattern}' found {len(found_items)} elements")
                if found_items:
                    items = found_items
                    break
            
            logger.info(f"Found {len(items)} items in cPlaneList")
            
            # Look for sctpPortMin in items
            for i, item in enumerate(items):
                logger.info(f"Checking item {i+1}")
                
                # Find sctpPortMin parameter (with namespace handling)
                sctp_patterns = [
                    ".//p[@name='sctpPortMin']",  # Standard
                    ".//*[local-name()='p'][@name='sctpPortMin']"  # Namespace-agnostic
                ]
                
                sctp_param = None
                for sctp_pattern in sctp_patterns:
                    found_sctp = item.xpath(sctp_pattern)
                    logger.info(f"sctpPortMin pattern '{sctp_pattern}' found {len(found_sctp)} elements in item {i+1}")
                    if found_sctp:
                        sctp_param = found_sctp[0]
                        break
                
                if sctp_param is not None and sctp_param.text:
                    sctp_port = sctp_param.text.strip()
                    logger.info(f"Found sctpPortMin: '{sctp_port}' in item {i+1}")
                    return sctp_port
                else:
                    logger.info(f"sctpPortMin not found in item {i+1}")
            
            logger.info("sctpPortMin parameter not found in any cPlaneList item - station may not have 3G")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting sctpPortMin: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_2g_parameters(self, tree):
        """Extract 2G parameters from GNBCF managedObject if 2G technology exists"""
        try:
            logger.info("Starting 2G parameters extraction...")
            
            # Debug: Print root element info
            root = tree.getroot()
            logger.info(f"Root element: {root.tag}, attributes: {root.attrib}")
            
            # Try different XPath patterns for GNBCF (with namespace handling)
            xpath_patterns = [
                "//managedObject[@class='com.nokia.srbts.gsm:GNBCF']",  # Standard
                "//*[local-name()='managedObject'][@class='com.nokia.srbts.gsm:GNBCF']",  # Namespace-agnostic
                "//managedObject[contains(@class, 'GNBCF')]",  # Contains GNBCF
                "//*[local-name()='managedObject'][contains(@class, 'GNBCF')]",  # Namespace-agnostic contains
                "//managedObject[contains(@distName, 'GNBCF')]",  # DistName contains GNBCF
                "//*[local-name()='managedObject'][contains(@distName, 'GNBCF')]"  # Namespace-agnostic distName
            ]
            
            gnbcf_objects = []
            for pattern in xpath_patterns:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} elements")
                if found:
                    gnbcf_objects = found
                    logger.info(f"Successfully found GNBCF objects using pattern: {pattern}")
                    break
            
            if not gnbcf_objects:
                logger.info("No GNBCF managedObject found - this station does not have 2G technology")
                return None
                
            # Get the first GNBCF object
            gnbcf = gnbcf_objects[0]
            dist_name = gnbcf.get('distName')
            logger.info(f"Using GNBCF object: class='{gnbcf.get('class')}', distName='{dist_name}'")
            
            # Parameters to extract
            params_to_extract = ['bcfId', 'bscId', 'mPlaneRemoteIpAddressOmuSig']
            extracted_params = {}
            
            for param_name in params_to_extract:
                # Find parameter (with namespace handling)
                param_patterns = [
                    f".//p[@name='{param_name}']",  # Standard
                    f".//*[local-name()='p'][@name='{param_name}']"  # Namespace-agnostic
                ]
                
                param_element = None
                for param_pattern in param_patterns:
                    found_param = gnbcf.xpath(param_pattern)
                    logger.info(f"Parameter '{param_name}' pattern '{param_pattern}' found {len(found_param)} elements")
                    if found_param:
                        param_element = found_param[0]
                        break
                
                if param_element is not None and param_element.text:
                    param_value = param_element.text.strip()
                    extracted_params[param_name] = param_value
                    logger.info(f"Found {param_name}: '{param_value}'")
                else:
                    logger.warning(f"Parameter {param_name} not found in GNBCF object")
            
            # Check if we have all required parameters
            if len(extracted_params) == len(params_to_extract):
                logger.info(f"Successfully extracted all 2G parameters: {extracted_params}")
                return extracted_params
            else:
                missing_params = set(params_to_extract) - set(extracted_params.keys())
                logger.warning(f"Missing 2G parameters: {missing_params}")
                return extracted_params if extracted_params else None
            
        except Exception as e:
            logger.error(f"Error extracting 2G parameters: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None