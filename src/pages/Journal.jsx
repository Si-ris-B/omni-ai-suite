import React, { useState, useEffect } from 'react';
import { Calendar, Card, Button, Typography, Row, Col, List, Modal, message, Input } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, BookOutlined, CalendarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import RichTextEditor from "../components/ckeditor/RichTextEditor.jsx";

const { Title, Text } = Typography;

const Journal = () => {
  const [entries, setEntries] = useState([]);
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [isEditorVisible, setIsEditorVisible] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [editorTitle, setEditorTitle] = useState('');

  useEffect(() => {
    // Load entries from localStorage on mount
    const loadedEntries = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key.startsWith('journal-')) {
        loadedEntries.push(JSON.parse(localStorage.getItem(key)));
      }
    }
    setEntries(loadedEntries);
  }, []);

  const entriesForSelectedDate = entries.filter(
    entry => dayjs(entry.date).isSame(selectedDate, 'day')
  );

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    if (!selectedEntry || !dayjs(selectedEntry.date).isSame(date, 'day')) {
      setIsEditorVisible(false);
      setSelectedEntry(null);
    }
  };

  const handleCreateEntry = () => {
    setSelectedEntry(null);
    setEditorTitle('');
    setEditorContent('<p>Write your journal entry here...</p>');
    setIsEditorVisible(true);
  };

  const handleEditEntry = (entry) => {
    setSelectedEntry(entry);
    setEditorTitle(entry.title);
    setEditorContent(entry.content);
    setIsEditorVisible(true);
  };

  const handleDeleteEntry = (entryId) => {
    Modal.confirm({
      title: 'Confirm Delete',
      content: 'Are you sure you want to delete this journal entry?',
      okText: 'Delete',
      okType: 'danger',
      onOk() {
        const updatedEntries = entries.filter(e => e.id !== entryId);
        setEntries(updatedEntries);
        localStorage.removeItem(`journal-${entryId}`);
        message.success('Entry deleted');
        if (selectedEntry?.id === entryId) {
          setIsEditorVisible(false);
          setSelectedEntry(null);
        }
      },
    });
  };

  const handleEditorSave = () => {
    if (!editorTitle.trim()) {
      message.error('Please enter a title for your entry.');
      return;
    }
    const formattedDate = selectedDate.format('YYYY-MM-DD');
    let entryToSave;

    if (selectedEntry) {
      entryToSave = { ...selectedEntry, title: editorTitle, content: editorContent };
      const updatedEntries = entries.map(e => (e.id === selectedEntry.id ? entryToSave : e));
      setEntries(updatedEntries);
      message.success('Entry updated!');
    } else {
      entryToSave = { id: Date.now().toString(), date: formattedDate, title: editorTitle, content: editorContent };
      setEntries(prev => [...prev, entryToSave]);
      message.success('New entry created!');
    }
    localStorage.setItem(`journal-${entryToSave.id}`, JSON.stringify(entryToSave));
    setIsEditorVisible(false);
    setSelectedEntry(null);
  };

  const handleEditorCancel = () => {
    setIsEditorVisible(false);
    setSelectedEntry(null);
  };

  const dateCellRender = (currentDate) => {
    const dateString = currentDate.format('YYYY-MM-DD');
    const dayEntries = entries.filter(entry => entry.date === dateString);
    if (dayEntries.length > 0) {
      return (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, maxHeight: 40, overflowY: 'auto' }}>
          {dayEntries.map((entry) => (
            <li key={entry.id} style={{ fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <span style={{ display: 'inline-block', width: 5, height: 5, borderRadius: '50%', backgroundColor: '#1890ff', marginRight: 4 }}></span>
              {entry.title}
            </li>
          ))}
        </ul>
      );
    }
    return null;
  };

  return (
    <Row gutter={[24, 24]}>
      <Col xs={24} lg={10} xl={8}>
        <Card title={<><CalendarOutlined /> Calendar</>}>
          <Calendar value={selectedDate} onSelect={handleDateSelect} dateCellRender={dateCellRender} fullscreen={false} />
        </Card>
      </Col>
      <Col xs={24} lg={14} xl={16}>
        <Card title={<><BookOutlined /> Journal Entries for {selectedDate.format("MMMM D, YYYY")}</>}
              extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreateEntry} disabled={isEditorVisible}>New Entry</Button>}>
          {!isEditorVisible ? (
            entriesForSelectedDate.length > 0 ? (
              <List itemLayout="vertical" dataSource={entriesForSelectedDate} renderItem={entry => (
                <List.Item
                  actions={[
                    <Button type="text" icon={<EditOutlined />} onClick={() => handleEditEntry(entry)}>Edit</Button>,
                    <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleDeleteEntry(entry.id)}>Delete</Button>,
                  ]}>
                  <List.Item.Meta title={entry.title} description={`Created on ${dayjs(entry.date).format('lll')}`} />
                  <div dangerouslySetInnerHTML={{ __html: entry.content }} style={{ maxHeight: 100, overflow: 'hidden' }} />
                </List.Item>
              )} />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Typography.Title level={4}>No Entries for this date.</Typography.Title>
                <Button type="primary" onClick={handleCreateEntry}>Create One</Button>
              </div>
            )
          ) : (
            <div>
              <Input placeholder="Entry Title" value={editorTitle} onChange={e => setEditorTitle(e.target.value)} style={{ marginBottom: 16 }} />
              <RichTextEditor
                initialContent={editorContent}
                onContentChange={(data) => setEditorContent(data)}
                height="400px"
                width="100%"
                showExportButtons={false}
              />
              <div style={{ marginTop: 16, textAlign: 'right' }}>
                <Button onClick={handleEditorCancel} style={{ marginRight: 8 }}>Cancel</Button>
                <Button type="primary" onClick={handleEditorSave}>{selectedEntry ? 'Update' : 'Save'}</Button>
              </div>
            </div>
          )}
        </Card>
      </Col>
    </Row>
  );
};

export default Journal;