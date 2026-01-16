# api/anomaly_routes.py - 이상 탐지 API 라우트

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Any
from utils.logger import setup_logger
from tools.anomaly_detection_tool import LSTMAnomalyDetectionTool
from tools.ai_diagnosis_tool import AIDiagnosisTool
from services.database_connector import DatabaseConnector

logger = setup_logger(__name__)

# Blueprint 생성
anomaly_bp = Blueprint('anomaly', __name__, url_prefix='/api/anomaly')

# 도구 인스턴스 (전역)
anomaly_detector = None
ai_diagnosis = None
db_connector = None


def initialize_tools():
    """도구 초기화"""
    global anomaly_detector, ai_diagnosis, db_connector

    if anomaly_detector is None:
        logger.info("이상 탐지 도구 초기화...")
        anomaly_detector = LSTMAnomalyDetectionTool()

    if ai_diagnosis is None:
        logger.info("AI 진단 도구 초기화...")
        ai_diagnosis = AIDiagnosisTool()

    if db_connector is None:
        logger.info("DB 커넥터 초기화...")
        db_connector = DatabaseConnector()


# ========== API 엔드포인트 ==========

@anomaly_bp.route('/detect', methods=['POST'])
def detect_anomaly():
    """이상 탐지 API

    POST /api/anomaly/detect
    Body: {
        "water_levels": [70.5, 70.8, ...],
        "pump_a": 0 or 1,
        "pump_b": 0 or 1,
        "actual_next_level": 72.5 (optional)
    }
    """
    try:
        initialize_tools()

        data = request.get_json()

        if not data:
            return jsonify({"error": "요청 데이터가 없습니다"}), 400

        water_levels = data.get('water_levels')
        pump_a = data.get('pump_a', 0)
        pump_b = data.get('pump_b', 0)
        actual_next_level = data.get('actual_next_level')

        # 검증
        if not water_levels or not isinstance(water_levels, list):
            return jsonify({"error": "water_levels는 숫자 배열이어야 합니다"}), 400

        # 이상 탐지 실행
        result = anomaly_detector.execute(
            water_levels=water_levels,
            pump_a=pump_a,
            pump_b=pump_b,
            actual_next_level=actual_next_level
        )

        if "error" in result:
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"이상 탐지 API 오류: {e}", exc_info=True)
        return jsonify({"error": f"이상 탐지 중 오류 발생: {str(e)}"}), 500


@anomaly_bp.route('/status', methods=['GET'])
def get_status():
    """전체 배수지 상태 조회

    GET /api/anomaly/status
    """
    try:
        initialize_tools()

        # 실시간 DB에서 최신 데이터 조회
        reservoirs = {}

        for reservoir_key in ['gagok', 'haeryong', 'sangsa']:
            try:
                # 최근 60개 데이터 조회
                recent_data = db_connector.fetch_recent_water_data(
                    reservoir=reservoir_key,
                    limit=60
                )

                if not recent_data or len(recent_data) < 10:
                    # 데이터 부족
                    reservoirs[reservoir_key] = {
                        "status": "데이터 부족",
                        "level": 0,
                        "prediction": 0,
                        "error": 0,
                        "pump_a": 0,
                        "pump_b": 0,
                        "lastUpdate": None
                    }
                    continue

                # 수위 데이터 추출
                water_levels = [row['water_level'] for row in recent_data]
                last_level = water_levels[-1]

                # 펌프 상태
                pump_a = recent_data[-1].get('pump_a', 0)
                pump_b = recent_data[-1].get('pump_b', 0)

                # LSTM 예측
                prediction_result = anomaly_detector.execute(
                    water_levels=water_levels[:-1],  # 마지막 제외
                    pump_a=pump_a,
                    pump_b=pump_b,
                    actual_next_level=last_level
                )

                # 상태 판정
                if prediction_result.get("error"):
                    status = "분석 불가"
                    error = 0
                elif prediction_result.get("is_anomaly"):
                    status = prediction_result.get("status", "이상")
                    error = prediction_result.get("error", 0)
                else:
                    status = "정상"
                    error = prediction_result.get("error", 0)

                reservoirs[reservoir_key] = {
                    "status": status,
                    "level": float(last_level),
                    "prediction": float(prediction_result.get("prediction", 0)),
                    "error": float(error),
                    "pump_a": int(pump_a),
                    "pump_b": int(pump_b),
                    "lastUpdate": recent_data[-1].get('measured_at', datetime.now()).isoformat()
                }

            except Exception as e:
                logger.error(f"{reservoir_key} 상태 조회 실패: {e}")
                reservoirs[reservoir_key] = {
                    "status": "오류",
                    "level": 0,
                    "prediction": 0,
                    "error": 0,
                    "pump_a": 0,
                    "pump_b": 0,
                    "lastUpdate": None
                }

        return jsonify({
            "success": True,
            "reservoirs": reservoirs,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"상태 조회 API 오류: {e}", exc_info=True)
        return jsonify({"error": f"상태 조회 중 오류 발생: {str(e)}"}), 500


@anomaly_bp.route('/diagnose', methods=['POST'])
def diagnose_anomaly():
    """AI 진단 API

    POST /api/anomaly/diagnose
    Body: {
        "reservoir": "gagok",
        "anomaly_type": "급감",
        "water_level_change": -15.5,
        "pump_status": {"pump_a": 1, "pump_b": 0},
        "error_magnitude": 12.3
    }
    """
    try:
        initialize_tools()

        data = request.get_json()

        if not data:
            return jsonify({"error": "요청 데이터가 없습니다"}), 400

        reservoir = data.get('reservoir')
        anomaly_type = data.get('anomaly_type')
        water_level_change = data.get('water_level_change')
        pump_status = data.get('pump_status', {})
        error_magnitude = data.get('error_magnitude')

        # 진단 실행
        result = ai_diagnosis.execute(
            anomaly_type=anomaly_type,
            reservoir=reservoir,
            water_level_change=water_level_change,
            pump_status=pump_status,
            error_magnitude=error_magnitude
        )

        if "error" in result:
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"AI 진단 API 오류: {e}", exc_info=True)
        return jsonify({"error": f"AI 진단 중 오류 발생: {str(e)}"}), 500


@anomaly_bp.route('/batch-detect', methods=['POST'])
def batch_detect():
    """배치 이상 탐지 API

    POST /api/anomaly/batch-detect
    Body: {
        "sequences": [
            {"water_levels": [...], "actual": 70.5},
            {"water_levels": [...], "actual": 71.2},
            ...
        ]
    }
    """
    try:
        initialize_tools()

        data = request.get_json()

        if not data or 'sequences' not in data:
            return jsonify({"error": "sequences 데이터가 필요합니다"}), 400

        sequences = data['sequences']

        if not isinstance(sequences, list):
            return jsonify({"error": "sequences는 배열이어야 합니다"}), 400

        # 배치 처리
        water_level_sequences = [seq.get('water_levels', []) for seq in sequences]
        actual_values = [seq.get('actual', 0) for seq in sequences]

        result = anomaly_detector.batch_detect(
            water_level_sequences=water_level_sequences,
            actual_values=actual_values
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"배치 탐지 API 오류: {e}", exc_info=True)
        return jsonify({"error": f"배치 탐지 중 오류 발생: {str(e)}"}), 500


@anomaly_bp.route('/set-threshold', methods=['POST'])
def set_threshold():
    """임계값 설정 API

    POST /api/anomaly/set-threshold
    Body: {
        "normal_data": [70.5, 70.8, ...],
        "predictions": [70.6, 70.9, ...]
    }
    """
    try:
        initialize_tools()

        data = request.get_json()

        if not data:
            return jsonify({"error": "요청 데이터가 없습니다"}), 400

        normal_data = data.get('normal_data')
        predictions = data.get('predictions')

        if not normal_data or not predictions:
            return jsonify({"error": "normal_data와 predictions가 필요합니다"}), 400

        result = anomaly_detector.set_threshold(
            normal_data=normal_data,
            predictions=predictions
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"임계값 설정 API 오류: {e}", exc_info=True)
        return jsonify({"error": f"임계값 설정 중 오류 발생: {str(e)}"}), 500


@anomaly_bp.route('/model-info', methods=['GET'])
def get_model_info():
    """모델 정보 조회 API

    GET /api/anomaly/model-info
    """
    try:
        initialize_tools()

        info = anomaly_detector.get_info()

        return jsonify({
            "success": True,
            "model_info": info
        }), 200

    except Exception as e:
        logger.error(f"모델 정보 조회 API 오류: {e}", exc_info=True)
        return jsonify({"error": f"모델 정보 조회 중 오류 발생: {str(e)}"}), 500


# 헬스체크
@anomaly_bp.route('/health', methods=['GET'])
def health_check():
    """헬스체크 API"""
    try:
        initialize_tools()

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "anomaly_detector": "initialized" if anomaly_detector else "not initialized",
            "ai_diagnosis": "initialized" if ai_diagnosis else "not initialized"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
