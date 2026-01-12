import React, { useState, useEffect } from 'react';
import promptService from '../services/prompt.service';
import { SystemPrompt, SystemPromptUpdate } from '../types';
import { Save, RefreshCw, Edit, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const PromptsPage: React.FC = () => {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPrompt, setEditingPrompt] = useState<SystemPrompt | null>(null);
  const [editContent, setEditContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [reloading, setReloading] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      setLoading(true);
      const data = await promptService.getPrompts();
      setPrompts(data);
    } catch (error) {
      console.error('프롬프트 조회 오류:', error);
      alert('프롬프트를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (prompt: SystemPrompt) => {
    setEditingPrompt(prompt);
    setEditContent(prompt.prompt_content);
  };

  const handleCancel = () => {
    setEditingPrompt(null);
    setEditContent('');
  };

  const handleSave = async () => {
    if (!editingPrompt) return;

    try {
      setSaving(true);
      const updateData: SystemPromptUpdate = {
        prompt_content: editContent,
        updated_by: user?.username,
      };
      await promptService.updatePrompt(editingPrompt.prompt_type, updateData);
      alert('프롬프트가 성공적으로 수정되었습니다.');
      handleCancel();
      loadPrompts();
    } catch (error) {
      console.error('프롬프트 수정 오류:', error);
      alert('프롬프트 수정에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleReload = async () => {
    if (!window.confirm('시스템 프롬프트를 다시 로드하시겠습니까?')) return;

    try {
      setReloading(true);
      const result = await promptService.reloadPrompts();
      if (result.success) {
        alert('프롬프트가 성공적으로 재로드되었습니다.');
      } else {
        alert('프롬프트 재로드에 실패했습니다.');
      }
    } catch (error) {
      console.error('프롬프트 재로드 오류:', error);
      alert('프롬프트 재로드에 실패했습니다.');
    } finally {
      setReloading(false);
    }
  };

  const getPromptTypeLabel = (type: string): string => {
    const labels: { [key: string]: string } = {
      function_selection: '도구 선택 프롬프트',
      response_generation: '응답 생성 프롬프트',
    };
    return labels[type] || type;
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">시스템 프롬프트 관리</h1>
          <p className="text-gray-600 mt-2">AI 시스템 프롬프트를 관리합니다. (관리자 전용)</p>
        </div>
        <button
          onClick={handleReload}
          disabled={reloading}
          className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:bg-gray-400"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${reloading ? 'animate-spin' : ''}`} />
          {reloading ? '재로드 중...' : '프롬프트 재로드'}
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {prompts.map((prompt) => (
            <div key={prompt.id} className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {getPromptTypeLabel(prompt.prompt_type)}
                  </h3>
                  {prompt.description && (
                    <p className="text-sm text-gray-600 mt-1">{prompt.description}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-2">
                    마지막 수정: {new Date(prompt.updated_at).toLocaleString('ko-KR')}
                    {prompt.updated_by && ` by ${prompt.updated_by}`}
                  </p>
                </div>
                {editingPrompt?.id !== prompt.id && (
                  <button
                    onClick={() => handleEdit(prompt)}
                    className="flex items-center px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    수정
                  </button>
                )}
              </div>

              <div className="p-4">
                {editingPrompt?.id === prompt.id ? (
                  <div>
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full h-96 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      placeholder="프롬프트 내용을 입력하세요..."
                    />
                    <div className="flex justify-end gap-2 mt-4">
                      <button
                        onClick={handleCancel}
                        disabled={saving}
                        className="flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:bg-gray-100"
                      >
                        <X className="w-4 h-4 mr-2" />
                        취소
                      </button>
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:bg-gray-400"
                      >
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? '저장 중...' : '저장'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700 bg-gray-50 p-4 rounded-lg overflow-x-auto">
                    {prompt.prompt_content}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && prompts.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-600">등록된 프롬프트가 없습니다.</p>
        </div>
      )}

      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="font-semibold text-yellow-900 mb-2">주의사항</h4>
        <ul className="text-sm text-yellow-800 space-y-1">
          <li>• 프롬프트 수정 후 반드시 '프롬프트 재로드' 버튼을 눌러 시스템에 적용해야 합니다.</li>
          <li>• 잘못된 프롬프트는 AI의 응답 품질에 영향을 줄 수 있으니 신중하게 수정하세요.</li>
          <li>• 프롬프트 변경 내역은 자동으로 데이터베이스에 저장됩니다.</li>
        </ul>
      </div>
    </div>
  );
};

export default PromptsPage;
