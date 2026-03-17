import type { ThemeConfig } from 'antd';

const theme: ThemeConfig = {
  token: {
    colorPrimary: '#7c3aed',
    colorBgBase: '#0b0b14',
    colorBgContainer: '#141422',
    colorBgElevated: '#1a1a30',
    colorBgLayout: '#0b0b14',
    colorText: '#f0f0f5',
    colorTextSecondary: '#b0b0c8',
    colorTextTertiary: '#8888a8',
    colorTextQuaternary: '#6666888',
    colorBorder: 'rgba(124, 58, 237, 0.25)',
    colorBorderSecondary: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    fontFamily: "'Inter', 'Noto Sans Georgian', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    colorSuccess: '#34d399',
    colorWarning: '#fbbf24',
    colorError: '#f87171',
    colorInfo: '#818cf8',
    colorLink: '#a78bfa',
    fontSize: 14,
    controlHeight: 40,
  },
  components: {
    Layout: {
      headerBg: 'rgba(11, 11, 20, 0.9)',
      bodyBg: '#0b0b14',
      siderBg: '#141422',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkItemSelectedBg: 'rgba(124, 58, 237, 0.2)',
      darkItemColor: '#b0b0c8',
      darkItemSelectedColor: '#e0e0ff',
      darkItemHoverColor: '#f0f0f5',
    },
    Card: {
      colorBgContainer: '#141422',
      colorText: '#f0f0f5',
      colorBorderSecondary: 'rgba(124, 58, 237, 0.18)',
    },
    Button: {
      primaryShadow: '0 2px 12px rgba(124, 58, 237, 0.35)',
      defaultBg: '#1e1e36',
      defaultColor: '#e0e0f0',
      defaultBorderColor: 'rgba(124, 58, 237, 0.3)',
    },
    Input: {
      colorBgContainer: '#1a1a30',
      colorText: '#f0f0f5',
      colorTextPlaceholder: '#6b6b88',
      activeBorderColor: '#7c3aed',
    },
    Select: {
      colorBgContainer: '#1a1a30',
      colorText: '#f0f0f5',
      optionActiveBg: 'rgba(124, 58, 237, 0.15)',
      optionSelectedBg: 'rgba(124, 58, 237, 0.25)',
      optionSelectedColor: '#f0f0f5',
      colorBgElevated: '#1a1a30',
    },
    Table: {
      headerBg: 'rgba(124, 58, 237, 0.12)',
      headerColor: '#d0d0e8',
      rowHoverBg: 'rgba(124, 58, 237, 0.07)',
      colorBgContainer: '#141422',
      colorText: '#e0e0f0',
      borderColor: 'rgba(255, 255, 255, 0.06)',
    },
    Tabs: {
      inkBarColor: '#7c3aed',
      itemActiveColor: '#c4b5fd',
      itemSelectedColor: '#c4b5fd',
      itemColor: '#8888a8',
      itemHoverColor: '#d0d0e8',
    },
    Modal: {
      contentBg: '#141422',
      headerBg: '#141422',
      titleColor: '#f0f0f5',
      colorText: '#e0e0f0',
    },
    Descriptions: {
      labelBg: 'rgba(124, 58, 237, 0.08)',
      colorText: '#e0e0f0',
      colorTextSecondary: '#b0b0c8',
    },
    Tag: {
      defaultColor: '#e0e0f0',
    },
    Upload: {
      colorFillAlter: 'rgba(124, 58, 237, 0.06)',
      colorText: '#b0b0c8',
    },
    Collapse: {
      headerBg: '#1a1a30',
      contentBg: '#141422',
      colorText: '#e0e0f0',
    },
    List: {
      colorText: '#e0e0f0',
    },
    Empty: {
      colorText: '#6b6b88',
      colorTextDescription: '#6b6b88',
    },
    Popconfirm: {
      colorText: '#e0e0f0',
    },
    Segmented: {
      itemSelectedBg: '#7c3aed',
      itemSelectedColor: '#ffffff',
      itemColor: '#b0b0c8',
      trackBg: '#1a1a30',
    },
    Form: {
      labelColor: '#c0c0d8',
    },
  },
};

export default theme;
