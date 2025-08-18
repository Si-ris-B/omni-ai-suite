import React, { useState } from "react";
import { Input, Button, Dropdown, Menu, Tabs, Card, Spin, Alert, Divider, Space, Typography } from "antd";
import {
  YoutubeOutlined,
  SearchOutlined,
  AudioOutlined,
  DownloadOutlined,
  GlobalOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  CalendarOutlined,
  InfoCircleOutlined,
  TranslationOutlined
} from "@ant-design/icons";
import "./YouTubeTranscriptPro.css";
import youtubeService from '../../services/youtubeService.js';

const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;

export default function YouTubeTranscriptPro() {
  const [url, setUrl] = useState("");
  const [selectedLang, setSelectedLang] = useState("English (Original)");
  const [selectedFormat, setSelectedFormat] = useState("text");
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("1");
  const [videoData, setVideoData] = useState(null);

  const handleProcess = async () => {
    if (!url.trim()) {
      setError("Please enter a valid YouTube URL");
      return;
    }

    setError(null);
    setLoading(true);
    setLogs([
      { type: "info", message: "Initializing YouTube Transcript Pro v2.1.5" },
      { type: "info", message: `Analyzing video URL: ${url}` },
    ]);
    setActiveTab("2"); // Switch to logs tab during processing

    try {
      const response = await youtubeService.getVideoInfo(url);
      setVideoData(response.data);

      setLogs(prev => [
        ...prev,
        { type: "success", message: "Connected to YouTube API successfully" },
        { type: "success", message: "Video metadata extracted successfully" },
      ]);
    } catch (err) {
      const errorMessage = err.response?.data?.error || "Failed to process video";
      setError(errorMessage);
      setLogs(prev => [
        ...prev,
        { type: "error", message: errorMessage },
      ]);
    } finally {
      setLoading(false);
      setActiveTab("1"); // Switch back to main tab
    }
  };

  const handleTranscribe = async () => {
    if (!url.trim()) {
      setError("Please enter a valid YouTube URL");
      return;
    }

    setError(null);
    setLoading(true);
    setLogs([]);
    setTranscript("");
    setActiveTab("2"); // Switch to logs tab during processing

    try {
      setLogs(prev => [
        ...prev,
        { type: "info", message: "Initializing YouTube Transcript Pro v2.1.5" },
        { type: "success", message: "Connected to YouTube API successfully" },
        { type: "info", message: `Analyzing video: ${videoData?.title || url}` },
        { type: "success", message: "Video metadata extracted successfully" },
        { type: "info", message: "Checking for existing English subtitles..." },
      ]);

      // Call the transcribe API with the selected format
      const response = await youtubeService.transcribeVideo(url, selectedFormat);

      setLogs(prev => [
        ...prev,
        { type: "success", message: "Processing completed successfully" },
      ]);

      // Set the transcript content
      setTranscript(response.data.transcript);

      setActiveTab("1"); // Switch back to transcript tab when done
    } catch (err) {
      const errorMessage = err.response?.data?.error || "Failed to transcribe video";
      setError(errorMessage);
      setLogs(prev => [
        ...prev,
        { type: "error", message: errorMessage },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    let content = transcript;
    let filename = "transcript.txt";

    if (selectedFormat === "text") {
      filename = `transcript_${videoData?.title?.replace(/\s+/g, '_') || 'video'}.txt`;
    } else {
      filename = "subtitles.srt";
    }

    const blob = new Blob([content], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  const languageMenu = (
    <Menu
      onClick={(e) => setSelectedLang(e.key)}
      items={[
        { key: "English (Original)", label: "English (Original)" },
        { key: "Spanish", label: "Spanish" },
        { key: "French", label: "French" },
        { key: "German", label: "German" },
        { key: "Japanese", label: "Japanese" },
        { key: "Chinese", label: "Chinese" },
        { key: "Portuguese", label: "Portuguese" },
      ]}
    />
  );

  return (
    <div className="ytp-wrapper">
      <header className="ytp-header">
        <div className="ytp-header-content">
          <Space align="center" size="middle">
            <YoutubeOutlined className="ytp-header-icon" />
            <Title level={2} className="ytp-title">YouTube Transcript Pro</Title>
          </Space>
          <Text className="ytp-subtitle">Extract, translate, and download transcripts from any YouTube video</Text>
        </div>
      </header>

      <main className="ytp-main">
        <Card className="ytp-card">
          <section className="ytp-input-section">
            <Title level={4} className="ytp-section-title">
              <InfoCircleOutlined style={{ marginRight: 8 }} />
              Video URL
            </Title>
            <Space.Compact block size="large" className="ytp-input-row">
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Paste YouTube video URL here..."
                allowClear
              />
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleProcess}
                loading={loading}
              >
                Process Video
              </Button>
            </Space.Compact>
            {error && !loading && (
              <Alert
                message={error}
                type="error"
                showIcon
                closable
                onClose={() => setError(null)}
                className="ytp-error-alert"
              />
            )}
          </section>

          {videoData && (
            <>
              <Divider />

              <section className="ytp-preview-section">
                <Title level={4} className="ytp-section-title">Video Information</Title>
                <div className="ytp-preview">
                  <div className="ytp-thumbnail-container">
                    <div className="ytp-thumbnail-wrapper">
                      <img src={videoData.thumbnail} alt="Video thumbnail" className="ytp-thumbnail" />
                      <div className="ytp-duration-badge">{videoData.duration}</div>
                    </div>
                    <div className="ytp-channel-info">
                      {videoData.channelLogo && (
                        <img src={videoData.channelLogo} alt="Channel logo" className="ytp-channel-logo" />
                      )}
                      <div>
                        <Text strong className="ytp-channel-name">{videoData.channel}</Text>
                        <div className="ytp-stats">
                          <Space size="middle">
                            <Text type="secondary"><EyeOutlined /> {videoData.views}</Text>
                            <Text type="secondary"><CalendarOutlined /> {videoData.date}</Text>
                          </Space>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="ytp-video-info">
                    <Title level={5} className="ytp-video-title">{videoData.title}</Title>
                    <Paragraph ellipsis={{ rows: 3 }} className="ytp-video-description">
                      {videoData.description}
                    </Paragraph>
                  </div>
                </div>
              </section>
            </>
          )}

          {videoData && (
            <>
              <Divider />

              <section className="ytp-controls-section">
                <Title level={4} className="ytp-section-title">Transcription Settings</Title>
                <div className="ytp-controls-grid">
                  <div className="ytp-control-group">
                    <Title level={5} className="ytp-control-title">
                      <GlobalOutlined className="ytp-control-icon" />
                      Language
                    </Title>
                    <Dropdown overlay={languageMenu} trigger={["click"]}>
                      <Button size="large" className="ytp-dropdown-button">
                        {selectedLang}
                      </Button>
                    </Dropdown>
                  </div>
                  <div className="ytp-control-group">
                    <Title level={5} className="ytp-control-title">
                      <FileTextOutlined className="ytp-control-icon" />
                      Output Format
                    </Title>
                    <Space size="middle" className="ytp-format-options">
                      <Button
                        type={selectedFormat === "text" ? "primary" : "default"}
                        onClick={() => setSelectedFormat("text")}
                        size="large"
                      >
                        Plain Text
                      </Button>
                      <Button
                        type={selectedFormat === "srt" ? "primary" : "default"}
                        onClick={() => setSelectedFormat("srt")}
                        size="large"
                      >
                        SRT Subtitles
                      </Button>
                    </Space>
                  </div>
                </div>
              </section>

              <section className="ytp-actions-section">
                <Space size="middle" className="ytp-action-buttons">
                  <Button
                    type="primary"
                    icon={<AudioOutlined />}
                    onClick={handleTranscribe}
                    size="large"
                    loading={loading}
                    className="ytp-action-button"
                  >
                    Transcribe Video
                  </Button>
                  <Button
                    type="default"
                    icon={<TranslationOutlined />}
                    size="large"
                    className="ytp-action-button"
                    disabled={!transcript}
                  >
                    Translate Transcript
                  </Button>
                </Space>
              </section>
            </>
          )}

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            className="ytp-tabs"
            items={[
              {
                key: "1",
                label: "Transcript",
                children: (
                  <div className="ytp-tab-content">
                    <Spin spinning={loading} tip="Processing video...">
                      {transcript && (
                        <div className="ytp-download-container">
                          <Button
                            icon={<DownloadOutlined />}
                            type="primary"
                            onClick={handleDownload}
                            size="large"
                          >
                            Download {selectedFormat === "text" ? "Transcript" : "Subtitles"}
                          </Button>
                        </div>
                      )}
                      <div className="ytp-transcript-container">
                        {transcript ? (
                          selectedFormat === "srt" ? (
                            // For SRT, display as preformatted text
                            <pre className="ytp-srt-content">{transcript}</pre>
                          ) : (
                            // For plain text, display as a paragraph
                            <Paragraph className="ytp-plain-text">
                              {transcript}
                            </Paragraph>
                          )
                        ) : (
                          <div className="ytp-empty-state">
                            <Paragraph type="secondary">
                              No transcript available. Click "Transcribe Video" to generate one.
                            </Paragraph>
                          </div>
                        )}
                      </div>
                    </Spin>
                  </div>
                )
              },
              {
                key: "2",
                label: "Processing Logs",
                children: (
                  <div className="ytp-tab-content">
                    <div className="ytp-terminal">
                      {logs.length > 0 ? (
                        logs.map((log, i) => (
                          <div key={i} className={`ytp-log ytp-log-${log.type}`}>
                            <Text type="secondary" className="ytp-log-timestamp">
                              [{new Date().toLocaleTimeString()}]
                            </Text>
                            <Text className="ytp-log-message">{log.message}</Text>
                          </div>
                        ))
                      ) : (
                        <div className="ytp-empty-state">
                          <Paragraph type="secondary">
                            Processing logs will appear here when you transcribe a video.
                          </Paragraph>
                        </div>
                      )}
                    </div>
                  </div>
                )
              }
            ]}
          />
        </Card>
      </main>

      <footer className="ytp-footer">
        <div className="ytp-footer-content">
          <Text type="secondary">
            YouTube Transcript Pro © {new Date().getFullYear()} | Professional Transcription Tool
          </Text>
          <Space size="middle" className="ytp-footer-links">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Contact Support</a>
          </Space>
        </div>
      </footer>
    </div>
  );
}