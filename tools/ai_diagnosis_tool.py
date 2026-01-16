# tools/ai_diagnosis_tool.py - AI 진단 도구 (이상 원인 분석)

from typing import Dict, Any, List, Optional
from storage.postgresql_storage import PostgreSQLStorage
from utils.logger import setup_logger
from models.ollama_client import OllamaClient

logger = setup_logger(__name__)


class AIDiagnosisTool:
    """AI 기반 수위 이상 진단 도구

    LSTM이 이상을 감지하면, 유지보수 이력을 검색하여
    어떤 문제가 발생했을 가능성이 높은지 AI가 분석합니다.
    """

    def __init__(self):
        self.name = "ai_diagnosis"
        self.description = "수위 이상 발생 시 과거 유지보수 이력을 바탕으로 원인을 분석하고 조치사항을 추천합니다."

        # PostgreSQL RAG 스토리지 (싱글톤)
        self.storage = PostgreSQLStorage.get_instance()

        # LLM 클라이언트
        self.llm = OllamaClient()

        logger.info("AI 진단 도구 초기화 완료")

    def execute(self,
                anomaly_type: str = None,
                reservoir: str = None,
                water_level_change: float = None,
                pump_status: Dict = None,
                error_magnitude: float = None,
                **kwargs) -> Dict[str, Any]:
        """AI 진단 실행

        Args:
            anomaly_type: 이상 유형 ("급감", "급증", "불안정" 등)
            reservoir: 배수지 이름 (가곡, 해룡, 상사)
            water_level_change: 수위 변화량 (cm)
            pump_status: 펌프 상태 {"pump_a": 0/1, "pump_b": 0/1}
            error_magnitude: 오차 크기

        Returns:
            진단 결과 딕셔너리
        """
        try:
            # 1. 이상 패턴 분석
            pattern_description = self._analyze_pattern(
                anomaly_type=anomaly_type,
                water_level_change=water_level_change,
                pump_status=pump_status,
                error_magnitude=error_magnitude
            )

            logger.info(f"이상 패턴: {pattern_description}")

            # 2. 유사한 과거 사례 검색
            search_query = self._build_search_query(
                pattern_description=pattern_description,
                reservoir=reservoir
            )

            similar_cases = self.storage.search_similar_documents(
                query=search_query,
                top_k=5,
                metadata_filter={'collection': 'maintenance'}
            )

            logger.info(f"유사 사례 {len(similar_cases)}개 발견")

            # 3. AI가 원인 분석 및 조치사항 추천
            diagnosis = self._generate_diagnosis(
                pattern_description=pattern_description,
                reservoir=reservoir,
                similar_cases=similar_cases,
                pump_status=pump_status
            )

            # 4. 결과 반환
            result = {
                "success": True,
                "reservoir": reservoir,
                "anomaly_type": anomaly_type,
                "pattern_description": pattern_description,
                "diagnosis": diagnosis,
                "similar_cases_count": len(similar_cases),
                "similar_cases": [
                    {
                        "content": case['content'][:200] + "...",
                        "similarity": case.get('similarity', 0),
                        "metadata": case.get('metadata', {})
                    }
                    for case in similar_cases[:3]  # 상위 3개만
                ]
            }

            return result

        except Exception as e:
            logger.error(f"AI 진단 오류: {str(e)}", exc_info=True)
            return {"error": f"AI 진단 중 오류 발생: {str(e)}"}

    def _analyze_pattern(self,
                        anomaly_type: str = None,
                        water_level_change: float = None,
                        pump_status: Dict = None,
                        error_magnitude: float = None) -> str:
        """이상 패턴 분석"""

        patterns = []

        # 이상 유형
        if anomaly_type:
            patterns.append(f"이상 유형: {anomaly_type}")

        # 수위 변화
        if water_level_change is not None:
            if water_level_change > 10:
                patterns.append(f"수위 급증 ({water_level_change:.2f}cm)")
            elif water_level_change < -10:
                patterns.append(f"수위 급감 ({abs(water_level_change):.2f}cm)")
            elif abs(water_level_change) > 5:
                patterns.append(f"수위 불안정 ({water_level_change:.2f}cm)")
            else:
                patterns.append(f"수위 미세 변동 ({water_level_change:.2f}cm)")

        # 펌프 상태
        if pump_status:
            pump_a = pump_status.get('pump_a', 0)
            pump_b = pump_status.get('pump_b', 0)

            if pump_a == 1 and pump_b == 1:
                patterns.append("펌프 A, B 모두 작동 중")
            elif pump_a == 1:
                patterns.append("펌프 A만 작동 중")
            elif pump_b == 1:
                patterns.append("펌프 B만 작동 중")
            else:
                patterns.append("펌프 모두 정지")

        # 오차 크기
        if error_magnitude is not None:
            if error_magnitude > 20:
                patterns.append(f"매우 큰 예측 오차 ({error_magnitude:.2f})")
            elif error_magnitude > 10:
                patterns.append(f"큰 예측 오차 ({error_magnitude:.2f})")
            else:
                patterns.append(f"예측 오차 ({error_magnitude:.2f})")

        return " | ".join(patterns) if patterns else "이상 패턴 불명확"

    def _build_search_query(self, pattern_description: str, reservoir: str = None) -> str:
        """검색 쿼리 구성"""

        query_parts = []

        # 패턴 설명
        if "급감" in pattern_description or "급증" in pattern_description:
            query_parts.append("수위 변화 급격한 문제")

        if "펌프" in pattern_description:
            query_parts.append("펌프 관련 문제")

        if "정지" in pattern_description:
            query_parts.append("펌프 정지 펌프 고장")

        # 배수지
        if reservoir:
            query_parts.append(reservoir)

        # 기본 쿼리
        if not query_parts:
            query_parts.append("수위 이상 문제 원인")

        return " ".join(query_parts)

    def _generate_diagnosis(self,
                           pattern_description: str,
                           reservoir: str,
                           similar_cases: List[Dict],
                           pump_status: Dict = None) -> Dict[str, Any]:
        """AI가 진단 생성"""

        # 유사 사례 텍스트 추출
        case_texts = []
        for i, case in enumerate(similar_cases[:5]):
            case_texts.append(f"[사례 {i+1}]\n{case['content']}\n")

        cases_summary = "\n".join(case_texts) if case_texts else "관련 사례 없음"

        # LLM 프롬프트 구성
        prompt = f"""당신은 수처리 시설 전문가입니다. 다음 수위 이상 상황을 분석하고 원인과 조치사항을 추천해주세요.

## 현재 상황
- 배수지: {reservoir}
- 이상 패턴: {pattern_description}
- 펌프 상태: {pump_status if pump_status else '불명'}

## 과거 유사 사례
{cases_summary}

## 분석 요청사항
1. **가능한 원인**: 위 패턴과 과거 사례를 바탕으로 가장 가능성 높은 원인 3가지를 분석하세요.
2. **심각도**: 상황의 긴급도를 평가하세요 (낮음/중간/높음/긴급).
3. **즉시 조치사항**: 현장에서 바로 확인하거나 조치해야 할 사항을 구체적으로 제시하세요.
4. **장기 대책**: 재발 방지를 위한 장기적인 대책을 제안하세요.

간결하고 명확하게 답변해주세요."""

        # LLM 호출
        try:
            response = self.llm.chat(prompt)

            # 응답 파싱 (간단한 방법)
            diagnosis_result = {
                "raw_diagnosis": response,
                "possible_causes": self._extract_causes(response),
                "severity": self._extract_severity(response),
                "immediate_actions": self._extract_actions(response),
                "long_term_solutions": self._extract_solutions(response)
            }

            return diagnosis_result

        except Exception as e:
            logger.error(f"LLM 진단 생성 실패: {e}")
            return {
                "raw_diagnosis": f"LLM 진단 생성 실패: {str(e)}",
                "possible_causes": ["진단 생성 실패"],
                "severity": "알 수 없음",
                "immediate_actions": ["전문가 확인 필요"],
                "long_term_solutions": []
            }

    def _extract_causes(self, text: str) -> List[str]:
        """원인 추출"""
        causes = []

        # 간단한 패턴 매칭
        if "펌프" in text and "고장" in text:
            causes.append("펌프 고장 가능성")

        if "센서" in text and ("오류" in text or "이상" in text):
            causes.append("센서 오류 가능성")

        if "밸브" in text or "배관" in text:
            causes.append("밸브/배관 문제 가능성")

        # 기본값
        if not causes:
            causes.append("원인 분석 필요")

        return causes

    def _extract_severity(self, text: str) -> str:
        """심각도 추출"""
        text_lower = text.lower()

        if "긴급" in text_lower or "즉시" in text_lower:
            return "긴급"
        elif "높음" in text_lower or "심각" in text_lower:
            return "높음"
        elif "중간" in text_lower or "보통" in text_lower:
            return "중간"
        else:
            return "낮음"

    def _extract_actions(self, text: str) -> List[str]:
        """즉시 조치사항 추출"""
        actions = []

        # 키워드 기반 추출
        if "확인" in text:
            actions.append("현장 점검 및 확인")

        if "펌프" in text:
            actions.append("펌프 작동 상태 점검")

        if "센서" in text:
            actions.append("센서 정상 작동 여부 확인")

        # 기본값
        if not actions:
            actions.append("전문가 진단 필요")

        return actions

    def _extract_solutions(self, text: str) -> List[str]:
        """장기 대책 추출"""
        solutions = []

        if "정기" in text and "점검" in text:
            solutions.append("정기 점검 주기 강화")

        if "교체" in text:
            solutions.append("노후 장비 교체 검토")

        if "모니터링" in text:
            solutions.append("실시간 모니터링 시스템 강화")

        return solutions

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
                        "anomaly_type": {
                            "type": "string",
                            "description": "이상 유형 (예: '급감', '급증', '불안정')"
                        },
                        "reservoir": {
                            "type": "string",
                            "description": "배수지 이름 (가곡, 해룡, 상사)"
                        },
                        "water_level_change": {
                            "type": "number",
                            "description": "수위 변화량 (cm)"
                        },
                        "pump_status": {
                            "type": "object",
                            "description": "펌프 상태 {pump_a: 0/1, pump_b: 0/1}",
                            "properties": {
                                "pump_a": {"type": "number"},
                                "pump_b": {"type": "number"}
                            }
                        },
                        "error_magnitude": {
                            "type": "number",
                            "description": "예측 오차 크기"
                        }
                    }
                }
            }
        }

    def get_info(self) -> Dict[str, str]:
        """도구 정보 반환"""
        return {
            "name": self.name,
            "description": self.description
        }
