// pages/AnomalyTest.js - 이상 탐지 테스트 인터페이스

import React, { useState } from 'react';
import api from '../services/api';
import './AnomalyTest.css';

const AnomalyTest = () => {
  const [testData, setTestData] = useState({
    reservoir: 'gagok',
    waterLevels: '',
    pumpA: 0,
    pumpB: 0,
    actualNextLevel: ''
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 샘플 데이터
  const sampleData = {
    normal: {
      name: '정상 패턴',
      data: Array.from({ length: 60 }, (_, i) => 70 + Math.sin(i / 10) * 2).join(', '),
      pumpA: 0,
      pumpB: 0,
      actual: 70.5
    },
    anomaly_drop: {
      name: '급격한 수위 하강 (이상)',
      data: Array.from({ length: 60 }, (_, i) => {
        if (i < 50) return 70 + Math.sin(i / 10) * 2;
        return 70 - (i - 50) * 3; // 급격히 하강
      }).join(', '),
      pumpA: 1,
      pumpB: 0,
      actual: 45
    },
    anomaly_spike: {
      name: '급격한 수위 상승 (이상)',
      data: Array.from({ length: 60 }, (_, i) => {
        if (i < 50) return 70 + Math.sin(i / 10) * 2;
        return 70 + (i - 50) * 4; // 급격히 상승
      }).join(', '),
      pumpA: 0,
      pumpB: 1,
      actual: 110
    },
    anomaly_unstable: {
      name: '불안정한 패턴 (이상)',
      data: Array.from({ length: 60 }, (_, i) =>
        70 + Math.random() * 20 - 10
      ).join(', '),
      pumpA: 1,
      pumpB: 1,
      actual: 85
    }
  };

  // 입력 변경
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTestData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (checked ? 1 : 0) : value
    }));
  };

  // 샘플 데이터 로드
  const loadSample = (key) => {
    const sample = sampleData[key];
    setTestData({
      reservoir: 'gagok',
      waterLevels: sample.data,
      pumpA: sample.pumpA,
      pumpB: sample.pumpB,
      actualNextLevel: sample.actual.toString()
    });
    setResult(null);
    setError(null);
  };

  // 테스트 실행
  const runTest = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 수위 데이터 파싱
      const waterLevelsArray = testData.waterLevels
        .split(',')
        .map(v => parseFloat(v.trim()))
        .filter(v => !isNaN(v));

      if (waterLevelsArray.length === 0) {
        throw new Error('유효한 수위 데이터를 입력하세요');
      }

      const actualNext = testData.actualNextLevel
        ? parseFloat(testData.actualNextLevel)
        : null;

      // API 요청
      const response = await api.post('/api/anomaly/detect', {
        water_levels: waterLevelsArray,
        pump_a: testData.pumpA,
        pump_b: testData.pumpB,
        actual_next_level: actualNext
      });

      setResult(response.data);

    } catch (err) {
      console.error('테스트 실패:', err);
      setError(err.response?.data?.error || err.message || '테스트 실행 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 상태 색상
  const getStatusColor = (statusCode) => {
    const colors = {
      normal: '#4caf50',
      minor_anomaly: '#ff9800',
      moderate_anomaly: '#ff5722',
      severe_anomaly: '#f44336'
    };
    return colors[statusCode] || '#9e9e9e';
  };

  return (
    <div className="anomaly-test">
      <div className="test-header">
        <h1>🧪 이상 탐지 테스트</h1>
        <p>수위 데이터와 펌프 상태를 입력하여 LSTM 모델이 이상을 탐지하는지 테스트합니다.</p>
      </div>

      <div className="test-container">
        {/* 입력 섹션 */}
        <div className="input-section">
          <h2>📝 테스트 데이터 입력</h2>

          {/* 샘플 데이터 버튼 */}
          <div className="sample-buttons">
            <h3>샘플 데이터:</h3>
            <div className="button-group">
              {Object.entries(sampleData).map(([key, sample]) => (
                <button
                  key={key}
                  onClick={() => loadSample(key)}
                  className="sample-btn"
                >
                  {sample.name}
                </button>
              ))}
            </div>
          </div>

          {/* 배수지 선택 */}
          <div className="input-group">
            <label>배수지</label>
            <select
              name="reservoir"
              value={testData.reservoir}
              onChange={handleChange}
            >
              <option value="gagok">가곡 배수지</option>
              <option value="haeryong">해룡 배수지</option>
              <option value="sangsa">상사 배수지</option>
            </select>
          </div>

          {/* 수위 데이터 */}
          <div className="input-group">
            <label>과거 수위 데이터 (쉼표로 구분, 최소 60개 권장)</label>
            <textarea
              name="waterLevels"
              value={testData.waterLevels}
              onChange={handleChange}
              placeholder="예: 70.5, 70.8, 71.2, 71.5, ..."
              rows={6}
            />
            <small>
              입력된 데이터 개수: {
                testData.waterLevels.split(',').filter(v => v.trim()).length
              }개
            </small>
          </div>

          {/* 펌프 상태 */}
          <div className="input-group">
            <label>펌프 상태</label>
            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="pumpA"
                  checked={testData.pumpA === 1}
                  onChange={handleChange}
                />
                펌프 A (ON: 체크, OFF: 미체크)
              </label>
              <label>
                <input
                  type="checkbox"
                  name="pumpB"
                  checked={testData.pumpB === 1}
                  onChange={handleChange}
                />
                펌프 B (ON: 체크, OFF: 미체크)
              </label>
            </div>
          </div>

          {/* 실제 다음 수위 */}
          <div className="input-group">
            <label>실제 다음 수위 (이상 탐지용, 선택)</label>
            <input
              type="number"
              name="actualNextLevel"
              value={testData.actualNextLevel}
              onChange={handleChange}
              placeholder="예: 72.5"
              step="0.01"
            />
            <small>입력하면 예측값과 비교하여 이상 여부를 판단합니다</small>
          </div>

          {/* 테스트 실행 버튼 */}
          <button
            onClick={runTest}
            disabled={loading || !testData.waterLevels}
            className="run-test-btn"
          >
            {loading ? '테스트 중...' : '🚀 테스트 실행'}
          </button>
        </div>

        {/* 결과 섹션 */}
        <div className="result-section">
          <h2>📊 테스트 결과</h2>

          {loading && (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>LSTM 모델이 분석 중입니다...</p>
            </div>
          )}

          {error && (
            <div className="error-box">
              <h3>❌ 오류</h3>
              <p>{error}</p>
            </div>
          )}

          {result && !loading && (
            <div className="result-content">
              {/* 상태 표시 */}
              <div
                className="status-box"
                style={{
                  borderColor: getStatusColor(result.status_code),
                  backgroundColor: `${getStatusColor(result.status_code)}15`
                }}
              >
                <div className="status-header">
                  <h3>
                    {result.is_anomaly ? '⚠️ 이상 감지' : '✅ 정상'}
                  </h3>
                  <span
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(result.status_code) }}
                  >
                    {result.status}
                  </span>
                </div>
              </div>

              {/* 예측 정보 */}
              <div className="info-card">
                <h3>🔮 예측 정보</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">마지막 수위</span>
                    <span className="info-value">{result.last_water_level?.toFixed(2)} cm</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">예측 수위</span>
                    <span className="info-value">{result.prediction?.toFixed(2)} cm</span>
                  </div>
                  {result.actual_value !== undefined && (
                    <>
                      <div className="info-item">
                        <span className="info-label">실제 수위</span>
                        <span className="info-value">{result.actual_value?.toFixed(2)} cm</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">오차</span>
                        <span className="info-value error">{result.error?.toFixed(2)} cm</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">임계값</span>
                        <span className="info-value">{result.threshold?.toFixed(2)} cm</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">심각도</span>
                        <span className="info-value">⭐ {result.severity} / 5</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* 펌프 상태 */}
              <div className="info-card">
                <h3>🔧 펌프 상태</h3>
                <div className="pump-status">
                  <span className={`pump ${result.pump_a === 1 ? 'on' : 'off'}`}>
                    펌프 A: {result.pump_a === 1 ? 'ON' : 'OFF'}
                  </span>
                  <span className={`pump ${result.pump_b === 1 ? 'on' : 'off'}`}>
                    펌프 B: {result.pump_b === 1 ? 'ON' : 'OFF'}
                  </span>
                </div>
              </div>

              {/* 요약 */}
              {result.anomaly_summary && (
                <div className="info-card summary">
                  <h3>📝 요약</h3>
                  <p>{result.anomaly_summary}</p>
                </div>
              )}
            </div>
          )}

          {!loading && !error && !result && (
            <div className="empty-state">
              <p>테스트 데이터를 입력하고 실행 버튼을 눌러주세요</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnomalyTest;
