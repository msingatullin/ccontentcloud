-- Migration: Create Scheduled Posts and Auto-Posting Rules tables
-- Date: 2025-11-14
-- Description: Tables for scheduled posting and auto-posting functionality

-- Таблица запланированных постов
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_id VARCHAR(36) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    account_id INTEGER,
    account_type VARCHAR(50),
    scheduled_time DATETIME NOT NULL,
    published_at DATETIME,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    platform_post_id VARCHAR(255),
    error_message TEXT,
    publish_options JSON DEFAULT '{}',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (content_id) REFERENCES content_pieces(id) ON DELETE CASCADE
);

-- Индексы для scheduled_posts
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_user_id ON scheduled_posts(user_id);
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_content_id ON scheduled_posts(content_id);
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_platform ON scheduled_posts(platform);
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_scheduled_time ON scheduled_posts(scheduled_time);
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_created_at ON scheduled_posts(created_at);
CREATE INDEX IF NOT EXISTS ix_scheduled_user_status ON scheduled_posts(user_id, status);
CREATE INDEX IF NOT EXISTS ix_scheduled_time_status ON scheduled_posts(scheduled_time, status);
CREATE INDEX IF NOT EXISTS ix_scheduled_platform ON scheduled_posts(platform, status);


-- Таблица правил автопостинга
CREATE TABLE IF NOT EXISTS auto_posting_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule_type VARCHAR(50) NOT NULL,
    schedule_config JSON NOT NULL,
    content_config JSON NOT NULL,
    platforms JSON NOT NULL,
    accounts JSON,
    content_types JSON,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_paused BOOLEAN NOT NULL DEFAULT 0,
    max_posts_per_day INTEGER,
    max_posts_per_week INTEGER,
    total_executions INTEGER NOT NULL DEFAULT 0,
    successful_executions INTEGER NOT NULL DEFAULT 0,
    failed_executions INTEGER NOT NULL DEFAULT 0,
    last_execution_at DATETIME,
    next_execution_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Индексы для auto_posting_rules
CREATE INDEX IF NOT EXISTS ix_auto_posting_rules_user_id ON auto_posting_rules(user_id);
CREATE INDEX IF NOT EXISTS ix_auto_posting_rules_is_active ON auto_posting_rules(is_active);
CREATE INDEX IF NOT EXISTS ix_auto_posting_rules_next_execution_at ON auto_posting_rules(next_execution_at);
CREATE INDEX IF NOT EXISTS ix_auto_posting_rules_created_at ON auto_posting_rules(created_at);
CREATE INDEX IF NOT EXISTS ix_auto_posting_user_active ON auto_posting_rules(user_id, is_active);
CREATE INDEX IF NOT EXISTS ix_auto_posting_next_execution ON auto_posting_rules(next_execution_at, is_active);

