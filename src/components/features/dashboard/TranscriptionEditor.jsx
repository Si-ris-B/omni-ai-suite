import React, { useState, useCallback } from 'react';
import { Card, Button, message } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import RichTextEditor from "../../ckeditor/RichTextEditor.jsx";

function TranscriptionEditor({ fileId, initialContent, format, onSave, onCancel }) {
  const [content, setContent] = useState(initialContent);

  const handleContentChange = useCallback((newContent) => {
    setContent(newContent);
  }, []);

  const handleSave = useCallback(async () => {
    if (onSave) {
      try {
        await onSave(content);
      } catch (error) {
        console.error("Error saving content:", error);
        message.error("Failed to save content.");
      }
    }
  }, [content, onSave]);

  return (
    <Card
      title={`Editing ${format?.toUpperCase() || 'Content'} for File ID: ${fileId}`}
      size="small"
      style={{ height: '70vh', display: 'flex', flexDirection: 'column' }}
    >
      <div style={{ flexGrow: 1, overflow: 'hidden', marginBottom: 16 }}>
        <RichTextEditor
          initialContent={content}
          onContentChange={handleContentChange}
          placeholder={`Edit your ${format?.toUpperCase() || 'content'} here...`}
          width="100%"
          height="100%"
          showExportButtons={true}
          fileName={`file_${fileId}_${format}`}
        />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <Button icon={<CloseOutlined />} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
          Save Changes
        </Button>
      </div>
    </Card>
  );
}

export default TranscriptionEditor;