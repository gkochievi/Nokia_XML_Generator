import { HistoryOutlined, DownloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { downloadUrl } from '../../api/client';

interface Props {
  files: { name: string; mtime?: number; size?: number }[];
}

export default function RecentGenerations({ files }: Props) {
  const { t } = useTranslation();

  if (files.length === 0) return null;

  return (
    <div className="mod-history-card">
      <div className="mod-section-header" style={{ marginBottom: 10 }}>
        <HistoryOutlined style={{ color: '#60a5fa' }} />
        <span style={{ fontSize: 13 }}>{t('recentGenerations')}</span>
      </div>
      {files.map((f, i) => (
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
  );
}
