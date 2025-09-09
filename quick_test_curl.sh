#!/bin/bash

# Быстрый тест API с фактчекингом
# Простая curl команда для проверки ResearchFactCheckAgent

echo "🚀 Быстрый тест API с фактчекингом"
echo "=================================="

# Проверяем здоровье API
echo "1. Проверка здоровья API:"
curl -s http://localhost:5000/api/health | python3 -m json.tool

echo ""
echo "2. Проверка статуса агентов:"
curl -s http://localhost:5000/api/agents/status | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Доступные агенты:')
for agent_id, agent_info in data.get('agents', {}).items():
    print(f'  - {agent_id}: {agent_info.get(\"name\", \"Unknown\")} ({agent_info.get(\"status\", \"Unknown\")})')
    if 'factcheck' in agent_id.lower() or 'research' in agent_id.lower():
        print(f'    🔍 Специализации: {\", \".join(agent_info.get(\"capabilities\", {}).get(\"specializations\", []))}')
"

echo ""
echo "3. Создание контента с фактчекингом:"
curl -X POST http://localhost:5000/api/content/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI статистика: 90% компаний используют технологии",
    "description": "В 2023 году произошла революция в AI. Исследования показывают, что 90% компаний уже используют AI технологии. Ученые подтвердили увеличение производительности на 40%.",
    "target_audience": "IT-специалисты",
    "business_goals": ["привлечение внимания к AI", "образование аудитории"],
    "call_to_action": "Подписывайтесь для получения статистики",
    "tone": "professional",
    "keywords": ["AI", "статистика", "2023"],
    "platforms": ["telegram"],
    "content_types": ["post"],
    "constraints": {"fact_checking": true},
    "test_mode": true
  }' | python3 -m json.tool

echo ""
echo "✅ Тест завершен!"
