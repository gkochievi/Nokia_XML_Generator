import { useState, useEffect, useCallback, useMemo } from 'react';
import { Modal, Tabs, List, Button, Upload, Space, Input, message, Segmented, Empty } from 'antd';
import {
  DeleteOutlined,
  DownloadOutlined,
  ReloadOutlined,
  UploadOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import {
  listExampleXml,
  listExampleExcel,
  listGeneratedFiles,
  deleteExampleFile,
  deleteGeneratedFile,
  uploadExampleFile,
  downloadUrl,
} from '../api/client';

interface Props {
  open: boolean;
  onClose: () => void;
  region: string;
}

export default function FileManagerModal({ open, onClose, region }: Props) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('ref');
  const [refRegion, setRefRegion] = useState(region);
  const [refFiles, setRefFiles] = useState<string[]>([]);
  const [ipFiles, setIpFiles] = useState<string[]>([]);
  const [genFiles, setGenFiles] = useState<{ name: string; mtime?: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const loadRef = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await listExampleXml(refRegion);
      setRefFiles(data.files || []);
    } catch { setRefFiles([]); }
    setLoading(false);
  }, [refRegion]);

  const loadIp = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await listExampleExcel('ip');
      setIpFiles(data.files || []);
    } catch { setIpFiles([]); }
    setLoading(false);
  }, []);

  const loadGen = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await listGeneratedFiles();
      if (data.filesWithMtime) {
        setGenFiles(data.filesWithMtime);
      } else {
        setGenFiles((data.files || []).map((f: string) => ({ name: f })));
      }
    } catch { setGenFiles([]); }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!open) return;
    setSearch('');
    if (activeTab === 'ref') loadRef();
    else if (activeTab === 'ip') loadIp();
    else loadGen();
  }, [open, activeTab, loadRef, loadIp, loadGen]);

  useEffect(() => { setRefRegion(region); }, [region]);
  useEffect(() => { if (open && activeTab === 'ref') loadRef(); }, [refRegion, open, activeTab, loadRef]);

  const q = search.toLowerCase();

  const filteredRef = useMemo(
    () => (q ? refFiles.filter((f) => f.toLowerCase().includes(q)) : refFiles),
    [refFiles, q],
  );
  const filteredIp = useMemo(
    () => (q ? ipFiles.filter((f) => f.toLowerCase().includes(q)) : ipFiles),
    [ipFiles, q],
  );
  const filteredGen = useMemo(
    () => (q ? genFiles.filter((f) => f.name.toLowerCase().includes(q)) : genFiles),
    [genFiles, q],
  );

  const handleDeleteRef = async (filename: string) => {
    await deleteExampleFile(filename, { region: refRegion });
    message.success('Deleted');
    loadRef();
  };

  const handleDeleteIp = async (filename: string) => {
    await deleteExampleFile(filename, { category: 'ip' });
    message.success('Deleted');
    loadIp();
  };

  const handleDeleteGen = async (filename: string) => {
    await deleteGeneratedFile(filename);
    message.success('Deleted');
    loadGen();
  };

  const emptyNode = <Empty description={<span style={{ color: '#555578' }}>No files</span>} />;

  const renderRefTab = () => (
    <>
      <Space style={{ marginBottom: 14 }}>
        <Segmented
          value={refRegion}
          options={[
            { label: t('east'), value: 'East' },
            { label: t('west'), value: 'West' },
          ]}
          onChange={(v) => setRefRegion(v as string)}
        />
        <Button icon={<ReloadOutlined />} size="small" onClick={loadRef} style={{ borderRadius: 8 }} />
        <Upload
          showUploadList={false}
          accept=".xml"
          beforeUpload={(file) => {
            uploadExampleFile(file, { region: refRegion }).then(() => {
              message.success('Uploaded');
              loadRef();
            });
            return false;
          }}
        >
          <Button size="small" icon={<UploadOutlined />} style={{ borderRadius: 8, color: '#b0b0c8' }}>
            {t('uploadNew')}
          </Button>
        </Upload>
      </Space>
      <List
        size="small"
        loading={loading}
        dataSource={filteredRef}
        locale={{ emptyText: emptyNode }}
        renderItem={(f) => (
          <List.Item
            actions={[
              <Button
                key="del"
                danger
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => handleDeleteRef(f)}
              />,
            ]}
          >
            <span style={{ color: '#e0e0f0' }}>{f}</span>
          </List.Item>
        )}
      />
    </>
  );

  const renderIpTab = () => (
    <>
      <Space style={{ marginBottom: 14 }}>
        <Button icon={<ReloadOutlined />} size="small" onClick={loadIp} style={{ borderRadius: 8 }} />
        <Upload
          showUploadList={false}
          accept=".xlsx,.xls"
          beforeUpload={(file) => {
            uploadExampleFile(file, { category: 'ip' }).then(() => {
              message.success('Uploaded');
              loadIp();
            });
            return false;
          }}
        >
          <Button size="small" icon={<UploadOutlined />} style={{ borderRadius: 8, color: '#b0b0c8' }}>
            {t('uploadNew')}
          </Button>
        </Upload>
      </Space>
      <List
        size="small"
        loading={loading}
        dataSource={filteredIp}
        locale={{ emptyText: emptyNode }}
        renderItem={(f) => (
          <List.Item
            actions={[
              <Button
                key="del"
                danger
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => handleDeleteIp(f)}
              />,
            ]}
          >
            <span style={{ color: '#e0e0f0' }}>{f}</span>
          </List.Item>
        )}
      />
    </>
  );

  const formatDate = (mtime?: number) => {
    if (!mtime) return '';
    const d = new Date(mtime * 1000);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  const renderGenTab = () => (
    <>
      <Space style={{ marginBottom: 14 }}>
        <Button icon={<ReloadOutlined />} size="small" onClick={loadGen} style={{ borderRadius: 8 }} />
      </Space>
      <List
        size="small"
        loading={loading}
        dataSource={filteredGen}
        locale={{ emptyText: emptyNode }}
        renderItem={(f) => (
          <List.Item
            actions={[
              <Button
                key="dl"
                type="text"
                size="small"
                icon={<DownloadOutlined />}
                href={downloadUrl(f.name)}
                style={{ color: '#818cf8' }}
              />,
              <Button
                key="del"
                danger
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => handleDeleteGen(f.name)}
              />,
            ]}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={{ color: '#e0e0f0' }}>{f.name}</span>
              {f.mtime && (
                <span style={{ color: '#6b6b88', fontSize: 11 }}>{formatDate(f.mtime)}</span>
              )}
            </div>
          </List.Item>
        )}
      />
    </>
  );

  return (
    <Modal
      title={<span style={{ color: '#f0f0f5' }}>{t('manageFiles')}</span>}
      open={open}
      onCancel={onClose}
      footer={
        <Button onClick={onClose} style={{ borderRadius: 8 }}>
          {t('close')}
        </Button>
      }
      width={660}
      styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column', maxHeight: '70vh' } }}
    >
      <div style={{ padding: '16px 24px 0', flexShrink: 0 }}>
        <Input
          placeholder={t('filter') + '...'}
          prefix={<SearchOutlined style={{ color: '#7878a0' }} />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          style={{ marginBottom: 12 }}
        />
        <Tabs
          activeKey={activeTab}
          onChange={(key) => { setActiveTab(key); setSearch(''); }}
          items={[
            { key: 'ref', label: `${t('referenceXmls')} (${filteredRef.length})` },
            { key: 'ip', label: `${t('ipPlanFiles')} (${filteredIp.length})` },
            { key: 'gen', label: `${t('generatedFiles')} (${filteredGen.length})` },
          ]}
          style={{ marginBottom: 0 }}
        />
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px 16px' }}>
        {activeTab === 'ref' && renderRefTab()}
        {activeTab === 'ip' && renderIpTab()}
        {activeTab === 'gen' && renderGenTab()}
      </div>
    </Modal>
  );
}
