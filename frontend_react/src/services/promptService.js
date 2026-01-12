import api from './api';

class PromptService {
  /**
   * 시스템 프롬프트 목록 조회
   */
  async getPrompts() {
    const response = await api.get('/api/prompts');
    return response.data.prompts || [];
  }

  /**
   * 시스템 프롬프트 수정
   */
  async updatePrompt(promptType, data) {
    const response = await api.put(`/api/prompts/${promptType}`, data);
    return response.data;
  }

  /**
   * 시스템 프롬프트 재로드
   */
  async reloadPrompts() {
    const response = await api.post('/api/prompts/reload');
    return response.data;
  }
}

export default new PromptService();
