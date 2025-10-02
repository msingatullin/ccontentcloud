#!/bin/bash
# ==============================================================================
# ЭКСТРЕННЫЙ ОТКАТ К SQLITE
# ==============================================================================
# Используется только в случае критических проблем с Cloud SQL
# Откатывает Cloud Run обратно к SQLite (dev режим)
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID="content-curator-1755119514"
SERVICE_NAME="content-curator"
REGION="us-central1"
CLOUD_SQL_CONNECTION="content-curator-1755119514:us-central1:content-curator-db"

echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║           ⚠️  ЭКСТРЕННЫЙ ОТКАТ К SQLITE                    ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Этот скрипт откатит приложение к SQLite!${NC}"
echo ""
echo "  ❌ Все новые данные в Cloud SQL будут недоступны"
echo "  ❌ Приложение будет работать в dev режиме"
echo "  ❌ При рестарте данные будут теряться"
echo ""
read -p "Вы уверены что хотите откатиться? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy](es)?$ ]]; then
    echo -e "${GREEN}✅ Откат отменен${NC}"
    exit 0
fi

echo -e "${YELLOW}🔄 Выполняю откат к SQLite...${NC}"
echo ""

# Откат Cloud Run к минимальной конфигурации
gcloud run services update "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --clear-env-vars \
  --set-env-vars "FLASK_ENV=production,FLASK_DEBUG=False,API_HOST=0.0.0.0,API_PORT=8080" \
  --remove-cloudsql-instances "$CLOUD_SQL_CONNECTION"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           ✅ ОТКАТ УСПЕШНО ВЫПОЛНЕН                       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}📋 Приложение вернулось к SQLite${NC}"
    echo ""
    echo -e "${YELLOW}🔍 Проверьте логи:${NC}"
    echo '   gcloud logging read '"'"'resource.type=cloud_run_revision \'
    echo '     AND resource.labels.service_name=content-curator \'
    echo '     AND textPayload:"Database connection"'"'"' \'
    echo '     --limit=5 --project='"$PROJECT_ID"
    echo ""
    echo -e "${RED}⚠️  Для возврата к Cloud SQL запустите: ./deploy-cloud-sql.sh${NC}"
else
    echo ""
    echo -e "${RED}❌ ОШИБКА ПРИ ОТКАТЕ!${NC}"
    exit 1
fi

