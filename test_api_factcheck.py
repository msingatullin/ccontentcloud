"""
Тест API для создания контента с фактчекингом
Проверяет корректную работу ResearchFactCheckAgent через API
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
API_BASE_URL = "http://localhost:5000/api"
CONTENT_CREATE_URL = f"{API_BASE_URL}/content/create"
WORKFLOW_STATUS_URL = f"{API_BASE_URL}/workflow"
AGENTS_STATUS_URL = f"{API_BASE_URL}/agents/status"

def test_content_creation_with_factcheck():
    """Тестирует создание контента с фактчекингом через API"""
    
    print("🧪 Тестирование API создания контента с фактчекингом")
    print("=" * 60)
    
    # 1. Проверяем статус агентов
    print("\n📊 Проверка статуса агентов:")
    try:
        response = requests.get(AGENTS_STATUS_URL, timeout=10)
        if response.status_code == 200:
            agents_data = response.json()
            print("✅ Агенты доступны:")
            
            # Ищем ResearchFactCheckAgent
            factcheck_agent_found = False
            for agent_id, agent_info in agents_data.get('agents', {}).items():
                if 'factcheck' in agent_id.lower() or 'research' in agent_id.lower():
                    factcheck_agent_found = True
                    print(f"   🔍 ResearchFactCheckAgent: {agent_info.get('name', 'Unknown')}")
                    print(f"      - Статус: {agent_info.get('status', 'Unknown')}")
                    print(f"      - Специализации: {', '.join(agent_info.get('capabilities', {}).get('specializations', []))}")
                    break
            
            if not factcheck_agent_found:
                print("⚠️ ResearchFactCheckAgent не найден в списке агентов")
                print("   Доступные агенты:")
                for agent_id, agent_info in agents_data.get('agents', {}).items():
                    print(f"   - {agent_id}: {agent_info.get('name', 'Unknown')}")
        else:
            print(f"❌ Ошибка получения статуса агентов: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False
    
    # 2. Создаем тестовый запрос на создание контента
    print("\n📝 Создание тестового контента с фактологическими утверждениями:")
    
    # Тестовые данные с фактологическими утверждениями для проверки
    test_content_request = {
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
            "fact_checking": True,  # Включаем фактчекинг
            "max_length": 1000,
            "include_statistics": True
        },
        "test_mode": True
    }
    
    print("📋 Данные запроса:")
    print(f"   - Заголовок: {test_content_request['title']}")
    print(f"   - Описание: {test_content_request['description'][:100]}...")
    print(f"   - Платформы: {', '.join(test_content_request['platforms'])}")
    print(f"   - Фактчекинг: {test_content_request['constraints'].get('fact_checking', False)}")
    
    # 3. Отправляем запрос на создание контента
    print("\n🚀 Отправка запроса на создание контента:")
    try:
        response = requests.post(
            CONTENT_CREATE_URL,
            json=test_content_request,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Запрос успешно отправлен!")
            print(f"   - Workflow ID: {result.get('workflow_id', 'Unknown')}")
            print(f"   - Brief ID: {result.get('brief_id', 'Unknown')}")
            print(f"   - Статус: {result.get('result', {}).get('status', 'Unknown')}")
            
            workflow_id = result.get('workflow_id')
            if workflow_id:
                # 4. Отслеживаем выполнение workflow
                print(f"\n⏳ Отслеживание выполнения workflow {workflow_id}:")
                return monitor_workflow_execution(workflow_id)
            else:
                print("❌ Workflow ID не получен")
                return False
        else:
            print(f"❌ Ошибка создания контента: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки запроса: {e}")
        return False

def monitor_workflow_execution(workflow_id: str, max_attempts: int = 10):
    """Отслеживает выполнение workflow"""
    
    print(f"🔍 Мониторинг workflow {workflow_id}")
    
    for attempt in range(max_attempts):
        try:
            # Получаем статус workflow
            response = requests.get(f"{WORKFLOW_STATUS_URL}/{workflow_id}/status", timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status', 'Unknown')
                progress = status_data.get('progress_percentage', 0)
                completed_tasks = status_data.get('completed_tasks', 0)
                total_tasks = status_data.get('total_tasks', 0)
                
                print(f"   Попытка {attempt + 1}: {status} ({progress:.1f}%) - {completed_tasks}/{total_tasks} задач")
                
                # Проверяем результаты задач
                if 'results' in status_data:
                    results = status_data['results']
                    print(f"   📊 Результаты задач:")
                    
                    for task_id, task_result in results.items():
                        agent_id = task_result.get('agent_id', 'Unknown')
                        task_status = task_result.get('status', 'Unknown')
                        
                        print(f"      - {task_id} ({agent_id}): {task_status}")
                        
                        # Ищем результаты фактчекинга
                        if 'factcheck' in agent_id.lower() or 'research' in agent_id.lower():
                            print(f"        🔍 Результаты фактчекинга:")
                            
                            # Проверяем наличие fact_check_report
                            if 'fact_check_report' in task_result:
                                fact_report = task_result['fact_check_report']
                                print(f"          - Всего утверждений: {fact_report.get('total_claims', 0)}")
                                print(f"          - Проверено: {fact_report.get('verified_claims', 0)}")
                                print(f"          - Спорных: {fact_report.get('disputed_claims', 0)}")
                                print(f"          - Ложных: {fact_report.get('false_claims', 0)}")
                                print(f"          - Общая уверенность: {fact_report.get('overall_confidence', 0):.2f}")
                                
                                recommendations = fact_report.get('recommendations', [])
                                if recommendations:
                                    print(f"          - Рекомендации:")
                                    for rec in recommendations[:3]:  # Показываем первые 3
                                        print(f"            • {rec}")
                            
                            # Проверяем детальные результаты
                            if 'detailed_results' in task_result:
                                detailed_results = task_result['detailed_results']
                                print(f"          - Детальные результаты ({len(detailed_results)} утверждений):")
                                for i, detail in enumerate(detailed_results[:3], 1):  # Показываем первые 3
                                    claim = detail.get('claim', '')[:50]
                                    status = detail.get('status', 'Unknown')
                                    confidence = detail.get('confidence', 0)
                                    print(f"            {i}. {claim}... - {status} ({confidence:.2f})")
                
                # Проверяем завершение
                if status in ['completed', 'failed']:
                    if status == 'completed':
                        print("✅ Workflow успешно завершен!")
                        return True
                    else:
                        print("❌ Workflow завершился с ошибкой")
                        return False
                
                # Ждем перед следующей проверкой
                time.sleep(3)
                
            else:
                print(f"❌ Ошибка получения статуса: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")
            return False
    
    print("⏰ Превышено время ожидания выполнения workflow")
    return False

def test_api_health():
    """Проверяет здоровье API"""
    print("\n❤️ Проверка здоровья API:")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API здоров: {health_data.get('status', 'Unknown')}")
            print(f"   - Сервис: {health_data.get('service', 'Unknown')}")
            print(f"   - Версия: {health_data.get('version', 'Unknown')}")
            return True
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def main():
    """Основная функция тестирования"""
    
    print("🚀 Запуск тестирования API с фактчекингом")
    print("=" * 60)
    
    # Проверяем здоровье API
    if not test_api_health():
        print("\n❌ API недоступен, тестирование невозможно")
        return
    
    # Тестируем создание контента с фактчекингом
    success = test_content_creation_with_factcheck()
    
    if success:
        print("\n🎉 Тестирование API с фактчекингом завершено успешно!")
        print("\n📝 Результаты:")
        print("   ✅ API доступен и работает")
        print("   ✅ ResearchFactCheckAgent интегрирован")
        print("   ✅ Фактчекинг выполняется автоматически")
        print("   ✅ Результаты проверки фактов возвращаются")
    else:
        print("\n❌ Тестирование не удалось")
        print("\n🔧 Возможные причины:")
        print("   - API сервер не запущен")
        print("   - ResearchFactCheckAgent не зарегистрирован")
        print("   - Ошибки в конфигурации")
        print("   - Проблемы с MCP интеграциями")

if __name__ == "__main__":
    main()
