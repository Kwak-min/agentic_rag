# services/realtime_anomaly_monitor.py - 실시간 이상 탐지 모니터링 서비스

import threading
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from utils.logger import setup_logger
from tools.anomaly_detection_tool import LSTMAnomalyDetectionTool
from services.database_connector import DatabaseConnector

logger = setup_logger(__name__)


class RealtimeAnomalyMonitor:
    """실시간 이상 탐지 모니터링 서비스

    주기적으로 데이터베이스에서 최신 수위 데이터를 조회하여
    이상 여부를 탐지하고, 콜백 함수를 통해 알림을 전송합니다.
    """

    def __init__(self,
                 check_interval: int = 60,
                 on_anomaly_detected: Optional[Callable] = None):
        """
        Args:
            check_interval: 체크 간격 (초)
            on_anomaly_detected: 이상 탐지 시 호출할 콜백 함수
        """
        self.check_interval = check_interval
        self.on_anomaly_detected = on_anomaly_detected
        self.is_running = False
        self.monitor_thread = None

        # 도구 초기화
        self.anomaly_detector = LSTMAnomalyDetectionTool()
        self.db_connector = DatabaseConnector()

        # 마지막 상태 캐시 (중복 알림 방지)
        self.last_status = {}

        logger.info(f"실시간 이상 탐지 모니터 초기화 완료 (체크 간격: {check_interval}초)")

    def start(self):
        """모니터링 시작"""
        if self.is_running:
            logger.warning("모니터링이 이미 실행 중입니다.")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("실시간 이상 탐지 모니터링 시작")

    def stop(self):
        """모니터링 중지"""
        if not self.is_running:
            return

        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("실시간 이상 탐지 모니터링 중지")

    def _monitor_loop(self):
        """모니터링 루프"""
        logger.info("모니터링 루프 시작")

        while self.is_running:
            try:
                # 모든 배수지 체크
                for reservoir_key in ['gagok', 'haeryong', 'sangsa']:
                    self._check_reservoir(reservoir_key)

                # 대기
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}", exc_info=True)
                time.sleep(self.check_interval)

    def _check_reservoir(self, reservoir_key: str):
        """배수지 이상 탐지 체크

        Args:
            reservoir_key: 배수지 키 (gagok, haeryong, sangsa)
        """
        try:
            # 최근 60개 데이터 조회
            recent_data = self.db_connector.fetch_recent_water_data(
                reservoir=reservoir_key,
                limit=60
            )

            if not recent_data or len(recent_data) < 10:
                logger.debug(f"{reservoir_key}: 데이터 부족")
                return

            # 수위 데이터 추출
            water_levels = [row['water_level'] for row in recent_data]
            last_level = water_levels[-1]

            # 펌프 상태
            pump_a = recent_data[-1].get('pump_a', 0)
            pump_b = recent_data[-1].get('pump_b', 0)

            # LSTM 예측 & 이상 탐지
            result = self.anomaly_detector.execute(
                water_levels=water_levels[:-1],  # 마지막 제외
                pump_a=pump_a,
                pump_b=pump_b,
                actual_next_level=last_level
            )

            if result.get("error"):
                logger.error(f"{reservoir_key}: 이상 탐지 실패 - {result.get('error')}")
                return

            # 상태 판정
            is_anomaly = result.get("is_anomaly", False)
            status_code = result.get("status_code", "normal")
            severity = result.get("severity", 1)

            # 상태 변화 체크 (중복 알림 방지)
            last_state = self.last_status.get(reservoir_key, {})
            last_status_code = last_state.get("status_code", "normal")

            # 상태가 변경되었거나, 심각한 이상인 경우 알림
            if status_code != last_status_code or (is_anomaly and severity >= 3):
                # 알림 데이터 구성
                anomaly_data = {
                    "reservoir": reservoir_key,
                    "reservoir_name": self._get_reservoir_name(reservoir_key),
                    "status": result.get("status", "정상"),
                    "status_code": status_code,
                    "is_anomaly": is_anomaly,
                    "severity": severity,
                    "level": float(last_level),
                    "prediction": float(result.get("prediction", 0)),
                    "error": float(result.get("error", 0)),
                    "threshold": float(result.get("threshold", 0)),
                    "pump_a": int(pump_a),
                    "pump_b": int(pump_b),
                    "timestamp": datetime.now().isoformat(),
                    "message": result.get("anomaly_summary", "")
                }

                # 콜백 실행
                if self.on_anomaly_detected:
                    try:
                        self.on_anomaly_detected(anomaly_data)
                    except Exception as e:
                        logger.error(f"알림 콜백 실행 오류: {e}", exc_info=True)

                # 로그 기록
                if is_anomaly:
                    logger.warning(f"🚨 {reservoir_key} 이상 탐지: {result.get('status')} "
                                  f"(오차: {result.get('error'):.2f}, 임계값: {result.get('threshold'):.2f})")
                else:
                    logger.info(f"✅ {reservoir_key} 정상 복귀")

            # 상태 업데이트
            self.last_status[reservoir_key] = {
                "status_code": status_code,
                "severity": severity,
                "checked_at": datetime.now()
            }

        except Exception as e:
            logger.error(f"{reservoir_key} 체크 오류: {e}", exc_info=True)

    def _get_reservoir_name(self, reservoir_key: str) -> str:
        """배수지 이름 반환"""
        names = {
            "gagok": "가곡 배수지",
            "haeryong": "해룡 배수지",
            "sangsa": "상사 배수지"
        }
        return names.get(reservoir_key, reservoir_key)

    def get_current_status(self) -> Dict[str, Any]:
        """현재 모니터링 상태 반환"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "last_status": self.last_status,
            "monitored_reservoirs": ["gagok", "haeryong", "sangsa"]
        }
