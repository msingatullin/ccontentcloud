#!/bin/bash
# ==============================================================================
# Cloud Run Deployment Script with PostgreSQL
# ==============================================================================
# ИСПОЛЬЗОВАНИЕ:
#   1. Создайте .env файл на основе .env.example
#   2. Заполните все необходимые переменные
#   3. Запустите: ./deploy-with-postgres.sh
#
# ТРЕБОВАНИЯ:
#   - gcloud CLI установлен и настроен
#   - .env файл с настройками базы данных
#   - Права на deploy в проект content-curator-1755119514
# ==============================================================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================================================
# CONFIGURATION
# ==============================================================================

PROJECT_ID="content-curator-1755119514"
SERVICE_NAME="content-curator"
REGION="us-central1"
ENV_FILE=".env"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Cloud Run Deployment with PostgreSQL Configuration      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==============================================================================
# ПРОВЕРКА ФАЙЛА .env
# ==============================================================================

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ ОШИБКА: Файл .env не найден!${NC}"
    echo ""
    echo "Создайте .env файл на основе .env.example:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Заполните реальными значениями"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Файл .env найден${NC}"

# ==============================================================================
# ЗАГРУЗКА ПЕРЕМЕННЫХ ИЗ .env
# ==============================================================================

echo -e "${YELLOW}📋 Загрузка переменных окружения...${NC}"

# Загружаем переменные
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
    echo ""
    echo "Проверьте файл .env и заполните все необходимые переменные."
    exit 1
fi

echo -e "${GREEN}✅ Все обязательные переменные заполнены${NC}"
echo ""

# ==============================================================================
# ПОКАЗЫВАЕМ КОНФИГУРАЦИЮ (БЕЗ ПАРОЛЕЙ)
# ==============================================================================

echo -e "${YELLOW}📊 Конфигурация деплоя:${NC}"
echo "  Project ID:     $PROJECT_ID"
echo "  Service:        $SERVICE_NAME"
echo "  Region:         $REGION"
echo "  Environment:    $ENVIRONMENT"
echo "  DB Host:        $DB_HOST"
echo "  DB Name:        $DB_NAME"
echo "  DB User:        $DB_USER"
echo "  DB Password:    ********** (скрыт)"
echo "  Secret Key:     ********** (скрыт)"
echo ""

# ==============================================================================
# ПОДТВЕРЖДЕНИЕ ДЕПЛОЯ
# ==============================================================================

echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Деплой изменит работающий сервис!${NC}"
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
[ ! -z "$STABILITY_API_KEY" ] && ENV_VARS="${ENV_VARS},STABILITY_API_KEY=${STABILITY_API_KEY}"
[ ! -z "$UNSPLASH_API_KEY" ] && ENV_VARS="${ENV_VARS},UNSPLASH_API_KEY=${UNSPLASH_API_KEY}"

# Выполняем деплой
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "$ENV_VARS" \
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
    echo -e "${GREEN}║              ✅ ДЕПЛОЙ УСПЕШНО ЗАВЕРШЕН!                  ║${NC}"
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
    echo -e "${GREEN}🔍 Проверьте работу:${NC}"
    echo "   Health: $SERVICE_URL/health"
    echo "   Swagger: $SERVICE_URL/api/docs/"
    echo "   Register: $SERVICE_URL/auth/register"
    echo ""
    echo -e "${YELLOW}📋 Следующие шаги:${NC}"
    echo "   1. Проверьте логи: gcloud logging read --project=$PROJECT_ID"
    echo "   2. Проверьте подключение к БД в логах"
    echo "   3. Попробуйте зарегистрировать пользователя"
    echo ""
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              ❌ ОШИБКА ПРИ ДЕПЛОЕ!                        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Проверьте логи ошибок выше."
    exit 1
fi

