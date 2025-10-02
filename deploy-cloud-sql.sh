#!/bin/bash
# ==============================================================================
# Cloud Run Deployment with Cloud SQL PostgreSQL
# ==============================================================================
# Деплой приложения с подключением к Cloud SQL через Unix Socket
# ==============================================================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# CONFIGURATION
# ==============================================================================

PROJECT_ID="content-curator-1755119514"
SERVICE_NAME="content-curator"
REGION="us-central1"
CLOUD_SQL_CONNECTION="content-curator-1755119514:us-central1:content-curator-db"
ENV_FILE=".env"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Cloud Run Deployment with Cloud SQL PostgreSQL          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==============================================================================
# ПРОВЕРКА ФАЙЛА .env
# ==============================================================================

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ ОШИБКА: Файл .env не найден!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Файл .env найден${NC}"

# ==============================================================================
# ЗАГРУЗКА ПЕРЕМЕННЫХ ИЗ .env
# ==============================================================================

echo -e "${YELLOW}📋 Загрузка переменных окружения...${NC}"

set -a
source "$ENV_FILE"
set +a

# Проверка обязательных переменных
REQUIRED_VARS=("ENVIRONMENT" "DB_HOST" "DB_NAME" "DB_USER" "DB_PASSWORD" "APP_SECRET_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ ОШИБКА: Отсутствуют обязательные переменные:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${RED}   - $var${NC}"
    done
    exit 1
fi

echo -e "${GREEN}✅ Все обязательные переменные заполнены${NC}"
echo ""

# ==============================================================================
# ПОКАЗЫВАЕМ КОНФИГУРАЦИЮ (БЕЗ ПАРОЛЕЙ)
# ==============================================================================

echo -e "${YELLOW}📊 Конфигурация деплоя:${NC}"
echo "  Project ID:          $PROJECT_ID"
echo "  Service:             $SERVICE_NAME"
echo "  Region:              $REGION"
echo "  Environment:         $ENVIRONMENT"
echo "  Cloud SQL Instance:  $CLOUD_SQL_CONNECTION"
echo "  DB Name:             $DB_NAME"
echo "  DB User:             $DB_USER"
echo "  DB Password:         ********** (скрыт)"
echo "  Secret Key:          ********** (скрыт)"
echo ""

# ==============================================================================
# ПОДТВЕРЖДЕНИЕ ДЕПЛОЯ
# ==============================================================================

echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Деплой изменит работающий сервис!${NC}"
echo -e "${YELLOW}   - Время простоя: ~30-60 секунд${NC}"
echo -e "${YELLOW}   - Приложение переключится на Cloud SQL${NC}"
echo ""
read -p "Продолжить деплой? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy](es)?$ ]]; then
    echo -e "${RED}❌ Деплой отменен${NC}"
    exit 1
fi

# ==============================================================================
# ДЕПЛОЙ В CLOUD RUN
# ==============================================================================

echo -e "${GREEN}🚀 Начинаем деплой в Cloud Run...${NC}"
echo ""

# Формируем env-vars строку
ENV_VARS="ENVIRONMENT=${ENVIRONMENT}"
ENV_VARS="${ENV_VARS},DB_HOST=${DB_HOST}"
ENV_VARS="${ENV_VARS},DB_PORT=${DB_PORT:-5432}"
ENV_VARS="${ENV_VARS},DB_NAME=${DB_NAME}"
ENV_VARS="${ENV_VARS},DB_USER=${DB_USER}"
ENV_VARS="${ENV_VARS},DB_PASSWORD=${DB_PASSWORD}"
ENV_VARS="${ENV_VARS},APP_SECRET_KEY=${APP_SECRET_KEY}"
ENV_VARS="${ENV_VARS},FLASK_ENV=${FLASK_ENV:-production}"
ENV_VARS="${ENV_VARS},FLASK_DEBUG=${FLASK_DEBUG:-False}"
ENV_VARS="${ENV_VARS},DEBUG_MODE=${DEBUG_MODE:-False}"
ENV_VARS="${ENV_VARS},API_HOST=${API_HOST:-0.0.0.0}"
ENV_VARS="${ENV_VARS},API_PORT=${API_PORT:-8080}"

# Добавляем опциональные переменные если они есть
[ ! -z "$OPENAI_API_KEY" ] && ENV_VARS="${ENV_VARS},OPENAI_API_KEY=${OPENAI_API_KEY}"
[ ! -z "$YOOKASSA_SHOP_ID" ] && ENV_VARS="${ENV_VARS},YOOKASSA_SHOP_ID=${YOOKASSA_SHOP_ID}"
[ ! -z "$YOOKASSA_SECRET_KEY" ] && ENV_VARS="${ENV_VARS},YOOKASSA_SECRET_KEY=${YOOKASSA_SECRET_KEY}"

echo -e "${BLUE}🔧 Добавляем Cloud SQL connector...${NC}"

# Выполняем деплой с Cloud SQL connection
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "$ENV_VARS" \
  --add-cloudsql-instances "$CLOUD_SQL_CONNECTION" \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# ==============================================================================
# ПРОВЕРКА РЕЗУЛЬТАТА
# ==============================================================================

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          ✅ ДЕПЛОЙ УСПЕШНО ЗАВЕРШЕН!                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Получаем URL сервиса
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
      --project "$PROJECT_ID" \
      --region "$REGION" \
      --format "value(status.url)")
    
    echo -e "${GREEN}🌐 URL сервиса:${NC}"
    echo "   $SERVICE_URL"
    echo ""
    echo -e "${GREEN}🔍 Проверьте работу Cloud SQL:${NC}"
    echo ""
    echo -e "${YELLOW}1. Проверить подключение к БД:${NC}"
    echo '   gcloud logging read '"'"'resource.type=cloud_run_revision \'
    echo '     AND resource.labels.service_name=content-curator \'
    echo '     AND textPayload:"Database connection established"'"'"' \'
    echo '     --limit=1 --project='"$PROJECT_ID"
    echo ""
    echo -e "${YELLOW}2. Проверить создание таблиц:${NC}"
    echo '   gcloud logging read '"'"'resource.type=cloud_run_revision \'
    echo '     AND resource.labels.service_name=content-curator \'
    echo '     AND textPayload:"Database tables created"'"'"' \'
    echo '     --limit=1 --project='"$PROJECT_ID"
    echo ""
    echo -e "${YELLOW}3. Тестовая регистрация:${NC}"
    echo "   curl -X POST $SERVICE_URL/auth/register \\"
    echo '     -H "Content-Type: application/json" \'
    echo '     -d '"'"'{"email":"test@example.com","username":"testuser","password":"TestPassword123"}'"'"
    echo ""
    echo -e "${YELLOW}4. Проверить дубликат (должна быть ошибка):${NC}"
    echo "   curl -X POST $SERVICE_URL/auth/register \\"
    echo '     -H "Content-Type: application/json" \'
    echo '     -d '"'"'{"email":"test@example.com","username":"testuser2","password":"TestPassword123"}'"'"
    echo ""
    echo -e "${GREEN}📋 Cloud SQL Credentials сохранены в .env${NC}"
    echo -e "${RED}⚠️  НЕ КОММИТИТЬ .env в Git!${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              ❌ ОШИБКА ПРИ ДЕПЛОЕ!                        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Для отката к SQLite запустите: ./rollback-to-sqlite.sh"
    exit 1
fi

