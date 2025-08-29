import os
from lxml import etree
import logging
from .xml_parser import XMLParser
from .excel_parser import ExcelParser
from copy import deepcopy

logger = logging.getLogger(__name__)

class ModernizationGenerator:
    """Generator for 5G modernization configurations"""
    
    def __init__(self):
        self.xml_parser = XMLParser()
        self.excel_parser = ExcelParser()
    
    def generate(self, station_name, existing_xml_path, reference_5g_xml_path, 
                 transmission_excel_path, output_folder, existing_bts_name=None, reference_bts_name=None,
                 ip_plan_excel_path=None):
        """Generate 5G modernization configuration using template replacement approach"""
        try:
            logger.info("Starting 5G modernization generation...")
            logger.info(f"Station name: {station_name}")
            logger.info(f"Existing btsName: {existing_bts_name}")
            logger.info(f"Reference btsName: {reference_bts_name}")
            
            # Parse IP Plan data if provided
            ip_plan_data = None
            if ip_plan_excel_path:
                try:
                    ip_plan_data = self.excel_parser.parse_ip_plan_excel(ip_plan_excel_path, station_name)
                    if ip_plan_data:
                        logger.info(f"IP Plan data loaded successfully for station: {station_name}")
                        logger.info(f"IP Plan technologies: {list(ip_plan_data['technologies'].keys())}")
                    else:
                        logger.warning(f"No IP Plan data found for station: {station_name}")
                except Exception as e:
                    logger.error(f"Error parsing IP Plan Excel: {str(e)}")
                    ip_plan_data = None
            
            # Extract all parameters from both XML files
            existing_bts_id = None
            reference_bts_id = None
            existing_sctp_port = None
            reference_sctp_port = None
            existing_2g_params = None
            reference_2g_params = None
            existing_4g_cells = None
            reference_4g_cells = None
            existing_4g_rootseq = None
            reference_4g_rootseq = None
            existing_5g_nrcells = None
            reference_5g_nrcells = None
            existing_vlan_data = None
            reference_vlan_data = None
            existing_ip_data = None
            reference_ip_data = None
            existing_routing_data = None
            reference_routing_data = None
            existing_network_params = None
            reference_network_params = None
            
            try:
                if existing_xml_path:
                    existing_tree = self.xml_parser.parse_file(existing_xml_path)
                    existing_bts_id = self.xml_parser.extract_bts_id(existing_tree)
                    existing_sctp_port = self.xml_parser.extract_sctp_port_min(existing_tree)
                    existing_2g_params = self.xml_parser.extract_2g_parameters(existing_tree)
                    existing_4g_cells = self.xml_parser.extract_4g_cells(existing_tree)
                    existing_4g_rootseq = self.xml_parser.extract_4g_rootseq(existing_tree)
                    existing_5g_nrcells = self.xml_parser.extract_5g_nrcells(existing_tree)
                    # Extract network-related parameters
                    existing_vlan_data = self.xml_parser.extract_vlan_parameters(existing_tree)
                    existing_ip_data = self.xml_parser.extract_ip_parameters(existing_tree)
                    existing_routing_data = self.xml_parser.extract_routing_parameters(existing_tree)
                    existing_network_params = self.xml_parser.extract_network_parameters(existing_tree)
                    logger.info(f"Existing BTS ID: {existing_bts_id}")
                    logger.info(f"Existing sctpPortMin: {existing_sctp_port}")
                    logger.info(f"Existing 2G params: {existing_2g_params}")
                    logger.info(f"Existing 4G cells: {existing_4g_cells}")
                    logger.info(f"Existing 4G rootSeq: {existing_4g_rootseq}")
                    logger.info(f"Existing 5G NRCells: {existing_5g_nrcells}")
                    logger.info(f"Existing VLAN data: {existing_vlan_data}")
                    logger.info(f"Existing IP data: {existing_ip_data}")
                    logger.info(f"Existing routing data: {existing_routing_data}")
                    logger.info(f"Existing network params: {existing_network_params}")
                
                if reference_5g_xml_path:
                    reference_tree = self.xml_parser.parse_file(reference_5g_xml_path)
                    reference_bts_id = self.xml_parser.extract_bts_id(reference_tree)
                    reference_sctp_port = self.xml_parser.extract_sctp_port_min(reference_tree)
                    reference_2g_params = self.xml_parser.extract_2g_parameters(reference_tree)
                    reference_4g_cells = self.xml_parser.extract_4g_cells(reference_tree)
                    reference_4g_rootseq = self.xml_parser.extract_4g_rootseq(reference_tree)
                    reference_5g_nrcells = self.xml_parser.extract_5g_nrcells(reference_tree)
                    # Extract network-related parameters
                    reference_vlan_data = self.xml_parser.extract_vlan_parameters(reference_tree)
                    reference_ip_data = self.xml_parser.extract_ip_parameters(reference_tree)
                    reference_routing_data = self.xml_parser.extract_routing_parameters(reference_tree)
                    reference_network_params = self.xml_parser.extract_network_parameters(reference_tree)
                    logger.info(f"Reference BTS ID: {reference_bts_id}")
                    logger.info(f"Reference sctpPortMin: {reference_sctp_port}")
                    logger.info(f"Reference 2G params: {reference_2g_params}")
                    logger.info(f"Reference 4G cells: {reference_4g_cells}")
                    logger.info(f"Reference 4G rootSeq: {reference_4g_rootseq}")
                    logger.info(f"Reference 5G NRCells: {reference_5g_nrcells}")
                    logger.info(f"Reference VLAN data: {reference_vlan_data}")
                    logger.info(f"Reference IP data: {reference_ip_data}")
                    logger.info(f"Reference routing data: {reference_routing_data}")
                    logger.info(f"Reference network params: {reference_network_params}")
            except Exception as e:
                logger.warning(f"Error extracting parameters: {str(e)}")
            
            # Read reference XML as template
            with open(reference_5g_xml_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Perform template replacements
            updated_content = template_content
            debug_log = []
            
            # Replace station names if available
            if existing_bts_name and reference_bts_name:
                logger.info("Performing template-based name replacement...")
                updated_content = self._replace_station_names(
                    updated_content, reference_bts_name, existing_bts_name
                )
            else:
                logger.warning("btsName extraction failed, skipping name replacement")
            
            # Replace BTS IDs if available
            if existing_bts_id and reference_bts_id:
                logger.info("Performing template-based BTS ID replacement...")
                updated_content = self._replace_bts_ids(
                    updated_content, reference_bts_id, existing_bts_id
                )
            else:
                logger.warning("BTS ID extraction failed, skipping ID replacement")
            
            # Replace VLAN IDs from IP Plan if available
            if ip_plan_data:
                logger.info("Performing template-based VLAN ID replacement from IP Plan...")
                updated_content = self._replace_vlan_ids(
                    updated_content, reference_vlan_data or {}, ip_plan_data['technologies'], debug_log
                )
            else:
                logger.info("IP Plan or reference VLAN data not available for VLAN replacement")
            
            # Replace IP addresses from IP Plan if available
            if ip_plan_data:
                logger.info("Performing template-based IP address replacement from IP Plan...")
                updated_content = self._replace_ip_addresses(
                    updated_content, reference_ip_data, ip_plan_data['technologies'], debug_log
                )
                # Replace gateway routes based on technology mapping
                logger.info("Performing gateway replacement from IP Plan...")
                updated_content = self._replace_gateways_by_tech(
                    updated_content, ip_plan_data['technologies'], debug_log
                )
            else:
                logger.info("IP Plan or reference IP data not available for IP replacement")
            
            # Replace routing rules from IP Plan if available
            if ip_plan_data and reference_routing_data:
                logger.info("Performing template-based IPv4 routing replacement from IP Plan...")
                updated_content = self._replace_routing_rules(
                    updated_content, reference_routing_data, ip_plan_data['routing_rules']
                )
            else:
                logger.info("IP Plan or reference routing data not available for routing replacement")
            
            # Replace network parameters (NRX2LINK, LNADJGNB) from IP Plan if available
            if ip_plan_data and reference_network_params:
                logger.info("Performing template-based network parameters replacement from IP Plan...")
                updated_content = self._replace_network_parameters(
                    updated_content, reference_network_params, ip_plan_data['technologies']
                )
            else:
                logger.info("IP Plan or reference network parameters not available for network replacement")
            
            # Replace sctpPortMin if available
            if existing_sctp_port and reference_sctp_port:
                logger.info("Performing template-based sctpPortMin replacement...")
                updated_content = self._replace_sctp_port_min(
                    updated_content, reference_sctp_port, existing_sctp_port
                )
            else:
                logger.info("sctpPortMin not available for replacement - station may not have 3G configuration")
            
            # Replace 2G parameters if available
            if existing_2g_params and reference_2g_params:
                logger.info("Performing template-based 2G parameters replacement...")
                updated_content = self._replace_2g_parameters(
                    updated_content, reference_2g_params, existing_2g_params
                )
            else:
                logger.info("2G parameters not available for replacement - station may not have 2G configuration")
            
            # Replace 4G cell parameters if available
            if existing_4g_cells and reference_4g_cells:
                logger.info("Performing template-based 4G cell parameters replacement...")
                updated_content = self._replace_4g_cells(
                    updated_content, reference_4g_cells, existing_4g_cells
                )
            else:
                logger.info("4G cell parameters not available for replacement - station may not have 4G cells")
            
            # Replace 4G rootSeqIndex parameters if available
            if existing_4g_rootseq and reference_4g_rootseq:
                logger.info("Performing template-based 4G rootSeqIndex replacement...")
                updated_content = self._replace_4g_rootseq(
                    updated_content, reference_4g_rootseq, existing_4g_rootseq
                )
            else:
                logger.info("4G rootSeqIndex parameters not available for replacement - station may not have 4G FDD cells")
            
            # Replace 5G NRCELL physCellId parameters if available
            # Use existing 4G cells phyCellId values for 5G NRCELL physCellId
            if existing_4g_cells and reference_5g_nrcells:
                logger.info("Performing template-based 5G NRCELL physCellId replacement...")
                updated_content = self._replace_5g_nrcells(
                    updated_content, reference_5g_nrcells, existing_4g_cells
                )
            else:
                logger.info("5G NRCELL physCellId parameters not available for replacement - station may not have 5G cells or 4G cells")
            
            # Parse transmission data for potential future use
            try:
                transmission_data = self.excel_parser.parse_transmission_excel(transmission_excel_path)
                station_data = transmission_data.get(station_name, {})
                logger.info(f"Transmission data loaded for station: {bool(station_data)}")
            except Exception as e:
                logger.warning(f"Could not parse transmission Excel: {str(e)}")
                station_data = {}
            
            # Generate output filename
            output_filename = f"{station_name}_5G_modernization.xml"
            output_path = os.path.join(output_folder, output_filename)
            
            # Write result
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info(f"Successfully generated: {output_filename}")
            # OPTIONAL: return debug_log for frontend if needed
            return output_filename, debug_log
            
        except Exception as e:
            logger.error(f"Error generating 5G modernization: {str(e)}")
            raise
    
    def _update_element_with_station_data(self, element, station_name, station_data):
        """Update XML element with station-specific data (deepcopy, distName)"""
        # Clone element deeply
        new_elem = deepcopy(element)
        # Update distName recursively in element and children
        def update_distname(elem):
            if 'distName' in elem.attrib:
                dist_name = elem.attrib['distName']
                parts = dist_name.split('/')
                for i, part in enumerate(parts):
                    if part.startswith('MRBTS-'):
                        parts[i] = f"MRBTS-{station_name}"
                    if part.startswith('NRBTS-'):
                        parts[i] = f"NRBTS-{station_name}"
                elem.attrib['distName'] = '/'.join(parts)
            for child in elem:
                update_distname(child)
        update_distname(new_elem)
        return new_elem
    
    def _update_network_configuration(self, tree, station_data):
        """Update network configuration with new 5G IP addresses"""
        # Find all IPNO managedObjects
        ipnos = tree.xpath("//managedObject[contains(@class, 'IPNO')]")
        found_5g = False
        for ipno in ipnos:
            # მოძებნე 5G IP-ისთვის (მაგალითად, თუ აქვს p name="ipAddress" და ემთხვევა 5G IP-ს)
            ip_elem = ipno.find(".//p[@name='ipAddress']")
            if ip_elem is not None and ip_elem.text == station_data.get('5g_ip'):
                # განაახლე საჭირო პარამეტრები
                found_5g = True
                for p in ipno.findall(".//p"):
                    if p.get('name') == 'ipAddress':
                        p.text = station_data.get('5g_ip', '')
                    elif p.get('name') == 'gateway':
                        p.text = station_data.get('gateway', '')
                    elif p.get('name') == 'vlanId':
                        p.text = str(station_data.get('vlan', ''))
                break
        if not found_5g:
            # თუ არ არსებობს, დაამატე ახალი IPNO ელემენტი
            config_data = tree.getroot().find(".//configData")
            if config_data is not None:
                ipno_elem = etree.Element('managedObject', attrib={
                    'class': 'IPNO',
                    'distName': f"MRBTS-{station_data.get('om_ip','')}/IPNO-5G"
                })
                p_ip = etree.Element('p', name='ipAddress')
                p_ip.text = station_data.get('5g_ip', '')
                p_gw = etree.Element('p', name='gateway')
                p_gw.text = station_data.get('gateway', '')
                p_vlan = etree.Element('p', name='vlanId')
                p_vlan.text = str(station_data.get('vlan', ''))
                ipno_elem.extend([p_ip, p_gw, p_vlan])
                config_data.append(ipno_elem) 
    
    def _replace_station_names(self, xml_content, old_name, new_name):
        """Replace station names preserving format (dashes vs underscores)"""
        logger.info(f"Replacing '{old_name}' with '{new_name}' in template")
        
        # Count replacements for logging
        total_replacements = 0
        
        # Replace underscore version
        old_underscore = old_name.replace('-', '_')
        new_underscore = new_name.replace('-', '_')
        
        if old_underscore != old_name:  # Only if they're different
            before_count = xml_content.count(old_underscore)
            xml_content = xml_content.replace(old_underscore, new_underscore)
            after_count = xml_content.count(old_underscore)
            replacements = before_count - after_count
            total_replacements += replacements
            logger.info(f"Replaced {replacements} instances of '{old_underscore}' with '{new_underscore}'")
        
        # Replace dash version  
        old_dash = old_name.replace('_', '-')
        new_dash = new_name.replace('_', '-')
        
        if old_dash != old_name:  # Only if they're different
            before_count = xml_content.count(old_dash)
            xml_content = xml_content.replace(old_dash, new_dash)
            after_count = xml_content.count(old_dash)
            replacements = before_count - after_count
            total_replacements += replacements
            logger.info(f"Replaced {replacements} instances of '{old_dash}' with '{new_dash}'")
        
        # Replace original format as well
        before_count = xml_content.count(old_name)
        xml_content = xml_content.replace(old_name, new_name)
        after_count = xml_content.count(old_name)
        replacements = before_count - after_count
        total_replacements += replacements
        logger.info(f"Replaced {replacements} instances of '{old_name}' with '{new_name}'")
        
        logger.info(f"Total replacements made: {total_replacements}")
        return xml_content 
    
    def _replace_bts_ids(self, xml_content, old_id, new_id):
        """Replace BTS IDs in distName attributes (e.g., MRBTS-90217 -> MRBTS-12345)"""
        logger.info(f"Replacing BTS ID '{old_id}' with '{new_id}' in template")
        
        # Count replacements for logging
        total_replacements = 0
        
        # Replace in MRBTS distName patterns
        patterns_to_replace = [
            f"MRBTS-{old_id}",
            f"NRBTS-{old_id}",
            f"LNBTS-{old_id}"
        ]
        
        for pattern in patterns_to_replace:
            new_pattern = pattern.replace(old_id, new_id)
            before_count = xml_content.count(pattern)
            xml_content = xml_content.replace(pattern, new_pattern)
            after_count = xml_content.count(pattern)
            replacements = before_count - after_count
            total_replacements += replacements
            if replacements > 0:
                logger.info(f"Replaced {replacements} instances of '{pattern}' with '{new_pattern}'")
        
        # Also replace lnBtsId parameter values
        import re
        lnBtsId_pattern = rf'(<p\s+name="lnBtsId"[^>]*>)\s*{re.escape(old_id)}\s*(</p>)'
        lnBtsId_replacement = rf'\g<1>{new_id}\g<2>'
        lnBtsId_matches = re.findall(lnBtsId_pattern, xml_content, flags=re.IGNORECASE)
        if lnBtsId_matches:
            xml_content = re.sub(lnBtsId_pattern, lnBtsId_replacement, xml_content, flags=re.IGNORECASE)
            lnBtsId_replacements = len(lnBtsId_matches)
            total_replacements += lnBtsId_replacements
            logger.info(f"Replaced {lnBtsId_replacements} instances of lnBtsId '{old_id}' with '{new_id}'")
        
        logger.info(f"Total BTS ID replacements made: {total_replacements}")
        return xml_content
    
    def _replace_sctp_port_min(self, xml_content, old_port, new_port):
        """Replace sctpPortMin values in XML content"""
        logger.info(f"Replacing sctpPortMin '{old_port}' with '{new_port}' in template")
        
        # Count replacements for logging
        total_replacements = 0
        
        # Look for the specific pattern: <p name="sctpPortMin">old_port</p>
        import re
        
        # Pattern to match sctpPortMin parameter
        pattern = rf'(<p\s+name="sctpPortMin"[^>]*>)\s*{re.escape(old_port)}\s*(</p>)'
        replacement = rf'\g<1>{new_port}\g<2>'
        
        # Count matches before replacement
        matches = re.findall(pattern, xml_content, re.IGNORECASE)
        total_replacements = len(matches)
        
        if total_replacements > 0:
            # Perform replacement
            xml_content = re.sub(pattern, replacement, xml_content, flags=re.IGNORECASE)
            logger.info(f"Replaced {total_replacements} instances of sctpPortMin '{old_port}' with '{new_port}'")
        else:
            logger.warning(f"No instances of sctpPortMin '{old_port}' found for replacement")
        
        logger.info(f"Total sctpPortMin replacements made: {total_replacements}")
        return xml_content
    
    def _replace_2g_parameters(self, xml_content, old_params, new_params):
        """Replace 2G parameters in XML content"""
        logger.info(f"Replacing 2G parameters in template")
        logger.info(f"Old 2G params: {old_params}")
        logger.info(f"New 2G params: {new_params}")
        
        # Count total replacements for logging
        total_replacements = 0
        
        # Parameters to replace
        params_to_replace = ['bcfId', 'bscId', 'mPlaneRemoteIpAddressOmuSig']
        
        import re
        
        for param_name in params_to_replace:
            if param_name in old_params and param_name in new_params:
                old_value = old_params[param_name]
                new_value = new_params[param_name]
                
                # Pattern to match the specific parameter
                pattern = rf'(<p\s+name="{re.escape(param_name)}"[^>]*>)\s*{re.escape(old_value)}\s*(</p>)'
                replacement = rf'\g<1>{new_value}\g<2>'
                
                # Count matches before replacement
                matches = re.findall(pattern, xml_content, re.IGNORECASE)
                param_replacements = len(matches)
                
                if param_replacements > 0:
                    # Perform replacement
                    xml_content = re.sub(pattern, replacement, xml_content, flags=re.IGNORECASE)
                    logger.info(f"Replaced {param_replacements} instances of {param_name} '{old_value}' with '{new_value}'")
                    total_replacements += param_replacements
                else:
                    logger.warning(f"No instances of {param_name} '{old_value}' found for replacement")
            else:
                if param_name not in old_params:
                    logger.info(f"Parameter {param_name} not found in reference template")
                if param_name not in new_params:
                    logger.info(f"Parameter {param_name} not found in existing station")
        
        logger.info(f"Total 2G parameter replacements made: {total_replacements}")
        return xml_content
    
    def _replace_4g_cells(self, xml_content, old_cells, new_cells):
        """Replace 4G cell parameters in XML content"""
        logger.info(f"Replacing 4G cell parameters in template")
        logger.info(f"Reference cells: {list(old_cells.keys()) if old_cells else 'None'}")
        logger.info(f"Target cells: {list(new_cells.keys()) if new_cells else 'None'}")
        
        # Count total replacements for logging
        total_replacements = 0
        
        # Parameters to replace in cells
        params_to_replace = ['phyCellId', 'tac', 'rootSeqIndex']
        
        import re
        
        # Process each cell
        for cell_id in old_cells.keys():
            if cell_id in new_cells:
                logger.info(f"Processing cell {cell_id}")
                old_cell_params = old_cells[cell_id]
                new_cell_params = new_cells[cell_id]
                
                # For each parameter in this cell
                for param_name in params_to_replace:
                    if param_name in old_cell_params and param_name in new_cell_params:
                        old_value = old_cell_params[param_name]
                        new_value = new_cell_params[param_name]
                        
                        if param_name == 'rootSeqIndex':
                            # rootSeqIndex is in LNCEL_FDD sub-object, need different pattern
                            # Pattern to find LNCEL_FDD managedObject that contains the cell_id in distName
                            cell_pattern = rf'(<managedObject[^>]*class="[^"]*LNCEL_FDD[^"]*"[^>]*distName="[^"]*{re.escape(cell_id)}[^"]*"[^>]*>.*?)(<p\s+name="{re.escape(param_name)}"[^>]*>)\s*{re.escape(old_value)}\s*(</p>.*?</managedObject>)'
                        else:
                            # phyCellId and tac are directly in LNCEL managedObject (not LNCEL_FDD)
                            # Pattern to find the LNCEL managedObject for this specific cell
                            cell_pattern = rf'(<managedObject[^>]*class="[^"]*:LNCEL"[^>]*distName="[^"]*{re.escape(cell_id)}[^"]*"[^>]*>.*?)(<p\s+name="{re.escape(param_name)}"[^>]*>)\s*{re.escape(old_value)}\s*(</p>.*?</managedObject>)'
                        
                        def replace_in_cell(match):
                            before_param = match.group(1)
                            param_start = match.group(2)
                            after_param = match.group(3)
                            return f"{before_param}{param_start}{new_value}{after_param}"
                        
                        # Count matches before replacement
                        matches = re.findall(cell_pattern, xml_content, re.DOTALL | re.IGNORECASE)
                        param_replacements = len(matches)
                        
                        if param_replacements > 0:
                            # Perform replacement
                            xml_content = re.sub(cell_pattern, replace_in_cell, xml_content, flags=re.DOTALL | re.IGNORECASE)
                            logger.info(f"Replaced {param_replacements} instances of {cell_id} {param_name} '{old_value}' with '{new_value}'")
                            total_replacements += param_replacements
                        else:
                            logger.warning(f"No instances of {cell_id} {param_name} '{old_value}' found for replacement")
                    else:
                        if param_name not in old_cell_params:
                            logger.info(f"Parameter {param_name} not found in reference cell {cell_id}")
                        if param_name not in new_cell_params:
                            logger.info(f"Parameter {param_name} not found in existing cell {cell_id}")
            else:
                logger.info(f"Cell {cell_id} from reference template not found in existing station")
        
        # Check for cells in existing that are not in reference
        for cell_id in new_cells.keys():
            if cell_id not in old_cells:
                logger.info(f"Cell {cell_id} found in existing station but not in reference template")
        
        logger.info(f"Total 4G cell parameter replacements made: {total_replacements}")
        return xml_content
    
    def _replace_4g_rootseq(self, xml_content, old_rootseq, new_rootseq):
        """Replace 4G rootSeqIndex parameters in LNCEL_FDD objects"""
        logger.info(f"Replacing 4G rootSeqIndex parameters in template")
        logger.info(f"Reference rootSeq: {list(old_rootseq.keys()) if old_rootseq else 'None'}")
        logger.info(f"Target rootSeq: {list(new_rootseq.keys()) if new_rootseq else 'None'}")
        
        # Count total replacements for logging
        total_replacements = 0
        
        import re
        
        # Process each cell
        for cell_id in old_rootseq.keys():
            if cell_id in new_rootseq:
                logger.info(f"Processing rootSeqIndex for cell {cell_id}")
                old_value = old_rootseq[cell_id]['rootSeqIndex']
                new_value = new_rootseq[cell_id]['rootSeqIndex']
                
                # Pattern to find LNCEL_FDD managedObject that contains the cell_id in distName
                # and then the rootSeqIndex parameter within it
                cell_pattern = rf'(<managedObject[^>]*class="[^"]*LNCEL_FDD[^"]*"[^>]*distName="[^"]*{re.escape(cell_id)}[^"]*"[^>]*>.*?)(<p\s+name="rootSeqIndex"[^>]*>)\s*{re.escape(old_value)}\s*(</p>.*?</managedObject>)'
                
                def replace_rootseq(match):
                    before_param = match.group(1)
                    param_start = match.group(2)
                    after_param = match.group(3)
                    return f"{before_param}{param_start}{new_value}{after_param}"
                
                # Count matches before replacement
                matches = re.findall(cell_pattern, xml_content, re.DOTALL | re.IGNORECASE)
                param_replacements = len(matches)
                
                if param_replacements > 0:
                    # Perform replacement
                    xml_content = re.sub(cell_pattern, replace_rootseq, xml_content, flags=re.DOTALL | re.IGNORECASE)
                    logger.info(f"Replaced {param_replacements} instances of {cell_id} rootSeqIndex '{old_value}' with '{new_value}'")
                    total_replacements += param_replacements
                else:
                    logger.warning(f"No instances of {cell_id} rootSeqIndex '{old_value}' found for replacement")
            else:
                logger.info(f"Cell {cell_id} from reference template not found in existing station")
        
        # Check for cells in existing that are not in reference
        for cell_id in new_rootseq.keys():
            if cell_id not in old_rootseq:
                logger.info(f"Cell {cell_id} found in existing station but not in reference template")
        
        logger.info(f"Total 4G rootSeqIndex replacements made: {total_replacements}")
        return xml_content
    
    def _replace_5g_nrcells(self, xml_content, old_nrcells, new_4g_cells):
        """Replace 5G NRCELL physCellId parameters using 4G LNCEL phyCellId values"""
        logger.info(f"Replacing 5G NRCELL physCellId parameters in template")
        logger.info(f"Reference 5G NRCells: {list(old_nrcells.keys()) if old_nrcells else 'None'}")
        logger.info(f"Source 4G cells: {list(new_4g_cells.keys()) if new_4g_cells else 'None'}")
        
        # Count total replacements for logging
        total_replacements = 0
        
        import re
        
        # Process each NRCELL
        for nrcell_id in old_nrcells.keys():
            logger.info(f"Processing NRCELL physCellId: {nrcell_id}")
            
            # Get the NRCELL info and old physCellId
            nrcell_info = old_nrcells[nrcell_id]
            mapped_lncel_id = nrcell_info['mapped_lncel']  # e.g., "LNCEL-11"
            old_phys_cell_id = nrcell_info['physCellId']
            
            # Check if the mapped LNCEL exists in new 4G cells
            if mapped_lncel_id in new_4g_cells:
                # Get new physCellId from 4G LNCEL
                if 'phyCellId' in new_4g_cells[mapped_lncel_id]:
                    new_phys_cell_id = new_4g_cells[mapped_lncel_id]['phyCellId']
                    
                    logger.info(f"Mapping {nrcell_id} (old physCellId: {old_phys_cell_id}) → {mapped_lncel_id} (new physCellId: {new_phys_cell_id})")
                    
                    # Pattern to find NRCELL managedObject that contains the specific NRCELL ID in distName
                    # and then the physCellId parameter within it
                    cell_pattern = rf'(<managedObject[^>]*class="[^"]*NRCELL[^"]*"[^>]*distName="[^"]*{re.escape(nrcell_id)}[^"]*"[^>]*>.*?)(<p\s+name="physCellId"[^>]*>)\s*{re.escape(old_phys_cell_id)}\s*(</p>.*?</managedObject>)'
                    
                    def replace_nrcell_phys(match):
                        before_param = match.group(1)
                        param_start = match.group(2)
                        after_param = match.group(3)
                        return f"{before_param}{param_start}{new_phys_cell_id}{after_param}"
                    
                    # Count matches before replacement
                    matches = re.findall(cell_pattern, xml_content, re.DOTALL | re.IGNORECASE)
                    param_replacements = len(matches)
                    
                    if param_replacements > 0:
                        # Perform replacement
                        xml_content = re.sub(cell_pattern, replace_nrcell_phys, xml_content, flags=re.DOTALL | re.IGNORECASE)
                        logger.info(f"Replaced {param_replacements} instances of {nrcell_id} physCellId '{old_phys_cell_id}' with '{new_phys_cell_id}'")
                        total_replacements += param_replacements
                    else:
                        logger.warning(f"No instances of {nrcell_id} physCellId '{old_phys_cell_id}' found for replacement")
                else:
                    logger.warning(f"phyCellId not found in 4G cell {mapped_lncel_id} for mapping to {nrcell_id}")
            else:
                logger.info(f"Mapped 4G cell {mapped_lncel_id} not found in existing station for 5G mapping")
        
        logger.info(f"Total 5G NRCELL physCellId replacements made: {total_replacements}")
        return xml_content

    def _replace_vlan_ids(self, xml_content, reference_vlan_data, ip_plan_technologies, debug_log=None):
        """
        ჩაანაცვლებს VLAN ID-ებს XML-ში userLabel-ის მიხედვით reference_vlan_data-სა და ip_plan_technologies სტრუქტურებიდან.
        xml_content: XML string
        reference_vlan_data: dict, მაგალითად {'2G': {'userLabel': '2G', 'vlanId': '3950'}, ...}
        ip_plan_technologies: dict, მაგალითად {'2G': {'userLabel': '2G', 'vlanId': '1234'}, ...}
        debug_log: optional list for step-by-step logging
        აბრუნებს განახლებულ XML string-ს.
        """
        import xml.etree.ElementTree as ET
        import re

        def normalize_tech(label):
            if not label:
                return None
            name = str(label).strip().upper()
            mapping = {
                'OAM': 'OAM', 'MGT': 'OAM',
                '2G': '2G', 'GSM': '2G',
                '3G': '3G', 'WCDMA': '3G',
                '4G': '4G', 'LTE': '4G',
                '5G': '5G', 'NR': '5G'
            }
            return mapping.get(name, name)

        def coerce_vlan(value):
            if value is None:
                return None
            s = str(value).strip()
            if not s or s.lower() == 'nan':
                return None
            try:
                # handle values like 3980, '3980', 3980.0
                vlan_int = int(float(s))
                if vlan_int < 1 or vlan_int > 4094:
                    return None
                return str(vlan_int)
            except Exception:
                return None

        if debug_log is None:
            debug_log = []

        debug_log.append("[VLAN] XML parsing started")

        # Remove default namespace for easier parsing
        xml_content = re.sub(r'xmlns="[^"]+"', '', xml_content, count=1)
        root = ET.fromstring(xml_content)

        # Build lookup maps
        old_vlan_by_tech = {}
        for key, info in (reference_vlan_data or {}).items():
            tech_norm = normalize_tech(info.get('userLabel', key))
            if tech_norm:
                old_vlan_by_tech[tech_norm] = str(info.get('vlanId')) if info.get('vlanId') is not None else None

        new_vlan_by_tech = {}
        for key, info in (ip_plan_technologies or {}).items():
            tech_norm = normalize_tech(info.get('userLabel', key))
            vlan_norm = coerce_vlan(info.get('vlanId'))
            if tech_norm and vlan_norm:
                new_vlan_by_tech[tech_norm] = vlan_norm

        ref_pairs = ', '.join([f'{k}:{v}' for k, v in old_vlan_by_tech.items() if v]) or 'none'
        new_pairs = ', '.join([f'{k}:{v}' for k, v in new_vlan_by_tech.items()]) or 'none'
        debug_log.append(f"[VLAN] Reference VLANs detected: {ref_pairs}")
        debug_log.append(f"[VLAN] New VLANs from IP Plan: {new_pairs}")

        replacements = 0
        for mo in root.findall('.//managedObject'):
            class_attr = mo.get('class', '')
            if 'VLANIF' not in class_attr:
                continue

            user_label = None
            vlan_elem = None
            for p in mo.findall('p'):
                if p.get('name') == 'userLabel':
                    user_label = p.text.strip() if p.text else None
                if p.get('name') == 'vlanId':
                    vlan_elem = p

            if not user_label or vlan_elem is None:
                continue

            tech_norm = normalize_tech(user_label)
            if not tech_norm:
                debug_log.append(f"[VLAN] Skipped unknown tech label '{user_label}'")
                continue

            new_vlan = new_vlan_by_tech.get(tech_norm)
            if not new_vlan:
                debug_log.append(f"[VLAN] No new VLAN for tech '{tech_norm}' (userLabel='{user_label}')")
                continue

            current_vlan_text = vlan_elem.text.strip() if vlan_elem.text else ''
            expected_old_vlan = old_vlan_by_tech.get(tech_norm)

            if expected_old_vlan and current_vlan_text and current_vlan_text != expected_old_vlan:
                debug_log.append(f"[VLAN] Warning: for tech '{tech_norm}' current XML VLAN '{current_vlan_text}' != reference '{expected_old_vlan}'")

            vlan_elem.text = new_vlan
            replacements += 1
            debug_log.append(f"[VLAN] userLabel '{user_label}' ({tech_norm}): VLAN {current_vlan_text or 'N/A'} -> {new_vlan}")

        debug_log.append(f"[VLAN] Total VLAN replacements: {replacements}")

        # Convert back to string
        updated_xml = ET.tostring(root, encoding='unicode')
        return updated_xml

    def _replace_ip_addresses(self, xml_content, reference_ip_data, ip_plan_technologies, debug_log=None):
        """Replace IP addresses, masks, and gateways from IP Plan data using structural mapping (IPIF → IPADDRESSV4)."""
        logger.info(f"Replacing IP addresses from IP Plan (structural)")
        total_replacements = 0
        import re
        import xml.etree.ElementTree as ET

        if debug_log is None:
            debug_log = []

        def normalize_tech(label):
            if not label:
                return None
            name = str(label).strip().upper()
            mapping = {
                'OAM': 'OAM', 'MGT': 'OAM',
                '2G': '2G', 'GSM': '2G',
                '3G': '3G', 'WCDMA': '3G',
                '4G': '4G', 'LTE': '4G',
                '5G': '5G', 'NR': '5G'
            }
            return mapping.get(name, name)

        def coerce_prefix(value):
            if value is None:
                return None
            s = str(value).strip()
            if not s or s.lower() == 'nan':
                return None
            try:
                n = int(float(s))
                return str(n)
            except Exception:
                return s

        # Namespace strip for easier parsing
        xml_content = re.sub(r'xmlns="[^"]+"', '', xml_content, count=1)
        root = ET.fromstring(xml_content)

        # Build IPIF map: distName -> userLabel
        ipif_label_by_dn = {}
        for mo in root.findall('.//managedObject'):
            class_attr = mo.get('class', '')
            if 'IPIF' in class_attr and 'IPADDRESSV4' not in class_attr:
                dn = mo.get('distName', '')
                user_label = None
                for p in mo.findall('p'):
                    if p.get('name') == 'userLabel':
                        user_label = p.text.strip() if p.text else None
                        break
                if dn and user_label:
                    ipif_label_by_dn[dn] = user_label

        # Iterate IPADDRESSV4 and set IP/mask by matching parent IPIF label
        for mo in root.findall('.//managedObject'):
            class_attr = mo.get('class', '')
            if 'IPADDRESSV4' not in class_attr:
                continue
            ipaddr_dn = mo.get('distName', '')
            if not ipaddr_dn:
                continue
            parent_ipif_dn = '/'.join(ipaddr_dn.split('/')[:-1])
            user_label = ipif_label_by_dn.get(parent_ipif_dn)
            if not user_label:
                continue
            tech = normalize_tech(user_label)
            tech_info = ip_plan_technologies.get(tech) if ip_plan_technologies else None
            if not tech_info:
                debug_log.append(f"[IP] No IP Plan data for tech '{tech}' (label='{user_label}')")
                continue

            new_ip = tech_info.get('localIpAddr')
            new_mask = coerce_prefix(tech_info.get('localIpPrefixLength'))

            # Locate fields to update
            ip_elem = None
            mask_elem = None
            for p in mo.findall('p'):
                if p.get('name') == 'localIpAddr':
                    ip_elem = p
                elif p.get('name') == 'localIpPrefixLength':
                    mask_elem = p

            replaced_any = False
            if ip_elem is not None and new_ip:
                old = ip_elem.text.strip() if ip_elem.text else ''
                ip_elem.text = str(new_ip)
                total_replacements += 1
                replaced_any = True
                debug_log.append(f"[IP] {tech} ({user_label}) IP {old or 'N/A'} -> {new_ip}")
            if mask_elem is not None and new_mask:
                old = mask_elem.text.strip() if mask_elem.text else ''
                mask_elem.text = str(new_mask)
                total_replacements += 1
                replaced_any = True
                debug_log.append(f"[IP] {tech} ({user_label}) Prefix {old or 'N/A'} -> {new_mask}")
            if not replaced_any:
                debug_log.append(f"[IP] {tech} ({user_label}) nothing to replace (missing elements or values)")

        logger.info(f"Total IP/mask replacements made: {total_replacements}")
        return ET.tostring(root, encoding='unicode')

    def _replace_routing_rules(self, xml_content, reference_routing_data, ip_plan_routing_rules):
        """Replace IPv4 routing rules from IP Plan data"""
        logger.info(f"Replacing IPv4 routing rules from IP Plan")
        logger.info(f"Reference routing data: {list(reference_routing_data.keys()) if reference_routing_data else 'None'}")
        logger.info(f"IP Plan routing rules: {ip_plan_routing_rules if ip_plan_routing_rules else 'None'}")
        
        total_replacements = 0
        import re
        
        if not ip_plan_routing_rules:
            logger.info("No IP Plan routing rules provided")
            return xml_content
        
        # Process IPRT-1 mappings
        iprt1_mappings = ip_plan_routing_rules.get('IPRT-1', {})
        for ip_prefix, new_gateway in iprt1_mappings.items():
            if not new_gateway:
                continue
                
            # Find matching routes in reference data
            if 'IPRT-1' in reference_routing_data:
                ref_routes = reference_routing_data['IPRT-1']
                if ip_prefix in ref_routes:
                    old_gateway = ref_routes[ip_prefix]['gateway']
                    dest_ip = ref_routes[ip_prefix]['destIpAddr']
                    
                    logger.info(f"Replacing IPRT-1 route: {ip_prefix} -> gateway {old_gateway} with {new_gateway}")
                    
                    # Pattern to replace gateway for specific destination IP
                    pattern = rf'(<managedObject[^>]*class="[^"]*IPRT[^"]*"[^>]*>.*?<p\s+name="destIpAddr"[^>]*>\s*{re.escape(dest_ip)}\s*</p>.*?)(<p\s+name="gateway"[^>]*>)\s*{re.escape(old_gateway)}\s*(</p>.*?</managedObject>)'
                    
                    def replace_route_gw(match):
                        before_gw = match.group(1)
                        gw_start = match.group(2)
                        after_gw = match.group(3)
                        return f"{before_gw}{gw_start}{new_gateway}{after_gw}"
                    
                    matches = re.findall(pattern, xml_content, re.DOTALL | re.IGNORECASE)
                    if matches:
                        xml_content = re.sub(pattern, replace_route_gw, xml_content, flags=re.DOTALL | re.IGNORECASE)
                        total_replacements += len(matches)
                        logger.info(f"Replaced {len(matches)} instances of IPRT-1 gateway for {dest_ip}")
        
        # Process IPRT-2 NR mappings  
        iprt2_mappings = ip_plan_routing_rules.get('IPRT-2 NR', {})
        for ip_prefix, new_gateway in iprt2_mappings.items():
            if not new_gateway:
                continue
                
            # Find matching routes in reference data
            for iprt_type in ['IPRT-2', 'IPRT-2 NR']:
                if iprt_type in reference_routing_data:
                    ref_routes = reference_routing_data[iprt_type]
                    if ip_prefix in ref_routes:
                        old_gateway = ref_routes[ip_prefix]['gateway']
                        dest_ip = ref_routes[ip_prefix]['destIpAddr']
                        
                        logger.info(f"Replacing {iprt_type} route: {ip_prefix} -> gateway {old_gateway} with {new_gateway}")
                        
                        # Pattern to replace gateway for specific destination IP
                        pattern = rf'(<managedObject[^>]*class="[^"]*IPRT[^"]*"[^>]*>.*?<p\s+name="destIpAddr"[^>]*>\s*{re.escape(dest_ip)}\s*</p>.*?)(<p\s+name="gateway"[^>]*>)\s*{re.escape(old_gateway)}\s*(</p>.*?</managedObject>)'
                        
                        def replace_route_gw(match):
                            before_gw = match.group(1)
                            gw_start = match.group(2) 
                            after_gw = match.group(3)
                            return f"{before_gw}{gw_start}{new_gateway}{after_gw}"
                        
                        matches = re.findall(pattern, xml_content, re.DOTALL | re.IGNORECASE)
                        if matches:
                            xml_content = re.sub(pattern, replace_route_gw, xml_content, flags=re.DOTALL | re.IGNORECASE)
                            total_replacements += len(matches)
                            logger.info(f"Replaced {len(matches)} instances of {iprt_type} gateway for {dest_ip}")
        
        logger.info(f"Total routing replacements made: {total_replacements}")
        return xml_content

    def _replace_network_parameters(self, xml_content, reference_network_params, ip_plan_technologies):
        """Replace network parameters (NRX2LINK_TRUST, LNADJGNB) from IP Plan data"""
        logger.info(f"Replacing network parameters from IP Plan")
        logger.info(f"Reference network params: {list(reference_network_params.keys()) if reference_network_params else 'None'}")
        logger.info(f"IP Plan technologies: {list(ip_plan_technologies.keys()) if ip_plan_technologies else 'None'}")
        
        total_replacements = 0
        import re
        
        # Replace NRX2LINK_TRUST ipV4Addr with LTE IP from IP Plan
        if 'NRX2LINK_TRUST_ipV4Addr' in reference_network_params:
            old_ip = reference_network_params['NRX2LINK_TRUST_ipV4Addr']['value']
            
            # Get LTE IP from IP Plan
            new_ip = None
            for tech, tech_data in ip_plan_technologies.items():
                if tech in ['4G', 'LTE']:
                    new_ip = tech_data.get('localIpAddr')
                    break
            
            if old_ip and new_ip:
                logger.info(f"Replacing NRX2LINK_TRUST ipV4Addr: {old_ip} -> {new_ip}")
                
                pattern = rf'(<p\s+name="ipV4Addr"[^>]*>)\s*{re.escape(old_ip)}\s*(</p>)'
                replacement = rf'\g<1>{new_ip}\g<2>'
                
                matches = re.findall(pattern, xml_content, re.IGNORECASE)
                if matches:
                    xml_content = re.sub(pattern, replacement, xml_content, flags=re.IGNORECASE)
                    total_replacements += len(matches)
                    logger.info(f"Replaced {len(matches)} instances of NRX2LINK_TRUST ipV4Addr")
            else:
                logger.warning("Could not replace NRX2LINK_TRUST ipV4Addr - missing old or new IP")
        
        # Replace LNADJGNB cPlaneIpAddr with 5G IP from IP Plan
        if 'LNADJGNB_cPlaneIpAddr' in reference_network_params:
            old_ip = reference_network_params['LNADJGNB_cPlaneIpAddr']['value']
            
            # Get 5G IP from IP Plan
            new_ip = None
            for tech, tech_data in ip_plan_technologies.items():
                if tech in ['5G', 'NR']:
                    new_ip = tech_data.get('localIpAddr')
                    break
            
            if old_ip and new_ip:
                logger.info(f"Replacing LNADJGNB cPlaneIpAddr: {old_ip} -> {new_ip}")
                
                pattern = rf'(<p\s+name="cPlaneIpAddr"[^>]*>)\s*{re.escape(old_ip)}\s*(</p>)'
                replacement = rf'\g<1>{new_ip}\g<2>'
                
                matches = re.findall(pattern, xml_content, re.IGNORECASE)
                if matches:
                    xml_content = re.sub(pattern, replacement, xml_content, flags=re.IGNORECASE)
                    total_replacements += len(matches)
                    logger.info(f"Replaced {len(matches)} instances of LNADJGNB cPlaneIpAddr")
            else:
                logger.warning("Could not replace LNADJGNB cPlaneIpAddr - missing old or new IP")
        
        logger.info(f"Total network parameter replacements made: {total_replacements}")
        return xml_content

    def _replace_gateways_by_tech(self, xml_content, ip_plan_technologies, debug_log=None):
        """Replace gateway IPs in IPRT static routes using Excel gateways per technology.
        Mapping:
          - IPRT-1 items by destIpAddr: 0.0.0.0->OAM, 10.0.0.192->3G, 10.0.7.112->2G, 10.111.0.0->4G
          - IPRT-2 (or userLabel NR) -> 5G
        """
        import re
        import xml.etree.ElementTree as ET
        if debug_log is None:
            debug_log = []

        def normalize_tech(label):
            if not label:
                return None
            name = str(label).strip().upper()
            mapping = {
                'OAM': 'OAM', 'MGT': 'OAM',
                '2G': '2G', 'GSM': '2G',
                '3G': '3G', 'WCDMA': '3G',
                '4G': '4G', 'LTE': '4G',
                '5G': '5G', 'NR': '5G'
            }
            return mapping.get(name, name)

        # Prepare gateway lookup from Excel
        gw_by_tech = {}
        for key, info in (ip_plan_technologies or {}).items():
            tech = normalize_tech(info.get('userLabel', key))
            gw = info.get('gateway')
            if tech and gw:
                gw_by_tech[tech] = str(gw).strip()

        # Early exit if nothing to replace
        if not gw_by_tech:
            debug_log.append("[GW] No gateways provided by IP Plan; skipping gateway replacement")
            return xml_content

        # Strip namespace and parse
        xml_no_ns = re.sub(r'xmlns="[^\"]+"', '', xml_content, count=1)
        root = ET.fromstring(xml_no_ns)

        # destIpAddr -> tech mapping for IPRT-1
        dest_to_tech = {
            '0.0.0.0': 'OAM',
            # 3G / WCDMA
            '10.0.0.192': '3G',
            '10.0.1.192': '3G',
            # 2G / GSM
            '10.0.7.112': '2G',
            '10.0.7.144': '2G',
            '10.0.7.96': '2G',
            # 4G / LTE
            '10.111.0.0': '4G',
            '10.121.0.0': '4G',
            '10.131.0.0': '4G',
            '172.28.16.64': '4G',
            '172.28.37.80': '4G',
            '172.28.37.96': '4G',
            '172.28.44.64': '4G',
            '172.28.44.80': '4G',
            '172.29.16.64': '4G',
            '172.29.37.16': '4G',
            '172.29.37.32': '4G',
            '172.30.157.240': '4G',
            '172.30.160.32': '4G',
            '10.112.0.0': '4G'
        }

        replacements = 0
        for mo in root.findall('.//managedObject'):
            class_attr = mo.get('class', '')
            if 'IPRT' not in class_attr:
                continue

            dn = mo.get('distName', '')
            iprt_type = 'IPRT-2' if 'IPRT-2' in dn else 'IPRT-1'
            mo_label = None
            for p in mo.findall('p'):
                if p.get('name') == 'userLabel':
                    mo_label = p.text.strip() if p.text else None

            # Process staticRoutes items
            for list_elem in mo.findall('list'):
                if list_elem.get('name') != 'staticRoutes':
                    continue
                for item in list_elem.findall('item'):
                    dest = None
                    gw_elem = None
                    for p in item.findall('p'):
                        if p.get('name') == 'destIpAddr':
                            dest = p.text.strip() if p.text else None
                        elif p.get('name') == 'gateway':
                            gw_elem = p

                    if gw_elem is None:
                        continue

                    target_tech = None
                    if iprt_type == 'IPRT-2' or (mo_label and normalize_tech(mo_label) == '5G'):
                        target_tech = '5G'
                    else:
                        target_tech = dest_to_tech.get(dest)

                    if not target_tech:
                        continue

                    new_gw = gw_by_tech.get(target_tech)
                    if not new_gw:
                        debug_log.append(f"[GW] No Excel gateway for tech '{target_tech}' (dest={dest})")
                        continue

                    old_gw = gw_elem.text.strip() if gw_elem.text else ''
                    if old_gw == new_gw:
                        continue
                    gw_elem.text = new_gw
                    replacements += 1
                    debug_log.append(f"[GW] {iprt_type} dest={dest or '-'} tech={target_tech}: GW {old_gw or 'N/A'} -> {new_gw}")

        debug_log.append(f"[GW] Total gateway replacements: {replacements}")
        return ET.tostring(root, encoding='unicode')