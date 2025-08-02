import React, { useState, useRef } from 'react';
import WavesurferPlayer from '@wavesurfer/react';
import { Button } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, FileOutlined } from '@ant-design/icons';
import styled from 'styled-components';

const PreviewWrapper = styled.div`
  height: 200px;
  width: 100%;
  background-color: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  img, video, iframe {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

const AudioWrapper = styled.div`
  width: 100%;
  padding: 10px;
`;

const GenericFileWrapper = styled.div`
  font-size: 64px;
  color: #a0a0a0;
`;

const getYouTubeEmbedUrl = (url) => {
    if (!url) return '';
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11)
      ? `https://www.youtube.com/embed/${match[2]}`
      : url;
};

const FilePreview = ({ file }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const wavesurferRef = useRef(null);

    const onReady = (ws) => {
        wavesurferRef.current = ws;
    };

    const onPlayPause = () => {
        wavesurferRef.current && wavesurferRef.current.playPause();
    };

    switch (file.file_type?.toLowerCase()) {
        case 'image':
            return (
              <PreviewWrapper>
                  <img src={file.file} alt={file.original_filename} />
              </PreviewWrapper>
            );

        case 'video':
            return (
              <PreviewWrapper>
                  <video src={file.file} controls />
              </PreviewWrapper>
            );

        case 'audio':
            return (
              <PreviewWrapper>
                  <AudioWrapper>
                      <WavesurferPlayer
                        height={100}
                        waveColor="#cccccc"
                        progressColor="#333333"
                        url={file.file}
                        onReady={onReady}
                        onPlay={() => setIsPlaying(true)}
                        onPause={() => setIsPlaying(false)}
                      />
                      <div style={{ textAlign: 'center', marginTop: '10px' }}>
                          <Button
                            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                            onClick={onPlayPause}
                          >
                              {isPlaying ? 'Pause' : 'Play'}
                          </Button>
                      </div>
                  </AudioWrapper>
              </PreviewWrapper>
            );

        case 'youtube':
            return (
              <PreviewWrapper>
                  <iframe
                    src={getYouTubeEmbedUrl(file.youtube_url)}
                    title={file.title}
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
              </PreviewWrapper>
            );

        default:
            return (
              <PreviewWrapper>
                  <GenericFileWrapper>
                      <FileOutlined />
                  </GenericFileWrapper>
              </PreviewWrapper>
            );
    }
};

export default FilePreview;