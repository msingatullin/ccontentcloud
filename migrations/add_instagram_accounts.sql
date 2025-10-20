-- Migration: Add Instagram Accounts support
-- Date: 2025-10-20
-- Description: Создает таблицу для хранения подключенных Instagram аккаунтов пользователей

-- Создаем таблицу Instagram аккаунтов
CREATE TABLE IF NOT EXISTS instagram_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Учетные данные (зашифрованные)
    instagram_username VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL,
    
    -- Информация об аккаунте
    account_name VARCHAR(255) NOT NULL,
    profile_pic_url TEXT,
    followers_count INTEGER,
    
    -- Статусы
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Данные сессии (JSON с session_id и cookies)
    session_data TEXT,
    last_login TIMESTAMP,
    
    -- Статистика публикаций
    posts_count INTEGER DEFAULT 0,
    last_post_at TIMESTAMP,
    last_error TEXT,
    
    -- Лимиты постинга
    daily_posts_limit INTEGER DEFAULT 10,
    posts_today INTEGER DEFAULT 0,
    posts_reset_date DATE DEFAULT CURRENT_DATE,
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Индексы
    CONSTRAINT unique_user_instagram UNIQUE (user_id, instagram_username)
);

-- Создаем индексы для быстрого поиска
CREATE INDEX idx_instagram_user_id ON instagram_accounts(user_id);
CREATE INDEX idx_instagram_user_active ON instagram_accounts(user_id, is_active);
CREATE INDEX idx_instagram_created_at ON instagram_accounts(created_at);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_instagram_accounts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_instagram_accounts_updated_at
    BEFORE UPDATE ON instagram_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_instagram_accounts_updated_at();

-- Комментарии к таблице
COMMENT ON TABLE instagram_accounts IS 'Подключенные Instagram аккаунты пользователей для автопостинга';
COMMENT ON COLUMN instagram_accounts.encrypted_password IS 'Пароль зашифрован с помощью Fernet (SOCIAL_TOKENS_ENCRYPTION_KEY)';
COMMENT ON COLUMN instagram_accounts.session_data IS 'JSON с сессионными данными Instagram (session_id, cookies)';
COMMENT ON COLUMN instagram_accounts.daily_posts_limit IS 'Максимум постов в день для защиты от блокировки (по умолчанию 10)';
COMMENT ON COLUMN instagram_accounts.posts_today IS 'Количество постов сегодня';
COMMENT ON COLUMN instagram_accounts.posts_reset_date IS 'Дата для сброса счетчика posts_today';


