# 📱 Подключение социальных сетей - Полная инструкция

Полное руководство по подключению Instagram, Twitter и Telegram для автоматической публикации контента.

---

## 📋 Содержание

1. [Instagram](#instagram-integration)
2. [Twitter](#twitter-integration)
3. [Telegram](#telegram-integration)
4. [Безопасность](#security)
5. [Технические детали](#technical-details)

---

## 📸 Instagram Integration

### Метод авторизации
Instagram использует **login/password** авторизацию через библиотеку `instagrapi`.

### ⚠️ ВАЖНЫЕ ТРЕБОВАНИЯ

#### 1. Отключение двухфакторной аутентификации (2FA)
```
❌ 2FA ДОЛЖНА БЫТЬ ОТКЛЮЧЕНА
```

**Как отключить 2FA:**
1. Откройте Instagram приложение
2. Профиль → Настройки → Безопасность
3. Двухфакторная аутентификация → **Выключить**

#### 2. Создание пароля (если входите через Facebook/Google)
Если вы входите в Instagram через Facebook или Google:
1. Instagram → Настройки → Безопасность
2. Пароль → **Создать пароль**

#### 3. Возраст аккаунта
- Рекомендуется использовать аккаунты старше **3 месяцев**
- Новые аккаунты могут быть заблокированы Instagram за подозрительную активность

### 🔒 Безопасность данных

- Пароль шифруется алгоритмом **Fernet** (AES 128-bit)
- Хранится в БД только в зашифрованном виде
- Сессия Instagram сохраняется для избежания повторных входов

### 📊 Лимиты публикации

Instagram имеет строгие лимиты для защиты от спама:

| Параметр | Значение |
|----------|----------|
| Посты в день | **10** (настраиваемо) |
| Минимальная задержка | 1-3 секунды между действиями |
| Формат изображения | JPG, PNG |
| Размер изображения | Рекомендуется 1080x1080px |

### 🛠️ API Endpoints

#### 1. Получить информацию
```http
GET /api/instagram/info
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "info": {
    "title": "Подключение Instagram",
    "requirements": [
      "Отключите двухфакторную аутентификацию (2FA)",
      "Используйте логин и пароль от Instagram",
      "Аккаунт должен быть старше 3 месяцев для стабильной работы"
    ],
    "limits": {
      "daily_posts": 10
    }
  }
}
```

#### 2. Добавить аккаунт
```http
POST /api/instagram/accounts
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "username": "your_instagram_username",
  "password": "your_instagram_password",
  "account_name": "Мой Instagram"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Instagram аккаунт успешно добавлен",
  "account": {
    "id": 1,
    "instagram_username": "your_username",
    "account_name": "Мой Instagram",
    "is_active": true,
    "is_verified": true,
    "is_default": true
  }
}
```

**Error Responses:**
```json
{
  "success": false,
  "error": "❌ Двухфакторная аутентификация (2FA) включена.\n\nОтключите 2FA в настройках Instagram"
}
```

```json
{
  "success": false,
  "error": "❌ Instagram требует дополнительную верификацию.\n\nВойдите в свой аккаунт через приложение Instagram и подтвердите, что это вы."
}
```

```json
{
  "success": false,
  "error": "❌ Неверный логин или пароль"
}
```

#### 3. Список аккаунтов
```http
GET /api/instagram/accounts?active_only=true
Authorization: Bearer {jwt_token}
```

#### 4. Установить дефолтный аккаунт
```http
PUT /api/instagram/accounts/{account_id}/default
Authorization: Bearer {jwt_token}
```

#### 5. Удалить аккаунт
```http
DELETE /api/instagram/accounts/{account_id}
Authorization: Bearer {jwt_token}
```

### 📝 Пример публикации

Через PublisherAgent:
```python
task = Task(
    id="publish_instagram_1",
    name="Publish to Instagram",
    task_type=TaskType.PLANNED,
    priority=TaskPriority.NORMAL,
    context={
        "content": {
            "title": "Мой пост",
            "text": "Текст поста",
            "hashtags": ["content4u", "ai", "automation"],
            "images": ["/path/to/image.jpg"]  # ОБЯЗАТЕЛЬНО
        },
        "platform": "instagram",
        "user_id": 1,  # ID пользователя
        "account_id": 1,  # ID Instagram аккаунта (опционально, по умолчанию используется дефолтный)
        "test_mode": False
    }
)

result = await publisher_agent.execute_task(task)
```

---

## 🐦 Twitter Integration

### Метод авторизации
Twitter использует **OAuth 1.0a** авторизацию через библиотеку `tweepy`.

### 🔑 Настройка Twitter Developer App

#### 1. Создайте приложение
1. Перейдите на https://developer.twitter.com/en/portal/dashboard
2. Создайте новый проект (Project)
3. Создайте новое приложение (App)

#### 2. Настройте права доступа
В настройках приложения:
- **App permissions**: `Read and Write`
- **Type of App**: `Web App`
- **Callback URLs**: `https://your-domain.com/api/twitter/oauth/callback`

#### 3. Получите ключи
В разделе "Keys and tokens":
- **API Key** (Consumer Key)
- **API Secret Key** (Consumer Secret)

Добавьте в `.env`:
```bash
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
```

### 🔒 Безопасность данных

- OAuth токены шифруются алгоритмом **Fernet** (AES 128-bit)
- Хранятся в БД только в зашифрованном виде
- Пользователь может отозвать доступ в любой момент в настройках Twitter

### 📊 Лимиты публикации

| Параметр | Значение |
|----------|----------|
| Длина твита | **280 символов** |
| Изображений в твите | До **4 шт** |
| Видео в твите | **1 шт** |
| Твитов в день | ~300 (Twitter API v2) |

### 🛠️ API Endpoints

#### 1. Получить информацию
```http
GET /api/twitter/info
Authorization: Bearer {jwt_token}
```

#### 2. Получить OAuth URL (шаг 1)
```http
GET /api/twitter/oauth/url?callback_url=https://your-app.com/callback
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "auth_url": "https://api.twitter.com/oauth/authorize?oauth_token=...",
  "oauth_token": "abc123...",
  "oauth_token_secret": "xyz789...",
  "message": "Сохраните oauth_token_secret и передайте в callback"
}
```

**Frontend процесс:**
1. Сохраните `oauth_token_secret` в localStorage
2. Перенаправьте пользователя на `auth_url`
3. Twitter вернет пользователя на callback_url с параметрами `oauth_token` и `oauth_verifier`

#### 3. Завершить OAuth (шаг 2)
```http
POST /api/twitter/oauth/callback?oauth_token={token}&oauth_verifier={verifier}
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "oauth_token_secret": "xyz789...",  // Из шага 1
  "account_name": "Мой Twitter"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Twitter аккаунт успешно подключен",
  "account": {
    "id": 1,
    "twitter_username": "username",
    "twitter_display_name": "Display Name",
    "followers_count": 1234,
    "is_default": true
  }
}
```

#### 4. Список аккаунтов
```http
GET /api/twitter/accounts?active_only=true
Authorization: Bearer {jwt_token}
```

#### 5. Установить дефолтный
```http
PUT /api/twitter/accounts/{account_id}/default
Authorization: Bearer {jwt_token}
```

#### 6. Удалить аккаунт
```http
DELETE /api/twitter/accounts/{account_id}
Authorization: Bearer {jwt_token}
```

### 📝 Пример публикации

Через PublisherAgent:
```python
task = Task(
    id="publish_twitter_1",
    name="Publish to Twitter",
    task_type=TaskType.PLANNED,
    priority=TaskPriority.NORMAL,
    context={
        "content": {
            "title": "Мой твит",
            "text": "Текст твита (до 280 символов)",
            "images": ["/path/to/image1.jpg", "/path/to/image2.jpg"]  # До 4 изображений
        },
        "platform": "twitter",
        "user_id": 1,
        "account_id": 1,  # Опционально
        "test_mode": False
    }
)

result = await publisher_agent.execute_task(task)
```

---

## 📱 Telegram Integration

См. подробную инструкцию в [TELEGRAM_CHANNELS_SETUP.md](TELEGRAM_CHANNELS_SETUP.md)

**Краткая информация:**
- Один бот (@content4ubot) для всех клиентов
- Клиенты добавляют бота в свои каналы как администратора
- Бот публикует контент в каналы клиентов

**API:**
- `GET /api/telegram/bot-info`
- `POST /api/telegram/channels`
- `GET /api/telegram/channels`
- `PUT /api/telegram/channels/{id}/default`
- `DELETE /api/telegram/channels/{id}`

---

## 🔐 Security

### Шифрование данных

Все чувствительные данные шифруются с помощью **Fernet (AES 128-bit)**:

| Данные | Способ хранения |
|--------|-----------------|
| Instagram пароли | Зашифрованы |
| Twitter OAuth токены | Зашифрованы |
| Instagram сессии | Зашифрованы |
| Telegram Bot Token | Environment variable |

### Генерация ключа шифрования

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Добавьте в `.env`:**
```bash
SOCIAL_TOKENS_ENCRYPTION_KEY=your_generated_key_here
```

⚠️ **ВАЖНО:** НЕ МЕНЯЙТЕ КЛЮЧ после начала использования - все зашифрованные данные станут недоступны!

### Рекомендации по безопасности

1. **Используйте HTTPS** для всех API запросов
2. **JWT токены** имеют ограниченное время жизни
3. **Rate limiting** на все endpoints
4. **Валидация** всех входных данных
5. **Логирование** всех операций с социальными сетями (без секретов)

---

## 🛠️ Technical Details

### База данных

#### Instagram Accounts
```sql
CREATE TABLE instagram_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    instagram_username VARCHAR(255),
    encrypted_password TEXT,
    account_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    daily_posts_limit INTEGER DEFAULT 10,
    posts_today INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Twitter Accounts
```sql
CREATE TABLE twitter_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    encrypted_access_token TEXT,
    encrypted_access_token_secret TEXT,
    twitter_user_id VARCHAR(255),
    twitter_username VARCHAR(255),
    account_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Применение миграций

```bash
# PostgreSQL
psql -U postgres -d content_curator -f migrations/add_social_media_accounts.sql

# SQLite (для разработки)
sqlite3 content_curator.db < migrations/add_social_media_accounts.sql
```

### Dependencies

```txt
instagrapi==2.1.2     # Instagram
tweepy==4.14.0        # Twitter
cryptography==41.0.7  # Шифрование
python-telegram-bot==20.7  # Telegram
```

### Environment Variables

Полный список переменных см. в [production.env.example](production.env.example)

Критичные переменные:
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Twitter
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret

# Encryption (ОБЯЗАТЕЛЬНО!)
SOCIAL_TOKENS_ENCRYPTION_KEY=your_fernet_key
```

---

## 📞 Поддержка

При возникновении проблем:

1. **Instagram**: Проверьте что 2FA отключена
2. **Twitter**: Проверьте права приложения (Read and Write)
3. **Telegram**: Проверьте что бот добавлен как администратор

**Логи:**
```bash
tail -f logs/app.log | grep -i "instagram\|twitter\|telegram"
```

**Тестирование:**
- Instagram: `POST /api/instagram/accounts` с тестовыми данными
- Twitter: `GET /api/twitter/oauth/url` для начала OAuth flow
- Telegram: `POST /api/telegram/channels` с тестовым каналом

---

## 🎯 Checklist для подключения

### Instagram
- [ ] 2FA отключена
- [ ] Пароль создан (если входите через соцсети)
- [ ] Аккаунт старше 3 месяцев
- [ ] `SOCIAL_TOKENS_ENCRYPTION_KEY` установлен
- [ ] Аккаунт подключен через UI
- [ ] Тестовая публикация успешна

### Twitter
- [ ] Twitter Developer App создано
- [ ] `TWITTER_API_KEY` установлен
- [ ] `TWITTER_API_SECRET` установлен
- [ ] Callback URL настроен
- [ ] `SOCIAL_TOKENS_ENCRYPTION_KEY` установлен
- [ ] OAuth flow работает
- [ ] Тестовая публикация успешна

### Telegram
- [ ] Бот создан через @BotFather
- [ ] `TELEGRAM_BOT_TOKEN` установлен
- [ ] Бот добавлен в канал как администратор
- [ ] Канал подключен через UI
- [ ] Тестовая публикация успешна

---

**Документация обновлена:** 20 октября 2025


