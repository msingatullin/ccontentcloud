# 🔥 Social Media API - Простое использование

## ✅ Endpoints работают БЕЗ Swagger UI

Social Media API используют обычные Flask Blueprint endpoints (как Telegram, Instagram, Twitter).
**Авторизация работает АВТОМАТИЧЕСКИ** - просто добавьте токен в заголовок запроса.

## 📍 Endpoints

```
GET  /api/social-media/accounts  - Получить все социальные сети
PUT  /api/social-media/accounts  - Обновить настройки
```

**Важно:** Эти endpoints НЕ в Swagger UI, но работают точно так же!

## 🚀 Как использовать

### Шаг 1: Получите токен

```bash
curl -X POST https://your-service.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "your_password"
  }'
```

Скопируйте `access_token` из ответа.

### Шаг 2: Используйте endpoints

#### GET - Получить все социальные сети

```bash
curl -X GET https://your-service.run.app/api/social-media/accounts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "name": "Telegram",
      "isActive": true,
      "metadata": {
        "channelLink": "https://t.me/channel",
        "accountId": 1,
        "isDefault": true,
        "channelId": "-1001234567890",
        "channelName": "My Channel"
      }
    },
    {
      "name": "Instagram",
      "isActive": true,
      "metadata": {
        "username": "my_instagram",
        "accountId": 2,
        "isDefault": false
      }
    }
  ]
}
```

#### PUT - Обновить настройки

```bash
curl -X PUT https://your-service.run.app/api/social-media/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Telegram",
    "isActive": true,
    "metadata": {
      "accountId": 1,
      "isDefault": true
    }
  }'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Telegram канал обновлен"
}
```

## 💻 Использование в JavaScript/TypeScript

```javascript
// Получить токен
const loginResponse = await fetch('https://your-service.run.app/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'your@email.com',
    password: 'your_password'
  })
});

const { access_token } = await loginResponse.json();

// Использовать Social Media API
const response = await fetch('https://your-service.run.app/api/social-media/accounts', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const data = await response.json();
console.log(data.data); // Массив социальных сетей
```

## 🎯 В чем разница с другими API?

| Endpoint | Путь | Swagger UI |
|----------|------|------------|
| Auth API | `/api/v1/auth/*` | ✅ Да |
| Social Media API | `/api/social-media/*` | ❌ Нет, но работает! |
| Telegram API | `/api/telegram/*` | ❌ Нет, но работает! |
| Instagram API | `/api/instagram/*` | ❌ Нет, но работает! |
| Twitter API | `/api/twitter/*` | ❌ Нет, но работает! |

**Все работают одинаково!** Просто добавьте `Authorization: Bearer <token>` в заголовок.

## ❌ Не нужно

- ❌ Не нужно ничего настраивать в Swagger UI
- ❌ Не нужно вручную добавлять Bearer
- ❌ Не нужно делать что-то особенное

## ✅ Просто используйте

```
Authorization: Bearer YOUR_TOKEN
```

Все работает автоматически! 🚀

