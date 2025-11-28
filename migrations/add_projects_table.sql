-- Миграция: Добавление таблицы projects и связей с существующими таблицами
-- Дата: 2025-11-27
-- Описание: Создание сущности "Проект" для группировки соц.сетей и контента

-- ============================================
-- 1. Создание таблицы projects
-- ============================================

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Основная информация
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Статус
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Настройки проекта (JSON)
    settings JSONB DEFAULT '{}'::jsonb NOT NULL,
    ai_settings JSONB DEFAULT '{}'::jsonb NOT NULL,
    
    -- Временные метки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Индексы для projects
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS ix_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS ix_projects_user_active ON projects(user_id, is_active);

-- ============================================
-- 2. Добавление project_id в telegram_channels
-- ============================================

ALTER TABLE telegram_channels 
ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_telegram_channels_project_id ON telegram_channels(project_id);

-- ============================================
-- 3. Добавление project_id в content_pieces
-- ============================================

ALTER TABLE content_pieces 
ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_content_pieces_project_id ON content_pieces(project_id);

-- ============================================
-- 4. Добавление project_id в scheduled_posts
-- ============================================

ALTER TABLE scheduled_posts 
ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_scheduled_posts_project_id ON scheduled_posts(project_id);

-- ============================================
-- 4.1. Добавление project_id в instagram_accounts
-- ============================================

ALTER TABLE instagram_accounts 
ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_instagram_accounts_project_id ON instagram_accounts(project_id);

-- ============================================
-- 5. Триггер для обновления updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_projects_updated_at ON projects;
CREATE TRIGGER trigger_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_projects_updated_at();

-- ============================================
-- 6. Комментарии к таблице
-- ============================================

COMMENT ON TABLE projects IS 'Проекты пользователей для группировки соц.сетей и контента';
COMMENT ON COLUMN projects.settings IS 'Настройки проекта: tone_of_voice, target_audience, brand_name и т.д.';
COMMENT ON COLUMN projects.ai_settings IS 'AI настройки: preferred_style, content_length, emoji_usage и т.д.';


