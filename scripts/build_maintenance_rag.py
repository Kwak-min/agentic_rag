# scripts/build_maintenance_rag.py - 유지보수 이력 RAG 구축 스크립트

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader.water_data_loader import MaintenanceDataLoader
from storage.postgresql_storage import PostgreSQLStorage
from config import PG_DB_HOST, PG_DB_PORT, PG_DB_NAME, PG_DB_USER, PG_DB_PASSWORD
from utils.logger import setup_logger
import json

logger = setup_logger(__name__)


def main():
    """유지보수 이력 RAG 구축"""

    logger.info("=" * 80)
    logger.info("유지보수 이력 RAG 구축 시작")
    logger.info("=" * 80)

    # ========== 1. 유지보수 데이터 로드 ==========
    logger.info("\n1단계: 유지보수 데이터 로드")

    maintenance_path = project_root / "RNN-LSTM_model 분석" / "1.2023년 부터_유지보수 관리이력.xlsx"

    loader = MaintenanceDataLoader(str(maintenance_path))
    df = loader.load()
    df = loader.preprocess()

    logger.info(f"유지보수 데이터 로드 완료: {len(df)}행")

    # ========== 2. 지식 베이스 생성 ==========
    logger.info("\n2단계: 지식 베이스 생성")

    documents = loader.create_knowledge_base()
    logger.info(f"문서 생성 완료: {len(documents)}개")

    # 샘플 출력
    if documents:
        logger.info(f"\n샘플 문서 1:")
        logger.info(f"  텍스트: {documents[0]['text'][:200]}...")
        logger.info(f"  메타데이터: {documents[0]['metadata']}")

    # ========== 3. PostgreSQL 벡터 DB에 저장 ==========
    logger.info("\n3단계: 벡터 DB 저장")

    try:
        # PostgreSQL 스토리지 초기화
        storage = PostgreSQLStorage(
            host=PG_DB_HOST,
            port=PG_DB_PORT,
            database=PG_DB_NAME,
            user=PG_DB_USER,
            password=PG_DB_PASSWORD
        )

        # 테이블 생성 (이미 있으면 스킵)
        storage.initialize()

        # 기존 유지보수 데이터 삭제 (재구축)
        logger.info("기존 유지보수 데이터 삭제...")
        # storage.clear_collection('maintenance')  # 필요시 구현

        # 문서 저장
        logger.info("문서 임베딩 및 저장 중...")
        stored_count = 0

        for doc in documents:
            try:
                # 문서 저장 (임베딩 자동 생성)
                storage.store_document(
                    content=doc['text'],
                    metadata={
                        **doc['metadata'],
                        'collection': 'maintenance',
                        'source': 'maintenance_history'
                    }
                )
                stored_count += 1

                if stored_count % 50 == 0:
                    logger.info(f"  진행: {stored_count}/{len(documents)}")

            except Exception as e:
                logger.error(f"문서 저장 실패 (ID: {doc['metadata'].get('id')}): {e}")
                continue

        logger.info(f"문서 저장 완료: {stored_count}/{len(documents)}")

        # ========== 4. 검색 테스트 ==========
        logger.info("\n4단계: 검색 테스트")

        test_queries = [
            "수위가 급격히 낮아지는 문제",
            "펌프 고장",
            "가곡 배수지 문제",
            "수위 센서 이상"
        ]

        for query in test_queries:
            logger.info(f"\n검색 쿼리: '{query}'")

            results = storage.search_similar_documents(
                query=query,
                top_k=3,
                metadata_filter={'collection': 'maintenance'}
            )

            for i, result in enumerate(results):
                logger.info(f"  결과 {i+1} (유사도: {result.get('similarity', 0):.4f}):")
                logger.info(f"    {result['content'][:150]}...")

        # ========== 완료 ==========
        logger.info("\n" + "=" * 80)
        logger.info("✅ RAG 구축 완료!")
        logger.info("=" * 80)
        logger.info(f"저장된 문서: {stored_count}개")
        logger.info(f"데이터베이스: {PG_DB_HOST}:{PG_DB_PORT}/{PG_DB_NAME}")

    except Exception as e:
        logger.error(f"RAG 구축 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
