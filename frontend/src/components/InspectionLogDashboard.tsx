'use client'

import { useState, useEffect } from 'react'
import { FileText, Plus, Trash2, Calendar, MapPin, AlertCircle } from 'lucide-react'
import { api } from '@/utils/api'

interface InspectionLog {
  id: number
  location: string
  datetime: string
  issue_location: string
  issue_description: string
  inspection_action: string
  handler: string
  created_at: string
}

export default function InspectionLogDashboard() {
  const [logs, setLogs] = useState<InspectionLog[]>([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    location: '',
    datetime: '',
    issue_location: '',
    issue_description: '',
    inspection_action: '',
    handler: ''
  })

  useEffect(() => {
    fetchLogs()
  }, [])

  const fetchLogs = async () => {
    try {
      const data = await api.get('/api/inspection-logs')
      setLogs(data.data)
    } catch (error) {
      console.error('로그 조회 오류:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/inspection-logs', formData)
      setFormData({
        location: '',
        datetime: '',
        issue_location: '',
        issue_description: '',
        inspection_action: '',
        handler: ''
      })
      setShowForm(false)
      fetchLogs()
      alert('점검 로그가 저장되었습니다')
    } catch (error) {
      console.error('로그 저장 오류:', error)
      alert('로그 저장 중 오류가 발생했습니다')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('이 로그를 삭제하시겠습니까?')) return

    try {
      await api.delete(`/api/inspection-logs/${id}`)
      fetchLogs()
      alert('로그가 삭제되었습니다')
    } catch (error) {
      console.error('로그 삭제 오류:', error)
      alert('로그 삭제 중 오류가 발생했습니다')
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">점검 로그</h1>
          <p className="text-gray-500 mt-1">시설 점검 및 조치 이력 관리</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span className="font-medium">새 로그 작성</span>
        </button>
      </div>

      {/* 입력 폼 */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">점검 로그 작성</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  장소
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="예: 가곡 배수지"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  일시
                </label>
                <input
                  type="datetime-local"
                  value={formData.datetime}
                  onChange={(e) => setFormData({ ...formData, datetime: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  문제 부위
                </label>
                <input
                  type="text"
                  value={formData.issue_location}
                  onChange={(e) => setFormData({ ...formData, issue_location: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="예: 펌프 A, 센서, 배관"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  처리자
                </label>
                <input
                  type="text"
                  value={formData.handler}
                  onChange={(e) => setFormData({ ...formData, handler: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="담당자 이름"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                문제
              </label>
              <textarea
                value={formData.issue_description}
                onChange={(e) => setFormData({ ...formData, issue_description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                rows={3}
                placeholder="발견된 문제를 상세히 기록해주세요"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                점검 조치
              </label>
              <textarea
                value={formData.inspection_action}
                onChange={(e) => setFormData({ ...formData, inspection_action: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                rows={3}
                placeholder="실시한 점검 및 조치 내용을 상세히 기록해주세요"
                required
              />
            </div>

            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                취소
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                저장
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 로그 테이블 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  장소
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  일시
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  문제 부위
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  문제
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  점검 조치
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  처리자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  작업
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                    <p>등록된 점검 로그가 없습니다</p>
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">{log.location}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-900">
                          {new Date(log.datetime).toLocaleString('ko-KR')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-orange-500" />
                        <span className="text-sm text-gray-900">{log.issue_location}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs">
                        {log.issue_description && log.issue_description.length > 80
                          ? log.issue_description.substring(0, 80) + '...'
                          : log.issue_description || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs">
                        {log.inspection_action && log.inspection_action.length > 80
                          ? log.inspection_action.substring(0, 80) + '...'
                          : log.inspection_action || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                        {log.handler}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleDelete(log.id)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                        title="삭제"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
