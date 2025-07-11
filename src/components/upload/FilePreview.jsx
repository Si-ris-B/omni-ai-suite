import React from 'react';
import { FileTextOutlined } from '@ant-design/icons';
import styled from 'styled-components';
const BACKEND_URL = 'http://127.0.0.1:8000';

const PreviewWrapper = styled.div`
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
  overflow: hidden;

  img, video, audio {
    max-width: 100%;
    max-height: 100%;
    display: block;
  }

  .generic-file-preview {
    text-align: center;
    color: #8c8c8c;
    font-size: 1.2em;
  }

  .anticon-file-text {
    font-size: 3em;
    display: block;
    margin-bottom: 8px;
  }
  
  iframe {
    width: 100%;
    height: 100%;
    border: none;
  }
`;

const getYoutubeEmbedUrl = (url) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    const videoId = (match && match[2].length === 11) ? match[2] : null;
    return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
}

const FilePreview = ({ file }) => {
    // Handle YouTube links from backend
    if (file.file_type === 'YOUTUBE' && file.youtube_url) {
        const embedUrl = getYoutubeEmbedUrl(file.youtube_url);
        if (!embedUrl) return <PreviewWrapper>Invalid YouTube Link</PreviewWrapper>;

        return (
            <PreviewWrapper>
                <iframe
                    src={embedUrl}
                    title="YouTube video player"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                ></iframe>
            </PreviewWrapper>
        );
    }

    // Handle uploaded files from backend
    const fileType = file.file_type || '';
    const fileUrl = file.upload_file ? `${BACKEND_URL}${file.upload_file}` : file.previewUrl;

    if (!fileUrl) {
        return (
            <PreviewWrapper>
                <div className="generic-file-preview"><FileTextOutlined /><span>Processing...</span></div>
            </PreviewWrapper>
        );
    }

    if (fileType.startsWith('IMAGE')) {
        return <PreviewWrapper><img src={fileUrl} alt={file.title} /></PreviewWrapper>;
    }

    if (fileType.startsWith('VIDEO')) {
        return <PreviewWrapper><video controls src={fileUrl} /></PreviewWrapper>;
    }

    if (fileType.startsWith('AUDIO')) {
        return <PreviewWrapper><audio controls src={fileUrl} style={{ width: '90%' }} /></PreviewWrapper>;
    }

    // Fallback for other file types
    return (
        <PreviewWrapper>
            <div className="generic-file-preview">
                <FileTextOutlined />
                <span>{file.title}</span>
            </div>
        </PreviewWrapper>
    );
};

export default FilePreview;
