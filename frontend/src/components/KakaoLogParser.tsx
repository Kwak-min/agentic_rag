'use client'

import { useState } from 'react'
import { MessageSquare, Wand2, AlertCircle, CheckCircle } from 'lucide-react'
import { api } from '@/utils/api'

interface ParsedLog {
  location?: string
  datetime?: string
  issue_location?: string
  issue_description?: string
  inspection_action?: string
  handler?: string
  confidence: number
  missing_fields: string[]
}

export default function KakaoLogParser() {
  const [kakaoText, setKakaoText] = useState('')
  const [parsing, setParsing] = useState(false)
  const [parsedLogs, setParsedLogs] = useState<ParsedLog[]>([])
  const [currentLogIndex, setCurrentLogIndex] = useState(0)
  const [editingLog, setEditingLog] = useState<any>(null)
  const [saveResult, setSaveResult] = useState<any>(null)

  const handleParse = async () => {
    if (!kakaoText.trim()) {
      alert('카카오톡 메시지를 입력해주세요')
      return
    }

    setParsing(true)
    setSaveResult(null)
    try {
      const response = await api.post('/api/parse-kakao-log', {
        kakao_text: kakaoText,
        auto_save: true
      })

      if (response.success) {
        if (response.auto_saved) {
          // 자동 저장 완료
          setSaveResult({
            saved_count: response.saved_count,
            failed_count: response.failed_count,
            saved_logs: response.saved_logs,
            failed_logs: response.failed_logs
          })

          if (response.saved_count > 0) {
            alert(`✅ ${response.saved_count}개의 점검 로그가 자동으로 저장되었습니다!`)
          }

          if (response.failed_count > 0) {
            alert(`⚠️ ${response.failed_count}개의 로그 저장에 실패했습니다. 결과를 확인해주세요.`)
          }
        } else if (response.logs && response.logs.length > 0) {
          // 기존 수동 방식
          setParsedLogs(response.logs)
          setCurrentLogIndex(0)
          setEditingLog(response.logs[0])
        } else {
          alert('메시지에서 점검 로그를 추출할 수 없습니다')
        }
      } else {
        alert('메시지에서 점검 로그를 추출할 수 없습니다')
      }
    } catch (error) {
      console.error('파싱 오류:', error)
      alert('메시지 분석 중 오류가 발생했습니다')
    } finally {
      setParsing(false)
    }
  }

  const handleSaveLog = async () => {
    // 필수 필드 검증
    const requiredFields = ['location', 'datetime', 'issue_location', 'issue_description', 'inspection_action', 'handler']
    const missingFields = requiredFields.filter(field => !editingLog[field] || editingLog[field].trim() === '')

    if (missingFields.length > 0) {
      alert(`다음 필드를 입력해주세요: ${missingFields.join(', ')}`)
      return
    }

    try {
      await api.post('/api/inspection-logs', editingLog)
      alert('점검 로그가 저장되었습니다')

      // 다음 로그로 이동
      if (currentLogIndex < parsedLogs.length - 1) {
        const nextIndex = currentLogIndex + 1
        setCurrentLogIndex(nextIndex)
        setEditingLog(parsedLogs[nextIndex])
      } else {
        // 모든 로그 저장 완료
        alert(`총 ${parsedLogs.length}개의 로그가 저장되었습니다`)
        setKakaoText('')
        setParsedLogs([])
        setEditingLog(null)
        setCurrentLogIndex(0)
      }
    } catch (error) {
      console.error('저장 오류:', error)
      alert('로그 저장 중 오류가 발생했습니다')
    }
  }

  const handleSkip = () => {
    if (currentLogIndex < parsedLogs.length - 1) {
      const nextIndex = currentLogIndex + 1
      setCurrentLogIndex(nextIndex)
      setEditingLog(parsedLogs[nextIndex])
    } else {
      alert('모든 로그 검토가 완료되었습니다')
      setKakaoText('')
      setParsedLogs([])
      setEditingLog(null)
      setCurrentLogIndex(0)
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">카톡 메시지 자동 분석</h1>
        <p className="text-gray-500 mt-1">카카오톡 메시지를 붙여넣으면 AI가 자동으로 점검 로그를 추출합니다</p>
      </div>

      {!editingLog && !saveResult ? (
        // 입력 단계
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare className="w-5 h-5 text-indigo-600" />
            <h2 className="text-xl font-semibold text-gray-900">카카오톡 메시지 입력</h2>
          </div>

          <textarea
            value={kakaoText}
            onChange={(e) => setKakaoText(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            rows={15}
            placeholder="카카오톡 대화 내용을 여기에 붙여넣으세요...&#10;&#10;예시:&#10;[오전 10:23] 김철수: 가곡 배수지 펌프 A 이상 소리 남&#10;[오전 10:25] 이영희: 확인했습니다. 베어링 마모로 보입니다&#10;[오전 11:00] 김철수: 교체 완료했습니다"
          />

          <div className="mt-4 flex justify-end">
            <button
              onClick={handleParse}
              disabled={parsing || !kakaoText.trim()}
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              <Wand2 className={`w-5 h-5 ${parsing ? 'animate-spin' : ''}`} />
              <span className="font-medium">{parsing ? 'AI 분석 중...' : 'AI로 자동 분석'}</span>
            </button>
          </div>

          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">사용 팁:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>여러 개의 점검 내용이 있어도 한번에 붙여넣으세요</li>
                  <li>날짜, 시간, 장소, 문제 내용, 조치 내용이 포함되면 더 정확합니다</li>
                  <li>AI가 자동으로 분석하여 자동으로 데이터베이스에 저장합니다</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ) : saveResult ? (
        // 자동 저장 결과 표시
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <h2 className="text-xl font-semibold text-gray-900">자동 저장 완료</h2>
            </div>

            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium">
                총 {saveResult.saved_count}개의 점검 로그가 자동으로 저장되었습니다!
              </p>
              {saveResult.failed_count > 0 && (
                <p className="text-red-600 mt-2">
                  {saveResult.failed_count}개의 로그 저장에 실패했습니다.
                </p>
              )}
            </div>

            {/* 저장된 로그 목록 */}
            {saveResult.saved_logs && saveResult.saved_logs.length > 0 && (
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900 mb-2">저장된 로그:</h3>
                {saveResult.saved_logs.map((log: any, index: number) => (
                  <div key={index} className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">장소:</span> {log.location}
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">일시:</span> {new Date(log.datetime).toLocaleString('ko-KR')}
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">문제 부위:</span> {log.issue_location}
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">처리자:</span> {log.handler}
                      </div>
                      <div className="col-span-2">
                        <span className="font-medium text-gray-700">문제:</span> {log.issue_description}
                      </div>
                      <div className="col-span-2">
                        <span className="font-medium text-gray-700">조치:</span> {log.inspection_action}
                      </div>
                      <div className="col-span-2">
                        <span className="text-xs text-gray-500">신뢰도: {Math.round(log.confidence * 100)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => {
                  setSaveResult(null)
                  setKakaoText('')
                }}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                새로운 메시지 분석
              </button>
            </div>
          </div>
        </div>
      ) : editingLog ? (
        // 편집 단계
        <div className="space-y-4">
          {/* 진행 상황 */}
          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-gray-700">
                  진행 상황: {currentLogIndex + 1} / {parsedLogs.length}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                AI 신뢰도: {Math.round(editingLog.confidence * 100)}%
              </span>
            </div>
          </div>

          {/* 편집 폼 */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">점검 로그 확인 및 수정</h2>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    장소 {!editingLog.location && <span className="text-red-600">*필수</span>}
                  </label>
                  <input
                    type="text"
                    value={editingLog.location || ''}
                    onChange={(e) => setEditingLog({ ...editingLog, location: e.target.value })}
                    className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                      !editingLog.location ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="예: 가곡 배수지"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    일시 {!editingLog.datetime && <span className="text-red-600">*필수</span>}
                  </label>
                  <input
                    type="datetime-local"
                    value={editingLog.datetime || ''}
                    onChange={(e) => setEditingLog({ ...editingLog, datetime: e.target.value })}
                    className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                      !editingLog.datetime ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    문제 부위 {!editingLog.issue_location && <span className="text-red-600">*필수</span>}
                  </label>
                  <input
                    type="text"
                    value={editingLog.issue_location || ''}
                    onChange={(e) => setEditingLog({ ...editingLog, issue_location: e.target.value })}
                    className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                      !editingLog.issue_location ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="예: 펌프 A, 센서, 배관"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    처리자 {!editingLog.handler && <span className="text-red-600">*필수</span>}
                  </label>
                  <input
                    type="text"
                    value={editingLog.handler || ''}
                    onChange={(e) => setEditingLog({ ...editingLog, handler: e.target.value })}
                    className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                      !editingLog.handler ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="담당자 이름"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  문제 {!editingLog.issue_description && <span className="text-red-600">*필수</span>}
                </label>
                <textarea
                  value={editingLog.issue_description || ''}
                  onChange={(e) => setEditingLog({ ...editingLog, issue_description: e.target.value })}
                  className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                    !editingLog.issue_description ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  rows={3}
                  placeholder="발견된 문제를 상세히 기록해주세요"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  점검 조치 {!editingLog.inspection_action && <span className="text-red-600">*필수</span>}
                </label>
                <textarea
                  value={editingLog.inspection_action || ''}
                  onChange={(e) => setEditingLog({ ...editingLog, inspection_action: e.target.value })}
                  className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                    !editingLog.inspection_action ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  rows={3}
                  placeholder="실시한 점검 및 조치 내용을 상세히 기록해주세요"
                />
              </div>
            </div>

            <div className="mt-6 flex gap-3 justify-end">
              <button
                onClick={() => {
                  setEditingLog(null)
                  setParsedLogs([])
                  setCurrentLogIndex(0)
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleSkip}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                건너뛰기
              </button>
              <button
                onClick={handleSaveLog}
                className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                저장 {currentLogIndex < parsedLogs.length - 1 && '후 다음'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
