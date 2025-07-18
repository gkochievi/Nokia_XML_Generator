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
                 transmission_excel_path, output_folder, existing_bts_name=None, reference_bts_name=None):
        """Generate 5G modernization configuration using template replacement approach"""
        try:
            logger.info("Starting 5G modernization generation...")
            logger.info(f"Station name: {station_name}")
            logger.info(f"Existing btsName: {existing_bts_name}")
            logger.info(f"Reference btsName: {reference_bts_name}")
            
            # Extract BTS IDs, sctpPortMin, and 2G parameters from both XML files
            existing_bts_id = None
            reference_bts_id = None
            existing_sctp_port = None
            reference_sctp_port = None
            existing_2g_params = None
            reference_2g_params = None
            
            try:
                if existing_xml_path:
                    existing_tree = self.xml_parser.parse_file(existing_xml_path)
                    existing_bts_id = self.xml_parser.extract_bts_id(existing_tree)
                    existing_sctp_port = self.xml_parser.extract_sctp_port_min(existing_tree)
                    existing_2g_params = self.xml_parser.extract_2g_parameters(existing_tree)
                    logger.info(f"Existing BTS ID: {existing_bts_id}")
                    logger.info(f"Existing sctpPortMin: {existing_sctp_port}")
                    logger.info(f"Existing 2G params: {existing_2g_params}")
                
                if reference_5g_xml_path:
                    reference_tree = self.xml_parser.parse_file(reference_5g_xml_path)
                    reference_bts_id = self.xml_parser.extract_bts_id(reference_tree)
                    reference_sctp_port = self.xml_parser.extract_sctp_port_min(reference_tree)
                    reference_2g_params = self.xml_parser.extract_2g_parameters(reference_tree)
                    logger.info(f"Reference BTS ID: {reference_bts_id}")
                    logger.info(f"Reference sctpPortMin: {reference_sctp_port}")
                    logger.info(f"Reference 2G params: {reference_2g_params}")
            except Exception as e:
                logger.warning(f"Error extracting parameters: {str(e)}")
            
            # Read reference XML as template
            with open(reference_5g_xml_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Perform template replacements
            updated_content = template_content
            
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
            return output_filename
            
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
            f"NRBTS-{old_id}"
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