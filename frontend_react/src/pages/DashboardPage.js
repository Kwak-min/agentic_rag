import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './DashboardPage.css';

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const cards = [
    { title: 'AI 챗봇', icon: '💬', description: 'Ollama 기반 AI와 대화하기', path: '/chat' },
    { title: '점검 로그', icon: '📝', description: '배수지 점검 이력 관리', path: '/inspection' },
  ];

  if (user?.role === 'admin') {
    cards.push(
      { title: '프롬프트 관리', icon: '⚙️', description: 'AI 시스템 프롬프트 설정', path: '/prompts' },
      { title: '설정', icon: '🔧', description: '시스템 설정', path: '/settings' }
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>대시보드</h1>
        <p>안녕하세요, {user?.name || user?.username}님!</p>
      </div>

      <div className="card-grid">
        {cards.map((card) => (
          <div key={card.path} className="dashboard-card" onClick={() => navigate(card.path)}>
            <div className="card-icon">{card.icon}</div>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
          </div>
        ))}
      </div>

      <div className="info-section">
        <h2>시스템 정보</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>AI 모델:</strong> Ollama (qwen2.5:7b)
          </div>
          <div className="info-item">
            <strong>인증 방식:</strong> JWT (3시간 유효)
          </div>
          <div className="info-item">
            <strong>사용자 역할:</strong> {user?.role === 'admin' ? '관리자' : '일반 사용자'}
          </div>
          <div className="info-item">
            <strong>Function Calling:</strong> 활성화됨
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
