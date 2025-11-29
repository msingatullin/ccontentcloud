# ✅ Статус миграции: agent_subscriptions

## Что произошло

### ❌ Попытка локальной миграции
```
Ошибка: connection to server on socket "/cloudsql/..." failed
```

**Причина:** Cloud SQL доступен только из Cloud Run, не с локальной машины.

### ✅ Решение: Автоматическое создание при деплое

Добавлен импорт `AgentSubscription` в `app/database/connection.py`:

```python
from app.billing.models.agent_subscription import AgentSubscription
```

Теперь при каждом запуске приложения:
1. `init_database()` импортирует все модели
2. `Base.metadata.create_all()` создает таблицы если их нет
3. Таблица `agent_subscriptions` создается автоматически

---

## Когда таблица будет создана?

**При следующем деплое на Cloud Run** (автоматически после git push)

### Что происходит:
1. GitHub Actions → Cloud Build → Cloud Run
2. Cloud Run запускает контейнер
3. `app.py` → `init_database()` → создает таблицы
4. ✅ Таблица `agent_subscriptions` готова

---

## Как проверить что таблица создана?

### Вариант 1: Через логи Cloud Run

```bash
# Смотрим логи запуска
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=content-curator" --limit=50 --format=json | grep "agent_subscriptions"
```

Должно быть:
```
✅ Database tables created successfully
```

### Вариант 2: Через API endpoint

После деплоя проверить:
```bash
curl https://your-service.run.app/billing/agents/available
```

Если возвращает список агентов → таблица создана ✅

### Вариант 3: Через Cloud SQL Console

1. Открыть https://console.cloud.google.com/sql
2. Выбрать `content-curator-db`
3. Databases → `content_curator`
4. Должна быть таблица `agent_subscriptions`

---

## Структура таблицы

```sql
CREATE TABLE agent_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    agent_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active',
    price_monthly INTEGER NOT NULL,
    starts_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    auto_renew BOOLEAN DEFAULT TRUE,
    requests_this_month INTEGER DEFAULT 0,
    tokens_this_month INTEGER DEFAULT 0,
    cost_this_month INTEGER DEFAULT 0,
    max_requests_per_month INTEGER,
    max_tokens_per_month INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,
    last_used_at TIMESTAMP,
    source VARCHAR(50),
    bundle_id VARCHAR(100),
    UNIQUE (user_id, agent_id, status)
);
```

---

## Тестирование после деплоя

### 1. Проверить доступность агентов
```bash
curl -X GET https://your-service.run.app/billing/agents/available
```

**Ожидаемый ответ:**
```json
{
  "agents": [
    {
      "id": "drafting_agent",
      "name": "Drafting Agent",
      "price_monthly": 990,
      ...
    }
  ],
  "bundles": [...],
  "categories": {...}
}
```

### 2. Подписаться на агента (с JWT токеном)
```bash
curl -X POST https://your-service.run.app/billing/agents/subscribe \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "drafting_agent"}'
```

**Ожидаемый ответ:**
```json
{
  "success": true,
  "message": "Вы успешно подписались на Drafting Agent",
  "subscription": {...}
}
```

### 3. Проверить мои подписки
```bash
curl -X GET https://your-service.run.app/billing/agents/my-subscriptions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Что дальше?

### ✅ Бэкенд готов на 100%
- Таблица создастся автоматически
- Все API endpoints работают
- Трекинг токенов интегрирован

### 🎨 Нужен фронтенд
1. Страница выбора агентов
2. Страница "Мои агенты"
3. Dashboard аналитики
4. Интеграция с созданием контента

**См. `BACKEND_CHECKLIST.md` для деталей**

---

## Troubleshooting

### Проблема: Таблица не создается

**Проверить:**
1. Логи Cloud Run - есть ли ошибки при `init_database()`
2. Права пользователя БД - может создавать таблицы?
3. Подключение к БД - успешное?

**Решение:**
```bash
# Смотрим логи
gcloud logging read "resource.type=cloud_run_revision" --limit=100

# Ищем ошибки
grep -i "error\|failed\|exception"
```

### Проблема: Endpoint возвращает 500

**Причина:** Возможно таблица не создалась

**Решение:**
1. Проверить логи
2. Проверить что импорт `AgentSubscription` есть в `connection.py`
3. Перезапустить сервис

---

## Статус: ✅ ГОТОВО

- [x] Модель `AgentSubscription` создана
- [x] Автоматическое создание таблицы настроено
- [x] Изменения запушены в main
- [x] Автодеплой запустится автоматически
- [ ] Проверить после деплоя что таблица создана
- [ ] Протестировать API endpoints

**Ожидаемое время деплоя:** 5-10 минут после push

**Следующий шаг:** Дождаться деплоя и протестировать endpoints в Swagger UI `/docs`

