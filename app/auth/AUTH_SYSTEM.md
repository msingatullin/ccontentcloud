# Система аутентификации пользователей

## 📋 Обзор

Полноценная система аутентификации с JWT токенами, email верификацией, управлением сессиями и интеграцией с billing системой.

## 🏗️ Архитектура

### Структура модулей
```
app/auth/
├── models/
│   └── user.py              # Модели User и UserSession
├── services/
│   └── auth_service.py      # Бизнес-логика аутентификации
├── routes/
│   └── auth.py              # API endpoints
├── middleware/
│   └── jwt.py               # JWT middleware и декораторы
├── utils/
│   └── email.py             # Email сервис
└── example.py               # Примеры использования
```

### Основные компоненты

**1. User Model**
- Полная информация о пользователе
- Связи с Subscription и UsageRecord
- Методы для работы с паролями и токенами
- Статистика использования

**2. AuthService**
- Регистрация и авторизация
- Управление JWT токенами
- Email верификация
- Сброс паролей
- Управление сессиями

**3. JWTMiddleware**
- Защита маршрутов
- Проверка токенов
- Управление ролями
- Rate limiting

**4. EmailService**
- Отправка уведомлений
- HTML и текстовые шаблоны
- Настраиваемые SMTP

## 🔐 Безопасность

### JWT Токены
- **Access Token**: 30 минут, для API запросов
- **Refresh Token**: 30 дней, для обновления access token
- **JTI (JWT ID)**: Уникальный идентификатор для отзыва токенов

### Пароли
- Хеширование с Werkzeug
- Минимум 8 символов
- Автоматическая деактивация сессий при смене пароля

### Email Верификация
- Токены действительны 24 часа
- Автоматическая отправка при регистрации
- Повторная отправка по запросу

### Сессии
- Отслеживание устройств и IP
- Возможность отзыва отдельных сессий
- Автоматическое истечение

## 📊 Модели данных

### User
```python
class User(Base):
    # Основные поля
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Персональная информация
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    company = Column(String(200))
    position = Column(String(100))
    
    # Статус и роли
    role = Column(Enum(UserRole), default=UserRole.USER)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Email верификация
    email_verification_token = Column(String(255))
    email_verification_expires = Column(DateTime)
    
    # Сброс пароля
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Настройки
    timezone = Column(String(50), default='Europe/Moscow')
    language = Column(String(10), default='ru')
    notifications_enabled = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
```

### UserSession
```python
class UserSession(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    token_jti = Column(String(255), unique=True)  # JWT ID
    refresh_token = Column(String(255), unique=True)
    device_info = Column(Text)  # JSON с информацией об устройстве
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
```

## 🚀 API Endpoints

### Регистрация и авторизация
```http
POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/logout-all
```

### Email верификация
```http
POST /auth/verify-email
POST /auth/resend-verification
```

### Сброс пароля
```http
POST /auth/forgot-password
POST /auth/reset-password
```

### Управление профилем
```http
GET /auth/me
PUT /auth/profile
POST /auth/change-password
```

### Управление сессиями
```http
GET /auth/sessions
DELETE /auth/sessions/{session_id}
```

### Обновление токенов
```http
POST /auth/refresh
```

## 🔧 Конфигурация

### Переменные окружения
```bash
# JWT Secret Key (обязательно)
SECRET_KEY=your-super-secret-jwt-key-here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Email Settings
FROM_EMAIL=noreply@goinvesting.ai
FROM_NAME=AI Content Orchestrator
BASE_URL=https://goinvesting.ai

# Security Settings
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

### Инициализация в app.py
```python
from app.auth.routes.auth import init_auth_routes

# Инициализация auth системы
auth_bp, jwt_middleware = init_auth_routes(db_session, app.config['SECRET_KEY'])

# Регистрация blueprint
app.register_blueprint(auth_bp)
```

## 🛡️ Middleware и декораторы

### Основные декораторы
```python
from app.auth.middleware.jwt import JWTMiddleware

jwt_middleware = JWTMiddleware(auth_service)

# Требует аутентификации
@jwt_middleware.require_auth
def protected_route():
    pass

# Требует подтвержденный email
@jwt_middleware.require_verified_email
def verified_route():
    pass

# Требует админские права
@jwt_middleware.require_admin
def admin_route():
    pass

# Требует права модератора
@jwt_middleware.require_moderator
def moderator_route():
    pass

# Опциональная аутентификация
@jwt_middleware.optional_auth
def optional_route():
    pass
```

### Проверка в коде
```python
from app.auth.middleware.jwt import get_current_user, is_authenticated, is_admin

# Получение текущего пользователя
user = get_current_user()

# Проверка аутентификации
if is_authenticated():
    # Пользователь аутентифицирован

# Проверка роли
if is_admin():
    # Пользователь - администратор
```

## 📧 Email уведомления

### Типы писем
- **Верификация email**: Подтверждение регистрации
- **Сброс пароля**: Инструкции по восстановлению
- **Приветственное письмо**: После подтверждения email
- **Подтверждение подписки**: Активация тарифа
- **Подтверждение платежа**: Успешная оплата

### Настройка SMTP
```python
# Gmail пример
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # App Password, не обычный пароль
```

### HTML шаблоны
Все письма имеют HTML и текстовую версии с:
- Адаптивным дизайном
- Брендингом AI Content Orchestrator
- Кнопками действий
- Информацией о безопасности

## 🔗 Интеграция с billing

### Связи с подписками
```python
# Получение активной подписки
user = get_current_user()
active_subscription = user.get_active_subscription()

# Проверка доступа к функции
if user.can_access_feature('premium_analytics'):
    # Пользователь имеет доступ
```

### Статистика использования
```python
# Получение статистики
usage_stats = user.get_usage_stats()
# {
#     'posts_used': 15,
#     'api_calls_used': 1200,
#     'subscription_plan': 'pro',
#     'subscription_status': 'active'
# }
```

## 🧪 Тестирование

### Запуск примеров
```bash
cd app/auth
python example.py
```

### Тестовые сценарии
1. **Регистрация пользователя**
2. **Авторизация с валидацией**
3. **Верификация JWT токенов**
4. **Сброс пароля**
5. **Обновление профиля**
6. **Управление ролями**

### Тестовые данные
```python
# Тестовый пользователь
email = "test@example.com"
password = "testpassword123"
username = "testuser"
```

## 📈 Мониторинг и логирование

### Логируемые события
- Регистрация пользователей
- Успешные/неуспешные входы
- Смена паролей
- Отзыв токенов
- Ошибки аутентификации

### Метрики
- Количество активных пользователей
- Частота входов
- Использование функций
- Ошибки аутентификации

## 🔄 Миграции базы данных

### Создание таблиц
```python
from app.auth.models.user import Base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///auth.db')
Base.metadata.create_all(engine)
```

### Обновление схемы
При изменении моделей необходимо создать миграции для обновления существующих таблиц.

## 🚨 Безопасность в продакшне

### Обязательные настройки
1. **SECRET_KEY**: Должен быть сложным и уникальным
2. **HTTPS**: Все соединения должны быть зашифрованы
3. **SMTP**: Использовать App Passwords для Gmail
4. **Rate Limiting**: Ограничить количество запросов
5. **Логирование**: Мониторить подозрительную активность

### Рекомендации
- Регулярно обновлять SECRET_KEY
- Мониторить неудачные попытки входа
- Использовать CORS для ограничения доменов
- Настроить автоматическое удаление истекших сессий

## 📚 Примеры использования

### Frontend интеграция
```javascript
// Регистрация
const response = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123',
        username: 'username'
    })
});

// Авторизация
const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
});

const { access_token, refresh_token } = await response.json();

// Использование токена
const apiResponse = await fetch('/api/v1/protected', {
    headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### Backend интеграция
```python
from app.auth.middleware.jwt import get_current_user, require_auth_response

@app.route('/api/v1/protected')
@jwt_middleware.require_auth
def protected_endpoint():
    user = get_current_user()
    return jsonify({
        'message': f'Привет, {user.get_display_name()}!',
        'user_id': user.id
    })
```

---

## ✅ Готово к использованию!

Система аутентификации полностью готова с:
- ✅ JWT токены и middleware
- ✅ Email верификация
- ✅ Управление сессиями
- ✅ Сброс паролей
- ✅ Роли и права доступа
- ✅ Интеграция с billing
- ✅ Безопасность и логирование
- ✅ API endpoints
- ✅ Документация и примеры

**URL**: `/auth/*`
