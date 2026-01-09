'use client'

import { useState } from 'react'
import { Activity, Power, AlertTriangle, Settings, CheckCircle } from 'lucide-react'

export default function AutomationDashboard() {
  const [automationActive, setAutomationActive] = useState(false)
  const [autonomousMonitoring, setAutonomousMonitoring] = useState(false)

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">통합 자동화 시스템</h1>
        <p className="text-gray-500 mt-1">자동화 및 자율 에이전트 관리</p>
      </div>

      {/* 자동화 제어 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* 펌프 자동화 */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                <Power className="w-6 h-6 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">펌프 자동화</h3>
                <p className="text-sm text-gray-500">수위 기반 자동 제어</p>
              </div>
            </div>
            <div
              className={`w-12 h-7 rounded-full cursor-pointer transition-colors ${
                automationActive ? 'bg-green-500' : 'bg-gray-300'
              }`}
              onClick={() => setAutomationActive(!automationActive)}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transition-transform mt-1 ${
                  automationActive ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">상태</span>
              <span className={`font-medium ${automationActive ? 'text-green-600' : 'text-gray-500'}`}>
                {automationActive ? '활성화' : '비활성화'}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">위험 수위</span>
              <span className="font-medium text-gray-900">70.0m</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">점검 주기</span>
              <span className="font-medium text-gray-900">30초</span>
            </div>
          </div>
        </div>

        {/* 자율 에이전트 */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">자율 에이전트</h3>
                <p className="text-sm text-gray-500">AI 기반 모니터링</p>
              </div>
            </div>
            <div
              className={`w-12 h-7 rounded-full cursor-pointer transition-colors ${
                autonomousMonitoring ? 'bg-green-500' : 'bg-gray-300'
              }`}
              onClick={() => setAutonomousMonitoring(!autonomousMonitoring)}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transition-transform mt-1 ${
                  autonomousMonitoring ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">상태</span>
              <span className={`font-medium ${autonomousMonitoring ? 'text-green-600' : 'text-gray-500'}`}>
                {autonomousMonitoring ? '모니터링 중' : '대기 중'}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">마지막 분석</span>
              <span className="font-medium text-gray-900">--</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">분석 주기</span>
              <span className="font-medium text-gray-900">1분</span>
            </div>
          </div>
        </div>
      </div>

      {/* 통합 상태 */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5" />
          통합 자동화 상태
        </h3>
        <div className="space-y-3">
          {automationActive && autonomousMonitoring ? (
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="font-medium text-green-900">완전 활성 상태</p>
                <p className="text-sm text-green-700">모든 자동화 시스템이 정상 작동 중입니다</p>
              </div>
            </div>
          ) : automationActive || autonomousMonitoring ? (
            <div className="flex items-center gap-3 p-4 bg-yellow-50 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <div>
                <p className="font-medium text-yellow-900">부분 활성 상태</p>
                <p className="text-sm text-yellow-700">일부 자동화 기능만 활성화되어 있습니다</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
              <Power className="w-5 h-5 text-gray-600" />
              <div>
                <p className="font-medium text-gray-900">비활성 상태</p>
                <p className="text-sm text-gray-600">자동화 시스템이 비활성화되어 있습니다</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 로그 */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">자동화 로그</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm">
            <span className="text-gray-600">시스템 대기 중...</span>
            <span className="text-gray-500">
              {new Date().toLocaleTimeString('ko-KR')}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
