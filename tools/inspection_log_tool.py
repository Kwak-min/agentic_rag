# tools/inspection_log_tool.py - 점검 로그 검색 도구

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)


class InspectionLogTool:
    """점검 로그를 검색하는 도구

    AI가 과거 점검 이력을 참조하여 답변할 수 있도록 합니다.
    """

    def __init__(self, storage):
        """
        Args:
            storage: PostgreSQLStorage 인스턴스
        """
        self.storage = storage
        logger.info("점검 로그 도구 초기화 완료")

    def get_tool_definition(self) -> Dict[str, Any]:
        """도구 정의 반환 (LLM function calling용)"""
        return {
            "name": "search_inspection_logs",
            "description": """점검 로그를 검색합니다. 과거의 점검 이력, 문제 발생 내역, 조치 사항을 확인할 수 있습니다.
            사용자가 "저번에", "이전에", "예전에" 같은 과거 이력을 물어보거나,
            특정 장소나 문제에 대한 이력을 물어볼 때 사용하세요.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "검색할 장소 (예: 가곡 배수지, 해룡 배수지). 없으면 전체 검색"
                    },
                    "issue_location": {
                        "type": "string",
                        "description": "검색할 문제 부위 (예: 펌프, 센서, 배관). 없으면 전체 검색"
                    },
                    "days": {
                        "type": "integer",
                        "description": "최근 며칠 이내의 로그를 검색할지 (기본값: 30일)",
                        "default": 30
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 검색 결과 수 (기본값: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        }

    def execute(
        self,
        location: Optional[str] = None,
        issue_location: Optional[str] = None,
        days: int = 30,
        limit: int = 10,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """점검 로그 검색 실행

        Args:
            location: 장소 필터
            issue_location: 문제 부위 필터
            days: 최근 며칠 이내
            limit: 최대 결과 수
            execution_context: 실행 컨텍스트

        Returns:
            List[Dict]: 검색된 점검 로그 목록
        """
        try:
            logger.info(f"점검 로그 검색: location={location}, issue_location={issue_location}, days={days}")

            conn = self.storage._connection
            cur = conn.cursor()

            # 기본 쿼리
            query = """
                SELECT id, location, datetime, issue_location, issue_description, inspection_action, handler, created_at
                FROM inspection_logs
                WHERE datetime >= NOW() - INTERVAL '%s days'
            """
            params = [days]

            # 장소 필터
            if location:
                query += " AND location ILIKE %s"
                params.append(f"%{location}%")

            # 문제 부위 필터
            if issue_location:
                query += " AND issue_location ILIKE %s"
                params.append(f"%{issue_location}%")

            query += " ORDER BY datetime DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()

            results = []
            for row in rows:
                results.append({
                    "id": row[0],
                    "location": row[1],
                    "datetime": row[2].strftime("%Y-%m-%d %H:%M:%S"),
                    "issue_location": row[3],
                    "issue_description": row[4],
                    "inspection_action": row[5],
                    "handler": row[6],
                    "created_at": row[7].strftime("%Y-%m-%d %H:%M:%S")
                })

            cur.close()
            conn.commit()

            logger.info(f"점검 로그 {len(results)}개 검색됨")
            return results

        except Exception as e:
            logger.error(f"점검 로그 검색 오류: {e}", exc_info=True)
            if self.storage and self.storage._connection:
                self.storage._connection.rollback()
            return []

    def __call__(self, **kwargs) -> List[Dict[str, Any]]:
        """도구 호출"""
        return self.execute(**kwargs)


def get_inspection_log_tool(storage):
    """점검 로그 도구 인스턴스 생성"""
    return InspectionLogTool(storage)
