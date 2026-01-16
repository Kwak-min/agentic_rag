import React, { useState, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';

interface ReservoirData {
  status: string;
  level: number;
  is_anomaly: boolean;
  timestamp?: string;
  anomaly_score?: number;
}

interface AnomalyHistory {
  reservoir: string;
  status: string;
  level: number;
  timestamp: string;
  anomaly_score: number;
}

const AnomalyMonitoringPage: React.FC = () => {
  const [anomalyData, setAnomalyData] = useState<{ [key: string]: ReservoirData }>({
    gagok: { status: '정상', level: 0, is_anomaly: false },
    haeryong: { status: '정상', level: 0, is_anomaly: false },
    sangsa: { status: '정상', level: 0, is_anomaly: false }
  });
  const [alertHistory, setAlertHistory] = useState<AnomalyHistory[]>([]);
  const [notificationEnabled, setNotificationEnabled] = useState(false);

  useEffect(() => {
    const socket: Socket = io('http://localhost:5000');

    // 이상 탐지 알림 수신
    socket.on('anomaly_alert', (data: any) => {
      console.log('이상 탐지 알림 수신:', data);

      // 상태 업데이트
      setAnomalyData(prev => ({
        ...prev,
        [data.reservoir]: {
          status: data.status,
          level: data.level,
          is_anomaly: data.is_anomaly,
          timestamp: data.timestamp || new Date().toISOString(),
          anomaly_score: data.anomaly_score
        }
      }));

      // 이상이 감지된 경우 히스토리에 추가
      if (data.is_anomaly) {
        const newAlert: AnomalyHistory = {
          reservoir: data.reservoir,
          status: data.status,
          level: data.level,
          timestamp: data.timestamp || new Date().toISOString(),
          anomaly_score: data.anomaly_score || 0
        };
        setAlertHistory(prev => [newAlert, ...prev].slice(0, 50)); // 최근 50개만 유지

        // 브라우저 알림
        if (notificationEnabled && Notification.permission === 'granted') {
          new Notification('이상 탐지 알림', {
            body: `${getReservoirName(data.reservoir)}: ${data.status}`,
            icon: '/favicon.ico'
          });
        }
      }
    });

    // 초기 데이터 로드
    fetchAnomalyStatus();

    return () => {
      socket.close();
    };
  }, [notificationEnabled]);

  const fetchAnomalyStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/anomaly/status');
      const data = await response.json();
      if (data && data.reservoirs) {
        setAnomalyData(data.reservoirs);
      }
    } catch (error) {
      console.error('이상 탐지 상태 조회 실패:', error);
    }
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        setNotificationEnabled(true);
      }
    }
  };

  const getReservoirName = (key: string): string => {
    const names: { [key: string]: string } = {
      gagok: '가곡 배수지',
      haeryong: '해룡 배수지',
      sangsa: '상사 배수지'
    };
    return names[key] || key;
  };

  const getStatusColor = (status: string): string => {
    if (status === '정상') return 'bg-green-500';
    if (status.includes('경미')) return 'bg-yellow-500';
    if (status.includes('중간')) return 'bg-orange-500';
    if (status.includes('심각')) return 'bg-red-500';
    return 'bg-gray-500';
  };

  const getStatusTextColor = (status: string): string => {
    if (status === '정상') return 'text-green-700';
    if (status.includes('경미')) return 'text-yellow-700';
    if (status.includes('중간')) return 'text-orange-700';
    if (status.includes('심각')) return 'text-red-700';
    return 'text-gray-700';
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">🚨 RNN-LSTM 이상 탐지 모니터링</h1>
        <button
          onClick={requestNotificationPermission}
          disabled={notificationEnabled}
          className={`px-4 py-2 rounded-lg transition ${
            notificationEnabled
              ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          {notificationEnabled ? '알림 활성화됨' : '알림 활성화'}
        </button>
      </div>

      {/* 실시간 상태 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {Object.entries(anomalyData).map(([key, data]) => (
          <div
            key={key}
            className={`bg-white rounded-lg shadow-lg p-6 border-l-4 ${
              data.is_anomaly ? 'border-red-500' : 'border-green-500'
            }`}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-gray-900">{getReservoirName(key)}</h3>
              <span className={`w-3 h-3 rounded-full animate-pulse ${getStatusColor(data.status)}`} />
            </div>
            <div className="space-y-2">
              <div className={`text-2xl font-bold ${getStatusTextColor(data.status)}`}>
                {data.status}
              </div>
              <div className="text-gray-600">
                <span className="font-semibold">수위:</span> {data.level?.toFixed(2) || '0.00'} cm
              </div>
              {data.anomaly_score !== undefined && (
                <div className="text-gray-600">
                  <span className="font-semibold">이상 점수:</span> {data.anomaly_score.toFixed(4)}
                </div>
              )}
              {data.timestamp && (
                <div className="text-sm text-gray-500">
                  {new Date(data.timestamp).toLocaleString('ko-KR')}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 이상 탐지 히스토리 */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">📋 이상 탐지 히스토리</h2>
        {alertHistory.length === 0 ? (
          <p className="text-gray-500 text-center py-8">아직 이상 탐지 기록이 없습니다.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">시간</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">배수지</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">수위 (cm)</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">이상 점수</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {alertHistory.map((alert, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(alert.timestamp).toLocaleString('ko-KR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {getReservoirName(alert.reservoir)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(alert.status)} text-white`}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {alert.level.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {alert.anomaly_score.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 시스템 정보 */}
      <div className="mt-6 bg-blue-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">💡 시스템 정보</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• 모니터링 주기: 60초</li>
          <li>• AI 모델: RNN-LSTM 하이브리드</li>
          <li>• 실시간 WebSocket 연결</li>
          <li>• 이상 탐지 임계값: 자동 학습</li>
        </ul>
      </div>
    </div>
  );
};

export default AnomalyMonitoringPage;
