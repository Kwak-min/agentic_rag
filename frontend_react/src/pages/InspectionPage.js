import React, { useState, useEffect } from 'react';
import inspectionService from '../services/inspectionService';
import './InspectionPage.css';

const InspectionPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingLog, setEditingLog] = useState(null);
  const [searchLocation, setSearchLocation] = useState('');

  // 폼 상태
  const [formData, setFormData] = useState({
    location: '',
    datetime: '',
    issue_location: '',
    issue_description: '',
    inspection_action: '',
    handler: '',
  });

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await inspectionService.getInspectionLogs();
      setLogs(data);
    } catch (error) {
      console.error('점검 로그 조회 오류:', error);
      alert('점검 로그를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingLog(null);
    setFormData({
      location: '',
      datetime: new Date().toISOString().slice(0, 16),
      issue_location: '',
      issue_description: '',
      inspection_action: '',
      handler: '',
    });
    setShowModal(true);
  };

  const handleEdit = (log) => {
    setEditingLog(log);
    setFormData({
      location: log.location,
      datetime: log.datetime.slice(0, 16),
      issue_location: log.issue_location || '',
      issue_description: log.issue_description || '',
      inspection_action: log.inspection_action || '',
      handler: log.handler || '',
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;

    try {
      await inspectionService.deleteInspectionLog(id);
      loadLogs();
    } catch (error) {
      console.error('삭제 오류:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingLog) {
        await inspectionService.updateInspectionLog(editingLog.id, formData);
      } else {
        await inspectionService.createInspectionLog(formData);
      }
      setShowModal(false);
      loadLogs();
    } catch (error) {
      console.error('저장 오류:', error);
      alert('저장에 실패했습니다.');
    }
  };

  const filteredLogs = logs.filter((log) =>
    searchLocation ? log.location.includes(searchLocation) : true
  );

  return (
    <div className="inspection-page">
      <div className="page-header">
        <h1>점검 로그 관리</h1>
        <p>배수지 점검 이력을 관리합니다.</p>
      </div>

      <div className="toolbar">
        <input
          type="text"
          placeholder="장소로 검색..."
          value={searchLocation}
          onChange={(e) => setSearchLocation(e.target.value)}
          className="search-input"
        />
        <button onClick={handleCreate} className="btn btn-primary">
          ➕ 새 로그 추가
        </button>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>로딩 중...</p>
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="empty-state">
          <p>점검 로그가 없습니다.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="inspection-table">
            <thead>
              <tr>
                <th>장소</th>
                <th>일시</th>
                <th>문제 위치</th>
                <th>문제 내용</th>
                <th>점검 조치</th>
                <th>담당자</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.id}>
                  <td>{log.location}</td>
                  <td>{new Date(log.datetime).toLocaleString('ko-KR')}</td>
                  <td>{log.issue_location || '-'}</td>
                  <td className="text-truncate">{log.issue_description || '-'}</td>
                  <td className="text-truncate">{log.inspection_action || '-'}</td>
                  <td>{log.handler || '-'}</td>
                  <td>
                    <button onClick={() => handleEdit(log)} className="btn-icon" title="수정">
                      ✏️
                    </button>
                    <button onClick={() => handleDelete(log.id)} className="btn-icon" title="삭제">
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 모달 */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingLog ? '점검 로그 수정' : '점검 로그 추가'}</h2>

            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>장소 *</label>
                  <input
                    type="text"
                    required
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="예: 가곡 배수지"
                  />
                </div>

                <div className="form-group">
                  <label>일시 *</label>
                  <input
                    type="datetime-local"
                    required
                    value={formData.datetime}
                    onChange={(e) => setFormData({ ...formData, datetime: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>문제 위치</label>
                  <input
                    type="text"
                    value={formData.issue_location}
                    onChange={(e) => setFormData({ ...formData, issue_location: e.target.value })}
                    placeholder="예: 펌프 A"
                  />
                </div>

                <div className="form-group">
                  <label>담당자</label>
                  <input
                    type="text"
                    value={formData.handler}
                    onChange={(e) => setFormData({ ...formData, handler: e.target.value })}
                    placeholder="담당자 이름"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>문제 내용</label>
                <textarea
                  value={formData.issue_description}
                  onChange={(e) => setFormData({ ...formData, issue_description: e.target.value })}
                  rows={3}
                  placeholder="발견된 문제 설명"
                />
              </div>

              <div className="form-group">
                <label>점검 조치 내용</label>
                <textarea
                  value={formData.inspection_action}
                  onChange={(e) => setFormData({ ...formData, inspection_action: e.target.value })}
                  rows={3}
                  placeholder="실시한 점검 및 조치 내용"
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">
                  취소
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingLog ? '수정' : '추가'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InspectionPage;
