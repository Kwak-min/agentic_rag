import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import InspectionPage from './pages/InspectionPage';
import PromptsPage from './pages/PromptsPage';
import AnomalyMonitoringPage from './pages/AnomalyMonitoringPage';

// 추후 구현할 페이지들 (임시 컴포넌트)
const ChatPage = () => <div className="p-6"><h1 className="text-3xl font-bold">AI 챗봇</h1></div>;
const WaterPage = () => <div className="p-6"><h1 className="text-3xl font-bold">수위 모니터링</h1></div>;
const SettingsPage = () => <div className="p-6"><h1 className="text-3xl font-bold">설정</h1></div>;

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* 로그인 페이지 */}
          <Route path="/login" element={<LoginPage />} />

          {/* 보호된 라우트 */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="water" element={<WaterPage />} />
            <Route path="inspection" element={<InspectionPage />} />
            <Route path="anomaly" element={<AnomalyMonitoringPage />} />

            {/* 관리자 전용 라우트 */}
            <Route
              path="prompts"
              element={
                <ProtectedRoute adminOnly>
                  <PromptsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="settings"
              element={
                <ProtectedRoute adminOnly>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* 404 페이지 */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
