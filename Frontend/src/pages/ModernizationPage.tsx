import { useState, useEffect, useCallback } from 'react';
import {
  Typography,
  Row,
  Col,
  Card,
  Form,
  Input,
  Button,
  Select,
  Upload,
  Segmented,
  Space,
  Tag,

  message,
  Descriptions,
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
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import {
  listExampleXml,
  listExampleExcel,
  inspectExistingXml,
  generateModernization,
  sftpDownload,
  downloadUrl,
  extractBtsName,
} from '../api/client';
import type { InspectResult } from '../api/client';
import DebugConsole, { type LogEntry, createLog } from '../components/DebugConsole';
import FileManagerModal from '../components/FileManagerModal';

const { Title, Text } = Typography;

export default function ModernizationPage() {
  const { t } = useTranslation();
  const [form] = Form.useForm();

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
      } catch {
        addLog('Could not extract station name', 'warning', 'extraction');
      }

      try {
        const inspRes = await inspectExistingXml(file, region);
        if (inspRes.data.success) {
          const d = inspRes.data.data;
          setInspectData(d);
          addLog(
            `3G: ${d.has3G ? 'YES' : 'NO'}, 4G: ${d.has4G ? 'YES' : 'NO'}, 5G: ${d.has5G ? 'YES' : 'NO'}, Sectors: ${d.sectorCount}`,
            'success',
            'extraction',
          );
          if (d.suggestedReference) {
            setSelectedRef(d.suggestedReference);
            addLog(`Suggested: ${d.suggestedReference}`, 'info', 'extraction');
          }
          if (d.sectorCount) setSectorFilter(`S${d.sectorCount}`);
          if (d.modelCodes?.length) setModelFilter(d.modelCodes[0].toUpperCase());
        }
      } catch {
        addLog('Could not inspect XML', 'warning', 'extraction');
      }
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
      a.href = url;
      a.download = filename;
      a.click();
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
    if (!existingFile) { message.warning(t('existingXmlHelp')); return; }

    setGenerating(true);
    addLog('Starting XML generation...', 'info', 'generation');
    const logName = mode === 'rollout'
      ? (form.getFieldValue('rolloutName') || stationName || '-')
      : (stationName || '-');
    addLog(`Station: "${logName}"`, 'info', 'generation');
    addLog(`Reference 5G XML: ${selectedRef || refUploadFile?.name || '-'}`, 'info', 'generation');
    addLog(`IP Plan: ${selectedIp || ipUploadFile?.name || '-'}`, 'info', 'generation');
    addLog(`Mode: ${mode === 'rollout' ? 'Rollout' : 'Modernization'}`, 'info', 'generation');
    addLog('Sending data to server...', 'info', 'generation');

    const fd = new FormData();
    fd.append('existingXml', existingFile);
    const effectiveName = mode === 'rollout'
      ? (form.getFieldValue('rolloutName') || stationName || '')
      : (stationName || '');
    fd.append('stationName', effectiveName);
    fd.append('mode', mode);
    fd.append('region', region);

    if (refUploadFile) fd.append('reference5gXmlUpload', refUploadFile);
    else if (selectedRef) fd.append('reference5gXmlSelection', selectedRef);

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

        // Detailed replacement report
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
            const planTxt = d.ip_plan_found ? 'FOUND' : 'NOT FOUND';
            addLog(`IP Plan lookup (${d.ip_plan_lookup_station || '-'}): ${planTxt}`, d.ip_plan_found ? 'success' : 'warning', 'generation');
          }

          addLog(`sctpPortMin: ref="${d.reference_sctp_port || 'N/A'}" → target="${d.existing_sctp_port || 'N/A'}" | Replaced: ${d.sctp_port_replacement_performed ? 'YES' : 'NO'}`, d.sctp_port_replacement_performed ? 'success' : 'info', 'generation');

          if (d.params_2g_replacement_performed && d.existing_2g_params && d.reference_2g_params) {
            addLog(`2G Parameters Replaced:`, 'success', 'generation');
            Object.entries(d.existing_2g_params).forEach(([key, value]: [string, any]) => {
              const old = d.reference_2g_params[key];
              if (old) addLog(`  ${key}: "${old}" → "${value}"`, 'success', 'generation');
            });
          } else {
            addLog(`2G Replacement: ${d.params_2g_replacement_performed ? 'YES' : 'NO (no 2G)'}`, 'info', 'generation');
          }

          addLog(`4G Cells Replacement: ${d.cells_4g_replacement_performed ? 'YES' : 'NO'}`, d.cells_4g_replacement_performed ? 'success' : 'info', 'generation');
          addLog(`4G RootSeq Replacement: ${d.rootseq_4g_replacement_performed ? 'YES' : 'NO'}`, d.rootseq_4g_replacement_performed ? 'success' : 'info', 'generation');
          addLog(`5G NRCells Replacement: ${d.nrcells_5g_replacement_performed ? 'YES' : 'NO'}`, d.nrcells_5g_replacement_performed ? 'success' : 'info', 'generation');

          addLog(`--- End Replacement Details ---`, 'info', 'generation');
        }

        // Backend debug log (VLAN/IP/GW replacements)
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

        // Download or warn about missing IP plan
        const doDownload = () => {
          addLog(t('autoDownload'), 'info', 'generation');
          const link = document.createElement('a');
          link.href = downloadUrl(data.filename);
          link.download = data.filename;
          link.click();
          message.success(`${t('generationSuccess')} ${data.filename}`);
          addLog(`${t('generationSuccess')} ${data.filename}`, 'success', 'generation');
        };

        if (data.warnings?.ip_plan) {
          addLog(`\u26A0 ${data.warnings.ip_plan}`, 'warning', 'generation');
          const lookupStation = d?.ip_plan_lookup_station || stationName || '?';
          Modal.confirm({
            title: <span style={{ color: '#fbbf24' }}>{t('ipPlanWarningTitle')}</span>,
            icon: <ExclamationCircleOutlined style={{ color: '#fbbf24' }} />,
            content: (
              <div style={{ color: '#d0d0e8' }}>
                <p style={{ marginBottom: 6 }}>
                  <strong style={{ color: '#c4b5fd' }}>{lookupStation}</strong>
                  {' — '}VLAN / IP / Gateway replacements were skipped.
                </p>
                <p style={{ color: '#b0b0c8' }}>{t('ipPlanConfirm')}</p>
              </div>
            ),
            okText: t('yes'),
            cancelText: t('no'),
            onOk: doDownload,
            onCancel: () => addLog('User cancelled — IP Plan not found', 'warning', 'generation'),
          });
        } else {
          doDownload();
        }
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

  const boolTag = (val: boolean) =>
    val ? (
      <Tag icon={<CheckCircleOutlined />} color="success" style={{ fontWeight: 500 }}>{t('yes')}</Tag>
    ) : (
      <Tag icon={<CloseCircleOutlined />} color="default" style={{ color: '#8888a8' }}>{t('no')}</Tag>
    );

  return (
    <>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={3} className="gradient-text" style={{ margin: 0, fontWeight: 700 }}>
          {t('modernization')}
        </Title>
        <Button
          icon={<FolderOpenOutlined />}
          onClick={() => setFileModalOpen(true)}
          style={{ borderRadius: 10 }}
        >
          {t('manageFiles')}
        </Button>
      </div>

      {/* SFTP Download */}
      <Card className="glass-card" size="small" style={{ marginBottom: 20 }}>
        <Text style={{ display: 'block', marginBottom: 10, fontSize: 13, color: '#8888a8' }}>
          {t('sftpLabel')}
        </Text>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="ID / Station Name"
            value={sftpQuery}
            onChange={(e) => setSftpQuery(e.target.value)}
            onPressEnter={handleSftpDownload}
            style={{ borderRadius: '10px 0 0 10px' }}
          />
          <Button
            type="primary"
            icon={<CloudDownloadOutlined />}
            loading={sftpLoading}
            onClick={handleSftpDownload}
            style={{ borderRadius: '0 10px 10px 0' }}
          >
            {t('sftpBtn')}
          </Button>
        </Space.Compact>
      </Card>

      <Row gutter={20}>
        {/* Left column */}
        <Col xs={24} lg={16}>
          <Card className="glass-card">
            {/* Mode & Region */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
              <div>
                <Text style={{ fontSize: 12, color: '#8888a8', display: 'block', marginBottom: 6 }}>{t('mode')}</Text>
                <Segmented
                  value={mode}
                  options={[
                    { label: t('modeModernization'), value: 'modernization' },
                    { label: t('modeRollout'), value: 'rollout' },
                  ]}
                  onChange={(v) => { setMode(v as 'modernization' | 'rollout'); addLog(`Mode changed: ${v}`, 'info', 'system'); }}
                />
              </div>
              <div style={{ width: 1, height: 40, background: 'rgba(255,255,255,0.08)' }} />
              <div>
                <Text style={{ fontSize: 12, color: '#8888a8', display: 'block', marginBottom: 6 }}>{t('region')}</Text>
                <Segmented
                  value={region}
                  options={[
                    { label: t('east'), value: 'East' },
                    { label: t('west'), value: 'West' },
                  ]}
                  onChange={(v) => { setRegion(v as string); addLog(`Region changed: ${v}`, 'info', 'system'); }}
                />
              </div>
            </div>

            <Form form={form} layout="vertical" requiredMark={false}>
              {mode === 'rollout' && (
                <Row gutter={12}>
                  <Col span={8}>
                    <Form.Item name="rolloutId" label={t('mrbtsId')}>
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="rolloutName" label={t('mrbtsName')}>
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="rolloutTac" label={t('tac')}>
                      <Input />
                    </Form.Item>
                  </Col>
                </Row>
              )}

              {/* Existing XML */}
              <Form.Item label={<span><FileTextOutlined style={{ marginRight: 6, color: '#818cf8' }} />{t('existingXml')}</span>} required>
                <Upload.Dragger
                  accept=".xml"
                  maxCount={1}
                  showUploadList={false}
                  beforeUpload={(file) => { handleExistingXmlChange(file); return false; }}
                >
                  <div style={{ padding: '12px 0' }}>
                    <CloudUploadOutlined style={{ fontSize: 32, color: '#7c3aed', marginBottom: 8 }} />
                    <p style={{ color: existingFile ? '#c4b5fd' : '#7878a0', fontWeight: existingFile ? 500 : 400, margin: 0 }}>
                      {existingFile ? existingFile.name : t('existingXmlHelp')}
                    </p>
                  </div>
                </Upload.Dragger>
              </Form.Item>

              {/* Station name: read-only display in modernization, editable in rollout */}
              {stationName && mode === 'modernization' && (
                <div style={{
                  background: 'rgba(124, 58, 237, 0.08)',
                  border: '1px solid rgba(124, 58, 237, 0.2)',
                  borderRadius: 10,
                  padding: '10px 16px',
                  marginBottom: 20,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}>
                  <Text style={{ color: '#8888a8', fontSize: 13 }}>{t('stationName')}:</Text>
                  <Text style={{ color: '#c4b5fd', fontWeight: 600, fontSize: 15 }}>{stationName}</Text>
                </div>
              )}
              

              {/* Reference 5G XML */}
              <Form.Item label={<span><WifiOutlined style={{ marginRight: 6, color: '#818cf8' }} />{t('reference5g')}</span>}>
                <Space style={{ marginBottom: 10 }} wrap>
                  {['S2', 'S3', 'S4'].map((s) => (
                    <Tag.CheckableTag
                      key={s}
                      checked={sectorFilter === s}
                      onChange={(checked) => setSectorFilter(checked ? s : null)}
                    >
                      {s}
                    </Tag.CheckableTag>
                  ))}
                  <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.08)' }} />
                  {['AHEGA', 'AHEGB'].map((m) => (
                    <Tag.CheckableTag
                      key={m}
                      checked={modelFilter === m}
                      onChange={(checked) => setModelFilter(checked ? m : null)}
                    >
                      {m}
                    </Tag.CheckableTag>
                  ))}
                </Space>
                <Select
                  value={selectedRef}
                  onChange={(v) => { setSelectedRef(v); if (v) addLog(`Reference XML selected: ${v}`, 'info', 'system'); }}
                  placeholder={t('selectFile')}
                  allowClear
                  showSearch
                  options={filteredRefFiles.map((f) => ({ label: f, value: f }))}
                  style={{ width: '100%', marginBottom: 10 }}
                />
                <Upload
                  accept=".xml"
                  maxCount={1}
                  showUploadList
                  beforeUpload={(file) => { setRefUploadFile(file); return false; }}
                  onRemove={() => setRefUploadFile(null)}
                >
                  <Button size="small" icon={<UploadOutlined />} style={{ borderRadius: 8, color: '#b0b0c8' }}>
                    {t('uploadNew')}
                  </Button>
                </Upload>
              </Form.Item>

              {/* IP Plan */}
              <Form.Item label={<span><DatabaseOutlined style={{ marginRight: 6, color: '#818cf8' }} />{t('ipPlan')}</span>}>
                <Select
                  value={selectedIp}
                  onChange={(v) => { setSelectedIp(v); if (v) addLog(`IP Plan selected: ${v}`, 'info', 'system'); }}
                  placeholder={t('selectFile')}
                  allowClear
                  showSearch
                  options={ipFiles.map((f) => ({ label: f, value: f }))}
                  style={{ width: '100%', marginBottom: 10 }}
                />
                <Upload
                  accept=".xlsx,.xls"
                  maxCount={1}
                  showUploadList
                  beforeUpload={(file) => { setIpUploadFile(file); return false; }}
                  onRemove={() => setIpUploadFile(null)}
                >
                  <Button size="small" icon={<UploadOutlined />} style={{ borderRadius: 8, color: '#b0b0c8' }}>
                    {t('uploadNew')}
                  </Button>
                </Upload>
              </Form.Item>

              {/* Generate */}
              <Button
                type="primary"
                size="large"
                icon={<ThunderboltOutlined />}
                loading={generating}
                onClick={handleGenerate}
                block
                className="generate-btn"
              >
                {generating ? t('processing') : t('generate')}
              </Button>
            </Form>
          </Card>
        </Col>

        {/* Right column */}
        <Col xs={24} lg={8}>
          {/* Inspect results */}
          {inspectData && (
            <Card
              className="glass-card"
              size="small"
              style={{ marginBottom: 16 }}
            >
              <Text strong style={{ display: 'block', marginBottom: 12, color: '#c4b5fd', fontSize: 14 }}>
                <RadarChartOutlined style={{ marginRight: 8 }} />{t('detected')}
              </Text>
              <Descriptions
                size="small"
                column={2}
                colon={false}
                styles={{
                  label: { color: '#8888a8' },
                  content: { color: '#f0f0f5' },
                }}
              >
                <Descriptions.Item label="3G">{boolTag(inspectData.has3G)}</Descriptions.Item>
                <Descriptions.Item label="4G">{boolTag(inspectData.has4G)}</Descriptions.Item>
                <Descriptions.Item label="5G">{boolTag(inspectData.has5G)}</Descriptions.Item>
                <Descriptions.Item label={t('sectors')}>
                  <Tag color="blue" style={{ fontWeight: 600 }}>{inspectData.sectorCount}</Tag>
                </Descriptions.Item>
              </Descriptions>
              {inspectData.models?.length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <Text style={{ fontSize: 12, color: '#8888a8' }}>{t('modules')}:</Text>{' '}
                  {inspectData.models.map((m) => (
                    <Tag key={m} color="geekblue">{m}</Tag>
                  ))}
                </div>
              )}
              {inspectData.suggestedReference && (
                <div style={{ marginTop: 10 }}>
                  <Text style={{ fontSize: 12, color: '#8888a8' }}>{t('suggestion')}:</Text>{' '}
                  <Tooltip title="Click to select">
                    <Tag
                      color="purple"
                      style={{ cursor: 'pointer', fontWeight: 500 }}
                      onClick={() => setSelectedRef(inspectData.suggestedReference!)}
                    >
                      {inspectData.suggestedReference}
                    </Tag>
                  </Tooltip>
                </div>
              )}
            </Card>
          )}

          <DebugConsole logs={logs} onClear={clearLogs} />
        </Col>
      </Row>

      <FileManagerModal open={fileModalOpen} onClose={() => setFileModalOpen(false)} region={region} />
    </>
  );
}
