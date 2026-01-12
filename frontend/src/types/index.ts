// 사용자 타입
export interface User {
  id: number;
  username: string;
  role: 'admin' | 'user';
  name: string;
}

// 로그인 응답
export interface LoginResponse {
  access_token: string;
  user: User;
}

// 점검 로그 타입
export interface InspectionLog {
  id: number;
  location: string;
  datetime: string;
  issue_location?: string;
  issue_description?: string;
  inspection_action?: string;
  handler?: string;
  work_type?: string;
  created_at: string;
}

// 점검 로그 생성/수정 타입
export interface InspectionLogInput {
  location: string;
  datetime: string;
  issue_location?: string;
  issue_description?: string;
  inspection_action?: string;
  handler?: string;
  work_type?: string;
}

// 시스템 프롬프트 타입
export interface SystemPrompt {
  id: number;
  prompt_type: string;
  prompt_content: string;
  description?: string;
  updated_by?: string;
  updated_at: string;
}

// 시스템 프롬프트 업데이트 타입
export interface SystemPromptUpdate {
  prompt_content: string;
  updated_by?: string;
}

// 채팅 메시지 타입
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// 수위 데이터 타입
export interface WaterData {
  measured_at: string;
  gagok_water_level?: number;
  gagok_pump_a?: number;
  gagok_pump_b?: number;
  haeryong_water_level?: number;
  haeryong_pump_a?: number;
  haeryong_pump_b?: number;
  sangsa_water_level?: number;
  sangsa_pump_a?: number;
  sangsa_pump_b?: number;
  sangsa_pump_c?: number;
}

// API 오류 응답
export interface ApiError {
  error: string;
  message?: string;
}
