-- Оптимизация запросов к таблице token_usage
-- Добавляет индексы для быстрой агрегации статистики

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

-- Добавляем проверку на положительные значения токенов
ALTER TABLE token_usage 
ADD CONSTRAINT check_tokens_positive 
CHECK (prompt_tokens >= 0 AND completion_tokens >= 0 AND total_tokens >= 0);

-- Добавляем проверку на соответствие total_tokens
ALTER TABLE token_usage 
ADD CONSTRAINT check_total_tokens_sum 
CHECK (total_tokens = prompt_tokens + completion_tokens);

-- Комментарии для документации
COMMENT ON INDEX idx_token_usage_user_date IS 'Быстрый поиск токенов пользователя по датам';
COMMENT ON INDEX idx_token_usage_user_agent IS 'Агрегация по агентам для конкретного пользователя';
COMMENT ON INDEX idx_token_usage_user_provider_model IS 'Статистика по AI провайдерам и моделям';
COMMENT ON INDEX idx_token_usage_workflow IS 'Отслеживание токенов в рамках workflow';
COMMENT ON INDEX idx_token_usage_detailed IS 'Детальная статистика с фильтрами';

-- Создаем материализованное представление для быстрой агрегации (опционально)
-- Обновляется раз в час через cron
CREATE MATERIALIZED VIEW IF NOT EXISTS token_usage_daily_stats AS
SELECT 
    user_id,
    DATE(created_at) as usage_date,
    agent_id,
    ai_provider,
    ai_model,
    COUNT(*) as requests_count,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    SUM(total_tokens) as total_tokens,
    SUM(cost_usd) as total_cost_usd,
    SUM(cost_rub) as total_cost_rub,
    AVG(execution_time_ms) as avg_execution_time_ms
FROM token_usage
GROUP BY user_id, DATE(created_at), agent_id, ai_provider, ai_model;

-- Индекс для materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_token_daily_stats_unique 
ON token_usage_daily_stats(user_id, usage_date, agent_id, ai_provider, ai_model);

CREATE INDEX IF NOT EXISTS idx_token_daily_stats_user_date 
ON token_usage_daily_stats(user_id, usage_date DESC);

-- Функция для обновления материализованного представления
CREATE OR REPLACE FUNCTION refresh_token_usage_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY token_usage_daily_stats;
END;
$$ LANGUAGE plpgsql;

-- Комментарий
COMMENT ON MATERIALIZED VIEW token_usage_daily_stats IS 
'Агрегированная статистика токенов по дням. Обновляется каждый час.';

COMMENT ON FUNCTION refresh_token_usage_stats() IS 
'Функция для обновления статистики токенов. Вызывается по расписанию.';

