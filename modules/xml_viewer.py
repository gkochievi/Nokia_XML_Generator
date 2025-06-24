import json
from lxml import etree
import logging

logger = logging.getLogger(__name__)

class XMLViewer:
    """Viewer for Nokia WebEM XML configuration files"""
    
    def extract_configuration_data(self, tree):
        """Extract key configuration data from XML tree (namespace-აგნოსტიკურად)"""
        try:
            data = {
                'stationInfo': self._extract_station_info(tree),
                'networkInfo': self._extract_network_info(tree),
                'radioInfo': self._extract_radio_info(tree),
                'hardwareInfo': self._extract_hardware_info(tree),
                'neighborInfo': self._extract_neighbor_info(tree)
            }
            return data
        except Exception as e:
            logger.error(f"Error extracting configuration data: {str(e)}")
            return {}
    
    def _findall_managed_objects(self, tree):
        # მოძებნოს ყველა managedObject ნებისმიერი namespace-ით
        return tree.xpath("//*[local-name()='managedObject']")
    
    def _extract_station_info(self, tree):
        """Extract basic station information"""
        info = {}
        managed_objects = self._findall_managed_objects(tree)
        # MRBTS
        mrbts = [mo for mo in managed_objects if mo.get('class','').endswith('MRBTS')]
        if mrbts:
            mrbts_elem = mrbts[0]
            info['mrbtsId'] = mrbts_elem.get('distName', '').split('-')[-1]
            info['version'] = mrbts_elem.get('version', '')
            # ამოიღე BTS სახელი
            bts_name_elem = mrbts_elem.xpath("./*[local-name()='p'][@name='btsName']")
            info['btsName'] = bts_name_elem[0].text if bts_name_elem else ''
        # NRBTS
        nrbts = [mo for mo in managed_objects if mo.get('class','').endswith('NRBTS')]
        info['has5G'] = bool(nrbts)
        info['nrbtsId'] = nrbts[0].get('distName', '').split('-')[-1] if nrbts else ''
        # LNBTS
        lnbts = [mo for mo in managed_objects if mo.get('class','').endswith('LNBTS')]
        info['has4G'] = bool(lnbts)
        info['lnbtsId'] = lnbts[0].get('distName', '').split('-')[-1] if lnbts else ''
        # WNBTS (3G)
        wnbts = [mo for mo in managed_objects if mo.get('class','').endswith('WNBTS')]
        info['has3G'] = bool(wnbts)
        info['wnbtsId'] = wnbts[0].get('distName', '').split('-')[-1] if wnbts else ''
        # BCF (2G)
        bcf = [mo for mo in managed_objects if mo.get('class','').endswith('BCF')]
        info['has2G'] = bool(bcf)
        info['bcfId'] = bcf[0].get('distName', '').split('-')[-1] if bcf else ''
        return info
    
    def _extract_network_info(self, tree):
        """Extract network configuration"""
        info = {
            'ipAddresses': [],
            'vlans': [],
            'routes': []
        }
        managed_objects = self._findall_managed_objects(tree)
        logger.warning(f"Managed objects: {len(managed_objects)}")
        vlanifs = [mo for mo in managed_objects if mo.get('class','').endswith('VLANIF')]
        logger.warning(f"VLANIF count: {len(vlanifs)}")
        for vlanif in vlanifs:
            logger.warning(f"VLANIF class: {vlanif.get('class')}, distName: {vlanif.get('distName')}")
            vlan_data = {}
            for p in vlanif.xpath('./*[local-name()="p"]'):
                name = p.get('name')
                if name in ['vlanId', 'userLabel']:
                    vlan_data[name] = p.text
            if vlan_data:
                info['vlans'].append(vlan_data)

        # --- VLANIF mapping by distName ---
        vlanif_map = {}
        vlanifs = [mo for mo in managed_objects if mo.get('class','').endswith('VLANIF')]
        for vlanif in vlanifs:
            vlanif_data = {'vlanId': '', 'userLabel': '', 'distName': vlanif.get('distName')}
            for p in vlanif.xpath('./*[local-name()="p"]'):
                name = p.get('name')
                if name == 'vlanId':
                    vlanif_data['vlanId'] = p.text
                elif name == 'userLabel':
                    vlanif_data['userLabel'] = p.text
            vlanif_map[vlanif_data['distName']] = vlanif_data

        # --- IPIF mapping by distName ---
        ipif_map = {ipif.get('distName'): ipif for ipif in [mo for mo in managed_objects if mo.get('class','').endswith('IPIF')]}

        # --- Combine IPADDRESSV4 with parent IPIF and VLANIF ---
        combined = []
        ipaddrs = [mo for mo in managed_objects if mo.get('class','').endswith('IPADDRESSV4')]
        for ipaddr in ipaddrs:
            ip_data = {}
            for p in ipaddr.xpath('./*[local-name()="p"]'):
                name = p.get('name')
                if name in ['localIpAddr', 'localIpPrefixLength']:
                    ip_data[name] = p.text
            # Find parent IPIF
            ipif_dn = '/'.join(ipaddr.get('distName', '').split('/')[:-1])
            ipif = ipif_map.get(ipif_dn)
            label = ''
            interface_dn = ''
            if ipif is not None:
                user_label_elem = ipif.xpath("./*[local-name()='p'][@name='userLabel']")
                if user_label_elem:
                    label = user_label_elem[0].text
                interface_dn_elem = ipif.xpath("./*[local-name()='p'][@name='interfaceDN']")
                if interface_dn_elem:
                    interface_dn = interface_dn_elem[0].text
            vlan_id = ''
            vlan_label = ''
            if interface_dn and interface_dn in vlanif_map:
                vlan_id = vlanif_map[interface_dn]['vlanId']
                vlan_label = vlanif_map[interface_dn]['userLabel']
            combined.append({
                'label': label or vlan_label,
                'vlanId': vlan_id,
                'ip': ip_data.get('localIpAddr', ''),
                'prefix': ip_data.get('localIpPrefixLength', '')
            })
        info['vlan_ip_combined'] = combined
        logger.warning(f'vlan_ip_combined: {combined}')
        
        return info
    
    def _extract_radio_info(self, tree):
        """Extract radio configuration"""
        info = {
            'sectors': [],
            'carriers': [],
            'antennas': [],
            'technologies': [],
            'sectorCount': 0,
            'sectorDetails': {},
            'cells': {'3G': [], '4G': [], '5G': []}
        }
        managed_objects = self._findall_managed_objects(tree)
        # ტექნოლოგიები
        if any(mo.get('class','').endswith('NRCELL') for mo in managed_objects):
            info['technologies'].append('5G')
        if any(mo.get('class','').endswith('LNCEL') for mo in managed_objects):
            info['technologies'].append('4G')
        if any(mo.get('class','').endswith('WCEL') or mo.get('class','').endswith('WNCEL') for mo in managed_objects):
            info['technologies'].append('3G')
        if any(mo.get('class','').endswith('BCF') for mo in managed_objects):
            info['technologies'].append('2G')

        # --- Count sectors and carriers by Cell ID logic ---
        # 3G
        wcel_objs = [mo for mo in managed_objects if mo.get('class','').endswith('WCEL') or mo.get('class','').endswith('WNCEL')]
        wcel_cellids = []
        for wcel in wcel_objs:
            dn = wcel.get('distName', '')
            if '-' in dn:
                cellid = dn.split('-')[-1]
                wcel_cellids.append(cellid)
        logger.warning(f'3G WCEL cellids: {wcel_cellids}')
        wcel_sectors = set()
        wcel_carriers = {}
        for cid in wcel_cellids:
            if cid and len(cid) == 2 and cid.isdigit():
                sector = cid[1]  # მეორე ციფრი სექტორი
                carrier = cid[0] # პირველი ციფრი ქერიერი
                wcel_sectors.add(sector)
                wcel_carriers.setdefault(sector, set()).add(carrier)
        logger.warning(f'3G WCEL sectors: {wcel_sectors}, carriers: {wcel_carriers}')
        # 4G
        lncel_objs = [mo for mo in managed_objects if mo.get('class','').endswith('LNCEL')]
        lncel_cellids = []
        for lncel in lncel_objs:
            dn = lncel.get('distName', '')
            if '-' in dn:
                cellid = dn.split('-')[-1]
                lncel_cellids.append(cellid)
        logger.warning(f'4G LNCEL cellids: {lncel_cellids}')
        lncel_sectors = set()
        lncel_carriers = {}
        for cid in lncel_cellids:
            if cid and len(cid) == 2 and cid.isdigit():
                sector = cid[1]
                carrier = cid[0]
                lncel_sectors.add(sector)
                lncel_carriers.setdefault(sector, set()).add(carrier)
        logger.warning(f'4G LNCEL sectors: {lncel_sectors}, carriers: {lncel_carriers}')
        # 5G
        nrcell_objs = [mo for mo in managed_objects if mo.get('class','').endswith('NRCELL')]
        nrcell_cellids = []
        for nrcell in nrcell_objs:
            dn = nrcell.get('distName', '')
            if '-' in dn:
                cellid = dn.split('-')[-1]
                nrcell_cellids.append(cellid)
        logger.warning(f'5G NRCELL cellids: {nrcell_cellids}')
        nrcell_sectors = set()
        nrcell_carriers = {}
        for cid in nrcell_cellids:
            if cid and len(cid) == 3 and cid.isdigit():
                sector = cid[2]   # მესამე ციფრი სექტორი
                carrier = cid[1]  # მეორე ციფრი ქერიერი
                nrcell_sectors.add(sector)
                nrcell_carriers.setdefault(sector, set()).add(carrier)
        logger.warning(f'5G NRCELL sectors: {nrcell_sectors}, carriers: {nrcell_carriers}')
        # 2G (GNCEL)
        gncel_objs = [mo for mo in managed_objects if mo.get('class','').endswith('GNCEL')]
        gncel_cellids = []
        for gncel in gncel_objs:
            dn = gncel.get('distName', '')
            if '-' in dn:
                cellid = dn.split('-')[-1]
                gncel_cellids.append(cellid)
        logger.warning(f'2G GNCEL cellids: {gncel_cellids}')
        gncel_sectors = set()
        for cid in gncel_cellids:
            if cid and cid.isdigit():
                sector = cid[-1]  # ბოლო ციფრი სექტორი
                gncel_sectors.add(sector)
        logger.warning(f'2G GNCEL sectors: {gncel_sectors}')
        # Max sector count across all technologies
        info['sectorCount'] = max(len(wcel_sectors), len(lncel_sectors), len(nrcell_sectors), len(gncel_sectors), 0)
        info['sectorDetails'] = {
            '2G': {s: 1 for s in gncel_sectors},  # always one carrier
            '3G': {s: len(wcel_carriers[s]) for s in wcel_carriers},
            '4G': {s: len(lncel_carriers[s]) for s in lncel_carriers},
            '5G': {s: len(nrcell_carriers[s]) for s in nrcell_carriers},
        }
        
        # Extract antenna information
        antls = [mo for mo in managed_objects if mo.get('class','').endswith('ANTL')]
        for antl in antls:
            antenna_data = {
                'id': antl.get('distName', '').split('/')[-1],
                'parameters': {}
            }
            for p in antl.findall(".//p"):
                name = p.get('name')
                if name in ['antPortId', 'totalLoss', 'antennaPathDelayDL', 'antennaPathDelayUL']:
                    antenna_data['parameters'][name] = p.text
            info['antennas'].append(antenna_data)
        
        # Extract detailed cell info for each technology
        info['cells'] = {'3G': [], '4G': [], '5G': []}

        # 3G (WCEL/WNCEL)
        for wcel in [mo for mo in managed_objects if mo.get('class','').endswith('WCEL') or mo.get('class','').endswith('WNCEL')]:
            cell = {}
            for p in wcel.xpath('./*[local-name()="p"]'):
                name = p.get('name')
                if name == 'lCelwDN':
                    # Cell ID: last part after '/' (e.g. LCELW-11)
                    val = p.text or ''
                    cell['cellId'] = val.split('/')[-1] if '/' in val else val
                elif name == 'defaultCarrier':
                    cell['uarfcnDl'] = p.text
                elif name == 'maxCarrierPower':
                    cell['maxTxPower'] = p.text
                # fallback for old fields
                elif name == 'cellId' and 'cellId' not in cell:
                    cell['cellId'] = p.text
                elif name == 'uarfcnDl' and 'uarfcnDl' not in cell:
                    cell['uarfcnDl'] = p.text
                elif name == 'maxTxPower' and 'maxTxPower' not in cell:
                    cell['maxTxPower'] = p.text
            info['cells']['3G'].append(cell)

        # 4G (LNCEL)
        # Build a map of LNCEL_FDD by parent LNCEL distName
        lncel_fdd_map = {}
        for lncel_fdd in [mo for mo in managed_objects if mo.get('class','').endswith('LNCEL_FDD')]:
            parent_dn = '/'.join(lncel_fdd.get('distName', '').split('/')[:-1])
            lncel_fdd_map.setdefault(parent_dn, []).append(lncel_fdd)

        for lncel in [mo for mo in managed_objects if mo.get('class','').endswith('LNCEL')]:
            cell = {}
            # Cell ID from distName (LNCEL-XX)
            dn = lncel.get('distName', '')
            cell['cellId'] = dn.split('-')[-1] if '-' in dn else ''
            for p in lncel.xpath('./*[local-name()="p"]'):
                name = p.get('name')
                if name == 'cellName':
                    cell['cellName'] = p.text
                elif name == 'lcrId':
                    cell['localCellId'] = p.text
                elif name == 'phyCellId':
                    cell['phyCellId'] = p.text
                elif name == 'tac':
                    cell['trackingAreaCode'] = p.text
            # Find LNCEL_FDD child for extra params
            lncel_fdd_list = lncel_fdd_map.get(dn, [])
            for lncel_fdd in lncel_fdd_list:
                for p in lncel_fdd.xpath('./*[local-name()="p"]'):
                    name = p.get('name')
                    if name == 'rootSeqIndex':
                        cell['rachRootSequence'] = p.text
                    elif name == 'earfcnDL':
                        cell['earfcnDL'] = p.text
                    elif name == 'earfcnUL':
                        cell['earfcnUL'] = p.text
                    elif name == 'dlMimoMode':
                        cell['mimoMode'] = p.text
                    elif name == 'dlChBw':
                        cell['bandwidth'] = p.text
            info['cells']['4G'].append(cell)

        # 5G (NRCELL)
        # Build a map of NRCELL_FDD by parent NRCELL distName
        nrcell_fdd_map = {}
        for nrcell_fdd in [mo for mo in managed_objects if mo.get('class','').endswith('NRCELL_FDD')]:
            parent_dn = '/'.join(nrcell_fdd.get('distName', '').split('/')[:-1])
            nrcell_fdd_map.setdefault(parent_dn, []).append(nrcell_fdd)
        
        # Build a map of NRHOIF by parent NRCELL distName
        nrhoif_map = {}
        for nrhoif in [mo for mo in managed_objects if mo.get('class','').endswith('NRHOIF')]:
            parent_dn = '/'.join(nrhoif.get('distName', '').split('/')[:-1])
            nrhoif_map.setdefault(parent_dn, []).append(nrhoif)

        # Only process NRCELL objects, skip NRADJNRCELL (neighbors)
        for nrcell in [mo for mo in managed_objects if mo.get('class','').endswith('NRCELL') and not mo.get('class','').endswith('NRADJNRCELL')]:
            cell = {}
            dn = nrcell.get('distName', '')
            cell['cellId'] = dn.split('-')[-1] if '-' in dn else ''
            for p in nrcell.xpath('./*[local-name()="p"]'):
                name = p.get('name')
                if name == 'cellName':
                    cell['cellName'] = p.text
                elif name == 'cellId':
                    cell['cellId'] = p.text
                elif name == 'lcrId':
                    cell['localCellId'] = p.text
                elif name == 'physCellId':
                    cell['phyCellId'] = p.text
                elif name == 'cellTechnology':
                    cell['cellTechnology'] = p.text
                elif name == 'nrCellType':
                    cell['cellWorkingType'] = p.text
                elif name == 'freqBandIndicatorNR':
                    cell['frequencyBand'] = p.text
                elif name == 'pMax':
                    cell['cellPower'] = p.text
                elif name == 'chBw':
                    cell['bandwidthDL'] = p.text
                    cell['bandwidthUL'] = p.text
                elif name == 'nrarfcn':
                    cell['nrarfcnDL'] = p.text
                    cell['nrarfcnUL'] = p.text
            # TDD: try NRHOIF only if not found in NRCELL
            if cell.get('cellTechnology') == 'TDD':
                if not cell.get('nrarfcnDL') or not cell.get('bandwidthDL'):
                    nrhoif_list = nrhoif_map.get(dn, [])
                    for nrhoif in nrhoif_list:
                        for p in nrhoif.xpath('./*[local-name()="p"]'):
                            name = p.get('name')
                            if name == 'nrarfcn' and not cell.get('nrarfcnDL'):
                                cell['nrarfcnDL'] = p.text
                                cell['nrarfcnUL'] = p.text
                            elif name == 'chBw' and not cell.get('bandwidthDL'):
                                cell['bandwidthDL'] = p.text
                                cell['bandwidthUL'] = p.text
                            elif name == 'freqBandIndicatorNR' and not cell.get('frequencyBand'):
                                cell['frequencyBand'] = p.text
            # FDD: NRCELL_FDD
            elif cell.get('cellTechnology') == 'FDD':
                nrcell_fdd_list = nrcell_fdd_map.get(dn, [])
                for nrcell_fdd in nrcell_fdd_list:
                    for p in nrcell_fdd.xpath('./*[local-name()="p"]'):
                        name = p.get('name')
                        if name == 'nrarfcnDl':
                            cell['nrarfcnDL'] = p.text
                        elif name == 'nrarfcnUl':
                            cell['nrarfcnUL'] = p.text
                        elif name == 'chBwDl':
                            cell['bandwidthDL'] = p.text
                        elif name == 'chBwUl':
                            cell['bandwidthUL'] = p.text
            # Only add if at least cellId or cellName is present and not a duplicate
            if (cell.get('cellId') or cell.get('cellName')) and any([cell.get(k) for k in ['nrarfcnDL','nrarfcnUL','bandwidthDL','bandwidthUL','cellTechnology','cellWorkingType','frequencyBand','cellPower','localCellId','phyCellId']]):
                info['cells']['5G'].append(cell)
        
        return info
    
    def _extract_hardware_info(self, tree):
        """Extract hardware configuration"""
        info = {
            'modules': [],
            'cabinetCount': 0
        }
        managed_objects = self._findall_managed_objects(tree)
        # Extract radio modules
        rmods = [mo for mo in managed_objects if mo.get('class','').endswith('RMOD')]
        for rmod in rmods:
            module_data = {
                'id': rmod.get('distName', '').split('/')[-1],
                'productCode': '',
                'state': ''
            }
            for p in rmod.findall(".//p"):
                name = p.get('name')
                if name == 'prodCodePlanned':
                    module_data['productCode'] = p.text
                elif name == 'administrativeState':
                    module_data['state'] = p.text
            info['modules'].append(module_data)
        
        # Extract cabinet info
        cabinets = [mo for mo in managed_objects if mo.get('class','').endswith('CABINET')]
        info['cabinetCount'] = len(cabinets)
        
        return info
    
    def _extract_neighbor_info(self, tree):
        """Extract neighbor relations"""
        info = {
            'lteNeighborCount': 0,
            'nrNeighborCount': 0,
            'x2LinkCount': 0
        }
        managed_objects = self._findall_managed_objects(tree)
        info['lteNeighborCount'] = len([mo for mo in managed_objects if mo.get('class','').endswith('LNADJ')])
        info['nrNeighborCount'] = len([mo for mo in managed_objects if mo.get('class','').endswith('NRADJ')])
        info['x2LinkCount'] = len([mo for mo in managed_objects if mo.get('class','').endswith('X2LINK')])
        return info
    
    def format_xml_for_display(self, tree):
        """Format XML for user-friendly display"""
        try:
            # Pretty print the XML
            xml_str = etree.tostring(tree, pretty_print=True, encoding='unicode')
            
            # Limit the size for display
            max_size = 50000  # 50KB limit for display
            if len(xml_str) > max_size:
                xml_str = xml_str[:max_size] + "\n\n... (truncated for display)"
            
            return xml_str
        except Exception as e:
            logger.error(f"Error formatting XML: {str(e)}")
            return "Error formatting XML"

    def html_tree_from_file(self, file_path):
        """Load XML from file and return as HTML collapsible tree"""
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(file_path, parser)
            root = tree.getroot()
            return self._element_to_html(root)
        except Exception as e:
            logger.error(f"Error generating HTML tree: {str(e)}")
            return f'<div class="text-danger">Error: {str(e)}</div>'

    def _element_to_html(self, elem, level=0):
        """Recursively convert XML element to HTML list (collapsible for children)"""
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        attrs = ' '.join([f'<span class="xml-attr">{k}="{v}"</span>' for k, v in elem.attrib.items()])
        text = (elem.text or '').strip()
        html = f'<li>'
        if len(elem):
            # If has children, make collapsible
            html += f'<span class="collapsible xml-tag">&lt;{tag} {attrs}&gt;</span>'
            html += '<ul class="content">'
            if text:
                html += f'<li><span class="xml-text">{text}</span></li>'
            for child in elem:
                html += self._element_to_html(child, level+1)
            html += '</ul>'
            html += f'<span class="xml-tag">&lt;/{tag}&gt;</span>'
        else:
            html += f'<span class="xml-tag">&lt;{tag} {attrs}&gt;</span>'
            if text:
                html += f'<span class="xml-text">{text}</span>'
            html += f'<span class="xml-tag">&lt;/{tag}&gt;</span>'
        html += '</li>'
        return html