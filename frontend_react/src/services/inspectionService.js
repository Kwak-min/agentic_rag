import api from './api';

class InspectionService {
  /**
   * 점검 로그 목록 조회
   */
  async getInspectionLogs(params = {}) {
    const response = await api.get('/api/inspection-logs', { params });
    return response.data.data || [];
  }

  /**
   * 점검 로그 생성
   */
  async createInspectionLog(data) {
    const response = await api.post('/api/inspection-logs', data);
    return response.data;
  }

  /**
   * 점검 로그 수정
   */
  async updateInspectionLog(id, data) {
    const response = await api.put(`/api/inspection-logs/${id}`, data);
    return response.data;
  }

  /**
   * 점검 로그 삭제
   */
  async deleteInspectionLog(id) {
    await api.delete(`/api/inspection-logs/${id}`);
  }
}

export default new InspectionService();
