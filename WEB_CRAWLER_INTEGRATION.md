# 🔗 Интеграция Web Crawler с системой автопостинга

## Обзор интеграции

Web Crawler интегрируется с существующей системой следующим образом:

```
┌──────────────────┐
│ WebCrawlerWorker │ ← Мониторит источники
└────────┬─────────┘
         │
         │ Находит новый контент
         ▼
┌────────────────┐
│ MonitoredItem  │ ← Сохраняет в БД
└────────┬───────┘
         │
         │ Если auto_post_enabled=true
         ▼
┌──────────────────┐
│ ScheduledPost    │ ← Создает отложенный пост
└────────┬─────────┘
         │
         │ По расписанию
         ▼
┌────────────────────┐
│ScheduledPostsWorker│ ← Публикует через API
└────────────────────┘
```

---

## 🎯 Workflow

### 1. Автоматическое создание постов из RSS

**Шаг 1:** Пользователь создает RSS источник

```bash
POST /api/v1/content-sources
{
  "name": "Tech News",
  "source_type": "rss",
  "url": "https://example.com/rss",
  "auto_post_enabled": true,
  "post_delay_minutes": 60,
  "auto_posting_rule_id": 5  # Ссылка на правило автопостинга
}
```

**Шаг 2:** WebCrawlerWorker проверяет RSS каждые N минут

```python
# В web_crawler_worker.py
async def _check_rss_source(self, source):
    feed_items = RSSParser.parse_feed(response.text)
    
    for feed_item in feed_items:
        # Создаем MonitoredItem
        monitored_item = MonitoredItemService.create_item(...)
        
        # Если auto_post_enabled, создаем пост
        if source.auto_post_enabled:
            self._create_scheduled_post(source, monitored_item, feed_item)
```

**Шаг 3:** Создается отложенный пост

```python
# Через post_delay_minutes минут
scheduled_time = now + timedelta(minutes=source.post_delay_minutes)

scheduled_post = ScheduledPostService.create_scheduled_post(
    user_id=source.user_id,
    platform='telegram',
    scheduled_time=scheduled_time,
    content_text=formatted_post,
    metadata={
        'source_id': source.id,
        'monitored_item_id': monitored_item.id
    }
)
```

**Шаг 4:** ScheduledPostsWorker публикует пост

```python
# Когда наступает scheduled_time
ScheduledPostsWorker → публикует через TelegramAPI/InstagramAPI/TwitterAPI
```

---

### 2. Мониторинг сайта с промо-акциями

**Сценарий:** На сайте курсов появляется новая промо-акция

**Шаг 1:** WebCrawlerWorker загружает страницу

```python
html = requests.get(source.url).text
```

**Шаг 2:** Определяет изменения

```python
changes = self.change_detector.detect_changes(html, source.last_snapshot_data)

if not changes.get('has_changes'):
    return  # Ничего нового
```

**Шаг 3:** AI извлекает контент

```python
extracted_data = await self.content_extractor.extract_from_html(html, source.url)

# Результат:
{
  "title": "Скидка 50% на все курсы",
  "summary": "Только до конца месяца...",
  "is_promotion": true,
  "relevance_score": 0.95,
  "sentiment": "positive"
}
```

**Шаг 4:** Если релевантно, создает пост

```python
if extracted_data.get('relevance_score', 0) >= 0.5:
    monitored_item = MonitoredItemService.create_item(...)
    
    if source.auto_post_enabled:
        self._create_scheduled_post(source, monitored_item, extracted_data)
```

---

## 🔄 Связь с AutoPostingRuleDB

ContentSource может быть связан с AutoPostingRule:

```python
# content_sources таблица
auto_posting_rule_id = Column(Integer, ForeignKey('auto_posting_rules.id'))
```

### Пример использования

```json
// 1. Создаем правило автопостинга
POST /api/v1/auto-posting/rules
{
  "name": "Daily Tech News",
  "schedule_type": "cron",
  "cron_expression": "0 9 * * *",
  "platforms": ["telegram"],
  "content_types": ["post"]
}

// Получаем rule_id = 5

// 2. Создаем источник контента с этим правилом
POST /api/v1/content-sources
{
  "name": "Tech RSS",
  "source_type": "rss",
  "url": "https://tech-news.com/rss",
  "auto_post_enabled": true,
  "auto_posting_rule_id": 5  // Связь с правилом
}
```

**Результат:**
- WebCrawler находит контент
- Создает ScheduledPost с учетом настроек из AutoPostingRule
- Использует platforms и content_types из правила

---

## 🛠️ Интеграция с ContentOrchestrator

MonitoredItems могут быть преобразованы в ContentPiece для обработки AI агентами:

```python
# Получаем MonitoredItem с высокой релевантностью
GET /api/v1/content-sources/items/new?limit=10

# Выбираем элемент для создания контента
POST /api/v1/content/create
{
  "text": monitored_item.summary,
  "title": monitored_item.title,
  "metadata": {
    "source": "web_crawler",
    "monitored_item_id": monitored_item.id,
    "original_url": monitored_item.url
  }
}

# ContentOrchestrator обрабатывает через AI агентов
# Улучшает текст, добавляет медиа, оптимизирует
```

---

## 📊 Workflow с утверждением пользователем

Для важного контента можно отключить автопостинг и требовать утверждения:

```json
POST /api/v1/content-sources
{
  "name": "Corporate Blog",
  "source_type": "website",
  "url": "https://company.com/blog",
  "auto_post_enabled": false  // Требует утверждения
}
```

**Workflow:**

1. WebCrawler находит новую статью → создает MonitoredItem со статусом "new"
2. UI показывает список новых элементов:
   ```bash
   GET /api/v1/content-sources/items/new
   ```
3. Пользователь проверяет и утверждает:
   ```bash
   POST /api/v1/content-sources/items/{id}/approve
   ```
4. Вручную создает пост или настраивает автопостинг

---

## 🔔 Уведомления о новом контенте

### Вариант 1: Через Telegram Bot

```python
# При нахождении нового релевантного контента
if monitored_item.relevance_score >= 0.8:
    telegram_bot.send_message(
        user.telegram_id,
        f"🆕 Найден новый контент:\n\n"
        f"{monitored_item.title}\n\n"
        f"Релевантность: {monitored_item.relevance_score}\n\n"
        f"Утвердить: /approve_{monitored_item.id}"
    )
```

### Вариант 2: WebSocket уведомления

```python
# Real-time уведомления в UI
socketio.emit('new_monitored_item', {
    'item_id': monitored_item.id,
    'title': monitored_item.title,
    'relevance_score': monitored_item.relevance_score
}, room=f'user_{user_id}')
```

---

## 🧩 Расширение: AI Content Generation

MonitoredItems → AI обработка → ScheduledPosts

```python
# Когда найден новый контент
monitored_item = MonitoredItemService.create_item(...)

# Отправляем в ContentOrchestrator для AI обработки
content_piece = await orchestrator.process_external_content(
    title=monitored_item.title,
    source_text=monitored_item.content,
    url=monitored_item.url,
    user_id=user_id
)

# AI агенты:
# 1. Улучшают текст
# 2. Генерируют изображение
# 3. Оптимизируют под платформу
# 4. Создают несколько вариантов

# Создаем отложенный пост
scheduled_post = ScheduledPostService.create_scheduled_post(
    content_id=content_piece.id,
    ...
)
```

---

## 📈 Метрики и аналитика

### Dashboard для источников контента

```python
GET /api/v1/content-sources/stats

{
  "total_sources": 10,
  "active_sources": 8,
  "total_items_today": 25,
  "posts_created_today": 15,
  "top_sources": [
    {
      "id": 1,
      "name": "Tech RSS",
      "items_found": 50,
      "posts_created": 20,
      "success_rate": 0.4
    }
  ]
}
```

### История проверок источника

```python
GET /api/v1/content-sources/{id}/history

[
  {
    "checked_at": "2024-01-15T10:00:00Z",
    "items_found": 10,
    "items_new": 3,
    "items_posted": 2,
    "status": "success",
    "execution_time_ms": 2500
  }
]
```

---

## 🎨 UI Components (для фронтенда)

### 1. Content Sources List

```jsx
<ContentSourcesList>
  <ContentSourceCard
    name="Tech News RSS"
    type="rss"
    status="active"
    stats={{
      totalChecks: 100,
      newItems: 25,
      postsCreated: 20
    }}
  />
</ContentSourcesList>
```

### 2. Monitored Items Feed

```jsx
<MonitoredItemsFeed>
  <MonitoredItemCard
    title="Новая технология AI"
    summary="..."
    relevanceScore={0.85}
    sentiment="positive"
    actions={['approve', 'ignore', 'view']}
  />
</MonitoredItemsFeed>
```

### 3. Source Configuration

```jsx
<SourceConfigForm>
  <URLInput />
  <KeywordsInput />
  <AutoPostToggle />
  <ScheduleSelector />
  <PostTemplateEditor />
</SourceConfigForm>
```

---

## 🔐 Permissions & Security

### Уровни доступа

1. **User** - может создавать/управлять своими источниками
2. **Team** - может делиться источниками с командой
3. **Admin** - может видеть все источники

### Rate Limiting

```python
# Ограничения на создание источников
MAX_SOURCES_PER_USER = {
    'free': 3,
    'pro': 10,
    'enterprise': 100
}

# Ограничения на частоту проверок
MIN_CHECK_INTERVAL_MINUTES = {
    'free': 60,
    'pro': 30,
    'enterprise': 5
}
```

---

## 🚀 Production Best Practices

### 1. Graceful Degradation

Если OpenAI API недоступен, fallback на простое извлечение:

```python
try:
    extracted = await self._call_openai(prompt)
except Exception as e:
    logger.warning(f"OpenAI unavailable, using fallback: {e}")
    extracted = self._fallback_extraction(html, url)
```

### 2. Circuit Breaker для внешних источников

```python
if source.consecutive_failures >= 5:
    source.is_active = False
    logger.error(f"Source {source.id} disabled after 5 failures")
```

### 3. Exponential Backoff

```python
if last_check_failed:
    next_check_interval = min(
        check_interval * 2,
        MAX_INTERVAL
    )
```

---

## 📝 Changelog интеграции

### v1.0.0 - Initial Implementation
- ✅ ContentSource, MonitoredItem, SourceCheckHistory модели
- ✅ WebCrawlerWorker
- ✅ ContentExtractor с AI
- ✅ ChangeDetector
- ✅ RSSParser
- ✅ API endpoints
- ✅ Интеграция с ScheduledPosts

### v1.1.0 - Planned
- 🔲 Selenium support для JS-rendered сайтов
- 🔲 Webhooks для real-time уведомлений
- 🔲 Bulk operations
- 🔲 Advanced filtering rules
- 🔲 Content deduplication across sources

---

**Автор:** Content Curator Team  
**Дата:** 2024-01-15

