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
        debug_log = []  # Store debug messages for frontend
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            debug_log.append(f"Excel file loaded successfully. Shape: {df.shape} (rows x columns)")
            logger.info(f"Excel file loaded. Shape: {df.shape}")
            
            # Find station name (could use - or _ separators)
            station_variants = [
                station_name,
                station_name.replace('-', '_'),
                station_name.replace('_', '-')
            ]
            station_row = None
            found_station = None
            debug_log.append(f"Searching for station name. Original: '{station_name}', Variants: {station_variants}")
            logger.info(f"Searching for station name. Variants: {station_variants}")
            
            # Search for exact match (case-insensitive) in any cell
            searched_cells = 0
            for idx, row in df.iterrows():
                for col_idx, cell_value in enumerate(row):
                    searched_cells += 1
                    if pd.notna(cell_value):
                        cell_str = str(cell_value).strip()
                        for variant in station_variants:
                            if cell_str.lower() == variant.lower():
                                station_row = idx
                                found_station = cell_str
                                debug_log.append(f"✓ Station found! '{found_station}' at row {station_row}, column {col_idx}")
                                logger.info(f"Found station '{found_station}' at row {station_row}")
                                break
                        if station_row is not None:
                            break
                if station_row is not None:
                    break
            
            debug_log.append(f"Search completed. Searched {searched_cells} cells total")
            
            if station_row is None:
                debug_log.append(f"✗ Station '{station_name}' not found in Excel file")
                debug_log.append(f"Tried variants: {station_variants}")
                logger.warning(f"Station '{station_name}' not found in Excel file. Tried variants: {station_variants}")
                # Return debug info even when station not found
                return {
                    'station_name': None,
                    'station_row': None,
                    'technologies': {},
                    'routing_rules': {},
                    'debug_log': debug_log,
                    'success': False,
                    'error': f"Station '{station_name}' not found"
                }
            
            debug_log.append(f"Station found successfully. Proceeding with data extraction from row {station_row}...")
            
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
            
            debug_log.append("Starting data extraction from specified columns...")
            
            # Extract data from the station row
            network_data = {}
            extracted_count = 0
            empty_count = 0
            
            for param_name, col_idx in column_map.items():
                try:
                    if col_idx < len(df.columns):
                        value = df.iloc[station_row, col_idx]
                        if pd.notna(value):
                            network_data[param_name] = str(value).strip()
                            debug_log.append(f"✓ {param_name} (col {col_idx}): '{network_data[param_name]}'")
                            extracted_count += 1
                        else:
                            network_data[param_name] = None
                            debug_log.append(f"○ {param_name} (col {col_idx}): empty/null")
                            empty_count += 1
                    else:
                        network_data[param_name] = None
                        debug_log.append(f"✗ {param_name} (col {col_idx}): column not found in Excel")
                        logger.warning(f"Column {col_idx} ({param_name}) not found in Excel")
                        empty_count += 1
                except Exception as e:
                    network_data[param_name] = None
                    debug_log.append(f"✗ {param_name} (col {col_idx}): error reading - {str(e)}")
                    logger.error(f"Error reading {param_name} from column {col_idx}: {str(e)}")
                    empty_count += 1
            
            debug_log.append(f"Data extraction summary: {extracted_count} values extracted, {empty_count} empty/error")
            
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
                'routing_rules': self._extract_routing_rules(network_data),
                'debug_log': debug_log,
                'success': True
            }
            
            # Log technology summary
            debug_log.append("=== Technology Summary ===")
            valid_techs = []
            for tech, data in ip_plan_data['technologies'].items():
                has_vlan = bool(data.get('vlanId'))
                has_ip = bool(data.get('localIpAddr'))
                has_gateway = bool(data.get('gateway'))
                
                if has_vlan or has_ip:
                    valid_techs.append(tech)
                    debug_log.append(f"✓ {tech}: VLAN={data.get('vlanId')}, IP={data.get('localIpAddr')}, GW={data.get('gateway')}")
                else:
                    debug_log.append(f"○ {tech}: no data")
            
            debug_log.append(f"Valid technologies found: {len(valid_techs)} - {', '.join(valid_techs) if valid_techs else 'None'}")
            
            logger.info(f"Successfully parsed IP Plan data for station '{found_station}'")
            logger.debug(f"IP Plan data: {ip_plan_data}")
            
            return ip_plan_data
            
        except Exception as e:
            debug_log.append(f"✗ Critical error during Excel parsing: {str(e)}")
            logger.error(f"Error parsing IP Plan Excel: {str(e)}")
            return {
                'station_name': None,
                'station_row': None,
                'technologies': {},
                'routing_rules': {},
                'debug_log': debug_log,
                'success': False,
                'error': str(e)
            }
    
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