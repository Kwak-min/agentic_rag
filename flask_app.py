# flask_app.py - Flask API 백엔드

import os
import sys
import json
import asyncio
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading
import time

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from models.lm_studio import LMStudioClient
from models.ollama_client import OllamaClient
from models.finetuned_model_client import FinetunedModelClient
from core.orchestrator import Orchestrator
from services.autonomous_agent import AutonomousAgent
from storage.postgresql_storage import PostgreSQLStorage
from utils.logger import setup_logger
from utils.state_manager import get_state_manager
from config import (
    print_config, USE_OLLAMA, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME,
    USE_FINETUNED_MODEL, FINETUNED_BASE_MODEL, FINETUNED_ADAPTER_PATH
)
from auth import get_auth_manager

logger = setup_logger(__name__)

# Flask 앱 초기화
app = Flask(__name__)

# JWT 설정
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=3)  # 3시간으로 변경

CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# JWT 초기화
jwt = JWTManager(app)

# 인증 관리자는 시스템 초기화 시 storage와 함께 초기화
auth_manager = None

# 전역 변수
lm_client: Optional[LMStudioClient] = None
orchestrator: Optional[Orchestrator] = None
autonomous_agent: Optional[AutonomousAgent] = None
storage: Optional[PostgreSQLStorage] = None
system_initialized = False
anomaly_monitor = None  # 실시간 이상 탐지 모니터


def initialize_system():
    """시스템 초기화"""
    global lm_client, orchestrator, autonomous_agent, storage, system_initialized, auth_manager

    try:
        logger.info("=== Flask 백엔드 시스템 초기화 시작 ===")

        # AI 클라이언트 초기화 (파인튜닝 모델, Ollama, 또는 LM Studio)
        if USE_FINETUNED_MODEL:
            logger.info("1/6: 파인튜닝 모델 클라이언트 초기화 중...")
            try:
                lm_client = FinetunedModelClient(
                    base_model_name=FINETUNED_BASE_MODEL,
                    adapter_path=FINETUNED_ADAPTER_PATH
                )
                logger.info(f"1/6: 파인튜닝 모델 클라이언트 초기화 완료")
            except Exception as e:
                logger.error(f"파인튜닝 모델 로드 실패: {str(e)}")
                logger.warning("Ollama로 폴백합니다...")
                lm_client = OllamaClient(base_url=OLLAMA_BASE_URL, model_name=OLLAMA_MODEL_NAME)
                logger.info(f"1/6: Ollama 클라이언트로 폴백 완료 (모델: {OLLAMA_MODEL_NAME})")
        elif USE_OLLAMA:
            logger.info("1/6: Ollama 클라이언트 초기화 중...")
            lm_client = OllamaClient(base_url=OLLAMA_BASE_URL, model_name=OLLAMA_MODEL_NAME)
            logger.info(f"1/6: Ollama 클라이언트 초기화 완료 (모델: {OLLAMA_MODEL_NAME})")
        else:
            logger.info("1/6: LM Studio 클라이언트 초기화 중...")
            lm_client = LMStudioClient()
            logger.info("1/6: LM Studio 클라이언트 초기화 완료")

        # PostgreSQLStorage 초기화 (오케스트레이터보다 먼저)
        logger.info("2/6: PostgreSQL 스토리지 초기화 중...")
        storage = PostgreSQLStorage.get_instance()
        logger.info("2/6: PostgreSQL 스토리지 초기화 완료")

        # Auth Manager 초기화 (storage 필요)
        logger.info("3/6: 인증 관리자 초기화 중...")
        from auth.auth_manager import AuthManager
        auth_manager = AuthManager(storage=storage)
        logger.info("3/6: 인증 관리자 초기화 완료")

        # 오케스트레이터 초기화 (storage 전달)
        logger.info("4/6: 오케스트레이터 초기화 중...")
        orchestrator = Orchestrator(lm_client, storage=storage)
        logger.info("4/6: 오케스트레이터 초기화 완료")

        # 자율 에이전트 초기화 (나중에 처리)
        logger.info("5/6: 자율 에이전트 초기화 스킵 (나중에 초기화)")
        autonomous_agent = None

        # 글로벌 상태 업데이트
        logger.info("6/6: 상태 관리 초기화 중...")
        try:
            state_manager = get_state_manager()
            state_manager.update_system_status(True, True)
            logger.info("6/6: 상태 관리 초기화 완료")
        except Exception as e:
            logger.warning(f"상태 관리 초기화 실패 (계속 진행): {e}")

        system_initialized = True
        logger.info("=== Flask 백엔드 시스템 초기화 성공 ===")
        return True

    except Exception as e:
        logger.error(f"시스템 초기화 오류: {str(e)}", exc_info=True)
        system_initialized = False
        return False


# ============================================
# REST API 엔드포인트
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "system_initialized": system_initialized,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    """로그인 - JWT 토큰 발급"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "사용자명과 비밀번호가 필요합니다"}), 400

    user = auth_manager.verify_user(username, password)
    if user:
        access_token = create_access_token(
            identity=username,
            additional_claims={"role": user["role"], "name": user["name"]}
        )
        return jsonify({
            "access_token": access_token,
            "user": {
                "username": username,
                "role": user["role"],
                "name": user["name"]
            }
        }), 200
    else:
        return jsonify({"error": "잘못된 사용자명 또는 비밀번호"}), 401


@app.route('/api/initialize', methods=['POST'])
def api_initialize():
    """시스템 초기화"""
    success = initialize_system()
    return jsonify({
        "success": success,
        "message": "시스템 초기화 성공" if success else "시스템 초기화 실패"
    })


@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """시스템 상태 조회"""
    model_info = {}
    if lm_client:
        model_info = lm_client.get_model_info()

    return jsonify({
        "initialized": system_initialized,
        "model_info": model_info,
        "config": print_config() if system_initialized else {}
    })


@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    """채팅 메시지 처리 (JWT 인증 필요)"""
    if not system_initialized or not orchestrator:
        return jsonify({"error": "시스템이 초기화되지 않았습니다"}), 400

    current_user = get_jwt_identity()
    logger.info(f"채팅 요청 - 사용자: {current_user}")

    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "메시지가 비어있습니다"}), 400

    try:
        # 오케스트레이터를 통해 응답 생성 (동기 방식)
        result = orchestrator.process_query_sync(user_message, stream=False)

        return jsonify({
            "response": result.get("response", ""),
            "tool_calls": result.get("tool_calls", []),
            "tool_results": result.get("tool_results", {}),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/water/current', methods=['GET'])
@jwt_required()
def get_current_water_level():
    """현재 수위 조회 (JWT 인증 필요)"""
    if not storage:
        return jsonify({"error": "스토리지가 초기화되지 않았습니다"}), 400

    try:
        # water 테이블에서 최근 데이터 조회
        conn = storage._connection
        cur = conn.cursor()

        query = """
        SELECT measured_at, gagok_water_level, gagok_pump_a, gagok_pump_b,
               haeryong_water_level, haeryong_pump_a, haeryong_pump_b
        FROM water
        ORDER BY measured_at DESC
        LIMIT 1
        """
        cur.execute(query)
        row = cur.fetchone()

        result = []
        if row:
            # 가곡 배수지 데이터
            result.append({
                "location": "gagok",
                "water_level": float(row[1]) if row[1] is not None else 0.0,
                "pump_status": float(row[2] or 0) + float(row[3] or 0),
                "timestamp": row[0].isoformat()
            })
            # 해룡 배수지 데이터
            result.append({
                "location": "haeryong",
                "water_level": float(row[4]) if row[4] is not None else 0.0,
                "pump_status": float(row[5] or 0) + float(row[6] or 0),
                "timestamp": row[0].isoformat()
            })

        cur.close()
        conn.commit()
        return jsonify({"data": result})

    except Exception as e:
        logger.error(f"수위 조회 오류: {e}", exc_info=True)
        if storage and storage._connection:
            storage._connection.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/water/history', methods=['GET'])
@jwt_required()
def get_water_history():
    """수위 이력 조회 (JWT 인증 필요)"""
    if not storage:
        return jsonify({"error": "스토리지가 초기화되지 않았습니다"}), 400

    hours = request.args.get('hours', default=24, type=int)

    try:
        conn = storage._connection
        cur = conn.cursor()

        query = """
        SELECT measured_at, gagok_water_level, gagok_pump_a, gagok_pump_b,
               haeryong_water_level, haeryong_pump_a, haeryong_pump_b
        FROM water
        WHERE measured_at >= NOW() - INTERVAL '%s hours'
        ORDER BY measured_at ASC
        """
        cur.execute(query, (hours,))
        rows = cur.fetchall()

        result = []
        for row in rows:
            # 가곡 배수지 데이터
            result.append({
                "location": "gagok",
                "water_level": float(row[1]) if row[1] is not None else 0.0,
                "pump_status": float(row[2] or 0) + float(row[3] or 0),
                "timestamp": row[0].isoformat()
            })
            # 해룡 배수지 데이터
            result.append({
                "location": "haeryong",
                "water_level": float(row[4]) if row[4] is not None else 0.0,
                "pump_status": float(row[5] or 0) + float(row[6] or 0),
                "timestamp": row[0].isoformat()
            })

        cur.close()
        conn.commit()
        return jsonify({"data": result})

    except Exception as e:
        logger.error(f"수위 이력 조회 오류: {e}", exc_info=True)
        if storage and storage._connection:
            storage._connection.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/files', methods=['GET'])
@jwt_required()
def list_files():
    """파일 목록 조회 (JWT 인증 필요)"""
    if not storage:
        return jsonify({"error": "스토리지가 초기화되지 않았습니다"}), 400

    try:
        files = storage.list_files()
        return jsonify({"files": files})

    except Exception as e:
        logger.error(f"파일 목록 조회 오류: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/files/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """파일 업로드 (JWT 인증 필요)"""
    if not storage:
        return jsonify({"error": "스토리지가 초기화되지 않았습니다"}), 400

    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다"}), 400

    file = request.files['file']

    try:
        # 파일 저장 로직 (기존 storage 메서드 사용)
        file_content = file.read()
        file_id = storage.add_document(
            filename=file.filename,
            content=file_content.decode('utf-8') if file.filename.endswith('.txt') else None,
            metadata={"uploaded_at": datetime.now().isoformat()}
        )

        return jsonify({
            "success": True,
            "file_id": file_id,
            "filename": file.filename
        })

    except Exception as e:
        logger.error(f"파일 업로드 오류: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================
# 점검 로그 API
# ============================================

@app.route('/api/inspection-logs', methods=['GET'])
@jwt_required()
def get_inspection_logs():
    """점검 로그 목록 조회 (JWT 인증 필요)"""
    if not storage:
        return jsonify({"error": "스토리지가 초기화되지 않았습니다"}), 400

    try:
        conn = storage._connection
        cur = conn.cursor()

        # 최근 로그부터 조회
        query = """
        SELECT id, location, datetime, issue_location, issue_description, inspection_action, handler, created_at
        FROM inspection_logs
        ORDER BY datetime DESC
        LIMIT 100
        """
        cur.execute(query)
        rows = cur.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "location": row[1],
                "datetime": row[2].isoformat(),
                "issue_location": row[3],
                "issue_description": row[4],
                "inspection_action": row[5],
                "handler": row[6],
                "created_at": row[7].isoformat()
            })

        cur.close()
        conn.commit()
        return jsonify({"data": result})

    except Exception as e:
        logger.error(f"점검 로그 조회 오류: {e}", exc_info=True)
        if storage and storage._connection:
            storage._connection.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/inspection-logs', methods=['POST'])
@jwt_required()
def create_inspection_log():
    """점검 로그 생성 (JWT 인증 필요)"""
    if not storage:
        return jsonify({"error": "스토리지가 초기화되지 않았습니다"}), 400

    data = request.json
    location = data.get('location')
    log_datetime = data.get('datetime')
    issue_location = data.get('issue_location')
    issue_description = data.get('issue_description')
    inspection_action = data.get('inspection_action')
    handler = data.get('handler')

    if not all([location, log_datetime, issue_location, issue_description, inspection_action, handler]):
        return jsonify({"error": "모든 필드를 입력해주세요"}), 400

    try:
        conn = storage._connection
        cur = conn.cursor()

        query = """
        INSERT INTO inspection_logs (location, datetime, issue_location, issue_description, inspection_action, handler)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        cur.execute(query, (location, log_datetime, issue_location, issue_description, inspection_action, handler))
        log_id = cur.fetchone()[0]

        cur.close()
        conn.commit()
        return jsonify({"success": True, "id": log_id}), 201

    except Exception as e:
        logger.error(f"점검 로그 생성 오류: {e}", exc_info=True)
        if storage and storage._connection:
            storage._connection.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/inspection-logs/<int:log_id>', methods=['DELETE'])
@jwt_required()
def delete_inspection_log(log_id):
    """점검 로그 삭제 (JWT 인증 필요)"""
    if not storage:
        return jsonify({"error": "스토리지가 초기화되지 않았습니다"}), 400

    try:
        conn = storage._connection
        cur = conn.cursor()

        query = "DELETE FROM inspection_logs WHERE id = %s"
        cur.execute(query, (log_id,))

        cur.close()
        conn.commit()
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"점검 로그 삭제 오류: {e}", exc_info=True)
        if storage and storage._connection:
            storage._connection.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/parse-kakao-log', methods=['POST'])
@jwt_required()
def parse_kakao_log():
    """카카오톡 메시지를 파싱하여 점검 로그 추출 및 자동 저장 (JWT 인증 필요)"""
    data = request.json
    kakao_text = data.get('kakao_text', '')
    auto_save = data.get('auto_save', True)  # 자동 저장 옵션 (기본값: True)

    if not kakao_text:
        return jsonify({"error": "카카오톡 텍스트가 필요합니다"}), 400

    try:
        # LLM을 사용하여 카톡 메시지 파싱
        from models.ollama_client import OllamaClient

        ollama_client = OllamaClient()

        parse_prompt = f"""다음은 카카오톡 대화 내용입니다. 이 대화에서 시설 점검/문제/조치와 관련된 내용을 추출하여 점검 로그로 변환해주세요.

카카오톡 대화:
{kakao_text}

다음 형식의 JSON 배열로 응답해주세요. 여러 개의 점검 로그가 있다면 모두 추출하세요:
[
  {{
    "location": "장소 (예: 가곡 배수지, 해룡 배수지)",
    "datetime": "YYYY-MM-DDTHH:MM 형식",
    "issue_location": "문제 부위 (예: 펌프 A, 센서, 배관)",
    "issue_description": "발견된 문제 설명",
    "inspection_action": "실시한 점검 및 조치 내용",
    "handler": "처리자/담당자 이름",
    "confidence": 0.0~1.0 사이의 신뢰도
  }}
]

규칙:
- 대화에서 명확하게 확인되는 정보만 채워주세요
- 확인되지 않은 필드는 null로 설정하거나, 불명확하면 "미확인"으로 설정하세요
- 날짜/시간 정보가 상대적이면 (예: "오늘", "어제") 현재 시각 기준으로 변환하세요
- 여러 사람의 대화를 종합하여 하나의 완전한 로그를 만들어주세요
- 반드시 유효한 JSON 배열만 반환하세요"""

        response = ollama_client.chat(
            model="qwen2.5:7b",
            messages=[{
                "role": "user",
                "content": parse_prompt
            }],
            options={
                "temperature": 0.3
            }
        )

        response_text = response['message']['content'].strip()

        # JSON 파싱
        import json
        import re

        # JSON 배열 추출 (마크다운 코드 블록 제거)
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            logs = json.loads(json_match.group(0))
        else:
            logs = json.loads(response_text)

        # 자동 저장 처리
        saved_logs = []
        failed_logs = []

        if auto_save and storage:
            conn = storage._connection
            cur = conn.cursor()

            for log in logs:
                try:
                    # 필수 필드 기본값 설정
                    location = log.get('location') or '미확인'
                    log_datetime = log.get('datetime') or datetime.now().isoformat()
                    issue_location = log.get('issue_location') or '미확인'
                    issue_description = log.get('issue_description') or '내용 미확인'
                    inspection_action = log.get('inspection_action') or '조치 미확인'
                    handler = log.get('handler') or '담당자 미확인'
                    confidence = log.get('confidence', 0.5)

                    # DB에 저장
                    query = """
                    INSERT INTO inspection_logs (location, datetime, issue_location, issue_description, inspection_action, handler)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """
                    cur.execute(query, (location, log_datetime, issue_location, issue_description, inspection_action, handler))
                    log_id = cur.fetchone()[0]

                    saved_logs.append({
                        "id": log_id,
                        "location": location,
                        "datetime": log_datetime,
                        "issue_location": issue_location,
                        "issue_description": issue_description,
                        "inspection_action": inspection_action,
                        "handler": handler,
                        "confidence": confidence
                    })

                except Exception as save_error:
                    logger.error(f"로그 저장 실패: {save_error}")
                    failed_logs.append({
                        "log": log,
                        "error": str(save_error)
                    })

            cur.close()
            conn.commit()

            return jsonify({
                "success": True,
                "auto_saved": True,
                "saved_count": len(saved_logs),
                "failed_count": len(failed_logs),
                "saved_logs": saved_logs,
                "failed_logs": failed_logs
            })
        else:
            # 자동 저장 안함 - 기존 방식
            for log in logs:
                missing_fields = []
                if not log.get('location'):
                    missing_fields.append('location')
                if not log.get('datetime'):
                    missing_fields.append('datetime')
                if not log.get('issue_location'):
                    missing_fields.append('issue_location')
                if not log.get('issue_description'):
                    missing_fields.append('issue_description')
                if not log.get('inspection_action'):
                    missing_fields.append('inspection_action')
                if not log.get('handler'):
                    missing_fields.append('handler')

                log['missing_fields'] = missing_fields

                # confidence가 없으면 0.5로 설정
                if 'confidence' not in log:
                    log['confidence'] = 0.5

            return jsonify({
                "success": True,
                "auto_saved": False,
                "logs": logs,
                "count": len(logs)
            })

    except Exception as e:
        logger.error(f"카톡 파싱 오류: {e}", exc_info=True)
        if storage and storage._connection:
            storage._connection.rollback()
        return jsonify({"error": str(e)}), 500


# ============================================
# 시스템 프롬프트 관리 API
# ============================================

@app.route('/api/prompts', methods=['GET'])
@jwt_required()
def get_prompts():
    """시스템 프롬프트 조회 (관리자만)"""
    try:
        # 사용자 권한 확인
        username = get_jwt_identity()
        user = auth_manager.get_user_info(username)

        if not user or user.get('role') != 'admin':
            return jsonify({"error": "관리자 권한이 필요합니다"}), 403

        if not storage:
            return jsonify({"error": "Storage가 초기화되지 않았습니다"}), 500

        # DB에서 전체 프롬프트 조회
        query = """
            SELECT id, prompt_type, prompt_content, description, updated_by, updated_at
            FROM system_prompts
            ORDER BY prompt_type
        """
        results = storage.execute_query(query, fetchall=True)

        prompts = []
        if results:
            for row in results:
                # RealDictRow 또는 튜플 모두 지원
                if hasattr(row, 'keys'):
                    prompts.append({
                        "id": row['id'],
                        "prompt_type": row['prompt_type'],
                        "prompt_content": row['prompt_content'],
                        "description": row['description'],
                        "updated_by": row['updated_by'],
                        "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                    })
                else:
                    prompts.append({
                        "id": row[0],
                        "prompt_type": row[1],
                        "prompt_content": row[2],
                        "description": row[3],
                        "updated_by": row[4],
                        "updated_at": row[5].isoformat() if row[5] else None
                    })

        return jsonify({
            "success": True,
            "prompts": prompts,
            "count": len(prompts)
        })

    except Exception as e:
        logger.error(f"프롬프트 조회 오류: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/prompts/<prompt_type>', methods=['PUT'])
@jwt_required()
def update_prompt(prompt_type):
    """시스템 프롬프트 수정 (관리자만)"""
    try:
        # 사용자 권한 확인
        username = get_jwt_identity()
        user = auth_manager.get_user_info(username)

        if not user or user.get('role') != 'admin':
            return jsonify({"error": "관리자 권한이 필요합니다"}), 403

        if not storage:
            return jsonify({"error": "Storage가 초기화되지 않았습니다"}), 500

        data = request.json
        prompt_content = data.get('prompt_content')

        if not prompt_content:
            return jsonify({"error": "prompt_content가 필요합니다"}), 400

        # DB 업데이트
        query = """
            UPDATE system_prompts
            SET prompt_content = %s, updated_by = %s, updated_at = NOW()
            WHERE prompt_type = %s
        """
        storage.execute_query(query, (prompt_content, username, prompt_type), commit=True)

        logger.info(f"프롬프트 업데이트: {prompt_type} by {username}")

        return jsonify({
            "success": True,
            "message": f"프롬프트 '{prompt_type}'가 성공적으로 업데이트되었습니다"
        })

    except Exception as e:
        logger.error(f"프롬프트 업데이트 오류: {e}", exc_info=True)
        if storage and storage._connection:
            storage._connection.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/prompts/reload', methods=['POST'])
@jwt_required()
def reload_prompts():
    """DB에서 프롬프트를 다시 로드하여 시스템에 적용 (관리자만)"""
    try:
        # 사용자 권한 확인
        username = get_jwt_identity()
        user = auth_manager.get_user_info(username)

        if not user or user.get('role') != 'admin':
            return jsonify({"error": "관리자 권한이 필요합니다"}), 403

        if not storage:
            return jsonify({"error": "Storage가 초기화되지 않았습니다"}), 500

        # Config 모듈에서 프롬프트 재로드 함수 호출
        from config import reload_prompts_from_db
        success = reload_prompts_from_db(storage)

        if success:
            logger.info(f"프롬프트 재로드 성공 by {username}")
            return jsonify({
                "success": True,
                "message": "시스템 프롬프트가 성공적으로 재로드되었습니다"
            })
        else:
            return jsonify({
                "success": False,
                "message": "프롬프트 재로드 실패"
            }), 500

    except Exception as e:
        logger.error(f"프롬프트 재로드 오류: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================
# WebSocket 이벤트
# ============================================

@socketio.on('connect')
def handle_connect():
    """WebSocket 연결"""
    logger.info(f"클라이언트 연결됨: {request.sid}")
    emit('connected', {'message': 'WebSocket 연결 성공'})


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 연결 해제"""
    logger.info(f"클라이언트 연결 해제됨: {request.sid}")


@socketio.on('chat_message')
def handle_chat_message(data):
    """실시간 채팅 메시지 처리 (스트리밍)"""
    if not system_initialized or not orchestrator:
        emit('error', {'message': '시스템이 초기화되지 않았습니다'})
        return

    user_message = data.get('message', '')

    if not user_message:
        emit('error', {'message': '메시지가 비어있습니다'})
        return

    try:
        # 스트리밍 응답 생성
        emit('chat_start', {'message': '응답 생성 중...'})

        # 오케스트레이터를 통해 스트리밍 응답 생성
        stream_generator = orchestrator.process_query_sync(user_message, stream=True)

        for chunk_data in stream_generator:
            if chunk_data.get('type') == 'chunk':
                emit('chat_chunk', {'chunk': chunk_data.get('content', '')})
            elif chunk_data.get('type') == 'done':
                emit('chat_done', {
                    'tool_calls': chunk_data.get('tool_calls', []),
                    'tool_results': chunk_data.get('tool_results', {})
                })

        emit('chat_end', {'message': '응답 생성 완료'})

    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}", exc_info=True)
        emit('error', {'message': str(e)})


@socketio.on('water_subscribe')
def handle_water_subscribe():
    """수위 데이터 실시간 구독"""
    logger.info(f"수위 데이터 구독 시작: {request.sid}")

    def send_water_updates():
        """수위 데이터 주기적 전송"""
        while True:
            try:
                if storage:
                    conn = storage._connection
                    cur = conn.cursor()

                    query = """
                    SELECT measured_at, gagok_water_level, gagok_pump_a, gagok_pump_b,
                           haeryong_water_level, haeryong_pump_a, haeryong_pump_b
                    FROM water
                    ORDER BY measured_at DESC
                    LIMIT 1
                    """
                    cur.execute(query)
                    row = cur.fetchone()

                    data = []
                    if row:
                        # 가곡 배수지 데이터
                        data.append({
                            "location": "gagok",
                            "water_level": float(row[1]) if row[1] is not None else 0.0,
                            "pump_status": float(row[2] or 0) + float(row[3] or 0),
                            "timestamp": row[0].isoformat()
                        })
                        # 해룡 배수지 데이터
                        data.append({
                            "location": "haeryong",
                            "water_level": float(row[4]) if row[4] is not None else 0.0,
                            "pump_status": float(row[5] or 0) + float(row[6] or 0),
                            "timestamp": row[0].isoformat()
                        })

                    cur.close()
                    conn.commit()
                    socketio.emit('water_update', {'data': data}, room=request.sid)

                time.sleep(5)  # 5초마다 업데이트

            except Exception as e:
                logger.error(f"수위 업데이트 오류: {e}")
                if storage and storage._connection:
                    storage._connection.rollback()
                time.sleep(5)

    # 백그라운드 스레드에서 실행
    thread = threading.Thread(target=send_water_updates, daemon=True)
    thread.start()


# ============================================
# API Blueprint 등록
# ============================================

# 이상 탐지 API 등록
try:
    from api.anomaly_routes import anomaly_bp
    app.register_blueprint(anomaly_bp)
    logger.info("✅ 이상 탐지 API 라우트 등록 완료")
except Exception as e:
    logger.error(f"이상 탐지 API 등록 실패: {e}")


# ============================================
# 실시간 이상 탐지 모니터링
# ============================================

def on_anomaly_detected(anomaly_data: Dict[str, Any]):
    """이상 탐지 시 웹소켓으로 알림 전송"""
    try:
        logger.info(f"이상 탐지 알림: {anomaly_data.get('reservoir')} - {anomaly_data.get('status')}")

        # 웹소켓으로 브로드캐스트
        socketio.emit('anomaly_alert', anomaly_data, broadcast=True)

    except Exception as e:
        logger.error(f"이상 탐지 알림 전송 오류: {e}", exc_info=True)


def start_anomaly_monitoring():
    """이상 탐지 모니터링 시작"""
    global anomaly_monitor

    try:
        from services.realtime_anomaly_monitor import RealtimeAnomalyMonitor

        # 모니터 초기화 (60초마다 체크)
        anomaly_monitor = RealtimeAnomalyMonitor(
            check_interval=60,
            on_anomaly_detected=on_anomaly_detected
        )

        # 모니터링 시작
        anomaly_monitor.start()

        logger.info("✅ 실시간 이상 탐지 모니터링 시작됨")

    except Exception as e:
        logger.error(f"이상 탐지 모니터링 시작 실패: {e}", exc_info=True)


# 웹소켓 이벤트: 이상 탐지 상태 조회
@socketio.on('get_anomaly_status')
def handle_get_anomaly_status():
    """현재 이상 탐지 상태 조회"""
    try:
        if anomaly_monitor:
            status = anomaly_monitor.get_current_status()
            emit('anomaly_status', status)
        else:
            emit('anomaly_status', {"error": "모니터링이 실행되지 않았습니다"})
    except Exception as e:
        logger.error(f"상태 조회 오류: {e}")
        emit('anomaly_status', {"error": str(e)})


# ============================================
# 앱 시작
# ============================================

if __name__ == '__main__':
    # 시스템 초기화
    initialize_system()

    # 실시간 이상 탐지 모니터링 시작
    start_anomaly_monitoring()

    # Flask-SocketIO 서버 실행
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
