-- Migration for databases that were initialized before behavioral events were added.
CREATE TABLE IF NOT EXISTS user_job_events (
    event_id BIGSERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('view', 'save', 'apply', 'dismiss')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_job_events_user ON user_job_events(user_email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_events_job ON user_job_events(job_id, event_type);
