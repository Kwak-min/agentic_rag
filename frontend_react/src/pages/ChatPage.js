import React, { useState, useRef, useEffect } from 'react';
import chatService from '../services/chatService';
import './ChatPage.css';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    <div className="chat-page">
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
  );
};

export default ChatPage;
