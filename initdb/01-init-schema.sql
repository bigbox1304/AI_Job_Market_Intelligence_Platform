-- =========================================
-- EXTENSION cho search ILIKE và trigram
-- =========================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =========================================
-- TABLES
-- =========================================
CREATE TABLE IF NOT EXISTS companies (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id BIGINT PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(company_id),
    industry TEXT,
    job_function TEXT,
    job_group TEXT,
    job_level TEXT,
    city TEXT,
    job_description TEXT,
    job_requirement TEXT,
    years_of_experience INTEGER,
    salary_min NUMERIC,
    salary_max NUMERIC,
    source TEXT NOT NULL DEFAULT 'unknown',
    source_url TEXT,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_on TIMESTAMP WITH TIME ZONE,
    expired_on TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id SERIAL PRIMARY KEY,
    skill_name TEXT UNIQUE NOT NULL,
    skill_type TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id BIGINT REFERENCES jobs(job_id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(skill_id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_email TEXT,
    query TEXT NOT NULL,
    filters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- USER BEHAVIOR EVENTS
-- =========================================
-- Append-only events make recommendation signals auditable and allow the
-- ranking layer to distinguish a view from a save, apply, or dismissal.
CREATE TABLE IF NOT EXISTS user_job_events (
    event_id BIGSERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('view', 'save', 'apply', 'dismiss')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendation_impressions (
    impression_id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    user_email TEXT,
    query_text TEXT NOT NULL DEFAULT '',
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    rank_position INTEGER NOT NULL,
    recommendation_score NUMERIC,
    features JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version TEXT NOT NULL DEFAULT 'hybrid-v1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    dag_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    status TEXT NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE
);

-- =========================================
-- INDEXES (tối ưu như bạn đã có)
-- =========================================
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_job ON job_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(skill_name);

-- Filter indexes
CREATE INDEX IF NOT EXISTS idx_jobs_level ON jobs(job_level);
CREATE INDEX IF NOT EXISTS idx_jobs_industry ON jobs(industry);
CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city);
CREATE INDEX IF NOT EXISTS idx_jobs_function ON jobs(job_function);
CREATE INDEX IF NOT EXISTS idx_jobs_experience ON jobs(years_of_experience);

-- Trigram search (rất quan trọng cho full-text)
CREATE INDEX IF NOT EXISTS idx_jobs_title_trgm ON jobs USING gin (job_title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_jobs_requirement_trgm ON jobs USING gin (job_requirement gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_jobs_description_trgm ON jobs USING gin (job_description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_skills_name_trgm ON skills USING gin (skill_name gin_trgm_ops);

-- Composite indexes (filter nhiều trường cùng lúc)
CREATE INDEX IF NOT EXISTS idx_jobs_level_industry ON jobs(job_level, industry);
CREATE INDEX IF NOT EXISTS idx_jobs_city_level ON jobs(city, job_level);
CREATE INDEX IF NOT EXISTS idx_jobs_industry_function ON jobs(industry, job_function);

-- Sort & expired
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_on DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_expired ON jobs(expired_on);

-- Additional useful
CREATE INDEX IF NOT EXISTS idx_job_skills_composite ON job_skills(skill_id, job_id);
CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_email);
CREATE INDEX IF NOT EXISTS idx_search_history_created ON search_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_events_user ON user_job_events(user_email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_events_job ON user_job_events(job_id, event_type);
CREATE INDEX IF NOT EXISTS idx_impressions_user ON recommendation_impressions(user_email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_impressions_request ON recommendation_impressions(request_id, rank_position);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_dag ON pipeline_runs(dag_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active, expired_on);
