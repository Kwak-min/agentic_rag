# auth/auth_manager.py - 인증 관리 시스템

import bcrypt
from datetime import timedelta
from typing import Optional, Dict, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthManager:
    """사용자 인증 관리 클래스"""

    def __init__(self):
        # 임시 사용자 데이터베이스 (실제로는 PostgreSQL 사용 권장)
        self.users = {
            "admin": {
                "password_hash": bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "role": "admin",
                "name": "관리자"
            }
        }
        logger.info("인증 관리자 초기화 완료")

    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """사용자 인증 확인

        Args:
            username: 사용자 이름
            password: 비밀번호

        Returns:
            Optional[Dict]: 인증 성공 시 사용자 정보, 실패 시 None
        """
        try:
            user = self.users.get(username)
            if not user:
                logger.warning(f"존재하지 않는 사용자: {username}")
                return None

            # 비밀번호 검증
            password_hash = user['password_hash'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), password_hash):
                logger.info(f"사용자 인증 성공: {username}")
                return {
                    "username": username,
                    "role": user["role"],
                    "name": user["name"]
                }
            else:
                logger.warning(f"비밀번호 불일치: {username}")
                return None

        except Exception as e:
            logger.error(f"인증 오류: {e}")
            return None

    def add_user(self, username: str, password: str, role: str = "user", name: str = "사용자"):
        """새 사용자 추가

        Args:
            username: 사용자 이름
            password: 비밀번호
            role: 역할 (admin, user 등)
            name: 표시 이름
        """
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.users[username] = {
                "password_hash": password_hash,
                "role": role,
                "name": name
            }
            logger.info(f"새 사용자 추가: {username} (역할: {role})")
        except Exception as e:
            logger.error(f"사용자 추가 오류: {e}")

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
            # 기존 비밀번호 확인
            if not self.verify_user(username, old_password):
                logger.warning(f"비밀번호 변경 실패 - 기존 비밀번호 불일치: {username}")
                return False

            # 새 비밀번호 설정
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.users[username]["password_hash"] = password_hash
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
        user = self.users.get(username)
        if user:
            return {
                "username": username,
                "role": user["role"],
                "name": user["name"]
            }
        return None


# 전역 인증 관리자 인스턴스
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """전역 인증 관리자 인스턴스 반환"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
