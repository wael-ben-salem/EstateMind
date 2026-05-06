import React from 'react';
import { Layout, Menu } from 'antd';
import { DatabaseOutlined, BarChartOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider } = Layout;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Sider width={250} theme="dark">
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        onClick={({ key }) => navigate(key)}
        items={[
          {
            key: '/admin',
            icon: <DatabaseOutlined />,
            label: 'Scraper Management'
          },
          {
            key: '/admin/dashboard',
            icon: <BarChartOutlined />,
            label: 'Data Analytics'
          }
        ]}
      />
    </Sider>
  );
};

export default Sidebar;
