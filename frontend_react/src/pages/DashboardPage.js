import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import io from 'socket.io-client';
import './DashboardPage.css';

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [anomalyStatus, setAnomalyStatus] = useState({
    gagok: { status: '정상', level: 0 },
    haeryong: { status: '정상', level: 0 },
    sangsa: { status: '정상', level: 0 }
  });

  // 웹소켓 연결
  useEffect(() => {
    const socket = io('http://localhost:5000');

    // 이상 탐지 알림 수신
    socket.on('anomaly_alert', (data) => {
      setAnomalyStatus(prev => ({
        ...prev,
        [data.reservoir]: {
          status: data.status,
          level: data.level,
          is_anomaly: data.is_anomaly
        }
      }));
    });

    // 초기 데이터 로드
    fetchAnomalyStatus();

    return () => socket.close();
  }, []);

  const fetchAnomalyStatus = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/anomaly/status');
      if (response.data && response.data.reservoirs) {
        setAnomalyStatus(response.data.reservoirs);
      }
    } catch (error) {
      console.error('이상 탐지 상태 조회 실패:', error);
    }
  };

  const getStatusColor = (status) => {
    if (status === '정상') return '#4caf50';
    if (status.includes('경미')) return '#ff9800';
    if (status.includes('중간')) return '#ff5722';
    if (status.includes('심각')) return '#f44336';
    return '#9e9e9e';
  };

  const cards = [
    { title: 'AI 챗봇', icon: '💬', description: 'Ollama 기반 AI와 대화하기', path: '/chat' },
    { title: '점검 로그', icon: '📝', description: '배수지 점검 이력 관리', path: '/inspection' },
    { title: 'RNN-LSTM 이상 탐지', icon: '🚨', description: '실시간 배수지 이상 탐지 모니터링', path: '/anomaly' },
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

      {/* 실시간 이상 탐지 상태 */}
      <div className="anomaly-status-section">
        <div className="section-header">
          <h2>🚨 실시간 이상 탐지 상태</h2>
          <button className="view-detail-btn" onClick={() => navigate('/anomaly')}>
            상세보기 →
          </button>
        </div>
        <div className="status-grid">
          <div className="status-card">
            <div className="status-header">
              <span className="reservoir-name">가곡 배수지</span>
              <span
                className="status-indicator"
                style={{ backgroundColor: getStatusColor(anomalyStatus.gagok?.status || '정상') }}
              />
            </div>
            <div className="status-body">
              <div className="status-text">{anomalyStatus.gagok?.status || '정상'}</div>
              <div className="level-text">
                수위: {anomalyStatus.gagok?.level?.toFixed(2) || '0.00'} cm
              </div>
            </div>
          </div>

          <div className="status-card">
            <div className="status-header">
              <span className="reservoir-name">해룡 배수지</span>
              <span
                className="status-indicator"
                style={{ backgroundColor: getStatusColor(anomalyStatus.haeryong?.status || '정상') }}
              />
            </div>
            <div className="status-body">
              <div className="status-text">{anomalyStatus.haeryong?.status || '정상'}</div>
              <div className="level-text">
                수위: {anomalyStatus.haeryong?.level?.toFixed(2) || '0.00'} cm
              </div>
            </div>
          </div>

          <div className="status-card">
            <div className="status-header">
              <span className="reservoir-name">상사 배수지</span>
              <span
                className="status-indicator"
                style={{ backgroundColor: getStatusColor(anomalyStatus.sangsa?.status || '정상') }}
              />
            </div>
            <div className="status-body">
              <div className="status-text">{anomalyStatus.sangsa?.status || '정상'}</div>
              <div className="level-text">
                수위: {anomalyStatus.sangsa?.level?.toFixed(2) || '0.00'} cm
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h2>시스템 정보</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>AI 모델:</strong> Ollama (qwen2.5:7b) + RNN-LSTM 하이브리드
          </div>
          <div className="info-item">
            <strong>인증 방식:</strong> JWT (3시간 유효)
          </div>
          <div className="info-item">
            <strong>사용자 역할:</strong> {user?.role === 'admin' ? '관리자' : '일반 사용자'}
          </div>
          <div className="info-item">
            <strong>이상 탐지:</strong> 실시간 모니터링 (60초 간격)
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
