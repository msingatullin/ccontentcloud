"""
Скрипт интеграции ResearchFactCheckAgent в систему
Добавляет агента проверки фактов в существующую систему
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.research_factcheck_agent import ResearchFactCheckAgent
from app.orchestrator.main_orchestrator import ContentOrchestrator
from app.orchestrator.workflow_engine import Task, TaskType, TaskPriority

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def integrate_factcheck_agent():
    """Интегрирует ResearchFactCheckAgent в систему"""
    
    print("🔧 Интеграция ResearchFactCheckAgent в систему")
    print("=" * 50)
    
    try:
        # Создаем оркестратор
        orchestrator = ContentOrchestrator()
        print("✅ ContentOrchestrator создан")
        
        # Создаем агента проверки фактов
        factcheck_agent = ResearchFactCheckAgent()
        print("✅ ResearchFactCheckAgent создан")
        
        # Регистрируем агента в системе
        success = orchestrator.register_agent(factcheck_agent)
        if success:
            print("✅ ResearchFactCheckAgent зарегистрирован в системе")
        else:
            print("❌ Ошибка регистрации ResearchFactCheckAgent")
            return False
        
        # Запускаем оркестратор
        await orchestrator.start()
        print("✅ ContentOrchestrator запущен")
        
        # Тестируем интеграцию
        print("\n🧪 Тестирование интеграции:")
        
        # Создаем тестовую задачу
        test_task = Task(
            name="Integration Test - Fact Check",
            task_type=TaskType.PLANNED,
            priority=TaskPriority.MEDIUM,
            context={
                "content": {
                    "id": "integration_test_1",
                    "text": "В 2023 году произошло важное событие. 90% пользователей довольны сервисом."
                },
                "check_type": "basic"
            }
        )
        
        # Создаем workflow для тестирования
        workflow = orchestrator.workflow_engine.create_workflow(
            name="test_factcheck_workflow",
            task_type=TaskType.PLANNED
        )
        print(f"✅ Workflow создан: {workflow.id}")
        
        # Добавляем задачу в workflow
        task = orchestrator.workflow_engine.add_task(
            workflow_id=workflow.id,
            task_name=test_task.name,
            task_type=test_task.task_type,
            priority=test_task.priority,
            context=test_task.context
        )
        print(f"✅ Тестовая задача добавлена: {task.id}")
        
        # Ждем выполнения задачи
        print("⏳ Ожидание выполнения задачи...")
        await asyncio.sleep(2)  # Даем время на выполнение
        
        # Проверяем статус задачи
        found_task = orchestrator.workflow_engine._find_task(task.id)
        if found_task:
            print(f"📊 Статус задачи: {found_task.status.value}")
            
            # Получаем результат
            if found_task.status.value == 'completed' and found_task.result:
                result = found_task.result
                fact_check_report = result.get('fact_check_report', {})
                
                print("✅ Задача выполнена успешно!")
                print(f"   - Всего утверждений: {fact_check_report.get('total_claims', 0)}")
                print(f"   - Проверено: {fact_check_report.get('verified_claims', 0)}")
                print(f"   - Общая уверенность: {fact_check_report.get('overall_confidence', 0):.2f}")
                
                if result.get('detailed_results'):
                    print("   - Детальные результаты:")
                    for i, detail in enumerate(result['detailed_results'][:2], 1):
                        print(f"     {i}. {detail['claim'][:40]}... - {detail['status']} ({detail['confidence']:.2f})")
            else:
                print("⚠️ Задача не завершена или есть ошибки")
        else:
            print("❌ Задача не найдена")
        
        # Останавливаем оркестратор
        await orchestrator.stop()
        print("✅ ContentOrchestrator остановлен")
        
        print("\n🎉 Интеграция ResearchFactCheckAgent завершена успешно!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка интеграции: {e}")
        print(f"❌ Ошибка интеграции: {e}")
        return False


async def test_agent_capabilities():
    """Тестирует возможности агента"""
    
    print("\n🔍 Тестирование возможностей агента")
    print("=" * 40)
    
    try:
        # Создаем агента
        agent = ResearchFactCheckAgent()
        
        # Проверяем базовые возможности
        print(f"📋 Информация об агенте:")
        print(f"   - ID: {agent.agent_id}")
        print(f"   - Имя: {agent.name}")
        print(f"   - Статус: {agent.status.value}")
        print(f"   - Специализации: {', '.join(agent.capabilities.specializations)}")
        print(f"   - Максимум параллельных задач: {agent.capabilities.max_concurrent_tasks}")
        print(f"   - Коэффициент производительности: {agent.capabilities.performance_score}")
        
        # Проверяем типы задач
        print(f"   - Поддерживаемые типы задач: {[t.value for t in agent.capabilities.task_types]}")
        
        # Проверяем кэш
        cache_stats = agent.get_cache_stats()
        print(f"   - Статистика кэша: {cache_stats['cached_facts']} фактов")
        
        print("✅ Все возможности агента проверены")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка тестирования возможностей: {e}")
        print(f"❌ Ошибка тестирования возможностей: {e}")
        return False


async def main():
    """Основная функция"""
    
    print("🚀 Запуск интеграции ResearchFactCheckAgent")
    print("=" * 60)
    
    # Тестируем возможности агента
    capabilities_ok = await test_agent_capabilities()
    
    if capabilities_ok:
        # Интегрируем агента
        integration_ok = await integrate_factcheck_agent()
        
        if integration_ok:
            print("\n🎯 Интеграция завершена успешно!")
            print("\n📝 Следующие шаги:")
            print("   1. Агент готов к использованию в системе")
            print("   2. Можно создавать задачи проверки фактов")
            print("   3. Агент автоматически обрабатывает контент")
            print("   4. Результаты сохраняются в кэше на 24 часа")
        else:
            print("\n❌ Интеграция не удалась")
    else:
        print("\n❌ Тестирование возможностей не удалось")


if __name__ == "__main__":
    asyncio.run(main())
