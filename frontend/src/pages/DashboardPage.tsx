import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { io, Socket } from 'socket.io-client';

interface ReservoirStatus {
  status: string;
  level: number;
  is_anomaly?: boolean;
}

interface AnomalyStatusMap {
  gagok: ReservoirStatus;
  haeryong: ReservoirStatus;
  sangsa: ReservoirStatus;
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [anomalyStatus, setAnomalyStatus] = useState<AnomalyStatusMap>({
    gagok: { status: '정상', level: 0 },
    haeryong: { status: '정상', level: 0 },
    sangsa: { status: '정상', level: 0 }
  });

  // 웹소켓 연결
  useEffect(() => {
    const socket: Socket = io('http://localhost:5000');

    // 이상 탐지 알림 수신
    socket.on('anomaly_alert', (data: any) => {
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

    return () => {
      socket.close();
    };
  }, []);

  const fetchAnomalyStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/anomaly/status');
      const data = await response.json();
      if (data && data.reservoirs) {
        setAnomalyStatus(data.reservoirs);
      }
    } catch (error) {
      console.error('이상 탐지 상태 조회 실패:', error);
    }
  };

  const getStatusColor = (status: string): string => {
    if (status === '정상') return '#4caf50';
    if (status.includes('경미')) return '#ff9800';
    if (status.includes('중간')) return '#ff5722';
    if (status.includes('심각')) return '#f44336';
    return '#9e9e9e';
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">대시보드</h1>

      {/* 환영 메시지 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">환영합니다, {user?.name}님!</h2>
        <p className="text-gray-600">
          역할: <span className="font-medium">{user?.role === 'admin' ? '관리자' : '사용자'}</span>
        </p>
      </div>

      {/* 실시간 이상 탐지 상태 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">🚨 실시간 이상 탐지 상태</h2>
          <button
            onClick={() => navigate('/anomaly')}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          >
            상세보기 →
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 가곡 배수지 */}
          <div className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-500 transition">
            <div className="flex justify-between items-center mb-3">
              <span className="font-semibold text-lg">가곡 배수지</span>
              <span
                className="w-4 h-4 rounded-full animate-pulse"
                style={{ backgroundColor: getStatusColor(anomalyStatus.gagok?.status || '정상') }}
              />
            </div>
            <div className="text-left">
              <div className="text-xl font-bold text-gray-900 mb-2">
                {anomalyStatus.gagok?.status || '정상'}
              </div>
              <div className="text-sm text-gray-600">
                수위: {anomalyStatus.gagok?.level?.toFixed(2) || '0.00'} cm
              </div>
            </div>
          </div>

          {/* 해룡 배수지 */}
          <div className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-500 transition">
            <div className="flex justify-between items-center mb-3">
              <span className="font-semibold text-lg">해룡 배수지</span>
              <span
                className="w-4 h-4 rounded-full animate-pulse"
                style={{ backgroundColor: getStatusColor(anomalyStatus.haeryong?.status || '정상') }}
              />
            </div>
            <div className="text-left">
              <div className="text-xl font-bold text-gray-900 mb-2">
                {anomalyStatus.haeryong?.status || '정상'}
              </div>
              <div className="text-sm text-gray-600">
                수위: {anomalyStatus.haeryong?.level?.toFixed(2) || '0.00'} cm
              </div>
            </div>
          </div>

          {/* 상사 배수지 */}
          <div className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-500 transition">
            <div className="flex justify-between items-center mb-3">
              <span className="font-semibold text-lg">상사 배수지</span>
              <span
                className="w-4 h-4 rounded-full animate-pulse"
                style={{ backgroundColor: getStatusColor(anomalyStatus.sangsa?.status || '정상') }}
              />
            </div>
            <div className="text-left">
              <div className="text-xl font-bold text-gray-900 mb-2">
                {anomalyStatus.sangsa?.status || '정상'}
              </div>
              <div className="text-sm text-gray-600">
                수위: {anomalyStatus.sangsa?.level?.toFixed(2) || '0.00'} cm
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
