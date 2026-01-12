'use client'

import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import ChatInterface from '@/components/ChatInterface'
import WaterDashboard from '@/components/WaterDashboard'
import AutomationDashboard from '@/components/AutomationDashboard'
import InspectionLogDashboard from '@/components/InspectionLogDashboard'
import KakaoLogParser from '@/components/KakaoLogParser'

export default function Home() {
  const [currentPage, setCurrentPage] = useState<'chat' | 'water' | 'automation' | 'inspection' | 'kakao'>('chat')
  const [systemInitialized, setSystemInitialized] = useState(false)

  return (
    <div className="flex h-screen bg-gradient-to-br from-indigo-50 to-purple-50">
      {/* Sidebar */}
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        systemInitialized={systemInitialized}
        setSystemInitialized={setSystemInitialized}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {currentPage === 'chat' && <ChatInterface systemInitialized={systemInitialized} />}
        {currentPage === 'water' && <WaterDashboard />}
        {currentPage === 'automation' && <AutomationDashboard />}
        {currentPage === 'inspection' && <InspectionLogDashboard />}
        {currentPage === 'kakao' && <KakaoLogParser />}
      </main>
    </div>
  )
}
