\set ON_ERROR_STOP on
-- ================================
-- Synergy Project: Schema & Seed
-- ================================
SET client_encoding TO 'UTF8';
SET datestyle TO 'ISO, YMD';
SET timezone TO 'UTC';

CREATE EXTENSION IF NOT EXISTS vector;

-- ---- schema ----
CREATE TABLE IF NOT EXISTS files (
  id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL UNIQUE,
  upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  length BIGINT NOT NULL,
  metadata JSONB,
  content BYTEA
);

CREATE TABLE IF NOT EXISTS chunks (
  id SERIAL PRIMARY KEY,
  file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  content TEXT,
  embedding vector(1024),
  metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
  ON chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS water (
  measured_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  gagok_water_level DOUBLE PRECISION,
  gagok_pump_a DOUBLE PRECISION,
  gagok_pump_b DOUBLE PRECISION,
  haeryong_water_level DOUBLE PRECISION,
  haeryong_pump_a DOUBLE PRECISION,
  haeryong_pump_b DOUBLE PRECISION,
  sangsa_water_level DOUBLE PRECISION,
  sangsa_pump_a DOUBLE PRECISION,
  sangsa_pump_b DOUBLE PRECISION,
  sangsa_pump_c DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_water_measured_at ON water(measured_at);
CREATE UNIQUE INDEX IF NOT EXISTS ux_water_measured_at ON water(measured_at);

-- ---- stable staging (영구 스테이징; 끝에 DROP) ----
DROP TABLE IF EXISTS water_stage;
CREATE TABLE water_stage (
  measured_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  gagok_water_level DOUBLE PRECISION,
  gagok_pump_a DOUBLE PRECISION,
  gagok_pump_b DOUBLE PRECISION,
  haeryong_water_level DOUBLE PRECISION,
  haeryong_pump_a DOUBLE PRECISION,
  haeryong_pump_b DOUBLE PRECISION,
  sangsa_water_level DOUBLE PRECISION,
  sangsa_pump_a DOUBLE PRECISION,
  sangsa_pump_b DOUBLE PRECISION,
  sangsa_pump_c DOUBLE PRECISION
);

-- CSV -> staging (파일은 같은 폴더가 /docker-entrypoint-initdb.d 로 마운트됨)
COPY water_stage (
  measured_at,
  gagok_water_level,
  gagok_pump_a,
  gagok_pump_b,
  haeryong_water_level,
  haeryong_pump_a,
  haeryong_pump_b,
  sangsa_water_level,
  sangsa_pump_a,
  sangsa_pump_b,
  sangsa_pump_c
) FROM '/docker-entrypoint-initdb.d/water.csv'
  WITH (
    FORMAT csv,
    HEADER true,
    NULL 'NULL',                                -- "NULL" 문자열을 실제 NULL로 처리
    FORCE_NULL (
      gagok_water_level,
      gagok_pump_a,
      gagok_pump_b,
      haeryong_water_level,
      haeryong_pump_a,
      haeryong_pump_b,
      sangsa_water_level,
      sangsa_pump_a,
      sangsa_pump_b,
      sangsa_pump_c
    )                                            -- 빈 칸(,)도 NULL로 강제
  );

-- staging -> 본 테이블 (중복 무시)
INSERT INTO water AS w (
  measured_at,
  gagok_water_level,
  gagok_pump_a,
  gagok_pump_b,
  haeryong_water_level,
  haeryong_pump_a,
  haeryong_pump_b,
  sangsa_water_level,
  sangsa_pump_a,
  sangsa_pump_b,
  sangsa_pump_c
)
SELECT
  s.measured_at,
  s.gagok_water_level,
  s.gagok_pump_a,
  s.gagok_pump_b,
  s.haeryong_water_level,
  s.haeryong_pump_a,
  s.haeryong_pump_b,
  s.sangsa_water_level,
  s.sangsa_pump_a,
  s.sangsa_pump_b,
  s.sangsa_pump_c
FROM water_stage s
ON CONFLICT (measured_at) DO NOTHING;

-- 정리
DROP TABLE water_stage;

-- 간단 검증 로그
DO $$
DECLARE c bigint; e timestamp; l timestamp;
BEGIN
  SELECT COUNT(*), MIN(measured_at), MAX(measured_at)
  INTO c, e, l FROM water;
  RAISE LOG 'water rows=% count, range=[% .. %]', c, e, l;
END$$;

-- ================================
-- 새로운 테이블 추가 (Phase 1)
-- ================================

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  name VARCHAR(100),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 점검 로그 테이블
CREATE TABLE IF NOT EXISTS inspection_logs (
  id SERIAL PRIMARY KEY,
  location VARCHAR(100) NOT NULL,
  datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  issue_location VARCHAR(100),
  issue_description TEXT,
  inspection_action TEXT,
  handler VARCHAR(100),
  work_type VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inspection_logs_location ON inspection_logs(location);
CREATE INDEX IF NOT EXISTS idx_inspection_logs_datetime ON inspection_logs(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_inspection_logs_work_type ON inspection_logs(work_type);

-- 시스템 프롬프트 설정 테이블
CREATE TABLE IF NOT EXISTS system_prompts (
  id SERIAL PRIMARY KEY,
  prompt_type VARCHAR(50) UNIQUE NOT NULL,
  prompt_content TEXT NOT NULL,
  description TEXT,
  updated_by VARCHAR(50),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 기본 사용자 데이터 삽입 (bcrypt 해시는 초기화 스크립트에서 업데이트)
INSERT INTO users (username, password_hash, role, name) VALUES
  ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxIZOHGOm', 'admin', '관리자'),
  ('user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxIZOHGOm', 'user', '사용자')
ON CONFLICT (username) DO NOTHING;

-- 시스템 프롬프트 기본값 삽입
INSERT INTO system_prompts (prompt_type, prompt_content, description) VALUES
('function_selection',
'너는 사용자의 요청에 맞춰 적절한 도구를 호출하는 에이전트다.

원칙:
- 의도 우선: 키워드가 아니라 의미를 보고 도구를 고른다.
- 검색/정보/자료/내용/방법/사용법을 묻거나 찾아줘/알려줘가 포함되면 기본적으로 vector_search_tool을 선택한다.
- 현재/과거 상태 조회는 DB/센서 기반 도구를 쓴다.
- 스몰톡/인사/잡담/농담/감사일 때만 []를 반환한다.

도구 선택 예시:
- "저번에 가곡 배수지에서 무슨 문제 있었어?" -> search_inspection_logs(location="가곡")
- "이전에 펌프 문제 있었나?" -> search_inspection_logs(issue_location="펌프")
- "파일 목록 보여줘" -> list_files_tool()',
'도구 선택용 시스템 프롬프트'
),
('response_generation',
'당신은 전문적인 AI 어시스턴트입니다. 도구 실행 결과를 바탕으로 구조화되고 명확한 한국어 답변을 제공하세요.

핵심 원칙:
1. 정확성: 도구 결과에 있는 정보만 사용
2. 구조화: 명확한 구조로 답변
3. 가독성: 이해하기 쉬운 형태로 제시',
'응답 생성용 시스템 프롬프트'
)
ON CONFLICT (prompt_type) DO NOTHING;
