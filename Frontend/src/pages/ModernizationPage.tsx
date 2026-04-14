import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Row, Col, Form, Input, Button, Select, Upload, Tag, message, Steps, Modal,
} from 'antd';
import {
  UploadOutlined, CloudUploadOutlined, ThunderboltOutlined,
  FileTextOutlined, DatabaseOutlined, WifiOutlined,
  AimOutlined, ExclamationCircleOutlined, FileProtectOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { sftpDownload } from '../api/client';
import type { TechnologyInfo } from '../types';
import DebugConsole, { type LogEntry, createLog } from '../components/DebugConsole';
import FileManagerModal from '../components/FileManagerModal';
import ControlsBar from './modernization/ControlsBar';
import InspectCard from './modernization/InspectCard';
import RecentGenerations from './modernization/RecentGenerations';
import { useFileSelection } from './modernization/useFileSelection';
import { useExistingXml, inferModelFilterFromInspect } from './modernization/useExistingXml';
import { useGeneration } from './modernization/useGeneration';

export default function ModernizationPage() {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [searchParams] = useSearchParams();
  const rolloutName = Form.useWatch('rolloutName', form);
  const rolloutId = Form.useWatch('rolloutId', form);
  const rolloutTac = Form.useWatch('rolloutTac', form);

  /* ─── Local state ─── */
  const [mode, setMode] = useState<'modernization' | 'rollout'>(
    searchParams.get('mode') === 'rollout' ? 'rollout' : 'modernization',
  );
  const [region, setRegion] = useState(() => {
    try {
      const saved = localStorage.getItem('region');
      return saved === 'West' ? 'West' : 'East';
    } catch { return 'East'; }
  });
  const [sftpQuery, setSftpQuery] = useState('');
  const [sftpLoading, setSftpLoading] = useState(false);
  const [fileModalOpen, setFileModalOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const dragDepthRef = useRef(0);
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

  useEffect(() => {
    try { localStorage.setItem('region', region); } catch { /* localStorage unavailable */ }
  }, [region]);

  /* ─── Hooks ─── */
  const existingXml = useExistingXml({ region, form, addLog });

  const fileSelection = useFileSelection({
    region, mode,
    stationName: existingXml.stationName,
    rolloutName: rolloutName || '',
    addLog,
  });

  const generation = useGeneration({
    form, mode, region,
    existingFile: existingXml.existingFile,
    stationName: existingXml.stationName,
    selectedRef: fileSelection.selectedRef,
    refUploadFile: fileSelection.refUploadFile,
    selectedIp: fileSelection.selectedIp,
    ipUploadFile: fileSelection.ipUploadFile,
    addLog,
  });

  // Auto-select filters when inspect data changes
  useEffect(() => {
    if (!existingXml.inspectData) return;
    const d = existingXml.inspectData;
    if (d.sectorCount) fileSelection.setSectorFilter(`S${d.sectorCount}`);
    if (d.suggestedReference) fileSelection.setSelectedRef(d.suggestedReference);
    const bestModel = inferModelFilterFromInspect(d);
    if (bestModel) fileSelection.setModelFilter(bestModel);
  }, [existingXml.inspectData]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── SFTP handler ─── */
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
    } catch (err: unknown) {
      addLog(`SFTP error: ${err instanceof Error ? err.message : String(err)}`, 'error', 'system');
      message.error('SFTP download failed');
    }
    setSftpLoading(false);
  };

  /* ─── Drag & Drop ─── */
  const handleDroppedFiles = async (files: File[]) => {
    const xmlFiles = files.filter((f) => f.name.toLowerCase().endsWith('.xml'));
    const excelFiles = files.filter((f) => /\.xlsx?$/i.test(f.name));
    if (xmlFiles.length > 0) {
      const f = xmlFiles[0];
      if (mode === 'modernization' && !existingXml.existingFile) {
        await existingXml.handleExistingXmlChange(f);
        return;
      }
      fileSelection.setRefUploadFile(f);
      fileSelection.setSelectedRef(undefined);
      addLog(`Reference XML dropped: ${f.name}`, 'info', 'extraction');
      return;
    }
    if (excelFiles.length > 0) {
      fileSelection.setIpUploadFile(excelFiles[0]);
      addLog(`IP Plan dropped: ${excelFiles[0].name} (${(excelFiles[0].size / 1024).toFixed(1)} KB)`, 'info', 'extraction');
    }
  };

  /* ─── Computed ─── */
  const hasReferenceXml = Boolean(fileSelection.selectedRef || fileSelection.refUploadFile);
  const hasIpPlan = Boolean(fileSelection.selectedIp || fileSelection.ipUploadFile);
  const hasModernizationExistingParsed = Boolean(existingXml.existingFile && existingXml.stationName.trim() && existingXml.inspectData);
  const hasRolloutFieldsFilled = Boolean(
    String(rolloutId || '').trim() &&
    String(rolloutName || '').trim() &&
    String(rolloutTac || '').trim(),
  );
  const canGenerate =
    !existingXml.existingXmlParsing &&
    (
      (mode === 'modernization' && hasModernizationExistingParsed && hasReferenceXml && hasIpPlan) ||
      (mode === 'rollout' && hasRolloutFieldsFilled && hasReferenceXml && hasIpPlan)
    );
  const detectedStationName = mode === 'rollout'
    ? (form.getFieldValue('rolloutName') || existingXml.stationName)
    : existingXml.stationName;

  /* ─── Render ─── */
  return (
    <div
      className="mod-page-dnd"
      onDragOver={(e) => e.preventDefault()}
      onDragEnter={(e) => { e.preventDefault(); dragDepthRef.current += 1; setDragActive(true); }}
      onDragLeave={(e) => { e.preventDefault(); dragDepthRef.current = Math.max(0, dragDepthRef.current - 1); if (dragDepthRef.current === 0) setDragActive(false); }}
      onDrop={(e) => {
        e.preventDefault(); e.stopPropagation();
        dragDepthRef.current = 0; setDragActive(false);
        const dt = e.dataTransfer;
        if (dt?.files?.length) void handleDroppedFiles(Array.from(dt.files));
      }}
    >
      {dragActive && (
        <div className="mod-dnd-overlay">
          <div className="mod-dnd-overlay-card">
            <CloudUploadOutlined style={{ fontSize: 28, color: '#c4b5fd' }} />
            <div style={{ marginTop: 8, fontWeight: 700, color: '#e5e7eb' }}>Drop to upload</div>
          </div>
        </div>
      )}

      <ControlsBar
        mode={mode}
        onModeChange={(v) => { setMode(v); addLog(`Mode changed: ${v}`, 'info', 'system'); }}
        region={region}
        onRegionChange={(v) => { setRegion(v); addLog(`Region changed: ${v}`, 'info', 'system'); }}
        sftpQuery={sftpQuery}
        onSftpQueryChange={setSftpQuery}
        sftpLoading={sftpLoading}
        onSftpDownload={handleSftpDownload}
        onOpenFileManager={() => setFileModalOpen(true)}
      />

      <Row gutter={20} style={{ alignItems: 'stretch' }}>
        {/* ─── Left: Form ─── */}
        <Col xs={24} lg={16}>
          <Form form={form} layout="vertical" requiredMark={false}>
            {/* Rollout overrides */}
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
                  beforeUpload={(file) => { existingXml.handleExistingXmlChange(file); return false; }}
                  className="mod-upload-zone"
                >
                  <div style={{ padding: '8px 0' }}>
                    <CloudUploadOutlined style={{ fontSize: 28, color: existingXml.existingFile ? '#34d399' : '#7c3aed', marginBottom: 6 }} />
                    <p style={{ color: existingXml.existingFile ? '#34d399' : '#7878a0', fontWeight: existingXml.existingFile ? 600 : 400, margin: 0, fontSize: 13 }}>
                      {existingXml.existingFile ? `\u2713 ${existingXml.existingFile.name}` : t('existingXmlHelp')}
                    </p>
                  </div>
                </Upload.Dragger>
                {existingXml.stationName && (
                  <div className="mod-station-badge">
                    <FileProtectOutlined style={{ color: '#818cf8' }} />
                    <span style={{ color: '#7878a0', fontSize: 12 }}>{t('stationName')}</span>
                    <span style={{ color: '#c4b5fd', fontWeight: 700, fontSize: 15 }}>{existingXml.stationName}</span>
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
                  <Tag.CheckableTag key={s} checked={fileSelection.sectorFilter === s} onChange={(c) => fileSelection.setSectorFilter(c ? s : null)}>{s}</Tag.CheckableTag>
                ))}
                <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.06)', alignSelf: 'center' }} />
                {['AHEGA', 'AHEGB'].map((m) => (
                  <Tag.CheckableTag key={m} checked={fileSelection.modelFilter === m} onChange={(c) => fileSelection.setModelFilter(c ? m : null)}>{m}</Tag.CheckableTag>
                ))}
              </div>
              <Select
                value={fileSelection.selectedRef}
                onChange={(v) => { fileSelection.setSelectedRef(v); if (v) addLog(`Reference XML selected: ${v}`, 'info', 'system'); }}
                placeholder={t('selectFile')}
                allowClear showSearch
                options={fileSelection.filteredRefFiles.map((f) => ({ label: f, value: f }))}
                style={{ width: '100%', marginBottom: 8 }}
              />
              <Upload accept=".xml" maxCount={1} showUploadList beforeUpload={(file) => { fileSelection.setRefUploadFile(file); return false; }} onRemove={() => fileSelection.setRefUploadFile(null)}>
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
                  value={fileSelection.selectedIp}
                  onChange={(v) => { fileSelection.setSelectedIp(v); if (v) addLog(`IP Plan selected: ${v}`, 'info', 'system'); }}
                  placeholder={t('selectFile')}
                  allowClear showSearch
                  options={fileSelection.ipFiles.map((f) => ({ label: f, value: f }))}
                  style={{ flex: 1 }}
                  size="small"
                />
                <Upload accept=".xlsx,.xls" maxCount={1} showUploadList={false} beforeUpload={(file) => { fileSelection.setIpUploadFile(file); return false; }}>
                  <Button size="small" icon={<UploadOutlined />} style={{ borderRadius: 8, color: '#8888a8', fontSize: 12 }}>{t('uploadNew')}</Button>
                </Upload>
              </div>
              {fileSelection.ipPreview?.technologies ? (
                <div className="ip-preview-grid">
                  {Object.entries(fileSelection.ipPreview.technologies).map(([tech, info]: [string, TechnologyInfo]) => {
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
              ) : fileSelection.ipNotFound && fileSelection.ipLookupName ? (
                <div className="ip-preview-notfound">
                  <ExclamationCircleOutlined style={{ color: '#f59e0b', marginRight: 6 }} />
                  <span><strong>{fileSelection.ipLookupName}</strong> not found in IP Plan. VLAN/IP/GW will not be replaced.</span>
                </div>
              ) : fileSelection.selectedIp && !fileSelection.ipLookupName ? (
                <div style={{ color: '#555578', fontSize: 12, fontStyle: 'italic' }}>
                  {mode === 'modernization' ? t('uploadXmlToDetect') : t('enterMrbtsToPreview')}
                </div>
              ) : null}
            </div>

            {/* Generate button */}
            <Button
              type="primary"
              size="large"
              icon={<ThunderboltOutlined />}
              loading={generation.generating}
              onClick={generation.handleGenerate}
              block
              className="generate-btn"
              disabled={generation.generating || !canGenerate}
              style={{ marginTop: 16, marginBottom: 8 }}
            >
              {generation.generating ? t('processing') : t('generate')}
            </Button>
          </Form>
        </Col>

        {/* ─── Right: Info + Console ─── */}
        <Col xs={24} lg={8} style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            {existingXml.inspectData && (
              <InspectCard
                inspectData={existingXml.inspectData}
                detectedStationName={detectedStationName}
                onSelectSuggested={fileSelection.setSelectedRef}
              />
            )}
            <RecentGenerations files={generation.recentFiles} />
            <div style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <DebugConsole logs={logs} onClear={clearLogs} />
            </div>
          </div>
        </Col>
      </Row>

      <FileManagerModal
        open={fileModalOpen}
        onClose={() => setFileModalOpen(false)}
        region={region}
        refreshSignal={generation.genRefreshSignal}
      />

      {/* Existing XML parse progress */}
      <Modal
        open={existingXml.existingXmlParsing}
        title={<span style={{ color: '#f0f0f5' }}>{t('parseExistingXmlTitle')}</span>}
        footer={null}
        closable={false}
        width={520}
        styles={{ body: { paddingTop: 10 } }}
        centered
      >
        <Steps
          size="small"
          current={existingXml.existingXmlParseStep}
          items={[
            { title: t('parseExistingXmlStepExtract') },
            { title: t('parseExistingXmlStepInspect') },
            { title: t('parseExistingXmlStepApply') },
          ]}
        />
      </Modal>

      {/* XML generation progress */}
      <Modal
        open={generation.popupOpen}
        title={<span style={{ color: '#f0f0f5' }}>{t('generateXmlTitle')}</span>}
        footer={null}
        closable={false}
        width={520}
        styles={{ body: { paddingTop: 10 } }}
        centered
      >
        <Steps
          size="small"
          current={generation.popupStep}
          items={[
            { title: t('generateXmlStepSend') },
            { title: t('generateXmlStepGenerate') },
            { title: t('generateXmlStepDownload') },
          ]}
        />
      </Modal>
    </div>
  );
}
