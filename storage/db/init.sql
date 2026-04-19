-- Initialize AI Agent Database

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Memory vectors table (for semantic search)
CREATE TABLE IF NOT EXISTS memory_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    type VARCHAR(20) DEFAULT 'medium_term'
);

-- Create vector index for faster search
CREATE INDEX IF NOT EXISTS memory_vectors_embedding_idx
ON memory_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Session history table
CREATE TABLE IF NOT EXISTS session_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    tokens_used INT DEFAULT 0,
    model_used VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for session queries
CREATE INDEX IF NOT EXISTS session_history_session_idx
ON session_history (session_id, created_at DESC);

-- Task records table
CREATE TABLE IF NOT EXISTS task_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result JSONB DEFAULT '{}',
    skills_used JSONB DEFAULT '[]',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create index for task status queries
CREATE INDEX IF NOT EXISTS task_records_status_idx
ON task_records (user_id, status, created_at DESC);

-- Skill usage statistics table
CREATE TABLE IF NOT EXISTS skill_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    success BOOLEAN DEFAULT true,
    execution_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model call statistics table
CREATE TABLE IF NOT EXISTS model_call_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    success BOOLEAN DEFAULT true,
    latency_ms INT NOT NULL,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Evolution events table (for tracking autonomous evolution)
CREATE TABLE IF NOT EXISTS evolution_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    level INT DEFAULT 1,
    details JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (for enterprise multi-user support)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default user if not exists
INSERT INTO users (id, email, name, role)
VALUES ('00000000-0000-0000-0000-000000000001', 'default@ai-agent.local', 'Default User', 'admin')
ON CONFLICT (email) DO NOTHING;