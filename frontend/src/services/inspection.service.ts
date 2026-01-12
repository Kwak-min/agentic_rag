import api from './api';
import { InspectionLog, InspectionLogInput } from '../types';

class InspectionService {
  /**
   * 점검 로그 목록 조회
   */
  async getInspectionLogs(params?: {
    location?: string;
    work_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<InspectionLog[]> {
    const response = await api.get<InspectionLog[]>('/api/inspection-logs', {
      params,
    });
    return response.data;
  }

  /**
   * 점검 로그 상세 조회
   */
  async getInspectionLog(id: number): Promise<InspectionLog> {
    const response = await api.get<InspectionLog>(`/api/inspection-logs/${id}`);
    return response.data;
  }

  /**
   * 점검 로그 생성
   */
  async createInspectionLog(data: InspectionLogInput): Promise<InspectionLog> {
    const response = await api.post<InspectionLog>('/api/inspection-logs', data);
    return response.data;
  }

  /**
   * 점검 로그 수정
   */
  async updateInspectionLog(id: number, data: Partial<InspectionLogInput>): Promise<InspectionLog> {
    const response = await api.put<InspectionLog>(`/api/inspection-logs/${id}`, data);
    return response.data;
  }

  /**
   * 점검 로그 삭제
   */
  async deleteInspectionLog(id: number): Promise<void> {
    await api.delete(`/api/inspection-logs/${id}`);
  }

  /**
   * 카카오톡 메시지 파싱 (향후 구현)
   */
  async parseKakaoMessage(message: string): Promise<InspectionLogInput> {
    const response = await api.post<InspectionLogInput>('/api/parse-kakao', {
      message,
    });
    return response.data;
  }
}

export default new InspectionService();
