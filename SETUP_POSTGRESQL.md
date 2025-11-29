# 🚀 НАСТРОЙКА POSTGRESQL ДЛЯ CONTENT CURATOR

## 🎯 ПРОБЛЕМА КОТОРУЮ РЕШАЕМ

**Текущая ситуация:**
- ❌ Cloud Run использует SQLite (эфемерная БД)
- ❌ Все данные теряются при рестарте контейнера
- ❌ Пользователи не сохраняются между запусками
- ❌ Регистрация "работает", но данные пропадают

**Решение:**
- ✅ Подключить внешний PostgreSQL
- ✅ Постоянное хранение данных
- ✅ Работа в production режиме

---

## 📋 БЫСТРЫЙ СТАРТ (5 минут)

### Шаг 1: Создать бесплатную PostgreSQL базу данных

**Рекомендуем Supabase** (самый простой вариант):

1. Перейдите на https://supabase.com/
2. Создайте аккаунт (GitHub OAuth)
3. Создайте новый проект
4. Дождитесь инициализации (~2 минуты)
5. Перейдите в **Settings → Database**
6. Скопируйте Connection String в формате URI

**Пример Connection String:**
```
postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

**Из этой строки выделите:**
```
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.xxxxx
DB_PASSWORD=your-password-here
```

---

### Шаг 2: Создать .env файл

```bash
# Скопировать шаблон
cp .env.example .env

# Отредактировать файл
nano .env
```

**Минимальная конфигурация:**
```bash
ENVIRONMENT=production
APP_SECRET_KEY=your-random-secret-key-at-least-32-chars

DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.xxxxx
DB_PASSWORD=your-supabase-password
```

**💡 Как сгенерировать APP_SECRET_KEY:**
```bash
# Вариант 1: OpenSSL
openssl rand -base64 32

# Вариант 2: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### Шаг 3: Задеплоить в Cloud Run

```bash
# Сделать скрипт исполняемым (если еще не сделали)
chmod +x deploy-with-postgres.sh

# Запустить деплой
./deploy-with-postgres.sh
```

**Скрипт автоматически:**
- ✅ Проверит наличие всех переменных
- ✅ Покажет конфигурацию (без паролей)
- ✅ Задеплоит в Cloud Run с правильными env переменными
- ✅ Покажет URL для проверки

---

### Шаг 4: Проверить работу

```bash
# Проверить health endpoint
curl https://content-curator-1046574462613.us-central1.run.app/health

# Проверить логи подключения к БД
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND textPayload:\"Database connection established\"" \
  --limit=5 \
  --project=content-curator-1755119514

# Должно быть:
# "Database connection established: postgresql://..."
# А НЕ "sqlite:///..."
```

---

## 🔧 АЛЬТЕРНАТИВНЫЕ ХОСТИНГИ POSTGRESQL

### 1. Neon (https://neon.tech/)
```
✅ Бесплатный tier: 10GB
✅ Serverless PostgreSQL
✅ Автоматическое масштабирование
✅ Удобный UI

Connection String:
postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb
```

### 2. ElephantSQL (https://www.elephantsql.com/)
```
✅ Бесплатный tier: 20MB
✅ Простая настройка
⚠️ Ограничение по размеру БД

Connection String:
postgresql://user:password@fanny.db.elephantsql.com/dbname
```

### 3. Railway (https://railway.app/)
```
✅ $5 кредитов в месяц бесплатно
✅ Много сервисов, включая PostgreSQL
✅ Простой деплой

Connection String:
postgresql://postgres:password@containers-us-west-xx.railway.app:7453/railway
```

### 4. Cloud SQL (Google Cloud)
```
💰 Платный, но надежный
✅ Интеграция с Cloud Run
✅ Автоматические бэкапы
✅ High availability

Создание инстанса:
gcloud sql instances create content-curator-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1
```

---

## 🔍 ПРОВЕРКА ПОСЛЕ ДЕПЛОЯ

### 1. Проверить переменные окружения в Cloud Run

```bash
gcloud run services describe content-curator \
  --region=us-central1 \
  --project=content-curator-1755119514 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

**Должны увидеть:**
```yaml
env:
- name: ENVIRONMENT
  value: production
- name: DB_HOST
  value: your-postgres-host
- name: DB_NAME
  value: postgres
```

### 2. Проверить логи подключения к БД

```bash
gcloud logging read 'resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND textPayload:"Database connection established"' \
  --limit=3 \
  --project=content-curator-1755119514
```

**Правильный лог:**
```
Database connection established: postgresql://postgres:***@host:5432/postgres
```

**Неправильный лог (старый):**
```
Database connection established: sqlite:///./content_curator.db
```

### 3. Проверить создание таблиц

```bash
gcloud logging read 'resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND textPayload:"Database tables created successfully"' \
  --limit=1 \
  --project=content-curator-1755119514
```

### 4. Попробовать регистрацию через API

```bash
curl -X POST https://content-curator-1046574462613.us-central1.run.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePassword123"
  }'
```

**Ожидаемый ответ:**
```json
{
  "message": "Пользователь успешно зарегистрирован. Проверьте email для подтверждения.",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "username": "testuser",
    ...
  }
}
```

### 5. Проверить что пользователь сохранился

```bash
# Подключиться к БД через SQL клиент
psql "postgresql://user:password@host:5432/dbname"

# Выполнить запрос
SELECT id, email, username, is_verified, created_at FROM users;
```

---

## 🚨 TROUBLESHOOTING

### Проблема: "Cannot connect to database"

**Решение:**
1. Проверьте что PostgreSQL хост доступен из Cloud Run
2. Проверьте правильность credentials в .env
3. Проверьте что IP Cloud Run разрешен в PostgreSQL firewall

```bash
# Тест подключения из Cloud Run
gcloud logging read 'resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND severity>=ERROR \
  AND textPayload:"database"' \
  --limit=10 \
  --project=content-curator-1755119514
```

---

### Проблема: "Still using SQLite"

**Решение:**
1. Проверьте что `ENVIRONMENT=production` установлена
2. Проверьте что переменные попали в Cloud Run
3. Redeploy с правильными переменными

```bash
# Проверка env переменных
gcloud run services describe content-curator \
  --region=us-central1 \
  --project=content-curator-1755119514 \
  --format="get(spec.template.spec.containers[0].env)"
```

---

### Проблема: "Tables not created"

**Решение:**
```bash
# Проверить логи создания таблиц
gcloud logging read 'resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND textPayload:"create"' \
  --limit=20 \
  --project=content-curator-1755119514

# Если таблицы не создались, проверьте права пользователя PostgreSQL
```

---

## 📊 МОНИТОРИНГ

### Полезные команды для мониторинга

```bash
# Все логи сервиса (последние 50)
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator" \
  --limit=50 \
  --format="table(timestamp,textPayload)" \
  --project=content-curator-1755119514

# Только ошибки
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND severity>=ERROR" \
  --limit=20 \
  --project=content-curator-1755119514

# Auth логи
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=content-curator \
  AND textPayload:\"auth\"" \
  --limit=20 \
  --project=content-curator-1755119514
```

---

## ✅ CHECKLIST

После успешной настройки должно быть:

- [ ] .env файл создан и заполнен
- [ ] PostgreSQL БД создана и доступна
- [ ] Deploy выполнен успешно
- [ ] Логи показывают `postgresql://` а не `sqlite://`
- [ ] Таблицы созданы в БД
- [ ] Регистрация работает через API
- [ ] Пользователи сохраняются после рестарта
- [ ] Повторная регистрация с тем же email выдает ошибку

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/14/dialects/postgresql.html)
- [Supabase Documentation](https://supabase.com/docs)
- [Flask Configuration Best Practices](https://flask.palletsprojects.com/en/2.3.x/config/)

---

## 🆘 НУЖНА ПОМОЩЬ?

Если что-то не работает:

1. Проверьте логи Cloud Run
2. Проверьте подключение к PostgreSQL
3. Проверьте переменные окружения
4. Создайте issue с полными логами ошибок

