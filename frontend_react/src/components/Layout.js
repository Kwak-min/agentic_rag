import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

const Layout = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    { path: '/dashboard', label: '대시보드', icon: '📊' },
    { path: '/chat', label: 'AI 챗봇', icon: '💬' },
    { path: '/inspection', label: '점검 로그', icon: '📝' },
    { path: '/anomaly', label: '이상 탐지 모니터링', icon: '🚨' },
    { path: '/anomaly/test', label: '이상 탐지 테스트', icon: '🧪' },
  ];

  if (isAdmin()) {
    menuItems.push(
      { path: '/prompts', label: '프롬프트 관리', icon: '⚙️' },
      { path: '/settings', label: '설정', icon: '🔧' }
    );
  }

  return (
    <div className="layout">
      {/* 사이드바 */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>Synergy</h2>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="toggle-btn">
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {sidebarOpen && <span className="nav-label">{item.label}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            {sidebarOpen && (
              <>
                <p className="user-name">{user?.name || user?.username}</p>
                <p className="user-role">{user?.role === 'admin' ? '관리자' : '사용자'}</p>
              </>
            )}
          </div>
          <button onClick={handleLogout} className="logout-btn">
            🚪 {sidebarOpen && '로그아웃'}
          </button>
        </div>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className={`main-content ${sidebarOpen ? 'with-sidebar' : 'full-width'}`}>
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
