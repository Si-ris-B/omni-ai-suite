// src/pages/Uploads.jsx
import React, { useState, useEffect } from 'react';
import {
    Row,
    Col,
    Card,
    Upload,
    message,
    Typography,
    Input,
    Button,
    Spin,
} from 'antd';
import { InboxOutlined, DeleteOutlined } from '@ant-design/icons';
import FilePreview from '../components/upload/FilePreview';
import uploadService from '../services/uploadService';

const { Dragger } = Upload;
const { Title, Paragraph } = Typography;

function Uploads() {
    const [fileList, setFileList] = useState([]);
    const [youtubeUrl, setYoutubeUrl] = useState('');
    const [loading, setLoading] = useState(true);

    // Fetch files on component mount
    useEffect(() => {
        const fetchFiles = async () => {
            try {
                const response = await uploadService.getFiles();
                setFileList(response.data);
            } catch (error) {
                message.error('Failed to fetch files.');
            } finally {
                setLoading(false);
            }
        };
        fetchFiles();
    }, []);

    const handleRemove = async (id) => {
        try {
            await uploadService.deleteFile(id);
            setFileList((prevList) => prevList.filter((file) => file.id !== id));
            message.success('File removed successfully.');
        } catch (error) {
            message.error('Failed to remove file.');
        }
    };

    const draggerProps = {
        name: 'file',
        multiple: true,
        customRequest: async ({ file, onSuccess, onError }) => {
            const formData = new FormData();
            formData.append('file', file); // Backend expects 'file' key
            try {
                const response = await uploadService.uploadFiles(formData);
                // The backend returns a list of created files, we take the first one
                const uploadedFile = response.data[0];
                setFileList(prevList => [uploadedFile, ...prevList]);
                onSuccess();
            } catch (error) {
                message.error(`${file.name} upload failed.`);
                onError(error);
            }
        },
        showUploadList: false,
    };

    const handleAddYoutubeUrl = async () => {
        if (!youtubeUrl) {
            message.error('Please enter a YouTube URL.');
            return;
        }
        try {
            const response = await uploadService.addYoutubeLink(youtubeUrl);
            setFileList(prevList => [response.data, ...prevList]);
            message.success('YouTube video added.');
            setYoutubeUrl('');
        } catch (error) {
            const errorMsg = error.response?.data?.error || 'Failed to add YouTube link.';
            message.error(errorMsg);
        }
    };

    return (
        <>
            <div className="tabled">
                <Row gutter={[24, 24]}>
                    <Col span={24}>
                        <Card bordered={false}>
                            <Title level={4}>Media Library</Title>
                            <Paragraph>Upload files or add YouTube links to your library.</Paragraph>
                            <Dragger {...draggerProps}><p className="ant-upload-drag-icon"><InboxOutlined /></p><p className="ant-upload-text">Click or drag files to this area to upload</p></Dragger>
                            <Input.Search
                                placeholder="Paste a YouTube URL here"
                                enterButton="Add Video"
                                size="large"
                                value={youtubeUrl}
                                onChange={(e) => setYoutubeUrl(e.target.value)}
                                onSearch={handleAddYoutubeUrl}
                                style={{ marginTop: 24 }}
                            />
                        </Card>
                    </Col>

                    <Col span={24}>
                        {loading ? (
                            <div style={{ textAlign: 'center', padding: '50px 0' }}><Spin size="large" /></div>
                        ) : (
                            <Row gutter={[16, 16]}>
                                {fileList.map((file) => (
                                    <Col xs={24} sm={12} md={8} lg={6} key={file.id}>
                                        <Card
                                            hoverable
                                            cover={<FilePreview file={file} />}
                                            actions={[<Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleRemove(file.id)}>Remove</Button>]}
                                        >
                                            <Card.Meta title={file.title} description={file.file_type} style={{textTransform: 'capitalize'}} />
                                        </Card>
                                    </Col>
                                ))}
                            </Row>
                        )}
                        { !loading && fileList.length === 0 && (
                            <Card><Paragraph style={{textAlign: 'center'}}>Your media library is empty. Upload some files to get started.</Paragraph></Card>
                        )}
                    </Col>
                </Row>
            </div>
        </>
    );
}

export default Uploads;
