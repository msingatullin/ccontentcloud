"""
Тест для ResearchFactCheckAgent MVP
Проверка базовой функциональности агента проверки фактов
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.research_factcheck_agent import ResearchFactCheckAgent
from app.orchestrator.workflow_engine import Task, TaskType, TaskPriority

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_fact_check_agent():
    """Тестирует базовую функциональность ResearchFactCheckAgent"""
    
    print("🧪 Тестирование ResearchFactCheckAgent MVP")
    print("=" * 50)
    
    # Создаем агента
    agent = ResearchFactCheckAgent()
    print(f"✅ Агент создан: {agent.name}")
    
    # Тест 1: Проверка статистических утверждений
    print("\n📊 Тест 1: Проверка статистических утверждений")
    task1 = Task(
        name="Test Statistical Fact Check",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.MEDIUM,
        context={
            "content": {
                "id": "test_content_1",
                "text": "90% пользователей довольны нашим сервисом. В 2023 году произошло важное событие."
            },
            "check_type": "basic"
        }
    )
    
    try:
        result1 = await agent.execute_task(task1)
        print(f"✅ Статистический тест завершен")
        print(f"   - Статус: {result1['status']}")
        print(f"   - Всего утверждений: {result1['fact_check_report']['total_claims']}")
        print(f"   - Проверено: {result1['fact_check_report']['verified_claims']}")
        print(f"   - Общая уверенность: {result1['fact_check_report']['overall_confidence']:.2f}")
        
        if result1['detailed_results']:
            print("   - Детальные результаты:")
            for i, detail in enumerate(result1['detailed_results'][:3], 1):
                print(f"     {i}. {detail['claim'][:50]}... - {detail['status']} ({detail['confidence']:.2f})")
        
    except Exception as e:
        print(f"❌ Ошибка в статистическом тесте: {e}")
    
    # Тест 2: Проверка временных утверждений
    print("\n📅 Тест 2: Проверка временных утверждений")
    task2 = Task(
        name="Test Temporal Fact Check",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.MEDIUM,
        context={
            "content": {
                "id": "test_content_2",
                "text": "В 2023 году произошло важное событие. 15.03.2024 был знаменательный день."
            },
            "check_type": "basic"
        }
    )
    
    try:
        result2 = await agent.execute_task(task2)
        print(f"✅ Временной тест завершен")
        print(f"   - Статус: {result2['status']}")
        print(f"   - Всего утверждений: {result2['fact_check_report']['total_claims']}")
        print(f"   - Проверено: {result2['fact_check_report']['verified_claims']}")
        print(f"   - Общая уверенность: {result2['fact_check_report']['overall_confidence']:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка во временном тесте: {e}")
    
    # Тест 3: Проверка цитат
    print("\n💬 Тест 3: Проверка цитат")
    task3 = Task(
        name="Test Quote Fact Check",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.MEDIUM,
        context={
            "content": {
                "id": "test_content_3",
                "text": 'Президент сказал: "Мы движемся вперед". Это важное заявление.'
            },
            "check_type": "basic"
        }
    )
    
    try:
        result3 = await agent.execute_task(task3)
        print(f"✅ Тест цитат завершен")
        print(f"   - Статус: {result3['status']}")
        print(f"   - Всего утверждений: {result3['fact_check_report']['total_claims']}")
        print(f"   - Проверено: {result3['fact_check_report']['verified_claims']}")
        print(f"   - Общая уверенность: {result3['fact_check_report']['overall_confidence']:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте цитат: {e}")
    
    # Тест 4: Проверка научных утверждений
    print("\n🔬 Тест 4: Проверка научных утверждений")
    task4 = Task(
        name="Test Scientific Fact Check",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.MEDIUM,
        context={
            "content": {
                "id": "test_content_4",
                "text": "Исследование показало, что 75% респондентов согласны. Ученые подтвердили результаты."
            },
            "check_type": "basic"
        }
    )
    
    try:
        result4 = await agent.execute_task(task4)
        print(f"✅ Научный тест завершен")
        print(f"   - Статус: {result4['status']}")
        print(f"   - Всего утверждений: {result4['fact_check_report']['total_claims']}")
        print(f"   - Проверено: {result4['fact_check_report']['verified_claims']}")
        print(f"   - Общая уверенность: {result4['fact_check_report']['overall_confidence']:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка в научном тесте: {e}")
    
    # Тест 5: Проверка кэша
    print("\n💾 Тест 5: Проверка кэша")
    try:
        cache_stats = agent.get_cache_stats()
        print(f"✅ Статистика кэша:")
        print(f"   - Кэшированных фактов: {cache_stats['cached_facts']}")
        print(f"   - TTL кэша (часы): {cache_stats['cache_ttl_hours']}")
        if cache_stats['oldest_cached']:
            print(f"   - Самый старый кэш: {cache_stats['oldest_cached']}")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте кэша: {e}")
    
    # Тест 6: Проверка пустого контента
    print("\n📝 Тест 6: Проверка пустого контента")
    task6 = Task(
        name="Test Empty Content",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.LOW,
        context={
            "content": {
                "id": "test_content_6",
                "text": ""
            },
            "check_type": "basic"
        }
    )
    
    try:
        result6 = await agent.execute_task(task6)
        print(f"✅ Тест пустого контента завершен")
        print(f"   - Статус: {result6['status']}")
        print(f"   - Всего утверждений: {result6['fact_check_report']['total_claims']}")
        print(f"   - Рекомендации: {result6['fact_check_report']['recommendations']}")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте пустого контента: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование ResearchFactCheckAgent MVP завершено!")
    
    # Показываем общую статистику
    print("\n📈 Общая статистика:")
    print(f"   - Агент: {agent.name}")
    print(f"   - ID: {agent.agent_id}")
    print(f"   - Статус: {agent.status.value}")
    print(f"   - Специализации: {', '.join(agent.capabilities.specializations)}")
    print(f"   - Максимум параллельных задач: {agent.capabilities.max_concurrent_tasks}")
    print(f"   - Коэффициент производительности: {agent.capabilities.performance_score}")


async def test_wikipedia_mcp():
    """Тестирует WikipediaMCP интеграцию"""
    
    print("\n🌐 Тестирование WikipediaMCP")
    print("=" * 30)
    
    try:
        from app.mcp.integrations.wikipedia import WikipediaMCP
        
        # Создаем WikipediaMCP
        wikipedia_mcp = WikipediaMCP()
        print(f"✅ WikipediaMCP создан")
        
        # Тест подключения
        print("\n🔌 Тест подключения:")
        connect_result = await wikipedia_mcp.connect()
        if connect_result.success:
            print(f"✅ Подключение успешно: {connect_result.data}")
        else:
            print(f"❌ Ошибка подключения: {connect_result.error}")
        
        # Тест поиска
        print("\n🔍 Тест поиска:")
        search_result = await wikipedia_mcp.search_general("Россия")
        if search_result.success:
            print(f"✅ Поиск успешен: найдено {search_result.data.get('results_count', 0)} результатов")
            if search_result.data.get('sources'):
                print(f"   - Источники: {search_result.data['sources'][:3]}")
        else:
            print(f"❌ Ошибка поиска: {search_result.error}")
        
        # Тест health check
        print("\n❤️ Тест health check:")
        health_result = await wikipedia_mcp.health_check()
        if health_result.success:
            print(f"✅ Health check успешен: {health_result.data}")
        else:
            print(f"❌ Ошибка health check: {health_result.error}")
        
        # Отключение
        disconnect_result = await wikipedia_mcp.disconnect()
        if disconnect_result.success:
            print(f"✅ Отключение успешно")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте WikipediaMCP: {e}")


async def main():
    """Основная функция тестирования"""
    
    print("🚀 Запуск тестов ResearchFactCheckAgent MVP")
    print("=" * 60)
    
    # Тестируем WikipediaMCP
    await test_wikipedia_mcp()
    
    # Тестируем основной агент
    await test_fact_check_agent()
    
    print("\n🎯 Все тесты завершены!")


if __name__ == "__main__":
    asyncio.run(main())
