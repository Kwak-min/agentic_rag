// pages/AnomalyMonitoring.js - LSTM 기반 이상 탐지 모니터링 화면

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import './AnomalyMonitoring.css';

const AnomalyMonitoring = () => {
  const [reservoirs, setReservoirs] = useState({
    gagok: { status: '정상', level: 0, prediction: 0, error: 0, lastUpdate: null },
    haeryong: { status: '정상', level: 0, prediction: 0, error: 0, lastUpdate: null },
    sangsa: { status: '정상', level: 0, prediction: 0, error: 0, lastUpdate: null }
  });

  const [selectedReservoir, setSelectedReservoir] = useState('gagok');
  const [diagnosis, setDiagnosis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [alerts, setAlerts] = useState([]); // 실시간 알림
  const [socket, setSocket] = useState(null);

  // 웹소켓 연결
  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    // 이상 탐지 알림 수신
    newSocket.on('anomaly_alert', (data) => {
      console.log('🚨 이상 탐지 알림:', data);

      // 알림 추가
      setAlerts(prev => [{
        id: Date.now(),
        ...data,
        time: new Date().toLocaleTimeString('ko-KR')
      }, ...prev].slice(0, 10)); // 최대 10개

      // 배수지 데이터 즉시 갱신
      fetchReservoirData();

      // 브라우저 알림 (권한이 있는 경우)
      if (Notification.permission === 'granted' && data.is_anomaly) {
        new Notification(`${data.reservoir_name} 이상 탐지!`, {
          body: `${data.status} - 오차: ${data.error.toFixed(2)}cm`,
          icon: '/logo192.png'
        });
      }
    });

    // 브라우저 알림 권한 요청
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    return () => newSocket.close();
  }, []);

  // 실시간 데이터 갱신
  useEffect(() => {
    fetchReservoirData();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchReservoirData();
      }, 10000); // 10초마다 갱신

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // 배수지 데이터 조회
  const fetchReservoirData = async () => {
    try {
      const response = await axios.get('/api/anomaly/status');

      if (response.data && response.data.reservoirs) {
        setReservoirs(response.data.reservoirs);
      }
    } catch (error) {
      console.error('데이터 조회 실패:', error);
    }
  };

  // 상세 진단 요청
  const requestDiagnosis = async (reservoir) => {
    setLoading(true);
    setDiagnosis(null);

    try {
      const reservoirData = reservoirs[reservoir];

      const response = await axios.post('/api/anomaly/diagnose', {
        reservoir: reservoir,
        anomaly_type: getAnomalyType(reservoirData.status),
        water_level_change: reservoirData.error,
        pump_status: {
          pump_a: reservoirData.pump_a || 0,
          pump_b: reservoirData.pump_b || 0
        },
        error_magnitude: Math.abs(reservoirData.error)
      });

      setDiagnosis(response.data);
    } catch (error) {
      console.error('진단 요청 실패:', error);
      setDiagnosis({ error: '진단 요청 중 오류가 발생했습니다.' });
    } finally {
      setLoading(false);
    }
  };

  // 이상 유형 판단
  const getAnomalyType = (status) => {
    if (status.includes('급감')) return '급감';
    if (status.includes('급증')) return '급증';
    if (status.includes('불안정')) return '불안정';
    return '이상';
  };

  // 상태 색상
  const getStatusColor = (status) => {
    if (status === '정상') return '#4caf50';
    if (status.includes('경미')) return '#ff9800';
    if (status.includes('중간')) return '#ff5722';
    if (status.includes('심각')) return '#f44336';
    return '#9e9e9e';
  };

  // 심각도 배지
  const getSeverityBadge = (severity) => {
    const colors = {
      '낮음': '#4caf50',
      '중간': '#ff9800',
      '높음': '#ff5722',
      '긴급': '#f44336'
    };

    return (
      <span
        className="severity-badge"
        style={{ backgroundColor: colors[severity] || '#9e9e9e' }}
      >
        {severity}
      </span>
    );
  };

  return (
    <div className="anomaly-monitoring">
      <div className="header">
        <h1>🔍 LSTM 이상 탐지 모니터링</h1>
        <div className="controls">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            자동 갱신 (10초)
          </label>
          <button onClick={fetchReservoirData} className="refresh-btn">
            🔄 새로고침
          </button>
        </div>
      </div>

      {/* 실시간 알림 배너 */}
      {alerts.length > 0 && (
        <div className="alert-banner">
          <h3>🔔 최근 알림</h3>
          <div className="alert-list">
            {alerts.map(alert => (
              <div
                key={alert.id}
                className={`alert-item ${alert.is_anomaly ? 'anomaly' : 'normal'} severity-${alert.severity}`}
              >
                <span className="alert-time">{alert.time}</span>
                <span className="alert-reservoir">{alert.reservoir_name}</span>
                <span className={`alert-status ${alert.status_code}`}>{alert.status}</span>
                <span className="alert-detail">
                  수위: {alert.level.toFixed(2)}cm (예측: {alert.prediction.toFixed(2)}cm, 오차: {alert.error.toFixed(2)}cm)
                </span>
              </div>
            ))}
          </div>
          {alerts.length > 0 && (
            <button className="clear-alerts-btn" onClick={() => setAlerts([])}>
              알림 지우기
            </button>
          )}
        </div>
      )}

      {/* 배수지 상태 카드 */}
      <div className="reservoir-cards">
        {Object.entries(reservoirs).map(([key, data]) => (
          <div
            key={key}
            className={`reservoir-card ${selectedReservoir === key ? 'selected' : ''}`}
            onClick={() => setSelectedReservoir(key)}
          >
            <div className="card-header">
              <h3>{getReservoirName(key)}</h3>
              <div
                className="status-indicator"
                style={{ backgroundColor: getStatusColor(data.status) }}
              />
            </div>

            <div className="card-body">
              <div className="metric">
                <span className="label">현재 수위</span>
                <span className="value">{data.level.toFixed(2)} cm</span>
              </div>

              <div className="metric">
                <span className="label">예측 수위</span>
                <span className="value">{data.prediction.toFixed(2)} cm</span>
              </div>

              <div className="metric">
                <span className="label">오차</span>
                <span className={`value ${Math.abs(data.error) > 10 ? 'error' : ''}`}>
                  {data.error > 0 ? '+' : ''}{data.error.toFixed(2)} cm
                </span>
              </div>

              <div className="status-text">
                <strong>상태:</strong> {data.status}
              </div>

              {data.lastUpdate && (
                <div className="last-update">
                  {new Date(data.lastUpdate).toLocaleString('ko-KR')}
                </div>
              )}
            </div>

            {data.status !== '정상' && (
              <button
                className="diagnose-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  requestDiagnosis(key);
                }}
              >
                🩺 AI 진단
              </button>
            )}
          </div>
        ))}
      </div>

      {/* AI 진단 결과 */}
      {loading && (
        <div className="diagnosis-section loading">
          <div className="spinner"></div>
          <p>AI가 진단 중입니다...</p>
        </div>
      )}

      {diagnosis && !loading && (
        <div className="diagnosis-section">
          <h2>🤖 AI 진단 결과 - {getReservoirName(selectedReservoir)}</h2>

          {diagnosis.error ? (
            <div className="error-message">{diagnosis.error}</div>
          ) : (
            <>
              {/* 심각도 */}
              <div className="diagnosis-card">
                <h3>⚠️ 심각도</h3>
                <div className="severity-info">
                  {getSeverityBadge(diagnosis.diagnosis?.severity || '알 수 없음')}
                </div>
              </div>

              {/* 가능한 원인 */}
              <div className="diagnosis-card">
                <h3>🔎 가능한 원인</h3>
                <ul className="cause-list">
                  {diagnosis.diagnosis?.possible_causes?.map((cause, idx) => (
                    <li key={idx}>{cause}</li>
                  )) || <li>원인 분석 중...</li>}
                </ul>
              </div>

              {/* 즉시 조치사항 */}
              <div className="diagnosis-card urgent">
                <h3>⚡ 즉시 조치사항</h3>
                <ul className="action-list">
                  {diagnosis.diagnosis?.immediate_actions?.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  )) || <li>조치사항 없음</li>}
                </ul>
              </div>

              {/* 장기 대책 */}
              {diagnosis.diagnosis?.long_term_solutions?.length > 0 && (
                <div className="diagnosis-card">
                  <h3>📋 장기 대책</h3>
                  <ul className="solution-list">
                    {diagnosis.diagnosis.long_term_solutions.map((solution, idx) => (
                      <li key={idx}>{solution}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 유사 사례 */}
              {diagnosis.similar_cases?.length > 0 && (
                <div className="diagnosis-card">
                  <h3>📚 과거 유사 사례</h3>
                  <div className="similar-cases">
                    {diagnosis.similar_cases.map((caseItem, idx) => (
                      <div key={idx} className="case-item">
                        <div className="case-header">
                          <span className="case-number">사례 {idx + 1}</span>
                          <span className="similarity">
                            유사도: {(caseItem.similarity * 100).toFixed(1)}%
                          </span>
                        </div>
                        <p className="case-content">{caseItem.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 전체 진단 내용 */}
              {diagnosis.diagnosis?.raw_diagnosis && (
                <div className="diagnosis-card full-diagnosis">
                  <h3>📄 상세 진단</h3>
                  <pre className="diagnosis-text">
                    {diagnosis.diagnosis.raw_diagnosis}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

// 배수지 이름 매핑
const getReservoirName = (key) => {
  const names = {
    gagok: '가곡 배수지',
    haeryong: '해룡 배수지',
    sangsa: '상사 배수지'
  };
  return names[key] || key;
};

export default AnomalyMonitoring;
