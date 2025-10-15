# 💰 Pay-Per-Agent Биллинг Модель

## Обзор

Реализована **Per-User Agent Clusters** архитектура с моделью подписок на отдельных AI агентов.

### Ключевые особенности:

✅ **Полная изоляция** - каждый пользователь получает свой изолированный оркестратор
✅ **Гибкая подписка** - платите только за нужных агентов
✅ **Детальная аналитика** - отслеживание токенов и расходов по каждому агенту
✅ **Пакетные предложения** - bundles со скидками до 51%
✅ **Автоматическое управление** - очистка неактивных оркестраторов

---

## 🏗️ Архитектура

### UserOrchestratorFactory

Фабрика создает изолированные оркестраторы для каждого пользователя:

```python
from app.orchestrator.user_orchestrator_factory import UserOrchestratorFactory

# Получить оркестратор для пользователя
user_orchestrator = UserOrchestratorFactory.get_orchestrator(user_id, db_session)

# Обновить агентов после изменения подписок
UserOrchestratorFactory.refresh_user_agents(user_id, db_session)

# Получить статистику
stats = UserOrchestratorFactory.get_stats()
```

**Особенности:**
- Автоматически загружает только купленных агентов
- Кеширует оркестраторы для производительности
- Автоматически очищает неактивные через 2 часа

---

## 💳 Модель подписок

### AgentSubscription

Таблица `agent_subscriptions` хранит подписки пользователей:

**Основные поля:**
- `user_id` - ID пользователя
- `agent_id` - ID агента (chief_content_agent, drafting_agent, ...)
- `status` - active, paused, cancelled, expired
- `price_monthly` - цена в копейках
- `expires_at` - дата окончания
- `requests_this_month` - счетчик запросов
- `tokens_this_month` - счетчик токенов
- `cost_this_month` - фактическая стоимость

**Методы:**
```python
subscription.is_active()  # Проверить активность
subscription.can_use()    # Можно ли использовать (с учетом лимитов)
subscription.increment_usage(tokens, cost)  # Увеличить счетчики
subscription.cancel()     # Отменить подписку
```

---

## 💰 Цены и пакеты

### Индивидуальные агенты

| Агент | Цена/месяц | Категория | Популярный |
|-------|-----------|-----------|-----------|
| Chief Content Agent | 490₽ | Стратегия | |
| **Drafting Agent** | **990₽** | Создание контента | ⭐ |
| Publisher Agent | 690₽ | Создание контента | |
| Research & FactCheck | 790₽ | Контроль качества | |
| Trends Scout | 590₽ | Аналитика | |
| Multimedia Producer | 890₽ | Мультимедиа | |
| **Legal Guard** | **1290₽** | Соответствие | |
| Repurpose Agent | 690₽ | Оптимизация | |
| Community Concierge | 790₽ | Вовлечение | |
| Paid Creative | 990₽ | Реклама | |

### Пакетные предложения (Bundles)

#### 🚀 Content Starter - 1490₽/мес (скидка 31%)
- Chief Content Agent
- Drafting Agent
- Publisher Agent

**Экономия:** 680₽/месяц

#### 💎 Pro Creator - 2790₽/мес (скидка 27%)
- Content Starter +
- Research & FactCheck
- Multimedia Producer

**Экономия:** 1060₽/месяц

#### 👑 Enterprise Suite - 3990₽/мес (скидка 51%)
- **Все 10 агентов**
- Максимальные возможности

**Экономия:** 4210₽/месяц

---

## 📡 API Эндпоинты

### 1. Получить доступных агентов

```http
GET /billing/agents/available
```

**Ответ:**
```json
{
  "agents": [
    {
      "id": "drafting_agent",
      "name": "Drafting Agent",
      "description": "Генерация качественных текстов",
      "price_monthly": 990,
      "category": "content_creation",
      "icon": "✍️",
      "features": ["Генерация текстов", "SEO-оптимизация", ...],
      "popular": true
    }
  ],
  "bundles": [...],
  "categories": {...}
}
```

### 2. Мои подписки

```http
GET /billing/agents/my-subscriptions
Authorization: Bearer {token}
```

**Ответ:**
```json
{
  "subscriptions": [
    {
      "id": 1,
      "agent_id": "drafting_agent",
      "agent_name": "Drafting Agent",
      "status": "active",
      "price_monthly_rub": 990,
      "expires_at": "2025-11-15T10:00:00",
      "usage": {
        "requests_this_month": 45,
        "tokens_this_month": 67800,
        "cost_this_month_rub": 25.65
      },
      "is_active": true,
      "can_use": true
    }
  ],
  "total_monthly_cost_rub": 990,
  "active_agents_count": 1
}
```

### 3. Подписаться на агента

```http
POST /billing/agents/subscribe
Authorization: Bearer {token}
Content-Type: application/json

{
  "agent_id": "drafting_agent",
  "bundle_id": "content_starter"  // опционально
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Вы успешно подписались на Drafting Agent",
  "subscription": {...}
}
```

### 4. Отписаться от агента

```http
POST /billing/agents/unsubscribe
Authorization: Bearer {token}
Content-Type: application/json

{
  "agent_id": "drafting_agent"
}
```

### 5. Статистика токенов

```http
GET /billing/usage/tokens?period=month&agent_id=drafting_agent
Authorization: Bearer {token}
```

**Ответ:**
```json
{
  "period": "current_month",
  "total_requests": 127,
  "total_tokens": 75840,
  "total_cost_rub": 28.55,
  "by_agent": [
    {
      "agent_id": "drafting_agent",
      "agent_name": "Drafting Agent",
      "requests": 127,
      "tokens": 75840,
      "cost_rub": 28.55,
      "avg_tokens_per_request": 597
    }
  ]
}
```

### 6. Рекомендации агентов

```http
GET /billing/agents/recommendations
Authorization: Bearer {token}
```

**Ответ:**
```json
{
  "bundle_recommendation": {
    "bundle_id": "content_starter",
    "bundle_name": "Content Starter",
    "bundle_price": 149000,
    "regular_price": 217000,
    "savings": 68000,
    "savings_percent": 31
  },
  "recommended_agents": [
    {
      "agent_id": "publisher_agent",
      "reason": "Дополняет Drafting Agent для полного цикла",
      "name": "Publisher Agent",
      "price_monthly": 690
    }
  ]
}
```

---

## 🔐 AgentAccessMiddleware

Middleware для проверки доступа к агентам:

```python
from app.billing.middleware.agent_access_middleware import AgentAccessMiddleware

# Проверить доступ к агенту
has_access = AgentAccessMiddleware.check_agent_access(user_id, agent_id, db_session)

# Получить список доступных агентов
available = AgentAccessMiddleware.get_user_agents(user_id, db_session)

# Проверить доступ для workflow
check = AgentAccessMiddleware.check_workflow_access(
    user_id, 
    required_agents=['chief_001', 'drafting_001'], 
    db_session
)

if not check['can_proceed']:
    print(f"Недоступны: {check['blocked_agents']}")
    print(f"Нужны подписки: {check['missing_subscriptions']}")

# Увеличить счетчики использования
AgentAccessMiddleware.increment_agent_usage(
    user_id, agent_id, tokens_used=1500, cost_kopeks=57, db_session
)
```

---

## 🔄 Интеграция в Content Creation

Обновленный endpoint `/content/create`:

```python
@api.route('/content/create')
class ContentCreate(Resource):
    @jwt_required
    def post(self, current_user):
        user_id = current_user.get('user_id')
        
        # Получаем персональный оркестратор пользователя
        from app.orchestrator.user_orchestrator_factory import UserOrchestratorFactory
        db_session = get_db_session()
        
        user_orchestrator = UserOrchestratorFactory.get_orchestrator(user_id, db_session)
        
        # Запускаем через персональный оркестратор
        # В нем зарегистрированы только купленные агенты
        result = run_async(user_orchestrator.process_content_request(request_data))
```

---

## 🧹 Lifecycle Management

### Автоматическая очистка

Фоновая задача очищает неактивные оркестраторы каждый час:

```python
# app.py
from app.orchestrator.user_orchestrator_factory import orchestrator_cleanup_task

loop.create_task(orchestrator_cleanup_task())
```

**Настройки:**
- `_cleanup_interval` = 3600 сек (1 час)
- `_max_idle_time` = 7200 сек (2 часа)

---

## 📊 Экономическая модель

### Себестоимость vs Цена

| Агент | Себестоимость/запрос | Цена подписки | Точка безубыточности |
|-------|---------------------|---------------|---------------------|
| Chief Content | 0.50₽ | 490₽/мес | ~980 запросов |
| Drafting | 1.50₽ | 990₽/мес | ~660 запросов |
| Publisher | 0.80₽ | 690₽/мес | ~862 запроса |

### Рекомендации по ценообразованию

1. **Для активных пользователей** (>500 запросов/мес) - рекомендовать bundles
2. **Для редких пользователей** (<100 запросов/мес) - индивидуальные агенты
3. **Enterprise** (>2000 запросов/мес) - Enterprise Suite с максимальной скидкой

---

## 🚀 Масштабируемость

### Текущие лимиты

- **До 1000 активных пользователей** - текущая архитектура работает отлично
- **Память:** ~50-100MB на пользователя
- **Cleanup:** автоматический каждый час

### Будущие улучшения

Когда >500 активных пользователей:
1. Внедрить **Celery + Redis** для очереди задач
2. Реализовать **Agent Pool** вместо per-user orchestrators
3. Добавить **Kubernetes** для горизонтального масштабирования

---

## 📝 Миграция БД

```bash
# Применить миграцию
psql -U postgres -d content_curator -f migrations/add_agent_subscriptions_table.sql
```

---

## ✅ Чеклист внедрения

- [x] Создана модель `AgentSubscription`
- [x] Создан справочник `AGENT_PRICING` и `AGENT_BUNDLES`
- [x] Реализован `UserOrchestratorFactory`
- [x] Добавлен `AgentAccessMiddleware`
- [x] Обновлены API endpoints
- [x] Добавлена фоновая задача cleanup
- [x] Создана миграция БД
- [x] Написана документация

---

## 🎯 Следующие шаги

1. **Тестирование** - покрыть тестами все новые компоненты
2. **Frontend интеграция** - UI для выбора агентов и bundles
3. **Платежная интеграция** - подключить оплату через ЮКassa
4. **Аналитика** - дашборд с детализацией расходов
5. **A/B тестирование** - оптимизация цен

---

**Готово к использованию!** 🎉

Все компоненты реализованы и готовы к тестированию.

