# 🚨 ВАЖНО: Требуется Применение Миграции Token Usage

## ❌ Проблема

Endpoint `/api/v1/billing/usage/tokens` возвращает **ошибку 500 "Internal Server Error"**.

**Причина:** Таблица `token_usage` существует в **локальной SQLite БД**, но НЕ существует в **PostgreSQL на Cloud SQL**.

## ✅ Решение

Применить миграцию `create_token_usage_table_postgres.sql` к PostgreSQL на Cloud SQL.

---

## 📋 Вариант 1: Через Cloud Console (РЕКОМЕНДУЕТСЯ)

### Шаг 1: Открыть Cloud SQL в консоли
```
https://console.cloud.google.com/sql/instances/content-curator-db/overview?project=content-curator-1755119514
```

### Шаг 2: Перейти в Query Editor
1. В левом меню выбрать **"Query Editor"**
2. Выбрать базу данных: `content_curator`
3. Подключиться (используя IAM или пароль)

### Шаг 3: Скопировать и выполнить SQL
Открыть файл миграции:
```bash
cat /home/mikhail/content-curator-cloud/migrations/create_token_usage_table_postgres.sql
```

Скопировать весь SQL код и вставить в Query Editor, затем нажать **"Run"**.

---

## 📋 Вариант 2: Через gcloud CLI

### Требования
- Установлен `psql` клиент ✅
- Аутентифицирован в gcloud ✅
- Известен пароль PostgreSQL ❌ (не подошел пароль из .env)

### Команда
```bash
cd /home/mikhail/content-curator-cloud

# С правильным паролем (нужно узнать из Cloud Console)
export PGPASSWORD='ПРАВИЛЬНЫЙ_ПАРОЛЬ'

gcloud sql connect content-curator-db \
  --project=content-curator-1755119514 \
  --database=content_curator \
  --user=content_curator_user \
  < migrations/create_token_usage_table_postgres.sql
```

---

## 📋 Вариант 3: Через Cloud SQL Proxy

### Установка Cloud SQL Proxy
```bash
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy
```

### Запуск Cloud SQL Proxy
```bash
./cloud_sql_proxy \
  -instances=content-curator-1755119514:us-central1:content-curator-db=tcp:5432 \
  -credential_file=~/.config/gcloud/application_default_credentials.json &
```

### Применение миграции
```bash
export PGPASSWORD='ПРАВИЛЬНЫЙ_ПАРОЛЬ'

psql -h 127.0.0.1 -p 5432 \
  -U content_curator_user \
  -d content_curator \
  < migrations/create_token_usage_table_postgres.sql
```

---

## 🔍 Проверка после применения

### В Cloud Console Query Editor:
```sql
-- Проверить что таблица создана
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'token_usage'
ORDER BY ordinal_position;

-- Проверить индексы
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'token_usage';

-- Проверить количество записей
SELECT COUNT(*) FROM token_usage;
```

### Через API (после применения миграции):
```bash
# Должно вернуть пустую статистику (все нули), но без ошибки 500
curl -H "Authorization: eyJ..." \
  https://content-curator-1046574462613.us-central1.run.app/api/v1/billing/usage/tokens/summary
```

Ожидаемый ответ:
```json
{
  "success": true,
  "data": {
    "today": {
      "total_tokens": 0,
      "cost_rub": 0.0,
      "requests_count": 0
    },
    "this_month": {...},
    "all_time": {...}
  }
}
```

---

## 📊 Что делает эта миграция

Создает таблицу `token_usage` с полями:
- **user_id** - ID пользователя
- **agent_id** - Какой агент использовал токены
- **ai_provider** - openai, anthropic, huggingface
- **ai_model** - gpt-4, claude-3, dall-e-3
- **prompt_tokens, completion_tokens, total_tokens** - Использованные токены
- **cost_usd, cost_rub** - Стоимость
- **created_at** - Дата/время

И 8 индексов для быстрых запросов.

---

## ⚠️ Важно

После применения миграции:
1. ✅ Ошибка 500 на `/billing/usage/tokens` исчезнет
2. ✅ Все endpoints `/billing/usage/tokens/*` заработают
3. 🔄 Данные начнут накапливаться при работе с AI агентами

---

## 🆘 Если возникли проблемы

1. **Пароль не подходит** - сбросить пароль через Cloud Console:
   - SQL -> Instances -> content-curator-db -> Users -> content_curator_user -> Reset Password

2. **Нет доступа к Cloud Console** - попросить администратора GCP проекта применить миграцию

3. **Миграция уже применена** - проверить наличие таблицы: `\d token_usage` в psql









