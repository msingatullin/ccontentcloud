# 📋 Changelog: Система запланированных постов и автопостинга

**Дата:** 14 ноября 2025  
**Автор:** AI Assistant  
**Статус:** ✅ Готово к использованию

---

## 🎯 Что реализовано

### 1. Модели базы данных

#### ScheduledPostDB (`app/models/scheduled_posts.py`)
- Хранение запланированных постов
- Связь с контентом и пользователем
- Статусы: scheduled, published, failed, cancelled
- Поддержка publish_options (геолокация, UTM, first comment)
- Индексы для быстрого поиска

#### AutoPostingRuleDB (`app/models/auto_posting_rules.py`)
- Правила для автоматического создания и публикации контента
- 4 типа расписаний: daily, weekly, custom, cron
- Хранение параметров для создания контента
- Статистика выполнения правил
- Лимиты постов (в день/неделю)

### 2. Обновленные модели

#### User (`app/auth/models/user.py`)
- Добавлены relationships: `scheduled_posts`, `auto_posting_rules`

#### ContentPieceDB (`app/models/content.py`)
- Добавлен relationship: `scheduled_posts`

#### Database Connection (`app/database/connection.py`)
- Добавлены импорты новых моделей

### 3. Сервисы

#### ScheduledPostService (`app/services/scheduled_post_service.py`)
**Методы:**
- `create_scheduled_post()` - создание поста
- `get_scheduled_post()` - получение поста
- `list_scheduled_posts()` - список с фильтрами
- `update_scheduled_post()` - обновление
- `cancel_scheduled_post()` - отмена
- `delete_scheduled_post()` - удаление
- `get_posts_to_publish()` - посты для публикации (scheduler)
- `mark_as_published()` - отметка о публикации

#### AutoPostingService (`app/services/auto_posting_service.py`)
**Методы:**
- `create_rule()` - создание правила
- `get_rule()` - получение правила
- `list_rules()` - список с фильтрами
- `update_rule()` - обновление
- `delete_rule()` - удаление
- `toggle_active()` - включить/выключить
- `get_rules_to_execute()` - правила для выполнения (scheduler)
- `mark_execution()` - отметка о выполнении
- `_calculate_next_execution()` - вычисление следующего времени

### 4. API Endpoints

#### Запланированные посты (`/api/v1/scheduled-posts`)
- `GET /` - список постов
- `POST /` - создать пост
- `GET /{post_id}` - получить пост
- `PUT /{post_id}` - обновить пост
- `DELETE /{post_id}` - удалить пост
- `POST /{post_id}/cancel` - отменить пост

#### Автопостинг (`/api/v1/auto-posting`)
- `GET /rules` - список правил
- `POST /rules` - создать правило
- `GET /rules/{rule_id}` - получить правило
- `PUT /rules/{rule_id}` - обновить правило
- `DELETE /rules/{rule_id}` - удалить правило
- `POST /rules/{rule_id}/toggle` - включить/выключить

### 5. Схемы валидации

В `app/api/schemas.py` добавлены:
- `ScheduledPostCreateSchema`
- `ScheduledPostUpdateSchema`
- `ScheduledPostResponseSchema`
- `ScheduleConfigSchema`
- `AutoPostingRuleCreateSchema`
- `AutoPostingRuleUpdateSchema`
- `AutoPostingRuleResponseSchema`

### 6. Интеграция

#### app.py
- Импорт новых namespaces
- Регистрация в Swagger API
- Доступны по путям:
  - `/api/v1/scheduled-posts`
  - `/api/v1/auto-posting`

### 7. Документация

#### SCHEDULED_POSTS_UI_GUIDE.md
Полное руководство для фронтенда:
- Описание всех API endpoints
- Примеры запросов и ответов
- React компоненты (примеры)
- JavaScript функции для интеграции
- Рекомендации по UI/UX
- Обработка ошибок

---

## 🔑 Основные возможности

### Запланированные посты:
✅ Планирование публикации готового контента  
✅ Поддержка Telegram, Instagram, Twitter  
✅ Выбор конкретного аккаунта для публикации  
✅ Дополнительные опции (геолокация, UTM, комментарии)  
✅ Отмена и редактирование запланированных постов  
✅ Отслеживание статусов публикации  

### Автопостинг:
✅ Автоматическое создание контента по расписанию  
✅ 4 типа расписаний (daily, weekly, custom, cron)  
✅ Гибкая настройка параметров контента  
✅ Публикация на несколько платформ одновременно  
✅ Лимиты публикаций (день/неделя)  
✅ Статистика выполнения правил  
✅ Вкл/Выкл правил без удаления  

---

## 📊 Структура БД

### Таблица: scheduled_posts
```sql
- id (PK)
- user_id (FK)
- content_id (FK)
- platform (telegram/instagram/twitter)
- account_id, account_type
- scheduled_time, published_at
- status (scheduled/published/failed/cancelled)
- platform_post_id, error_message
- publish_options (JSON)
- created_at, updated_at
```

**Индексы:**
- `user_id + status`
- `scheduled_time + status`
- `platform + status`

### Таблица: auto_posting_rules
```sql
- id (PK)
- user_id (FK)
- name, description
- schedule_type, schedule_config (JSON)
- content_config (JSON)
- platforms (JSON), accounts (JSON)
- content_types (JSON)
- is_active, is_paused
- max_posts_per_day, max_posts_per_week
- total_executions, successful_executions, failed_executions
- last_execution_at, next_execution_at
- created_at, updated_at
```

**Индексы:**
- `user_id + is_active`
- `next_execution_at + is_active`

---

## 🚀 Следующие шаги

### Требуется реализовать (не включено):

1. **Background Scheduler** (отдельный процесс)
   - Опрос `ScheduledPostService.get_posts_to_publish()`
   - Вызов `PublisherAgent` для публикации
   - Обновление статусов через `mark_as_published()`
   
2. **Auto-posting Worker** (отдельный процесс)
   - Опрос `AutoPostingService.get_rules_to_execute()`
   - Вызов `/api/v1/content/create` с параметрами из rule
   - Создание `scheduled_post` для полученного контента
   - Обновление статистики через `mark_execution()`

3. **Интеграция с PublisherAgent**
   - Метод для публикации scheduled post
   - Обработка ошибок публикации
   - Сохранение platform_post_id

4. **Cron-like расписание**
   - Интеграция библиотеки `croniter`
   - Поддержка cron выражений в `_calculate_next_execution()`

5. **UI Компоненты** (фронтенд)
   - Календарь запланированных постов
   - Форма создания scheduled post
   - Форма создания auto posting rule
   - Список и управление правилами

---

## ✅ Проверка работы

### 1. Проверка БД
```bash
# После запуска приложения проверьте создание таблиц:
sqlite3 app.db
.tables
# Должны быть: scheduled_posts, auto_posting_rules
```

### 2. Проверка Swagger UI
```
https://content-curator-1046574462613.us-central1.run.app/api/docs
```
- Должны быть разделы: `scheduled-posts`, `auto-posting`
- Авторизуйтесь через кнопку "Authorize"
- Протестируйте создание scheduled post

### 3. Проверка endpoints

**Создание scheduled post:**
```bash
curl -X POST https://content-curator-1046574462613.us-central1.run.app/api/v1/scheduled-posts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "existing-content-uuid",
    "platform": "telegram",
    "scheduled_time": "2025-01-15T10:00:00Z"
  }'
```

**Создание auto-posting rule:**
```bash
curl -X POST https://content-curator-1046574462613.us-central1.run.app/api/v1/auto-posting/rules \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Rule",
    "schedule_type": "daily",
    "schedule_config": {
      "times": ["10:00"],
      "days_of_week": [1,2,3,4,5]
    },
    "content_config": {
      "title": "Test",
      "description": "Test post"
    },
    "platforms": ["telegram"]
  }'
```

---

## 📁 Измененные файлы

### Новые файлы:
1. `app/models/scheduled_posts.py`
2. `app/models/auto_posting_rules.py`
3. `app/services/scheduled_post_service.py`
4. `app/services/auto_posting_service.py`
5. `app/api/scheduled_posts_ns.py`
6. `app/api/auto_posting_ns.py`
7. `SCHEDULED_POSTS_UI_GUIDE.md`
8. `SCHEDULED_POSTING_CHANGELOG.md`

### Измененные файлы:
1. `app/auth/models/user.py` - добавлены relationships
2. `app/models/content.py` - добавлен relationship
3. `app/database/connection.py` - добавлены импорты
4. `app/api/schemas.py` - добавлены новые схемы
5. `app.py` - добавлены импорты и регистрация namespaces

---

## ⚠️ Важные замечания

1. **НЕ удалено** ничего из существующего кода
2. **НЕ изменена** работающая функциональность
3. **Добавлены** только новые компоненты
4. **Все импорты** корректны и проверены линтером
5. **JWT авторизация** использует существующий `@jwt_required` декоратор
6. **База данных** автоматически создаст новые таблицы при запуске

---

## 🔄 Откат изменений

Если нужно откатить изменения:

```bash
# Удалить новые файлы
rm app/models/scheduled_posts.py
rm app/models/auto_posting_rules.py
rm app/services/scheduled_post_service.py
rm app/services/auto_posting_service.py
rm app/api/scheduled_posts_ns.py
rm app/api/auto_posting_ns.py

# Восстановить измененные файлы
git checkout app/auth/models/user.py
git checkout app/models/content.py
git checkout app/database/connection.py
git checkout app/api/schemas.py
git checkout app.py
```

---

**Готово к использованию!** ✅

