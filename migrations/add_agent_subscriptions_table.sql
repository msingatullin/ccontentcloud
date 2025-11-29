-- Миграция: Добавление таблицы agent_subscriptions для Pay-Per-Agent биллинг модели
-- Дата: 2025-10-15
-- Описание: Реализует подписки на отдельных AI агентов

-- Создаем таблицу подписок на агентов
CREATE TABLE IF NOT EXISTS agent_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Информация об агенте
    agent_id VARCHAR(100) NOT NULL,
    agent_name VARCHAR(200),
    
    -- Статус подписки
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    price_monthly INTEGER NOT NULL, -- Цена в копейках
    
    -- Период действия
    starts_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Статистика использования за текущий месяц
    requests_this_month INTEGER NOT NULL DEFAULT 0,
    tokens_this_month INTEGER NOT NULL DEFAULT 0,
    cost_this_month INTEGER NOT NULL DEFAULT 0, -- В копейках
    
    -- Лимиты (опционально)
    max_requests_per_month INTEGER,
    max_tokens_per_month INTEGER,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,
    last_used_at TIMESTAMP,
    
    -- Источник подписки
    source VARCHAR(50), -- direct, bundle, trial, promotion
    bundle_id VARCHAR(100),
    
    -- Индексы для производительности
    CONSTRAINT agent_subscriptions_user_agent_unique UNIQUE (user_id, agent_id, status)
);

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_user_id ON agent_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_agent_id ON agent_subscriptions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_status ON agent_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_starts_at ON agent_subscriptions(starts_at);
CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_expires_at ON agent_subscriptions(expires_at);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_agent_subscription_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для обновления updated_at
DROP TRIGGER IF EXISTS trigger_update_agent_subscription_updated_at ON agent_subscriptions;
CREATE TRIGGER trigger_update_agent_subscription_updated_at
    BEFORE UPDATE ON agent_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_subscription_updated_at();

-- Комментарии к таблице
COMMENT ON TABLE agent_subscriptions IS 'Подписки пользователей на отдельных AI агентов (Pay-Per-Agent модель)';
COMMENT ON COLUMN agent_subscriptions.agent_id IS 'ID агента (chief_content_agent, drafting_agent, и т.д.)';
COMMENT ON COLUMN agent_subscriptions.status IS 'Статус: active, paused, cancelled, expired';
COMMENT ON COLUMN agent_subscriptions.price_monthly IS 'Цена подписки в копейках (99000 = 990₽)';
COMMENT ON COLUMN agent_subscriptions.cost_this_month IS 'Фактическая стоимость использования AI токенов в копейках';

-- Вставляем тестовые данные для первого пользователя (если есть)
-- Это можно закомментировать в продакшене
-- INSERT INTO agent_subscriptions (user_id, agent_id, agent_name, status, price_monthly, starts_at, expires_at)
-- SELECT 
--     1,
--     'drafting_agent',
--     'Drafting Agent',
--     'active',
--     99000,
--     CURRENT_TIMESTAMP,
--     CURRENT_TIMESTAMP + INTERVAL '30 days'
-- WHERE EXISTS (SELECT 1 FROM users WHERE id = 1)
-- ON CONFLICT (user_id, agent_id, status) DO NOTHING;

