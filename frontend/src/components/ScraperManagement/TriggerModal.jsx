import React, { useContext, useEffect, useState } from 'react';
import { Modal, Steps, Button, Spin, Alert, Statistic, Row, Col, Empty } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { PipelineContext } from '../../context/PipelineContext';
import { airflowService } from '../../services/airflowService';
import './TriggerModal.css';

const TriggerModal = ({ visible, onClose }) => {
  const { isRunning, triggerPipeline, dagRunId } = useContext(PipelineContext);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dagRunId && isRunning) {
      fetchTaskProgress();
      const interval = setInterval(fetchTaskProgress, 3000);
      return () => clearInterval(interval);
    }
  }, [dagRunId, isRunning]);

  const fetchTaskProgress = async () => {
    try {
      const tasks = await airflowService.getTaskInstances(dagRunId);
      const formattedSteps = tasks.task_instances.map(task => ({
        id: task.task_id,
        name: task.task_id.replace(/_/g, ' ').toUpperCase(),
        status: task.state,
        startDate: task.start_date,
        endDate: task.end_date,
        duration: task.duration
      }));
      setSteps(formattedSteps);
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const getStepStatus = (status) => {
    switch(status) {
      case 'success': return 'finish';
      case 'failed': return 'error';
      case 'running': return 'process';
      default: return 'wait';
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'success': return '#52c41a';
      case 'failed': return '#f5222d';
      case 'running': return '#1890ff';
      default: return '#d9d9d9';
    }
  };

  const handleTrigger = async () => {
    setLoading(true);
    try {
      console.log('[MODAL] Trigger button clicked');
      await triggerPipeline();
      console.log('[MODAL] Pipeline triggered successfully');
    } catch (error) {
      console.error('[MODAL] Error:', error.message);
      alert(`Failed to start pipeline:\n\n${error.message}\n\nCheck your browser console for more details.`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!isRunning) {
      onClose();
    }
  };

  // Get current step index (first non-finished task)
  const currentStep = steps.findIndex(step => 
    step.status !== 'success' && step.status !== 'failed'
  );
  const actualCurrentStep = currentStep === -1 ? steps.length - 1 : currentStep;

  // Transform steps for the Steps component
  const stepsConfig = steps.map((step, index) => ({
    title: `Step ${index + 1}`,
    description: step.name,
    status: getStepStatus(step.status),
    icon: step.status === 'running' ? <LoadingOutlined /> : undefined,
    subDescription: step.duration ? `Duration: ${Math.round(step.duration)}s` : ''
  }));

  return (
    <Modal
      title="ETL Pipeline Monitor - Step by Step"
      open={visible}
      onCancel={handleClose}
      width={800}
      footer={[
        <Button key="close" onClick={handleClose} disabled={isRunning}>
          {isRunning ? 'Monitoring...' : 'Close'}
        </Button>,
        !isRunning && (
          <Button key="trigger" type="primary" loading={loading} onClick={handleTrigger}>
            Start Pipeline
          </Button>
        )
      ]}
    >
      {isRunning && (
        <Alert 
          message="Pipeline is running..."
          type="info"
          showIcon
          style={{ marginBottom: '20px' }}
        />
      )}

      {steps.length > 0 ? (
        <div style={{ marginTop: '20px' }}>
          <Steps
            current={actualCurrentStep}
            status={steps[actualCurrentStep]?.status === 'failed' ? 'error' : 'process'}
            items={stepsConfig}
            progressDot
            direction="vertical"
            style={{ marginBottom: '30px' }}
          />
          
          {/* Detailed step info */}
          {actualCurrentStep < steps.length && (
            <div style={{ 
              marginTop: '20px',
              padding: '15px',
              backgroundColor: '#fafafa',
              borderRadius: '4px',
              borderLeft: `4px solid ${getStatusColor(steps[actualCurrentStep].status)}`
            }}>
              <h4 style={{ marginTop: 0 }}>Current Step Details</h4>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="Step"
                    value={actualCurrentStep + 1}
                    suffix={`of ${steps.length}`}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Status"
                    value={steps[actualCurrentStep].status.toUpperCase()}
                    valueStyle={{ color: getStatusColor(steps[actualCurrentStep].status) }}
                  />
                </Col>
                {steps[actualCurrentStep].startDate && (
                  <Col span={8}>
                    <Statistic
                      title="Started At"
                      value={new Date(steps[actualCurrentStep].startDate).toLocaleTimeString()}
                    />
                  </Col>
                )}
              </Row>
            </div>
          )}
        </div>
      ) : isRunning ? (
        <Spin tip="Initializing pipeline..." size="large" />
      ) : (
        <Empty
          description="No pipeline runs yet"
          style={{ marginTop: '30px', marginBottom: '30px' }}
        />
      )}
    </Modal>
  );
};

export default TriggerModal;
