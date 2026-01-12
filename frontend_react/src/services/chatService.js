import api from './api';

class ChatService {
  /**
   * 채팅 메시지 전송 (비스트리밍)
   */
  async sendMessage(message) {
    const response = await api.post('/api/chat', { message });
    return response.data;
  }

  /**
   * 시스템 상태 조회
   */
  async getSystemStatus() {
    const response = await api.get('/api/system/status');
    return response.data;
  }

  /**
   * 시스템 초기화
   */
  async initializeSystem() {
    const response = await api.post('/api/initialize');
    return response.data;
  }
}

export default new ChatService();
