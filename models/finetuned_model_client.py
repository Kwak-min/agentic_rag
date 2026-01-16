# models/finetuned_model_client.py

import os
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from typing import Optional, Generator, Dict, Any, List

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logger

logger = setup_logger(__name__)


class FinetunedModelClient:
    """파인튜닝된 LoRA 모델 클라이언트"""

    def __init__(self,
                 base_model_name: str = "Qwen/Qwen2.5-7B-Instruct",
                 adapter_path: str = None,
                 device: str = "auto"):
        """
        Args:
            base_model_name: 베이스 모델 이름 (HuggingFace)
            adapter_path: LoRA 어댑터 경로
            device: 사용할 디바이스 (auto, cuda, cpu)
        """
        self.base_model_name = base_model_name
        self.adapter_path = adapter_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "Finetuning",
            "final_model"
        )
        self.device = device
        self.model = None
        self.tokenizer = None

        logger.info(f"파인튜닝 모델 클라이언트 초기화: {base_model_name}")
        logger.info(f"어댑터 경로: {self.adapter_path}")

        self._load_model()

    def _load_model(self):
        """모델 로드 (LoRA 어댑터 적용)"""
        try:
            logger.info("토크나이저 로드 중...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.adapter_path,
                trust_remote_code=True
            )

            # GPU 사용 가능 여부 확인
            use_cuda = torch.cuda.is_available() and self.device != "cpu"
            logger.info(f"CUDA 사용 가능: {use_cuda}")

            if use_cuda:
                # 4bit 양자화 설정 (메모리 절약)
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )

                logger.info("베이스 모델 로드 중 (4bit 양자화)...")
                base_model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                    local_files_only=False,
                    resume_download=True
                )
            else:
                logger.info("베이스 모델 로드 중 (CPU)...")
                base_model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                    local_files_only=False,
                    resume_download=True
                )

            logger.info("LoRA 어댑터 적용 중...")
            self.model = PeftModel.from_pretrained(base_model, self.adapter_path)
            self.model.eval()

            logger.info("파인튜닝 모델 로드 완료!")

        except Exception as e:
            logger.error(f"모델 로드 오류: {str(e)}")
            logger.error("파인튜닝 모델 로드 실패. 베이스 모델을 HuggingFace에서 다운로드해야 합니다.")
            logger.error(f"필요한 베이스 모델: {self.base_model_name}")
            logger.error("해결 방법:")
            logger.error("1. 인터넷 연결 확인")
            logger.error("2. HuggingFace 토큰 설정 (필요시): export HF_TOKEN=your_token")
            logger.error("3. 로컬에 모델 다운로드 후 경로 지정")
            logger.error("4. .env에서 USE_FINETUNED_MODEL=false로 설정하여 Ollama 사용")
            raise

    def generate_response(self,
                         prompt: str,
                         temperature: float = 0.7,
                         max_new_tokens: int = 512,
                         stream: bool = False) -> str:
        """응답 생성"""
        try:
            # 입력 토큰화
            inputs = self.tokenizer(prompt, return_tensors="pt")

            if self.device != "cpu" and torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # 생성 설정
            gen_config = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "do_sample": True,
                "top_p": 0.9,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }

            # 생성
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **gen_config)

            # 디코딩 (프롬프트 제외)
            response = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True
            )

            return response.strip()

        except Exception as e:
            logger.error(f"응답 생성 오류: {str(e)}")
            raise

    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       temperature: float = 0.7,
                       max_new_tokens: int = 512,
                       stream: bool = False) -> str:
        """채팅 완성 생성"""
        try:
            # 메시지를 프롬프트로 변환
            if hasattr(self.tokenizer, 'apply_chat_template'):
                # 채팅 템플릿 적용
                prompt = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            else:
                # 수동으로 프롬프트 구성
                prompt = ""
                for msg in messages:
                    role = msg["role"]
                    content = msg["content"]
                    if role == "system":
                        prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
                    elif role == "user":
                        prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
                    elif role == "assistant":
                        prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
                prompt += "<|im_start|>assistant\n"

            return self.generate_response(prompt, temperature, max_new_tokens, stream)

        except Exception as e:
            logger.error(f"채팅 완성 오류: {str(e)}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model": "finetuned-qwen2.5-7b",
            "base_model": self.base_model_name,
            "adapter_path": self.adapter_path,
            "device": str(self.model.device) if self.model else "not loaded",
            "api_available": self.model is not None,
        }
