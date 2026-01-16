# tools/anomaly_detection_tool.py - RNN-LSTM 하이브리드 기반 이상 탐지 도구

import numpy as np
import tensorflow as tf
from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.logger import setup_logger
from models.rnn_lstm_hybrid_model import RNNLSTMHybridModel, RNNLSTMAnomalyDetector
from sklearn.preprocessing import MinMaxScaler
import json

logger = setup_logger(__name__)


class LSTMAnomalyDetectionTool:
    """RNN-LSTM 하이브리드 기반 수위 이상 탐지 도구

    사용자가 수위 데이터 + 펌프 상태를 입력하면
    RNN-LSTM 하이브리드 모델로 예측하여 이상 여부를 판단합니다.
    """

    def __init__(self, model_path: str = None, threshold_multiplier: float = 3.0):
        """
        Args:
            model_path: RNN-LSTM 모델 경로 (.keras 파일)
            threshold_multiplier: 이상 판정 임계값 배수
        """
        self.name = "rnn_lstm_anomaly_detection"
        self.description = "RNN-LSTM 하이브리드 모델을 사용하여 수위 데이터의 이상 여부를 탐지합니다. 과거 수위 데이터를 입력하면 예측값과 비교하여 이상 여부를 판단합니다."

        # 모델 경로 설정
        if model_path is None:
            project_root = Path(__file__).parent.parent
            model_path = str(project_root / "rnn_lstm_model" / "rnn_lstm_gagok_model.keras")

        self.model_path = model_path
        self.threshold_path = None
        self.lstm_model = None
        self.anomaly_detector = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.threshold_multiplier = threshold_multiplier

        # 모델 설정
        self.seq_length = 60
        self.pred_length = 1

        logger.info(f"RNN-LSTM 이상 탐지 도구 초기화: model_path={model_path}")

    def _load_model(self):
        """RNN-LSTM 하이브리드 모델 로드"""
        try:
            if Path(self.model_path).exists():
                # RNN-LSTM 하이브리드 모델 로드
                self.lstm_model = RNNLSTMHybridModel(
                    seq_length=self.seq_length,
                    pred_length=self.pred_length,
                    rnn_units=64,
                    lstm_units=128,
                    dropout_rate=0.2
                )
                self.lstm_model.load(self.model_path)

                # 이상 탐지기 초기화
                self.anomaly_detector = RNNLSTMAnomalyDetector(
                    rnn_lstm_model=self.lstm_model,
                    threshold_multiplier=self.threshold_multiplier
                )

                # 임계값 파일 로드 시도
                self.threshold_path = str(Path(self.model_path).parent /
                                        Path(self.model_path).stem.replace('_model', '_threshold.json'))

                if Path(self.threshold_path).exists():
                    with open(self.threshold_path, 'r', encoding='utf-8') as f:
                        threshold_data = json.load(f)
                        self.anomaly_detector.threshold = threshold_data.get('threshold')
                        self.anomaly_detector.mean_error = threshold_data.get('mean_error')
                        self.anomaly_detector.std_error = threshold_data.get('std_error')
                        logger.info(f"임계값 로드 완료: {self.anomaly_detector.threshold:.6f}")

                logger.info(f"RNN-LSTM 하이브리드 모델 로드 완료: {self.model_path}")
                return True
            else:
                logger.warning(f"모델 파일을 찾을 수 없습니다: {self.model_path}")
                logger.info("기존 LSTM 모델로 대체 시도 중...")

                # 기존 LSTM 모델로 대체
                from models.lstm_water_model import WaterLevelLSTM, AnomalyDetector
                legacy_model_path = str(Path(self.model_path).parent.parent / "lstm_model" / "lstm_gagok_model.h5")

                if Path(legacy_model_path).exists():
                    from models.lstm_water_model import WaterLevelLSTM, AnomalyDetector
                    legacy_model = WaterLevelLSTM(
                        seq_length=self.seq_length,
                        pred_length=self.pred_length
                    )
                    legacy_model.load(legacy_model_path)

                    # 임시로 RNN-LSTM 모델 대신 LSTM 모델 사용
                    self.lstm_model = legacy_model
                    self.anomaly_detector = AnomalyDetector(
                        lstm_model=legacy_model,
                        threshold_multiplier=self.threshold_multiplier
                    )

                    logger.info(f"기존 LSTM 모델 로드 완료 (대체): {legacy_model_path}")
                    return True
                else:
                    logger.error(f"대체 모델도 찾을 수 없습니다: {legacy_model_path}")
                    return False

        except Exception as e:
            logger.error(f"모델 로드 실패: {str(e)}", exc_info=True)
            return False

    def _ensure_model_loaded(self):
        """모델이 로드되어 있지 않으면 로드"""
        if self.lstm_model is None:
            return self._load_model()
        return True

    def set_threshold(self, normal_data: List[float], predictions: List[float]):
        """정상 데이터로 임계값 설정

        Args:
            normal_data: 정상 수위 데이터 리스트
            predictions: 해당 데이터의 예측값 리스트
        """
        if not self._ensure_model_loaded():
            return {"error": "모델을 로드할 수 없습니다"}

        try:
            normal_array = np.array(normal_data).reshape(-1, 1)
            pred_array = np.array(predictions).reshape(-1, 1)

            # 임계값 계산 (간단한 방법)
            errors = np.abs(normal_array - pred_array).flatten()
            mean_error = np.mean(errors)
            std_error = np.std(errors)

            self.anomaly_detector.mean_error = mean_error
            self.anomaly_detector.std_error = std_error
            self.anomaly_detector.threshold = mean_error + self.threshold_multiplier * std_error

            logger.info(f"임계값 설정: {self.anomaly_detector.threshold:.6f}")

            return {
                "success": True,
                "threshold": float(self.anomaly_detector.threshold),
                "mean_error": float(mean_error),
                "std_error": float(std_error)
            }

        except Exception as e:
            logger.error(f"임계값 설정 실패: {str(e)}")
            return {"error": f"임계값 설정 중 오류: {str(e)}"}

    def execute(self,
                water_levels: List[float] = None,
                pump_a: float = None,
                pump_b: float = None,
                actual_next_level: float = None,
                threshold: float = None,
                **kwargs) -> Dict[str, Any]:
        """이상 탐지 실행

        Args:
            water_levels: 과거 수위 데이터 리스트 (최소 60개 권장)
            pump_a: 펌프 A 상태 (0 or 1)
            pump_b: 펌프 B 상태 (0 or 1)
            actual_next_level: 실제 다음 수위 (이상 탐지용)
            threshold: 사용자 지정 임계값 (선택)

        Returns:
            이상 탐지 결과 딕셔너리
        """
        # 모델 로드 확인
        if not self._ensure_model_loaded():
            return {"error": "LSTM 모델을 로드할 수 없습니다"}

        # 데이터 검증
        if water_levels is None or len(water_levels) == 0:
            return {"error": "water_levels 데이터가 필요합니다"}

        try:
            # 데이터 전처리
            water_array = np.array(water_levels, dtype=np.float64).reshape(-1, 1)

            # 60개 시퀀스 맞추기
            if len(water_array) < self.seq_length:
                # 패딩
                pad_length = self.seq_length - len(water_array)
                last_values = np.repeat(water_array[-1], pad_length).reshape(-1, 1)
                water_array = np.concatenate([water_array, last_values])
            elif len(water_array) > self.seq_length:
                # 최근 60개만 사용
                water_array = water_array[-self.seq_length:]

            # 정규화 (현재 데이터 기준)
            data_min = np.min(water_array)
            data_max = np.max(water_array)
            data_range = data_max - data_min

            if data_range > 0:
                normalized_data = (water_array - data_min) / data_range
            else:
                normalized_data = water_array

            # LSTM 입력 형태로 변환 (1, seq_length, 1)
            input_data = normalized_data.reshape(1, self.seq_length, 1)

            # 예측
            pred_normalized = self.lstm_model.predict(input_data)

            # 역정규화
            if data_range > 0:
                pred_value = pred_normalized[0, 0] * data_range + data_min
            else:
                pred_value = pred_normalized[0, 0]

            # 결과 구성
            result = {
                "success": True,
                "prediction": float(pred_value),
                "input_data_length": len(water_levels),
                "last_water_level": float(water_levels[-1]),
                "pump_a": pump_a,
                "pump_b": pump_b
            }

            # 실제값이 있으면 이상 탐지
            if actual_next_level is not None:
                error = abs(actual_next_level - pred_value)

                # 임계값 설정
                if threshold is not None:
                    use_threshold = threshold
                elif self.anomaly_detector.threshold is not None:
                    use_threshold = self.anomaly_detector.threshold
                else:
                    # 기본 임계값 (예측값의 10%)
                    use_threshold = abs(pred_value * 0.1)

                is_anomaly = error > use_threshold

                # Z-score 계산 (임계값 기준)
                if self.anomaly_detector and self.anomaly_detector.std_error:
                    z_score = (error - self.anomaly_detector.mean_error) / self.anomaly_detector.std_error
                else:
                    z_score = error / (use_threshold / 3)  # 임계값이 3*std라고 가정

                # 심각도 계산 (1~5)
                severity = int(min(5, max(1, np.ceil(abs(z_score)))))

                # 상태 판정
                if not is_anomaly:
                    status = "정상"
                    status_code = "normal"
                elif severity <= 2:
                    status = "경미한 이상"
                    status_code = "minor_anomaly"
                elif severity <= 3:
                    status = "중간 이상"
                    status_code = "moderate_anomaly"
                else:
                    status = "심각한 이상"
                    status_code = "severe_anomaly"

                result.update({
                    "actual_value": float(actual_next_level),
                    "error": float(error),
                    "threshold": float(use_threshold),
                    "is_anomaly": bool(is_anomaly),
                    "z_score": float(z_score),
                    "severity": severity,
                    "status": status,
                    "status_code": status_code,
                    "anomaly_summary": f"예측값 {pred_value:.2f}에서 실제값 {actual_next_level:.2f} - 오차 {error:.2f} ({'이상' if is_anomaly else '정상'})"
                })

            logger.info(f"예측 완료: {pred_value:.2f}")
            return result

        except Exception as e:
            logger.error(f"이상 탐지 오류: {str(e)}")
            return {"error": f"이상 탐지 중 오류 발생: {str(e)}"}

    def batch_detect(self,
                     water_level_sequences: List[List[float]],
                     actual_values: List[float]) -> Dict[str, Any]:
        """배치 이상 탐지

        Args:
            water_level_sequences: 수위 시퀀스 리스트
            actual_values: 실제값 리스트

        Returns:
            배치 탐지 결과
        """
        if not self._ensure_model_loaded():
            return {"error": "LSTM 모델을 로드할 수 없습니다"}

        results = []
        anomaly_count = 0

        for seq, actual in zip(water_level_sequences, actual_values):
            result = self.execute(
                water_levels=seq,
                actual_next_level=actual
            )

            if result.get("is_anomaly"):
                anomaly_count += 1

            results.append(result)

        return {
            "success": True,
            "total_samples": len(results),
            "anomaly_count": anomaly_count,
            "anomaly_ratio": anomaly_count / len(results) if results else 0,
            "results": results
        }

    def get_tool_config(self) -> Dict[str, Any]:
        """LLM 도구 설정 반환"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "water_levels": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "과거 수위 데이터 리스트 (최소 60개 권장, cm 단위)"
                        },
                        "pump_a": {
                            "type": "number",
                            "description": "펌프 A 상태 (0=OFF, 1=ON)"
                        },
                        "pump_b": {
                            "type": "number",
                            "description": "펌프 B 상태 (0=OFF, 1=ON)"
                        },
                        "actual_next_level": {
                            "type": "number",
                            "description": "실제 다음 수위값 (이상 탐지를 위해 필요)"
                        },
                        "threshold": {
                            "type": "number",
                            "description": "사용자 지정 임계값 (선택, 기본값은 자동 계산)"
                        }
                    },
                    "required": ["water_levels"]
                }
            }
        }

    def get_info(self) -> Dict[str, str]:
        """도구 정보 반환"""
        return {
            "name": self.name,
            "description": self.description,
            "model_path": self.model_path,
            "model_loaded": str(self.lstm_model is not None)
        }
