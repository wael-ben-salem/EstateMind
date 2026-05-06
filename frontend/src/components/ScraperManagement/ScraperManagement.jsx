import React, { useState } from 'react';
import { Row, Col, Button, Space } from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import ScraperCard from './ScraperCard';
import TriggerModal from './TriggerModal';
import './ScraperManagement.css';

const ScraperManagement = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);

  const scrapers = [
    {
      id: 1,
      name: 'Tayara',
      status: 'active',
      url: 'https://tayara.tn',
      lastRun: '2026-05-06 10:30 AM',
      propertiesScraped: 12543,
      icon: '🏠'
    },
    {
      id: 2,
      name: 'moubaweb.tn',
      status: 'coming-soon',
      url: 'https://moubaweb.tn',
      lastRun: null,
      propertiesScraped: 0,
      icon: '🔒'
    },
    {
      id: 3,
      name: 'technocasa',
      status: 'coming-soon',
      url: 'https://technocasa.tn',
      lastRun: null,
      propertiesScraped: 0,
      icon: '🔒'
    },
    {
      id: 4,
      name: 'Tunisie Annonce',
      status: 'coming-soon',
      url: 'https://tunisie-annonce.tn',
      lastRun: null,
      propertiesScraped: 0,
      icon: '🔒'
    },
  ];

  return (
    <div className="scraper-management">
      <div className="header-section">
        <h1>Scraper Management</h1>
        <Button 
          type="primary" 
          size="large"
          icon={<PlayCircleOutlined />}
          onClick={() => setIsModalVisible(true)}
        >
          Trigger ETL Pipeline
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {scrapers.map(scraper => (
          <Col xs={24} sm={12} lg={8} key={scraper.id}>
            <ScraperCard scraper={scraper} />
          </Col>
        ))}
      </Row>

      <TriggerModal 
        visible={isModalVisible}
        onClose={() => setIsModalVisible(false)}
      />
    </div>
  );
};

export default ScraperManagement;
