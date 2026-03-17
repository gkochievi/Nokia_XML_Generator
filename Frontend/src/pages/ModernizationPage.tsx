import { useState, useEffect, useCallback } from 'react';
import {
  Typography,
  Row,
  Col,
  Form,
  Input,
  Button,
  Select,
  Upload,
  Segmented,
  Space,
  Tag,
  message,
  Tooltip,
  Modal,
} from 'antd';
import {
  UploadOutlined,
  FolderOpenOutlined,
  CloudDownloadOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudUploadOutlined,
  ExclamationCircleOutlined,
  RadarChartOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  WifiOutlined,
  SwapOutlined,
  EnvironmentOutlined,
  AimOutlined,
  AppstoreOutlined,
  BranchesOutlined,
  FileProtectOutlined,
  HistoryOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import {
  listExampleXml,
  listExampleExcel,
  listGeneratedFiles,
  inspectExistingXml,
  generateModernization,
  sftpDownload,
  downloadUrl,
  extractBtsName,
  parseIpPlanFromExample,
} from '../api/client';
import type { InspectResult } from '../api/client';
import DebugConsole, { type LogEntry, createLog } from '../components/DebugConsole';
import FileManagerModal from '../components/FileManagerModal';

const { Text } = Typography;

export default function ModernizationPage() {
  const { t } = useTranslation();
  const [form] = Form.useForm();

  const rolloutName = Form.useWatch('rolloutName', form);
  const [mode, setMode] = useState<'modernization' | 'rollout'>('modernization');
  const [region, setRegion] = useState('East');
  const [existingFile, setExistingFile] = useState<File | null>(null);
  const [stationName, setStationName] = useState('');
  const [inspectData, setInspectData] = useState<InspectResult['data'] | null>(null);

  const [refFiles, setRefFiles] = useState<string[]>([]);
  const [ipFiles, setIpFiles] = useState<string[]>([]);
  const [selectedRef, setSelectedRef] = useState<string | undefined>();
  const [selectedIp, setSelectedIp] = useState<string | undefined>();
  const [refUploadFile, setRefUploadFile] = useState<File | null>(null);
  const [ipUploadFile, setIpUploadFile] = useState<File | null>(null);

  const [sectorFilter, setSectorFilter] = useState<string | null>(null);
  const [modelFilter, setModelFilter] = useState<string | null>(null);

  const [generating, setGenerating] = useState(false);
  const [sftpQuery, setSftpQuery] = useState('');
  const [sftpLoading, setSftpLoading] = useState(false);
  const [fileModalOpen, setFileModalOpen] = useState(false);

  const [recentFiles, setRecentFiles] = useState<{ name: string; mtime?: number }[]>([]);
  const [ipPreview, setIpPreview] = useState<any>(null);
  const [ipNotFound, setIpNotFound] = useState(false);

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const addLog = useCallback(
    (msg: string, level: LogEntry['level'], tab: LogEntry['tab']) =>
      setLogs((prev) => [...prev, createLog(msg, level, tab)]),
    [],
  );
  const clearLogs = useCallback(
    (tab: string) => setLogs((prev) => prev.filter((l) => l.tab !== tab)),
    [],
  );

  const loadRecentFiles = useCallback(async () => {
    try {
      const { data } = await listGeneratedFiles();
      setRecentFiles((data.filesWithMtime || []).slice(0, 5));
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadRecentFiles(); }, [loadRecentFiles]);

  const loadFiles = useCallback(async () => {
    try {
      const [refRes, ipRes] = await Promise.all([listExampleXml(region), listExampleExcel('ip')]);
      const refList = refRes.data.files || [];
      const ipList = ipRes.data.files || [];
      setRefFiles(refList);
      setIpFiles(ipList);
      addLog(`File lists loaded — Region: ${region}, Reference XMLs: ${refList.length}, IP Plans: ${ipList.length}`, 'info', 'system');
      if (ipList.length > 0 && !selectedIp) {
        setSelectedIp(ipList[ipList.length - 1]);
        addLog(`Auto-selected IP Plan: ${ipList[ipList.length - 1]}`, 'info', 'system');
      }
    } catch {
      addLog('Failed to load file lists', 'error', 'system');
    }
  }, [region, addLog, selectedIp]);

  useEffect(() => { loadFiles(); }, [loadFiles]);

  // Load IP plan preview when station name + IP plan file are both set
  const ipLookupName = mode === 'rollout'
    ? (rolloutName || stationName)
    : stationName;

  useEffect(() => {
    if (!ipLookupName || !selectedIp) { setIpPreview(null); setIpNotFound(false); return; }
    let cancelled = false;
    setIpNotFound(false);
    parseIpPlanFromExample(ipLookupName, selectedIp)
      .then(({ data }) => {
        if (cancelled) return;
        if (data.success) { setIpPreview(data.data || data); setIpNotFound(false); }
        else { setIpPreview(null); setIpNotFound(true); }
      })
      .catch(() => { if (!cancelled) { setIpPreview(null); setIpNotFound(true); } });
    return () => { cancelled = true; };
  }, [ipLookupName, selectedIp]); // eslint-disable-line react-hooks/exhaustive-deps

  const filteredRefFiles = refFiles.filter((f) => {
    const upper = f.toUpperCase();
    if (sectorFilter && !upper.includes(sectorFilter)) return false;
    if (modelFilter && !upper.includes(modelFilter)) return false;
    return true;
  });

  const handleExistingXmlChange = useCallback(
    async (file: File) => {
      setExistingFile(file);
      addLog(`Existing XML selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'info', 'system');
      addLog(`Uploading: ${file.name}`, 'info', 'extraction');
      try {
        const nameRes = await extractBtsName(file);
        if (nameRes.data.success && nameRes.data.btsName) {
          setStationName(nameRes.data.btsName);
          form.setFieldValue('stationName', nameRes.data.btsName);
          addLog(`Station name: ${nameRes.data.btsName}`, 'success', 'extraction');
        }
      } catch { addLog('Could not extract station name', 'warning', 'extraction'); }
      try {
        const inspRes = await inspectExistingXml(file, region);
        if (inspRes.data.success) {
          const d = inspRes.data.data;
          setInspectData(d);
          addLog(`3G: ${d.has3G ? 'YES' : 'NO'}, 4G: ${d.has4G ? 'YES' : 'NO'}, 5G: ${d.has5G ? 'YES' : 'NO'}, Sectors: ${d.sectorCount}`, 'success', 'extraction');
          if (d.suggestedReference) { setSelectedRef(d.suggestedReference); addLog(`Suggested: ${d.suggestedReference}`, 'info', 'extraction'); }
          if (d.sectorCount) setSectorFilter(`S${d.sectorCount}`);
          if (d.modelCodes?.length) setModelFilter(d.modelCodes[0].toUpperCase());
        }
      } catch { addLog('Could not inspect XML', 'warning', 'extraction'); }
    },
    [region, form, addLog],
  );

  const handleSftpDownload = async () => {
    if (!sftpQuery.trim()) return;
    setSftpLoading(true);
    addLog(`SFTP query: ${sftpQuery}`, 'info', 'system');
    try {
      const res = await sftpDownload(sftpQuery);
      const blob = new Blob([res.data]);
      const disposition = res.headers['content-disposition'];
      const filename = disposition?.match(/filename="?(.+?)"?$/)?.[1] || `backup_${sftpQuery}.xml`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename; a.click();
      URL.revokeObjectURL(url);
      addLog(`Downloaded: ${filename}`, 'success', 'system');
    } catch (err: any) {
      addLog(`SFTP error: ${err.message}`, 'error', 'system');
      message.error('SFTP download failed');
    }
    setSftpLoading(false);
  };

  const handleGenerate = async () => {
    try { await form.validateFields(); } catch { return; }
    if (mode === 'modernization' && !existingFile) { message.warning(t('existingXmlHelp')); return; }
    if (mode === 'rollout' && !selectedRef && !refUploadFile) { message.warning('Please select a Reference XML'); return; }
    setGenerating(true);
    const logName = mode === 'rollout' ? (form.getFieldValue('rolloutName') || stationName || '-') : (stationName || '-');
    addLog('Starting XML generation...', 'info', 'generation');
    addLog(`Station: "${logName}"`, 'info', 'generation');
    addLog(`Reference 5G XML: ${selectedRef || refUploadFile?.name || '-'}`, 'info', 'generation');
    addLog(`IP Plan: ${selectedIp || ipUploadFile?.name || '-'}`, 'info', 'generation');
    addLog(`Mode: ${mode === 'rollout' ? 'Rollout' : 'Modernization'}`, 'info', 'generation');
    addLog('Sending data to server...', 'info', 'generation');
    const fd = new FormData();
    const effectiveName = mode === 'rollout' ? (form.getFieldValue('rolloutName') || stationName || '') : (stationName || '');
    fd.append('stationName', effectiveName);
    fd.append('mode', mode);
    fd.append('region', region);

    if (mode === 'rollout') {
      // In rollout: reference XML serves as both existing and reference
      if (refUploadFile) {
        fd.append('existingXml', refUploadFile);
        fd.append('reference5gXmlUpload', refUploadFile);
      } else if (selectedRef) {
        fd.append('reference5gXmlSelection', selectedRef);
        fd.append('existingXmlSelection', selectedRef);
      }
    } else {
      fd.append('existingXml', existingFile!);
      if (refUploadFile) fd.append('reference5gXmlUpload', refUploadFile);
      else if (selectedRef) fd.append('reference5gXmlSelection', selectedRef);
    }

    if (ipUploadFile) fd.append('ipPlanUpload', ipUploadFile);
    else if (selectedIp) fd.append('ipPlanSelection', selectedIp);
    if (mode === 'rollout') {
      fd.append('rolloutId', form.getFieldValue('rolloutId') || '');
      fd.append('rolloutName', form.getFieldValue('rolloutName') || '');
      fd.append('rolloutTac', form.getFieldValue('rolloutTac') || '');
    }
    try {
      const res = await generateModernization(fd);
      const data = res.data;
      addLog('Server response received', 'info', 'generation');
      if (data.success) {
        addLog(`\u2713 XML generated successfully!`, 'success', 'generation');
        addLog(`Filename: ${data.filename}`, 'success', 'generation');
        const d = data.details;
        if (d) {
          addLog(`--- Replacement Details (${d.mode === 'rollout' ? 'Rollout' : 'Modernization'}) ---`, 'info', 'generation');
          if (d.mode === 'rollout' && d.rollout_overrides) {
            addLog(`Override Name: ${d.rollout_overrides.name || '-'}`, 'info', 'generation');
            addLog(`Override ID: ${d.rollout_overrides.id || '-'}`, 'info', 'generation');
            addLog(`Override TAC: ${d.rollout_overrides.tac || '-'}`, 'info', 'generation');
          }
          addLog(`Reference Name: "${d.reference_bts_name || '-'}"`, 'info', 'generation');
          addLog(`Target Name: "${d.existing_bts_name || '-'}"`, 'info', 'generation');
          addLog(`Name Replacement: ${d.replacement_performed ? 'YES' : 'NO'}`, d.replacement_performed ? 'success' : 'warning', 'generation');
          addLog(`Reference BTS ID: "${d.reference_bts_id || 'N/A'}"`, 'info', 'generation');
          addLog(`Target BTS ID: "${d.existing_bts_id || 'N/A'}"`, 'info', 'generation');
          addLog(`BTS ID Replacement: ${d.bts_id_replacement_performed ? 'YES' : 'NO'}`, d.bts_id_replacement_performed ? 'success' : 'warning', 'generation');
          if (typeof d.ip_plan_found !== 'undefined') {
            addLog(`IP Plan lookup (${d.ip_plan_lookup_station || '-'}): ${d.ip_plan_found ? 'FOUND' : 'NOT FOUND'}`, d.ip_plan_found ? 'success' : 'warning', 'generation');
          }
          addLog(`sctpPortMin: ref="${d.reference_sctp_port || 'N/A'}" → target="${d.existing_sctp_port || 'N/A'}" | Replaced: ${d.sctp_port_replacement_performed ? 'YES' : 'NO'}`, d.sctp_port_replacement_performed ? 'success' : 'info', 'generation');
          if (d.params_2g_replacement_performed && d.existing_2g_params && d.reference_2g_params) {
            addLog(`2G Parameters Replaced:`, 'success', 'generation');
            Object.entries(d.existing_2g_params).forEach(([key, value]: [string, any]) => {
              const old = d.reference_2g_params[key];
              if (old) addLog(`  ${key}: "${old}" → "${value}"`, 'success', 'generation');
            });
          } else { addLog(`2G Replacement: ${d.params_2g_replacement_performed ? 'YES' : 'NO (no 2G)'}`, 'info', 'generation'); }
          addLog(`4G Cells: ${d.cells_4g_replacement_performed ? 'YES' : 'NO'} | 4G RootSeq: ${d.rootseq_4g_replacement_performed ? 'YES' : 'NO'} | 5G NR: ${d.nrcells_5g_replacement_performed ? 'YES' : 'NO'}`, d.cells_4g_replacement_performed || d.nrcells_5g_replacement_performed ? 'success' : 'info', 'generation');
          addLog(`--- End Replacement Details ---`, 'info', 'generation');
        }
        if (data.debug_log?.length) {
          addLog('--- Backend Debug Log ---', 'info', 'generation');
          data.debug_log.forEach((msg: string) => {
            if (typeof msg !== 'string') return;
            if (msg.startsWith('✓')) addLog(msg, 'success', 'generation');
            else if (msg.startsWith('✗')) addLog(msg, 'error', 'generation');
            else if (msg.startsWith('○') || msg.toLowerCase().includes('warning')) addLog(msg, 'warning', 'generation');
            else addLog(msg, 'info', 'generation');
          });
          addLog('--- End Backend Debug Log ---', 'info', 'generation');
        }
        const doDownload = () => {
          addLog(t('autoDownload'), 'info', 'generation');
          const link = document.createElement('a');
          link.href = downloadUrl(data.filename); link.download = data.filename; link.click();
          message.success(`${t('generationSuccess')} ${data.filename}`);
          addLog(`${t('generationSuccess')} ${data.filename}`, 'success', 'generation');
          loadRecentFiles();
        };
        if (data.warnings?.ip_plan) {
          addLog(`\u26A0 ${data.warnings.ip_plan}`, 'warning', 'generation');
          const lookupStation = d?.ip_plan_lookup_station || stationName || '?';
          Modal.confirm({
            title: <span style={{ color: '#fbbf24' }}>{t('ipPlanWarningTitle')}</span>,
            icon: <ExclamationCircleOutlined style={{ color: '#fbbf24' }} />,
            content: (
              <div style={{ color: '#d0d0e8' }}>
                <p style={{ marginBottom: 6 }}><strong style={{ color: '#c4b5fd' }}>{lookupStation}</strong>{' — '}VLAN / IP / Gateway replacements were skipped.</p>
                <p style={{ color: '#b0b0c8' }}>{t('ipPlanConfirm')}</p>
              </div>
            ),
            okText: t('yes'), cancelText: t('no'),
            onOk: doDownload,
            onCancel: () => addLog('User cancelled — IP Plan not found', 'warning', 'generation'),
          });
        } else { doDownload(); }
      } else {
        addLog(`\u2717 Error: ${data.error}`, 'error', 'generation');
        message.error(data.error || 'Generation failed');
      }
    } catch (err: any) {
      addLog(`\u2717 Network error: ${err.message}`, 'error', 'generation');
      message.error('Generation failed');
    }
    addLog('Generation process finished', 'info', 'generation');
    setGenerating(false);
  };

  const techBadge = (label: string, has: boolean) => (
    <span className={`tech-badge ${has ? 'yes' : 'no'}`}>
      {has ? <CheckCircleOutlined /> : <CloseCircleOutlined />} {label}
    </span>
  );

  return (
    <>
      {/* ─── Top Controls Bar ─── */}
      <div className="mod-controls-bar">
        <div className="mod-control-group">
          <SwapOutlined style={{ color: '#818cf8', fontSize: 14 }} />
          <Text style={{ color: '#7878a0', fontSize: 12, fontWeight: 600 }}>{t('mode')}</Text>
          <Segmented
            value={mode}
            options={[
              { label: t('modeModernization'), value: 'modernization' },
              { label: t('modeRollout'), value: 'rollout' },
            ]}
            onChange={(v) => { setMode(v as 'modernization' | 'rollout'); addLog(`Mode changed: ${v}`, 'info', 'system'); }}
          />
        </div>
        <div className="mod-controls-divider" />
        <div className="mod-control-group">
          <EnvironmentOutlined style={{ color: '#34d399', fontSize: 14 }} />
          <Text style={{ color: '#7878a0', fontSize: 12, fontWeight: 600 }}>{t('region')}</Text>
          <Segmented
            value={region}
            options={[
              { label: t('east'), value: 'East' },
              { label: t('west'), value: 'West' },
            ]}
            onChange={(v) => { setRegion(v as string); addLog(`Region changed: ${v}`, 'info', 'system'); }}
          />
        </div>
        <div className="mod-controls-divider" />
        <div className="mod-control-group">
          <CloudDownloadOutlined style={{ color: '#60a5fa', fontSize: 14 }} />
          <Text style={{ color: '#7878a0', fontSize: 12, fontWeight: 600 }}>SFTP</Text>
          <Space.Compact size="small">
            <Input
              placeholder="ID / Name"
              value={sftpQuery}
              onChange={(e) => setSftpQuery(e.target.value)}
              onPressEnter={handleSftpDownload}
              style={{ width: 150, borderRadius: '8px 0 0 8px' }}
              size="small"
            />
            <Button type="primary" icon={<CloudDownloadOutlined />} loading={sftpLoading} onClick={handleSftpDownload} size="small" style={{ borderRadius: '0 8px 8px 0' }} />
          </Space.Compact>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <Button
            icon={<FolderOpenOutlined />}
            onClick={() => setFileModalOpen(true)}
            className="mod-manage-btn"
            size="small"
          >
            {t('manageFiles')}
          </Button>
        </div>
      </div>

      <Row gutter={20} style={{ alignItems: 'stretch' }}>
        {/* ─── Left: Form ─── */}
        <Col xs={24} lg={16}>
          <Form form={form} layout="vertical" requiredMark={false}>
            {/* Rollout fields */}
            {mode === 'rollout' && (
              <div className="mod-section">
                <div className="mod-section-header">
                  <AimOutlined style={{ color: '#f87171' }} />
                  <span>Rollout Overrides</span>
                  <span className="mod-step-badge">1</span>
                </div>
                <Row gutter={12}>
                  <Col span={8}><Form.Item name="rolloutId" label={t('mrbtsId')}><Input size="small" /></Form.Item></Col>
                  <Col span={8}><Form.Item name="rolloutName" label={t('mrbtsName')}><Input size="small" /></Form.Item></Col>
                  <Col span={8}><Form.Item name="rolloutTac" label={t('tac')}><Input size="small" /></Form.Item></Col>
                </Row>
              </div>
            )}

            {/* Step 1: Existing XML (modernization only) */}
            {mode === 'modernization' && (
              <div className="mod-section">
                <div className="mod-section-header">
                  <FileTextOutlined style={{ color: '#818cf8' }} />
                  <span>{t('existingXml')}</span>
                  <span className="mod-step-badge">1</span>
                </div>
                <Upload.Dragger
                  accept=".xml"
                  maxCount={1}
                  showUploadList={false}
                  beforeUpload={(file) => { handleExistingXmlChange(file); return false; }}
                  className="mod-upload-zone"
                >
                  <div style={{ padding: '8px 0' }}>
                    <CloudUploadOutlined style={{ fontSize: 28, color: existingFile ? '#34d399' : '#7c3aed', marginBottom: 6 }} />
                    <p style={{ color: existingFile ? '#34d399' : '#7878a0', fontWeight: existingFile ? 600 : 400, margin: 0, fontSize: 13 }}>
                      {existingFile ? `✓ ${existingFile.name}` : t('existingXmlHelp')}
                    </p>
                  </div>
                </Upload.Dragger>

                {stationName && (
                  <div className="mod-station-badge">
                    <FileProtectOutlined style={{ color: '#818cf8' }} />
                    <span style={{ color: '#7878a0', fontSize: 12 }}>{t('stationName')}</span>
                    <span style={{ color: '#c4b5fd', fontWeight: 700, fontSize: 15 }}>{stationName}</span>
                  </div>
                )}
              </div>
            )}

            {/* Step 2: Reference XML */}
            <div className="mod-section">
              <div className="mod-section-header">
                <WifiOutlined style={{ color: '#818cf8' }} />
                <span>{t('reference5g')}</span>
                <span className="mod-step-badge">2</span>
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                {['S2', 'S3', 'S4'].map((s) => (
                  <Tag.CheckableTag key={s} checked={sectorFilter === s} onChange={(c) => setSectorFilter(c ? s : null)}>{s}</Tag.CheckableTag>
                ))}
                <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.06)', alignSelf: 'center' }} />
                {['AHEGA', 'AHEGB'].map((m) => (
                  <Tag.CheckableTag key={m} checked={modelFilter === m} onChange={(c) => setModelFilter(c ? m : null)}>{m}</Tag.CheckableTag>
                ))}
              </div>
              <Select
                value={selectedRef}
                onChange={(v) => { setSelectedRef(v); if (v) addLog(`Reference XML selected: ${v}`, 'info', 'system'); }}
                placeholder={t('selectFile')}
                allowClear showSearch
                options={filteredRefFiles.map((f) => ({ label: f, value: f }))}
                style={{ width: '100%', marginBottom: 8 }}
              />
              <Upload accept=".xml" maxCount={1} showUploadList beforeUpload={(file) => { setRefUploadFile(file); return false; }} onRemove={() => setRefUploadFile(null)}>
                <Button size="small" icon={<UploadOutlined />} style={{ borderRadius: 8, color: '#8888a8', fontSize: 12 }}>{t('uploadNew')}</Button>
              </Upload>
            </div>

            {/* Step 3: IP Plan */}
            <div className="mod-section">
              <div className="mod-section-header">
                <DatabaseOutlined style={{ color: '#34d399' }} />
                <span>{t('ipPlan')}</span>
                <span className="mod-step-badge">3</span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
                <Select
                  value={selectedIp}
                  onChange={(v) => { setSelectedIp(v); if (v) addLog(`IP Plan selected: ${v}`, 'info', 'system'); }}
                  placeholder={t('selectFile')}
                  allowClear showSearch
                  options={ipFiles.map((f) => ({ label: f, value: f }))}
                  style={{ flex: 1 }}
                  size="small"
                />
                <Upload accept=".xlsx,.xls" maxCount={1} showUploadList={false} beforeUpload={(file) => { setIpUploadFile(file); return false; }}>
                  <Button size="small" icon={<UploadOutlined />} style={{ borderRadius: 8, color: '#8888a8', fontSize: 12 }}>{t('uploadNew')}</Button>
                </Upload>
              </div>
              {ipPreview?.technologies ? (
                <div className="ip-preview-grid">
                  {Object.entries(ipPreview.technologies).map(([tech, info]: [string, any]) => {
                    if (tech === '2G') return null;
                    if (!info?.vlanId && !info?.localIpAddr) return null;
                    return (
                      <div key={tech} className="ip-preview-item">
                        <span className="ip-preview-tech">{tech}</span>
                        <span className="ip-preview-ip">{info.localIpAddr || '-'}</span>
                        <span className="ip-preview-detail">VLAN {info.vlanId || '-'} | GW {info.gateway || '-'}</span>
                      </div>
                    );
                  })}
                </div>
              ) : ipNotFound && ipLookupName ? (
                <div className="ip-preview-notfound">
                  <ExclamationCircleOutlined style={{ color: '#f59e0b', marginRight: 6 }} />
                  <span><strong>{ipLookupName}</strong> not found in IP Plan. VLAN/IP/GW will not be replaced.</span>
                </div>
              ) : selectedIp && !ipLookupName ? (
                <div style={{ color: '#555578', fontSize: 12, fontStyle: 'italic' }}>
                  {mode === 'modernization' ? 'Upload XML to detect station' : 'Enter MRBTS Name to preview'}
                </div>
              ) : null}
            </div>

            {/* Generate */}
            <Button
              type="primary"
              size="large"
              icon={<ThunderboltOutlined />}
              loading={generating}
              onClick={handleGenerate}
              block
              className="generate-btn"
              style={{ marginTop: 16, marginBottom: 8 }}
            >
              {generating ? t('processing') : t('generate')}
            </Button>
          </Form>
        </Col>

        {/* ─── Right: Info + Console ─── */}
        <Col xs={24} lg={8} style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {inspectData && (
            <div className="mod-inspect-card">
              <div className="mod-section-header" style={{ marginBottom: 14 }}>
                <RadarChartOutlined style={{ color: '#c4b5fd' }} />
                <span>{t('detected')}</span>
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
                {techBadge('3G', inspectData.has3G)}
                {techBadge('4G', inspectData.has4G)}
                {techBadge('5G', inspectData.has5G)}
              </div>
              <div className="mod-inspect-row">
                <AppstoreOutlined style={{ color: '#60a5fa' }} />
                <span className="mod-inspect-label">{t('sectors')}</span>
                <span className="mod-inspect-value">{inspectData.sectorCount}</span>
              </div>
              {((inspectData as any).radioModuleSummary || inspectData.models?.length > 0) && (
                <div className="mod-inspect-row">
                  <BranchesOutlined style={{ color: '#818cf8' }} />
                  <span className="mod-inspect-label">{t('modules')}</span>
                  <span style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
                    {(inspectData as any).radioModuleSummary
                      ? <Tag color="geekblue" style={{ margin: 0, fontWeight: 600 }}>{(inspectData as any).radioModuleSummary}</Tag>
                      : inspectData.models.map((m) => <Tag key={m} color="geekblue" style={{ margin: 0 }}>{m}</Tag>)
                    }
                  </span>
                </div>
              )}
              {(inspectData as any).radioModules?.length > 0 && (
                <div style={{ marginTop: 6, paddingLeft: 30 }}>
                  {(inspectData as any).radioModules.map((rm: any, i: number) => (
                    <span key={i} style={{ fontSize: 11, color: '#7878a0', marginRight: 10 }}>
                      S{rm.sector}: <span style={{ color: rm.model === 'AHEGA' ? '#34d399' : rm.model === 'AHEGB' ? '#60a5fa' : '#fbbf24', fontWeight: 600 }}>{rm.model}</span>
                    </span>
                  ))}
                </div>
              )}
              {inspectData.suggestedReference && (
                <div className="mod-inspect-row">
                  <AimOutlined style={{ color: '#34d399' }} />
                  <span className="mod-inspect-label">{t('suggestion')}</span>
                  <Tooltip title="Click to select">
                    <Tag
                      color="purple"
                      style={{ cursor: 'pointer', fontWeight: 600, margin: 0 }}
                      onClick={() => setSelectedRef(inspectData.suggestedReference!)}
                    >
                      {inspectData.suggestedReference}
                    </Tag>
                  </Tooltip>
                </div>
              )}
            </div>
          )}

          {/* Generation History */}
          {recentFiles.length > 0 && (
            <div className="mod-history-card">
              <div className="mod-section-header" style={{ marginBottom: 10 }}>
                <HistoryOutlined style={{ color: '#60a5fa' }} />
                <span style={{ fontSize: 13 }}>Recent Generations</span>
              </div>
              {recentFiles.map((f, i) => (
                <div key={i} className="mod-history-item">
                  <span className="mod-history-name">{f.name}</span>
                  {f.mtime && (
                    <span className="mod-history-time">
                      {new Date(f.mtime * 1000).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                  <a href={downloadUrl(f.name)} download className="mod-history-dl">
                    <DownloadOutlined />
                  </a>
                </div>
              ))}
            </div>
          )}

          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <DebugConsole logs={logs} onClear={clearLogs} />
          </div>
          </div>
        </Col>
      </Row>

      <FileManagerModal open={fileModalOpen} onClose={() => setFileModalOpen(false)} region={region} />
    </>
  );
}
