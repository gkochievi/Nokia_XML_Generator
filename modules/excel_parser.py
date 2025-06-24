import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ExcelParser:
    """Parser for transmission and radio parameter Excel files"""
    
    def parse_transmission_excel(self, file_path):
        """Parse transmission Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert to dictionary for easy lookup
            transmission_data = {}
            for _, row in df.iterrows():
                station_name = str(row.get('Station_Name', '')).strip()
                if station_name:
                    transmission_data[station_name] = {
                        'om_ip': row.get('OM_IP', ''),
                        '2g_ip': row.get('2G_IP', ''),
                        '3g_ip': row.get('3G_IP', ''),
                        '4g_ip': row.get('4G_IP', ''),
                        '5g_ip': row.get('5G_IP', ''),
                        'gateway': row.get('Gateway', ''),
                        'vlan': row.get('VLAN', ''),
                        'subnet_mask': row.get('Subnet_Mask', '')
                    }
            
            return transmission_data
            
        except Exception as e:
            logger.error(f"Error parsing transmission Excel: {str(e)}")
            raise
    
    def parse_radio_excel(self, file_path):
        """Parse radio parameters Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert to dictionary
            radio_data = {}
            for _, row in df.iterrows():
                station_name = str(row.get('Station_Name', '')).strip()
                if station_name:
                    if station_name not in radio_data:
                        radio_data[station_name] = {
                            'sectors': [],
                            'carriers': [],
                            'frequencies': []
                        }
                    
                    # Add sector info
                    sector_info = {
                        'sector_id': row.get('Sector_ID', ''),
                        'antenna_count': row.get('Antenna_Count', ''),
                        'radio_module': row.get('Radio_Module', ''),
                        'frequency': row.get('Frequency', ''),
                        'carrier_id': row.get('Carrier_ID', '')
                    }
                    radio_data[station_name]['sectors'].append(sector_info)
            
            return radio_data
            
        except Exception as e:
            logger.error(f"Error parsing radio Excel: {str(e)}")
            raise