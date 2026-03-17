import { Row, Col, Card, Typography } from 'antd';
import {
  ToolOutlined,
  RocketOutlined,
  FileSearchOutlined,
  ArrowRightOutlined,
  WifiOutlined,
  ApiOutlined,
  DeploymentUnitOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;

const tools = [
  {
    key: 'modernization',
    path: '/modernization',
    icon: <ToolOutlined />,
    accent: <WifiOutlined />,
    gradient: 'linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)',
    shadow: 'rgba(124, 58, 237, 0.25)',
    accentColor: '#7c3aed',
  },
  {
    key: 'rollout',
    path: '/modernization',
    icon: <RocketOutlined />,
    accent: <DeploymentUnitOutlined />,
    gradient: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
    shadow: 'rgba(37, 99, 235, 0.25)',
    accentColor: '#2563eb',
  },
  {
    key: 'xmlViewer',
    path: '/xml-viewer',
    icon: <FileSearchOutlined />,
    accent: <ApiOutlined />,
    gradient: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
    shadow: 'rgba(16, 185, 129, 0.25)',
    accentColor: '#10b981',
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
    <div style={{ textAlign: 'center', paddingTop: 72 }}>
      <div style={{ marginBottom: 12 }}>
        <WifiOutlined style={{ fontSize: 40, color: '#7c3aed', opacity: 0.5 }} />
      </div>
      <Title
        level={1}
        className="gradient-text"
        style={{ marginBottom: 8, fontSize: 38, fontWeight: 700, letterSpacing: '-0.5px' }}
      >
        {t('homeTitle')}
      </Title>
      <Text style={{ fontSize: 16, display: 'block', marginBottom: 60, color: '#7878a0' }}>
        {t('homeSubtitle')}
      </Text>

      <Row gutter={[28, 28]} justify="center">
        {tools.map((tool) => (
          <Col xs={24} sm={12} md={8} key={tool.key}>
            <Card
              hoverable
              className="feature-card"
              onClick={() => navigate(tool.path)}
              styles={{ body: { padding: '44px 28px 36px' } }}
            >
              {/* Decorative accent icon */}
              <div className="feature-card-accent" style={{ color: tool.accentColor }}>
                {tool.accent}
              </div>

              <div
                className="icon-circle"
                style={{
                  background: tool.gradient,
                  boxShadow: `0 8px 28px ${tool.shadow}`,
                  color: '#fff',
                }}
              >
                {tool.icon}
              </div>
              <Title level={4} style={{ margin: '0 0 8px', color: '#f0f0f5', fontWeight: 600 }}>
                {t(tool.key)}
              </Title>
              <Text style={{ color: '#7878a0', fontSize: 14, display: 'block', marginBottom: 16 }}>
                {t(descKeys[tool.key])}
              </Text>
              <div className="feature-card-arrow">
                <ArrowRightOutlined />
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
