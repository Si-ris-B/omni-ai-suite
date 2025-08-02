// src/pages/Uploads.jsx
import React, { useState, useEffect } from 'react';
import {
    Upload, message, Row, Col, Card, Typography, Input, Spin, Button, List
} from 'antd';
import {
    InboxOutlined, DeleteOutlined, UploadOutlined, ClearOutlined
} from '@ant-design/icons';

// Make sure your import paths are correct for your project structure
import uploadService from '../services/uploadService';
import FilePreview from '../components/upload/FilePreview';

const { Dragger } = Upload;
const { Title, Paragraph } = Typography;

function Uploads() {
    const [fileList, setFileList] = useState([]);
    const [filesToUpload, setFilesToUpload] = useState([]);
    const [youtubeUrl, setYoutubeUrl] = useState('');
    const [loading, setLoading] = useState(true);
    const [isUploading, setIsUploading] = useState(false);

    useEffect(() => {
        const fetchFiles = async () => {
            setLoading(true);
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
        fileList: filesToUpload,
        beforeUpload: (file) => {
            // Add the file to our custom state queue
            setFilesToUpload(prev => [...prev, file]);
            // Return false to prevent antd from uploading automatically
            return false;
        },
        onRemove: (file) => {
            setFilesToUpload(prev => prev.filter(f => f.uid !== file.uid));
        }
    };

    const handleUpload = async () => {
        if (filesToUpload.length === 0) {
            message.error('No files selected for upload.');
            return;
        }

        setIsUploading(true);

        // Create an array of promises, one for each file upload
        const uploadPromises = filesToUpload.map(file => {
            const formData = new FormData();
            formData.append('file', file); // The file blob itself

            // =================================================================
            // THIS IS THE CRITICAL FIX
            // Get the file's last modified date as a standard ISO string.
            const lastModifiedISO = new Date(file.lastModified).toISOString();
            // Append it to the form data with the key the backend expects: 'modified_at'
            formData.append('modified_at', lastModifiedISO);
            // =================================================================

            // Your upload service should post this formData object to the backend
            return uploadService.uploadFiles(formData);
        });

        try {
            const results = await Promise.all(uploadPromises);
            const newlyUploadedFiles = results.flatMap(res => res.data);

            setFileList(prev => [...newlyUploadedFiles, ...prev]);
            setFilesToUpload([]); // Clear the upload queue
            message.success(`${newlyUploadedFiles.length} file(s) uploaded successfully!`);
        } catch (error) {
            console.error("Upload failed:", error.response?.data || error.message);
            message.error('An error occurred during upload. Check the console for details.');
        } finally {
            setIsUploading(false);
        }
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
                          <Dragger {...draggerProps}>
                              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                              <p className="ant-upload-text">Click or drag files to add to the upload queue</p>
                          </Dragger>

                          {filesToUpload.length > 0 && (
                            <Card size="small" style={{ marginTop: 16 }}>
                                <List
                                  header={<div>{filesToUpload.length} file(s) ready to upload</div>}
                                  dataSource={filesToUpload}
                                  renderItem={item => (<List.Item>{item.name}</List.Item>)}
                                />
                                <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                                    <Button
                                      icon={<ClearOutlined />}
                                      onClick={() => setFilesToUpload([])}
                                      disabled={isUploading}
                                    >
                                        Clear Queue
                                    </Button>
                                    <Button
                                      type="primary"
                                      icon={<UploadOutlined />}
                                      onClick={handleUpload}
                                      loading={isUploading}
                                    >
                                        {isUploading ? 'Uploading...' : 'Upload Now'}
                                    </Button>
                                </div>
                            </Card>
                          )}

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
                      <Title level={5} style={{ marginTop: 16 }}>Library Content</Title>
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
                                      <Card.Meta
                                        title={<span title={file.title}>{file.title}</span>}
                                        description={file.file_type.toLowerCase()}
                                        style={{textTransform: 'capitalize'}}
                                      />
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