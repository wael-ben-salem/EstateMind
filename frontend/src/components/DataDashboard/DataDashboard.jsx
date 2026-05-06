import React, { useContext, useEffect } from 'react';
import { Row, Col, Card, Statistic, Spin, Empty } from 'antd';
import { DatabaseOutlined, EnvironmentOutlined, HomeOutlined, DollarOutlined } from '@ant-design/icons';
import { DataContext } from '../../context/DataContext';
import LocationChart from './LocationChart';
import PropertyTypeChart from './PropertyTypeChart';
import PriceDistributionChart from './PriceDistributionChart';
import './DataDashboard.css';

const DataDashboard = () => {
  const { data, loading, refetch } = useContext(DataContext);

  useEffect(() => {
    refetch();
  }, []);

  if (loading) {
    return <Spin tip="Loading dashboard data..." size="large" style={{ marginTop: '50px' }} />;
  }

  if (!data) {
    return <Empty description="No data available" />;
  }

  return (
    <div className="data-dashboard">
      <h1>Data Analytics Dashboard</h1>
      
      <Row gutter={[16, 16]} style={{ marginBottom: '30px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Properties"
              value={data.totalProperties || 0}
              icon={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Unique Locations"
              value={data.uniqueLocations || 0}
              icon={<EnvironmentOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Property Types"
              value={data.propertyTypes || 0}
              icon={<HomeOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Price"
              value={data.avgPrice || 0}
              icon={<DollarOutlined />}
              prefix="TND"
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Properties by Location" loading={loading}>
            <LocationChart data={data.locationData} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Property Types Distribution" loading={loading}>
            <PropertyTypeChart data={data.propertyTypeData} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24}>
          <Card title="Price Distribution" loading={loading}>
            <PriceDistributionChart data={data.priceData} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DataDashboard;
