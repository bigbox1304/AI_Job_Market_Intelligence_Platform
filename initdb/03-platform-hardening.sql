-- Idempotent migration for databases initialized before platform hardening.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_min NUMERIC;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_max NUMERIC;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS recommendation_impressions (
    impression_id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    user_email TEXT,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    rank_position INTEGER NOT NULL,
    recommendation_score NUMERIC,
    model_version TEXT NOT NULL DEFAULT 'hybrid-v1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE recommendation_impressions ADD COLUMN IF NOT EXISTS query_text TEXT NOT NULL DEFAULT '';
ALTER TABLE recommendation_impressions ADD COLUMN IF NOT EXISTS features JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    dag_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    status TEXT NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_impressions_user ON recommendation_impressions(user_email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_impressions_request ON recommendation_impressions(request_id, rank_position);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_dag ON pipeline_runs(dag_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active, expired_on);
