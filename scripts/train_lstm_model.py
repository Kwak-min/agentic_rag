# scripts/train_lstm_model.py - LSTM 모델 학습 스크립트

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader.water_data_loader import WaterDataLoader
from models.lstm_water_model import WaterLevelLSTM, AnomalyDetector
from utils.logger import setup_logger
import matplotlib.pyplot as plt
import numpy as np

logger = setup_logger(__name__)


def plot_history(history, save_path: str = None):
    """학습 히스토리 시각화"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Loss 그래프
    axes[0].plot(history.history['loss'], label='Train Loss')
    if 'val_loss' in history.history:
        axes[0].plot(history.history['val_loss'], label='Val Loss')
    axes[0].set_title('Model Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].legend()
    axes[0].grid(True)

    # MAE 그래프
    axes[1].plot(history.history['mae'], label='Train MAE')
    if 'val_mae' in history.history:
        axes[1].plot(history.history['val_mae'], label='Val MAE')
    axes[1].set_title('Model MAE')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('MAE')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"학습 히스토리 저장: {save_path}")

    plt.show()


def plot_predictions(y_true, y_pred, title: str = "Predictions", save_path: str = None):
    """예측 결과 시각화"""
    plt.figure(figsize=(15, 5))

    # 샘플 수 제한 (처음 500개만)
    n_samples = min(500, len(y_true))

    plt.plot(y_true[:n_samples], label='Actual', alpha=0.7)
    plt.plot(y_pred[:n_samples], label='Predicted', alpha=0.7)
    plt.title(title)
    plt.xlabel('Time Step')
    plt.ylabel('Water Level')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"예측 결과 저장: {save_path}")

    plt.show()


def main():
    """메인 학습 프로세스"""

    # ========== 1. 데이터 로드 ==========
    logger.info("=" * 80)
    logger.info("1단계: 데이터 로드")
    logger.info("=" * 80)

    water_data_path = project_root / "RNN-LSTM_model 분석" / "3.배수지 수위 데이터_WATERDATA.xlsx"

    loader = WaterDataLoader(str(water_data_path))

    # 모든 시트 로드 및 병합
    merged_data = loader.load_and_merge()

    # 전처리
    processed_data = loader.preprocess()

    logger.info(f"전처리 완료: {len(processed_data)}행")

    # ========== 2. LSTM 데이터 준비 ==========
    logger.info("\n" + "=" * 80)
    logger.info("2단계: LSTM 학습 데이터 준비")
    logger.info("=" * 80)

    # 가곡 배수지 데이터로 학습
    reservoir = 'gagok'
    seq_length = 60  # 과거 60분 데이터로 예측
    pred_length = 1  # 1분 후 예측

    dataset = loader.prepare_lstm_data(
        reservoir=reservoir,
        seq_length=seq_length,
        pred_length=pred_length,
        test_split=0.2
    )

    X_train = dataset['X_train']
    X_test = dataset['X_test']
    y_train = dataset['y_train']
    y_test = dataset['y_test']
    scaler = dataset['scaler']

    logger.info(f"X_train: {X_train.shape}")
    logger.info(f"X_test: {X_test.shape}")
    logger.info(f"y_train: {y_train.shape}")
    logger.info(f"y_test: {y_test.shape}")

    # ========== 3. 모델 학습 ==========
    logger.info("\n" + "=" * 80)
    logger.info("3단계: LSTM 모델 학습")
    logger.info("=" * 80)

    # 검증 데이터 분리 (Train의 20%)
    val_split = 0.2
    val_size = int(len(X_train) * val_split)
    X_val = X_train[-val_size:]
    y_val = y_train[-val_size:]
    X_train = X_train[:-val_size]
    y_train = y_train[:-val_size]

    logger.info(f"최종 Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # 모델 생성
    lstm_model = WaterLevelLSTM(
        seq_length=seq_length,
        pred_length=pred_length,
        lstm_units=128,
        dropout_rate=0.2
    )

    # 모델 구축
    input_shape = (X_train.shape[1], X_train.shape[2])
    lstm_model.build_model(input_shape)

    # 학습
    history = lstm_model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=100,
        batch_size=64,
        early_stopping_patience=15
    )

    # 학습 히스토리 시각화
    plot_dir = project_root / "lstm_model" / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    plot_history(history, save_path=str(plot_dir / "training_history.png"))

    # ========== 4. 모델 평가 ==========
    logger.info("\n" + "=" * 80)
    logger.info("4단계: 모델 평가")
    logger.info("=" * 80)

    # 테스트 데이터 평가
    metrics = lstm_model.evaluate(X_test, y_test)

    logger.info(f"테스트 결과:")
    logger.info(f"  - MSE: {metrics['mse']:.6f}")
    logger.info(f"  - RMSE: {metrics['rmse']:.6f}")
    logger.info(f"  - MAE: {metrics['mae']:.6f}")
    logger.info(f"  - MAPE: {metrics['mape']:.2f}%")

    # 예측 결과 시각화
    y_pred = lstm_model.predict(X_test)
    plot_predictions(
        y_test.flatten(),
        y_pred.flatten(),
        title=f"{reservoir.upper()} Reservoir - Test Set Predictions",
        save_path=str(plot_dir / "test_predictions.png")
    )

    # ========== 5. 이상 탐지 임계값 설정 ==========
    logger.info("\n" + "=" * 80)
    logger.info("5단계: 이상 탐지 임계값 설정")
    logger.info("=" * 80)

    # 정상 데이터로 임계값 계산 (Train 데이터 사용)
    anomaly_detector = AnomalyDetector(
        lstm_model=lstm_model,
        threshold_multiplier=3.0
    )

    anomaly_detector.fit_threshold(X_train, y_train)

    # 테스트 데이터 이상 탐지
    anomaly_result = anomaly_detector.detect(X_test, y_test)

    logger.info(f"이상 탐지 결과:")
    logger.info(f"  - 전체 샘플: {len(y_test)}")
    logger.info(f"  - 이상 샘플: {anomaly_result['anomaly_count']}")
    logger.info(f"  - 이상 비율: {anomaly_result['anomaly_ratio']*100:.2f}%")
    logger.info(f"  - 임계값: {anomaly_result['threshold']:.6f}")

    # ========== 6. 모델 저장 ==========
    logger.info("\n" + "=" * 80)
    logger.info("6단계: 모델 저장")
    logger.info("=" * 80)

    model_dir = project_root / "lstm_model"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / f"lstm_{reservoir}_model.h5"
    lstm_model.save(str(model_path))

    logger.info(f"모델 저장 완료: {model_path}")

    # ========== 7. 미래 예측 테스트 ==========
    logger.info("\n" + "=" * 80)
    logger.info("7단계: 미래 예측 테스트")
    logger.info("=" * 80)

    # 마지막 시퀀스로 10분 후까지 예측
    last_sequence = X_test[-1]  # (seq_length, features)
    future_predictions = lstm_model.predict_future(
        last_sequence,
        n_steps=10,
        scaler=scaler
    )

    logger.info(f"향후 10분 예측: {future_predictions}")

    # ========== 완료 ==========
    logger.info("\n" + "=" * 80)
    logger.info("✅ 모델 학습 완료!")
    logger.info("=" * 80)
    logger.info(f"모델 파일: {model_path}")
    logger.info(f"시각화 파일: {plot_dir}")
    logger.info(f"임계값: {anomaly_detector.threshold:.6f}")


if __name__ == "__main__":
    main()
