# auth/auth_manager.py - 인증 관리 시스템

import bcrypt
from datetime import timedelta
from typing import Optional, Dict, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthManager:
    """사용자 인증 관리 클래스 (PostgreSQL 기반)"""

    def __init__(self, storage=None):
        """
        Args:
            storage: PostgreSQL 스토리지 인스턴스
        """
        self.storage = storage
        logger.info("인증 관리자 초기화 완료 (PostgreSQL 기반)")

    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """사용자 인증 확인

        Args:
            username: 사용자 이름
            password: 비밀번호

        Returns:
            Optional[Dict]: 인증 성공 시 사용자 정보, 실패 시 None
        """
        try:
            if not self.storage:
                logger.error("Storage가 초기화되지 않았습니다")
                return None

            # DB에서 사용자 조회
            query = "SELECT id, username, password_hash, role, name FROM users WHERE username = %s"
            results = self.storage.execute_query(query, (username,))

            if not results or len(results) == 0:
                logger.warning(f"존재하지 않는 사용자: {username}")
                return None

            user = results[0]
            user_id, username_db, password_hash, role, name = user

            # 비밀번호 검증
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                logger.info(f"사용자 인증 성공: {username}")
                return {
                    "id": user_id,
                    "username": username_db,
                    "role": role,
                    "name": name
                }
            else:
                logger.warning(f"비밀번호 불일치: {username}")
                return None

        except Exception as e:
            logger.error(f"인증 오류: {e}")
            return None

    def add_user(self, username: str, password: str, role: str = "user", name: str = "사용자") -> bool:
        """새 사용자 추가

        Args:
            username: 사용자 이름
            password: 비밀번호
            role: 역할 (admin, user 등)
            name: 표시 이름

        Returns:
            bool: 성공 여부
        """
        try:
            if not self.storage:
                logger.error("Storage가 초기화되지 않았습니다")
                return False

            # 비밀번호 해시 생성
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # DB에 사용자 삽입
            query = """
                INSERT INTO users (username, password_hash, role, name)
                VALUES (%s, %s, %s, %s)
            """
            self.storage.execute_query(query, (username, password_hash, role, name), commit=True)
            logger.info(f"새 사용자 추가: {username} (역할: {role})")
            return True

        except Exception as e:
            logger.error(f"사용자 추가 오류: {e}")
            return False

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """비밀번호 변경

        Args:
            username: 사용자 이름
            old_password: 기존 비밀번호
            new_password: 새 비밀번호

        Returns:
            bool: 성공 여부
        """
        try:
            if not self.storage:
                logger.error("Storage가 초기화되지 않았습니다")
                return False

            # 기존 비밀번호 확인
            if not self.verify_user(username, old_password):
                logger.warning(f"비밀번호 변경 실패 - 기존 비밀번호 불일치: {username}")
                return False

            # 새 비밀번호 해시 생성
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # DB 업데이트
            query = "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE username = %s"
            self.storage.execute_query(query, (password_hash, username), commit=True)
            logger.info(f"비밀번호 변경 성공: {username}")
            return True

        except Exception as e:
            logger.error(f"비밀번호 변경 오류: {e}")
            return False

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """사용자 정보 조회

        Args:
            username: 사용자 이름

        Returns:
            Optional[Dict]: 사용자 정보 (비밀번호 해시 제외)
        """
        try:
            if not self.storage:
                logger.error("Storage가 초기화되지 않았습니다")
                return None

            # DB에서 사용자 조회
            query = "SELECT id, username, role, name FROM users WHERE username = %s"
            results = self.storage.execute_query(query, (username,))

            if results and len(results) > 0:
                user = results[0]
                return {
                    "id": user[0],
                    "username": user[1],
                    "role": user[2],
                    "name": user[3]
                }
            return None

        except Exception as e:
            logger.error(f"사용자 정보 조회 오류: {e}")
            return None


# 전역 인증 관리자 인스턴스
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """전역 인증 관리자 인스턴스 반환"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
