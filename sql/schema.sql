CREATE TABLE IF NOT EXISTS sessions (
 id UUID PRIMARY KEY, owner_key_hash VARCHAR(64) NOT NULL,
 title VARCHAR(200) NOT NULL DEFAULT 'New conversation',
 total_prompt_tokens INTEGER NOT NULL DEFAULT 0,
 total_completion_tokens INTEGER NOT NULL DEFAULT 0,
 total_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS messages (
 id UUID PRIMARY KEY, session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 role VARCHAR(20) NOT NULL, content TEXT NOT NULL, tokens INTEGER NOT NULL DEFAULT 0,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS rate_limit_events (
 id UUID PRIMARY KEY, api_key_hash VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS ix_rate_limit_key_created ON rate_limit_events(api_key_hash, created_at);
