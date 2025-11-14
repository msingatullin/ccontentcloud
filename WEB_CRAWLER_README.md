# 🕷️ Web Crawler & Content Monitoring System

## 📋 Обзор

Система автоматического мониторинга источников контента с использованием:
- **Web Crawler** - для мониторинга сайтов без RSS
- **RSS Feed Monitor** - для RSS лент
- **AI-based Content Extraction** - извлечение контента через GPT-4
- **Change Detection** - определение новизны контента
- **Auto-posting** - автоматическое создание отложенных постов

---

## 🏗️ Архитектура

### Компоненты системы

```
┌─────────────────────────────────────────────────────┐
│                   WebCrawlerWorker                   │
│         (Background Thread, проверка каждые 60s)     │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
   ┌────▼─────┐          ┌──────▼──────┐
   │   RSS    │          │   Website   │
   │  Parser  │          │   Crawler   │
   └────┬─────┘          └──────┬──────┘
        │                       │
        └───────────┬───────────┘
                    │
            ┌───────▼────────┐
            │ ContentExtractor│
            │   (AI-based)   │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │ ChangeDetector │
            └───────┬────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
   ┌────▼─────┐          ┌──────▼──────┐
   │Monitored │          │ Scheduled   │
   │  Items   │          │   Posts     │
   └──────────┘          └─────────────┘
```

---

## 🗄️ Модели данных

### 1. ContentSource (Источники контента)

Источники для мониторинга:

```python
{
    "id": 1,
    "user_id": 123,
    "name": "Новостной сайт",
    "description": "Мониторинг новостей о технологиях",
    "source_type": "website",  # website | rss | news_api | social
    "url": "https://example.com/news",
    "extraction_method": "ai",  # ai | selectors | rss
    
    # Фильтры
    "keywords": ["AI", "технологии"],
    "exclude_keywords": ["спорт", "политика"],
    "categories": ["tech", "business"],
    
    # Автопостинг
    "auto_post_enabled": true,
    "post_delay_minutes": 30,
    "post_template": "{title}\n\n{description}\n\n{url}",
    "auto_posting_rule_id": 5,
    
    # Расписание
    "check_interval_minutes": 60,
    "next_check_at": "2024-01-15T10:00:00Z",
    "last_check_at": "2024-01-15T09:00:00Z",
    "last_check_status": "success",
    
    # Статистика
    "total_checks": 100,
    "total_items_found": 50,
    "total_items_new": 25,
    "total_posts_created": 20
}
```

### 2. MonitoredItem (Найденные элементы)

Контент найденный системой мониторинга:

```python
{
    "id": 1,
    "source_id": 1,
    "user_id": 123,
    "external_id": "https://example.com/article-1",
    "title": "Новая технология AI",
    "content": "Полный текст статьи...",
    "summary": "Краткое описание...",
    "url": "https://example.com/article-1",
    "image_url": "https://example.com/image.jpg",
    "author": "Иван Иванов",
    "published_at": "2024-01-15T09:30:00Z",
    
    # Статус обработки
    "status": "new",  # new | approved | posted | ignored | duplicate
    
    # AI анализ
    "relevance_score": 0.85,
    "ai_summary": "AI-сгенерированное резюме",
    "ai_sentiment": "positive",
    "ai_category": "technology",
    "ai_keywords": ["AI", "innovation"],
    
    # Связи
    "content_id": "uuid-content",
    "scheduled_post_id": 10
}
```

### 3. SourceCheckHistory (История проверок)

```python
{
    "id": 1,
    "source_id": 1,
    "checked_at": "2024-01-15T09:00:00Z",
    "items_found": 10,
    "items_new": 3,
    "items_duplicate": 7,
    "items_posted": 2,
    "status": "success",
    "execution_time_ms": 2500
}
```

---

## 🔌 API Endpoints

### Управление источниками

#### **POST /api/v1/content-sources**
Создание нового источника контента

```bash
curl -X POST https://api.example.com/api/v1/content-sources \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech News RSS",
    "source_type": "rss",
    "url": "https://example.com/rss.xml",
    "keywords": ["AI", "machine learning"],
    "auto_post_enabled": true,
    "check_interval_minutes": 30
  }'
```

#### **GET /api/v1/content-sources**
Получение списка источников

```bash
curl -X GET https://api.example.com/api/v1/content-sources \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Параметры:
- `source_type` - фильтр по типу (website, rss)
- `is_active` - фильтр по активности (true/false)

#### **GET /api/v1/content-sources/{id}**
Получение информации об источнике

#### **PUT /api/v1/content-sources/{id}**
Обновление источника

#### **DELETE /api/v1/content-sources/{id}**
Удаление источника

### Работа с найденным контентом

#### **GET /api/v1/content-sources/{id}/items**
Получение элементов из источника

Параметры:
- `status` - фильтр по статусу (new, approved, posted, ignored)
- `limit` - количество элементов (по умолчанию 100)

#### **GET /api/v1/content-sources/items/new**
Получение новых необработанных элементов

Параметры:
- `limit` - количество элементов (по умолчанию 50)

#### **POST /api/v1/content-sources/items/{id}/approve**
Утверждение элемента для публикации

#### **POST /api/v1/content-sources/items/{id}/ignore**
Игнорирование элемента

---

## 🚀 Примеры использования

### Пример 1: Мониторинг RSS ленты

```json
POST /api/v1/content-sources
{
  "name": "Хабр - Новости AI",
  "description": "Автоматический мониторинг статей об AI на Хабре",
  "source_type": "rss",
  "url": "https://habr.com/ru/rss/hub/artificial_intelligence/all/",
  "extraction_method": "rss",
  "keywords": ["GPT", "нейросети", "машинное обучение"],
  "exclude_keywords": ["реклама"],
  "auto_post_enabled": true,
  "post_delay_minutes": 60,
  "post_template": "📰 Новая статья на Хабре\n\n{title}\n\n{summary}\n\nЧитать: {url}",
  "check_interval_minutes": 30
}
```

**Что происходит:**
1. WebCrawlerWorker проверяет RSS каждые 30 минут
2. Находит новые статьи с ключевыми словами
3. Создает MonitoredItem для каждой статьи
4. Если auto_post_enabled=true, создает отложенный пост через 60 минут
5. Пост публикуется автоматически в указанное время

---

### Пример 2: Мониторинг сайта с промо-акциями

```json
POST /api/v1/content-sources
{
  "name": "Промо-акции на сайте курсов",
  "description": "Отслеживание специальных предложений",
  "source_type": "website",
  "url": "https://courses-example.com/promotions",
  "extraction_method": "ai",
  "keywords": ["скидка", "акция", "промо"],
  "auto_post_enabled": true,
  "post_delay_minutes": 0,
  "post_template": "🔥 Специальное предложение!\n\n{title}\n\n{summary}\n\nПодробнее: {url}",
  "check_interval_minutes": 60
}
```

**Что происходит:**
1. WebCrawlerWorker загружает страницу каждый час
2. Вычисляет hash контента для определения изменений
3. Если контент изменился, использует AI (GPT-4) для извлечения:
   - Заголовка акции
   - Описания
   - Оценки релевантности
   - Тональности (positive/negative/neutral)
4. Если найдена промо-акция (relevance_score >= 0.5), создает пост
5. Пост публикуется немедленно (post_delay_minutes=0)

---

### Пример 3: Мониторинг блога с селекторами

```json
POST /api/v1/content-sources
{
  "name": "Корпоративный блог компании",
  "source_type": "website",
  "url": "https://company.com/blog",
  "extraction_method": "ai",
  "config": {
    "selectors": {
      "articles": ".blog-post",
      "title": "h2.title",
      "content": ".post-content"
    }
  },
  "categories": ["company_news", "product_updates"],
  "auto_post_enabled": true,
  "check_interval_minutes": 120
}
```

---

## 🧠 AI-based Content Extraction

### Как работает AI извлечение

1. **Загрузка страницы** → HTML контент
2. **Очистка HTML** → Удаление скриптов, стилей
3. **Формирование промпта** для GPT-4:

```text
Проанализируй HTML страницы и извлеки структурированную информацию.

URL: https://example.com/article

HTML:
<article>...</article>

Извлеки следующую информацию в формате JSON:
{
  "title": "Заголовок статьи",
  "content": "Полный текст",
  "summary": "Краткое описание (2-3 предложения)",
  "is_promotion": true/false,
  "relevance_score": 0.0-1.0,
  "sentiment": "positive/negative/neutral"
}
```

4. **Обработка ответа** → Структурированные данные
5. **Создание MonitoredItem**

### Преимущества AI-based extraction

✅ **Не требует CSS селекторов** - работает на любых сайтах
✅ **Умное извлечение** - понимает структуру контента
✅ **Оценка релевантности** - фильтрует нерелевантный контент
✅ **Определение тональности** - positive/negative/neutral
✅ **Категоризация** - автоматически определяет категорию

---

## 🔍 Change Detection (Определение новизны)

### Метод 1: Hash-based

```python
new_hash = md5(content)
if new_hash != old_snapshot_hash:
    # Контент изменился
```

**Плюсы:**
- Быстро
- Точно определяет любые изменения

**Минусы:**
- Не видит где именно изменения
- Чувствительно к незначительным изменениям (даты, счетчики)

### Метод 2: Structural Comparison

```python
# Сравнение структурированных данных
old_items = extract_items(old_html)
new_items = extract_items(new_html)

new_articles = [item for item in new_items if item not in old_items]
```

**Плюсы:**
- Видит конкретные новые элементы
- Игнорирует незначительные изменения

**Минусы:**
- Медленнее hash-based
- Требует правильной структуры

### Метод 3: AI Diff (Будущая функция)

```python
prompt = f"""
Compare OLD and NEW versions of the page.
Identify NEW content that appeared.

OLD: {old_snapshot}
NEW: {new_content}
"""
```

---

## ⚙️ Конфигурация

### Переменные окружения

```bash
# OpenAI для AI extraction
OPENAI_API_KEY=sk-...

# Отключение workers (для тестов)
DISABLE_WORKERS=false
```

### Настройки WebCrawlerWorker

```python
# В app.py
web_crawler_worker = WebCrawlerWorker(
    check_interval=60  # Проверка каждые 60 секунд
)
```

---

## 📊 Мониторинг и логи

### Логи WebCrawlerWorker

```log
2024-01-15 10:00:00 - WebCrawlerWorker - INFO - WebCrawlerWorker initialized with check_interval=60s
2024-01-15 10:00:00 - WebCrawlerWorker - INFO - WebCrawlerWorker started
2024-01-15 10:00:00 - WebCrawlerWorker - INFO - WebCrawlerWorker main loop started
2024-01-15 10:01:00 - WebCrawlerWorker - INFO - Found 3 sources to check
2024-01-15 10:01:00 - WebCrawlerWorker - INFO - Checking source: 1 - Tech News (rss)
2024-01-15 10:01:02 - WebCrawlerWorker - INFO - RSS source 1: found 10 items
2024-01-15 10:01:03 - WebCrawlerWorker - INFO - Source 1 checked successfully: 3 new items
2024-01-15 10:01:03 - WebCrawlerWorker - INFO - Created scheduled post 15 from monitored item 25
```

### Метрики

```python
# Статистика источника
GET /api/v1/content-sources/{id}

{
  "total_checks": 100,        # Всего проверок
  "total_items_found": 50,    # Найдено элементов
  "total_items_new": 25,      # Новых элементов
  "total_posts_created": 20,  # Создано постов
  "last_check_status": "success",
  "last_check_at": "2024-01-15T10:00:00Z"
}
```

---

## 🧪 Тестирование

### 1. Создание тестового RSS источника

```bash
curl -X POST http://localhost:8080/api/v1/content-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test RSS Feed",
    "source_type": "rss",
    "url": "https://news.ycombinator.com/rss",
    "auto_post_enabled": false,
    "check_interval_minutes": 5
  }'
```

### 2. Проверка найденных элементов

```bash
# Получить ID источника из ответа выше
SOURCE_ID=1

# Проверить найденные элементы через 5+ минут
curl -X GET "http://localhost:8080/api/v1/content-sources/$SOURCE_ID/items" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Создание website источника с AI

```bash
curl -X POST http://localhost:8080/api/v1/content-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI Blog",
    "source_type": "website",
    "url": "https://openai.com/blog",
    "extraction_method": "ai",
    "keywords": ["GPT", "ChatGPT"],
    "auto_post_enabled": false,
    "check_interval_minutes": 60
  }'
```

---

## 🔧 Troubleshooting

### Проблема: Worker не запускается

**Решение:**
1. Проверьте логи: `tail -f logs/app.log`
2. Убедитесь что `DISABLE_WORKERS=false`
3. Проверьте что OpenAI API key установлен

### Проблема: AI extraction не работает

**Решение:**
1. Проверьте `OPENAI_API_KEY` в `.env`
2. Проверьте баланс OpenAI аккаунта
3. Логи покажут ошибки: `grep "OpenAI" logs/app.log`

### Проблема: Не находит новые элементы

**Решение:**
1. Проверьте `next_check_at` источника
2. Убедитесь что `is_active=true`
3. Проверьте фильтры `keywords` / `exclude_keywords`
4. Посмотрите историю проверок: `GET /api/v1/content-sources/{id}/history`

### Проблема: Много дубликатов

**Решение:**
1. Система автоматически определяет дубликаты по `external_id` или `url`
2. Дубликаты получают статус `duplicate`
3. Проверьте логику в `check_duplicate()` метода

---

## 🚦 Production Checklist

- [ ] Установить `OPENAI_API_KEY` в production окружении
- [ ] Настроить правильные `check_interval_minutes` для каждого источника
- [ ] Добавить мониторинг логов WebCrawlerWorker
- [ ] Настроить алерты на ошибки в source_check_history
- [ ] Оптимизировать интервалы проверки (не чаще чем нужно)
- [ ] Добавить rate limiting для внешних запросов
- [ ] Настроить User-Agent для crawler запросов
- [ ] Добавить retry логику для failed checks
- [ ] Мониторинг OpenAI usage и costs

---

## 📝 TODO (Будущие улучшения)

- [ ] Поддержка JavaScript-rendered сайтов (Selenium/Playwright)
- [ ] AI Diff для более точного определения изменений
- [ ] Webhooks для уведомлений о новом контенте
- [ ] Bulk operations для источников
- [ ] Экспорт/импорт конфигураций источников
- [ ] Dashboard для аналитики источников
- [ ] Machine Learning для улучшения relevance_score
- [ ] Поддержка Social Media API (Twitter, Facebook, LinkedIn)

---

## 🤝 Интеграция с существующими компонентами

### С AutoPostingWorker
- WebCrawler создает MonitoredItems
- При `auto_post_enabled=true` создаются ScheduledPosts
- AutoPostingWorker/ScheduledPostsWorker публикуют их по расписанию

### С ContentOrchestrator
- Можно создавать ContentPiece из MonitoredItem
- AI агенты могут улучшать контент перед публикацией

### С Social Media Integrations
- ScheduledPosts публикуются через Telegram/Instagram/Twitter API
- Используются существующие интеграции

---

## 📄 Связанные документы

- `SCHEDULED_POSTS_UI_GUIDE.md` - Интеграция UI для отложенных постов
- `WORKERS_README.md` - Документация по background workers
- `API_STRUCTURE.md` - Общая структура API

---

**Дата создания:** 2024-01-15  
**Версия:** 1.0.0  
**Автор:** Content Curator Team

