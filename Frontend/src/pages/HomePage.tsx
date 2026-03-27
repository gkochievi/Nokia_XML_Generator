import { Row, Col, Typography } from 'antd';
import {
  ToolOutlined,
  RocketOutlined,
  FileSearchOutlined,
  ArrowRightOutlined,
  WifiOutlined,
  ApiOutlined,
  DeploymentUnitOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

const tools = [
  {
    key: 'modernization',
    path: '/modernization',
    icon: <ToolOutlined />,
    accent: <WifiOutlined />,
    gradient: 'linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)',
    shadow: 'rgba(124, 58, 237, 0.25)',
    accentColor: '#7c3aed',
    borderColor: 'rgba(124, 58, 237, 0.15)',
  },
  {
    key: 'rollout',
    path: '/modernization?mode=rollout',
    icon: <RocketOutlined />,
    accent: <DeploymentUnitOutlined />,
    gradient: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
    shadow: 'rgba(37, 99, 235, 0.25)',
    accentColor: '#2563eb',
    borderColor: 'rgba(37, 99, 235, 0.15)',
  },
  {
    key: 'xmlViewer',
    path: '/xml-viewer',
    icon: <FileSearchOutlined />,
    accent: <ApiOutlined />,
    gradient: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
    shadow: 'rgba(16, 185, 129, 0.25)',
    accentColor: '#10b981',
    borderColor: 'rgba(16, 185, 129, 0.15)',
  },
];

const descKeys: Record<string, string> = {
  modernization: 'modernizationDesc',
  rollout: 'rolloutDesc',
  xmlViewer: 'xmlViewerDesc',
};

export default function HomePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div style={{ paddingTop: 48 }}>
      {/* Hero */}
      <div className="home-hero">
        <div className="home-hero-icon">
          <ThunderboltOutlined />
        </div>
        <div className="home-hero-title gradient-text">
          BTS Forge
        </div>
        <Text style={{ color: '#6b6b88', fontSize: 14, display: 'block' }}>
          {t('homeSubtitle')}
        </Text>
      </div>

      {/* Tool cards */}
      <Row gutter={[20, 20]} justify="center">
        {tools.map((tool) => (
          <Col xs={24} sm={12} md={8} key={tool.key}>
            <div
              className="home-card"
              style={{ borderColor: tool.borderColor }}
              onClick={() => navigate(tool.path)}
            >
              {/* Background accent */}
              <div className="home-card-accent" style={{ color: tool.accentColor }}>
                {tool.accent}
              </div>

              {/* Icon */}
              <div
                className="home-card-icon"
                style={{ background: tool.gradient, boxShadow: `0 6px 24px ${tool.shadow}` }}
              >
                {tool.icon}
              </div>

              {/* Text */}
              <div className="home-card-title">{t(tool.key)}</div>
              <div className="home-card-desc">{t(descKeys[tool.key])}</div>

              {/* Arrow */}
              <div className="home-card-arrow">
                <ArrowRightOutlined />
              </div>
            </div>
          </Col>
        ))}
      </Row>

      {/* Stats bar */}
      <div className="home-stats">
        <div className="home-stat">
          <WifiOutlined style={{ color: '#7c3aed' }} />
          <span>5G Modernization</span>
        </div>
        <div className="home-stat-divider" />
        <div className="home-stat">
          <DeploymentUnitOutlined style={{ color: '#2563eb' }} />
          <span>New Site Rollout</span>
        </div>
        <div className="home-stat-divider" />
        <div className="home-stat">
          <ApiOutlined style={{ color: '#10b981' }} />
          <span>XML Analysis</span>
        </div>
      </div>
    </div>
  );
}
