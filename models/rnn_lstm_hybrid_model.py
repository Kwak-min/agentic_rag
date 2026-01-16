# models/rnn_lstm_hybrid_model.py - RNN-LSTM 하이브리드 수위 예측 모델

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RNNLSTMHybridModel:
    """RNN-LSTM 하이브리드 수위 예측 모델

    RNN과 LSTM을 결합하여:
    - RNN: 빠른 시퀀스 패턴 학습 및 단기 의존성 포착
    - LSTM: 장기 의존성 학습 및 그래디언트 소실 문제 해결
    """

    def __init__(self,
                 seq_length: int = 60,
                 pred_length: int = 1,
                 rnn_units: int = 64,
                 lstm_units: int = 128,
                 dropout_rate: float = 0.2):
        """
        Args:
            seq_length: 입력 시퀀스 길이 (과거 60개 타임스텝)
            pred_length: 예측 시퀀스 길이 (다음 1개 타임스텝)
            rnn_units: SimpleRNN 레이어 유닛 수
            lstm_units: LSTM 레이어 유닛 수
            dropout_rate: 드롭아웃 비율
        """
        self.seq_length = seq_length
        self.pred_length = pred_length
        self.rnn_units = rnn_units
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.model = None
        self.history = None

        logger.info(f"RNN-LSTM 하이브리드 모델 초기화: seq_length={seq_length}, "
                   f"rnn_units={rnn_units}, lstm_units={lstm_units}")

    def build_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """RNN-LSTM 하이브리드 모델 구축

        Architecture:
        1. SimpleRNN Layer (빠른 초기 패턴 학습)
        2. LSTM Layer 1 (장기 의존성 학습)
        3. LSTM Layer 2 (심화 학습)
        4. Dense Layers (예측)

        Args:
            input_shape: (seq_length, n_features)

        Returns:
            Keras 모델
        """
        model = keras.Sequential([
            # RNN Layer (빠른 시퀀스 패턴 인식)
            layers.SimpleRNN(
                self.rnn_units,
                return_sequences=True,
                input_shape=input_shape,
                activation='tanh',
                name='rnn_layer'
            ),
            layers.Dropout(self.dropout_rate, name='rnn_dropout'),

            # LSTM Layer 1 (장기 의존성 학습)
            layers.LSTM(
                self.lstm_units,
                return_sequences=True,
                name='lstm_1'
            ),
            layers.Dropout(self.dropout_rate, name='lstm_1_dropout'),

            # LSTM Layer 2 (심화 학습)
            layers.LSTM(
                self.lstm_units // 2,
                return_sequences=False,
                name='lstm_2'
            ),
            layers.Dropout(self.dropout_rate, name='lstm_2_dropout'),

            # Dense Layer 1
            layers.Dense(64, activation='relu', name='dense_1'),
            layers.Dropout(self.dropout_rate, name='dense_1_dropout'),

            # Dense Layer 2
            layers.Dense(32, activation='relu', name='dense_2'),

            # Output Layer
            layers.Dense(self.pred_length, name='output')
        ])

        # 모델 컴파일
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mse', 'mape']
        )

        self.model = model
        total_params = model.count_params()
        logger.info(f"모델 구축 완료: {total_params:,}개 파라미터")

        # 모델 구조 출력
        model.summary(print_fn=logger.info)

        return model

    def train(self,
              X_train: np.ndarray,
              y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None,
              epochs: int = 100,
              batch_size: int = 32,
              early_stopping_patience: int = 15) -> keras.callbacks.History:
        """모델 학습

        Args:
            X_train: 학습 데이터 (samples, seq_length, features)
            y_train: 학습 레이블 (samples, pred_length)
            X_val: 검증 데이터
            y_val: 검증 레이블
            epochs: 학습 에포크
            batch_size: 배치 크기
            early_stopping_patience: 조기 종료 patience

        Returns:
            학습 히스토리
        """
        if self.model is None:
            # 모델이 없으면 자동 생성
            input_shape = (X_train.shape[1], X_train.shape[2])
            self.build_model(input_shape)

        # 콜백 설정
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                'best_rnn_lstm_model.keras',
                monitor='val_loss' if X_val is not None else 'loss',
                save_best_only=True,
                verbose=1
            )
        ]

        # 학습
        logger.info(f"학습 시작: epochs={epochs}, batch_size={batch_size}")
        logger.info(f"학습 데이터: X_train.shape={X_train.shape}, y_train.shape={y_train.shape}")

        if X_val is not None and y_val is not None:
            logger.info(f"검증 데이터: X_val.shape={X_val.shape}, y_val.shape={y_val.shape}")
            validation_data = (X_val, y_val)
        else:
            validation_data = None

        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        logger.info("학습 완료")

        # 최종 성능 출력
        if X_val is not None:
            final_val_loss = self.history.history['val_loss'][-1]
            final_val_mae = self.history.history['val_mae'][-1]
            logger.info(f"최종 검증 손실: {final_val_loss:.6f}, MAE: {final_val_mae:.6f}")

        return self.history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """예측 수행

        Args:
            X: 입력 데이터 (samples, seq_length, features)

        Returns:
            예측 결과 (samples, pred_length)
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        predictions = self.model.predict(X, verbose=0)
        return predictions

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """모델 평가

        Args:
            X_test: 테스트 데이터
            y_test: 테스트 레이블

        Returns:
            평가 메트릭 딕셔너리
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        # 예측
        y_pred = self.predict(X_test)

        # 메트릭 계산
        mse = np.mean((y_test - y_pred) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_test - y_pred))
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100

        # R² Score
        ss_res = np.sum((y_test - y_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2_score = 1 - (ss_res / (ss_tot + 1e-8))

        metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'r2_score': float(r2_score)
        }

        logger.info(f"평가 결과:")
        logger.info(f"  MSE:  {mse:.6f}")
        logger.info(f"  RMSE: {rmse:.6f}")
        logger.info(f"  MAE:  {mae:.6f}")
        logger.info(f"  MAPE: {mape:.2f}%")
        logger.info(f"  R²:   {r2_score:.4f}")

        return metrics

    def save(self, save_path: str):
        """모델 저장

        Args:
            save_path: 저장 경로 (.h5 또는 .keras)
        """
        if self.model is None:
            raise ValueError("저장할 모델이 없습니다.")

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        self.model.save(save_path)
        logger.info(f"모델 저장 완료: {save_path}")

    def load(self, model_path: str):
        """모델 로드

        Args:
            model_path: 모델 파일 경로
        """
        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")

        self.model = keras.models.load_model(model_path)
        logger.info(f"모델 로드 완료: {model_path}")

    def predict_future(self,
                       last_sequence: np.ndarray,
                       n_steps: int,
                       scaler=None) -> np.ndarray:
        """미래 여러 스텝 예측 (재귀적)

        Args:
            last_sequence: 마지막 시퀀스 (seq_length, features)
            n_steps: 예측할 스텝 수
            scaler: 역정규화를 위한 스케일러

        Returns:
            예측 결과 (n_steps,)
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        predictions = []
        current_seq = last_sequence.copy()

        for step in range(n_steps):
            # 예측 (1 step)
            pred = self.model.predict(
                current_seq.reshape(1, current_seq.shape[0], current_seq.shape[1]),
                verbose=0
            )
            predictions.append(pred[0, 0])

            # 다음 시퀀스 업데이트 (슬라이딩 윈도우)
            new_value = pred[0, 0]
            current_seq = np.roll(current_seq, -1, axis=0)
            current_seq[-1, 0] = new_value

        predictions = np.array(predictions)

        # 역정규화
        if scaler is not None:
            predictions = scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()

        return predictions


class RNNLSTMAnomalyDetector:
    """RNN-LSTM 기반 이상 탐지기"""

    def __init__(self,
                 rnn_lstm_model: RNNLSTMHybridModel,
                 threshold_multiplier: float = 3.0):
        """
        Args:
            rnn_lstm_model: 학습된 RNN-LSTM 하이브리드 모델
            threshold_multiplier: 임계값 배수 (표준편차의 N배)
        """
        self.rnn_lstm_model = rnn_lstm_model
        self.threshold_multiplier = threshold_multiplier
        self.threshold = None
        self.mean_error = None
        self.std_error = None

        logger.info(f"RNN-LSTM 이상 탐지기 초기화: threshold_multiplier={threshold_multiplier}")

    def fit_threshold(self, X_normal: np.ndarray, y_normal: np.ndarray):
        """정상 데이터로 임계값 계산

        Args:
            X_normal: 정상 입력 데이터
            y_normal: 정상 타겟 데이터
        """
        # 정상 데이터 예측
        y_pred = self.rnn_lstm_model.predict(X_normal)

        # 예측 오차 계산
        errors = np.abs(y_normal - y_pred).flatten()

        # 통계량 계산
        self.mean_error = np.mean(errors)
        self.std_error = np.std(errors)

        # 임계값 설정 (평균 + N * 표준편차)
        self.threshold = self.mean_error + self.threshold_multiplier * self.std_error

        logger.info(f"임계값 설정:")
        logger.info(f"  평균 오차: {self.mean_error:.6f}")
        logger.info(f"  표준편차: {self.std_error:.6f}")
        logger.info(f"  임계값: {self.threshold:.6f}")

    def detect(self, X: np.ndarray, y_actual: np.ndarray) -> Dict:
        """이상 탐지

        Args:
            X: 입력 데이터
            y_actual: 실제 값

        Returns:
            탐지 결과 딕셔너리
        """
        if self.threshold is None:
            raise ValueError("임계값이 설정되지 않았습니다. fit_threshold()를 먼저 호출하세요.")

        # 예측
        y_pred = self.rnn_lstm_model.predict(X)

        # 오차 계산
        errors = np.abs(y_actual - y_pred).flatten()

        # 이상 판정
        is_anomaly = errors > self.threshold

        # Z-score 계산
        z_scores = (errors - self.mean_error) / (self.std_error + 1e-8)

        # 이상 심각도 (1~5)
        severity = np.clip(np.ceil(z_scores), 1, 5).astype(int)

        result = {
            'is_anomaly': is_anomaly,
            'errors': errors,
            'predictions': y_pred.flatten(),
            'threshold': self.threshold,
            'z_scores': z_scores,
            'severity': severity,
            'anomaly_count': int(np.sum(is_anomaly)),
            'anomaly_ratio': float(np.mean(is_anomaly))
        }

        if np.any(is_anomaly):
            logger.warning(f"이상 탐지: {result['anomaly_count']}개 ({result['anomaly_ratio']*100:.2f}%)")
        else:
            logger.info("이상 없음")

        return result

    def detect_single(self, X: np.ndarray, y_actual: float) -> Dict:
        """단일 데이터 포인트 이상 탐지

        Args:
            X: 입력 시퀀스 (seq_length, features)
            y_actual: 실제 값

        Returns:
            탐지 결과
        """
        # 배치 차원 추가
        X_batch = X.reshape(1, X.shape[0], X.shape[1])
        y_batch = np.array([[y_actual]])

        # 이상 탐지
        result = self.detect(X_batch, y_batch)

        # 단일 결과 추출
        single_result = {
            'is_anomaly': bool(result['is_anomaly'][0]),
            'error': float(result['errors'][0]),
            'prediction': float(result['predictions'][0]),
            'actual': y_actual,
            'threshold': result['threshold'],
            'z_score': float(result['z_scores'][0]),
            'severity': int(result['severity'][0])
        }

        return single_result
