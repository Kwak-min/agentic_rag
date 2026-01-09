'use client'

import { useState } from 'react'
import { MessageCircle, Droplets, Settings, RefreshCw, Activity, CheckCircle, XCircle, Circle, LogOut, FileText, Sparkles } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/utils/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

interface SidebarProps {
  currentPage: 'chat' | 'water' | 'automation' | 'inspection' | 'kakao'
  setCurrentPage: (page: 'chat' | 'water' | 'automation' | 'inspection' | 'kakao') => void
  systemInitialized: boolean
  setSystemInitialized: (initialized: boolean) => void
}

export default function Sidebar({ currentPage, setCurrentPage, systemInitialized, setSystemInitialized }: SidebarProps) {
  const [initializing, setInitializing] = useState(false)
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'unknown'>('unknown')
  const { user, logout } = useAuth()

  const handleInitialize = async () => {
    setInitializing(true)
    try {
      const data = await api.post('/api/initialize', {}, false)
      if (data.success) {
        setSystemInitialized(true)
        setApiStatus('connected')
        alert('시스템 초기화 성공!')
      } else {
        alert('시스템 초기화 실패')
      }
    } catch (error) {
      console.error('초기화 오류:', error)
      alert('시스템 초기화 중 오류 발생')
      setApiStatus('disconnected')
    } finally {
      setInitializing(false)
    }
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white text-xl font-bold">S</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Synergy</h1>
            <p className="text-xs text-gray-500">ChatBot</p>
          </div>
        </div>

        {/* User Info & Logout */}
        {user && (
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
              <p className="text-xs text-gray-500 truncate">@{user.username}</p>
            </div>
            <button
              onClick={logout}
              className="ml-2 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="로그아웃"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* System Control */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">시스템 제어</h2>
        <button
          onClick={handleInitialize}
          disabled={initializing}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${initializing ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium">
            {initializing ? '초기화 중...' : '시스템 초기화'}
          </span>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        <button
          onClick={() => setCurrentPage('chat')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            currentPage === 'chat'
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          <MessageCircle className="w-5 h-5" />
          <span className="font-medium">채팅</span>
        </button>

        <button
          onClick={() => setCurrentPage('water')}
          disabled={!systemInitialized}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            currentPage === 'water'
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-700 hover:bg-gray-50'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <Droplets className="w-5 h-5" />
          <span className="font-medium">수위 대시보드</span>
        </button>

        <button
          onClick={() => setCurrentPage('automation')}
          disabled={!systemInitialized}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            currentPage === 'automation'
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-700 hover:bg-gray-50'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <Activity className="w-5 h-5" />
          <span className="font-medium">통합 자동화 시스템</span>
        </button>

        <button
          onClick={() => setCurrentPage('inspection')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            currentPage === 'inspection'
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          <FileText className="w-5 h-5" />
          <span className="font-medium">점검 로그</span>
        </button>

        <button
          onClick={() => setCurrentPage('kakao')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            currentPage === 'kakao'
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          <Sparkles className="w-5 h-5" />
          <span className="font-medium">카톡 자동 분석</span>
        </button>
      </nav>

      {/* Status */}
      <div className="p-4 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">모델 / 연결 상태</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">API</span>
            <div className="flex items-center gap-1">
              {apiStatus === 'connected' && (
                <>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-green-700">연결됨</span>
                </>
              )}
              {apiStatus === 'disconnected' && (
                <>
                  <XCircle className="w-4 h-4 text-red-500" />
                  <span className="text-red-700">연결 안됨</span>
                </>
              )}
              {apiStatus === 'unknown' && (
                <>
                  <Circle className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-500">알 수 없음</span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">아두이노</span>
            <div className="flex items-center gap-1">
              <Circle className="w-4 h-4 text-gray-400" />
              <span className="text-gray-500">시뮬레이션</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">자동화</span>
            <div className="flex items-center gap-1">
              <Circle className="w-4 h-4 text-gray-400" />
              <span className="text-gray-500">비활성</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
