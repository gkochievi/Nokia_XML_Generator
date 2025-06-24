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
                 transmission_excel_path, output_folder):
        """Generate 5G modernization configuration"""
        try:
            # Parse input files
            existing_tree = self.xml_parser.parse_file(existing_xml_path)
            reference_5g_tree = self.xml_parser.parse_file(reference_5g_xml_path)
            transmission_data = self.excel_parser.parse_transmission_excel(transmission_excel_path)
            
            # Get transmission info for station
            station_data = transmission_data.get(station_name)
            if not station_data:
                raise ValueError(f"Station {station_name} not found in transmission Excel")
            
            # Clone existing configuration
            result_tree = etree.ElementTree(existing_tree.getroot())
            
            # Extract 5G elements from reference
            nrbts_elements = reference_5g_tree.xpath("//managedObject[contains(@class, 'NRBTS')]")
            nr_elements = reference_5g_tree.xpath("//managedObject[contains(@class, 'NR')]")
            
            # Add 5G elements to existing configuration
            root = result_tree.getroot()
            config_data = root.find(".//configData")
            
            if config_data is not None:
                # Add NRBTS and related elements
                for elem in nrbts_elements + nr_elements:
                    # Update element with station-specific data
                    updated_elem = self._update_element_with_station_data(
                        elem, station_name, station_data
                    )
                    config_data.append(updated_elem)
                
                # Update network configuration
                self._update_network_configuration(result_tree, station_data)
            
            # Generate output filename
            output_filename = f"{station_name}_5G_modernization.xml"
            output_path = os.path.join(output_folder, output_filename)
            
            # Write result
            result_tree.write(output_path, pretty_print=True, 
                            xml_declaration=True, encoding='UTF-8')
            
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