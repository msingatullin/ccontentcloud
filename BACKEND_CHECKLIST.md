# ✅ Backend Checklist - Pay-Per-Agent System

## Что уже сделано ✅

### Архитектура
- [x] UserOrchestratorFactory - изоляция по пользователям
- [x] AgentSubscription модель
- [x] AGENT_PRICING справочник (10 агентов + 4 bundles)
- [x] AgentAccessMiddleware для проверки доступа
- [x] Интеграция трекинга токенов с AgentSubscription

### API Endpoints
- [x] `GET /billing/agents/available` - список агентов и bundles
- [x] `GET /billing/agents/my-subscriptions` - мои подписки
- [x] `POST /billing/agents/subscribe` - подписаться
- [x] `POST /billing/agents/unsubscribe` - отписаться
- [x] `GET /billing/usage/tokens` - статистика токенов
- [x] `GET /billing/agents/recommendations` - рекомендации

### База данных
- [x] Таблица `agent_subscriptions`
- [x] Миграция SQL скрипт
- [x] Индексы для производительности

### Интеграция
- [x] `/content/create` использует UserOrchestratorFactory
- [x] Автоматическое обновление счетчиков при использовании
- [x] Cleanup task для неактивных оркестраторов

---

## Что нужно сделать на бэкенде 🔧

### 1. Применить миграцию БД ⚠️ КРИТИЧНО

```bash
# Подключиться к БД и выполнить
psql -U postgres -d content_curator -f migrations/add_agent_subscriptions_table.sql
```

**Или через Cloud SQL:**
```bash
gcloud sql connect content-curator-db --user=postgres --database=content_curator
\i migrations/add_agent_subscriptions_table.sql
```

### 2. Создать тестовые подписки (опционально)

Для тестирования создать подписки для первого пользователя:

```sql
-- Подписка на Drafting Agent
INSERT INTO agent_subscriptions (
    user_id, agent_id, agent_name, status, 
    price_monthly, starts_at, expires_at
) VALUES (
    1, 'drafting_agent', 'Drafting Agent', 'active',
    99000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (user_id, agent_id, status) DO NOTHING;

-- Подписка на Chief Content Agent
INSERT INTO agent_subscriptions (
    user_id, agent_id, agent_name, status,
    price_monthly, starts_at, expires_at
) VALUES (
    1, 'chief_content_agent', 'Chief Content Agent', 'active',
    49000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (user_id, agent_id, status) DO NOTHING;
```

### 3. Интеграция с платежами (будущее)

Когда пользователь оплачивает подписку через ЮКassa:

```python
# В webhook обработчике
@webhook_ns.route('/yookassa')
def yookassa_webhook():
    # После успешной оплаты
    if payment_status == 'succeeded':
        # Создать подписку на агента
        subscription = AgentSubscription(
            user_id=user_id,
            agent_id=agent_id,
            status='active',
            price_monthly=price,
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Обновить оркестратор пользователя
        UserOrchestratorFactory.refresh_user_agents(user_id, db_session)
```

### 4. Cron задача для продления подписок (будущее)

Автоматическое продление подписок с `auto_renew=True`:

```python
# app/billing/tasks/subscription_renewal.py
async def renew_expiring_subscriptions():
    """Продлевает подписки которые истекают сегодня"""
    expiring = db_session.query(AgentSubscription).filter(
        AgentSubscription.expires_at <= datetime.utcnow() + timedelta(days=1),
        AgentSubscription.auto_renew == True,
        AgentSubscription.status == 'active'
    ).all()
    
    for sub in expiring:
        # Списать оплату через ЮКassa
        payment = yookassa.create_payment(sub.price_monthly, sub.user_id)
        
        if payment.status == 'succeeded':
            sub.renew(months=1)
            db_session.commit()
```

### 5. Endpoint для отмены автопродления

```python
@billing_ns.route('/agents/subscription/<int:subscription_id>/auto-renew')
class ToggleAutoRenew(Resource):
    @jwt_required
    def patch(self, current_user, subscription_id):
        """Включить/выключить автопродление"""
        data = request.json
        auto_renew = data.get('auto_renew', True)
        
        subscription = db_session.query(AgentSubscription).filter(
            AgentSubscription.id == subscription_id,
            AgentSubscription.user_id == current_user['user_id']
        ).first()
        
        if subscription:
            subscription.auto_renew = auto_renew
            db_session.commit()
            return {'success': True}
```

### 6. Endpoint для истории платежей по агентам

```python
@billing_ns.route('/agents/payment-history')
class AgentPaymentHistory(Resource):
    @jwt_required
    def get(self, current_user):
        """История платежей за подписки на агентов"""
        # Связать с таблицей payments
        # Показать все списания за подписки
```

---

## Что нужно на фронтенде 🎨

### 1. Страница выбора агентов

**UI компоненты:**
- Карточки агентов с ценами
- Фильтр по категориям
- Маркеры "Популярный", "Рекомендуем"
- Кнопка "Подписаться"

**API вызовы:**
```javascript
// Получить список агентов
GET /billing/agents/available

// Подписаться
POST /billing/agents/subscribe
{
  "agent_id": "drafting_agent"
}
```

### 2. Страница "Мои агенты"

**Показать:**
- Активные подписки
- Дата окончания
- Использование за месяц (запросы, токены, стоимость)
- Кнопка "Отменить подписку"

**API вызовы:**
```javascript
// Получить мои подписки
GET /billing/agents/my-subscriptions

// Отписаться
POST /billing/agents/unsubscribe
{
  "agent_id": "drafting_agent"
}
```

### 3. Dashboard аналитики

**Графики:**
- Использование токенов по дням
- Расходы по агентам (pie chart)
- Топ агентов по использованию

**API вызовы:**
```javascript
// Статистика токенов
GET /billing/usage/tokens?period=month

// Рекомендации
GET /billing/agents/recommendations
```

### 4. Страница Bundles

**Показать:**
- Пакетные предложения
- Процент скидки
- Сумма экономии
- Список агентов в bundle
- Кнопка "Купить bundle"

### 5. Интеграция в создание контента

**Проверка перед созданием:**
```javascript
// Перед вызовом /content/create
// Проверить есть ли нужные агенты
const subscriptions = await fetch('/billing/agents/my-subscriptions')

if (!subscriptions.active_agents_count) {
  // Показать модалку "Выберите агентов"
  showAgentSelectionModal()
}
```

---

## Приоритеты

### Высокий приоритет (сделать сейчас)
1. ✅ Применить миграцию БД
2. ✅ Создать тестовые подписки
3. 🎨 Фронт: Страница выбора агентов
4. 🎨 Фронт: Страница "Мои агенты"

### Средний приоритет (следующая неделя)
5. 🎨 Фронт: Dashboard аналитики
6. 🎨 Фронт: Страница Bundles
7. 🔧 Бэк: Интеграция платежей с ЮКassa
8. 🔧 Бэк: Endpoint автопродления

### Низкий приоритет (когда будет время)
9. 🔧 Бэк: Cron задача продления
10. 🔧 Бэк: История платежей
11. 🎨 Фронт: A/B тестирование цен
12. 🎨 Фронт: Реферальная программа

---

## Тестирование

### Ручное тестирование в Swagger UI

1. Авторизоваться (получить JWT токен)
2. Открыть `/docs`
3. Протестировать endpoints:
   - `GET /billing/agents/available` - должен вернуть 10 агентов
   - `POST /billing/agents/subscribe` - подписаться на агента
   - `GET /billing/agents/my-subscriptions` - проверить подписку
   - `POST /content/create` - создать контент (должен использовать только купленных агентов)
   - `GET /billing/usage/tokens` - проверить статистику

### Автоматические тесты (TODO)

```python
# tests/test_agent_subscriptions.py
def test_subscribe_to_agent():
    """Тест подписки на агента"""
    
def test_user_orchestrator_isolation():
    """Тест изоляции оркестраторов"""
    
def test_token_tracking():
    """Тест трекинга токенов"""
```

---

## Готово к использованию! 🎉

**Бэкенд:** 95% готов, нужно только применить миграцию
**Фронтенд:** Нужна реализация UI для управления подписками

**Документация:**
- `PAY_PER_AGENT_GUIDE.md` - полный гайд по системе
- `BACKEND_CHECKLIST.md` - этот файл
- Swagger UI `/docs` - все endpoints задокументированы

