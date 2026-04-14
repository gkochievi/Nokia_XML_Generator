import { Typography, Segmented, Space, Input, Button, Tooltip } from 'antd';
import {
  SwapOutlined, EnvironmentOutlined, CloudDownloadOutlined,
  FolderOpenOutlined, ToolOutlined, RocketOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import eastSvg from '../../assets/east.svg';
import westSvg from '../../assets/west.svg';

const { Text } = Typography;

interface Props {
  mode: 'modernization' | 'rollout';
  onModeChange: (mode: 'modernization' | 'rollout') => void;
  region: string;
  onRegionChange: (region: string) => void;
  sftpQuery: string;
  onSftpQueryChange: (query: string) => void;
  sftpLoading: boolean;
  onSftpDownload: () => void;
  onOpenFileManager: () => void;
}

export default function ControlsBar({
  mode, onModeChange, region, onRegionChange,
  sftpQuery, onSftpQueryChange, sftpLoading, onSftpDownload,
  onOpenFileManager,
}: Props) {
  const { t } = useTranslation();

  const regionIcon = (which: 'East' | 'West') => (
    <Tooltip title={which === 'East' ? `${t('east')} ${t('georgia')}` : `${t('west')} ${t('georgia')}`}>
      <span className={`region-icon ${which === 'East' ? 'region-icon-east' : 'region-icon-west'}`}>
        <img src={which === 'East' ? eastSvg : westSvg} alt={which} />
      </span>
    </Tooltip>
  );

  return (
    <div className="mod-controls-bar">
      <div className="mod-control-group">
        <SwapOutlined style={{ color: '#818cf8', fontSize: 14 }} />
        <Text style={{ color: '#7878a0', fontSize: 12, fontWeight: 600 }}>{t('mode')}</Text>
        <Segmented
          value={mode}
          options={[
            { label: <Tooltip title={t('modeModernization')}><span className="mode-option"><ToolOutlined /></span></Tooltip>, value: 'modernization' },
            { label: <Tooltip title={t('modeRollout')}><span className="mode-option"><RocketOutlined /></span></Tooltip>, value: 'rollout' },
          ]}
          onChange={(v) => onModeChange(v as 'modernization' | 'rollout')}
        />
      </div>
      <div className="mod-controls-divider" />
      <div className="mod-control-group">
        <EnvironmentOutlined style={{ color: '#34d399', fontSize: 14 }} />
        <Text style={{ color: '#7878a0', fontSize: 12, fontWeight: 600 }}>{t('region')}</Text>
        <Segmented
          value={region}
          options={[
            { label: regionIcon('West'), value: 'West' },
            { label: regionIcon('East'), value: 'East' },
          ]}
          onChange={(v) => onRegionChange(v as string)}
        />
      </div>
      <div className="mod-controls-divider" />
      <div className="mod-control-group">
        <CloudDownloadOutlined style={{ color: '#60a5fa', fontSize: 14 }} />
        <Text style={{ color: '#7878a0', fontSize: 12, fontWeight: 600 }}>SFTP</Text>
        <Space.Compact size="small">
          <Input
            placeholder={t('sftpPlaceholder')}
            value={sftpQuery}
            onChange={(e) => onSftpQueryChange(e.target.value)}
            onPressEnter={onSftpDownload}
            style={{ width: 170, borderRadius: '8px 0 0 8px' }}
            size="middle"
          />
          <Button type="primary" icon={<CloudDownloadOutlined />} loading={sftpLoading} onClick={onSftpDownload} size="middle" style={{ borderRadius: '0 8px 8px 0' }} />
        </Space.Compact>
      </div>
      <div style={{ marginLeft: 'auto' }}>
        <Tooltip title={t('manageFiles')}>
          <Button
            icon={<FolderOpenOutlined />}
            onClick={onOpenFileManager}
            className="mod-manage-btn"
            size="small"
          />
        </Tooltip>
      </div>
    </div>
  );
}
