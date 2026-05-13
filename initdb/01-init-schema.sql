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