# models/ollama_client.py

import json
import os
import sys
import requests
from typing import Optional, Generator, Dict, Any, List

from config import (
    TOOL_SELECTION_TEMPERATURE,
    RESPONSE_TEMPERATURE,
    MAX_TOKENS,
    REQUEST_TIMEOUT,
)
from utils.logger import setup_logger
from utils.helpers import retry

# 프로젝트 루트를 우선 탐색하도록 sys.path 조정
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = setup_logger(__name__)


class OllamaClient:
    """Ollama API 클라이언트 (스트리밍 지원)"""

    def __init__(self, base_url: str = None, model_name: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model_name or os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:7b")

        # API 엔드포인트
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"

        logger.info(f"Ollama 클라이언트 초기화: {self.model}, URL: {self.base_url}")

    @retry(max_retries=3)
    def generate_response(self, prompt: str, temperature: Optional[float] = None, stream: bool = True) -> Generator[str, None, None] | str:
        """일반 응답 생성 (스트리밍 지원)"""
        if temperature is None:
            temperature = RESPONSE_TEMPERATURE

        logger.info(f"Ollama 응답 생성, 온도: {temperature}, 스트리밍: {stream}")

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": stream,
            }

            if stream:
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    stream=True,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()

                def response_generator():
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'response' in chunk:
                                    yield chunk['response']
                            except json.JSONDecodeError:
                                continue

                return response_generator()
            else:
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                return result.get('response', '')

        except Exception as e:
            logger.error(f"Ollama 응답 생성 오류: {str(e)}")
            raise

    @retry(max_retries=3)
    def chat_completion(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, stream: bool = True) -> Generator[str, None, None] | str:
        """채팅 완성 생성 (스트리밍 지원)"""
        if temperature is None:
            temperature = RESPONSE_TEMPERATURE

        logger.info(f"Ollama 채팅 완성, 온도: {temperature}, 스트리밍: {stream}")

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
            }

            if stream:
                response = requests.post(
                    self.chat_url,
                    json=payload,
                    stream=True,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()

                def response_generator():
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'message' in chunk and 'content' in chunk['message']:
                                    yield chunk['message']['content']
                            except json.JSONDecodeError:
                                continue

                return response_generator()
            else:
                response = requests.post(
                    self.chat_url,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                return result.get('message', {}).get('content', '')

        except Exception as e:
            logger.error(f"Ollama 채팅 완성 오류: {str(e)}")
            raise

    @retry(max_retries=3)
    def function_call(self, prompt: str, functions: List[Dict[str, Any]], temperature: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        도구/함수 호출 생성
        Ollama는 네이티브 function calling을 지원하지 않으므로
        프롬프트에 함수 정의를 포함하고 JSON 응답을 파싱합니다.
        """
        if temperature is None:
            temperature = TOOL_SELECTION_TEMPERATURE

        tool_selection_max_tokens = 128

        logger.info(f"Ollama 도구 선택, 온도: {temperature}")

        try:
            # 함수 정의를 프롬프트에 추가
            functions_json = json.dumps(functions, ensure_ascii=False, indent=2)

            full_prompt = f"""{prompt}

Available functions:
```json
{functions_json}
```

Respond with ONLY a JSON object in this format:
{{"name": "function_name", "arguments": {{"arg1": "value1"}}}}

Or respond with an empty array [] if no function is needed.
"""

            # 비스트리밍 모드로 응답 받기
            response = requests.post(
                self.generate_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "stream": False,
                },
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            content = result.get('response', '').strip()

            # JSON 파싱
            return self._parse_function_response(content)

        except Exception as e:
            logger.error(f"Ollama 도구 선택 오류: {str(e)}", exc_info=True)
            raise

    def _parse_function_response(self, content: str) -> Optional[Dict[str, Any]]:
        """함수 호출 응답 파싱"""
        try:
            # Markdown 코드 블록 제거
            if content.strip().startswith("```json"):
                content = content.strip()[len("```json"):].strip()
                if content.endswith("```"):
                    content = content[:-len("```")].strip()
            elif content.strip().startswith("```"):
                lines = content.strip().split("\n")
                if len(lines) > 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
                    content = "\n".join(lines[1:-1])

            # JSON 파싱
            try:
                result = json.loads(content)
                if (isinstance(result, dict) and "name" in result and "arguments" in result) or isinstance(result, list):
                    logger.info(f"함수 호출 파싱 성공: {result}")
                    return result
            except json.JSONDecodeError:
                logger.warning(f"JSON 파싱 실패, 내용: {content}")
                return None

        except Exception as e:
            logger.error(f"함수 응답 파싱 오류: {e}")

        return None

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "api_available": self._check_api_available(),
        }

    def _check_api_available(self) -> bool:
        """API 연결 가능 여부 확인"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Ollama API 연결 확인 실패: {e}")
            return False
