import React from 'react';
import { useAuth } from '../context/AuthContext';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">대시보드</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">환영합니다, {user?.name}님!</h2>
        <p className="text-gray-600">
          역할: <span className="font-medium">{user?.role === 'admin' ? '관리자' : '사용자'}</span>
        </p>
        <p className="text-gray-600 mt-2">
          이곳은 메인 대시보드입니다. 좌측 메뉴에서 원하는 기능을 선택해주세요.
        </p>
      </div>
    </div>
  );
};

export default DashboardPage;
