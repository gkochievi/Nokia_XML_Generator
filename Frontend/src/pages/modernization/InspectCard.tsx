import { Button, Tag, Tooltip, message } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined,
  RadarChartOutlined, AppstoreOutlined, BranchesOutlined,
  AimOutlined, CopyOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { InspectResult } from '../../api/client';

interface Props {
  inspectData: InspectResult['data'];
  detectedStationName: string;
  onSelectSuggested: (ref: string) => void;
}

export default function InspectCard({ inspectData, detectedStationName, onSelectSuggested }: Props) {
  const { t } = useTranslation();

  const techBadge = (label: string, has: boolean) => (
    <span className={`tech-badge ${has ? 'yes' : 'no'}`}>
      {has ? <CheckCircleOutlined /> : <CloseCircleOutlined />} {label}
    </span>
  );

  const handleCopyStationName = async () => {
    const text = String(detectedStationName || '').trim();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      message.success(t('copied'));
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      message.success(t('copied'));
    }
  };

  return (
    <div className="mod-inspect-card">
      <div className="mod-section-header" style={{ marginBottom: 14 }}>
        <RadarChartOutlined style={{ color: '#c4b5fd' }} />
        <span>{t('detected')}</span>
      </div>
      {detectedStationName && (
        <div className="mod-detected-name-row">
          <span className="mod-detected-name-label">{t('stationName')}:</span>
          <span className="mod-detected-name-value">{detectedStationName}</span>
          <Button
            size="small"
            icon={<CopyOutlined />}
            onClick={handleCopyStationName}
            style={{ marginLeft: 8, borderRadius: 10 }}
          />
        </div>
      )}
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
      {(inspectData.radioModuleSummary || inspectData.models?.length > 0) && (
        <div className="mod-inspect-row">
          <BranchesOutlined style={{ color: '#818cf8' }} />
          <span className="mod-inspect-label">{t('modules')}</span>
          <span style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
            {inspectData.radioModuleSummary
              ? <Tag color="geekblue" style={{ margin: 0, fontWeight: 600 }}>{inspectData.radioModuleSummary}</Tag>
              : inspectData.models.map((m) => <Tag key={m} color="geekblue" style={{ margin: 0 }}>{m}</Tag>)
            }
          </span>
        </div>
      )}
      {inspectData.radioModules && inspectData.radioModules.length > 0 && (
        <div style={{ marginTop: 6, paddingLeft: 30 }}>
          {inspectData.radioModules.map((rm, i) => (
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
              onClick={() => onSelectSuggested(inspectData.suggestedReference!)}
            >
              {inspectData.suggestedReference}
            </Tag>
          </Tooltip>
        </div>
      )}
    </div>
  );
}
