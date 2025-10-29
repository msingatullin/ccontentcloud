-- Создание таблицы token_usage для PostgreSQL
-- Детальный учет использования AI токенов

CREATE TABLE IF NOT EXISTS token_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_id VARCHAR(36) REFERENCES content_pieces(id) ON DELETE SET NULL,
    workflow_id VARCHAR(36),
    agent_id VARCHAR(100) NOT NULL,
    
    -- Запрос
    request_id VARCHAR(255) UNIQUE,
    endpoint VARCHAR(100),
    
    -- AI Модель
    ai_provider VARCHAR(50) NOT NULL,  -- openai, anthropic, huggingface
    ai_model VARCHAR(100) NOT NULL,    -- gpt-3.5-turbo, gpt-4, dall-e-3
    
    -- Токены
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    
    -- Стоимость
    cost_usd DECIMAL(10, 4) NOT NULL DEFAULT 0.0,
    cost_rub DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
    
    -- Контекст
    platform VARCHAR(50),           -- telegram, vk, instagram, twitter
    content_type VARCHAR(50),       -- post, thread, story, video
    task_type VARCHAR(50),          -- generation, analysis, transformation
    
    -- Метрики
    execution_time_ms INTEGER,
    
    -- Метаданные (JSON)
    request_metadata JSONB,
    response_metadata JSONB,
    
    -- Временные метки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Проверки
    CONSTRAINT check_tokens_positive 
        CHECK (prompt_tokens >= 0 AND completion_tokens >= 0 AND total_tokens >= 0),
    CONSTRAINT check_total_tokens_sum 
        CHECK (total_tokens = prompt_tokens + completion_tokens)
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_token_usage_user_date 
    ON token_usage(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_token_usage_user_agent 
    ON token_usage(user_id, agent_id);

CREATE INDEX IF NOT EXISTS idx_token_usage_user_provider_model 
    ON token_usage(user_id, ai_provider, ai_model);

CREATE INDEX IF NOT EXISTS idx_token_usage_workflow 
    ON token_usage(workflow_id) WHERE workflow_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_token_usage_detailed 
    ON token_usage(user_id, agent_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_token_usage_request_id 
    ON token_usage(request_id) WHERE request_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_token_usage_created_at 
    ON token_usage(created_at DESC);

-- Комментарии для документации
COMMENT ON TABLE token_usage IS 
'Детальный учет использования AI токенов для биллинга и аналитики';

COMMENT ON COLUMN token_usage.user_id IS 'ID пользователя (владельца контента)';
COMMENT ON COLUMN token_usage.agent_id IS 'ID агента который использовал AI';
COMMENT ON COLUMN token_usage.ai_provider IS 'Провайдер AI (openai, anthropic, huggingface)';
COMMENT ON COLUMN token_usage.ai_model IS 'Модель AI (gpt-4, claude-3, dall-e-3, etc)';
COMMENT ON COLUMN token_usage.total_tokens IS 'Всего токенов (prompt + completion)';
COMMENT ON COLUMN token_usage.cost_rub IS 'Стоимость в рублях';

-- Права доступа (опционально)
-- GRANT SELECT, INSERT ON token_usage TO your_app_user;



