// src/components/MainLayout.jsx

import React, { useState } from 'react';
import { Layout } from 'antd';
import { MenuUnfoldOutlined, MenuFoldOutlined } from '@ant-design/icons';
import AppSider from './AppSider';
import { appConfig } from '../config/appConfig.jsx'; // Import our configuration

const { Header, Content } = Layout;

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppSider collapsed={collapsed} menuItems={appConfig} />
      <Layout className="site-layout">
        <Header className="site-layout-background" style={{ padding: 0, background: '#fff' }}>
          {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
            className: 'trigger',
            style: { padding: '0 24px', fontSize: '18px' },
            onClick: () => setCollapsed(!collapsed),
          })}
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: '#fff',
          }}
        >
          {/* Your page content (<Switch> with <Route>s) will render here */}
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;