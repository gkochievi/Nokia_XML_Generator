/* ───── XML Viewer Types ───── */

export interface RadioCell {
  cellName?: string;
  name?: string;
  cellId?: string;
  localCellId?: string;
  userLabel?: string;
  technology: string;
  sector?: number;
  carrier?: number;
  phyCellId?: string;
  trackingAreaCode?: string;
  nrarfcnDL?: string;
  earfcnDL?: string;
  uarfcnDl?: string;
  bcch?: string;
  bandwidthDL?: string | number;
  bandwidth?: string | number;
}

export interface StationInfo {
  btsName?: string;
  mrbtsId?: string;
  version?: string;
  has5G: boolean;
  has4G: boolean;
  has3G: boolean;
  has2G: boolean;
  nrbtsId?: string;
  lnbtsId?: string;
  wnbtsId?: string;
  bcfId?: string;
}

export interface VlanEntry {
  label?: string;
  name?: string;
  vlanId?: string;
  ip?: string;
  ipAddr?: string;
  prefix?: string;
  localIpPrefixLength?: string;
}

export interface NrX2LinkEntry {
  ipV4Addr?: string;
}

export interface LnAdjGnbEntry {
  cPlaneIpAddr?: string;
}

export interface NetworkInfo {
  vlan_ip_combined?: VlanEntry[];
  vlans?: VlanEntry[];
  nrx2link_trust?: NrX2LinkEntry[];
  lnadjgnb?: LnAdjGnbEntry[];
}

export interface CellRadioMapping {
  cellName?: string;
  name?: string;
  cell?: string;
  sector?: number | string;
  technology?: string;
  radio_module?: string;
  rmodName?: string;
  productCode?: string;
  port?: string;
  mode?: string;
}

export interface HardwareInfo {
  modules?: unknown[];
  radioModuleSummary?: string;
  cabinetCount?: number;
}

export interface NeighborInfo {
  lteNeighborCount?: number;
  nrNeighborCount?: number;
  x2LinkCount?: number;
}

export interface RoutingEntry {
  dest?: string;
  gateway?: string;
  metric?: string;
}

export interface NetworkParam {
  name?: string;
  value?: string;
}

export interface AdvancedInfo {
  routing?: RoutingEntry[];
  networkParams?: NetworkParam[];
}

export interface RadioInfo {
  cells: RadioCell[] | Record<string, RadioCell[]>;
  technologies?: string[] | Record<string, unknown>;
  sectorCount?: number;
}

export interface XmlViewerData {
  stationInfo?: StationInfo;
  radioInfo?: RadioInfo;
  networkInfo?: NetworkInfo;
  cellRadioMapping?: CellRadioMapping[] | Record<string, CellRadioMapping[]>;
  hardwareInfo?: HardwareInfo;
  neighborInfo?: NeighborInfo;
  advanced?: AdvancedInfo;
}

/* ───── Modernization Types ───── */

export interface RadioModule {
  sector: number;
  model: string;
}

export interface TechnologyInfo {
  vlanId?: string;
  localIpAddr?: string;
  gateway?: string;
  localIpPrefixLength?: string;
}

export interface IpPreviewData {
  technologies: Record<string, TechnologyInfo>;
  success?: boolean;
}

export interface GenerationDetails {
  mode: 'modernization' | 'rollout';
  rollout_overrides?: { name?: string; id?: string; tac?: string };
  reference_bts_name?: string;
  existing_bts_name?: string;
  replacement_performed: boolean;
  reference_bts_id?: string;
  existing_bts_id?: string;
  bts_id_replacement_performed: boolean;
  ip_plan_found?: boolean;
  ip_plan_lookup_station?: string;
  reference_sctp_port?: string;
  existing_sctp_port?: string;
  sctp_port_replacement_performed: boolean;
  params_2g_replacement_performed: boolean;
  reference_2g_params?: Record<string, string>;
  existing_2g_params?: Record<string, string>;
  cells_4g_replacement_performed: boolean;
  rootseq_4g_replacement_performed: boolean;
  nrcells_5g_replacement_performed: boolean;
}

export interface GenerationResponse {
  success: boolean;
  filename?: string;
  error?: string;
  details?: GenerationDetails;
  debug_log?: string[];
  warnings?: { ip_plan?: string };
}

/* ───── Collapse item type (Ant Design) ───── */

export interface CollapseItem {
  key: string;
  label: React.ReactNode;
  children: React.ReactNode;
}
