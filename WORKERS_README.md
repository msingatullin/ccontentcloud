# 🔄 Background Workers - Документация

## Что реализовано

### 1. ScheduledPostsWorker
**Назначение:** Автоматическая публикация запланированных постов

**Как работает:**
- Запускается в отдельном thread при старте приложения
- Каждую минуту (60s) проверяет таблицу `scheduled_posts`
- Находит посты где `scheduled_time <= NOW()` и `status = 'scheduled'`
- Публикует через интеграции Telegram/Instagram/Twitter
- Обновляет статусы: `published` (успех) или `failed` (ошибка)

**Файл:** `app/workers/scheduled_posts_worker.py`

### 2. AutoPostingWorker
**Назначение:** Автоматическое создание и публикация контента по правилам

**Как работает:**
- Запускается в отдельном thread при старте приложения
- Каждые 5 минут (300s) проверяет таблицу `auto_posting_rules`
- Находит правила где `next_execution_at <= NOW()` и `is_active = true`
- Создает контент через AI
- Планирует публикацию через `scheduled_posts`
- Обновляет статистику выполнения

**Файл:** `app/workers/auto_posting_worker.py`

---

## 🚀 Запуск

### Локальный режим

```bash
# Workers запускаются автоматически
python app.py
```

**Логи запуска:**
```
2025-11-14 12:00:00 - app - INFO - Запуск background workers...
2025-11-14 12:00:00 - app - INFO - ✅ ScheduledPostsWorker запущен (интервал: 60s)
2025-11-14 12:00:00 - app - INFO - ✅ AutoPostingWorker запущен (интервал: 300s)
2025-11-14 12:00:00 - app - INFO - 🚀 Все background workers успешно запущены
```

### Production (Gunicorn)

Workers запускаются автоматически при старте каждого worker процесса gunicorn.

```bash
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

---

## ⚙️ Конфигурация

### Переменные окружения

```bash
# Отключить workers (для тестов/дебага)
DISABLE_WORKERS=true

# Базовый URL API (для AutoPostingWorker)
API_BASE_URL=https://content-curator-1046574462613.us-central1.run.app
```

### Изменение интервалов

В `app.py`:

```python
# Scheduled Posts Worker - по умолчанию 60 секунд
scheduled_posts_worker = ScheduledPostsWorker(check_interval=60)

# Auto Posting Worker - по умолчанию 300 секунд (5 минут)
auto_posting_worker = AutoPostingWorker(check_interval=300)
```

---

## 🧪 Тестирование

### 1. Тест ScheduledPostsWorker

**Шаг 1:** Создать контент
```bash
curl -X POST http://localhost:8080/api/v1/content/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тестовый пост",
    "description": "Создай короткий пост о Python"
  }'
```

**Шаг 2:** Запланировать публикацию (на 1 минуту вперед)
```bash
curl -X POST http://localhost:8080/api/v1/scheduled-posts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "CONTENT_ID_FROM_STEP_1",
    "platform": "telegram",
    "scheduled_time": "2025-11-14T12:01:00Z"
  }'
```

**Шаг 3:** Проверить логи
```bash
# Должны появиться логи через 1 минуту:
# ScheduledPostsWorker - INFO - Найдено 1 постов для публикации
# ScheduledPostsWorker - INFO - Публикация поста 1 (content_id=..., platform=telegram)
# ScheduledPostsWorker - INFO - Пост 1 успешно опубликован
```

**Шаг 4:** Проверить статус
```bash
curl -X GET http://localhost:8080/api/v1/scheduled-posts/1 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Должен быть status: "published"
```

### 2. Тест AutoPostingWorker

**Шаг 1:** Создать правило автопостинга
```bash
curl -X POST http://localhost:8080/api/v1/auto-posting/rules \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовое правило",
    "schedule_type": "daily",
    "schedule_config": {
      "times": ["12:05"],
      "days_of_week": [1,2,3,4,5,6,7]
    },
    "content_config": {
      "title": "Ежедневный пост",
      "description": "Создай пост о технологиях"
    },
    "platforms": ["telegram"]
  }'
```

**Шаг 2:** Дождаться выполнения (когда текущее время = 12:05)

**Шаг 3:** Проверить логи
```bash
# Должны появиться логи:
# AutoPostingWorker - INFO - Найдено 1 правил для выполнения
# AutoPostingWorker - INFO - Выполнение правила 1 'Тестовое правило'
# AutoPostingWorker - INFO - Создан контент ... для правила 1
# AutoPostingWorker - INFO - Правило 1 успешно выполнено
```

**Шаг 4:** Проверить созданные посты
```bash
curl -X GET http://localhost:8080/api/v1/scheduled-posts?status=scheduled \
  -H "Authorization: Bearer YOUR_TOKEN"

# Должен быть создан новый запланированный пост
```

### 3. Тест отключения workers

```bash
DISABLE_WORKERS=true python app.py

# В логах должно быть:
# ⚠️ WORKERS DISABLED: Background workers отключены
```

---

## 📊 Мониторинг

### Проверка работы workers

```bash
# Логи приложения
tail -f logs/app.log | grep Worker

# Логи scheduled posts
tail -f logs/app.log | grep "ScheduledPostsWorker"

# Логи auto posting
tail -f logs/app.log | grep "AutoPostingWorker"
```

### Метрики

Можно добавить в будущем:
- Количество обработанных постов
- Количество ошибок публикации
- Время выполнения
- Alerting при падении workers

---

## 🐛 Troubleshooting

### Worker не запускается

**Проблема:** Логов о запуске workers нет

**Решение:**
1. Проверить `DISABLE_WORKERS` не установлен в `true`
2. Проверить что нет ошибок импорта: `python -c "from app.workers import ScheduledPostsWorker"`
3. Проверить логи: `tail -f logs/app.log`

### Посты не публикуются

**Проблема:** Worker работает, но посты остаются в статусе `scheduled`

**Решение:**
1. Проверить что `scheduled_time` в прошлом (UTC)
2. Проверить логи worker'а на ошибки
3. Проверить интеграции (Telegram bot token, etc)
4. Проверить статусы в БД: `SELECT * FROM scheduled_posts WHERE status='failed'`

### Worker падает с ошибкой

**Проблема:** Exception в логах worker'а

**Решение:**
1. Worker автоматически перезапустится через `check_interval` секунд
2. Проверить стек ошибки в логах
3. Проверить доступность БД
4. Проверить доступность внешних API

---

## 🔧 Улучшения (TODO)

### 1. Интеграция с PublisherAgent
Сейчас используются прямые вызовы интеграций. Можно улучшить:
```python
# Вместо прямого вызова TelegramIntegration
result = await publisher_agent.publish_to_platform(content, platform, account_id)
```

### 2. Реальное создание контента для AutoPosting
Сейчас используется mock. Нужно:
```python
# Прямой вызов через ContentOrchestrator
from app.orchestrator.user_orchestrator_factory import UserOrchestratorFactory

orchestrator = UserOrchestratorFactory.get_or_create(user_id)
content = await orchestrator.create_content(rule.content_config)
```

### 3. Rate limiting
Добавить учет лимитов платформ:
- Telegram: 30 постов/час
- Instagram: 25 постов/час
- Twitter: 300 постов/час

### 4. Retry механизм
При ошибках пытаться повторить публикацию:
```python
max_retries = 3
for attempt in range(max_retries):
    result = publish()
    if result.success:
        break
    time.sleep(60 * (attempt + 1))  # Exponential backoff
```

### 5. Health check endpoint
```python
@app.route('/health/workers')
def workers_health():
    return {
        'scheduled_posts_worker': scheduled_posts_worker.is_running,
        'auto_posting_worker': auto_posting_worker.is_running
    }
```

---

## 📝 Логи и отладка

### Увеличить детализацию логов

В `app/workers/scheduled_posts_worker.py`:
```python
# Изменить уровень логирования
logger.setLevel(logging.DEBUG)
```

### Тестовый режим

Для быстрого тестирования можно уменьшить интервалы:
```python
# В app.py
scheduled_posts_worker = ScheduledPostsWorker(check_interval=10)  # 10 секунд
```

---

**Версия:** 1.0  
**Дата:** 14 ноября 2025  
**Автор:** AI Assistant

