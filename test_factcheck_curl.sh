#!/bin/bash

# Тест API для создания контента с фактчекингом через curl
# Проверяет работу ResearchFactCheckAgent через REST API

echo "🧪 Тестирование API создания контента с фактчекингом"
echo "=================================================="

# Конфигурация
API_BASE_URL="http://localhost:5000/api"
CONTENT_CREATE_URL="$API_BASE_URL/content/create"
WORKFLOW_STATUS_URL="$API_BASE_URL/workflow"
AGENTS_STATUS_URL="$API_BASE_URL/agents/status"

# Функция для форматированного вывода JSON
format_json() {
    echo "$1" | python3 -m json.tool 2>/dev/null || echo "$1"
}

# 1. Проверяем здоровье API
echo ""
echo "❤️ Проверка здоровья API:"
echo "------------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/health")
HEALTH_HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HEALTH_HTTP_CODE" = "200" ]; then
    echo "✅ API здоров"
    format_json "$HEALTH_BODY"
else
    echo "❌ API недоступен (HTTP $HEALTH_HTTP_CODE)"
    echo "$HEALTH_BODY"
    exit 1
fi

# 2. Проверяем статус агентов
echo ""
echo "📊 Проверка статуса агентов:"
echo "---------------------------"
AGENTS_RESPONSE=$(curl -s -w "\n%{http_code}" "$AGENTS_STATUS_URL")
AGENTS_HTTP_CODE=$(echo "$AGENTS_RESPONSE" | tail -n1)
AGENTS_BODY=$(echo "$AGENTS_RESPONSE" | head -n -1)

if [ "$AGENTS_HTTP_CODE" = "200" ]; then
    echo "✅ Агенты доступны"
    
    # Ищем ResearchFactCheckAgent
    if echo "$AGENTS_BODY" | grep -q "factcheck\|research"; then
        echo "✅ ResearchFactCheckAgent найден"
        echo "$AGENTS_BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for agent_id, agent_info in data.get('agents', {}).items():
    if 'factcheck' in agent_id.lower() or 'research' in agent_id.lower():
        print(f'   🔍 {agent_info.get(\"name\", \"Unknown\")} ({agent_id})')
        print(f'      - Статус: {agent_info.get(\"status\", \"Unknown\")}')
        print(f'      - Специализации: {\", \".join(agent_info.get(\"capabilities\", {}).get(\"specializations\", []))}')
        break
"
    else
        echo "⚠️ ResearchFactCheckAgent не найден"
        echo "   Доступные агенты:"
        echo "$AGENTS_BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for agent_id, agent_info in data.get('agents', {}).items():
    print(f'   - {agent_id}: {agent_info.get(\"name\", \"Unknown\")}')
"
    fi
else
    echo "❌ Ошибка получения статуса агентов (HTTP $AGENTS_HTTP_CODE)"
    echo "$AGENTS_BODY"
    exit 1
fi

# 3. Создаем тестовый запрос на создание контента
echo ""
echo "📝 Создание тестового контента с фактологическими утверждениями:"
echo "----------------------------------------------------------------"

# JSON данные для запроса
CONTENT_REQUEST='{
    "title": "Статистика использования AI в бизнесе: 90% компаний уже внедряют технологии",
    "description": "Анализ влияния искусственного интеллекта на современный бизнес. В 2023 году произошла революция в области AI. Исследования показывают, что 90% компаний уже используют AI технологии. Ученые подтвердили, что AI увеличивает производительность на 40%.",
    "target_audience": "IT-специалисты и бизнес-лидеры",
    "business_goals": [
        "привлечение внимания к инновациям в AI",
        "образование аудитории о статистике внедрения AI",
        "установление экспертного авторитета в области технологий"
    ],
    "call_to_action": "Подписывайтесь на наш канал для получения актуальной статистики по AI",
    "tone": "professional",
    "keywords": ["AI", "искусственный интеллект", "статистика", "бизнес", "технологии", "2023"],
    "platforms": ["telegram", "vk"],
    "content_types": ["post"],
    "constraints": {
        "fact_checking": true,
        "max_length": 1000,
        "include_statistics": true
    },
    "test_mode": true
}'

echo "📋 Данные запроса:"
echo "$CONTENT_REQUEST" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'   - Заголовок: {data[\"title\"]}')
print(f'   - Описание: {data[\"description\"][:100]}...')
print(f'   - Платформы: {\", \".join(data[\"platforms\"])}')
print(f'   - Фактчекинг: {data[\"constraints\"].get(\"fact_checking\", False)}')
"

# 4. Отправляем запрос на создание контента
echo ""
echo "🚀 Отправка запроса на создание контента:"
echo "----------------------------------------"

CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$CONTENT_REQUEST" \
    "$CONTENT_CREATE_URL")

CREATE_HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
CREATE_BODY=$(echo "$CREATE_RESPONSE" | head -n -1)

if [ "$CREATE_HTTP_CODE" = "200" ]; then
    echo "✅ Запрос успешно отправлен!"
    format_json "$CREATE_BODY"
    
    # Извлекаем workflow_id
    WORKFLOW_ID=$(echo "$CREATE_BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('workflow_id', ''))
")
    
    if [ -n "$WORKFLOW_ID" ]; then
        echo ""
        echo "⏳ Отслеживание выполнения workflow $WORKFLOW_ID:"
        echo "------------------------------------------------"
        
        # Мониторим выполнение workflow
        for attempt in $(seq 1 10); do
            echo "   Попытка $attempt:"
            
            STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" "$WORKFLOW_STATUS_URL/$WORKFLOW_ID/status")
            STATUS_HTTP_CODE=$(echo "$STATUS_RESPONSE" | tail -n1)
            STATUS_BODY=$(echo "$STATUS_RESPONSE" | head -n -1)
            
            if [ "$STATUS_HTTP_CODE" = "200" ]; then
                STATUS=$(echo "$STATUS_BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'     Статус: {data.get(\"status\", \"Unknown\")}')
print(f'     Прогресс: {data.get(\"progress_percentage\", 0):.1f}%')
print(f'     Задачи: {data.get(\"completed_tasks\", 0)}/{data.get(\"total_tasks\", 0)}')
")
                echo "$STATUS"
                
                # Проверяем результаты фактчекинга
                echo "$STATUS_BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
results = data.get('results', {})
for task_id, task_result in results.items():
    agent_id = task_result.get('agent_id', '')
    if 'factcheck' in agent_id.lower() or 'research' in agent_id.lower():
        print(f'     🔍 Результаты фактчекинга ({agent_id}):')
        if 'fact_check_report' in task_result:
            report = task_result['fact_check_report']
            print(f'       - Всего утверждений: {report.get(\"total_claims\", 0)}')
            print(f'       - Проверено: {report.get(\"verified_claims\", 0)}')
            print(f'       - Спорных: {report.get(\"disputed_claims\", 0)}')
            print(f'       - Ложных: {report.get(\"false_claims\", 0)}')
            print(f'       - Общая уверенность: {report.get(\"overall_confidence\", 0):.2f}')
            
            recommendations = report.get('recommendations', [])
            if recommendations:
                print(f'       - Рекомендации:')
                for rec in recommendations[:2]:
                    print(f'         • {rec}')
        break
"
                
                # Проверяем завершение
                FINAL_STATUS=$(echo "$STATUS_BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('status', 'Unknown'))
")
                
                if [ "$FINAL_STATUS" = "completed" ]; then
                    echo "     ✅ Workflow успешно завершен!"
                    break
                elif [ "$FINAL_STATUS" = "failed" ]; then
                    echo "     ❌ Workflow завершился с ошибкой"
                    break
                fi
            else
                echo "     ❌ Ошибка получения статуса (HTTP $STATUS_HTTP_CODE)"
            fi
            
            # Ждем перед следующей проверкой
            sleep 3
        done
    else
        echo "❌ Workflow ID не получен"
    fi
else
    echo "❌ Ошибка создания контента (HTTP $CREATE_HTTP_CODE)"
    format_json "$CREATE_BODY"
fi

echo ""
echo "🎯 Тестирование завершено!"
