import api from './api';
import { SystemPrompt, SystemPromptUpdate } from '../types';

class PromptService {
  /**
   * 시스템 프롬프트 목록 조회 (관리자만)
   */
  async getPrompts(): Promise<SystemPrompt[]> {
    const response = await api.get<SystemPrompt[]>('/api/prompts');
    return response.data;
  }

  /**
   * 시스템 프롬프트 수정 (관리자만)
   */
  async updatePrompt(promptType: string, data: SystemPromptUpdate): Promise<SystemPrompt> {
    const response = await api.put<SystemPrompt>(`/api/prompts/${promptType}`, data);
    return response.data;
  }

  /**
   * 프롬프트 재로드 (관리자만)
   */
  async reloadPrompts(): Promise<{ success: boolean; message: string }> {
    const response = await api.post<{ success: boolean; message: string }>('/api/prompts/reload');
    return response.data;
  }
}

export default new PromptService();
