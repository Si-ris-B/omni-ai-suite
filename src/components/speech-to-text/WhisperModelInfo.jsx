import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Switch, Tag, Typography, Space } from 'antd';
import {
  DatabaseOutlined,
  ApiOutlined,
  ClusterOutlined,
  CalculatorOutlined,
  DeploymentUnitOutlined,
  TeamOutlined,
  PoweroffOutlined,
  CheckCircleOutlined,
  StopOutlined,
  SettingOutlined, // For the main card icon
} from '@ant-design/icons';

const { Title, Text } = Typography;

const WhisperModelInfo = () => {
  const [modelInfo, setModelInfo] = useState(null);
  const [isModelLoaded, setIsModelLoaded] = useState(false);

  // Mock data initialization
  useEffect(() => {
    const mockData = {
      model_size_or_path: "distil-large-v3", // Slightly longer name to test wrapping
      device: "auto",
      device_index: [0, 1, 2], // Example of multiple GPUs
      compute_type: "float16", // Example compute type
      cpu_threads: 12,
      num_workers: 6,
    };
    setModelInfo(mockData);
  }, []);

  const handleToggleLoad = (checked) => {
    setIsModelLoaded(checked);
    if (checked) {
      console.log("Loading model...");
      // Integrate your model loading logic here
    } else {
      console.log("Unloading model...");
      // Integrate your model unloading logic here
    }
  };

  // Loading state for data
  if (!modelInfo) {
    return (
      <Card size="small" style={{ width: '100%', margin: '16px 0' }} loading>
        <div style={{ padding: '24px 0', textAlign: 'center' }}>Loading model information...</div>
      </Card>
    );
  }

  return (
    <Card
      size="small" // Smaller overall padding for the card
      title={
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap', // Allow items to wrap on small screens
            gap: '12px', // Consistent spacing between title and controls
            width: '100%',
          }}
        >
          <Title level={5} style={{ margin: 0, color: '#1890ff', display: 'flex', alignItems: 'center' }}>
            <SettingOutlined style={{ marginRight: 10 }} />
            Whisper Model Configuration
          </Title>
          <Space wrap> {/* Space also wraps if needed */}
            <Tag
              icon={isModelLoaded ? <CheckCircleOutlined /> : <StopOutlined />}
              color={isModelLoaded ? 'success' : 'error'}
              style={{ fontWeight: 'bold', padding: '0 8px' }}
            >
              {isModelLoaded ? 'Loaded' : 'Unloaded'}
            </Tag>
            <Switch
              checked={isModelLoaded}
              onChange={handleToggleLoad}
              checkedChildren={<PoweroffOutlined />}
              unCheckedChildren={<PoweroffOutlined />}
              style={{
                backgroundColor: isModelLoaded ? '#52c41a' : '#ff4d4f',
              }}
            />
          </Space>
        </div>
      }
      style={{
        width: '100%', // Key change: Make card width 100% of its container
        margin: '16px 0', // Vertical margin, no horizontal auto margin
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        borderRadius: 6,
      }}
    >
      {/* Descriptions with responsive columns */}
      <Descriptions
        bordered
        size="small" // Smaller padding for description items
        column={{
          xs: 1,  // 1 column on extra small screens
          sm: 1,  // 1 column on small screens
          md: 2,  // 2 columns on medium screens
          lg: 2,  // 2 columns on large screens
          xl: 2,  // 2 columns on extra large screens
          xxl: 2, // 2 columns on XXL screens
        }}
        // Optional: Add row spacing if needed
        // style={{ marginTop: 8 }}
      >
        <Descriptions.Item
          label={
            <span>
              <DatabaseOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              Model
            </span>
          }
        >
          <Text strong copyable>{modelInfo.model_size_or_path}</Text> {/* Make model name copyable */}
        </Descriptions.Item>

        <Descriptions.Item
          label={
            <span>
              <ApiOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              Device
            </span>
          }
        >
          <Tag color="green">{modelInfo.device}</Tag>
        </Descriptions.Item>

        <Descriptions.Item
          label={
            <span>
              <ClusterOutlined style={{ marginRight: 8, color: '#722ed1' }} />
              GPU IDs
            </span>
          }
        >
          <Tag color="purple">
            {Array.isArray(modelInfo.device_index)
              ? `[${modelInfo.device_index.join(', ')}]`
              : modelInfo.device_index}
          </Tag>
        </Descriptions.Item>

        <Descriptions.Item
          label={
            <span>
              <CalculatorOutlined style={{ marginRight: 8, color: '#13c2c2' }} />
              Precision
            </span>
          }
        >
          <Tag color="cyan">{modelInfo.compute_type}</Tag>
        </Descriptions.Item>

        <Descriptions.Item
          label={
            <span>
              <DeploymentUnitOutlined style={{ marginRight: 8, color: '#fa8c16' }} />
              CPU Threads
            </span>
          }
        >
          <Tag color="orange">{modelInfo.cpu_threads}</Tag>
        </Descriptions.Item>

        <Descriptions.Item
          label={
            <span>
              <TeamOutlined style={{ marginRight: 8, color: '#eb2f96' }} />
              Workers
            </span>
          }
        >
          <Tag color="magenta">{modelInfo.num_workers}</Tag>
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default WhisperModelInfo;