# 파인튜닝 모델 사용 가이드

## 현재 상태

현재 시스템은 **Ollama (qwen2.5:7b)** 를 사용하여 AI 챗봇 기능을 제공하고 있습니다.

파인튜닝된 모델을 사용하려고 시도했으나, Docker 컨테이너 내에서 HuggingFace로부터 베이스 모델(Qwen/Qwen2.5-7B-Instruct)을 다운로드하는 과정에서 네트워크 오류가 발생했습니다.

## 문제 상황

```
RuntimeError: Data processing error: CAS service error : ReqwestMiddleware Error
```

이 오류는 Docker 컨테이너 내에서 HuggingFace의 transfer 서비스에 연결할 때 발생하는 네트워크 문제입니다.

## 해결 방법

### 방법 1: 호스트 머신에서 모델 다운로드 후 Docker 볼륨 마운트 (권장)

1. **호스트 머신에서 베이스 모델 다운로드:**

```bash
# Python 환경 활성화
# Windows
python -m venv venv
venv\Scripts\activate

# 필요한 패키지 설치
pip install transformers torch

# Python 스크립트로 모델 다운로드
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-7B-Instruct'); tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct'); print('Download complete!')"
```

2. **다운로드된 모델 경로 확인:**

Windows: `C:\Users\{사용자명}\.cache\huggingface\hub\models--Qwen--Qwen2.5-7B-Instruct`

3. **docker-compose-new.yml 수정:**

```yaml
  backend:
    volumes:
      - ./:/app
      - model_data:/app/rnn_lstm_model
      - C:\Users\{사용자명}\.cache\huggingface:/root/.cache/huggingface  # HuggingFace 캐시 마운트
```

4. **.env 파일 수정:**

```env
USE_FINETUNED_MODEL=true
USE_OLLAMA=false
```

5. **컨테이너 재시작:**

```bash
docker-compose -f docker-compose-new.yml down backend
docker-compose -f docker-compose-new.yml up -d backend
```

### 방법 2: 로컬 모델 파일 복사

1. **베이스 모델을 프로젝트 디렉토리로 복사:**

```bash
# 모델 다운로드 디렉토리 생성
mkdir -p models/base_model

# HuggingFace에서 모델 다운로드 (호스트에서 실행)
# 방법 1과 동일하게 다운로드 후
# models/base_model 디렉토리로 복사
```

2. **.env 파일 수정:**

```env
USE_FINETUNED_MODEL=true
USE_OLLAMA=false
FINETUNED_BASE_MODEL=./models/base_model  # 로컬 경로 사용
```

3. **컨테이너 재시작:**

```bash
docker-compose -f docker-compose-new.yml restart backend
```

### 방법 3: HuggingFace 토큰 사용 (일부 모델의 경우)

일부 제한된 모델의 경우 HuggingFace 토큰이 필요할 수 있습니다:

1. **HuggingFace 토큰 발급:**
   - https://huggingface.co/settings/tokens 에서 토큰 생성

2. **.env 파일에 토큰 추가:**

```env
HF_TOKEN=your_huggingface_token_here
```

3. **docker-compose-new.yml 수정:**

```yaml
  backend:
    environment:
      HF_TOKEN: ${HF_TOKEN}
```

## 파인튜닝 모델 구조

현재 프로젝트의 파인튜닝 모델:
- **위치:** `Finetuning/final_model/`
- **타입:** LoRA 어댑터
- **베이스 모델:** Qwen/Qwen2.5-7B-Instruct
- **파일:**
  - `adapter_config.json` - LoRA 설정
  - `adapter_model.safetensors` - LoRA 가중치 (4.39 MB)
  - 토크나이저 파일들

## 구현된 코드

### models/finetuned_model_client.py

파인튜닝 모델을 로드하고 사용하는 클라이언트 클래스가 이미 구현되어 있습니다:

- LoRA 어댑터 로드
- 4-bit 양자화 지원 (GPU 사용 시)
- CPU/GPU 자동 감지
- 채팅 완성 생성

### flask_app.py

파인튜닝 모델 로드 실패 시 Ollama로 자동 폴백하는 로직이 구현되어 있습니다.

## 성능 고려사항

### GPU 사용

- **GPU 있음:** 4-bit 양자화로 메모리 효율적 추론 (약 4-5GB VRAM 필요)
- **CPU만 있음:** 느린 추론 속도 (7B 모델은 CPU에서 매우 느림)

### 권장 사항

대용량 언어 모델(7B)을 Docker 컨테이너에서 실행하는 것은 다음과 같은 이유로 비효율적일 수 있습니다:

1. **메모리:** 7B 모델은 최소 8-16GB RAM 필요
2. **속도:** CPU 추론은 매우 느림
3. **네트워크:** 컨테이너에서 대용량 모델 다운로드 시 문제 발생 가능

**대안:**
- Ollama 사용 (현재 설정) - 호스트에서 실행되어 더 안정적
- LM Studio 사용 - 호스트에서 실행
- GPU 서버에 모델 배포 후 API로 연결

## 현재 설정 (.env)

```env
# Ollama (현재 활성화)
USE_OLLAMA=true
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL_NAME=qwen2.5:7b

# 파인튜닝 모델 (현재 비활성화)
USE_FINETUNED_MODEL=false
FINETUNED_BASE_MODEL=Qwen/Qwen2.5-7B-Instruct
FINETUNED_ADAPTER_PATH=./Finetuning/final_model
```

## 테스트

파인튜닝 모델 설정 후 테스트:

```bash
# 백엔드 로그 확인
docker logs synergy-backend --tail 50

# 성공 시 다음 메시지 확인:
# "1/6: 파인튜닝 모델 클라이언트 초기화 완료"
# "파인튜닝 모델 로드 완료!"

# API 테스트
curl -X POST http://localhost:5000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요", "session_id": "test"}'
```

## 문제 해결

### 로그 확인

```bash
docker logs synergy-backend -f
```

### 컨테이너 내 확인

```bash
# 컨테이너 접속
docker exec -it synergy-backend /bin/sh

# Python으로 직접 테스트
python
>>> from models.finetuned_model_client import FinetunedModelClient
>>> # 오류 메시지 확인
```

## 참고 자료

- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [PEFT (LoRA)](https://huggingface.co/docs/peft)
- [Qwen2.5 모델](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
