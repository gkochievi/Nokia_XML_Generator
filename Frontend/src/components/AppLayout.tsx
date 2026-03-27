import { Layout } from 'antd';
import {
  HomeOutlined,
  ToolOutlined,
  FileSearchOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const { Content } = Layout;

const navItems = [
  { key: '/', icon: <HomeOutlined />, labelKey: 'home' },
  { key: '/modernization', icon: <ToolOutlined />, labelKey: 'modernization' },
  { key: '/xml-viewer', icon: <FileSearchOutlined />, labelKey: 'xmlViewer' },
];

export default function AppLayout() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const currentLang = i18n.language;

  const switchLang = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('lang', lang);
    document.documentElement.setAttribute('lang', lang);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Tech background layers */}
      <div className="bg-grid" />
      <div className="bg-glow" />
      <div className="bg-lines" />
      <div className="bg-corner-glow bg-corner-glow-tl" />
      <div className="bg-corner-glow bg-corner-glow-br" />

      {/* ─── Navbar ─── */}
      <nav className="app-navbar">
        <div className="nav-inner">
          {/* Brand */}
          <div className="nav-brand" onClick={() => navigate('/')}>
            <span className="gradient-text">BTS</span>
            <span className="brand-suffix">Forge</span>
          </div>

          {/* Nav links */}
          <div className="nav-links">
            {navItems.map((item) => {
              const active = location.pathname === item.key;
              return (
                <button
                  key={item.key}
                  className={`nav-pill ${active ? 'nav-pill-active' : ''}`}
                  onClick={() => navigate(item.key)}
                >
                  <span className="nav-pill-icon">{item.icon}</span>
                  <span className="nav-pill-label">{t(item.labelKey)}</span>
                </button>
              );
            })}
          </div>

          {/* Language switcher */}
          <div className="nav-lang">
            <GlobalOutlined className="nav-lang-globe" />
            <div className="lang-toggle">
              <button
                className={`lang-btn ${currentLang === 'ka' ? 'lang-btn-active' : ''}`}
                onClick={() => switchLang('ka')}
              >
                🇬🇪
              </button>
              <button
                className={`lang-btn ${currentLang === 'en' ? 'lang-btn-active' : ''}`}
                onClick={() => switchLang('en')}
              >
                🇬🇧
              </button>
            </div>
          </div>
        </div>
      </nav>

      <Content style={{ padding: '28px 32px', maxWidth: 1440, margin: '0 auto', width: '100%' }}>
        <Outlet />
      </Content>
    </Layout>
  );
}
