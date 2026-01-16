# LSTM 기반 수위 이상 탐지 시스템

## 📌 개요

이 시스템은 **RNN-LSTM 모델**을 사용하여 배수지 수위 데이터의 이상을 실시간으로 탐지하고, 과거 유지보수 이력을 바탕으로 AI가 원인을 진단하는 통합 시스템입니다.

### 주요 기능

1. **LSTM 수위 예측**: 과거 60분 데이터로 다음 수위 예측
2. **실시간 이상 탐지**: 예측값 vs 실제값 비교로 이상 판정
3. **AI 진단**: 유지보수 이력 RAG 검색으로 원인 분석 및 조치사항 추천
4. **React 모니터링 화면**: 실시간 상태 모니터링 및 진단
5. **테스트 인터페이스**: 임의 데이터로 이상 탐지 테스트

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     엑셀 데이터                               │
│  ┌────────────────────┐    ┌──────────────────────────┐    │
│  │ 배수지 수위 데이터  │    │ 유지보수 관리 이력        │    │
│  │ (2020.06~11)       │    │ (2023~)                  │    │
│  └─────────┬──────────┘    └───────────┬──────────────┘    │
└────────────┼─────────────────────────────┼──────────────────┘
             │                             │
             ▼                             ▼
    ┌────────────────┐          ┌───────────────────┐
    │ LSTM 모델 학습  │          │ RAG 벡터 DB 구축   │
    │                │          │ (PostgreSQL)      │
    └────────┬───────┘          └─────────┬─────────┘
             │                             │
             ▼                             ▼
    ┌──────────────────────────────────────────────┐
    │           백엔드 (Flask API)                  │
    │  ┌──────────────┐    ┌──────────────────┐   │
    │  │ 이상 탐지 API │    │ AI 진단 API       │   │
    │  │ /anomaly/*    │    │ /anomaly/diagnose │   │
    │  └──────────────┘    └──────────────────┘   │
    └───────────────────┬──────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   프론트엔드 (React)          │
         │  ┌────────────────────────┐  │
         │  │ 실시간 모니터링 화면    │  │
         │  │ (AnomalyMonitoring)    │  │
         │  └────────────────────────┘  │
         │  ┌────────────────────────┐  │
         │  │ 테스트 인터페이스      │  │
         │  │ (AnomalyTest)          │  │
         │  └────────────────────────┘  │
         └──────────────────────────────┘
```

---

## 📂 파일 구조

```
agentic_rag/
├── RNN-LSTM_model 분석/
│   ├── 1.2023년 부터_유지보수 관리이력.xlsx    # 유지보수 데이터
│   └── 3.배수지 수위 데이터_WATERDATA.xlsx      # 수위 데이터
│
├── data_loader/
│   └── water_data_loader.py                   # 엑셀 데이터 로더
│
├── models/
│   └── lstm_water_model.py                    # LSTM 모델 & 이상 탐지기
│
├── tools/
│   ├── anomaly_detection_tool.py              # 이상 탐지 도구
│   └── ai_diagnosis_tool.py                   # AI 진단 도구
│
├── api/
│   └── anomaly_routes.py                      # Flask API 라우트
│
├── scripts/
│   ├── train_lstm_model.py                    # 모델 학습 스크립트
│   └── build_maintenance_rag.py               # RAG 구축 스크립트
│
├── frontend_react/src/pages/
│   ├── AnomalyMonitoring.js                   # 실시간 모니터링 화면
│   ├── AnomalyMonitoring.css
│   ├── AnomalyTest.js                         # 테스트 인터페이스
│   └── AnomalyTest.css
│
└── lstm_model/
    ├── lstm_gagok_model.h5                    # 학습된 LSTM 모델
    └── plots/                                 # 학습 시각화 결과
```

---

## 🚀 설치 및 실행

### 1. 필수 패키지 설치

```bash
pip install tensorflow pandas numpy scikit-learn openpyxl matplotlib flask flask-cors psycopg2-binary
```

### 2. LSTM 모델 학습

```bash
cd "c:\Users\A\Documents\Github Clone 파일\agentic_rag"
python scripts/train_lstm_model.py
```

**출력:**
- `lstm_model/lstm_gagok_model.h5` - 학습된 모델
- `lstm_model/plots/training_history.png` - 학습 곡선
- `lstm_model/plots/test_predictions.png` - 예측 결과

### 3. 유지보수 이력 RAG 구축

```bash
python scripts/build_maintenance_rag.py
```

**수행 작업:**
- 엑셀에서 유지보수 이력 로드
- 텍스트 전처리 및 문서화
- PostgreSQL 벡터 DB에 임베딩 저장

### 4. Flask 백엔드 실행

```bash
python flask_app.py
```

**실행 포트:** `http://localhost:5000`

### 5. React 프론트엔드 실행

```bash
cd frontend_react
npm install
npm start
```

**실행 포트:** `http://localhost:3000`

---

## 🔧 API 엔드포인트

### 1. 이상 탐지

**POST** `/api/anomaly/detect`

```json
{
  "water_levels": [70.5, 70.8, 71.2, ...],  // 60개 권장
  "pump_a": 0,                               // 0 or 1
  "pump_b": 1,                               // 0 or 1
  "actual_next_level": 72.5                  // optional
}
```

**응답:**

```json
{
  "success": true,
  "prediction": 71.8,
  "actual_value": 72.5,
  "error": 0.7,
  "is_anomaly": false,
  "status": "정상",
  "threshold": 5.0,
  "severity": 1
}
```

### 2. 전체 배수지 상태 조회

**GET** `/api/anomaly/status`

**응답:**

```json
{
  "success": true,
  "reservoirs": {
    "gagok": {
      "status": "정상",
      "level": 70.5,
      "prediction": 70.8,
      "error": 0.3,
      "pump_a": 0,
      "pump_b": 1,
      "lastUpdate": "2026-01-13T10:30:00"
    },
    "haeryong": { ... },
    "sangsa": { ... }
  }
}
```

### 3. AI 진단

**POST** `/api/anomaly/diagnose`

```json
{
  "reservoir": "gagok",
  "anomaly_type": "급감",
  "water_level_change": -15.5,
  "pump_status": {"pump_a": 1, "pump_b": 0},
  "error_magnitude": 12.3
}
```

**응답:**

```json
{
  "success": true,
  "diagnosis": {
    "possible_causes": [
      "펌프 고장 가능성",
      "센서 오류 가능성",
      "밸브/배관 문제 가능성"
    ],
    "severity": "높음",
    "immediate_actions": [
      "현장 점검 및 확인",
      "펌프 작동 상태 점검"
    ],
    "long_term_solutions": [
      "정기 점검 주기 강화",
      "노후 장비 교체 검토"
    ]
  },
  "similar_cases": [ ... ]
}
```

---

## 📊 React 화면 사용법

### 실시간 모니터링 화면 (`/anomaly-monitoring`)

1. **배수지 상태 카드**
   - 3개 배수지 (가곡, 해룡, 상사) 실시간 상태 표시
   - 현재 수위, 예측 수위, 오차 표시
   - 상태: 정상 (초록) / 경미 (주황) / 중간 (빨강) / 심각 (진한 빨강)

2. **AI 진단 버튼**
   - 이상 발생 시 "🩺 AI 진단" 버튼 활성화
   - 클릭 시 AI가 유사 사례 검색 및 원인 분석

3. **자동 갱신**
   - 10초마다 자동 갱신 (토글 가능)

### 테스트 인터페이스 (`/anomaly-test`)

1. **샘플 데이터 버튼**
   - "정상 패턴" / "급격한 수위 하강" / "급격한 수위 상승" / "불안정한 패턴"
   - 클릭 시 자동으로 테스트 데이터 입력

2. **수동 입력**
   - 배수지 선택
   - 과거 수위 데이터 입력 (쉼표로 구분)
   - 펌프 상태 (체크박스)
   - 실제 다음 수위 입력

3. **테스트 실행**
   - "🚀 테스트 실행" 버튼 클릭
   - LSTM 모델이 예측 및 이상 탐지 수행
   - 결과: 예측값, 오차, 이상 여부, 심각도 표시

---

## 📈 데이터 흐름

### 이상 탐지 프로세스

```
1. 실시간 수위 데이터 수집
   ↓
2. LSTM 모델로 다음 수위 예측
   ↓
3. 예측값 vs 실제값 비교
   ↓
4. 오차가 임계값 초과?
   ├─ YES → 이상 감지
   │   ↓
   │   5. AI 진단 도구 호출
   │   ↓
   │   6. 유지보수 이력 RAG 검색
   │   ↓
   │   7. 원인 분석 및 조치사항 추천
   │
   └─ NO → 정상
```

### RAG 진단 프로세스

```
1. 이상 패턴 분석
   - 수위 변화: 급감 / 급증 / 불안정
   - 펌프 상태: ON/OFF 조합
   - 오차 크기: 작음 / 중간 / 큼
   ↓
2. 검색 쿼리 생성
   예: "수위 급감 펌프 정지 가곡"
   ↓
3. 벡터 DB에서 유사 사례 검색
   ↓
4. LLM에게 컨텍스트 전달
   - 현재 이상 패턴
   - 과거 유사 사례 5개
   ↓
5. LLM이 진단 생성
   - 가능한 원인 3가지
   - 심각도 평가
   - 즉시 조치사항
   - 장기 대책
```

---

## 🎯 모델 성능

### LSTM 모델 (가곡 배수지)

- **입력**: 60분 과거 수위 데이터
- **출력**: 1분 후 수위 예측
- **아키텍처**:
  - LSTM Layer 1: 128 units
  - LSTM Layer 2: 64 units
  - Dense Layer: 64 units
  - Output: 1 unit

### 학습 결과

- **MSE**: 0.XXXXXX
- **RMSE**: X.XX cm
- **MAE**: X.XX cm
- **MAPE**: X.X%

*(실제 학습 후 업데이트)*

---

## 🛠️ 커스터마이징

### 1. 임계값 조정

`tools/anomaly_detection_tool.py`에서 `threshold_multiplier` 변경:

```python
anomaly_detector = LSTMAnomalyDetectionTool(threshold_multiplier=3.0)
```

- `threshold_multiplier=2.0`: 더 민감 (더 많은 이상 탐지)
- `threshold_multiplier=4.0`: 덜 민감 (심각한 이상만 탐지)

### 2. LSTM 모델 재학습

다른 배수지 또는 더 많은 데이터로 재학습:

```python
# scripts/train_lstm_model.py 수정
reservoir = 'haeryong'  # 'gagok', 'haeryong', 'sangsa'
seq_length = 120  # 60 → 120 (2시간 데이터)
```

### 3. RAG 문서 필터링

특정 카테고리만 검색하도록 필터링:

```python
# tools/ai_diagnosis_tool.py
results = self.storage.search_similar_documents(
    query=search_query,
    top_k=5,
    metadata_filter={
        'collection': 'maintenance',
        '대상': '가압장'  # 특정 대상만
    }
)
```

---

## 🐛 트러블슈팅

### 1. 모델 파일이 없습니다

**증상**: `FileNotFoundError: lstm_gagok_model.h5`

**해결**:

```bash
python scripts/train_lstm_model.py
```

### 2. PostgreSQL 연결 실패

**증상**: `psycopg2.OperationalError`

**해결**: `config.py`에서 DB 설정 확인

```python
PG_DB_HOST = 'localhost'
PG_DB_PORT = 5432
PG_DB_NAME = 'water_db'
PG_DB_USER = 'your_user'
PG_DB_PASSWORD = 'your_password'
```

### 3. React에서 API 호출 실패

**증상**: `CORS` 에러 또는 `Network Error`

**해결**:
1. Flask 백엔드가 실행 중인지 확인
2. `frontend_react/src/config.js`에서 API URL 확인
3. CORS 설정 확인 (`flask_app.py`)

### 4. 유지보수 이력 검색 결과 없음

**증상**: `similar_cases: []`

**해결**:

```bash
python scripts/build_maintenance_rag.py
```

---

## 📝 향후 개선사항

- [ ] **다변량 LSTM**: 펌프 상태도 입력으로 사용
- [ ] **실시간 재학습**: 새로운 데이터로 모델 업데이트
- [ ] **앙상블 모델**: LSTM + GRU + Transformer 조합
- [ ] **이상 유형 분류**: 급감/급증/불안정 자동 분류
- [ ] **알림 시스템**: 이상 발생 시 이메일/SMS 알림
- [ ] **대시보드 확장**: 차트, 통계, 히스토리 추가

---

## 📄 라이선스

MIT License

---

## 👥 기여자

- AI Assistant (LSTM 모델 및 시스템 설계)
- Your Name (프로젝트 관리)

---

## 📞 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.
