import { useState, useCallback, useEffect } from 'react';
import {
  Typography,
  Upload,
  Select,
  Button,
  Tag,
  Table,
  Input,
  Empty,
  Popconfirm,
  message,
  Spin,
  Collapse,
} from 'antd';
import {
  DeleteOutlined,
  CloudUploadOutlined,
  SearchOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  WifiOutlined,
  AppstoreOutlined,
  ClusterOutlined,
  GlobalOutlined,
  ApartmentOutlined,
  FileSearchOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { uploadXmls, listUploadedXmls, viewXml, deleteUploadedXml } from '../api/client';
import type { XmlViewerData, RadioCell, VlanEntry, NrX2LinkEntry, LnAdjGnbEntry, CellRadioMapping, CollapseItem } from '../types';

const { Text } = Typography;
const { Dragger } = Upload;

const MODEL_MAP: Record<string, string> = {
  '474090A': 'AHEGB', '474088A': 'AHEGB', '474084A': 'AHEGA',
  '474082A': 'AHEGA', '472815A': 'AWHQA', '474086A': 'AHEGA',
  '474092A': 'AHEGB', '473995A': 'AHEGA', '476501A': 'AAHF',
};

function flattenCells(cells: RadioCell[] | Record<string, RadioCell[]> | undefined): RadioCell[] {
  if (!cells) return [];
  if (Array.isArray(cells)) return cells;
  const result: RadioCell[] = [];
  for (const [tech, arr] of Object.entries(cells)) {
    if (Array.isArray(arr)) {
      arr.forEach((c) => result.push({ ...c, technology: c.technology || tech }));
    }
  }
  return result;
}

export default function XmlViewerPage() {
  const { t } = useTranslation();

  const [files, setFiles] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<XmlViewerData | null>(null);
  const [cellNameFilter, setCellNameFilter] = useState('');
  const [cellTechFilter, setCellTechFilter] = useState<string | null>(null);

  const refreshFileList = useCallback(async () => {
    try {
      const res = await listUploadedXmls();
      setFiles(res.data.files || []);
    } catch { /* empty */ }
  }, []);

  useEffect(() => { refreshFileList(); }, [refreshFileList]);

  const loadXmlData = useCallback(async (filename: string) => {
    setSelected(filename);
    setLoading(true);
    try {
      const res = await viewXml(filename);
      if (res.data.success) setData(res.data.data);
      else { setData(null); message.error('Parse failed'); }
    } catch { setData(null); message.error('Could not load XML'); }
    setLoading(false);
  }, []);

  const handleUpload = async (fileList: File[]) => {
    if (!fileList.length) return;
    setLoading(true);
    try {
      const res = await uploadXmls(fileList);
      message.success(`Uploaded ${res.data.saved?.length || 0} file(s)`);
      await refreshFileList();
      const firstSaved = res.data.saved?.[0];
      if (firstSaved) await loadXmlData(firstSaved);
    } catch { message.error('Upload failed'); }
    setLoading(false);
  };

  const handleDelete = async () => {
    if (!selected) return;
    await deleteUploadedXml(selected);
    message.success('Deleted');
    setSelected(undefined);
    setData(null);
    refreshFileList();
  };

  const techBadge = (label: string, has: boolean) => (
    <span className={`tech-badge ${has ? 'yes' : 'no'}`}>{has ? '✓' : '✗'} {label}</span>
  );

  const techClass = (tech: string) => {
    if (tech === '5G') return 't5g';
    if (tech === '4G') return 't4g';
    if (tech === '3G') return 't3g';
    return 't2g';
  };

  const getFreq = (r: RadioCell) => {
    if (r.technology === '5G') return r.nrarfcnDL;
    if (r.technology === '4G') return r.earfcnDL;
    if (r.technology === '3G') return r.uarfcnDl;
    return r.bcch;
  };

  /* ─── Sections ─── */

  const renderStationInfo = () => {
    if (!data?.stationInfo) return null;
    const si = data.stationInfo;
    return (
      <div className="mod-section">
        <div className="mod-section-header">
          <InfoCircleOutlined style={{ color: '#7c3aed' }} />
          <span>{t('stationInfo')}</span>
        </div>
        <div className="stat-grid">
          <div className="stat-block"><div className="stat-block-label">BTS Name</div><div className="stat-block-value accent">{si.btsName || '-'}</div></div>
          <div className="stat-block"><div className="stat-block-label">MRBTS ID</div><div className="stat-block-value">{si.mrbtsId || '-'}</div></div>
          <div className="stat-block"><div className="stat-block-label">Version</div><div className="stat-block-value">{si.version || '-'}</div></div>
          <div className="stat-block">
            <div className="stat-block-label">Technologies</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
              {techBadge('5G', !!si.has5G)}{techBadge('4G', !!si.has4G)}{techBadge('3G', !!si.has3G)}{techBadge('2G', !!si.has2G)}
            </div>
          </div>
          {si.nrbtsId && <div className="stat-block"><div className="stat-block-label">NRBTS ID</div><div className="stat-block-value">{si.nrbtsId}</div></div>}
          {si.lnbtsId && <div className="stat-block"><div className="stat-block-label">LNBTS ID</div><div className="stat-block-value">{si.lnbtsId}</div></div>}
          {si.wnbtsId && <div className="stat-block"><div className="stat-block-label">WNBTS ID</div><div className="stat-block-value">{si.wnbtsId}</div></div>}
          {si.bcfId && <div className="stat-block"><div className="stat-block-label">BCF ID</div><div className="stat-block-value">{si.bcfId}</div></div>}
        </div>
      </div>
    );
  };

  const renderSummaryChips = () => {
    if (!data) return null;
    const cells = flattenCells(data.radioInfo?.cells);
    const total2G = cells.filter((c) => c.technology === '2G').length;
    const total3G = cells.filter((c) => c.technology === '3G').length;
    const total4G = cells.filter((c) => c.technology === '4G').length;
    const total5G = cells.filter((c) => c.technology === '5G').length;
    const totalVlans = (data.networkInfo?.vlan_ip_combined || []).length;
    const totalModules = (data.hardwareInfo?.modules || []).length;
    const nb = data.neighborInfo || {};
    return (
      <div className="summary-chips" style={{ marginBottom: 16 }}>
        <span className="summary-chip purple">Cells: <strong>{cells.length}</strong></span>
        {total2G > 0 && <span className="summary-chip">2G: <strong>{total2G}</strong></span>}
        {total3G > 0 && <span className="summary-chip">3G: <strong>{total3G}</strong></span>}
        {total4G > 0 && <span className="summary-chip">4G: <strong>{total4G}</strong></span>}
        {total5G > 0 && <span className="summary-chip">5G: <strong>{total5G}</strong></span>}
        <span className="summary-chip blue">VLAN/IP: <strong>{totalVlans}</strong></span>
        <span className="summary-chip">RMOD: <strong>{totalModules}</strong></span>
        <span className="summary-chip green">Neighbors: <strong>{nb.lteNeighborCount || 0}/{nb.nrNeighborCount || 0}/{nb.x2LinkCount || 0}</strong></span>
      </div>
    );
  };

  const renderRadioSummary = () => {
    if (!data?.radioInfo) return null;
    const ri = data.radioInfo;
    const techs: string[] = Array.isArray(ri.technologies) ? ri.technologies : (typeof ri.technologies === 'object' ? Object.keys(ri.technologies) : []);
    const allCells = flattenCells(ri.cells);
    const radioSummary = data.hardwareInfo?.radioModuleSummary;
    return (
      <div className="mod-section">
        <div className="mod-section-header">
          <WifiOutlined style={{ color: '#818cf8' }} />
          <span>{t('radioSummary')}</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <span className="summary-chip purple">{t('sectors')}: <strong>{ri.sectorCount ?? '-'}</strong></span>
          {techs.map((tech: string) => {
            const count = allCells.filter((c) => (c.technology || '') === tech).length;
            return <span key={tech} className="summary-chip blue">{tech}: <strong>{count} cells</strong></span>;
          })}
          {radioSummary && <span className="summary-chip green">Modules: <strong>{radioSummary}</strong></span>}
        </div>
      </div>
    );
  };

  const renderCells = () => {
    if (!data?.radioInfo?.cells) return null;
    const allCells = flattenCells(data.radioInfo.cells);
    if (!allCells.length) return null;
    const techs = [...new Set(allCells.map((c) => c.technology || 'Unknown'))];
    let filtered = allCells;
    if (cellNameFilter) {
      const q = cellNameFilter.toLowerCase();
      filtered = filtered.filter((c) =>
        (c.name || c.cellName || c.userLabel || '').toLowerCase().includes(q) ||
        String(c.cellId || c.localCellId || '').includes(q),
      );
    }
    if (cellTechFilter) filtered = filtered.filter((c) => (c.technology || '') === cellTechFilter);

    return (
      <div className="mod-section">
        <div className="mod-section-header">
          <AppstoreOutlined style={{ color: '#60a5fa' }} />
          <span>{t('cells')} ({allCells.length})</span>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14, alignItems: 'center' }}>
          <Input
            placeholder={t('filter')}
            prefix={<SearchOutlined style={{ color: '#7878a0' }} />}
            value={cellNameFilter}
            onChange={(e) => setCellNameFilter(e.target.value)}
            allowClear
            style={{ width: 200 }}
            size="small"
          />
          <Tag.CheckableTag checked={!cellTechFilter} onChange={() => setCellTechFilter(null)}>{t('all')}</Tag.CheckableTag>
          {techs.map((tech) => (
            <Tag.CheckableTag key={tech} checked={cellTechFilter === tech} onChange={(c) => setCellTechFilter(c ? tech : null)}>{tech}</Tag.CheckableTag>
          ))}
          <Button size="small" type="text" icon={<ClearOutlined />} onClick={() => { setCellNameFilter(''); setCellTechFilter(null); }} style={{ color: '#7878a0', fontSize: 12 }}>{t('clearFilters')}</Button>
        </div>
        <div style={{ maxHeight: 520, overflowY: 'auto', paddingRight: 4 }}>
          <div className="cell-cards-grid">
            {filtered.map((c, i) => (
              <div className="cell-card" key={`${c.cellId || c.localCellId || ''}-${i}`}>
                <div className="cell-card-header">
                  <span className="cell-card-name">{c.cellName || c.name || '-'}</span>
                  <span className={`cell-card-tech ${techClass(c.technology)}`}>{c.technology}</span>
                </div>
                <div className="cell-card-props">
                  <div className="cell-card-prop"><span className="cell-card-prop-label">Cell ID</span><span className="cell-card-prop-value">{c.localCellId || c.cellId || '-'}</span></div>
                  <div className="cell-card-prop"><span className="cell-card-prop-label">Sector</span><span className="cell-card-prop-value">{c.sector ?? '-'}</span></div>
                  <div className="cell-card-prop"><span className="cell-card-prop-label">Carrier</span><span className="cell-card-prop-value">{c.carrier ?? '-'}</span></div>
                  <div className="cell-card-prop"><span className="cell-card-prop-label">PCI</span><span className="cell-card-prop-value">{c.phyCellId ?? '-'}</span></div>
                  <div className="cell-card-prop"><span className="cell-card-prop-label">TAC</span><span className="cell-card-prop-value">{c.trackingAreaCode ?? '-'}</span></div>
                  <div className="cell-card-prop"><span className="cell-card-prop-label">ARFCN</span><span className="cell-card-prop-value">{getFreq(c) || '-'}</span></div>
                  {(c.bandwidthDL || c.bandwidth) && <div className="cell-card-prop"><span className="cell-card-prop-label">BW</span><span className="cell-card-prop-value">{c.bandwidthDL || c.bandwidth}</span></div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderNetworkInfo = () => {
    if (!data?.networkInfo) return null;
    const ni = data.networkInfo;
    const combined = ni.vlan_ip_combined || ni.vlans || [];
    if (!combined.length) return null;
    const nrx2links: NrX2LinkEntry[] = ni.nrx2link_trust || [];
    const lnadjgnbs: LnAdjGnbEntry[] = ni.lnadjgnb || [];
    return (
      <div className="mod-section">
        <div className="mod-section-header">
          <GlobalOutlined style={{ color: '#34d399' }} />
          <span>{t('networkInfo')}</span>
        </div>
        <div className="net-cards-grid">
          {combined.map((v: VlanEntry, i: number) => (
            <div className="net-card" key={`vlan-${i}`}>
              <div className="net-card-vlan">{v.label || v.name || 'VLAN'}</div>
              <div className="net-card-row"><span className="net-card-row-label">VLAN ID</span><span className="net-card-row-value">{v.vlanId || '-'}</span></div>
              <div className="net-card-row"><span className="net-card-row-label">IP</span><span className="net-card-row-value">{v.ip || v.ipAddr || '-'}</span></div>
              <div className="net-card-row"><span className="net-card-row-label">Prefix</span><span className="net-card-row-value">/{v.prefix || v.localIpPrefixLength || '-'}</span></div>
            </div>
          ))}
          {nrx2links.map((x, i) => (
            <div className="net-card" key={`x2-${i}`} style={{ borderColor: 'rgba(251, 191, 36, 0.15)' }}>
              <div className="net-card-vlan" style={{ color: '#fcd34d' }}>NRX2LINK</div>
              <div className="net-card-row"><span className="net-card-row-label">ipV4Addr</span><span className="net-card-row-value">{x.ipV4Addr || '-'}</span></div>
            </div>
          ))}
          {lnadjgnbs.map((x, i) => (
            <div className="net-card" key={`gnb-${i}`} style={{ borderColor: 'rgba(167, 139, 250, 0.15)' }}>
              <div className="net-card-vlan" style={{ color: '#c4b5fd' }}>LNADJGNB</div>
              <div className="net-card-row"><span className="net-card-row-label">cPlaneIpAddr</span><span className="net-card-row-value">{x.cPlaneIpAddr || '-'}</span></div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderCellRadioMapping = () => {
    if (!data?.cellRadioMapping) return null;
    const raw = data.cellRadioMapping;
    let entries: CellRadioMapping[] = [];
    if (Array.isArray(raw)) entries = raw;
    else if (typeof raw === 'object') {
      for (const [sector, cells] of Object.entries(raw)) {
        if (Array.isArray(cells)) cells.forEach((c) => entries.push({ sector, ...c }));
      }
    }
    if (!entries.length) return null;
    return (
      <div className="mod-section">
        <div className="mod-section-header">
          <ClusterOutlined style={{ color: '#fbbf24' }} />
          <span>{t('cellRadioMapping')} ({entries.length})</span>
        </div>
        <div style={{ maxHeight: 480, overflowY: 'auto', paddingRight: 4 }}>
          <div className="cell-cards-grid">
            {entries.map((r, i) => {
              const model = r.productCode ? MODEL_MAP[r.productCode] : undefined;
              return (
                <div className="cell-card" key={i}>
                  <div className="cell-card-header">
                    <span className="cell-card-name">{r.cellName || r.name || r.cell || '-'}</span>
                    {r.technology && <span className={`cell-card-tech ${techClass(r.technology)}`}>{r.technology}</span>}
                  </div>
                  <div className="cell-card-props">
                    <div className="cell-card-prop"><span className="cell-card-prop-label">Sector</span><span className="cell-card-prop-value">{r.sector ?? '-'}</span></div>
                    <div className="cell-card-prop"><span className="cell-card-prop-label">Module</span><span className="cell-card-prop-value">{r.radio_module || r.rmodName || '-'}</span></div>
                    {r.productCode && <div className="cell-card-prop"><span className="cell-card-prop-label">Product</span><span className="cell-card-prop-value">{r.productCode}{model ? ` (${model})` : ''}</span></div>}
                    {r.port && <div className="cell-card-prop"><span className="cell-card-prop-label">Port</span><span className="cell-card-prop-value">{r.port}</span></div>}
                    {r.mode && <div className="cell-card-prop"><span className="cell-card-prop-label">Mode</span><span className="cell-card-prop-value">{r.mode}</span></div>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderNeighbors = () => {
    const hw = data?.hardwareInfo;
    const nb = data?.neighborInfo;
    if (!hw && !nb) return null;
    return (
      <div className="mod-section">
        <div className="mod-section-header">
          <ApartmentOutlined style={{ color: '#f87171' }} />
          <span>{t('neighbors')}</span>
        </div>
        <div className="stat-grid">
          {hw?.cabinetCount != null && <div className="stat-block"><div className="stat-block-label">Cabinets</div><div className="stat-block-value">{hw.cabinetCount}</div></div>}
          {nb?.lteNeighborCount != null && <div className="stat-block"><div className="stat-block-label">LTE Neighbors</div><div className="stat-block-value">{nb.lteNeighborCount}</div></div>}
          {nb?.nrNeighborCount != null && <div className="stat-block"><div className="stat-block-label">NR Neighbors</div><div className="stat-block-value">{nb.nrNeighborCount}</div></div>}
          {nb?.x2LinkCount != null && <div className="stat-block"><div className="stat-block-label">X2 Links</div><div className="stat-block-value">{nb.x2LinkCount}</div></div>}
        </div>
      </div>
    );
  };

  const renderAdvanced = () => {
    if (!data?.advanced) return null;
    const adv = data.advanced;
    const items: CollapseItem[] = [];
    if (adv.routing?.length) {
      items.push({ key: 'routing', label: <span style={{ color: '#c0c0d8' }}>IPv4 Routing (IPRT)</span>, children: (
        <Table size="small" dataSource={adv.routing} columns={[
          { title: 'Destination', dataIndex: 'dest', key: 'dest' },
          { title: 'Gateway', dataIndex: 'gateway', key: 'gw' },
          { title: 'Metric', dataIndex: 'metric', key: 'metric' },
        ]} rowKey={(_, i) => String(i)} pagination={false} />
      )});
    }
    if (adv.networkParams?.length) {
      items.push({ key: 'netparams', label: <span style={{ color: '#c0c0d8' }}>Core Network Parameters</span>, children: (
        <Table size="small" dataSource={adv.networkParams} columns={[
          { title: 'Parameter', dataIndex: 'name', key: 'name' },
          { title: 'Value', dataIndex: 'value', key: 'value' },
        ]} rowKey={(_, i) => String(i)} pagination={false} />
      )});
    }
    if (!items.length) return null;
    return <Collapse items={items} style={{ marginBottom: 16 }} />;
  };

  /* ─── Main render ─── */
  return (
    <>
      {/* Controls bar */}
      <div className="mod-controls-bar">
        <div className="mod-control-group">
          <FileSearchOutlined style={{ color: '#818cf8', fontSize: 14 }} />
          <Text style={{ color: '#c0c0d8', fontSize: 13, fontWeight: 600 }}>{t('xmlViewer')}</Text>
        </div>
        <div className="mod-controls-divider" />
        <div className="mod-control-group" style={{ flex: 1 }}>
          <Select
            value={selected}
            onChange={(val) => loadXmlData(val)}
            placeholder={t('selectXml')}
            allowClear
            onClear={() => { setSelected(undefined); setData(null); }}
            showSearch
            style={{ minWidth: 280, flex: 1 }}
            size="small"
            options={files.map((f) => ({ label: f, value: f }))}
            onOpenChange={(open) => { if (open) refreshFileList(); }}
          />
          {selected && (
            <Popconfirm title={<span style={{ color: '#e0e0f0' }}>Delete this file?</span>} onConfirm={handleDelete}>
              <Button danger size="small" icon={<DeleteOutlined />} style={{ borderRadius: 8 }}>{t('deleteFile')}</Button>
            </Popconfirm>
          )}
        </div>
      </div>

      {/* Upload zone */}
      {!data && (
        <div className="mod-section" style={{ marginBottom: 20 }}>
          <Dragger
            accept=".xml"
            multiple
            showUploadList={false}
            beforeUpload={(_, fileList) => { handleUpload(fileList as unknown as File[]); return false; }}
          >
            <div style={{ padding: '20px 0' }}>
              <CloudUploadOutlined style={{ fontSize: 36, color: '#7c3aed', marginBottom: 8 }} />
              <p style={{ color: '#7878a0', margin: 0, fontSize: 14 }}>{t('dropOrClick')}</p>
            </div>
          </Dragger>
        </div>
      )}

      {/* Content */}
      <Spin spinning={loading}>
        {data ? (
          <>
            {renderStationInfo()}
            {renderSummaryChips()}
            {renderRadioSummary()}
            {renderCells()}
            {renderCellRadioMapping()}
            {renderNetworkInfo()}
            {renderNeighbors()}
            {renderAdvanced()}
          </>
        ) : (
          !loading && !files.length && (
            <Empty description={<span style={{ color: '#7878a0' }}>Upload an XML file to view</span>} style={{ marginTop: 60 }} />
          )
        )}
      </Spin>
    </>
  );
}
