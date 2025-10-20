-- Оптимизация запросов к таблице token_usage для SQLite
-- Добавляет индексы для быстрой агрегации статистики

-- Создаем таблицу если её нет (на основе модели TokenUsageDB)
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_id VARCHAR(36),
    workflow_id VARCHAR(36),
    agent_id VARCHAR(100) NOT NULL,
    request_id VARCHAR(255) UNIQUE,
    endpoint VARCHAR(100),
    ai_provider VARCHAR(50) NOT NULL,
    ai_model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    cost_rub REAL NOT NULL DEFAULT 0.0,
    platform VARCHAR(50),
    content_type VARCHAR(50),
    task_type VARCHAR(50),
    execution_time_ms INTEGER,
    request_metadata TEXT,
    response_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (content_id) REFERENCES content_pieces(id)
);

-- Индексы для фильтрации по дате и пользователю
CREATE INDEX IF NOT EXISTS idx_token_usage_user_date 
ON token_usage(user_id, created_at DESC);

-- Индекс для группировки по агентам
CREATE INDEX IF NOT EXISTS idx_token_usage_user_agent 
ON token_usage(user_id, agent_id);

-- Индекс для группировки по AI моделям
CREATE INDEX IF NOT EXISTS idx_token_usage_user_provider_model 
ON token_usage(user_id, ai_provider, ai_model);

-- Индекс для поиска по workflow_id
CREATE INDEX IF NOT EXISTS idx_token_usage_workflow 
ON token_usage(workflow_id) WHERE workflow_id IS NOT NULL;

-- Комбинированный индекс для детальной статистики
CREATE INDEX IF NOT EXISTS idx_token_usage_detailed 
ON token_usage(user_id, agent_id, created_at DESC);

-- Индекс на request_id для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_token_usage_request_id
ON token_usage(request_id);

-- Индекс на created_at для временных запросов
CREATE INDEX IF NOT EXISTS idx_token_usage_created_at
ON token_usage(created_at DESC);

