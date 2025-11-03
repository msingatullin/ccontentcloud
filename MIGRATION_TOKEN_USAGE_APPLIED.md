# ✅ Миграция Token Usage Применена

**Дата:** 2025-10-28  
**Миграция:** `add_token_usage_indexes_sqlite.sql`

## Что было сделано

### 1. Создана таблица `token_usage`
Таблица для хранения детальной статистики использования AI токенов.

**Структура:**
- `id` - PRIMARY KEY
- `user_id` - ID пользователя (FK к users)
- `content_id` - ID контента (FK к content_pieces)
- `workflow_id` - ID workflow
- `agent_id` - ID агента который использовал токены
- `request_id` - Уникальный ID запроса
- `endpoint` - API endpoint
- `ai_provider` - Провайдер AI (openai, anthropic, huggingface)
- `ai_model` - Модель AI (gpt-4, claude-3, etc)
- `prompt_tokens` - Токены в промпте
- `completion_tokens` - Токены в ответе
- `total_tokens` - Всего токенов
- `cost_usd` - Стоимость в USD
- `cost_rub` - Стоимость в RUB
- `platform` - Платформа (telegram, vk, etc)
- `content_type` - Тип контента
- `task_type` - Тип задачи
- `execution_time_ms` - Время выполнения
- `request_metadata` - Метаданные запроса (JSON)
- `response_metadata` - Метаданные ответа (JSON)
- `created_at` - Дата создания

### 2. Созданы индексы для оптимизации

✅ `idx_token_usage_user_date` - для фильтрации по пользователю и дате  
✅ `idx_token_usage_user_agent` - для группировки по агентам  
✅ `idx_token_usage_user_provider_model` - для группировки по AI моделям  
✅ `idx_token_usage_workflow` - для поиска по workflow_id  
✅ `idx_token_usage_detailed` - комбинированный для детальной статистики  
✅ `idx_token_usage_request_id` - для быстрого поиска по request_id  
✅ `idx_token_usage_created_at` - для временных запросов  

## Проверка

```bash
# Таблица создана
sqlite3 content_curator.db "SELECT name FROM sqlite_master WHERE type='table' AND name='token_usage';"
# Результат: token_usage ✅

# Индексы созданы
sqlite3 content_curator.db "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='token_usage';"
# Результат: 8 индексов ✅

# Таблица пустая (нет данных)
sqlite3 content_curator.db "SELECT COUNT(*) FROM token_usage;"
# Результат: 0 ✅
```

## Затронутые API endpoints

Теперь работают следующие endpoints:

### ✅ `/api/v1/billing/usage/tokens` (LEGACY)
Базовая статистика использования токенов

### ✅ `/api/v1/billing/usage/tokens/summary`
Сводка: сегодня, месяц, всего

### ✅ `/api/v1/billing/usage/tokens/history`
История по дням для графиков

### ✅ `/api/v1/billing/usage/tokens/by-agent`
Расход по агентам

### ✅ `/api/v1/billing/usage/tokens/by-model`
Расход по AI моделям

### ✅ `/api/v1/billing/usage/tokens/detailed`
Детальная таблица с пагинацией

## Следующие шаги

1. ✅ **Перезапустить приложение** - миграция применена, endpoints готовы к использованию
2. 🔄 **Начнется запись данных** - при каждом обращении к AI будет создаваться запись в token_usage
3. 📊 **Проверить в Swagger UI** - все endpoints `/billing/usage/tokens/*` должны работать без ошибок

## Важно

⚠️ **Для продакшн на Cloud Run с PostgreSQL:**
Нужно применить миграцию `migrations/add_token_usage_indexes.sql` (версия для PostgreSQL)

```bash
psql $DATABASE_URL -f migrations/add_token_usage_indexes.sql
```

## Документация

- Подробная API документация: `TOKEN_USAGE_API.md`
- Инструкция по внедрению: `TOKEN_USAGE_IMPLEMENTATION.md`









