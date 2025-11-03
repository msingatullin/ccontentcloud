# Интеграция с Telegram Bot API

## Архитектура

**ОДИН БОТ → МНОГО КАНАЛОВ**

Используется единый бот (@content4ubot), который клиенты добавляют администратором в свои каналы.

### Как это работает:

```
TELEGRAM_BOT_TOKEN (переменная окружения)
         ↓
TelegramChannelService
         ↓
PublisherAgent._publish_to_telegram_user_channel()
         ↓
POST https://api.telegram.org/bot{TOKEN}/sendMessage
         ↓
Telegram Channel (клиента)
```

## Изменения в коде

### 1. TelegramChannelService.send_message()

**Новый метод** для прямой отправки через Bot API:

```python
async def send_message(self, chat_id: str, text: str, 
                      parse_mode: str = "HTML",
                      disable_web_page_preview: bool = False) -> dict
```

**Возвращает:**
```python
{
    "success": bool,
    "data": dict,  # Telegram message object если успешно
    "error": str   # Сообщение об ошибке если неуспешно
}
```

**Использует:**
- `httpx.AsyncClient` для HTTP запросов
- `self.bot_token` из `TELEGRAM_BOT_TOKEN` env variable
- `https://api.telegram.org/bot{TOKEN}/sendMessage`

### 2. PublisherAgent._publish_to_telegram_user_channel()

**Изменения:**

**БЫЛО (TelegramMCP):**
```python
# Проверяем доступность TelegramMCP
if self.telegram_mcp is None:
    logger.error("TelegramMCP недоступен")
    return PublicationResult(success=False, ...)

# Отправляем через TelegramMCP
result = await self.telegram_mcp.send_message(
    text=message_text,
    chat_id=channel.chat_id
)

if result.success:
    message_data = result.data
    ...
```

**СТАЛО (Bot API):**
```python
# Отправляем через TelegramChannelService (прямо через Bot API)
result = await service.send_message(
    chat_id=channel.chat_id,
    text=message_text,
    parse_mode="HTML",
    disable_web_page_preview=False
)

if result["success"]:
    message_data = result["data"]
    ...
```

### 3. PublisherAgent._publish_to_telegram()

**Логика роутинга:**

```python
async def _publish_to_telegram(self, content, schedule_time=None, 
                               user_id=None, account_id=None):
    # Если указан user_id - публикуем в канал пользователя через Bot API
    if user_id:
        return await self._publish_to_telegram_user_channel(
            content, user_id, account_id, schedule_time
        )
    
    # Иначе - fallback (для обратной совместимости)
    logger.warning("user_id не указан, используем fallback")
    return await self._publish_to_telegram_fallback(content, schedule_time)
```

## Настройка

### 1. Переменная окружения

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

Или в `.env`:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Создание бота

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен и добавьте в `TELEGRAM_BOT_TOKEN`

### 3. Подключение канала

**Для клиента:**

1. Создайте Telegram канал (если еще нет)
2. Добавьте бота @content4ubot в администраторы канала
3. Дайте боту право "Публикация сообщений"
4. В приложении добавьте канал через API:

```bash
POST /api/v1/telegram/channels
{
  "channelLink": "https://t.me/mychannel",  # или @mychannel
  "channelName": "My Channel"
}
```

**API автоматически:**
- Проверит что бот добавлен в канал
- Проверит права администратора
- Сохранит channel в БД с `is_verified=true`

### 4. Публикация

Когда создается контент с `platforms: ["telegram"]`:

```
ContentOrchestrator
  ↓
PublisherAgent.execute_task()
  ↓
_publish_to_telegram(user_id=5)  # user_id передается из workflow
  ↓
_publish_to_telegram_user_channel(user_id=5)
  ↓
TelegramChannelService.send_message(chat_id=channel.chat_id)
  ↓
POST api.telegram.org/bot{TOKEN}/sendMessage
```

## База данных

### Таблица `telegram_channels`

```sql
CREATE TABLE telegram_channels (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,           -- Владелец канала
  channel_name VARCHAR(255),          -- Название для UI
  channel_username VARCHAR(100),      -- @username канала
  chat_id VARCHAR(100) NOT NULL,      -- ID для Bot API (-1001234567890)
  channel_title VARCHAR(255),         -- Реальное название из Telegram
  channel_type VARCHAR(50),           -- "channel", "supergroup"
  is_verified BOOLEAN DEFAULT 0,      -- Бот - админ с правами?
  is_active BOOLEAN DEFAULT 1,        -- Активен ли канал
  is_default BOOLEAN DEFAULT 0,       -- Канал по умолчанию?
  posts_count INTEGER DEFAULT 0,      -- Счетчик постов
  last_post_at DATETIME,              -- Дата последнего поста
  last_error TEXT,                    -- Последняя ошибка
  members_count INTEGER,              -- Кол-во подписчиков
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Flow создания и публикации

### 1. Фронтенд

```javascript
// content-curator-web/src/services/api.jsx
contentAPI.createContent({
  title: "Новый пост",
  platforms: ["telegram"],
  test_mode: false  // Реальная публикация
})
```

### 2. Backend API

```python
# app/api/routes.py
@content_ns.route('/create')
class ContentCreate(Resource):
    def post(self):
        # Получаем user_id из JWT токена
        user_id = current_user.get('user_id')
        
        # Добавляем в request
        request_data['user_id'] = user_id
        
        # Передаем в оркестратор
        orchestrator = UserOrchestratorFactory.get_orchestrator(user_id, db)
        result = await orchestrator.process_content_request(request_data)
```

### 3. Orchestrator

```python
# app/orchestrator/main_orchestrator.py
async def create_content_workflow(self, ..., user_id, test_mode):
    # Создает workflow
    workflow = self.workflow_engine.create_workflow(
        context={
            "user_id": user_id,
            "test_mode": test_mode
        }
    )
    
    # Добавляет задачи
    # Task 1: Create post for telegram (ChiefContentAgent)
    # Task 2: Publish post to telegram (PublisherAgent)
```

### 4. PublisherAgent

```python
# app/agents/publisher_agent.py
async def execute_task(self, task):
    user_id = task.context.get("user_id")  # 5
    test_mode = task.context.get("test_mode")  # False
    
    if test_mode:
        return await self._publish_test_content(...)
    else:
        return await self._publish_content(..., user_id=user_id)
```

### 5. TelegramChannelService

```python
# app/services/telegram_channel_service.py
async def send_message(self, chat_id, text):
    payload = {
        'chat_id': chat_id,      # -1001234567890
        'text': text,
        'parse_mode': "HTML"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.base_url}/sendMessage",  # https://api.telegram.org/bot{TOKEN}/sendMessage
            json=payload
        )
        
        result = response.json()
        if result.get('ok'):
            return {"success": True, "data": result['result']}
        else:
            return {"success": False, "error": result.get('description')}
```

## Отличия от TelegramMCP

| Параметр | TelegramMCP (старое) | Bot API (новое) |
|----------|---------------------|-----------------|
| Зависимости | MCP интеграция | Только httpx |
| Настройка | MCP конфиг файл | Env variable |
| Архитектура | Wrapper над Bot API | Прямо Bot API |
| Код | MCPResponse, MCPError | Простой dict |
| Сложность | Высокая | Низкая |

## Преимущества нового подхода

✅ **Простота** - нет MCP слоя  
✅ **Прозрачность** - прямые вызовы к Telegram API  
✅ **Меньше зависимостей** - только httpx  
✅ **Легче отладка** - видны все запросы  
✅ **Мультиарендность** - один бот, много каналов  

## Тестирование

### Test mode (без реальной отправки):

```bash
POST /api/v1/content/create
{
  "platforms": ["telegram"],
  "test_mode": true  # ← Важно!
}
```

Результат:
```json
{
  "publication": {
    "status": "test_mode",
    "message": "Контент готов к публикации (тестовый режим)",
    "telegram_preview": "📱 [Telegram] <содержание>"
  }
}
```

### Production mode (реальная отправка):

```bash
POST /api/v1/content/create
{
  "platforms": ["telegram"],
  "test_mode": false
}
```

**Требования:**
1. У пользователя должен быть подключен Telegram канал
2. Канал должен быть верифицирован (`is_verified=true`)
3. `TELEGRAM_BOT_TOKEN` должен быть установлен

## Проверка настройки

```bash
# 1. Проверить переменную окружения
echo $TELEGRAM_BOT_TOKEN

# 2. Проверить info о боте
python3 -c "
from app.services.telegram_channel_service import TelegramChannelService
from app.database.connection import get_db_session
import asyncio

db = get_db_session()
service = TelegramChannelService(db)

async def test():
    bot_info = await service.get_bot_info()
    print(f'Bot: @{bot_info.get(\"username\")}')
    print(f'Name: {bot_info.get(\"first_name\")}')

asyncio.run(test())
"

# 3. Проверить каналы пользователя
python3 -c "
from app.services.telegram_channel_service import TelegramChannelService
from app.database.connection import get_db_session

db = get_db_session()
service = TelegramChannelService(db)

channels = service.get_user_channels(user_id=5)
for ch in channels:
    print(f'{ch.channel_name}: verified={ch.is_verified}, active={ch.is_active}')
"
```

## Миграция

Если у вас было старое решение с TelegramMCP:

1. ✅ Код уже обновлен
2. ✅ Изменения обратно совместимы
3. ⚠️ Удалите MCP конфиг для Telegram (если был)
4. ✅ Убедитесь что `TELEGRAM_BOT_TOKEN` установлен
5. ✅ Проверьте что каналы добавлены в БД

## FAQ

**Q: Можно ли использовать разных ботов для разных пользователей?**  
A: Нет. Архитектура предполагает ОДИН БОТ для всех. Но каждый пользователь добавляет этого бота в СВОЙ канал.

**Q: Как отличить посты разных пользователей?**  
A: По `user_id` в БД. Каждый пост связан с `user_id`, а каждый канал принадлежит пользователю.

**Q: Что если бот не админ канала?**  
A: При добавлении канала API проверяет права и устанавливает `is_verified=false`. Публикация не будет работать до верификации.

**Q: Можно ли отправлять фото/видео?**  
A: Пока нет, только текст. Для медиа нужно добавить методы `send_photo()`, `send_video()` в `TelegramChannelService`.

**Q: Как работает test_mode?**  
A: В test_mode контент не отправляется в Telegram. PublisherAgent возвращает preview без реального вызова Bot API.

