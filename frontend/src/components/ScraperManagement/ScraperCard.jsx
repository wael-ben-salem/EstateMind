import React from 'react';
import { Card, Tag, Statistic, Row, Col, Empty } from 'antd';
import { ClockCircleOutlined, DatabaseOutlined } from '@ant-design/icons';
import './ScraperManagement.css';

const ScraperCard = ({ scraper }) => {
  const isActive = scraper.status === 'active';
  
  return (
    <Card 
      className={`scraper-card ${scraper.status}`}
      hoverable={isActive}
    >
      <div className="card-header">
        <span className="icon">{scraper.icon}</span>
        <div className="info">
          <h3>{scraper.name}</h3>
          <a href={scraper.url} target="_blank" rel="noreferrer">
            {scraper.url}
          </a>
        </div>
      </div>

      {isActive ? (
        <>
          <hr />
          <Row gutter={16}>
            <Col xs={12}>
              <Statistic
                title="Properties Scraped"
                value={scraper.propertiesScraped}
                icon={<DatabaseOutlined />}
              />
            </Col>
            <Col xs={12}>
              <Statistic
                title="Last Run"
                value={scraper.lastRun}
                valueStyle={{ fontSize: '12px' }}
                icon={<ClockCircleOutlined />}
              />
            </Col>
          </Row>
          <Tag color="green" style={{ marginTop: '10px' }}>Active</Tag>
        </>
      ) : (
        <>
          <Empty 
            description="Coming Soon"
            style={{ marginTop: '20px' }}
          />
          <Tag color="default" style={{ marginTop: '10px' }}>
            Locked
          </Tag>
        </>
      )}
    </Card>
  );
};

export default ScraperCard;
