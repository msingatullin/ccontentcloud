# Гайд по тестированию flow создания и публикации контента

## Что было сделано

### 1. Исправления в backend

**Файлы изменены:**
- `app/orchestrator/main_orchestrator.py` - добавлен параметр `test_mode` в workflow и задачи
- `app/orchestrator/user_orchestrator_factory.py` - регистрация всех агентов когда нет подписок
- `app/orchestrator/main_orchestrator.py` - создание задач публикации и передача контента

**Что исправлено:**
1. ✅ `test_mode` передается из API запроса через workflow в задачи PublisherAgent
2. ✅ Агенты регистрируются без проверки подписок (для dev/testing)
3. ✅ Workflow создает задачи публикации для каждой платформы
4. ✅ Результат создания контента автоматически передается в задачу публикации

### 2. Flow работы

```
Фронтенд -> POST /api/v1/content/create
  ↓
ContentRequestSchema валидация
  ↓
UserOrchestratorFactory.get_orchestrator(user_id)
  ↓
ContentOrchestrator.process_content_request()
  ↓
create_content_workflow() создает:
  - Task "Create post for telegram" -> ChiefContentAgent
  - Task "Publish post to telegram" -> PublisherAgent
  ↓
execute_workflow():
  1. ChiefContentAgent создает контент
  2. Контент передается в задачу публикации
  3. PublisherAgent публикует в Telegram (test_mode)
  ↓
Результат сохраняется в БД (content_pieces, content_history)
```

## Как протестировать

### Вариант 1: Через Python скрипт (рекомендуется)

```bash
cd /home/mikhail/content-curator-cloud

# Получаем JWT токен (замените email/password на реальные)
TOKEN=$(wget -q -O - --post-data='{"email":"test@example.com","password":"Test123!"}' \
  --header='Content-Type: application/json' \
  'https://content-curator-dt3n7kzpwq-uc.a.run.app/api/v1/auth/login' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Запускаем тест
python3 test_content_create_flow.py "$TOKEN"
```

### Вариант 2: Через wget напрямую

```bash
# 1. Health check
wget -q -O - 'https://content-curator-dt3n7kzpwq-uc.a.run.app/health'

# 2. Получить профиль пользователя
wget -q -O - --header="Authorization: Bearer YOUR_TOKEN" \
  'https://content-curator-dt3n7kzpwq-uc.a.run.app/api/v1/auth/me'

# 3. Создать контент
wget -q -O - --post-data='{
  "title": "Тестовый пост",
  "description": "Описание",
  "target_audience": "Разработчики",
  "platforms": ["telegram"],
  "content_types": ["post"],
  "test_mode": true
}' \
  --header='Content-Type: application/json' \
  --header="Authorization: Bearer YOUR_TOKEN" \
  'https://content-curator-dt3n7kzpwq-uc.a.run.app/api/v1/content/create'

# 4. Проверить статус workflow
wget -q -O - --header="Authorization: Bearer YOUR_TOKEN" \
  'https://content-curator-dt3n7kzpwq-uc.a.run.app/api/v1/workflow/WORKFLOW_ID/status'
```

## Что проверяет тест

1. ✅ **Health Check** - API доступен
2. ✅ **User Profile** - получение данных пользователя и его социальных сетей
3. ✅ **Create Content** - создание контента с `test_mode: true`
4. ✅ **Workflow Status** - проверка статуса выполнения workflow

## Ожидаемый результат

### Успешный сценарий:

```json
{
  "success": true,
  "workflow_id": "wf_abc123...",
  "brief_id": "brief_123...",
  "result": {
    "workflow_id": "wf_abc123...",
    "status": "completed",
    "results": {
      "task_1": {
        "content": {
          "id": "content_123",
          "title": "...",
          "text": "...",
          "platform": "telegram"
        }
      },
      "task_2": {
        "publication": {
          "status": "test_mode",
          "message": "Контент готов к публикации (тестовый режим)"
        }
      }
    },
    "completed_tasks": 2,
    "failed_tasks": 0,
    "total_tasks": 2
  }
}
```

### В логах GCP должно быть:

```
INFO: Found 0 active agent subscriptions for user X
WARNING: Agent subscriptions not available. Registering all agents.
INFO: Successfully registered 10 agents (all available)
INFO: Создан workflow wf_xxx для бриф brief_xxx с задачами создания и публикации
INFO: PublisherAgent выполняет задачу: Publish post to telegram
INFO: Публикация в test mode: контент готов к отправке
```

## Критические проблемы которые были найдены

### Проблема 1: Нет подписок на агентов ❌
**Решение:** UserOrchestratorFactory теперь регистрирует всех агентов если таблицы agent_subscriptions нет

### Проблема 2: Нет Telegram каналов у пользователя ⚠️
**Статус:** Не критично для test_mode, но для реальной публикации нужны каналы

**Как добавить Telegram канал:**
```sql
INSERT INTO telegram_channels (
  user_id, 
  channel_name, 
  channel_username, 
  chat_id, 
  is_active, 
  is_default, 
  is_verified
) VALUES (
  5,  -- user_id
  'Test Channel',
  '@testchannel',
  -1001234567890,  -- реальный chat_id
  1,  -- is_active
  1,  -- is_default
  1   -- is_verified
);
```

### Проблема 3: test_mode не передавался ❌
**Решение:** Добавлен параметр test_mode в signature методов и передача через контекст workflow

### Проблема 4: Workflow не создавал задачу публикации ❌
**Решение:** Добавлено создание задачи "Publish {content_type} to {platform}"

## Проверка логов

```bash
# Смотреть логи последнего запуска
gcloud logging read "resource.type=cloud_run_revision 
  AND resource.labels.service_name=content-curator
  AND severity>=INFO" \
  --limit 100 --format json \
  --project YOUR_PROJECT_ID
```

## Дополнительная информация

- **API URL:** https://content-curator-dt3n7kzpwq-uc.a.run.app
- **Тестовый скрипт:** `test_content_create_flow.py`
- **Frontend:** работает на моках, не зависит от backend изменений
- **БД:** SQLite для dev, PostgreSQL для prod (через Cloud SQL)

## Next Steps

После успешного теста:
1. Добавить реальные Telegram каналы для пользователя
2. Отключить `test_mode` для реальной публикации
3. Настроить TelegramMCP с реальным bot token
4. Проверить сохранение результатов в БД

## Troubleshooting

**Q: Ошибка "No available agent"**
A: Проверьте что UserOrchestratorFactory зарегистрировал агентов. Смотрите логи на "Successfully registered X agents"

**Q: Ошибка "No active session"**
A: Проблема с lazy loading SQLAlchemy. Уже исправлена в User._get_social_media_status()

**Q: Timeout 30 секунд**
A: Была проблема с session в _get_social_media_status(). Проверьте что используется последняя версия кода.

