import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Typography, Spin, Tag, Switch, Avatar, message, Statistic, Alert } from 'antd';
import { HddOutlined, PoweroffOutlined, CheckCircleOutlined } from '@ant-design/icons';
import containerService from "../../../services/containerService.js";
import WhisperModelInfo from '../../../components/speech-to-text/WhisperModelInfo.jsx';

const { Title, Text, Paragraph } = Typography;

// The exact name of the container you want to control
const CONTAINER_NAME = 'faster_whisper_stt_service_container';

function SystemStatus() {
    const [container, setContainer] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isToggling, setIsToggling] = useState(false);
    const [streamError, setStreamError] = useState(false);

    // Initial status fetch
    const fetchInitialStatus = async () => {
        setLoading(true);
        try {
            const response = await containerService.getContainerStatus(CONTAINER_NAME);
            setContainer(response.data);
            setStreamError(false);
        } catch (error) {
            const status = error.response?.status;
            if (status === 404 || status === 503) {
                setContainer({ service: CONTAINER_NAME, status: 'not_found' });
            } else {
                message.error("Failed to fetch initial container status.");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // 1. Fetch the status immediately when the component mounts.
        fetchInitialStatus();

        // 2. Set up the real-time event stream.
        const eventSource = containerService.getStatusStream(CONTAINER_NAME);

        // 3. Define what to do when a message is received from the server.
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("[SSE] Status update received:", data);
            setContainer(data); // Update the state with the new data
            setStreamError(false); // Clear any previous stream errors
            if (loading) setLoading(false); // If we were loading, we're not anymore
        };

        // 4. Define what to do if the connection fails.
        eventSource.onerror = () => {
            console.error("[SSE] Connection to status stream failed. Will not auto-reconnect.");
            setStreamError(true);
            eventSource.close(); // Stop the browser from trying to reconnect constantly
        };

        // 5. Clean up the connection when the component unmounts.
        return () => {
            console.log("[SSE] Closing status stream connection.");
            eventSource.close();
        };
    }, []); // The empty dependency array ensures this runs only once on mount.

    const handleToggle = async (checked) => {
        setIsToggling(true);
        const action = checked ? 'start' : 'stop';
        try {
            const result = await containerService.controlContainer(CONTAINER_NAME, action);
            message.success(result.data.message || `Container action '${action}' sent successfully.`);
            // No need to manually refetch; the SSE stream will send the update automatically.
        } catch (error) {
            message.error(error.response?.data?.message || `Failed to ${action} container.`);
        } finally {
            setIsToggling(false);
        }
    };

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '50px 0' }}><Spin size="large" tip="Connecting to service..." /></div>;
    }

    if (!container) {
        return <Card><Text>Could not load system status.</Text></Card>;
    }

    const isRunning = container.status === 'running';
    const isFound = container.status !== 'not_found';
    const tagColor = isRunning ? 'green' : (isFound ? 'default' : 'red');

    return (
        <Card bordered={false} style={{ boxShadow: 'none' }}>
            <Title level={4}>Service Management</Title>
            <Paragraph type="secondary">Control and monitor the status of the external STT service.</Paragraph>

            {streamError && !isToggling && (
                 <Alert
                    message="Real-time Updates Disconnected"
                    description="Could not maintain a connection to the status stream. The data below may be stale. Refresh the page to try again."
                    type="warning"
                    showIcon
                    style={{ marginBottom: 24 }}
                />
            )}

            <Card>
                <Row align="middle" gutter={[16, 16]}>
                    <Col>
                        <Avatar size={64} icon={<HddOutlined />} style={{ backgroundColor: isRunning ? '#52c41a' : '#bfbfbf' }} />
                    </Col>
                    <Col flex="auto">
                        <Title level={5} style={{ marginBottom: 0, wordBreak: 'break-all' }}>{container.container_name || CONTAINER_NAME}</Title>
                        <Text type="secondary">Speech-to-Text Service Container</Text>
                    </Col>
                    <Col>
                         <Switch
                            checkedChildren={<CheckCircleOutlined />}
                            unCheckedChildren={<PoweroffOutlined />}
                            checked={isRunning}
                            onChange={handleToggle}
                            loading={isToggling}
                            disabled={!isFound}
                        />
                    </Col>
                </Row>
                <Row gutter={16} style={{ marginTop: 24 }}>
                     <Col xs={24} sm={8}>
                        <Statistic
                            title="Status"
                            valueRender={() => (
                                <Tag color={tagColor} style={{ textTransform: 'uppercase', fontSize: 14 }}>
                                    {container.status.replace('_', ' ')}
                                </Tag>
                            )}
                        />
                    </Col>
                    <Col xs={24} sm={8}>
                         <Statistic title="Container ID" value={container.container_id || 'N/A'} />
                    </Col>
                     <Col xs={24} sm={8}>
                         <Statistic title="Image" value={container.image?.split('@')[0] || 'N/A'} />
                    </Col>
                </Row>
            </Card>
            <Card>
                <WhisperModelInfo />
            </Card>
        </Card>
    );
}

export default SystemStatus;