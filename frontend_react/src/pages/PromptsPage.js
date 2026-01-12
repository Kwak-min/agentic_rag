import React, { useState, useEffect } from 'react';
import promptService from '../services/promptService';
import { useAuth } from '../context/AuthContext';
import './PromptsPage.css';

const PromptsPage = () => {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingPrompt, setEditingPrompt] = useState(null);
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

  const handleEdit = (prompt) => {
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
      await promptService.updatePrompt(editingPrompt.prompt_type, {
        prompt_content: editContent,
        updated_by: user?.username,
      });
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

  const getPromptTypeLabel = (type) => {
    const labels = {
      function_selection: '도구 선택 프롬프트',
      response_generation: '응답 생성 프롬프트',
    };
    return labels[type] || type;
  };

  return (
    <div className="prompts-page">
      <div className="page-header">
        <div>
          <h1>시스템 프롬프트 관리</h1>
          <p>AI 시스템 프롬프트를 관리합니다. (관리자 전용)</p>
        </div>
        <button onClick={handleReload} disabled={reloading} className="btn btn-primary">
          {reloading ? '🔄 재로드 중...' : '🔄 프롬프트 재로드'}
        </button>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>로딩 중...</p>
        </div>
      ) : (
        <div className="prompts-list">
          {prompts.map((prompt) => (
            <div key={prompt.id} className="prompt-card">
              <div className="prompt-header">
                <div>
                  <h3>{getPromptTypeLabel(prompt.prompt_type)}</h3>
                  {prompt.description && <p className="description">{prompt.description}</p>}
                  <p className="meta">
                    마지막 수정: {new Date(prompt.updated_at).toLocaleString('ko-KR')}
                    {prompt.updated_by && ` by ${prompt.updated_by}`}
                  </p>
                </div>
                {editingPrompt?.id !== prompt.id && (
                  <button onClick={() => handleEdit(prompt)} className="btn btn-secondary">
                    ✏️ 수정
                  </button>
                )}
              </div>

              <div className="prompt-body">
                {editingPrompt?.id === prompt.id ? (
                  <div>
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="prompt-editor"
                      placeholder="프롬프트 내용을 입력하세요..."
                    />
                    <div className="editor-footer">
                      <button onClick={handleCancel} disabled={saving} className="btn btn-secondary">
                        취소
                      </button>
                      <button onClick={handleSave} disabled={saving} className="btn btn-primary">
                        {saving ? '저장 중...' : '💾 저장'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <pre className="prompt-content">{prompt.prompt_content}</pre>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="warning-box">
        <h4>⚠️ 주의사항</h4>
        <ul>
          <li>프롬프트 수정 후 반드시 '프롬프트 재로드' 버튼을 눌러 시스템에 적용해야 합니다.</li>
          <li>잘못된 프롬프트는 AI의 응답 품질에 영향을 줄 수 있으니 신중하게 수정하세요.</li>
          <li>프롬프트 변경 내역은 자동으로 데이터베이스에 저장됩니다.</li>
        </ul>
      </div>
    </div>
  );
};

export default PromptsPage;
