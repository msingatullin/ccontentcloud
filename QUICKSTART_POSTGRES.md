# ⚡ БЫСТРЫЙ СТАРТ: POSTGRESQL ЗА 5 МИНУТ

## 🎯 ЧТО МЫ ДЕЛАЕМ

Переключаем Cloud Run с эфемерной SQLite на постоянную PostgreSQL БД.

---

## 📋 ШАГ 1: СОЗДАТЬ POSTGRESQL БД (2 минуты)

### Используем Supabase (самый простой способ):

1. **Открыть:** https://supabase.com/
2. **Sign Up** → используйте GitHub аккаунт
3. **New Project** → придумайте имя и пароль
4. **Подождать** ~2 минуты пока БД создается ☕
5. **Settings → Database → Connection String** 
6. **Выбрать режим:** URI (не Transaction pooler)

**Пример Connection String:**
```
postgresql://postgres.abcdefgh:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

**Выделите из строки:**
```
Хост:    aws-0-us-east-1.pooler.supabase.com
Порт:    5432
БД:      postgres  
Юзер:    postgres.abcdefgh
Пароль:  ваш-пароль-который-придумали
```

---

## 📋 ШАГ 2: НАСТРОИТЬ .ENV (1 минута)

```bash
# Скопировать шаблон
cp .env.production.example .env

# Открыть редактор
nano .env
```

**Заполнить ТОЛЬКО эти поля:**

```bash
ENVIRONMENT=production

# Сгенерировать секретный ключ:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
APP_SECRET_KEY=ваш-сгенерированный-ключ-32-символа

# Из Supabase:
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.abcdefgh
DB_PASSWORD=ваш-supabase-пароль
```

**Сохранить:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 📋 ШАГ 3: ЗАДЕПЛОИТЬ (5 минут)

```bash
# Запустить деплой
./deploy-with-postgres.sh
```

**Скрипт спросит подтверждение:**
```
⚠️ ВНИМАНИЕ: Деплой изменит работающий сервис!
Продолжить деплой? (yes/no): 
```

**Ввести:** `yes`

**Дождаться окончания** (~5 минут)

---

## ✅ ШАГ 4: ПРОВЕРИТЬ ЧТО ВСЕ РАБОТАЕТ (1 минута)

### Проверка 1: Подключение к PostgreSQL

```bash
gcloud logging read 'resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND textPayload:"Database connection established"' \
  --limit=1 \
  --project=content-curator-1755119514
```

**Должно показать:**
```
✅ Database connection established: postgresql://postgres:***@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

**НЕ должно быть:**
```
❌ Database connection established: sqlite:///./content_curator.db
```

### Проверка 2: Таблицы созданы

```bash
gcloud logging read 'resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND textPayload:"Database tables created successfully"' \
  --limit=1 \
  --project=content-curator-1755119514
```

### Проверка 3: Регистрация работает

```bash
curl -X POST https://content-curator-1046574462613.us-central1.run.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123"
  }'
```

**Ожидаемый ответ:**
```json
{
  "message": "Пользователь успешно зарегистрирован...",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "username": "testuser"
  }
}
```

### Проверка 4: Повторная регистрация с тем же email

```bash
# Запустить ту же команду еще раз
curl -X POST https://content-curator-1046574462613.us-central1.run.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser2",
    "password": "TestPassword123"
  }'
```

**Должно вернуть:**
```json
{
  "error": "Пользователь с таким email уже существует"
}
```

**✅ ЕСЛИ ВСЕ ТАК - ВСЕ РАБОТАЕТ!**

---

## 🚨 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Проблема: "Cannot connect to database"

```bash
# Проверить логи ошибок
gcloud logging read 'resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND severity>=ERROR' \
  --limit=10 \
  --project=content-curator-1755119514
```

**Возможные причины:**
- ❌ Неправильный пароль PostgreSQL
- ❌ Неправильный хост/порт
- ❌ Supabase БД еще не готова (подождите 1-2 минуты)

**Решение:** Проверьте credentials в .env файле

---

### Проблема: "Still using SQLite"

```bash
# Проверить переменные окружения
gcloud run services describe content-curator \
  --region=us-central1 \
  --project=content-curator-1755119514 \
  --format="value(spec.template.spec.containers[0].env[?(@.name=='ENVIRONMENT')].value)"
```

**Должно вернуть:** `production`

**Если пусто:**
```bash
# Переменные не попали в Cloud Run, редеплой:
./deploy-with-postgres.sh
```

---

## 🎉 ГОТОВО!

После успешной настройки:
- ✅ Пользователи сохраняются навсегда
- ✅ Рестарты Cloud Run не удаляют данные
- ✅ Проверка дубликатов email работает
- ✅ Все инстансы видят одну БД

**Теперь можно работать! 🚀**

---

## 📚 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ

- **Полная документация:** `SETUP_POSTGRESQL.md`
- **Ответ разработчику:** `DEVELOPER_RESPONSE.md`
- **Deploy скрипт:** `deploy-with-postgres.sh`

---

## ⏱️ SUMMARY

| Шаг | Действие | Время |
|-----|----------|-------|
| 1 | Создать Supabase БД | 2 мин |
| 2 | Настроить .env | 1 мин |
| 3 | Задеплоить | 5 мин |
| 4 | Проверить | 1 мин |
| **Итого** | | **~10 минут** |

