#!/bin/bash
# Применение миграции token_usage к PostgreSQL на Cloud SQL

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Применение миграции token_usage к Cloud SQL             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Конфигурация
PROJECT_ID="content-curator-1755119514"
INSTANCE_NAME="content-curator-db"
REGION="us-central1"
DATABASE_NAME="content_curator"
CONNECTION_NAME="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"

MIGRATION_FILE="migrations/create_token_usage_table_postgres.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}❌ Файл миграции не найден: $MIGRATION_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Конфигурация:${NC}"
echo -e "  Project: ${PROJECT_ID}"
echo -e "  Instance: ${INSTANCE_NAME}"
echo -e "  Database: ${DATABASE_NAME}"
echo -e "  Region: ${REGION}"
echo ""

# Вариант 1: Через gcloud sql connect (требует подтверждения пароля)
echo -e "${YELLOW}🔐 Применение миграции через gcloud...${NC}"
echo ""

gcloud sql connect "${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --database="${DATABASE_NAME}" \
    --quiet < "${MIGRATION_FILE}"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Миграция успешно применена!${NC}"
    echo ""
    echo -e "${GREEN}Проверка:${NC}"
    echo "gcloud sql connect ${INSTANCE_NAME} --project=${PROJECT_ID} --database=${DATABASE_NAME}"
    echo "\\d token_usage"
else
    echo -e "${RED}❌ Ошибка при применении миграции${NC}"
    exit 1
fi








