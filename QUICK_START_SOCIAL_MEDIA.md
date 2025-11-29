# 🚀 Быстрый старт - Социальные сети

## 🎯 За 5 минут до первой публикации

### 1️⃣ Настройка окружения

```bash
# Установите зависимости
pip install instagrapi==2.1.2 tweepy==4.14.0 cryptography

# Сгенерируйте ключ шифрования
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Добавьте в .env
SOCIAL_TOKENS_ENCRYPTION_KEY=<ваш_сгенерированный_ключ>
TELEGRAM_BOT_TOKEN=7579380481:AAFAiTobG-PFv7Wgr2VC-BioWcnGsaQZafc
```

### 2️⃣ Twitter Developer App

1. https://developer.twitter.com/en/portal/dashboard
2. Создайте App с правами **Read and Write**
3. Скопируйте API Key и API Secret

```bash
# Добавьте в .env
TWITTER_API_KEY=ваш_api_key
TWITTER_API_SECRET=ваш_api_secret
```

### 3️⃣ Применить миграции БД

```bash
# PostgreSQL
psql -U postgres -d content_curator -f migrations/add_social_media_accounts.sql

# Проверка
psql -U postgres -d content_curator -c "SELECT tablename FROM pg_tables WHERE tablename IN ('instagram_accounts', 'twitter_accounts');"
```

### 4️⃣ Запуск приложения

```bash
# Запуск Flask
python app.py

# Проверка endpoints
curl http://localhost:5000/api/instagram/info
curl http://localhost:5000/api/twitter/info
curl http://localhost:5000/api/telegram/bot-info
```

---

## 📱 Instagram - Подключение за 2 минуты

### ⚠️ Подготовка
1. **Отключите 2FA** в Instagram → Настройки → Безопасность
2. Если входите через Facebook/Google - создайте пароль

### 🔌 Подключение через API

```bash
curl -X POST http://localhost:5000/api/instagram/accounts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_instagram_username",
    "password": "your_instagram_password",
    "account_name": "Мой Instagram"
  }'
```

**Success:**
```json
{
  "success": true,
  "message": "Instagram аккаунт успешно добавлен",
  "account": {
    "id": 1,
    "instagram_username": "your_username",
    "is_verified": true
  }
}
```

### 📸 Публикация

```python
# Через API
POST /api/content/publish
{
    "platform": "instagram",
    "user_id": 1,
    "content": {
        "text": "Мой пост в Instagram",
        "hashtags": ["ai", "content"],
        "images": ["/path/to/image.jpg"]  # ОБЯЗАТЕЛЬНО
    }
}
```

---

## 🐦 Twitter - Подключение через OAuth

### 🔑 Подготовка
Убедитесь что `TWITTER_API_KEY` и `TWITTER_API_SECRET` в `.env`

### 1. Получить OAuth URL

```bash
curl -X GET "http://localhost:5000/api/twitter/oauth/url?callback_url=http://localhost:3000/callback" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "auth_url": "https://api.twitter.com/oauth/authorize?oauth_token=abc123",
  "oauth_token_secret": "xyz789"  // СОХРАНИТЕ!
}
```

### 2. Пользователь авторизуется
1. Перенаправьте на `auth_url`
2. Twitter вернет на callback с `?oauth_token=...&oauth_verifier=...`

### 3. Завершить OAuth

```bash
curl -X POST "http://localhost:5000/api/twitter/oauth/callback?oauth_token=abc123&oauth_verifier=def456" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "oauth_token_secret": "xyz789",
    "account_name": "Мой Twitter"
  }'
```

**Success:**
```json
{
  "success": true,
  "account": {
    "id": 1,
    "twitter_username": "username"
  }
}
```

### 🐦 Публикация

```python
POST /api/content/publish
{
    "platform": "twitter",
    "user_id": 1,
    "content": {
        "text": "Мой твит (до 280 символов)",
        "images": ["/path/to/image.jpg"]  // Опционально, до 4 шт
    }
}
```

---

## 📱 Telegram - Подключение за 1 минуту

### 1. Добавьте бота в канал
1. Откройте свой Telegram канал
2. Настройки → Администраторы → Добавить
3. Найдите **@content4ubot**
4. Дайте права: **Публикация сообщений**

### 2. Подключите канал

```bash
curl -X POST http://localhost:5000/api/telegram/channels \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_link": "https://t.me/your_channel",
    "channel_name": "Мой канал"
  }'
```

**Success:**
```json
{
  "success": true,
  "channel": {
    "id": 1,
    "channel_name": "Мой канал",
    "is_verified": true
  }
}
```

### 📤 Публикация

```python
POST /api/content/publish
{
    "platform": "telegram",
    "user_id": 1,
    "content": {
        "text": "Мой пост в Telegram",
        "images": ["/path/to/image.jpg"]  // Опционально
    }
}
```

---

## 🔍 Проверка статуса

### Список подключенных аккаунтов

```bash
# Instagram
curl -X GET http://localhost:5000/api/instagram/accounts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Twitter
curl -X GET http://localhost:5000/api/twitter/accounts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Telegram
curl -X GET http://localhost:5000/api/telegram/channels \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## ⚠️ Troubleshooting

### Instagram
```bash
# Error: "2FA включена"
→ Отключите в Instagram → Настройки → Безопасность → 2FA

# Error: "Challenge required"
→ Войдите в Instagram приложение и подтвердите вход

# Error: "Неверный пароль"
→ Проверьте username/password
```

### Twitter
```bash
# Error: "TWITTER_API_KEY не установлен"
→ Добавьте в .env: TWITTER_API_KEY=...

# Error: "Invalid oauth_verifier"
→ Проверьте что передаете правильный oauth_token_secret

# Error: "Could not authenticate"
→ Проверьте права App: должны быть Read and Write
```

### Telegram
```bash
# Error: "Бот не является администратором"
→ Добавьте @content4ubot в админы канала

# Error: "Chat not found"
→ Проверьте что ссылка на канал правильная

# Error: "Bot was kicked"
→ Разблокируйте бота и добавьте снова
```

---

## 📊 Тестирование

### Instagram Test
```python
import requests

response = requests.post(
    'http://localhost:5000/api/instagram/accounts',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        'username': 'test_username',
        'password': 'test_password',
        'account_name': 'Test Account'
    }
)
print(response.json())
```

### Twitter OAuth Test
```python
# Step 1: Get auth URL
response = requests.get(
    'http://localhost:5000/api/twitter/oauth/url',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    params={'callback_url': 'http://localhost:3000/callback'}
)
data = response.json()
print(f"Go to: {data['auth_url']}")
print(f"Save: {data['oauth_token_secret']}")
```

### Telegram Test
```python
response = requests.post(
    'http://localhost:5000/api/telegram/channels',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        'channel_link': 'https://t.me/test_channel',
        'channel_name': 'Test Channel'
    }
)
print(response.json())
```

---

## 🎯 Checklist

- [ ] `SOCIAL_TOKENS_ENCRYPTION_KEY` в .env
- [ ] `TELEGRAM_BOT_TOKEN` в .env
- [ ] `TWITTER_API_KEY` и `TWITTER_API_SECRET` в .env
- [ ] Миграции БД применены
- [ ] Instagram: 2FA отключена
- [ ] Twitter: App создано с Read and Write
- [ ] Telegram: Бот добавлен в канал как админ
- [ ] Все 3 платформы подключены через API
- [ ] Тестовые публикации успешны

---

**Полная документация:** [SOCIAL_MEDIA_SETUP.md](SOCIAL_MEDIA_SETUP.md)


