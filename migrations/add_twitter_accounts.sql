-- Migration: Add Twitter Accounts support
-- Date: 2025-10-20
-- Description: Создает таблицу для хранения подключенных Twitter аккаунтов пользователей

-- Создаем таблицу Twitter аккаунтов
CREATE TABLE IF NOT EXISTS twitter_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- OAuth токены (зашифрованные)
    encrypted_access_token TEXT NOT NULL,
    encrypted_access_token_secret TEXT NOT NULL,
    
    -- Информация об аккаунте Twitter
    twitter_user_id VARCHAR(255) NOT NULL,
    twitter_username VARCHAR(255) NOT NULL,
    twitter_display_name VARCHAR(255),
    profile_image_url TEXT,
    followers_count INTEGER,
    
    -- Название для отображения в UI
    account_name VARCHAR(255) NOT NULL,
    
    -- Статусы
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Статистика публикаций
    tweets_count INTEGER DEFAULT 0,
    last_tweet_at TIMESTAMP,
    last_error TEXT,
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Индексы
    CONSTRAINT unique_user_twitter UNIQUE (user_id, twitter_user_id)
);

-- Создаем индексы для быстрого поиска
CREATE INDEX idx_twitter_user_id ON twitter_accounts(user_id);
CREATE INDEX idx_twitter_user_active ON twitter_accounts(user_id, is_active);
CREATE INDEX idx_twitter_created_at ON twitter_accounts(created_at);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_twitter_accounts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_twitter_accounts_updated_at
    BEFORE UPDATE ON twitter_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_twitter_accounts_updated_at();

-- Комментарии к таблице
COMMENT ON TABLE twitter_accounts IS 'Подключенные Twitter аккаунты пользователей для автопостинга';
COMMENT ON COLUMN twitter_accounts.encrypted_access_token IS 'OAuth Access Token зашифрован с помощью Fernet (SOCIAL_TOKENS_ENCRYPTION_KEY)';
COMMENT ON COLUMN twitter_accounts.encrypted_access_token_secret IS 'OAuth Access Token Secret зашифрован с помощью Fernet (SOCIAL_TOKENS_ENCRYPTION_KEY)';
COMMENT ON COLUMN twitter_accounts.twitter_user_id IS 'Уникальный ID пользователя в Twitter';


