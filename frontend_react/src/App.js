import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import InspectionPage from './pages/InspectionPage';
import PromptsPage from './pages/PromptsPage';
import AnomalyMonitoring from './pages/AnomalyMonitoring';
import AnomalyTest from './pages/AnomalyTest';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* 로그인 페이지 */}
          <Route path="/login" element={<LoginPage />} />

          {/* 보호된 라우트 (레이아웃 포함) */}
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
            <Route path="inspection" element={<InspectionPage />} />

            {/* RNN-LSTM 이상 탐지 페이지 */}
            <Route path="anomaly" element={<AnomalyMonitoring />} />
            <Route path="anomaly/test" element={<AnomalyTest />} />

            {/* 관리자 전용 */}
            <Route
              path="prompts"
              element={
                <ProtectedRoute adminOnly>
                  <PromptsPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* 404 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
