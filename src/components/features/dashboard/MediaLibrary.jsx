import React, { useState, useEffect } from 'react';
import {
  Upload, message, Row, Col, Card, Typography, Input, Spin, Button, List,
  Dropdown, Alert, Modal, Select, Form, Space, Divider
} from 'antd';
import {
  InboxOutlined, DeleteOutlined, UploadOutlined, ClearOutlined,
  MoreOutlined, AudioOutlined, TranslationOutlined, PlayCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import TranscriptionEditor from './TranscriptionEditor';
import uploadService from "../../../services/uploadService.js";
import FilePreview from '../../../components/upload/FilePreview.jsx';

const { Dragger } = Upload;
const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

function MediaLibrary() {
  const [fileList, setFileList] = useState([]);
  const [filesToUpload, setFilesToUpload] = useState([]);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [processingModalVisible, setProcessingModalVisible] = useState(false);
  const [selectedFileForProcessing, setSelectedFileForProcessing] = useState(null);
  const [processingForm] = Form.useForm();
  const [editorModalVisible, setEditorModalVisible] = useState(false);
  const [editingFile, setEditingFile] = useState(null); // Changed from editingFileId
  const [editingContent, setEditingContent] = useState('');
  const [processingStatus, setProcessingStatus] = useState({});

  useEffect(() => {
    const fetchFiles = async () => {
      setLoading(true);
      try {
        const response = await uploadService.getFiles();
        setFileList(response.data);
      } catch (error) {
        console.error('Failed to fetch files:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchFiles();
  }, []);

  const handleRemove = async (id) => {
    if (processingStatus[id]?.status === 'processing') {
      message.info('Cannot remove file while it is being processed.');
      return;
    }
    try {
      await uploadService.deleteFile(id);
      setFileList((prevList) => prevList.filter((file) => file.id !== id));
      message.success('File removed successfully.');
    } catch (error) {
      console.error('Failed to remove file:', error);
    }
  };

  const showProcessingModal = (file) => {
    if (processingStatus[file.id]?.status === 'processing') {
      message.info('File is already being processed.');
      return;
    }
    setSelectedFileForProcessing(file);
    setProcessingModalVisible(true);
    processingForm.resetFields();
  };

  const handleProcessingModalOk = async () => {
    try {
      const values = await processingForm.validateFields();
      const { action, format } = values;
      const file = selectedFileForProcessing;

      setProcessingModalVisible(false);

      setProcessingStatus(prev => ({ ...prev, [file.id]: { status: 'processing', action, format } }));

      let response;
      if (action === 'transcribe') {
        // This is now a simple, blocking call that waits for the full result.
        response = await uploadService.transcribeFile(file.id, format);
      } else {
        // This will correctly show an error message.
        response = await uploadService.translateFile(file.id, format);
      }

      if (response && response.data) {
        setEditingFile({ ...file, action, format }); // Store the whole file object and action/format
        setEditingContent(response.data.content || '');
        setEditorModalVisible(true);
        setProcessingStatus(prev => ({ ...prev, [file.id]: { status: 'completed', action, format } }));
      }
    } catch (error) {
      const fileId = selectedFileForProcessing?.id;
      const errorMessage = error.response?.data?.error || 'Processing failed.';
      if (fileId) {
        setProcessingStatus(prev => ({ ...prev, [fileId]: { status: 'error', error: errorMessage } }));
      }
    }
  };

  const handleProcessingModalCancel = () => setProcessingModalVisible(false);
  const handleEditorSave = async () => message.success('Content saved successfully!');
  const handleEditorCancel = () => setEditorModalVisible(false);

  const draggerProps = {
    name: 'file',
    multiple: true,
    fileList: filesToUpload,
    beforeUpload: (file) => {
      setFilesToUpload(prev => [...prev, file]);
      return false;
    },
    onRemove: (file) => {
      setFilesToUpload(prev => prev.filter(f => f.uid !== file.uid));
    }
  };

  const handleUpload = async () => {
    if (filesToUpload.length === 0) { message.error('No files selected for upload.'); return; }
    setIsUploading(true);
    const uploadPromises = filesToUpload.map(file => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('file_type', file.type.split('/')[0] || 'document');
      formData.append('last_modified_timestamp', file.lastModified);
      return uploadService.uploadFile(formData);
    });
    try {
      const results = await Promise.all(uploadPromises);
      const newlyUploadedFiles = results.map(res => res.data);
      setFileList(prev => [...newlyUploadedFiles, ...prev]);
      setFilesToUpload([]);
      message.success(`${newlyUploadedFiles.length} file(s) uploaded successfully!`);
    } catch (error) {
      console.error('An error occurred during upload:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleAddYoutubeUrl = async () => {
    if (!youtubeUrl) return message.error('Please enter a YouTube URL.');
    try {
      await uploadService.addYoutubeLink(youtubeUrl);
    } catch (error) {
      console.error('Failed to add YouTube link:', error);
    }
  };

  const getMenuItems = (file) => {
    if (file.file_type === 'audio') {
      return [{ key: 'process', label: 'Process File', icon: <PlayCircleOutlined />, onClick: () => showProcessingModal(file) }];
    }
    return [];
  };

  return (
    <>
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card bordered={false} style={{ boxShadow: 'none' }}>
            <Title level={4}>Media Uploader</Title>
            <Paragraph>Upload files or add YouTube links to your library.</Paragraph>
            <Dragger {...draggerProps}><p className="ant-upload-drag-icon"><InboxOutlined /></p><p className="ant-upload-text">Click or drag files to add to the upload queue</p></Dragger>
            {filesToUpload.length > 0 && (
              <Card size="small" style={{ marginTop: 16 }}>
                <List header={<div>{filesToUpload.length} file(s) ready to upload</div>} dataSource={filesToUpload} renderItem={item => (<List.Item>{item.name}</List.Item>)} />
                <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  <Button icon={<ClearOutlined />} onClick={() => setFilesToUpload([])} disabled={isUploading}>Clear Queue</Button>
                  <Button type="primary" icon={<UploadOutlined />} onClick={handleUpload} loading={isUploading}>{isUploading ? 'Uploading...' : 'Upload Now'}</Button>
                </div>
              </Card>
            )}
            <Divider style={{ margin: '24px 0' }} />
            <Input.Search placeholder="Paste a YouTube URL here (Not Implemented)" enterButton="Add Video" size="large" value={youtubeUrl} onChange={(e) => setYoutubeUrl(e.target.value)} onSearch={handleAddYoutubeUrl} />
          </Card>
        </Col>
        <Col span={24}>
          <Title level={5} style={{ marginTop: 16 }}>Library Content</Title>
          {loading ? <div style={{ textAlign: 'center', padding: '50px 0' }}><Spin size="large" /></div> : (
            <Row gutter={[16, 24]}>
              {fileList.map((file) => {
                const currentProcessingStatus = processingStatus[file.id]?.status;
                const isProcessing = currentProcessingStatus === 'processing';
                const hasProcessingError = currentProcessingStatus === 'error';
                return (
                  <Col xs={24} sm={12} md={8} lg={6} key={file.id}>
                    <Card hoverable cover={<FilePreview file={file} />} actions={[<Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleRemove(file.id)} disabled={isProcessing}>Remove</Button>, getMenuItems(file).length > 0 && <Dropdown menu={{ items: getMenuItems(file) }} placement="topRight" arrow trigger={['click']}><Button type="text" icon={<MoreOutlined />} disabled={isProcessing} /></Dropdown>]}>
                      <Card.Meta title={<span title={file.original_filename}>{file.original_filename}</span>} description={<><span style={{ textTransform: 'capitalize' }}>{file.file_type}</span>{isProcessing && <Spin size="small" style={{ marginLeft: 8 }} />}</>} />
                    </Card>
                    {isProcessing && <div style={{ padding: '10px', textAlign: 'center', marginTop: '8px' }}><Spin size="small" /><Text type="secondary" style={{ display: 'block', marginTop: '5px', fontSize: '12px' }}>{processingStatus[file.id]?.action === 'transcribe' ? 'Transcribing...' : 'Translating...'}</Text></div>}
                    {hasProcessingError && <Alert message="Processing Error" description={processingStatus[file.id]?.error} type="error" showIcon style={{ marginTop: '8px' }} closable onClose={() => setProcessingStatus(prev => { const newStatus = { ...prev }; delete newStatus[file.id]; return newStatus; })} />}
                  </Col>
                );
              })}
            </Row>
          )}
          {!loading && fileList.length === 0 && <Card><Paragraph style={{ textAlign: 'center' }}>Your media library is empty.</Paragraph></Card>}
        </Col>
      </Row>

      <Modal title="Process Audio File" open={processingModalVisible} onOk={handleProcessingModalOk} onCancel={handleProcessingModalCancel} okText="Start Processing" destroyOnClose>
        {selectedFileForProcessing && <div style={{ marginBottom: 16 }}><Text strong>File:</Text> {selectedFileForProcessing.original_filename}</div>}
        <Form form={processingForm} layout="vertical" initialValues={{ action: 'transcribe', format: 'srt' }}>
          <Form.Item name="action" label="Action" rules={[{ required: true }]}><Select><Option value="transcribe"><Space><AudioOutlined /> Transcribe</Space></Option><Option value="translate" disabled><Space><TranslationOutlined /> Translate (Not Implemented)</Space></Option></Select></Form.Item>
          <Form.Item name="format" label="Output Format" rules={[{ required: true }]}><Select><Option value="txt"><Space><FileTextOutlined /> Plain Text (.txt)</Space></Option><Option value="srt"><Space><FileTextOutlined /> SubRip Subtitle (.srt)</Space></Option></Select></Form.Item>
        </Form>
      </Modal>

      <Modal
        title={<span>Edit {editingFile?.action === 'transcribe' ? 'Transcription' : 'Translation'} ({editingFile?.format?.toUpperCase()}) for: {editingFile?.original_filename}</span>}
        open={editorModalVisible}
        onCancel={handleEditorCancel}
        width="80%"
        footer={null}
        destroyOnClose
      >
        {editingFile && <TranscriptionEditor fileId={editingFile.id} initialContent={editingContent} format={editingFile.format} action={editingFile.action} onSave={handleEditorSave} onCancel={handleEditorCancel} />}
      </Modal>
    </>
  );
}

export default MediaLibrary;