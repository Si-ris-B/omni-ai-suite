import React, { useState, useEffect, useRef } from "react";
import { Row, Col, Calendar, Typography, Card, Badge } from "antd";
import dayjs from "dayjs";
import styled from "styled-components";

// Import dayjs plugins for Ant Design Calendar
import weekday from 'dayjs/plugin/weekday';
import localeData from 'dayjs/plugin/localeData';
dayjs.extend(weekday);
dayjs.extend(localeData);

import { CKEditor } from '@ckeditor/ckeditor5-react';
import { ClassicEditor, Essentials, Paragraph, Bold, Italic } from 'ckeditor5';
import { FormatPainter } from 'ckeditor5-premium-features';
import 'ckeditor5/ckeditor5.css';
import 'ckeditor5-premium-features/ckeditor5-premium-features.css';
import RichTextEditor from "../components/ckeditor/RichTextEditor.jsx";
import CustomCalender from "./CustomCalender.jsx";

const { Title } = Typography;

// --- Styled Components ---
const JournalWrapper = styled.div`
    padding: 24px;
    height: 100vh;
    box-sizing: border-box;
    background: #1a1a1a;
    color: #e0e0e0;

    .ant-card {
        background: transparent;
        border: none;
        height: 100%;
    }
`;

const SidebarCard = styled(Card)`
    background-color: #3a3a3a !important;
    border-radius: 8px;
    
    .ant-card-body { 
        padding: 20px !important; 
        height: 100%; 
    }
    
    .ant-picker-calendar { 
        background: transparent; 
    }
    
    .ant-picker-calendar-header { 
        color: #e0e0e0; 
        
        .ant-btn { 
            color: #e0e0e0; 
            border-color: #4a4a4a;
            background: transparent;
            
            &:hover {
                color: #4caf50;
                border-color: #4caf50;
                background: rgba(76, 175, 80, 0.1);
            }
        }
        
        .ant-select-selector {
            background: #2d2d2d;
            border-color: #4a4a4a;
            color: #e0e0e0;
        }
        
        .ant-select-arrow {
            color: #e0e0e0;
        }
        
        .ant-select-dropdown {
            background: #2d2d2d;
            border: 1px solid #4a4a4a;
            
            .ant-select-item {
                color: #e0e0e0;
                
                &:hover {
                    background: #4f4f4f;
                }
                
                &-selected {
                    background: #4caf50;
                    color: #212121;
                }
            }
        }
    }
    
    .ant-picker-content th { 
        color: #9e9e9e; 
        font-weight: 400; 
    }
    
    .ant-picker-cell { 
        color: #e0e0e0; 
        
        &:hover .ant-picker-cell-inner { 
            background: #4f4f4f; 
        }
    }
    
    .ant-picker-cell-in-view.ant-picker-cell-today .ant-picker-cell-inner::before { 
        border-color: #4caf50; 
    }
    
    .ant-picker-cell-selected .ant-picker-cell-inner, 
    .ant-picker-cell-selected:hover .ant-picker-cell-inner { 
        background: #4caf50; 
        color: #212121; 
    }
    
    .events { 
        list-style: none; 
        margin: 0; 
        padding: 0; 
        max-height: 60px;
        overflow: hidden;
    }
    
    .events .ant-badge-status { 
        width: 100%; 
        overflow: hidden; 
        font-size: 11px; 
        white-space: nowrap; 
        text-overflow: ellipsis; 
        line-height: 1.2;
        margin-bottom: 1px;
    }
    
    .ant-badge-status-text { 
        color: #c8c8c8; 
        font-size: 10px; 
    }
`;

const MainContentCard = styled(Card)`
    background-color: #2d2d2d !important;
    border-radius: 8px;
    position: relative;
    z-index: 1;

    .ant-card-body { 
        display: flex; 
        flex-direction: column; 
        height: 100%; 
        padding: 24px;
    }
    
    .entry-title { 
        color: #e0e0e0 !important; 
        font-weight: 600; 
        padding-bottom: 10px; 
        border-bottom: 1px solid #4a4a4a; 
        margin-bottom: 20px !important; 
    }
    
    .editor-container {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        
        /* CKEditor Dark Theme Styling */
        .ck.ck-editor {
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid #4a4a4a;
            
            &:focus-within {
                border-color: #4caf50;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
            }
        }
        
        .ck.ck-toolbar {
            background: #3a3a3a;
            border-bottom: 1px solid #4a4a4a;
            border-top: none;
            border-left: none;
            border-right: none;
            border-radius: 0;
        }
        
        .ck.ck-button, 
        .ck.ck-dropdown__button {
            color: #e0e0e0;
            background: transparent;
            border: none;
            
            &:not(.ck-disabled):hover {
                background: #4f4f4f;
                color: #ffffff;
            }
            
            &.ck-on {
                background: #4caf50;
                color: #212121;
            }
        }
        
        .ck.ck-dropdown__panel {
            background: #3a3a3a;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
        }
        
        .ck.ck-list__item {
            color: #e0e0e0;
            
            &:hover {
                background: #4f4f4f;
            }
        }
        
        .ck.ck-editor__main > .ck-editor__editable {
            background-color: #212121;
            color: #e0e0e0;
            border: none;
            min-height: 400px;
            padding: 20px;
            
            &:focus {
                background-color: #212121;
                color: #e0e0e0;
                box-shadow: none;
            }
            
            /* Content styling within editor */
            h1, h2, h3, h4, h5, h6 {
                color: #4caf50;
            }
            
            blockquote {
                border-left: 4px solid #4caf50;
                background: rgba(76, 175, 80, 0.1);
                color: #d0d0d0;
            }
            
            a {
                color: #81c784;
                
                &:hover {
                    color: #4caf50;
                }
            }
            
            ul, ol {
                li {
                    color: #e0e0e0;
                }
            }
        }
        
        /* Hide CKEditor branding */
        .ck.ck-powered-by {
            display: none !important;
        }
        
        .ck.ck-reset_all {
            color: #e0e0e0;
        }
    }
    
    .editor-stats {
        margin-top: 12px;
        padding: 8px 12px;
        background: #1a1a1a;
        border-radius: 4px;
        font-size: 12px;
        color: #999;
        border: 1px solid #4a4a4a;
    }
`;

// CKEditor Configuration
const editorConfig = {
    plugins: [ Essentials, Paragraph, Bold, Italic, FormatPainter ],

    toolbar: [ 'undo', 'redo', '|', 'bold', 'italic', '|', 'formatPainter' ],

    initialData: '<p>Hello from CKEditor 5 in React!</p>',

    licenseKey: 'GPL',
};

function Editor() {
    const [selectedDate, setSelectedDate] = useState(dayjs());
    const [journalEntries, setJournalEntries] = useState({});
    const [editorInstance, setEditorInstance] = useState(null);
    const debounceTimeoutRef = useRef(null);

    const formatDateToKey = (date) => date.format("YYYY-MM-DD");

    // Load journal entries from localStorage on component mount
    useEffect(() => {
        const loadEntries = () => {
            const entries = {};
            const keys = Object.keys(localStorage);

            keys.forEach(key => {
                if (key.startsWith('journal-')) {
                    const dateKey = key.substring(8); // Remove 'journal-' prefix
                    const content = localStorage.getItem(key);
                    if (content && content.trim()) {
                        entries[dateKey] = content;
                    }
                }
            });

            setJournalEntries(entries);
        };

        loadEntries();
    }, []);

    // Load content when date changes
    useEffect(() => {
        if (editorInstance) {
            const dateKey = formatDateToKey(selectedDate);
            const savedEntry = journalEntries[dateKey] || "";
            editorInstance.setData(savedEntry);
        }
    }, [selectedDate, editorInstance, journalEntries]);

    // Cleanup timeout on unmount
    useEffect(() => {
        return () => {
            if (debounceTimeoutRef.current) {
                clearTimeout(debounceTimeoutRef.current);
            }
        };
    }, []);

    const saveEntry = (dateToSave, content) => {
        const dateKey = dateToSave.format("YYYY-MM-DD");
        const storageKey = `journal-${dateKey}`;
        const textContent = content.replace(/<[^>]*>/g, '').trim();
        const isEmpty = !textContent;

        if (!isEmpty) {
            localStorage.setItem(storageKey, content);
            setJournalEntries(prev => ({
                ...prev,
                [dateKey]: content
            }));
        } else {
            localStorage.removeItem(storageKey);
            setJournalEntries(prev => {
                const newEntries = { ...prev };
                delete newEntries[dateKey];
                return newEntries;
            });
        }
    };

    const handleEditorChange = (event, editor) => {
        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }

        debounceTimeoutRef.current = setTimeout(() => {
            const data = editor.getData();
            saveEntry(selectedDate, data);
        }, 1000); // Save after 1 second of inactivity
    };

    const handleDateSelect = (date) => {
        // Save current entry before switching dates
        if (editorInstance) {
            if (debounceTimeoutRef.current) {
                clearTimeout(debounceTimeoutRef.current);
            }
            const currentContent = editorInstance.getData();
            saveEntry(selectedDate, currentContent);
        }

        setSelectedDate(date);
    };

    const dateCellRender = (value) => {
        const dateKey = formatDateToKey(value);
        const entry = journalEntries[dateKey];

        if (!entry) return null;

        // Extract text content for preview
        const textContent = entry.replace(/<[^>]*>/g, '').trim();
        if (!textContent) return null;

        // Create a short preview
        const preview = textContent.length > 25 ?
            textContent.substring(0, 25) + '...' :
            textContent;

        return (
            <ul className="events">
                <li>
                    <Badge status="success" text={preview} />
                </li>
            </ul>
        );
    };

    const cellRender = (current, info) => {
        if (info.type === 'date') return dateCellRender(current);
        return info.originNode;
    };

    // Calculate stats for current entry
    const getCurrentEntryStats = () => {
        const dateKey = formatDateToKey(selectedDate);
        const entry = journalEntries[dateKey] || "";
        const textContent = entry.replace(/<[^>]*>/g, '');
        const wordCount = textContent.trim() ? textContent.trim().split(/\s+/).length : 0;
        const charCount = textContent.length;

        return { wordCount, charCount };
    };

    const stats = getCurrentEntryStats();

    return (
        <JournalWrapper>
            <Row gutter={[24, 24]} style={{ height: "100%" }}>
                {/*<Col xs={24} lg={8}>*/}
                {/*    <SidebarCard>*/}
                {/*        <Calendar*/}
                {/*            fullscreen={false}*/}
                {/*            onSelect={handleDateSelect}*/}
                {/*            value={selectedDate}*/}
                {/*            cellRender={cellRender}*/}
                {/*        />*/}
                {/*    </SidebarCard>*/}
                {/*</Col>*/}
                <Col xs={24} lg={16}>
                    <MainContentCard>
                        <Title level={4} className="entry-title">
                            Journal Entry for {selectedDate.format("MMMM D, YYYY")}
                        </Title>

                        <div className="editor-container">
                            <RichTextEditor />
                        </div>

                        <div className="editor-stats">
                            {stats.wordCount} words • {stats.charCount} characters
                            {Object.keys(journalEntries).length > 0 && (
                                <span style={{ marginLeft: '12px' }}>
                                    • {Object.keys(journalEntries).length} total entries
                                </span>
                            )}
                        </div>
                    </MainContentCard>
                        <CustomCalender />
                </Col>
            </Row>
        </JournalWrapper>
    );
}

export default Editor;
