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
    
    def parse_ip_plan_excel(self, file_path, station_name):
        """Parse IP Plan Excel file and extract network parameters for a specific station"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            logger.info(f"Excel file loaded. Shape: {df.shape}")
            
            # Find station name (could use - or _ separators)
            station_variants = [
                station_name,
                station_name.replace('-', '_'),
                station_name.replace('_', '-')
            ]
            station_row = None
            found_station = None
            logger.info(f"Searching for station name. Variants: {station_variants}")
            # Search for exact match (case-insensitive) in any cell
            for idx, row in df.iterrows():
                for col_idx, cell_value in enumerate(row):
                    if pd.notna(cell_value):
                        cell_str = str(cell_value).strip()
                        for variant in station_variants:
                            if cell_str.lower() == variant.lower():
                                station_row = idx
                                found_station = cell_str
                                logger.info(f"Found station '{found_station}' at row {station_row}")
                                break
                        if station_row is not None:
                            break
                if station_row is not None:
                    break
            if station_row is None:
                logger.warning(f"Station '{station_name}' not found in Excel file. Tried variants: {station_variants}")
                return None
            
            # Column mappings (Excel columns are 0-indexed)
            column_map = {
                # VLANs
                'MGT_VLAN_ID': 6,   # G
                'GSM_VLAN_ID': 10,  # K  
                'WCDMA_VLAN_ID': 17, # R
                'LTE_VLAN': 26,     # AA
                '5G_VLAN': 36,      # AK
                
                # IPs
                'MGT_IP': 7,        # H
                'GSM_IP': 11,       # L
                'WCDMA_IP': 18,     # S
                'LTE_IP': 27,       # AB
                '5G_IP': 37,        # AL
                
                # Masks
                'MGT_MASK': 8,      # I
                'GSM_MASK': 12,     # M
                'WCDMA_MASK': 19,   # T
                'LTE_MASK': 28,     # AC
                '5G_MASK': 38,      # AM
                
                # Gateways
                'MGT_GW': 9,        # J
                'GSM_GW': 13,       # N
                'WCDMA_GW': 20,     # U
                'LTE_GW': 29,       # AD
                '5G_GW': 39         # AN
            }
            
            # Extract data from the station row
            network_data = {}
            
            for param_name, col_idx in column_map.items():
                try:
                    if col_idx < len(df.columns):
                        value = df.iloc[station_row, col_idx]
                        if pd.notna(value):
                            network_data[param_name] = str(value).strip()
                        else:
                            network_data[param_name] = None
                    else:
                        network_data[param_name] = None
                        logger.warning(f"Column {col_idx} ({param_name}) not found in Excel")
                except Exception as e:
                    logger.error(f"Error reading {param_name} from column {col_idx}: {str(e)}")
                    network_data[param_name] = None
            
            # Group data by technology
            ip_plan_data = {
                'station_name': found_station,
                'station_row': station_row,
                'technologies': {
                    'OAM': {
                        'userLabel': 'OAM',
                        'vlanId': network_data.get('MGT_VLAN_ID'),
                        'localIpAddr': network_data.get('MGT_IP'),
                        'localIpPrefixLength': network_data.get('MGT_MASK'),
                        'gateway': network_data.get('MGT_GW')
                    },
                    '2G': {
                        'userLabel': '2G',
                        'vlanId': network_data.get('GSM_VLAN_ID'),
                        'localIpAddr': network_data.get('GSM_IP'),
                        'localIpPrefixLength': network_data.get('GSM_MASK'),
                        'gateway': network_data.get('GSM_GW')
                    },
                    '3G': {
                        'userLabel': '3G',
                        'vlanId': network_data.get('WCDMA_VLAN_ID'),
                        'localIpAddr': network_data.get('WCDMA_IP'),
                        'localIpPrefixLength': network_data.get('WCDMA_MASK'),
                        'gateway': network_data.get('WCDMA_GW')
                    },
                    '4G': {
                        'userLabel': '4G',
                        'vlanId': network_data.get('LTE_VLAN'),
                        'localIpAddr': network_data.get('LTE_IP'),
                        'localIpPrefixLength': network_data.get('LTE_MASK'),
                        'gateway': network_data.get('LTE_GW')
                    },
                    '5G': {
                        'userLabel': '5G',
                        'vlanId': network_data.get('5G_VLAN'),
                        'localIpAddr': network_data.get('5G_IP'),
                        'localIpPrefixLength': network_data.get('5G_MASK'),
                        'gateway': network_data.get('5G_GW')
                    }
                },
                'routing_rules': self._extract_routing_rules(network_data)
            }
            
            logger.info(f"Successfully parsed IP Plan data for station '{found_station}'")
            logger.debug(f"IP Plan data: {ip_plan_data}")
            
            return ip_plan_data
            
        except Exception as e:
            logger.error(f"Error parsing IP Plan Excel: {str(e)}")
            raise
    
    def _extract_routing_rules(self, network_data):
        """Extract IPv4 routing rules based on gateway patterns"""
        routing_rules = {}
        
        # IPRT-1 rules
        iprt1_mappings = {
            '10.110': network_data.get('MGT_GW'),      # OAM
            '10.171': network_data.get('GSM_GW'),      # 2G
            '10.141': network_data.get('WCDMA_GW'),    # 3G
            '10.111': network_data.get('LTE_GW')       # 4G
        }
        
        # IPRT-2 NR rules
        iprt2_mappings = {
            '10.112': network_data.get('5G_GW')        # 5G
        }
        
        routing_rules['IPRT-1'] = iprt1_mappings
        routing_rules['IPRT-2_NR'] = iprt2_mappings
        
        return routing_rules