# API Guide для Frontend Developer

## ✅ Реализованные API Endpoints

**Важно:** Social Media endpoints используют обычные Flask Blueprint (не в Swagger UI).
Авторизация работает **автоматически** - просто добавьте `Authorization: Bearer <token>` в заголовок запроса.

### 1. Универсальные Social Media API

#### `GET /api/social-media/accounts`
Получить все социальные сети пользователя

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "name": "Telegram",
      "isActive": true,
      "metadata": {
        "channelLink": "https://t.me/mychannel",
        "accountId": 123,
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
        "accountId": 456,
        "isDefault": false,
        "isActive": true
      }
    },
    {
      "name": "Twitter",
      "isActive": true,
      "metadata": {
        "username": "my_twitter",
        "accountId": 789,
        "isDefault": true,
        "userId": "123456789"
      }
    }
  ]
}
```

#### `PUT /api/social-media/accounts`
Обновить настройки социальной сети

**Request Body:**
```json
{
  "name": "Telegram",
  "isActive": true,
  "metadata": {
    "channelLink": "https://t.me/mychannel",
    "accountId": 123,
    "isDefault": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Telegram канал обновлен"
}
```

### 2. Login Response обновлен ✅

При логине в объекте пользователя **ВСЕГДА** есть поле `socialMedia` со всеми социальными сетями:

```json
{
  "message": "Успешная авторизация",
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user",
    "first_name": "John",
    "last_name": "Doe",
    "socialMedia": [
      {
        "name": "Telegram",
        "isActive": true  // true если есть подключенные каналы
      },
      {
        "name": "Instagram", 
        "isActive": true  // true если есть подключенные аккаунты
      },
      {
        "name": "Twitter",
        "isActive": false  // false если нет подключенных аккаунтов
      }
    ],
    // ... другие поля пользователя
  }
}
```

**Важно:** Массив `socialMedia` **всегда содержит все 3 социальные сети**, даже если они не подключены. Поле `isActive` показывает статус подключения.

### 3. Специфичные API для каждой социальной сети

#### Telegram Channels
- `GET /api/telegram/channels` - получить каналы
- `POST /api/telegram/channels` - добавить канал
- `PUT /api/telegram/channels/{id}/default` - установить по умолчанию
- `DELETE /api/telegram/channels/{id}` - удалить канал

#### Instagram Accounts
- `GET /api/instagram/accounts` - получить аккаунты
- `POST /api/instagram/accounts` - добавить аккаунт (логин/пароль)
- `PUT /api/instagram/accounts/{id}/default` - установить по умолчанию
- `DELETE /api/instagram/accounts/{id}` - удалить аккаунт

#### Twitter Accounts
- `GET /api/twitter/oauth/url` - получить OAuth URL
- `GET /api/twitter/oauth/callback` - OAuth callback
- `GET /api/twitter/accounts` - получить аккаунты
- `PUT /api/twitter/accounts/{id}/default` - установить по умолчанию
- `DELETE /api/twitter/accounts/{id}` - удалить аккаунт

## 🔧 Исправления по вашим заметкам

### ✅ Metadata как объект (не массив)
Исправлено! Теперь `metadata` - это объект `{}`, а не массив `[]`.

### ✅ Универсальные endpoints
Реализованы `getSocialMediaAccounts()` и `updateSocialMediaAccount()` как запрашивал фронтенд-разработчик.

### ✅ SocialMedia в login response
Добавлено поле `socialMedia` в ответ при логине.

## 📋 Примеры использования

### Получение всех социальных сетей
```javascript
const response = await fetch('/api/social-media/accounts', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
const data = await response.json();
console.log(data.data); // массив социальных сетей
```

### Обновление настроек
```javascript
const response = await fetch('/api/social-media/accounts', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    name: "Telegram",
    isActive: true,
    metadata: {
      accountId: 123,
      isDefault: true
    }
  })
});
```

## 🎯 Готово к использованию!

Все API endpoints работают и соответствуют вашим требованиям. Сервис развернут и доступен по адресу:
`https://content-curator-dt3n7kzpwq-uc.a.run.app`