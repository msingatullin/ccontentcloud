# 📅 Инструкция для UI: Запланированные посты и автопостинг

## API Endpoints

### Базовый URL
```
https://content-curator-1046574462613.us-central1.run.app/api/v1
```

### Аутентификация
Все endpoints требуют JWT токен:
```
Authorization: Bearer <token>
```

---

## 1. Запланированные посты

### 1.1 Создать запланированный пост

**POST** `/scheduled-posts`

**Request:**
```json
{
  "content_id": "uuid-контента",
  "platform": "telegram",
  "account_id": 1,
  "scheduled_time": "2025-01-15T10:00:00Z",
  "publish_options": {
    "geolocation": "Москва",
    "first_comment": "Комментарий",
    "utm_tags": "?utm_source=telegram&utm_campaign=post"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "content_id": "uuid",
    "platform": "telegram",
    "account_id": 1,
    "scheduled_time": "2025-01-15T10:00:00Z",
    "status": "scheduled",
    "publish_options": {},
    "created_at": "2025-01-10T12:00:00Z",
    "updated_at": "2025-01-10T12:00:00Z"
  },
  "timestamp": "2025-01-10T12:00:00Z"
}
```

### 1.2 Получить список постов

**GET** `/scheduled-posts?status=scheduled&platform=telegram&limit=50&offset=0`

**Query параметры:**
- `status` (optional): scheduled, published, failed, cancelled
- `platform` (optional): telegram, instagram, twitter
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "content_id": "uuid",
      "platform": "telegram",
      "account_id": 1,
      "scheduled_time": "2025-01-15T10:00:00Z",
      "status": "scheduled",
      "created_at": "2025-01-10T12:00:00Z"
    }
  ],
  "timestamp": "2025-01-10T12:00:00Z"
}
```

### 1.3 Получить пост

**GET** `/scheduled-posts/{post_id}`

### 1.4 Обновить пост

**PUT** `/scheduled-posts/{post_id}`

**Request:**
```json
{
  "scheduled_time": "2025-01-16T15:00:00Z",
  "status": "scheduled"
}
```

### 1.5 Отменить пост

**POST** `/scheduled-posts/{post_id}/cancel`

**Response:**
```json
{
  "success": true,
  "message": "Пост успешно отменен",
  "timestamp": "2025-01-10T12:00:00Z"
}
```

### 1.6 Удалить пост

**DELETE** `/scheduled-posts/{post_id}`

**Response:**
```json
{
  "success": true,
  "message": "Пост успешно удален",
  "timestamp": "2025-01-10T12:00:00Z"
}
```

---

## 2. Правила автопостинга

### 2.1 Создать правило

**POST** `/auto-posting/rules`

**Request (daily):**
```json
{
  "name": "Ежедневные посты о финансах",
  "description": "Посты каждый день в 9:00 и 18:00",
  "schedule_type": "daily",
  "schedule_config": {
    "times": ["09:00", "18:00"],
    "days_of_week": [1, 2, 3, 4, 5]
  },
  "content_config": {
    "title": "Финансовые советы",
    "description": "Создай пост о личных финансах и инвестициях",
    "target_audience": "Молодые предприниматели 25-35 лет",
    "business_goals": ["привлечение аудитории", "образование"],
    "tone": "professional",
    "keywords": ["финансы", "инвестиции", "бизнес"],
    "call_to_action": ["подписаться", "узнать больше"]
  },
  "platforms": ["telegram", "instagram"],
  "accounts": {
    "telegram": [1, 2],
    "instagram": [3]
  },
  "content_types": ["post"],
  "max_posts_per_day": 2
}
```

**Request (weekly):**
```json
{
  "name": "Еженедельный обзор",
  "description": "Еженедельный обзор новостей",
  "schedule_type": "weekly",
  "schedule_config": {
    "day_of_week": 1,
    "time": "10:00"
  },
  "content_config": {
    "title": "Обзор недели",
    "description": "Создай обзор главных новостей недели",
    "target_audience": "Профессионалы IT",
    "business_goals": ["образование", "лидерство мысли"],
    "tone": "professional",
    "keywords": ["технологии", "новости", "обзор"]
  },
  "platforms": ["telegram"]
}
```

**Request (custom):**
```json
{
  "name": "Специальные даты",
  "description": "Посты на конкретные даты",
  "schedule_type": "custom",
  "schedule_config": {
    "dates": [
      "2025-01-15T10:00:00Z",
      "2025-01-20T15:00:00Z",
      "2025-02-01T12:00:00Z"
    ]
  },
  "content_config": {
    "title": "Специальный пост",
    "description": "Создай пост для специального события",
    "target_audience": "Клиенты компании",
    "business_goals": ["вовлечение"],
    "tone": "friendly"
  },
  "platforms": ["telegram", "instagram"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Ежедневные посты о финансах",
    "description": "Посты каждый день в 9:00 и 18:00",
    "schedule_type": "daily",
    "schedule_config": {
      "times": ["09:00", "18:00"],
      "days_of_week": [1, 2, 3, 4, 5]
    },
    "content_config": {...},
    "platforms": ["telegram", "instagram"],
    "accounts": {
      "telegram": [1, 2],
      "instagram": [3]
    },
    "is_active": true,
    "is_paused": false,
    "next_execution_at": "2025-01-11T09:00:00Z",
    "total_executions": 0,
    "successful_executions": 0,
    "failed_executions": 0,
    "created_at": "2025-01-10T12:00:00Z"
  },
  "timestamp": "2025-01-10T12:00:00Z"
}
```

### 2.2 Получить список правил

**GET** `/auto-posting/rules?is_active=true&limit=50&offset=0`

**Query параметры:**
- `is_active` (optional): true, false
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

### 2.3 Получить правило

**GET** `/auto-posting/rules/{rule_id}`

### 2.4 Обновить правило

**PUT** `/auto-posting/rules/{rule_id}`

**Request:**
```json
{
  "name": "Новое название",
  "is_active": true,
  "schedule_config": {
    "times": ["10:00", "19:00"],
    "days_of_week": [1, 2, 3, 4, 5]
  }
}
```

### 2.5 Включить/выключить правило

**POST** `/auto-posting/rules/{rule_id}/toggle`

**Request:**
```json
{
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Правило включено",
  "timestamp": "2025-01-10T12:00:00Z"
}
```

### 2.6 Удалить правило

**DELETE** `/auto-posting/rules/{rule_id}`

**Response:**
```json
{
  "success": true,
  "message": "Правило успешно удалено",
  "timestamp": "2025-01-10T12:00:00Z"
}
```

---

## 3. Примеры использования в React

### Создание запланированного поста

```javascript
const schedulePost = async (contentId, platform, scheduledTime, accountId = null) => {
  try {
    const response = await fetch('/api/v1/scheduled-posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        content_id: contentId,
        platform: platform,
        account_id: accountId,
        scheduled_time: scheduledTime,
        publish_options: {}
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Пост запланирован:', data.data);
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Ошибка планирования поста:', error);
    throw error;
  }
};

// Использование
await schedulePost(
  'content-uuid',
  'telegram',
  '2025-01-15T10:00:00Z',
  1
);
```

### Создание правила автопостинга

```javascript
const createAutoPostingRule = async (ruleData) => {
  try {
    const response = await fetch('/api/v1/auto-posting/rules', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(ruleData)
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Правило создано:', data.data);
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Ошибка создания правила:', error);
    throw error;
  }
};

// Использование
await createAutoPostingRule({
  name: 'Ежедневные посты',
  schedule_type: 'daily',
  schedule_config: {
    times: ['09:00', '18:00'],
    days_of_week: [1, 2, 3, 4, 5]
  },
  content_config: {
    title: 'Финансовые советы',
    description: 'Создай пост о личных финансах',
    target_audience: 'Молодые предприниматели',
    business_goals: ['образование'],
    tone: 'professional',
    keywords: ['финансы']
  },
  platforms: ['telegram'],
  max_posts_per_day: 2
});
```

### Получение списка запланированных постов

```javascript
const getScheduledPosts = async (filters = {}) => {
  const params = new URLSearchParams({
    limit: filters.limit || 50,
    offset: filters.offset || 0,
    ...(filters.status && { status: filters.status }),
    ...(filters.platform && { platform: filters.platform })
  });
  
  try {
    const response = await fetch(`/api/v1/scheduled-posts?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Ошибка получения постов:', error);
    throw error;
  }
};

// Использование
const posts = await getScheduledPosts({
  status: 'scheduled',
  platform: 'telegram',
  limit: 20
});
```

### React компонент для списка запланированных постов

```javascript
import React, { useState, useEffect } from 'react';

const ScheduledPostsList = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    status: 'scheduled',
    platform: 'all'
  });

  useEffect(() => {
    loadPosts();
  }, [filter]);

  const loadPosts = async () => {
    setLoading(true);
    try {
      const data = await getScheduledPosts(filter);
      setPosts(data);
    } catch (error) {
      console.error('Ошибка загрузки постов:', error);
    } finally {
      setLoading(false);
    }
  };

  const cancelPost = async (postId) => {
    try {
      const response = await fetch(`/api/v1/scheduled-posts/${postId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('Пост отменен');
        loadPosts();
      }
    } catch (error) {
      console.error('Ошибка отмены поста:', error);
    }
  };

  return (
    <div className="scheduled-posts">
      <h2>Запланированные посты</h2>
      
      <div className="filters">
        <select value={filter.status} onChange={(e) => setFilter({...filter, status: e.target.value})}>
          <option value="all">Все</option>
          <option value="scheduled">Запланированные</option>
          <option value="published">Опубликованные</option>
          <option value="cancelled">Отмененные</option>
        </select>
        
        <select value={filter.platform} onChange={(e) => setFilter({...filter, platform: e.target.value})}>
          <option value="all">Все платформы</option>
          <option value="telegram">Telegram</option>
          <option value="instagram">Instagram</option>
          <option value="twitter">Twitter</option>
        </select>
      </div>

      {loading ? (
        <div>Загрузка...</div>
      ) : (
        <div className="posts-list">
          {posts.map(post => (
            <div key={post.id} className="post-item">
              <div className="post-info">
                <strong>{post.platform}</strong>
                <span>{new Date(post.scheduled_time).toLocaleString()}</span>
                <span className={`status ${post.status}`}>{post.status}</span>
              </div>
              
              {post.status === 'scheduled' && (
                <button onClick={() => cancelPost(post.id)}>
                  Отменить
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ScheduledPostsList;
```

---

## 4. UI Компоненты (рекомендации)

### 4.1 Календарь запланированных постов

**Функции:**
- Отображение постов в формате календаря
- Фильтры по статусу и платформе
- Drag & drop для изменения времени
- Быстрое создание поста

**Поля для отображения:**
- Время публикации
- Платформа (с иконкой)
- Статус (цветной бейдж)
- Превью контента
- Кнопки: Редактировать, Отменить, Удалить

### 4.2 Форма создания запланированного поста

**Поля:**
1. Выбор контента (из созданных)
2. Выбор платформы
3. Выбор аккаунта (если несколько)
4. Дата и время публикации (date-time picker)
5. Дополнительные опции (геолокация, UTM-метки, первый комментарий)

**Валидация:**
- Контент должен быть создан
- Время должно быть в будущем
- Платформа и аккаунт должны быть активны

### 4.3 Форма создания правила автопостинга

**Шаги:**

1. **Основная информация:**
   - Название правила
   - Описание

2. **Расписание:**
   - Тип: Daily / Weekly / Custom
   - Для Daily: выбор времен и дней недели
   - Для Weekly: день недели и время
   - Для Custom: список конкретных дат

3. **Параметры контента:**
   - Все поля как в `/api/v1/content/create`
   - Title, Description, Target Audience
   - Business Goals, Keywords
   - Tone

4. **Платформы и аккаунты:**
   - Выбор платформ (чекбоксы)
   - Выбор аккаунтов для каждой платформы

5. **Лимиты:**
   - Максимум постов в день
   - Максимум постов в неделю

### 4.4 Список правил автопостинга

**Колонки таблицы:**
- Название
- Статус (Активно/Пауза)
- Тип расписания
- Следующее выполнение
- Статистика (всего/успешно/ошибок)
- Действия (Редактировать, Включить/Выключить, Удалить)

**Фильтры:**
- Активные/Неактивные
- Тип расписания

---

## 5. Обработка ошибок

### Типичные ошибки

**400 Bad Request:**
```json
{
  "success": false,
  "error": "Validation Error",
  "message": "Некорректные данные запроса",
  "details": [...],
  "status_code": 400,
  "timestamp": "2025-01-10T12:00:00Z"
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Требуется авторизация",
  "status_code": 401
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": "Not Found",
  "message": "Пост не найден",
  "status_code": 404
}
```

### Обработка в коде

```javascript
const handleApiError = (error, data) => {
  if (data.status_code === 400) {
    // Ошибка валидации
    alert(`Ошибка: ${data.message}`);
    if (data.details) {
      console.log('Детали:', data.details);
    }
  } else if (data.status_code === 401) {
    // Не авторизован
    window.location.href = '/login';
  } else if (data.status_code === 404) {
    // Не найдено
    alert('Запись не найдена');
  } else {
    // Другие ошибки
    alert('Произошла ошибка. Попробуйте позже.');
  }
};
```

---

## 6. Swagger UI

Интерактивная документация доступна по адресу:
```
https://content-curator-1046574462613.us-central1.run.app/api/docs
```

В Swagger UI можно:
- Протестировать все endpoints
- Посмотреть примеры запросов и ответов
- Авторизоваться с помощью JWT токена (кнопка "Authorize")

---

## 7. Следующие шаги для фронтенда

1. **Создать компоненты:**
   - ScheduledPostsCalendar
   - ScheduledPostForm
   - AutoPostingRuleForm
   - AutoPostingRulesList

2. **Добавить маршруты:**
   - `/scheduled-posts` - календарь постов
   - `/auto-posting` - список правил
   - `/auto-posting/create` - создание правила
   - `/auto-posting/:id/edit` - редактирование правила

3. **Интегрировать с Redux/Context:**
   - Состояние для постов
   - Состояние для правил
   - Actions для API calls

4. **Добавить уведомления:**
   - Toast для успешных операций
   - Модальные окна для подтверждения удаления

---

**Документация обновлена:** 14 ноября 2025  
**Версия API:** v1

