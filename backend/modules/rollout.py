import os
from lxml import etree
import logging
from .xml_parser import XMLParser
from .excel_parser import ExcelParser
from copy import deepcopy

logger = logging.getLogger(__name__)

class RolloutGenerator:
    """Generator for new rollout configurations"""
    
    def __init__(self):
        self.xml_parser = XMLParser()
        self.excel_parser = ExcelParser()
    
    def generate(self, station_name, reference_xml_path, radio_excel_path, 
                 transmission_excel_path, output_folder):
        """Generate new rollout configuration"""
        try:
            # Parse input files
            reference_tree = self.xml_parser.parse_file(reference_xml_path)
            radio_data = self.excel_parser.parse_radio_excel(radio_excel_path)
            transmission_data = self.excel_parser.parse_transmission_excel(transmission_excel_path)
            
            # Get data for station
            station_radio = radio_data.get(station_name)
            station_transmission = transmission_data.get(station_name)
            
            if not station_radio:
                raise ValueError(f"Station {station_name} not found in radio Excel")
            if not station_transmission:
                raise ValueError(f"Station {station_name} not found in transmission Excel")
            
            # Clone reference configuration
            result_tree = etree.ElementTree(reference_tree.getroot())
            
            # Update with station-specific data
            self._update_station_configuration(
                result_tree, station_name, station_radio, station_transmission
            )
            
            # Generate output filename
            output_filename = f"{station_name}_rollout.xml"
            output_path = os.path.join(output_folder, output_filename)
            
            # Write result
            result_tree.write(output_path, pretty_print=True, 
                            xml_declaration=True, encoding='UTF-8')
            
            return output_filename
            
        except Exception as e:
            logger.error(f"Error generating rollout: {str(e)}")
            raise
    
    def _update_station_configuration(self, tree, station_name, radio_data, transmission_data):
        """Update configuration tree with station-specific data"""
        # Update station identifiers (distName)
        for elem in tree.xpath("//managedObject"):
            if 'distName' in elem.attrib:
                dist_name = elem.attrib['distName']
                parts = dist_name.split('/')
                for i, part in enumerate(parts):
                    if part.startswith('MRBTS-'):
                        parts[i] = f"MRBTS-{station_name}"
                    if part.startswith('NRBTS-'):
                        parts[i] = f"NRBTS-{station_name}"
                elem.attrib['distName'] = '/'.join(parts)
        # Update IP configurations (IPNO)
        for ipno in tree.xpath("//managedObject[contains(@class, 'IPNO')]"):
            for p in ipno.findall(".//p"):
                if p.get('name') == 'ipAddress':
                    p.text = transmission_data.get('5g_ip', '') or transmission_data.get('om_ip', '')
                elif p.get('name') == 'gateway':
                    p.text = transmission_data.get('gateway', '')
                elif p.get('name') == 'vlanId':
                    p.text = str(transmission_data.get('vlan', ''))
        # Update radio configurations (RMOD, sectors, carriers, frequencies)
        # (საჭიროებისამებრ დაამატე მეტი ლოგიკა radio_data-სთვის)
        for rmod in tree.xpath("//managedObject[contains(@class, 'RMOD')]"):
            for p in rmod.findall(".//p"):
                if p.get('name') == 'prodCodePlanned':
                    if radio_data['sectors']:
                        p.text = radio_data['sectors'][0].get('radio_module', '')
        # (საჭიროებისამებრ დაამატე სხვა პარამეტრების განახლება)