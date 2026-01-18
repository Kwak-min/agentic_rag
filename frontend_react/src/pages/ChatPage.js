import React, { useState, useRef, useEffect } from 'react';
import chatService from '../services/chatService';
import api from '../services/api';
import './ChatPage.css';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // PDF 업로드 관련 상태
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 업로드된 파일 목록 불러오기
  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  const fetchUploadedFiles = async () => {
    try {
      const response = await api.get('/api/files');
      setUploadedFiles(response.data.files || []);
    } catch (error) {
      console.error('파일 목록 조회 오류:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadError('');

    for (const file of files) {
      // PDF 파일만 허용
      if (!file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.txt')) {
        setUploadError('PDF 또는 TXT 파일만 업로드 가능합니다.');
        continue;
      }

      const formData = new FormData();
      formData.append('file', file);

      try {
        await api.post('/api/files/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } catch (error) {
        console.error('파일 업로드 오류:', error);
        setUploadError(`${file.name} 업로드 실패`);
      }
    }

    setUploading(false);
    fetchUploadedFiles();
    // 파일 입력 초기화
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // 사용자 메시지 추가
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await chatService.sendMessage(userMessage);

      // AI 응답 추가
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.response || '응답을 생성할 수 없습니다.',
          toolCalls: response.tool_calls,
          toolResults: response.tool_results,
        },
      ]);
    } catch (error) {
      console.error('챗봇 오류:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '오류가 발생했습니다. 다시 시도해주세요.', error: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = (message, index) => {
    const isUser = message.role === 'user';

    return (
      <div key={index} className={`message ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-avatar">{isUser ? '👤' : '🤖'}</div>
        <div className="message-content">
          <div className="message-text">{message.content}</div>
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="tool-calls">
              <p>
                <strong>🛠️ 사용된 도구:</strong>
              </p>
              <ul>
                {message.toolCalls.map((tool, i) => (
                  <li key={i}>{tool.name || tool}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="chat-page-container">
      {/* PDF 업로드 사이드바 */}
      <div className="pdf-sidebar">
        <div className="pdf-sidebar-header">
          <h2>📄 문서 관리</h2>
          <p>PDF/TXT 파일을 업로드하면 AI가 내용을 참고합니다</p>
        </div>

        <div className="pdf-upload-area">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.txt"
            multiple
            className="pdf-file-input"
            id="pdf-upload"
          />
          <label htmlFor="pdf-upload" className="pdf-upload-label">
            {uploading ? (
              <span>⏳ 업로드 중...</span>
            ) : (
              <>
                <span className="upload-icon">📁</span>
                <span>파일 선택 또는 드래그</span>
                <span className="upload-hint">PDF, TXT 지원</span>
              </>
            )}
          </label>
        </div>

        {uploadError && <div className="upload-error">{uploadError}</div>}

        <div className="uploaded-files-list">
          <h3>업로드된 파일 ({uploadedFiles.length})</h3>
          {uploadedFiles.length === 0 ? (
            <p className="no-files">업로드된 파일이 없습니다</p>
          ) : (
            <ul>
              {uploadedFiles.map((file, index) => (
                <li key={index} className="file-item">
                  <span className="file-icon">
                    {file.filename?.endsWith('.pdf') ? '📕' : '📄'}
                  </span>
                  <span className="file-name" title={file.filename}>
                    {file.filename}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* 채팅 영역 */}
      <div className="chat-main">
        <div className="chat-header">
          <h1>💬 AI 챗봇</h1>
          <p>Ollama (qwen2.5:7b)를 사용한 대화형 AI</p>
        </div>

        <div className="chat-container">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="empty-chat">
                <p>👋 안녕하세요! 무엇을 도와드릴까요?</p>
                <div className="example-questions">
                  <p>
                    <strong>예시 질문:</strong>
                  </p>
                  <ul>
                    <li>저번에 가곡 배수지에서 무슨 문제 있었어?</li>
                    <li>이전에 펌프 관련 점검 이력 알려줘</li>
                    <li>최근 점검 로그 요약해줘</li>
                    <li>업로드한 문서에서 OO 찾아줘</li>
                  </ul>
                </div>
              </div>
            ) : (
              messages.map(renderMessage)
            )}
            {loading && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="chat-input-form">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="메시지를 입력하세요..."
              disabled={loading}
              className="chat-input"
            />
            <button type="submit" disabled={loading || !inputMessage.trim()} className="send-button">
              {loading ? '⏳' : '📤'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
