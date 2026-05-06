import React from 'react';
import { Layout, Menu, Avatar, Dropdown } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header } = Layout;

const AppHeader = () => {
  const navigate = useNavigate();

  const menu = (
    <Menu>
      <Menu.Item key="profile" icon={<UserOutlined />}>Profile</Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />}>Logout</Menu.Item>
    </Menu>
  );

  return (
    <Header style={{ background: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>🏠 EstateMind Admin</h2>
        <Dropdown menu={{ items: menu }} trigger={['click']}>
          <Avatar style={{ cursor: 'pointer', backgroundColor: '#1890ff' }} icon={<UserOutlined />} />
        </Dropdown>
      </div>
    </Header>
  );
};

export default AppHeader;
