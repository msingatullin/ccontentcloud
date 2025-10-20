-- Миграция: Добавление таблицы для Telegram каналов пользователей
-- Дата: 2025-10-20
-- Описание: Архитектура "ОДИН БОТ - МНОГО КАНАЛОВ"
-- Позволяет каждому пользователю подключить свои Telegram каналы для публикации

-- Создание таблицы telegram_channels
CREATE TABLE IF NOT EXISTS telegram_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    -- Информация о канале
    channel_name VARCHAR(255) NOT NULL,
    channel_username VARCHAR(255),
    chat_id VARCHAR(255) NOT NULL,
    
    -- Статус подключения
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    is_verified BOOLEAN DEFAULT 0 NOT NULL,
    is_default BOOLEAN DEFAULT 0 NOT NULL,
    
    -- Метаданные канала из Telegram API
    channel_title VARCHAR(500),
    channel_type VARCHAR(50),
    members_count INTEGER,
    
    -- Статистика использования
    posts_count INTEGER DEFAULT 0 NOT NULL,
    last_post_at DATETIME,
    last_error TEXT,
    
    -- Временные метки
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Внешний ключ на пользователя
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS ix_telegram_channels_user_id 
ON telegram_channels(user_id);

CREATE INDEX IF NOT EXISTS ix_telegram_channels_chat_id 
ON telegram_channels(chat_id);

CREATE INDEX IF NOT EXISTS ix_telegram_channels_user_active 
ON telegram_channels(user_id, is_active);

-- Уникальный индекс: один канал может быть подключен только один раз к одному пользователю
CREATE UNIQUE INDEX IF NOT EXISTS ix_telegram_channels_user_chat 
ON telegram_channels(user_id, chat_id);

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER IF NOT EXISTS telegram_channels_update_timestamp 
AFTER UPDATE ON telegram_channels
FOR EACH ROW
BEGIN
    UPDATE telegram_channels 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Комментарии для документации
-- user_id: ID пользователя из таблицы users
-- channel_name: Название канала для отображения в UI (задается пользователем)
-- channel_username: @username канала если публичный
-- chat_id: ID канала в Telegram (может быть -1001234567890 или @username)
-- is_active: Активен ли канал (false = удален/деактивирован)
-- is_verified: Проверен ли канал (бот есть в админах с правами на постинг)
-- is_default: Используется ли канал по умолчанию для публикаций
-- channel_title: Название канала из Telegram API
-- channel_type: Тип: channel, group, supergroup
-- members_count: Количество подписчиков
-- posts_count: Количество опубликованных постов через систему
-- last_post_at: Дата последней публикации
-- last_error: Последняя ошибка при публикации

-- Примечание: Используется один общий бот (@content4ubot) для всех пользователей
-- Бот постит в разные каналы используя chat_id из этой таблицы

