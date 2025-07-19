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
            
            try:
                if existing_xml_path:
                    existing_tree = self.xml_parser.parse_file(existing_xml_path)
                    existing_bts_id = self.xml_parser.extract_bts_id(existing_tree)
                    existing_sctp_port = self.xml_parser.extract_sctp_port_min(existing_tree)
                    existing_2g_params = self.xml_parser.extract_2g_parameters(existing_tree)
                    existing_4g_cells = self.xml_parser.extract_4g_cells(existing_tree)
                    existing_4g_rootseq = self.xml_parser.extract_4g_rootseq(existing_tree)
                    existing_5g_nrcells = self.xml_parser.extract_5g_nrcells(existing_tree)
                    logger.info(f"Existing BTS ID: {existing_bts_id}")
                    logger.info(f"Existing sctpPortMin: {existing_sctp_port}")
                    logger.info(f"Existing 2G params: {existing_2g_params}")
                    logger.info(f"Existing 4G cells: {existing_4g_cells}")
                    logger.info(f"Existing 4G rootSeq: {existing_4g_rootseq}")
                    logger.info(f"Existing 5G NRCells: {existing_5g_nrcells}")
                
                if reference_5g_xml_path:
                    reference_tree = self.xml_parser.parse_file(reference_5g_xml_path)
                    reference_bts_id = self.xml_parser.extract_bts_id(reference_tree)
                    reference_sctp_port = self.xml_parser.extract_sctp_port_min(reference_tree)
                    reference_2g_params = self.xml_parser.extract_2g_parameters(reference_tree)
                    reference_4g_cells = self.xml_parser.extract_4g_cells(reference_tree)
                    reference_4g_rootseq = self.xml_parser.extract_4g_rootseq(reference_tree)
                    reference_5g_nrcells = self.xml_parser.extract_5g_nrcells(reference_tree)
                    logger.info(f"Reference BTS ID: {reference_bts_id}")
                    logger.info(f"Reference sctpPortMin: {reference_sctp_port}")
                    logger.info(f"Reference 2G params: {reference_2g_params}")
                    logger.info(f"Reference 4G cells: {reference_4g_cells}")
                    logger.info(f"Reference 4G rootSeq: {reference_4g_rootseq}")
                    logger.info(f"Reference 5G NRCells: {reference_5g_nrcells}")
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