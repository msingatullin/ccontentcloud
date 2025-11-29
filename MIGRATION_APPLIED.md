# ✅ Миграция БД применена успешно!

**Дата:** 20 октября 2025  
**Время:** MSK (Europe/Moscow)  
**БД:** SQLite (content_curator.db)  
**Статус:** ✅ Успешно

---

## 📊 Что сделано

### 1. Создана таблица `token_usage`
```sql
CREATE TABLE token_usage (
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
```

### 2. Добавлено 7 индексов
✅ `idx_token_usage_user_date` - (user_id, created_at DESC)  
✅ `idx_token_usage_user_agent` - (user_id, agent_id)  
✅ `idx_token_usage_user_provider_model` - (user_id, ai_provider, ai_model)  
✅ `idx_token_usage_workflow` - (workflow_id) WHERE workflow_id IS NOT NULL  
✅ `idx_token_usage_detailed` - (user_id, agent_id, created_at DESC)  
✅ `idx_token_usage_request_id` - (request_id)  
✅ `idx_token_usage_created_at` - (created_at DESC)  

### 3. Проверка целостности
```bash
sqlite3 content_curator.db "PRAGMA integrity_check;"
# Результат: ok
```

---

## 🚀 API Endpoints готовы к использованию

После перезапуска backend доступны:

### 1. **Сводка**
```bash
GET /api/billing/usage/tokens/summary
```
Возвращает статистику: сегодня, месяц, всего

### 2. **История**
```bash
GET /api/billing/usage/tokens/history?days=30
```
График расхода по дням

### 3. **По агентам**
```bash
GET /api/billing/usage/tokens/by-agent?period_days=30
```
Какой агент сколько расходует

### 4. **По моделям**
```bash
GET /api/billing/usage/tokens/by-model?period_days=30
```
GPT-4, GPT-3.5, Claude и т.д.

### 5. **Детальная таблица**
```bash
GET /api/billing/usage/tokens/detailed?limit=100&offset=0
```
С пагинацией и фильтрами

---

## 🔧 Следующий шаг

**Перезапустить backend для активации новых endpoints:**

```bash
# Если запущен локально
pkill -f "python app.py"
python app.py

# Или если через systemd/supervisor
sudo systemctl restart content-curator

# Или если в Docker
docker-compose restart backend
```

---

## 📝 Файлы миграции

1. **PostgreSQL:** `migrations/add_token_usage_indexes.sql`
   - С материализованными представлениями
   - Функции для автообновления
   - Для продакшн на Cloud SQL

2. **SQLite:** `migrations/add_token_usage_indexes_sqlite.sql` ✅ (применена)
   - Упрощенная версия
   - Для локальной разработки
   - Используется сейчас

---

## ✅ Проверка работы

После перезапуска проверь любой endpoint:

```bash
# Получить JWT токен (если нужен)
# ... твой способ получения токена ...

# Проверить сводку
curl -H "Authorization: Bearer YOUR_JWT" \
  http://localhost:8080/api/billing/usage/tokens/summary

# Ожидаемый ответ:
{
  "success": true,
  "data": {
    "today": {
      "total_tokens": 0,
      "cost_rub": 0.0,
      "requests_count": 0
    },
    "this_month": {
      "total_tokens": 0,
      "cost_rub": 0.0,
      "requests_count": 0
    },
    "all_time": {
      "total_tokens": 0,
      "cost_rub": 0.0,
      "requests_count": 0
    }
  }
}
```

Сейчас будут нули, потому что таблица пустая. Как только начнешь использовать AI агенты - данные будут записываться.

---

## 📊 Когда появятся данные?

Данные в `token_usage` записываются автоматически при использовании:

1. **Community Concierge Agent** - при ответе на комментарии
2. **Multimedia Producer Agent** - при генерации изображений
3. **Legal Guard Agent** - при проверке контента
4. **Trends Scout Agent** - при анализе трендов
5. **Research Factcheck Agent** - при фактчекинге
6. **Repurpose Agent** - при адаптации контента

Каждый вызов AI (OpenAI, Anthropic) записывает:
- Количество токенов
- Стоимость в USD и RUB
- Время выполнения
- Используемую модель

---

## 🎉 Готово!

Система учета токенов полностью функциональна:
- ✅ База данных настроена
- ✅ Индексы созданы
- ✅ API endpoints готовы
- ✅ Документация написана

**Осталось только перезапустить backend!** 🚀

