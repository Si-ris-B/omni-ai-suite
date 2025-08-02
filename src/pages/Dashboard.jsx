import React from 'react';
import { Card, Tabs, Typography } from 'antd';
import { CloudUploadOutlined, HddOutlined } from '@ant-design/icons';
import MediaLibrary from "../components/features/dashboard/MediaLibrary.jsx";
import SystemStatus from "../components/features/dashboard/SystemStatus.jsx";

const { Title, Paragraph } = Typography;

function Dashboard() {
    return (
        <div className="layout-content">
            <Card>
                <Title level={2}>Dashboard</Title>
                <Paragraph>Manage your application's media library and system services from one place.</Paragraph>

                <Tabs defaultActiveKey="1" type="card">
                    <Tabs.TabPane
                        tab={
                            <span>
                                <CloudUploadOutlined />
                                Media Library
                            </span>
                        }
                        key="1"
                    >
                        <MediaLibrary />
                    </Tabs.TabPane>
                    <Tabs.TabPane
                        tab={
                            <span>
                                <HddOutlined />
                                Service Management
                            </span>
                        }
                        key="2"
                    >
                        <SystemStatus />
                    </Tabs.TabPane>
                </Tabs>
            </Card>
        </div>
    );
}

export default Dashboard;