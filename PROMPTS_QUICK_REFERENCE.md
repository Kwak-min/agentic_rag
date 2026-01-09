# 프롬프트 빠른 참조 가이드

## 🎯 주요 프롬프트 위치

| 프롬프트 종류 | 파일 | 행 번호 | 사용 모델 |
|-------------|------|---------|----------|
| **일반 대화 응답** | `core/response_generator.py` | 70-105 | Ollama qwen2.5:7b |
| **도구 결과 기반 응답** | `core/response_generator.py` | 141-245 | Ollama qwen2.5:7b |
| **자율 에이전트 (펌프 제어)** | `services/autonomous_agent.py` | 69-117 | Ollama qwen2.5:7b |
| **레거시 응답 (config)** | `config.py` | 475-518 | - |

---

## ⚡ 빠른 수정 가이드

### 1단계: 파일 열기
```bash
# Windows
notepad core/response_generator.py

# Linux/Mac
vim core/response_generator.py
```

### 2단계: 해당 행 찾기
- **일반 대화**: 70-105행 → `chat_prompt` 변수
- **도구 응답**: 141-245행 → `retrieval_guard_prompt` 변수
- **자율 에이전트**: 69-117행 → `self.system_prompt` 변수

### 3단계: 수정 후 저장

### 4단계: 재시작
```bash
docker-compose -f docker-compose-new.yml restart backend
```

### 5단계: 테스트
```bash
# API 헬스체크
curl http://localhost:5000/api/health

# 웹 UI 접속
http://localhost:3000
```

---

## 📋 주요 프롬프트 변수

### 플레이스홀더 (절대 삭제 금지!)
- `{user_query}` - 사용자 질문
- `{formatted_results}` - 도구 실행 결과
- `{tool_results}` - 원본 도구 결과

### XML 태그 (구조화에 필수)
- `<ROLE>` - AI의 역할 정의
- `<INSTRUCTIONS>` - 지시사항
- `<FORMATTING_RULES>` - 형식 규칙
- `<REQUIRED_STRUCTURE>` - 필수 구조
- `<CONTEXT>` - 컨텍스트 정보
- `<CRITICAL_RULES>` - 핵심 규칙

---

## 🔥 자주 수정하는 부분

### 응답 톤 변경
**위치**: `core/response_generator.py` 71행

```python
# 현재 (격식)
당신은 사용자의 질문에 대해 체계적이고 유용한 답변을 제공하는 전문 AI 어시스턴트입니다.

# 친근한 톤으로 변경 예시
당신은 사용자와 친근하게 대화하며 도움을 주는 AI 어시스턴트입니다.
```

### 응답 구조 변경
**위치**: `core/response_generator.py` 90-98행

```python
# 현재 구조
## 답변
### 상세 설명
### 도움말

# 변경 예시
## 결과
### 설명
### 다음 단계
```

### 펌프 제어 임계값 변경
**위치**: `services/autonomous_agent.py` 77-81행

```python
# 현재
1. 가곡 수위 < 40m → 저수지1 펌프 ON
2. 가곡 수위 > 80m → 저수지1 펌프 OFF

# 변경 예시 (임계값 조정)
1. 가곡 수위 < 30m → 저수지1 펌프 ON
2. 가곡 수위 > 70m → 저수지1 펌프 OFF
```

---

## ⚠️ 절대 삭제하면 안 되는 것

1. **플레이스홀더**: `{user_query}`, `{formatted_results}` 등
2. **JSON 형식 지시**: "JSON만 출력한다" (자율 에이전트)
3. **코드 블록 금지**: "코드 블록(```)을 절대 사용하지 마십시오"
4. **이모지 제목 금지**: "제목에는 절대 이모지를 사용하지 마십시오"

---

## 🧪 테스트 명령어

### 백엔드 로그 확인
```bash
docker logs -f synergy-backend | grep -E "(Ollama|응답|ERROR)"
```

### API 직접 테스트
```bash
# Python으로 테스트
python -c "import requests; r = requests.post('http://localhost:5000/api/chat', json={'message': '안녕하세요'}); print(r.json())"
```

### 웹 UI 테스트
1. http://localhost:3000 접속
2. 채팅창에 메시지 입력
3. 응답 형식 확인

---

## 💾 백업 추천

프롬프트 수정 전 백업:
```bash
# 파일 백업
cp core/response_generator.py core/response_generator.py.backup
cp services/autonomous_agent.py services/autonomous_agent.py.backup
cp config.py config.py.backup

# 날짜별 백업
cp core/response_generator.py core/response_generator.py.$(date +%Y%m%d)
```

---

## 📞 문제 발생 시

### 응답이 이상할 때
1. 로그 확인: `docker logs synergy-backend --tail 50`
2. 프롬프트 문법 오류 확인 (따옴표, 중괄호 등)
3. 백업 파일로 복원

### 백엔드가 시작 안 될 때
1. 문법 오류 확인: `python -m py_compile core/response_generator.py`
2. Docker 로그: `docker logs synergy-backend`
3. 이전 버전으로 롤백

---

## 🎓 프롬프트 엔지니어링 핵심

### Good ✅
```
명확한 지시: "반드시 다음 구조를 따르세요:"
구체적 예시: "예시: {\"key\": \"value\"}"
제약 명시: "절대 코드 블록을 사용하지 마세요"
```

### Bad ❌
```
모호한 지시: "적절히 답변하세요"
예시 없음: "JSON으로 답변하세요" (형식 예시 없음)
이중 부정: "사용하지 않지 않아야 합니다"
```

---

## 📚 더 자세한 내용

전체 가이드: [PROMPTS.md](PROMPTS.md) 참조
