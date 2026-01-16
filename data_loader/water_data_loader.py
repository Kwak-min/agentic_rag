# data_loader/water_data_loader.py - 배수지 수위 데이터 로더

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WaterDataLoader:
    """배수지 수위 데이터 로더 (엑셀 파일)"""

    def __init__(self, excel_path: str):
        """
        Args:
            excel_path: 엑셀 파일 경로 (3.배수지 수위 데이터_WATERDATA.xlsx)
        """
        self.excel_path = Path(excel_path)
        self.data = None
        self.sheets = None

        if not self.excel_path.exists():
            raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {excel_path}")

        logger.info(f"데이터 로더 초기화: {excel_path}")

    def load_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """모든 시트 로드"""
        try:
            # 모든 시트 읽기
            excel_file = pd.ExcelFile(self.excel_path)
            self.sheets = {}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                logger.info(f"시트 '{sheet_name}' 로드: {len(df)}행, {len(df.columns)}컬럼")
                self.sheets[sheet_name] = df

            logger.info(f"총 {len(self.sheets)}개 시트 로드 완료")
            return self.sheets

        except Exception as e:
            logger.error(f"엑셀 파일 로드 실패: {e}")
            raise

    def load_and_merge(self) -> pd.DataFrame:
        """모든 시트를 하나의 DataFrame으로 병합"""
        if self.sheets is None:
            self.load_all_sheets()

        # 모든 시트를 하나로 병합
        all_data = []
        for sheet_name, df in self.sheets.items():
            all_data.append(df)

        merged = pd.concat(all_data, ignore_index=True)
        logger.info(f"병합 완료: 총 {len(merged)}행")

        self.data = merged
        return merged

    def preprocess(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """데이터 전처리

        - 시간 컬럼 datetime 변환
        - 결측치 처리
        - 이상치 제거
        """
        if df is None:
            df = self.data

        if df is None:
            raise ValueError("데이터가 로드되지 않았습니다. load_and_merge()를 먼저 호출하세요.")

        df = df.copy()

        # 1. 시간 컬럼 변환
        if 'Time' in df.columns:
            # "2020 06 01 00:00" -> datetime
            df['Time'] = pd.to_datetime(df['Time'], format='%Y %m %d %H:%M', errors='coerce')
            df = df.sort_values('Time').reset_index(drop=True)
            logger.info("Time 컬럼을 datetime으로 변환 완료")

        # 2. 결측치 확인
        missing_counts = df.isnull().sum()
        if missing_counts.sum() > 0:
            logger.warning(f"결측치 발견:\n{missing_counts[missing_counts > 0]}")

            # 선형 보간법으로 결측치 채우기 (시계열 데이터에 적합)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].interpolate(method='linear', limit_direction='both')
            logger.info("결측치를 선형 보간법으로 처리 완료")

        # 3. 이상치 제거 (수위가 음수이거나 비정상적으로 큰 값)
        # 가곡 수위: 0~200cm 범위
        if 'Gagok_WaterLevel' in df.columns:
            before = len(df)
            df = df[(df['Gagok_WaterLevel'] >= 0) & (df['Gagok_WaterLevel'] <= 200)]
            after = len(df)
            if before != after:
                logger.info(f"가곡 수위 이상치 제거: {before - after}행")

        # 해룡 수위: 0~10m 범위
        if '해룡수위' in df.columns:
            before = len(df)
            df = df[(df['해룡수위'] >= 0) & (df['해룡수위'] <= 10)]
            after = len(df)
            if before != after:
                logger.info(f"해룡 수위 이상치 제거: {before - after}행")

        # 상사 수위: 0~200cm 범위
        if '상사수위' in df.columns:
            before = len(df)
            df = df[(df['상사수위'] >= 0) & (df['상사수위'] <= 200)]
            after = len(df)
            if before != after:
                logger.info(f"상사 수위 이상치 제거: {before - after}행")

        logger.info(f"전처리 완료: 최종 {len(df)}행")
        self.data = df
        return df

    def get_reservoir_data(self, reservoir: str = 'gagok') -> pd.DataFrame:
        """특정 배수지 데이터만 추출

        Args:
            reservoir: 'gagok', 'haeryong', 'sangsa' 중 하나

        Returns:
            해당 배수지의 수위 및 펌프 데이터
        """
        if self.data is None:
            raise ValueError("데이터가 로드되지 않았습니다.")

        df = self.data.copy()

        if reservoir.lower() == 'gagok':
            cols = ['Time', 'Gagok_WaterLevel', 'Gagok_PumpA', 'Gagok_PumpB']
            result = df[cols].copy()
            result.columns = ['Time', 'WaterLevel', 'PumpA', 'PumpB']

        elif reservoir.lower() == 'haeryong':
            cols = ['Time', '해룡수위', '해룡펌프A', '해룡펌프B']
            result = df[cols].copy()
            result.columns = ['Time', 'WaterLevel', 'PumpA', 'PumpB']

        elif reservoir.lower() == 'sangsa':
            cols = ['Time', '상사수위', '상사펌프A', '상사펌프B', '상사펌프C']
            result = df[cols].copy()
            result.columns = ['Time', 'WaterLevel', 'PumpA', 'PumpB', 'PumpC']

        else:
            raise ValueError(f"알 수 없는 배수지: {reservoir}. 'gagok', 'haeryong', 'sangsa' 중 하나를 선택하세요.")

        logger.info(f"{reservoir} 배수지 데이터 추출: {len(result)}행")
        return result

    def create_sequences(self,
                        data: np.ndarray,
                        seq_length: int = 60,
                        pred_length: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """시계열 시퀀스 생성 (LSTM 입력용)

        Args:
            data: 원본 데이터 (1D or 2D array)
            seq_length: 입력 시퀀스 길이 (과거 N개 데이터)
            pred_length: 예측 시퀀스 길이 (미래 M개 데이터)

        Returns:
            X: 입력 시퀀스 (samples, seq_length, features)
            y: 타겟 시퀀스 (samples, pred_length)
        """
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)

        X, y = [], []

        for i in range(len(data) - seq_length - pred_length + 1):
            X.append(data[i:i + seq_length])
            y.append(data[i + seq_length:i + seq_length + pred_length, 0])  # 첫 번째 feature만 예측

        X = np.array(X)
        y = np.array(y)

        logger.info(f"시퀀스 생성 완료: X={X.shape}, y={y.shape}")
        return X, y

    def prepare_lstm_data(self,
                          reservoir: str = 'gagok',
                          seq_length: int = 60,
                          pred_length: int = 1,
                          test_split: float = 0.2) -> Dict:
        """LSTM 학습용 데이터 준비

        Args:
            reservoir: 배수지 이름
            seq_length: 입력 시퀀스 길이
            pred_length: 예측 시퀀스 길이
            test_split: 테스트 데이터 비율

        Returns:
            데이터셋 딕셔너리 (X_train, X_test, y_train, y_test, scaler)
        """
        from sklearn.preprocessing import MinMaxScaler

        # 배수지 데이터 추출
        df = self.get_reservoir_data(reservoir)

        # 수위 데이터만 추출
        water_level = df['WaterLevel'].values

        # 정규화
        scaler = MinMaxScaler(feature_range=(0, 1))
        water_level_scaled = scaler.fit_transform(water_level.reshape(-1, 1))

        # 시퀀스 생성
        X, y = self.create_sequences(water_level_scaled, seq_length, pred_length)

        # Train/Test 분리
        split_idx = int(len(X) * (1 - test_split))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        logger.info(f"데이터 분리: Train={len(X_train)}, Test={len(X_test)}")

        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'scaler': scaler,
            'reservoir': reservoir,
            'seq_length': seq_length,
            'pred_length': pred_length,
            'original_data': df
        }


class MaintenanceDataLoader:
    """유지보수 관리 이력 로더"""

    def __init__(self, excel_path: str):
        """
        Args:
            excel_path: 엑셀 파일 경로 (1.2023년 부터_유지보수 관리이력.xlsx)
        """
        self.excel_path = Path(excel_path)
        self.data = None

        if not self.excel_path.exists():
            raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {excel_path}")

        logger.info(f"유지보수 데이터 로더 초기화: {excel_path}")

    def load(self) -> pd.DataFrame:
        """유지보수 이력 로드"""
        try:
            # 첫 번째 시트 읽기
            df = pd.read_excel(self.excel_path, sheet_name=0)
            logger.info(f"유지보수 이력 로드: {len(df)}행, {len(df.columns)}컬럼")

            self.data = df
            return df

        except Exception as e:
            logger.error(f"엑셀 파일 로드 실패: {e}")
            raise

    def preprocess(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """데이터 전처리"""
        if df is None:
            df = self.data

        if df is None:
            raise ValueError("데이터가 로드되지 않았습니다. load()를 먼저 호출하세요.")

        df = df.copy()

        # 1. 날짜 컬럼 변환
        date_cols = ['발생일자', 'A/S 조치일자']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # 2. 결측치가 적은 중요 컬럼만 선택
        important_cols = [
            '순번', '발생일자', '대상', '발생 개소', '발생 장비',
            '문제 및 요구사항', '진행상태', 'A/S 조치일자',
            'A/S 진행내용(원인 및 조치사항)'
        ]

        available_cols = [col for col in important_cols if col in df.columns]
        df = df[available_cols].copy()

        # 3. 텍스트 컬럼 전처리 (공백 제거)
        text_cols = ['문제 및 요구사항', 'A/S 진행내용(원인 및 조치사항)']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip()

        logger.info(f"전처리 완료: {len(df)}행")
        self.data = df
        return df

    def create_knowledge_base(self) -> List[Dict]:
        """RAG용 지식 베이스 생성

        Returns:
            문서 리스트 [{"text": "...", "metadata": {...}}, ...]
        """
        if self.data is None:
            raise ValueError("데이터가 로드되지 않았습니다.")

        df = self.data.copy()
        documents = []

        for idx, row in df.iterrows():
            # 텍스트 생성
            problem = row.get('문제 및 요구사항', '')
            solution = row.get('A/S 진행내용(원인 및 조치사항)', '')

            if not problem and not solution:
                continue

            # 문서 텍스트 구성
            text_parts = []

            # 발생 정보
            if pd.notna(row.get('발생일자')):
                text_parts.append(f"발생일자: {row['발생일자']}")

            if pd.notna(row.get('대상')):
                text_parts.append(f"대상: {row['대상']}")

            if pd.notna(row.get('발생 개소')):
                text_parts.append(f"발생 개소: {row['발생 개소']}")

            if pd.notna(row.get('발생 장비')):
                text_parts.append(f"발생 장비: {row['발생 장비']}")

            # 문제 설명
            if problem:
                text_parts.append(f"문제: {problem}")

            # 조치 내용
            if solution:
                text_parts.append(f"조치사항: {solution}")

            # 최종 텍스트
            text = "\n".join(text_parts)

            # 메타데이터
            metadata = {
                'id': idx,
                '순번': row.get('순번'),
                '발생일자': str(row.get('발생일자')) if pd.notna(row.get('발생일자')) else None,
                '대상': row.get('대상'),
                '발생 개소': row.get('발생 개소'),
                '발생 장비': row.get('발생 장비'),
                '진행상태': row.get('진행상태')
            }

            documents.append({
                'text': text,
                'metadata': metadata
            })

        logger.info(f"지식 베이스 생성 완료: {len(documents)}개 문서")
        return documents
