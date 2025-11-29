#!/bin/bash

# Content Curator AI - Google Cloud Run Deployment Script
# Автор: Михаил
# Дата: $(date)

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_ID="content-curator-1755119514"  # Замените на ваш PROJECT_ID
REGION="us-central1"
SERVICE_NAME="content-curator"
IMAGE_NAME="gcr.io/${PROJECT_ID}/contentcurator"

echo -e "${BLUE}🚀 Запуск развертывания Content Curator AI на Google Cloud Run${NC}"
echo "=================================================="

# Проверка наличия gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI не установлен. Установите Google Cloud SDK${NC}"
    exit 1
fi

# Проверка аутентификации
echo -e "${YELLOW}🔐 Проверка аутентификации...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Не авторизован в gcloud. Выполните: gcloud auth login${NC}"
    exit 1
fi

# Установка проекта
echo -e "${YELLOW}📁 Установка проекта: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Включение необходимых API
echo -e "${YELLOW}🔧 Включение Cloud Run API...${NC}"
gcloud services enable run.googleapis.com

# Сборка Docker образа
echo -e "${YELLOW}🐳 Сборка Docker образа...${NC}"
docker build -t ${IMAGE_NAME} .

# Отправка образа в Container Registry
echo -e "${YELLOW}📤 Отправка образа в Container Registry...${NC}"
docker push ${IMAGE_NAME}

# Развертывание на Cloud Run
echo -e "${YELLOW}🚀 Развертывание на Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --set-env-vars "FLASK_ENV=production" \
    --set-env-vars "PYTHONUNBUFFERED=1"

# Получение URL сервиса
echo -e "${YELLOW}🔍 Получение URL сервиса...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo -e "${GREEN}✅ Развертывание завершено успешно!${NC}"
echo "=================================================="
echo -e "${BLUE}🌐 URL сервиса: ${SERVICE_URL}${NC}"
echo -e "${BLUE}🔍 Health check: ${SERVICE_URL}/health${NC}"
echo -e "${BLUE}📊 Мониторинг: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}${NC}"

# Тестирование health check
echo -e "${YELLOW}🧪 Тестирование health check...${NC}"
sleep 10  # Ждем запуска сервиса

if curl -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check прошел успешно${NC}"
else
    echo -e "${RED}❌ Health check не прошел${NC}"
fi

echo -e "${GREEN}🎉 Развертывание завершено!${NC}"
