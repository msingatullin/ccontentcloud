-- Migration: Add Social Media Accounts (Instagram & Twitter)
-- Date: 2025-10-20
-- Description: Создает таблицы для Instagram и Twitter аккаунтов пользователей
-- Run: psql -U <user> -d <database> -f migrations/add_social_media_accounts.sql

-- ==========================================
-- INSTAGRAM ACCOUNTS
-- ==========================================

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

COMMENT ON TABLE instagram_accounts IS 'Подключенные Instagram аккаунты пользователей для автопостинга';

-- ==========================================
-- TWITTER ACCOUNTS
-- ==========================================

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

COMMENT ON TABLE twitter_accounts IS 'Подключенные Twitter аккаунты пользователей для автопостинга';

-- ==========================================
-- VERIFICATION
-- ==========================================

-- Проверка созданных таблиц
SELECT 
    tablename,
    schemaname
FROM pg_tables 
WHERE tablename IN ('instagram_accounts', 'twitter_accounts');

-- Подсчет строк
SELECT 
    'instagram_accounts' as table_name, 
    COUNT(*) as row_count 
FROM instagram_accounts
UNION ALL
SELECT 
    'twitter_accounts' as table_name, 
    COUNT(*) as row_count 
FROM twitter_accounts;


