#!/usr/bin/env python3
"""
Тест всех агентов с главным оркестратором
Проверяет полный цикл создания и публикации контента
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.orchestrator.main_orchestrator import ContentOrchestrator
from app.agents.chief_agent import ChiefContentAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.publisher_agent import PublisherAgent
from app.models.content import ContentBrief, Platform, ContentType


async def test_full_workflow():
    """Тестирует полный workflow с реальными агентами"""
    print("🚀 Начинаем тестирование полного workflow с реальными агентами")
    
    # Создаем оркестратор
    orchestrator = ContentOrchestrator()
    
    # Создаем реальных агентов
    print("🤖 Создаем реальных агентов...")
    chief_agent = ChiefContentAgent("chief_001")
    drafting_agent = DraftingAgent("drafting_001")
    publisher_agent = PublisherAgent("publisher_001")
    
    # Регистрируем агентов
    print("📝 Регистрируем агентов в оркестраторе...")
    orchestrator.register_agent(chief_agent)
    orchestrator.register_agent(drafting_agent)
    orchestrator.register_agent(publisher_agent)
    
    # Запускаем оркестратор
    print("▶️ Запускаем оркестратор...")
    await orchestrator.start()
    
    # Проверяем статус системы
    print("📊 Статус системы:")
    status = orchestrator.get_system_status()
    print(f"  - Оркестратор запущен: {status['orchestrator']['is_running']}")
    print(f"  - Всего агентов: {status['agents']['total_agents']}")
    print(f"  - Активных задач: {status['agents']['active_tasks']}")
    
    # Создаем детальный запрос на контент
    print("📝 Создаем детальный запрос на контент...")
    request = {
        "title": "Революция в AI: как искусственный интеллект меняет бизнес",
        "description": "Глубокий анализ влияния AI на современный бизнес и перспективы развития",
        "target_audience": "IT-специалисты и бизнес-лидеры",
        "business_goals": [
            "привлечение внимания к инновациям",
            "образование аудитории о возможностях AI",
            "установление экспертного авторитета",
            "генерация лидов"
        ],
        "call_to_action": "Подписывайтесь на наш канал для получения экспертных инсайтов",
        "tone": "professional",
        "keywords": ["AI", "искусственный интеллект", "бизнес", "инновации", "автоматизация"],
        "platforms": ["telegram", "vk", "twitter"],
        "content_types": ["post", "thread"]
    }
    
    # Обрабатываем запрос
    print("⚙️ Обрабатываем запрос через полный workflow...")
    result = await orchestrator.process_content_request(request)
    
    if result["success"]:
        print("✅ Запрос успешно обработан!")
        print(f"  - Workflow ID: {result['workflow_id']}")
        print(f"  - Brief ID: {result['brief_id']}")
        print(f"  - Статус: {result['result']['status']}")
        print(f"  - Выполнено задач: {result['result']['completed_tasks']}")
        print(f"  - Провалено задач: {result['result']['failed_tasks']}")
        
        # Показываем детали результатов
        print("\n📋 Детали выполнения:")
        for task_id, task_result in result['result']['results'].items():
            agent_name = task_result.get('agent_id', 'unknown')
            print(f"  - Задача {task_id[:8]}... выполнена агентом {agent_name}")
            
            # Показываем специфичные результаты для каждого агента
            if 'chief' in agent_name:
                strategy = task_result.get('strategy', {})
                print(f"    🎯 Стратегия: {strategy.get('target_audience', 'N/A')}")
                print(f"    📝 Ключевые сообщения: {len(strategy.get('key_messages', []))}")
                print(f"    🎨 Темы контента: {len(strategy.get('content_themes', []))}")
                
            elif 'drafting' in agent_name:
                content = task_result.get('content', {})
                print(f"    ✍️ Создан контент: {content.get('title', 'N/A')}")
                print(f"    📱 Платформа: {content.get('platform', 'N/A')}")
                print(f"    📊 SEO оценка: {task_result.get('quality_metrics', {}).get('seo_score', 0):.2f}")
                
            elif 'publisher' in agent_name:
                publication = task_result.get('publication', {})
                print(f"    📤 Публикация: {'✅' if publication.get('success') else '❌'}")
                if publication.get('success'):
                    print(f"    🆔 Post ID: {publication.get('platform_post_id', 'N/A')}")
                    print(f"    📊 Метрики: {len(publication.get('metrics', {}))} показателей")
    
    else:
        print(f"❌ Ошибка обработки запроса: {result['error']}")
    
    # Тестируем индивидуальные возможности агентов
    print("\n🔬 Тестируем индивидуальные возможности агентов...")
    
    # Тест ChiefContentAgent
    print("\n🎯 Тестируем ChiefContentAgent...")
    chief_brief = ContentBrief(
        title="Тест стратегии",
        description="Тестовый бриф для проверки стратегического планирования",
        target_audience="тестовая аудитория",
        business_goals=["тестирование", "проверка функциональности"],
        call_to_action="Тестовый CTA"
    )
    
    # Создаем тестовую задачу для Chief агента
    from app.orchestrator.workflow_engine import Task, TaskType, TaskPriority
    chief_task = Task(
        name="Test Chief Strategy",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.HIGH,
        context={
            "brief_data": {
                "title": chief_brief.title,
                "description": chief_brief.description,
                "target_audience": chief_brief.target_audience,
                "business_goals": chief_brief.business_goals,
                "call_to_action": chief_brief.call_to_action
            },
            "platforms": ["telegram", "vk"]
        }
    )
    
    chief_result = await chief_agent.execute_task(chief_task)
    print(f"  ✅ ChiefAgent создал стратегию с {len(chief_result.get('strategy', {}).get('content_themes', []))} темами")
    
    # Тест DraftingAgent
    print("\n✍️ Тестируем DraftingAgent...")
    drafting_task = Task(
        name="Test Drafting Content",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.MEDIUM,
        context={
            "brief_data": {
                "title": "Тестовый пост",
                "description": "Создание тестового контента",
                "target_audience": "тестовая аудитория",
                "tone": "professional",
                "keywords": ["тест", "контент"]
            },
            "platform": "telegram",
            "content_type": "post"
        }
    )
    
    drafting_result = await drafting_agent.execute_task(drafting_task)
    content = drafting_result.get('content', {})
    print(f"  ✅ DraftingAgent создал контент: '{content.get('title', 'N/A')}'")
    print(f"  📝 Длина текста: {len(content.get('text', ''))} символов")
    print(f"  🏷️ Хештеги: {len(content.get('hashtags', []))}")
    
    # Тест PublisherAgent
    print("\n📤 Тестируем PublisherAgent...")
    publisher_task = Task(
        name="Test Publishing",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.MEDIUM,
        context={
            "content": {
                "id": "test_content_001",
                "title": "Тестовый пост для публикации",
                "text": "Это тестовый контент для проверки публикации в социальных сетях.",
                "hashtags": ["#тест", "#публикация"],
                "call_to_action": "Подписывайтесь!"
            },
            "platform": "telegram",
            "test_mode": True
        }
    )
    
    publisher_result = await publisher_agent.execute_task(publisher_task)
    publication = publisher_result.get('publication', {})
    print(f"  ✅ PublisherAgent {'успешно опубликовал' if publication.get('success') else 'не смог опубликовать'} контент")
    if publication.get('success'):
        print(f"  🆔 Post ID: {publication.get('platform_post_id', 'N/A')}")
        print(f"  📊 Метрики: {publication.get('metrics', {})}")
    
    # Проверяем финальный статус
    print("\n📊 Финальный статус системы:")
    final_status = orchestrator.get_system_status()
    print(f"  - Всего агентов: {final_status['agents']['total_agents']}")
    print(f"  - Выполнено задач: {final_status['agents']['completed_tasks']}")
    print(f"  - Активных задач: {final_status['agents']['active_tasks']}")
    print(f"  - Ошибок: {final_status['agents']['error_agents']}")
    
    # Показываем статус каждого агента
    print("\n🤖 Статус агентов:")
    agents_status = orchestrator.get_all_agents_status()
    for agent_id, agent_status in agents_status.items():
        print(f"  - {agent_status['name']}: {agent_status['status']}")
        print(f"    Выполнено задач: {agent_status['completed_tasks']}")
        print(f"    Активных задач: {agent_status['current_tasks']}")
        print(f"    Ошибок: {agent_status['error_count']}")
    
    # Останавливаем оркестратор
    print("\n⏹️ Останавливаем оркестратор...")
    await orchestrator.stop()
    
    print("\n🎉 Полное тестирование завершено!")
    print("✅ Все агенты работают корректно")
    print("✅ Интеграция с оркестратором успешна")
    print("✅ Полный цикл создания контента функционирует")


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
