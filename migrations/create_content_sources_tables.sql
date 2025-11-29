-- Миграция для создания таблиц системы мониторинга контента
-- Дата: 2024
-- Автор: Content Curator Team

-- 1. Таблица источников контента
CREATE TABLE IF NOT EXISTS content_sources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Основная информация
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Тип источника и URL
    source_type VARCHAR(50) NOT NULL, -- 'website', 'rss', 'news_api', 'social'
    url TEXT NOT NULL,
    
    -- Конфигурация источника
    config JSONB DEFAULT '{}'::jsonb,
    
    -- Метод извлечения контента
    extraction_method VARCHAR(50) DEFAULT 'ai', -- 'ai', 'selectors', 'rss'
    
    -- Правила фильтрации
    keywords JSONB DEFAULT '[]'::jsonb,
    exclude_keywords JSONB DEFAULT '[]'::jsonb,
    categories JSONB DEFAULT '[]'::jsonb,
    
    -- Настройки автопостинга
    auto_post_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    post_delay_minutes INTEGER DEFAULT 0,
    post_template TEXT,
    
    -- Связь с правилами автопостинга
    auto_posting_rule_id INTEGER REFERENCES auto_posting_rules(id) ON DELETE SET NULL,
    
    -- Расписание проверок
    check_interval_minutes INTEGER NOT NULL DEFAULT 60,
    next_check_at TIMESTAMP,
    last_check_at TIMESTAMP,
    last_check_status VARCHAR(50),
    last_error_message TEXT,
    
    -- Статус источника
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Статистика
    total_checks INTEGER NOT NULL DEFAULT 0,
    total_items_found INTEGER NOT NULL DEFAULT 0,
    total_items_new INTEGER NOT NULL DEFAULT 0,
    total_posts_created INTEGER NOT NULL DEFAULT 0,
    
    -- Хранение последнего снимка для diff
    last_snapshot_hash VARCHAR(64),
    last_snapshot_data JSONB,
    
    -- Временные метки
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для content_sources
CREATE INDEX IF NOT EXISTS idx_content_sources_user_id ON content_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_content_sources_source_type ON content_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_content_sources_is_active ON content_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_content_sources_next_check ON content_sources(next_check_at) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_content_sources_user_active ON content_sources(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_content_sources_type_active ON content_sources(source_type, is_active);
CREATE INDEX IF NOT EXISTS idx_content_sources_created_at ON content_sources(created_at);


-- 2. Таблица найденных элементов контента
CREATE TABLE IF NOT EXISTS monitored_items (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES content_sources(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Данные элемента
    external_id VARCHAR(255),
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    url TEXT,
    image_url TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP,
    
    -- Метаданные
    raw_data JSONB,
    extracted_data JSONB,
    
    -- Обработка и статус
    status VARCHAR(50) NOT NULL DEFAULT 'new', -- new, approved, posted, ignored, duplicate, error
    duplicate_of INTEGER REFERENCES monitored_items(id) ON DELETE SET NULL,
    
    -- AI анализ
    relevance_score FLOAT NOT NULL DEFAULT 0.0,
    ai_summary TEXT,
    ai_sentiment VARCHAR(50),
    ai_category VARCHAR(100),
    ai_keywords JSONB DEFAULT '[]'::jsonb,
    
    -- Связь с созданным контентом
    content_id VARCHAR(36) REFERENCES content_pieces(id) ON DELETE SET NULL,
    scheduled_post_id INTEGER REFERENCES scheduled_posts(id) ON DELETE SET NULL,
    
    -- Временные метки
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    posted_at TIMESTAMP
);

-- Индексы для monitored_items
CREATE INDEX IF NOT EXISTS idx_monitored_items_source_id ON monitored_items(source_id);
CREATE INDEX IF NOT EXISTS idx_monitored_items_user_id ON monitored_items(user_id);
CREATE INDEX IF NOT EXISTS idx_monitored_items_status ON monitored_items(status);
CREATE INDEX IF NOT EXISTS idx_monitored_items_external_id ON monitored_items(external_id);
CREATE INDEX IF NOT EXISTS idx_monitored_items_published_at ON monitored_items(published_at);
CREATE INDEX IF NOT EXISTS idx_monitored_items_source_status ON monitored_items(source_id, status);
CREATE INDEX IF NOT EXISTS idx_monitored_items_user_status ON monitored_items(user_id, status);
CREATE INDEX IF NOT EXISTS idx_monitored_items_relevance ON monitored_items(relevance_score, status);
CREATE INDEX IF NOT EXISTS idx_monitored_items_created_at ON monitored_items(created_at);


-- 3. Таблица истории проверок источников
CREATE TABLE IF NOT EXISTS source_check_history (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES content_sources(id) ON DELETE CASCADE,
    
    -- Результаты проверки
    checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    items_found INTEGER NOT NULL DEFAULT 0,
    items_new INTEGER NOT NULL DEFAULT 0,
    items_duplicate INTEGER NOT NULL DEFAULT 0,
    items_posted INTEGER NOT NULL DEFAULT 0,
    
    -- Статус
    status VARCHAR(50) NOT NULL, -- 'success', 'error', 'partial'
    error_message TEXT,
    
    -- Производительность
    execution_time_ms INTEGER
);

-- Индексы для source_check_history
CREATE INDEX IF NOT EXISTS idx_source_check_history_source_id ON source_check_history(source_id);
CREATE INDEX IF NOT EXISTS idx_source_check_history_checked_at ON source_check_history(checked_at);
CREATE INDEX IF NOT EXISTS idx_source_check_history_source_date ON source_check_history(source_id, checked_at);


-- Комментарии к таблицам
COMMENT ON TABLE content_sources IS 'Источники контента для автоматического мониторинга и создания постов';
COMMENT ON TABLE monitored_items IS 'Элементы контента найденные системой мониторинга';
COMMENT ON TABLE source_check_history IS 'История проверок источников контента';

-- Комментарии к важным полям
COMMENT ON COLUMN content_sources.source_type IS 'Тип источника: website (crawler), rss (RSS feed), news_api (новостные API), social (соцсети)';
COMMENT ON COLUMN content_sources.extraction_method IS 'Метод извлечения: ai (AI-based), selectors (CSS селекторы), rss (RSS парсер)';
COMMENT ON COLUMN monitored_items.status IS 'Статус элемента: new (новый), approved (утвержден), posted (опубликован), ignored (игнорирован), duplicate (дубликат), error (ошибка)';
COMMENT ON COLUMN monitored_items.relevance_score IS 'Оценка релевантности от 0.0 до 1.0, определяется AI';

