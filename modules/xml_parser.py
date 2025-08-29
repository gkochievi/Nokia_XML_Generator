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
    
    def extract_4g_cells(self, tree):
        """Extract 4G cell parameters from LNCEL managedObjects"""
        try:
            logger.info("Starting 4G cell parameters extraction...")
            
            # Debug: Print root element info
            root = tree.getroot()
            logger.info(f"Root element: {root.tag}, attributes: {root.attrib}")
            
            # Try different XPath patterns for LNCEL (with namespace handling)
            xpath_patterns = [
                "//managedObject[@class='NOKLTE:LNCEL']",  # Standard
                "//*[local-name()='managedObject'][@class='NOKLTE:LNCEL']",  # Namespace-agnostic
                "//managedObject[contains(@class, 'LNCEL')]",  # Contains LNCEL
                "//*[local-name()='managedObject'][contains(@class, 'LNCEL')]",  # Namespace-agnostic contains
                "//managedObject[contains(@distName, 'LNCEL')]",  # DistName contains LNCEL
                "//*[local-name()='managedObject'][contains(@distName, 'LNCEL')]"  # Namespace-agnostic distName
            ]
            
            lncel_objects = []
            for pattern in xpath_patterns:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} elements")
                if found:
                    lncel_objects = found
                    logger.info(f"Successfully found LNCEL objects using pattern: {pattern}")
                    break
            
            if not lncel_objects:
                logger.info("No LNCEL managedObjects found - this station does not have 4G cells")
                return None
            
            logger.info(f"Found {len(lncel_objects)} LNCEL objects (4G cells)")
            
            # Extract parameters from each cell  
            cells_data = {}
            params_to_extract = ['phyCellId', 'tac']
            
            for i, lncel in enumerate(lncel_objects):
                dist_name = lncel.get('distName')
                class_name = lncel.get('class')
                logger.info(f"Processing LNCEL {i+1}: class='{class_name}', distName='{dist_name}'")
                
                # Extract cell ID from distName (LNCEL-XX)
                import re
                cell_id_match = re.search(r'LNCEL-(\d+)', dist_name) if dist_name else None
                if cell_id_match:
                    full_cell_id = f"LNCEL-{cell_id_match.group(1)}"
                    logger.info(f"Found cell ID: {full_cell_id}")
                else:
                    logger.warning(f"Could not extract cell ID from distName: '{dist_name}'")
                    continue
                
                # Extract parameters for this cell
                cell_params = {}
                for param_name in params_to_extract:
                    # phyCellId and tac are directly in LNCEL
                    param_patterns = [
                        f".//p[@name='{param_name}']",  # Standard
                        f".//*[local-name()='p'][@name='{param_name}']"  # Namespace-agnostic
                    ]
                    
                    param_element = None
                    for param_pattern in param_patterns:
                        found_param = lncel.xpath(param_pattern)
                        logger.info(f"Cell {full_cell_id} parameter '{param_name}' pattern '{param_pattern}' found {len(found_param)} elements")
                        if found_param:
                            param_element = found_param[0]
                            break
                    
                    if param_element is not None and param_element.text:
                        param_value = param_element.text.strip()
                        cell_params[param_name] = param_value
                        logger.info(f"Found {full_cell_id} {param_name}: '{param_value}'")
                    else:
                        logger.warning(f"Parameter {param_name} not found in cell {full_cell_id}")
                
                # Store cell data if we found any parameters
                if cell_params:
                    cells_data[full_cell_id] = cell_params
                    logger.info(f"Stored cell {full_cell_id} with {len(cell_params)} parameters")
                else:
                    logger.warning(f"No parameters found for cell {full_cell_id}")
            
            if cells_data:
                logger.info(f"Successfully extracted 4G cell data for {len(cells_data)} cells: {list(cells_data.keys())}")
                return cells_data
            else:
                logger.info("No 4G cell parameters found")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting 4G cell parameters: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_4g_rootseq(self, tree):
        """Extract rootSeqIndex parameters from LNCEL_FDD managedObjects"""
        try:
            logger.info("Starting 4G rootSeqIndex extraction...")
            
            # Debug: Print root element info
            root = tree.getroot()
            logger.info(f"Root element: {root.tag}, attributes: {root.attrib}")
            
            # Try different XPath patterns for LNCEL_FDD (with namespace handling)
            xpath_patterns = [
                "//managedObject[@class='NOKLTE:LNCEL_FDD']",  # Standard
                "//*[local-name()='managedObject'][@class='NOKLTE:LNCEL_FDD']",  # Namespace-agnostic
                "//managedObject[contains(@class, 'LNCEL_FDD')]",  # Contains LNCEL_FDD
                "//*[local-name()='managedObject'][contains(@class, 'LNCEL_FDD')]",  # Namespace-agnostic contains
                "//managedObject[contains(@distName, 'LNCEL_FDD')]",  # DistName contains LNCEL_FDD
                "//*[local-name()='managedObject'][contains(@distName, 'LNCEL_FDD')]"  # Namespace-agnostic distName
            ]
            
            lncel_fdd_objects = []
            for pattern in xpath_patterns:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} LNCEL_FDD elements")
                if found:
                    lncel_fdd_objects = found
                    logger.info(f"Successfully found LNCEL_FDD objects using pattern: {pattern}")
                    break
            
            if not lncel_fdd_objects:
                logger.info("No LNCEL_FDD managedObjects found - this station does not have 4G FDD cells")
                return None
            
            logger.info(f"Found {len(lncel_fdd_objects)} LNCEL_FDD objects")
            
            # Extract rootSeqIndex from each LNCEL_FDD
            rootseq_data = {}
            
            for i, lncel_fdd in enumerate(lncel_fdd_objects):
                dist_name = lncel_fdd.get('distName')
                class_name = lncel_fdd.get('class')
                logger.info(f"Processing LNCEL_FDD {i+1}: class='{class_name}', distName='{dist_name}'")
                
                # Extract cell ID from distName (LNCEL-XX)
                # distName example: "MRBTS-90134/LNBTS-90134/LNCEL-11/LNCEL_FDD-0"
                import re
                cell_id_match = re.search(r'LNCEL-(\d+)', dist_name) if dist_name else None
                if cell_id_match:
                    full_cell_id = f"LNCEL-{cell_id_match.group(1)}"
                    logger.info(f"Found cell ID: {full_cell_id}")
                else:
                    logger.warning(f"Could not extract cell ID from distName: '{dist_name}'")
                    continue
                
                # Find rootSeqIndex parameter (with namespace handling)
                param_patterns = [
                    ".//p[@name='rootSeqIndex']",  # Standard
                    ".//*[local-name()='p'][@name='rootSeqIndex']"  # Namespace-agnostic
                ]
                
                param_element = None
                for param_pattern in param_patterns:
                    found_param = lncel_fdd.xpath(param_pattern)
                    logger.info(f"Cell {full_cell_id} rootSeqIndex pattern '{param_pattern}' found {len(found_param)} elements")
                    if found_param:
                        param_element = found_param[0]
                        break
                
                if param_element is not None and param_element.text:
                    param_value = param_element.text.strip()
                    rootseq_data[full_cell_id] = {'rootSeqIndex': param_value}
                    logger.info(f"Found {full_cell_id} rootSeqIndex: '{param_value}'")
                else:
                    logger.warning(f"rootSeqIndex not found in cell {full_cell_id}")
            
            if rootseq_data:
                logger.info(f"Successfully extracted rootSeqIndex data for {len(rootseq_data)} cells: {list(rootseq_data.keys())}")
                return rootseq_data
            else:
                logger.info("No rootSeqIndex parameters found")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting 4G rootSeqIndex: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_5g_nrcells(self, tree):
        """Extract 5G physCellId parameters from NRCELL managedObjects"""
        try:
            logger.info("Starting 5G NRCELL physCellId extraction...")
            
            # Debug: Print root element info
            root = tree.getroot()
            logger.info(f"Root element: {root.tag}, attributes: {root.attrib}")
            
            # Try different XPath patterns for NRCELL (with namespace handling)
            xpath_patterns = [
                "//managedObject[@class='com.nokia.srbts.nrbts:NRCELL']",  # Standard
                "//*[local-name()='managedObject'][@class='com.nokia.srbts.nrbts:NRCELL']",  # Namespace-agnostic
                "//managedObject[contains(@class, 'NRCELL')]",  # Contains NRCELL
                "//*[local-name()='managedObject'][contains(@class, 'NRCELL')]",  # Namespace-agnostic contains
                "//managedObject[contains(@distName, 'NRCELL')]",  # DistName contains NRCELL
                "//*[local-name()='managedObject'][contains(@distName, 'NRCELL')]"  # Namespace-agnostic distName
            ]
            
            nrcell_objects = []
            for pattern in xpath_patterns:
                found = tree.xpath(pattern)
                logger.info(f"XPath '{pattern}' found {len(found)} NRCELL elements")
                if found:
                    nrcell_objects = found
                    logger.info(f"Successfully found NRCELL objects using pattern: {pattern}")
                    break
            
            if not nrcell_objects:
                logger.info("No NRCELL managedObjects found - this station does not have 5G cells")
                return None
            
            logger.info(f"Found {len(nrcell_objects)} NRCELL objects")
            
            # Extract physCellId from each NRCELL
            nrcell_data = {}
            
            for i, nrcell in enumerate(nrcell_objects):
                dist_name = nrcell.get('distName')
                class_name = nrcell.get('class')
                logger.info(f"Processing NRCELL {i+1}: class='{class_name}', distName='{dist_name}'")
                
                # Extract cell ID from distName (NRCELL-XXX)
                # distName example: "MRBTS-90134/NRBTS-90134/NRCELL-111"
                import re
                cell_id_match = re.search(r'NRCELL-(\d+)', dist_name) if dist_name else None
                if cell_id_match:
                    full_cell_id = f"NRCELL-{cell_id_match.group(1)}"
                    cell_number = cell_id_match.group(1)
                    
                    # Map NRCELL to corresponding LNCEL (last 2 digits)
                    # NRCELL-111 -> LNCEL-11, NRCELL-311 -> LNCEL-11, etc.
                    if len(cell_number) >= 2:
                        lncel_number = cell_number[-2:]  # Last 2 digits
                        mapped_lncel_id = f"LNCEL-{lncel_number}"
                        logger.info(f"Found 5G cell ID: {full_cell_id} → maps to 4G: {mapped_lncel_id}")
                    else:
                        logger.warning(f"Could not map NRCELL ID to LNCEL: '{cell_number}'")
                        continue
                else:
                    logger.warning(f"Could not extract cell ID from distName: '{dist_name}'")
                    continue
                
                # Find physCellId parameter (with namespace handling)
                param_patterns = [
                    ".//p[@name='physCellId']",  # Standard
                    ".//*[local-name()='p'][@name='physCellId']"  # Namespace-agnostic
                ]
                
                param_element = None
                for param_pattern in param_patterns:
                    found_param = nrcell.xpath(param_pattern)
                    logger.info(f"Cell {full_cell_id} physCellId pattern '{param_pattern}' found {len(found_param)} elements")
                    if found_param:
                        param_element = found_param[0]
                        break
                
                if param_element is not None and param_element.text:
                    param_value = param_element.text.strip()
                    # Use NRCELL ID as key instead of mapped LNCEL to avoid overwrites
                    nrcell_data[full_cell_id] = {
                        'mapped_lncel': mapped_lncel_id,
                        'physCellId': param_value
                    }
                    logger.info(f"Found {full_cell_id} physCellId: '{param_value}' (mapped to {mapped_lncel_id})")
                else:
                    logger.warning(f"physCellId not found in cell {full_cell_id}")
            
            if nrcell_data:
                logger.info(f"Successfully extracted 5G NRCELL data for {len(nrcell_data)} mapped cells: {list(nrcell_data.keys())}")
                return nrcell_data
            else:
                logger.info("No 5G NRCELL physCellId parameters found")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting 5G NRCELL physCellId: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def extract_network_parameters(self, tree):
        """Extract network parameters like NRX2LINK_TRUST and LNADJGNB"""
        network_params = {}
        
        try:
            logger.info("Starting network parameters extraction...")
            
            # Extract NRX2LINK_TRUST ipV4Addr (this should be LTE IP from IP Plan) (namespace-agnostic)
            nrx2link_objects = tree.xpath("//*[local-name()='managedObject' and contains(@class, 'NRX2LINK_TRUST')]")
            logger.info(f"Found {len(nrx2link_objects)} NRX2LINK_TRUST objects")
            for obj in nrx2link_objects:
                dist_name = obj.get('distName', '')
                ipv4_addr_elem = obj.find(".//*[local-name()='p'][@name='ipV4Addr']")
                if ipv4_addr_elem is not None and ipv4_addr_elem.text:
                    network_params['NRX2LINK_TRUST_ipV4Addr'] = {
                        'value': ipv4_addr_elem.text.strip(),
                        'distName': dist_name
                    }
                    logger.info(f"Found NRX2LINK_TRUST ipV4Addr: {ipv4_addr_elem.text.strip()}")
            
            # Extract LNADJGNB cPlaneIpAddr (this should be 5G IP from IP Plan) (namespace-agnostic)
            lnadjgnb_objects = tree.xpath("//*[local-name()='managedObject' and contains(@class, 'LNADJGNB')]")
            logger.info(f"Found {len(lnadjgnb_objects)} LNADJGNB objects")
            for obj in lnadjgnb_objects:
                dist_name = obj.get('distName', '')
                cplane_ip_elem = obj.find(".//*[local-name()='p'][@name='cPlaneIpAddr']")
                if cplane_ip_elem is not None and cplane_ip_elem.text:
                    network_params['LNADJGNB_cPlaneIpAddr'] = {
                        'value': cplane_ip_elem.text.strip(),
                        'distName': dist_name
                    }
                    logger.info(f"Found LNADJGNB cPlaneIpAddr: {cplane_ip_elem.text.strip()}")
            
            logger.info(f"Network parameters extraction completed. Found {len(network_params)} params: {list(network_params.keys())}")
            return network_params
            
        except Exception as e:
            logger.error(f"Error extracting network parameters: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}

    def extract_vlan_parameters(self, tree):
        """Extract VLAN parameters from VLANIF objects"""
        vlan_data = {}
        
        try:
            logger.info("Starting VLAN parameters extraction...")
            
            # Find all VLANIF managedObjects (namespace-agnostic)
            vlanif_objects = tree.xpath("//*[local-name()='managedObject' and contains(@class, 'VLANIF')]")
            logger.info(f"Found {len(vlanif_objects)} VLANIF objects")
            
            for i, obj in enumerate(vlanif_objects):
                dist_name = obj.get('distName', '')
                logger.info(f"Processing VLANIF {i+1}: distName={dist_name}")
                
                # Extract userLabel and vlanId (namespace-agnostic)
                user_label_elem = obj.find(".//*[local-name()='p'][@name='userLabel']")
                vlan_id_elem = obj.find(".//*[local-name()='p'][@name='vlanId']")
                
                logger.info(f"  userLabel elem: {user_label_elem is not None}")
                logger.info(f"  vlanId elem: {vlan_id_elem is not None}")
                
                if user_label_elem is not None:
                    logger.info(f"  userLabel text: '{user_label_elem.text}'")
                if vlan_id_elem is not None:
                    logger.info(f"  vlanId text: '{vlan_id_elem.text}'")
                
                if user_label_elem is not None and vlan_id_elem is not None:
                    user_label = user_label_elem.text.strip() if user_label_elem.text else None
                    vlan_id = vlan_id_elem.text.strip() if vlan_id_elem.text else None
                    
                    logger.info(f"  Processed: userLabel='{user_label}', vlanId='{vlan_id}'")
                    
                    if user_label and vlan_id:
                        # Map userLabel to standardized technology names
                        tech_mapping = {
                            'OAM': 'OAM',
                            'MGT': 'OAM',
                            '2G': '2G',
                            'GSM': '2G',
                            '3G': '3G',
                            'WCDMA': '3G',
                            '4G': '4G',
                            'LTE': '4G',
                            '5G': '5G',
                            'NR': '5G'
                        }
                        
                        tech_name = tech_mapping.get(user_label.upper(), user_label)
                        vlan_data[tech_name] = {
                            'vlanId': vlan_id,
                            'userLabel': user_label,
                            'distName': dist_name
                        }
                        logger.info(f"  Added VLAN: {tech_name} -> vlanId: {vlan_id}, userLabel: {user_label}")
                    else:
                        logger.warning(f"  Skipped VLANIF {i+1}: missing userLabel or vlanId")
                else:
                    logger.warning(f"  Skipped VLANIF {i+1}: missing userLabel or vlanId elements")
            
            logger.info(f"VLAN extraction completed. Found {len(vlan_data)} VLANs: {list(vlan_data.keys())}")
            return vlan_data
            
        except Exception as e:
            logger.error(f"Error extracting VLAN parameters: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}

    def extract_ip_parameters(self, tree):
        """Extract IP parameters from IPIF and IPADDRESSV4 objects, mapped by technology"""
        ip_data = {}
        
        try:
            logger.info("Starting IP parameters extraction...")
            
            # Collect IPIF objects to map userLabel -> technology and distName
            ipif_objects = tree.xpath("//*[local-name()='managedObject' and contains(@class, 'IPIF')]")
            logger.info(f"Found {len(ipif_objects)} IPIF objects")
            
            ipif_map = {}  # distName -> { userLabel, tech_name }
            for obj in ipif_objects:
                dist_name = obj.get('distName', '')
                user_label_elem = obj.find(".//*[local-name()='p'][@name='userLabel']")
                user_label = user_label_elem.text.strip() if user_label_elem is not None and user_label_elem.text else None
                if not dist_name or not user_label:
                    continue
                tech_mapping = {
                    'OAM': 'OAM', 'MGT': 'OAM',
                    '2G': '2G', 'GSM': '2G',
                    '3G': '3G', 'WCDMA': '3G',
                    '4G': '4G', 'LTE': '4G',
                    '5G': '5G', 'NR': '5G'
                }
                tech_name = tech_mapping.get(user_label.upper(), user_label)
                ipif_map[dist_name] = { 'userLabel': user_label, 'tech': tech_name }
            
            # Now collect IPADDRESSV4 objects and pair them with their IPIF via distName
            ipaddr_objects = tree.xpath("//*[local-name()='managedObject' and contains(@class, 'IPADDRESSV4')]")
            logger.info(f"Found {len(ipaddr_objects)} IPADDRESSV4 objects")
            
            for obj in ipaddr_objects:
                dist_name = obj.get('distName', '')
                if not dist_name:
                    continue
                # Parent IPIF DN is the part before '/IPADDRESSV4-'
                parent_ipif_dn = dist_name.split('/IPADDRESSV4-', 1)[0]
                if parent_ipif_dn not in ipif_map:
                    # Try alternative separators just in case
                    if '/IPADDRESSV4/' in dist_name:
                        parent_ipif_dn = dist_name.split('/IPADDRESSV4/', 1)[0]
                info = ipif_map.get(parent_ipif_dn)
                if not info:
                    continue
                
                local_ip_elem = obj.find(".//*[local-name()='p'][@name='localIpAddr']")
                prefix_len_elem = obj.find(".//*[local-name()='p'][@name='localIpPrefixLength']")
                gateway_elem = obj.find(".//*[local-name()='p'][@name='gateway']")
                
                local_ip = local_ip_elem.text.strip() if local_ip_elem is not None and local_ip_elem.text else None
                prefix_len = prefix_len_elem.text.strip() if prefix_len_elem is not None and prefix_len_elem.text else None
                gateway = gateway_elem.text.strip() if gateway_elem is not None and gateway_elem.text else None
                
                tech_name = info['tech']
                user_label = info['userLabel']
                if tech_name:
                    ip_data[tech_name] = {
                        'localIpAddr': local_ip,
                        'localIpPrefixLength': prefix_len,
                        'gateway': gateway,
                        'userLabel': user_label,
                        'distName': parent_ipif_dn
                    }
                    logger.info(f"Found IP config: {tech_name} -> IP: {local_ip}, Prefix: {prefix_len}, Gateway: {gateway}")
            
            logger.info(f"IP extraction completed. Found {len(ip_data)} IP configs: {list(ip_data.keys())}")
            return ip_data
            
        except Exception as e:
            logger.error(f"Error extracting IP parameters: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}

    def extract_routing_parameters(self, tree):
        """Extract IPv4 routing parameters from IPRT objects"""
        routing_data = {}
        
        try:
            logger.info("Starting routing parameters extraction...")
            
            # Find all IPRT managedObjects (IPv4 routing) (namespace-agnostic)
            iprt_objects = tree.xpath("//*[local-name()='managedObject' and contains(@class, 'IPRT')]")
            logger.info(f"Found {len(iprt_objects)} IPRT objects")
            
            for obj in iprt_objects:
                dist_name = obj.get('distName', '')
                
                # Extract routing parameters (namespace-agnostic)
                dest_ip_elem = obj.find(".//*[local-name()='p'][@name='destIpAddr']")
                prefix_len_elem = obj.find(".//*[local-name()='p'][@name='destIpPrefixLength']")
                gateway_elem = obj.find(".//*[local-name()='p'][@name='gateway']")
                
                if dest_ip_elem is not None and dest_ip_elem.text and gateway_elem is not None and gateway_elem.text:
                    dest_ip = dest_ip_elem.text.strip()
                    prefix_len = prefix_len_elem.text.strip() if prefix_len_elem is not None and prefix_len_elem.text else None
                    gateway = gateway_elem.text.strip()
                    
                    # Determine IPRT type from distName
                    iprt_type = 'IPRT-1'  # Default
                    if 'IPRT-2' in dist_name:
                        iprt_type = 'IPRT-2'
                    elif 'NR' in dist_name:
                        iprt_type = 'IPRT-2 NR'
                    
                    if iprt_type not in routing_data:
                        routing_data[iprt_type] = {}
                    
                    # Use first two octets as key for mapping
                    ip_prefix = '.'.join(dest_ip.split('.')[:2])
                    routing_data[iprt_type][ip_prefix] = {
                        'destIpAddr': dest_ip,
                        'destIpPrefixLength': prefix_len,
                        'gateway': gateway,
                        'distName': dist_name
                    }
                    logger.info(f"Found routing: {iprt_type} {ip_prefix} -> Gateway: {gateway}")
            
            logger.info(f"Routing extraction completed. Found {len(routing_data)} IPRT types: {list(routing_data.keys())}")
            return routing_data
            
        except Exception as e:
            logger.error(f"Error extracting routing parameters: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}