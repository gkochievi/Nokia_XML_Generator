import { useRef, useEffect, useCallback, useState } from 'react';
import { Tabs, Button, Typography } from 'antd';
import { ClearOutlined, DownOutlined, UpOutlined, CodeOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

export interface LogEntry {
  time: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
  tab: 'extraction' | 'generation' | 'system';
}

interface Props {
  logs: LogEntry[];
  onClear: (tab: string) => void;
}

function timestamp() {
  const d = new Date();
  return d.toLocaleTimeString('en-GB', { hour12: false });
}

export function createLog(
  message: string,
  level: LogEntry['level'],
  tab: LogEntry['tab'],
): LogEntry {
  return { time: timestamp(), message, level, tab };
}

export default function DebugConsole({ logs, onClear }: Props) {
  const { t } = useTranslation();
  const [collapsed, setCollapsed] = useState(true);
  const [activeTab, setActiveTab] = useState('extraction');
  const endRef = useRef<HTMLDivElement>(null);

  const filteredLogs = logs.filter((l) => l.tab === activeTab);

  // Auto-switch to the tab that received the latest log and expand if collapsed
  useEffect(() => {
    if (logs.length > 0) {
      const lastLog = logs[logs.length - 1];
      if (lastLog.tab !== activeTab) {
        setActiveTab(lastLog.tab);
      }
      if (collapsed) {
        setCollapsed(false);
      }
    }
  }, [logs.length]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [filteredLogs.length]);

  const renderLogs = useCallback(
    () =>
      filteredLogs.map((log, i) => (
        <div key={i} className="log-line">
          <span className="log-time">[{log.time}]</span>
          <span className={`log-${log.level}`}>{log.message}</span>
        </div>
      )),
    [filteredLogs],
  );

  const tabCounts = {
    extraction: logs.filter((l) => l.tab === 'extraction').length,
    generation: logs.filter((l) => l.tab === 'generation').length,
    system: logs.filter((l) => l.tab === 'system').length,
  };

  const tabItems = [
    { key: 'extraction', label: `${t('extraction')}${tabCounts.extraction ? ` (${tabCounts.extraction})` : ''}` },
    { key: 'generation', label: `${t('generation')}${tabCounts.generation ? ` (${tabCounts.generation})` : ''}` },
    { key: 'system', label: `${t('system')}${tabCounts.system ? ` (${tabCounts.system})` : ''}` },
  ];

  return (
    <div style={{ marginTop: 16 }}>
      <div
        className="debug-console-header"
        onClick={() => setCollapsed(!collapsed)}
      >
        <Typography.Text style={{ color: '#b0b0c8', fontSize: 13, fontWeight: 600 }}>
          <CodeOutlined style={{ marginRight: 7, color: '#818cf8' }} />
          {t('debugConsole')}
        </Typography.Text>
        <div
          className="debug-console-toggle"
        >
          {collapsed ? <DownOutlined /> : <UpOutlined />}
        </div>
      </div>

      {!collapsed && (
        <>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size="small"
            items={tabItems}
            tabBarExtraContent={
              <Button
                type="text"
                size="small"
                icon={<ClearOutlined />}
                onClick={() => onClear(activeTab)}
                style={{ color: '#7878a0' }}
              />
            }
          />
          <div className="debug-console">
            {filteredLogs.length === 0 ? (
              <div style={{ color: '#555578', fontStyle: 'italic' }}>No logs yet.</div>
            ) : (
              renderLogs()
            )}
            <div ref={endRef} />
          </div>
        </>
      )}
    </div>
  );
}
