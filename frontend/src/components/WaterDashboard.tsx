'use client'

import { useState, useEffect } from 'react'
import { Droplets, TrendingUp, AlertCircle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { io, Socket } from 'socket.io-client'
import { api } from '@/utils/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

interface WaterData {
  location: string
  water_level: number
  pump_status: number
  timestamp: string
}

export default function WaterDashboard() {
  const [currentData, setCurrentData] = useState<WaterData[]>([])
  const [historyData, setHistoryData] = useState<WaterData[]>([])
  const [socket, setSocket] = useState<Socket | null>(null)

  useEffect(() => {
    // 현재 수위 조회
    fetchCurrentData()

    // 수위 이력 조회
    fetchHistoryData()

    // JWT 토큰 가져오기
    const token = localStorage.getItem('access_token')

    // WebSocket 연결 (JWT 토큰 포함)
    const newSocket = io(API_URL, {
      auth: {
        token: token
      }
    })

    newSocket.on('connect', () => {
      console.log('WebSocket 연결됨')
      newSocket.emit('water_subscribe')
    })

    newSocket.on('water_update', (data) => {
      setCurrentData(data.data)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  const fetchCurrentData = async () => {
    try {
      const data = await api.get('/api/water/current')
      setCurrentData(data.data)
    } catch (error) {
      console.error('현재 수위 조회 오류:', error)
    }
  }

  const fetchHistoryData = async () => {
    try {
      const data = await api.get('/api/water/history?hours=24')
      setHistoryData(data.data)
    } catch (error) {
      console.error('수위 이력 조회 오류:', error)
    }
  }

  const gagokData = currentData.find(d => d.location === 'gagok')
  const haeryongData = currentData.find(d => d.location === 'haeryong')

  // 그래프 데이터 가공
  const chartData = historyData.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
    [d.location]: d.water_level
  }))

  // 위치별로 그룹화
  const groupedData: any[] = []
  chartData.forEach(item => {
    const existingItem = groupedData.find(d => d.time === item.time)
    if (existingItem) {
      Object.assign(existingItem, item)
    } else {
      groupedData.push(item)
    }
  })

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">수위 모니터링</h1>
        <p className="text-gray-500 mt-1">실시간 배수지 수위 현황</p>
      </div>

      {/* Current Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* 가곡 배수지 */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Droplets className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">가곡 배수지</h3>
                <p className="text-sm text-gray-500">Gagok Reservoir</p>
              </div>
            </div>
            {gagokData && gagokData.pump_status > 0 && (
              <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                펌프 ON
              </span>
            )}
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500">현재 수위</p>
              <p className="text-4xl font-bold text-gray-900">
                {gagokData ? gagokData.water_level.toFixed(1) : '--'}
                <span className="text-xl text-gray-500 ml-2">m</span>
              </p>
            </div>
            <div className="pt-3 border-t border-gray-200">
              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-gray-600">마지막 업데이트:</span>
                <span className="text-gray-900">
                  {gagokData ? new Date(gagokData.timestamp).toLocaleTimeString('ko-KR') : '--'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 해룡 배수지 */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Droplets className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">해룡 배수지</h3>
                <p className="text-sm text-gray-500">Haeryong Reservoir</p>
              </div>
            </div>
            {haeryongData && haeryongData.pump_status > 0 && (
              <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                펌프 ON
              </span>
            )}
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500">현재 수위</p>
              <p className="text-4xl font-bold text-gray-900">
                {haeryongData ? haeryongData.water_level.toFixed(1) : '--'}
                <span className="text-xl text-gray-500 ml-2">m</span>
              </p>
            </div>
            <div className="pt-3 border-t border-gray-200">
              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-gray-600">마지막 업데이트:</span>
                <span className="text-gray-900">
                  {haeryongData ? new Date(haeryongData.timestamp).toLocaleTimeString('ko-KR') : '--'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 수위 그래프 */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">24시간 수위 추이</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={groupedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis label={{ value: '수위 (m)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="gagok" stroke="#3B82F6" name="가곡" strokeWidth={2} />
            <Line type="monotone" dataKey="haeryong" stroke="#8B5CF6" name="해룡" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 경고 정보 */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-yellow-900">위험 수위 알림</h4>
            <p className="text-sm text-yellow-800 mt-1">
              수위가 70m를 초과하면 자동으로 알림이 발송됩니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
