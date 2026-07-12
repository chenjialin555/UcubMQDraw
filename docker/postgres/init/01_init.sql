-- UcubMQDraw PostgreSQL 初始化（Phase 1）
-- Docker 首次启动 postgres 容器时自动执行

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,

    user_id VARCHAR(64) NOT NULL,
    user_type VARCHAR(20) NOT NULL,

    phone VARCHAR(32),
    email VARCHAR(128),

    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,

    password_hash VARCHAR(255),

    nickname VARCHAR(64) NOT NULL,
    avatar_url VARCHAR(512),

    status VARCHAR(20) NOT NULL DEFAULT 'active',

    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_users_user_id
ON users(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_users_phone
ON users(phone)
WHERE phone IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uniq_users_email
ON users(email)
WHERE email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_user_type
ON users(user_type);

CREATE INDEX IF NOT EXISTS idx_users_created_at
ON users(created_at);


CREATE TABLE IF NOT EXISTS generation_tasks (
    id BIGSERIAL PRIMARY KEY,

    task_id VARCHAR(64) NOT NULL,
    inner_task_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,

    tool_key VARCHAR(64) NOT NULL,
    tool_name VARCHAR(128) NOT NULL,

    status VARCHAR(32) NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,

    task_submit_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    task_dispatch_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    task_callback_params JSONB,

    error_message TEXT,
    cost_time DOUBLE PRECISION,
    favorite BOOLEAN NOT NULL DEFAULT FALSE,

    deleted_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_generation_tasks_task_id
ON generation_tasks(task_id);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_generation_tasks_inner_task_id
ON generation_tasks(inner_task_id);

CREATE INDEX IF NOT EXISTS idx_generation_tasks_user_created
ON generation_tasks(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_generation_tasks_user_status
ON generation_tasks(user_id, status);

CREATE INDEX IF NOT EXISTS idx_generation_tasks_status_updated
ON generation_tasks(status, updated_at);

CREATE INDEX IF NOT EXISTS idx_generation_tasks_deleted_at
ON generation_tasks(deleted_at);


INSERT INTO users (
    user_id,
    user_type,
    nickname,
    status,
    phone_verified,
    email_verified,
    created_at,
    updated_at
)
VALUES (
    'user_guest_public',
    'guest',
    '游客',
    'active',
    FALSE,
    FALSE,
    NOW(),
    NOW()
)
ON CONFLICT (user_id) DO NOTHING;
