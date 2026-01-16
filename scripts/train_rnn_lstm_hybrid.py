# scripts/train_rnn_lstm_hybrid.py - RNN-LSTM 하이브리드 모델 학습 스크립트

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader.water_data_loader import WaterDataLoader
from models.rnn_lstm_hybrid_model import RNNLSTMHybridModel, RNNLSTMAnomalyDetector
from utils.logger import setup_logger
import matplotlib.pyplot as plt
import numpy as np

logger = setup_logger(__name__)


def plot_history(history, save_path: str = None):
    """학습 히스토리 시각화"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Loss 그래프
    axes[0, 0].plot(history.history['loss'], label='Train Loss')
    if 'val_loss' in history.history:
        axes[0, 0].plot(history.history['val_loss'], label='Val Loss')
    axes[0, 0].set_title('Model Loss')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True)

    # MAE 그래프
    axes[0, 1].plot(history.history['mae'], label='Train MAE')
    if 'val_mae' in history.history:
        axes[0, 1].plot(history.history['val_mae'], label='Val MAE')
    axes[0, 1].set_title('Model MAE')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('MAE')
    axes[0, 1].legend()
    axes[0, 1].grid(True)

    # MSE 그래프
    axes[1, 0].plot(history.history['mse'], label='Train MSE')
    if 'val_mse' in history.history:
        axes[1, 0].plot(history.history['val_mse'], label='Val MSE')
    axes[1, 0].set_title('Model MSE')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('MSE')
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # MAPE 그래프
    axes[1, 1].plot(history.history['mape'], label='Train MAPE')
    if 'val_mape' in history.history:
        axes[1, 1].plot(history.history['val_mape'], label='Val MAPE')
    axes[1, 1].set_title('Model MAPE')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('MAPE (%)')
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"학습 히스토리 저장: {save_path}")

    plt.close()


def plot_predictions(y_true, y_pred, title: str = "Predictions", save_path: str = None):
    """예측 결과 시각화"""
    fig, axes = plt.subplots(2, 1, figsize=(15, 10))

    # 샘플 수 제한 (처음 500개만)
    n_samples = min(500, len(y_true))

    # 시계열 예측 그래프
    axes[0].plot(y_true[:n_samples], label='Actual', alpha=0.7, linewidth=2)
    axes[0].plot(y_pred[:n_samples], label='Predicted', alpha=0.7, linewidth=2)
    axes[0].set_title(f'{title} - Time Series')
    axes[0].set_xlabel('Time Step')
    axes[0].set_ylabel('Water Level')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Scatter Plot (Actual vs Predicted)
    axes[1].scatter(y_true[:n_samples], y_pred[:n_samples], alpha=0.5)
    axes[1].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()],
                 'r--', linewidth=2, label='Perfect Prediction')
    axes[1].set_title(f'{title} - Scatter Plot')
    axes[1].set_xlabel('Actual Water Level')
    axes[1].set_ylabel('Predicted Water Level')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"예측 결과 저장: {save_path}")

    plt.close()


def plot_anomaly_detection(y_true, y_pred, is_anomaly, save_path: str = None):
    """이상 탐지 결과 시각화"""
    plt.figure(figsize=(15, 6))

    n_samples = min(500, len(y_true))

    # 정상 데이터
    normal_mask = ~is_anomaly[:n_samples]
    plt.scatter(np.arange(n_samples)[normal_mask], y_true[:n_samples][normal_mask],
                c='blue', label='Normal', alpha=0.6, s=30)

    # 이상 데이터
    anomaly_mask = is_anomaly[:n_samples]
    plt.scatter(np.arange(n_samples)[anomaly_mask], y_true[:n_samples][anomaly_mask],
                c='red', label='Anomaly', alpha=0.8, s=50, marker='x')

    # 예측 선
    plt.plot(y_pred[:n_samples], label='Predicted', alpha=0.5, linewidth=2, color='green')

    plt.title('Anomaly Detection Results')
    plt.xlabel('Time Step')
    plt.ylabel('Water Level')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"이상 탐지 시각화 저장: {save_path}")

    plt.close()


def main():
    """메인 학습 프로세스"""

    # ========== 1. 데이터 로드 ==========
    logger.info("=" * 80)
    logger.info("1단계: 데이터 로드")
    logger.info("=" * 80)

    water_data_path = project_root / "RNN-LSTM_model 분석" / "3.배수지 수위 데이터_WATERDATA.xlsx"

    if not water_data_path.exists():
        logger.error(f"데이터 파일을 찾을 수 없습니다: {water_data_path}")
        return

    loader = WaterDataLoader(str(water_data_path))

    # 모든 시트 로드 및 병합
    merged_data = loader.load_and_merge()

    # 전처리
    processed_data = loader.preprocess()

    logger.info(f"전처리 완료: {len(processed_data)}행")

    # ========== 2. RNN-LSTM 데이터 준비 ==========
    logger.info("\n" + "=" * 80)
    logger.info("2단계: RNN-LSTM 학습 데이터 준비")
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

    # ========== 3. RNN-LSTM 하이브리드 모델 학습 ==========
    logger.info("\n" + "=" * 80)
    logger.info("3단계: RNN-LSTM 하이브리드 모델 학습")
    logger.info("=" * 80)

    # 검증 데이터 분리 (Train의 20%)
    val_split = 0.2
    val_size = int(len(X_train) * val_split)
    X_val = X_train[-val_size:]
    y_val = y_train[-val_size:]
    X_train = X_train[:-val_size]
    y_train = y_train[:-val_size]

    logger.info(f"최종 Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # RNN-LSTM 하이브리드 모델 생성
    hybrid_model = RNNLSTMHybridModel(
        seq_length=seq_length,
        pred_length=pred_length,
        rnn_units=64,      # RNN 유닛 수
        lstm_units=128,    # LSTM 유닛 수
        dropout_rate=0.2
    )

    # 모델 구축
    input_shape = (X_train.shape[1], X_train.shape[2])
    hybrid_model.build_model(input_shape)

    # 학습
    history = hybrid_model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=100,
        batch_size=64,
        early_stopping_patience=15
    )

    # 학습 히스토리 시각화
    plot_dir = project_root / "rnn_lstm_model" / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    plot_history(history, save_path=str(plot_dir / "training_history.png"))

    # ========== 4. 모델 평가 ==========
    logger.info("\n" + "=" * 80)
    logger.info("4단계: 모델 평가")
    logger.info("=" * 80)

    # 테스트 데이터 평가
    metrics = hybrid_model.evaluate(X_test, y_test)

    logger.info(f"테스트 결과:")
    logger.info(f"  - MSE:  {metrics['mse']:.6f}")
    logger.info(f"  - RMSE: {metrics['rmse']:.6f}")
    logger.info(f"  - MAE:  {metrics['mae']:.6f}")
    logger.info(f"  - MAPE: {metrics['mape']:.2f}%")
    logger.info(f"  - R²:   {metrics['r2_score']:.4f}")

    # 예측 결과 시각화
    y_pred = hybrid_model.predict(X_test)
    plot_predictions(
        y_test.flatten(),
        y_pred.flatten(),
        title=f"{reservoir.upper()} Reservoir - RNN-LSTM Test Predictions",
        save_path=str(plot_dir / "test_predictions.png")
    )

    # ========== 5. 이상 탐지 임계값 설정 ==========
    logger.info("\n" + "=" * 80)
    logger.info("5단계: 이상 탐지 임계값 설정")
    logger.info("=" * 80)

    # 정상 데이터로 임계값 계산 (Train 데이터 사용)
    anomaly_detector = RNNLSTMAnomalyDetector(
        rnn_lstm_model=hybrid_model,
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

    # 이상 탐지 시각화
    plot_anomaly_detection(
        y_test.flatten(),
        y_pred.flatten(),
        anomaly_result['is_anomaly'],
        save_path=str(plot_dir / "anomaly_detection.png")
    )

    # ========== 6. 모델 저장 ==========
    logger.info("\n" + "=" * 80)
    logger.info("6단계: 모델 저장")
    logger.info("=" * 80)

    model_dir = project_root / "rnn_lstm_model"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / f"rnn_lstm_{reservoir}_model.keras"
    hybrid_model.save(str(model_path))

    logger.info(f"모델 저장 완료: {model_path}")

    # 임계값 정보도 저장
    import json
    threshold_info = {
        'threshold': float(anomaly_detector.threshold),
        'mean_error': float(anomaly_detector.mean_error),
        'std_error': float(anomaly_detector.std_error),
        'threshold_multiplier': anomaly_detector.threshold_multiplier,
        'reservoir': reservoir
    }

    threshold_path = model_dir / f"rnn_lstm_{reservoir}_threshold.json"
    with open(threshold_path, 'w', encoding='utf-8') as f:
        json.dump(threshold_info, f, indent=2)

    logger.info(f"임계값 정보 저장: {threshold_path}")

    # ========== 7. 미래 예측 테스트 ==========
    logger.info("\n" + "=" * 80)
    logger.info("7단계: 미래 예측 테스트")
    logger.info("=" * 80)

    # 마지막 시퀀스로 10분 후까지 예측
    last_sequence = X_test[-1]  # (seq_length, features)
    future_predictions = hybrid_model.predict_future(
        last_sequence,
        n_steps=10,
        scaler=scaler
    )

    logger.info(f"향후 10분 예측:")
    for i, pred in enumerate(future_predictions, 1):
        logger.info(f"  {i}분 후: {pred:.2f}")

    # ========== 완료 ==========
    logger.info("\n" + "=" * 80)
    logger.info("✅ RNN-LSTM 하이브리드 모델 학습 완료!")
    logger.info("=" * 80)
    logger.info(f"모델 파일: {model_path}")
    logger.info(f"임계값 파일: {threshold_path}")
    logger.info(f"시각화 파일: {plot_dir}")
    logger.info(f"임계값: {anomaly_detector.threshold:.6f}")
    logger.info(f"테스트 R² Score: {metrics['r2_score']:.4f}")


if __name__ == "__main__":
    main()
