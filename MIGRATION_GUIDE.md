# 🚀 Synergy ChatBot 마이그레이션 가이드

## 변경 사항 요약

### 1. **AI 모델: LM Studio → Ollama (phi3:mini)**
- LM Studio 대신 Ollama 사용
- 모델: `phi3:mini`
- 호스트 머신에서 실행 (http://localhost:11434)

### 2. **프론트엔드: Streamlit → Next.js + React**
- 모던한 React 기반 UI
- Tailwind CSS로 스타일링
- WebSocket 실시간 통신

### 3. **백엔드: Flask API**
- REST API + WebSocket
- Streamlit 세션 대신 HTTP 기반 통신

---

## 📋 사전 요구사항

### 1. Ollama 설치 및 실행
```bash
# Ollama 실행 (이미 실행 중이어야 함)
ollama serve

# phi3:mini 모델 다운로드 (이미 완료)
ollama pull phi3:mini

# 모델 확인
ollama list
```

### 2. Node.js 설치
- Node.js 18 이상 필요
- https://nodejs.org/

---

## 🛠️ 설치 및 실행

### 방법 1: Docker로 실행 (권장)

```bash
# 1. 기존 컨테이너 중지
docker-compose down

# 2. 새 Docker Compose로 실행
docker-compose -f docker-compose-new.yml up --build

# 3. 브라우저에서 접속
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:5000
```

### 방법 2: 로컬에서 실행

#### Backend (Flask)
```bash
# 1. Python 패키지 설치
pip install flask flask-cors flask-socketio python-socketio

# 2. Flask 앱 실행
python flask_app.py

# Backend API가 http://localhost:5000에서 실행됩니다
```

#### Frontend (Next.js)
```bash
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. 패키지 설치
npm install

# 3. 개발 서버 실행
npm run dev

# Frontend가 http://localhost:3000에서 실행됩니다
```

---

## 📁 프로젝트 구조

```
agentic_rag/
├── models/
│   ├── ollama_client.py      # NEW: Ollama 클라이언트
│   └── lm_studio.py           # OLD: LM Studio (비활성화)
├── flask_app.py               # NEW: Flask API 백엔드
├── frontend/                  # NEW: Next.js 프론트엔드
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # 메인 페이지
│   │   │   ├── layout.tsx     # 레이아웃
│   │   │   └── globals.css    # 글로벌 스타일
│   │   └── components/
│   │       ├── Sidebar.tsx           # 사이드바
│   │       ├── ChatInterface.tsx     # 채팅 인터페이스
│   │       ├── WaterDashboard.tsx    # 수위 대시보드
│   │       └── AutomationDashboard.tsx # 자동화 대시보드
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── app.py                     # OLD: Streamlit (비활성화)
├── docker-compose-new.yml     # NEW: Docker Compose
└── .env                       # 환경 변수 (업데이트됨)
```

---

## 🔧 주요 기능

### 1. **채팅 인터페이스**
- 실시간 AI 채팅
- WebSocket 스트리밍 응답
- Markdown 지원

### 2. **수위 모니터링 대시보드**
- 실시간 수위 데이터
- 24시간 추이 그래프 (Recharts)
- 가곡/해룡 배수지 모니터링

### 3. **자동화 시스템**
- 펌프 자동화 제어
- 자율 에이전트 관리
- 통합 상태 모니터링

---

## 🌐 API 엔드포인트

### REST API
- `GET /api/health` - 헬스 체크
- `POST /api/initialize` - 시스템 초기화
- `GET /api/system/status` - 시스템 상태
- `POST /api/chat` - 채팅 메시지
- `GET /api/water/current` - 현재 수위
- `GET /api/water/history` - 수위 이력
- `GET /api/files` - 파일 목록
- `POST /api/files/upload` - 파일 업로드

### WebSocket
- `connect` - 연결
- `disconnect` - 연결 해제
- `chat_message` - 채팅 메시지 (스트리밍)
- `water_subscribe` - 수위 데이터 구독

---

## ⚙️ 환경 변수

`.env` 파일:
```bash
# Ollama 설정
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL_NAME=phi3:mini
USE_OLLAMA=true

# Flask 설정
FLASK_PORT=5000

# 데이터베이스 설정
PG_DB_HOST=postgres
PG_DB_PORT=5432
PG_DB_NAME=synergy
PG_DB_USER=synergy
PG_DB_PASSWORD=synergy

# 시뮬레이션 모드
SIMULATION_MODE=true
USE_ARDUINO=false
MOCK_ARDUINO=true
```

---

## 🐛 문제 해결

### 1. Ollama 연결 실패
```bash
# Ollama가 실행 중인지 확인
curl http://localhost:11434/api/tags

# phi3:mini 모델이 있는지 확인
ollama list
```

### 2. Frontend 빌드 실패
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

### 3. Backend API 연결 실패
```bash
# Flask 앱이 실행 중인지 확인
curl http://localhost:5000/api/health

# 로그 확인
docker logs synergy-backend
```

---

## 📚 다음 단계

1. **시스템 초기화**: 브라우저에서 "시스템 초기화" 버튼 클릭
2. **채팅 테스트**: 메시지를 입력하여 Ollama 응답 확인
3. **수위 모니터링**: 수위 대시보드에서 실시간 데이터 확인
4. **자동화 시스템**: 자동화 기능 활성화 및 테스트

---

## 🎉 완료!

이제 새로운 아키텍처로 Synergy ChatBot을 사용할 수 있습니다!

- Frontend: http://localhost:3000
- Backend: http://localhost:5000
