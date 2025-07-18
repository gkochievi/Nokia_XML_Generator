import os
import re
from lxml import etree
import logging
from .xml_parser import XMLParser

logger = logging.getLogger(__name__)

class TemplateManager:
    """Manager for 5G modernization templates and parameter replacement"""
    
    def __init__(self):
        self.xml_parser = XMLParser()
    
    def extract_bts_info(self, xml_file_path):
        """
        Extract BTS name and ID from existing configuration XML
        
        Args:
            xml_file_path (str): Path to existing BTS XML configuration
            
        Returns:
            dict: Dictionary containing bts_name, bts_id, bts_name_dash
        """
        try:
            tree = self.xml_parser.parse_file(xml_file_path)
            
            # Find MRBTS managedObject - try different XPath patterns
            mrbts_elements = tree.xpath("//managedObject[contains(@class, 'MRBTS')]")
            if not mrbts_elements:
                # Try alternative patterns
                mrbts_elements = tree.xpath("//*[@class and contains(@class, 'MRBTS')]")
            if not mrbts_elements:
                # Try without namespace
                mrbts_elements = tree.xpath("//managedObject[contains(@distName, 'MRBTS')]")
            
            if not mrbts_elements:
                raise ValueError("MRBTS managedObject not found in XML")
            
            mrbts = mrbts_elements[0]
            
            # Extract BTS ID from distName (e.g., "MRBTS-90217" -> "90217")
            dist_name = mrbts.get('distName', '')
            bts_id = None
            
            # Pattern to extract ID from MRBTS-xxxxx format
            id_match = re.search(r'MRBTS-(\d+)', dist_name)
            if id_match:
                bts_id = id_match.group(1)
            
            # Extract BTS name from btsName parameter
            bts_name = None
            bts_name_elem = mrbts.find(".//p[@name='btsName']")
            if bts_name_elem is not None and bts_name_elem.text:
                bts_name = bts_name_elem.text.strip()
            
            # Create dash version of BTS name (replace underscore with dash)
            bts_name_dash = None
            if bts_name:
                bts_name_dash = bts_name.replace('_', '-')
            
            result = {
                'bts_name': bts_name,
                'bts_id': bts_id,
                'bts_name_dash': bts_name_dash,
                'dist_name': dist_name
            }
            
            logger.info(f"Extracted BTS info: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting BTS info: {str(e)}")
            raise
    
    def replace_bts_parameters_in_template(self, template_path, bts_info, output_path):
        """
        Replace BTS parameters in template XML with extracted values
        
        Args:
            template_path (str): Path to 5G template XML file
            bts_info (dict): BTS information from extract_bts_info()
            output_path (str): Path where to save the modified template
            
        Returns:
            str: Path to the output file
        """
        try:
            # Read template content as text for string replacement
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Extract template placeholders (we'll need to identify what placeholders are used)
            # For now, let's assume common patterns like MBTS_Name, 90217, etc.
            
            bts_name = bts_info.get('bts_name')
            bts_id = bts_info.get('bts_id')
            bts_name_dash = bts_info.get('bts_name_dash')
            
            if not bts_name or not bts_id:
                raise ValueError("BTS name or ID not found in source configuration")
            
            modified_content = template_content
            
            # Replace BTS Name (both underscore and dash versions)
            # Common patterns in Nokia XML:
            # - btsName parameter values
            # - distName references
            # - id references
            
            # 1. Replace template BTS name with actual BTS name (underscore version)
            modified_content = self._replace_template_bts_name(modified_content, bts_name)
            
            # 2. Replace template BTS name with dash version where needed
            modified_content = self._replace_template_bts_name_dash(modified_content, bts_name_dash)
            
            # 3. Replace template BTS ID with actual BTS ID
            modified_content = self._replace_template_bts_id(modified_content, bts_id)
            
            # Write modified content to output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            logger.info(f"Template modified and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error replacing BTS parameters in template: {str(e)}")
            raise
    
    def _replace_template_bts_name(self, content, bts_name):
        """Replace template BTS name patterns with actual BTS name (underscore version)"""
        
        # Template BTS name patterns from actual templates
        placeholders = [
            'TBLS_Oriental_Studies_Inst',  # Actual template name
            'MBTS_Name',
            'BTS_NAME', 
            'TEMPLATE_BTS_NAME',
            'SITE_NAME'
        ]
        
        modified_content = content
        for placeholder in placeholders:
            if placeholder in content:
                modified_content = modified_content.replace(placeholder, bts_name)
                logger.debug(f"Replaced '{placeholder}' with '{bts_name}'")
        
        return modified_content
    
    def _replace_template_bts_name_dash(self, content, bts_name_dash):
        """Replace template BTS name patterns with dash version"""
        
        # Template BTS name patterns with dash (from cell names)
        placeholders = [
            'TBLS-Oriental-Studies-Inst',  # Dash version
            'MBTS-Name',
            'BTS-NAME',
            'TEMPLATE-BTS-NAME',
            'SITE-NAME'
        ]
        
        modified_content = content
        for placeholder in placeholders:
            if placeholder in content:
                modified_content = modified_content.replace(placeholder, bts_name_dash)
                logger.debug(f"Replaced '{placeholder}' with '{bts_name_dash}'")
        
        return modified_content
    
    def _replace_template_bts_id(self, content, bts_id):
        """Replace template BTS ID patterns with actual BTS ID"""
        
        # Common template placeholders for BTS ID
        placeholders = [
            '90217',  # Example template ID
            'TEMPLATE_ID',
            'BTS_ID',
            'SITE_ID'
        ]
        
        modified_content = content
        for placeholder in placeholders:
            if placeholder in content:
                modified_content = modified_content.replace(placeholder, bts_id)
                logger.debug(f"Replaced '{placeholder}' with '{bts_id}'")
        
        # Also replace in MRBTS distName patterns
        # Pattern: MRBTS-{template_id} -> MRBTS-{actual_id}
        mrbts_pattern = r'MRBTS-\d+'
        replacement = f'MRBTS-{bts_id}'
        
        # Find all MRBTS-xxxxx patterns and replace with actual ID
        modified_content = re.sub(mrbts_pattern, replacement, modified_content)
        logger.debug(f"Replaced MRBTS-xxx patterns with 'MRBTS-{bts_id}'")
        
        return modified_content
    
    def analyze_template_compatibility(self, config_path):
        """
        Analyze existing configuration to determine compatible templates
        
        Args:
            config_path (str): Path to existing BTS configuration
            
        Returns:
            dict: Analysis results with recommended templates
        """
        try:
            tree = self.xml_parser.parse_file(config_path)
            
            analysis = {
                'sectors': 0,
                'has_2g': False,
                'has_3g': False,
                'has_4g': False,
                'rrh_type': None,
                'recommended_templates': []
            }
            
            # Count sectors by analyzing LNCEL elements (4G cells)
            lncel_elements = tree.xpath("//managedObject[contains(@class, 'LNCEL')]")
            sectors = set()
            for lncel in lncel_elements:
                # Extract sector info from cell ID or name
                cell_id = None
                for p in lncel.findall(".//p"):
                    if p.get('name') in ['cellId', 'localCellId']:
                        cell_id = p.text
                        break
                
                if cell_id and len(cell_id) >= 2:
                    sector = cell_id[-1]  # Last digit usually indicates sector
                    sectors.add(sector)
            
            analysis['sectors'] = len(sectors) if sectors else 3  # Default to 3 if unclear
            
            # Check for different technologies
            analysis['has_2g'] = len(tree.xpath("//managedObject[contains(@class, 'BTS')]")) > 0
            analysis['has_3g'] = len(tree.xpath("//managedObject[contains(@class, 'WCEL')]")) > 0  
            analysis['has_4g'] = len(lncel_elements) > 0
            
            # Determine RRH type (simplified analysis)
            rmod_elements = tree.xpath("//managedObject[contains(@class, 'RMOD')]")
            for rmod in rmod_elements:
                for p in rmod.findall(".//p"):
                    if p.get('name') == 'prodCodePlanned' and p.text:
                        if 'AHEGA' in p.text:
                            analysis['rrh_type'] = 'AHEGA'
                            break
                        elif 'AHEGB' in p.text:
                            analysis['rrh_type'] = 'AHEGB'
                            break
            
            # Generate recommended templates based on analysis
            templates = []
            
            sector_suffix = f"S{analysis['sectors']}"
            rrh_suffix = analysis['rrh_type'] if analysis['rrh_type'] else 'AHEGA'
            
            if analysis['has_2g']:
                templates.append(f"5G-{sector_suffix}-{rrh_suffix}")
            else:
                templates.append(f"5G-no2G-{sector_suffix}-{rrh_suffix}")
            
            analysis['recommended_templates'] = templates
            
            logger.info(f"Template analysis complete: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing template compatibility: {str(e)}")
            raise
    
    def validate_template_replacement(self, original_path, modified_path):
        """
        Validate that template replacement was successful
        
        Args:
            original_path (str): Path to original template
            modified_path (str): Path to modified template
            
        Returns:
            dict: Validation results
        """
        try:
            # Parse both XML files to validate structure
            original_tree = self.xml_parser.parse_file(original_path)
            modified_tree = self.xml_parser.parse_file(modified_path)
            
            validation = {
                'valid_xml': True,
                'structure_preserved': True,
                'bts_name_replaced': False,
                'bts_id_replaced': False,
                'errors': []
            }
            
            # Check if BTS name was properly replaced
            mrbts_modified = modified_tree.xpath("//managedObject[contains(@class, 'MRBTS')]")
            if mrbts_modified:
                bts_name_elem = mrbts_modified[0].find(".//p[@name='btsName']")
                if bts_name_elem is not None and bts_name_elem.text:
                    # Check if it's not a template placeholder anymore
                    if not any(placeholder in bts_name_elem.text.upper() 
                             for placeholder in ['TEMPLATE', 'MBTS_NAME', 'BTS_NAME']):
                        validation['bts_name_replaced'] = True
            
            # Check if BTS ID was properly replaced  
            if mrbts_modified:
                dist_name = mrbts_modified[0].get('distName', '')
                if 'MRBTS-' in dist_name and not 'TEMPLATE' in dist_name.upper():
                    validation['bts_id_replaced'] = True
            
            logger.info(f"Template validation complete: {validation}")
            return validation
            
        except etree.XMLSyntaxError as e:
            return {
                'valid_xml': False,
                'structure_preserved': False,
                'bts_name_replaced': False,
                'bts_id_replaced': False,
                'errors': [f"XML syntax error: {str(e)}"]
            }
        except Exception as e:
            logger.error(f"Error validating template replacement: {str(e)}")
            return {
                'valid_xml': False,
                'structure_preserved': False,
                'bts_name_replaced': False,
                'bts_id_replaced': False,
                'errors': [str(e)]
            } 