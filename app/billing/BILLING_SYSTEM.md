# Billing System - Система платежей и подписок

## 📋 Обзор

Система billing для AI Content Orchestrator обеспечивает:
- Интеграцию с ЮКассой для обработки платежей
- Управление подписками и тарифными планами
- Отслеживание использования ресурсов
- Автоматическое управление доступом к функциям

## 🏗️ Архитектура

```
app/billing/
├── models/                 # Модели данных
│   └── subscription.py     # Модели подписок, платежей, использования
├── services/               # Бизнес-логика
│   ├── yookassa_service.py # Интеграция с ЮКассой
│   └── subscription_service.py # Управление подписками
├── api/                    # API endpoints
│   └── billing_routes.py   # REST API для billing
├── webhooks/               # Обработчики webhook
│   └── yookassa_webhook.py # Webhook от ЮКассы
├── middleware/             # Middleware
│   └── usage_middleware.py # Проверка лимитов
├── config.py              # Конфигурация
└── example.py             # Примеры использования
```

## 💰 Тарифные планы

### Free Plan
- **Цена**: Бесплатно
- **Лимиты**:
  - 50 постов в месяц
  - 3 AI агента
  - Telegram и VK платформы
  - 100 API вызовов в день
  - 1 GB хранилища
- **Поддержка**: Сообщество
- **Пробный период**: 7 дней

### Pro Plan
- **Цена**: 2990₽/месяц, 29900₽/год
- **Лимиты**:
  - Неограниченные посты
  - Все 10 AI агентов
  - Все платформы
  - 10,000 API вызовов в день
  - 100 GB хранилища
- **Поддержка**: Приоритетная
- **Пробный период**: 14 дней

### Enterprise Plan
- **Цена**: Договорная
- **Лимиты**:
  - Неограниченные ресурсы
  - Белый лейбл
  - Выделенная поддержка 24/7
  - Кастомные интеграции
- **Поддержка**: Выделенная
- **Пробный период**: 30 дней

## 🔧 Настройка

### Переменные окружения

```bash
# ЮКасса настройки
YOOKASSA_SHOP_ID=1134145
YOOKASSA_SECRET_KEY=live_144m9a57yZytkuyh90IAiM0sQoF-L3SAyfB4hZMSDFk
YOOKASSA_WEBHOOK_SECRET=your_webhook_secret_here
YOOKASSA_TEST_MODE=false

# URL для возврата
YOOKASSA_RETURN_URL=https://content-curator-1046574462613.us-central1.run.app/billing/success
YOOKASSA_CANCEL_URL=https://content-curator-1046574462613.us-central1.run.app/billing/cancel

# Настройки billing
BILLING_DEFAULT_TRIAL_DAYS=7
BILLING_AUTO_RENEW_ENABLED=true
BILLING_NOTIFICATIONS_ENABLED=true
BILLING_WEBHOOK_SIGNATURE_REQUIRED=true
BILLING_PAYMENT_TIMEOUT_MINUTES=30
```

### Инициализация в app.py

```python
from app.billing.api.billing_routes import billing_bp
from app.billing.webhooks.yookassa_webhook import webhook_bp
from app.billing.middleware.usage_middleware import UsageMiddleware

# Регистрация Blueprint
app.register_blueprint(billing_bp)
app.register_blueprint(webhook_bp)

# Инициализация middleware
billing_middleware = UsageMiddleware(app)
```

## 📡 API Endpoints

### Тарифные планы

```http
GET /api/v1/billing/plans
```

Возвращает все доступные тарифные планы.

```http
GET /api/v1/billing/plans/{plan_id}
```

Возвращает конкретный тарифный план.

### Подписки

```http
GET /api/v1/billing/subscription
```

Получить подписку пользователя.

```http
POST /api/v1/billing/subscription
Content-Type: application/json

{
  "plan_id": "pro",
  "billing_period": "monthly"
}
```

Создать подписку.

```http
POST /api/v1/billing/subscription/{subscription_id}/cancel
Content-Type: application/json

{
  "reason": "user_request"
}
```

Отменить подписку.

### Использование

```http
GET /api/v1/billing/usage
```

Получить статистику использования.

### Платежи

```http
GET /api/v1/billing/payment-methods
```

Получить доступные способы оплаты.

```http
GET /api/v1/billing/payment/{payment_id}
```

Получить статус платежа.

### События

```http
GET /api/v1/billing/events?limit=50&offset=0
```

Получить события billing системы.

## 🔗 Webhook

### Настройка webhook в ЮКассе

URL: `https://content-curator-1046574462613.us-central1.run.app/webhook/yookassa`

События:
- `payment.succeeded` - Успешный платеж
- `payment.canceled` - Отмененный платеж
- `refund.succeeded` - Успешный возврат

### Обработка webhook

```python
@webhook_bp.route('/yookassa', methods=['POST'])
def yookassa_webhook():
    # Проверка подписи
    # Парсинг события
    # Обработка платежа
    # Обновление подписки
```

## 🛡️ Middleware для проверки лимитов

### Декораторы

```python
from app.billing.middleware.usage_middleware import check_usage_limit, require_plan

@check_usage_limit("posts", quantity=1)
def create_post():
    # Создание поста
    pass

@require_plan("pro")
def advanced_feature():
    # Продвинутая функция
    pass
```

### Проверка лимитов

```python
from app.billing.middleware.usage_middleware import get_user_limits

limits = get_user_limits(user_id)
if limits:
    print(f"Использовано постов: {limits['usage']['posts_used']}/{limits['limits']['posts_per_month']}")
```

## 📊 Модели данных

### Subscription

```python
class Subscription(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    plan_id = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=True)
```

### Payment

```python
class Payment(Base):
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    yookassa_payment_id = Column(String(255), unique=True)
    amount = Column(Integer, nullable=False)  # в копейках
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### UsageRecord

```python
class UsageRecord(Base):
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    user_id = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
```

## 🔄 Жизненный цикл подписки

1. **Создание подписки**
   - Пользователь выбирает план
   - Создается платеж в ЮКассе
   - Пользователь оплачивает

2. **Активация подписки**
   - Webhook от ЮКассы о успешном платеже
   - Создается активная подписка
   - Пользователь получает доступ к функциям

3. **Использование**
   - Отслеживание использования ресурсов
   - Проверка лимитов при каждом действии
   - Запись статистики

4. **Продление**
   - Автоматическое продление (если включено)
   - Создание нового платежа
   - Обновление даты окончания

5. **Отмена**
   - Пользователь отменяет подписку
   - Подписка остается активной до окончания периода
   - Автопродление отключается

## 🚀 Развертывание

### 1. Установка зависимостей

```bash
pip install -r requirements_billing.txt
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
# Отредактировать .env файл
```

### 3. Настройка webhook в ЮКассе

1. Войти в личный кабинет ЮКассы
2. Перейти в раздел "Настройки" → "Webhook"
3. Добавить URL: `https://content-curator-1046574462613.us-central1.run.app/webhook/yookassa`
4. Выбрать события: `payment.succeeded`, `payment.canceled`, `refund.succeeded`

### 4. Тестирование

```bash
python app/billing/example.py
```

## 🔍 Мониторинг и логирование

### Логирование

```python
import logging
logger = logging.getLogger(__name__)

# Логирование платежей
logger.info(f"Создан платеж {payment_id} для пользователя {user_id}")

# Логирование webhook
logger.info(f"Получен webhook от ЮКассы: {event_type}")
```

### Мониторинг

- Отслеживание успешности платежей
- Мониторинг webhook событий
- Статистика использования ресурсов
- Алерты при превышении лимитов

## 🛠️ Разработка

### Добавление нового тарифного плана

```python
# В app/billing/models/subscription.py
PLANS["new_plan"] = SubscriptionPlan(
    id="new_plan",
    name="New Plan",
    description="Описание нового плана",
    price_monthly=500000,  # 5000₽
    price_yearly=5000000,  # 50000₽
    plan_type=PlanType.PRO,
    limits=PlanLimits(
        posts_per_month=1000,
        max_agents=5,
        platforms=["telegram", "vk", "facebook"],
        api_calls_per_day=5000,
        storage_gb=50,
        support_level="priority"
    ),
    features=["Новая функция 1", "Новая функция 2"]
)
```

### Добавление нового типа ресурса

```python
# В middleware/usage_middleware.py
def check_usage_limit(resource_type: str, quantity: int = 1):
    # Добавить проверку для нового типа ресурса
    if resource_type == "new_resource":
        return usage_stats.new_resource_used + quantity <= usage_stats.new_resource_limit
```

## 🔒 Безопасность

### Проверка подписи webhook

```python
def verify_webhook(self, request_body: str, signature: str) -> bool:
    expected_signature = hmac.new(
        self.webhook_secret.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

### Валидация данных

- Проверка всех входящих данных
- Валидация сумм платежей
- Проверка прав доступа
- Логирование всех операций

## 📈 Аналитика

### Метрики

- Конверсия в платные планы
- Средний чек
- Retention rate
- Использование ресурсов по планам

### Отчеты

- Финансовые отчеты
- Статистика использования
- Анализ отмен подписок
- Эффективность тарифных планов

## 🆘 Поддержка

### Частые проблемы

1. **Webhook не приходят**
   - Проверить URL webhook
   - Проверить доступность сервера
   - Проверить логи

2. **Платежи не обрабатываются**
   - Проверить настройки ЮКассы
   - Проверить подпись webhook
   - Проверить логи обработки

3. **Лимиты не работают**
   - Проверить middleware
   - Проверить записи использования
   - Проверить конфигурацию планов

### Контакты

- Техническая поддержка: support@your-domain.com
- Документация: https://docs.your-domain.com/billing
- GitHub Issues: https://github.com/your-repo/issues
