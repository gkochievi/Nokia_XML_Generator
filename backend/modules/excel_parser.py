import pandas as pd
import logging
from constants import IP_PLAN_COLUMNS, IPRT1_PREFIX_TO_TECH, IPRT2_PREFIX_TO_TECH

logger = logging.getLogger(__name__)

class ExcelParser:
    """Parser for IP Plan Excel files (Nokia IP Plan template)."""

    def parse_ip_plan_excel(self, file_path, station_name):
        """Parse IP Plan Excel file and extract network parameters for a specific station"""
        debug_log = []  # Store debug messages for frontend
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            debug_log.append(f"Excel file loaded successfully. Shape: {df.shape} (rows x columns)")
            logger.info(f"Excel file loaded. Shape: {df.shape}")
            
            # Find station name (could use - or _ separators; tolerate stray whitespace)
            import re as _re
            def _collapse_ws(s: str) -> str:
                return _re.sub(r'\s+', '', s or '')

            station_variants = [
                station_name,
                station_name.replace('-', '_'),
                station_name.replace('_', '-')
            ]
            normalized_variants = {_collapse_ws(v).lower() for v in station_variants}
            station_row = None
            found_station = None
            debug_log.append(f"Searching for station name. Original: '{station_name}', Variants: {station_variants}")
            logger.info(f"Searching for station name. Variants: {station_variants}")

            # Search for exact match (case-insensitive, whitespace-insensitive) in any cell
            searched_cells = 0
            for idx, row in df.iterrows():
                for col_idx, cell_value in enumerate(row):
                    searched_cells += 1
                    if pd.notna(cell_value):
                        cell_str = str(cell_value).strip()
                        if _collapse_ws(cell_str).lower() in normalized_variants:
                            station_row = idx
                            found_station = cell_str
                            debug_log.append(f"✓ Station found! '{found_station}' at row {station_row}, column {col_idx}")
                            logger.info(f"Found station '{found_station}' at row {station_row}")
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
            
            column_map = IP_PLAN_COLUMNS
            
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
        
        # Map routing prefixes to gateways from network data
        tech_to_gw_key = {'OAM': 'MGT_GW', '2G': 'GSM_GW', '3G': 'WCDMA_GW', '4G': 'LTE_GW', '5G': '5G_GW'}

        iprt1_mappings = {
            prefix: network_data.get(tech_to_gw_key.get(tech, ''))
            for prefix, tech in IPRT1_PREFIX_TO_TECH.items()
        }

        iprt2_mappings = {
            prefix: network_data.get(tech_to_gw_key.get(tech, ''))
            for prefix, tech in IPRT2_PREFIX_TO_TECH.items()
        }
        
        routing_rules['IPRT-1'] = iprt1_mappings
        routing_rules['IPRT-2 NR'] = iprt2_mappings

        return routing_rules