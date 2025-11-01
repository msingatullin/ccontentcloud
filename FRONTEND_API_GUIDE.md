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

### 4. Frontend: Подключение Twitter (OAuth 1.0a)

Важно: пользователю НИЧЕГО не нужно вводить (никакие ключи). Ключи приложения находятся на сервере. Фронт выполняет двухшаговый OAuth.

1) Инициация OAuth
```javascript
// 1. Запрашиваем URL авторизации
const r = await fetch(`/api/twitter/oauth/url?callback_url=${encodeURIComponent(window.location.origin + '/twitter/callback')}`, {
  headers: { Authorization: `Bearer ${accessToken}` }
});
const { success, auth_url, oauth_token_secret } = await r.json();
if (!success) throw new Error('OAuth URL error');

// 2. Сохраняем secret до возврата из Twitter
sessionStorage.setItem('tw_oauth_secret', oauth_token_secret);

// 3. Редиректим пользователя в Twitter для авторизации
window.location.href = auth_url;
```

2) Callback страница (после возврата из Twitter)
```javascript
// Пример на странице /twitter/callback
const params = new URLSearchParams(window.location.search);
const oauth_token = params.get('oauth_token');
const oauth_verifier = params.get('oauth_verifier');
const oauth_token_secret = sessionStorage.getItem('tw_oauth_secret');

if (!oauth_token || !oauth_verifier || !oauth_token_secret) {
  // показать ошибку пользователю
}

const resp = await fetch(`/api/twitter/oauth/callback?oauth_token=${encodeURIComponent(oauth_token)}&oauth_verifier=${encodeURIComponent(oauth_verifier)}`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`
  },
  body: JSON.stringify({ oauth_token_secret, account_name: 'Мой Twitter' })
});
const data = await resp.json();
if (data.success) {
  // Аккаунт подключен, можно обновить список
  sessionStorage.removeItem('tw_oauth_secret');
} else {
  // показать data.error
}
```

3) Проверка подключения и управление аккаунтами
```javascript
// Получить аккаунты
const accountsRes = await fetch('/api/twitter/accounts', {
  headers: { Authorization: `Bearer ${accessToken}` }
});
const { accounts } = await accountsRes.json();

// Установить по умолчанию
await fetch(`/api/twitter/accounts/${accounts[0].id}/default`, {
  method: 'PUT',
  headers: { Authorization: `Bearer ${accessToken}` }
});

// Удалить аккаунт
await fetch(`/api/twitter/accounts/${accounts[0].id}`, {
  method: 'DELETE',
  headers: { Authorization: `Bearer ${accessToken}` }
});
```

Ошибки и особые случаи:
- Если не передан `callback_url` в шаге 1, будет использован дефолт `API_BASE_URL/api/twitter/oauth/callback` (бэкенд).
- При `400` в callback: проверьте, что передаёте `oauth_token_secret` из шага 1 и что query содержит `oauth_token` и `oauth_verifier`.
- Всегда отправляйте Bearer JWT в заголовках.

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

