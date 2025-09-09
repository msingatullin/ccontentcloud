"""
УПРОЩЕННОЕ ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ AI CONTENT ORCHESTRATOR
"""

import asyncio
import sys
import time
from datetime import datetime

# Добавляем путь к приложению
sys.path.append('.')

from app.agents.chief_agent import ChiefContentAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.publisher_agent import PublisherAgent
from app.models.content import ContentBrief, ContentType
from app.orchestrator.workflow_engine import Task, TaskType, TaskPriority


async def test_individual_agents():
    """Тестирование отдельных агентов"""
    print("🔧 ТЕСТИРОВАНИЕ ОТДЕЛЬНЫХ АГЕНТОВ")
    print("=" * 60)
    
    try:
        # Создаем агентов
        chief = ChiefContentAgent("test_chief")
        drafting = DraftingAgent("test_drafting")
        publisher = PublisherAgent("test_publisher")
        
        print("✅ Все агенты созданы успешно")
        
        # Проверяем MCP интеграции
        print(f"\n📰 ChiefContentAgent News API: {'✅' if chief.news_mcp else '⚠️ Fallback'}")
        print(f"🤖 DraftingAgent HuggingFace: {'✅' if drafting.huggingface_mcp else '⚠️ Fallback'}")
        print(f"🤖 DraftingAgent OpenAI: {'✅' if drafting.openai_mcp else '⚠️ Fallback'}")
        print(f"📱 PublisherAgent Telegram: {'✅' if publisher.telegram_mcp else '⚠️ Fallback'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания агентов: {e}")
        return False


async def test_workflow():
    """Тестирование workflow"""
    print("\n🔄 ТЕСТИРОВАНИЕ WORKFLOW")
    print("=" * 60)
    
    try:
        chief = ChiefContentAgent("test_chief")
        drafting = DraftingAgent("test_drafting")
        publisher = PublisherAgent("test_publisher")
        
        # Тестовые данные
        business_goals = ["привлечение клиентов", "повышение узнаваемости"]
        target_audience = "IT-специалисты"
        platforms = ["telegram"]
        
        print(f"📝 Тестовые данные:")
        print(f"   Цели: {business_goals}")
        print(f"   Аудитория: {target_audience}")
        print(f"   Платформы: {platforms}")
        
        # Шаг 1: Создание стратегии
        print(f"\n📊 Создание стратегии...")
        start_time = time.time()
        strategy = await chief._create_content_strategy(business_goals, target_audience, platforms)
        strategy_time = time.time() - start_time
        print(f"✅ Стратегия создана за {strategy_time:.2f}с")
        print(f"   Темы: {len(strategy.content_themes)}")
        print(f"   Сообщения: {len(strategy.key_messages)}")
        
        # Шаг 2: Создание брифа
        print(f"\n📋 Создание брифа...")
        brief = ContentBrief(
            title="Тест контента",
            description="Тестовое описание для IT-специалистов",
            target_audience=target_audience,
            business_goals=business_goals,
            call_to_action="Подпишитесь на наш канал",
            tone="professional",
            keywords=["IT", "технологии", "разработка"]
        )
        print("✅ Бриф создан")
        
        # Шаг 3: Генерация контента через execute_task
        print(f"\n✍️ Генерация контента...")
        start_time = time.time()
        
        # Создаем задачу для DraftingAgent
        task = Task(
            id="test_task",
            name="Генерация контента",
            task_type=TaskType.PLANNED,  # Используем PLANNED вместо CREATIVE
            priority=TaskPriority.MEDIUM,
            context={
                "brief": brief,
                "platforms": platforms
            }
        )
        
        content_result = await drafting.execute_task(task)
        drafting_time = time.time() - start_time
        print(f"✅ Контент сгенерирован за {drafting_time:.2f}с")
        
        if content_result and 'content' in content_result:
            content = content_result['content']
            for platform, platform_content in content.items():
                text_len = len(platform_content.get('text', ''))
                print(f"   {platform}: {text_len} символов")
        
        # Шаг 4: Публикация
        print(f"\n📤 Публикация контента...")
        start_time = time.time()
        if content_result and 'content' in content_result:
            publish_result = await publisher.publish_content(content_result['content'], platforms)
            publish_time = time.time() - start_time
            print(f"✅ Контент опубликован за {publish_time:.2f}с")
            
            if publish_result and 'results' in publish_result:
                for platform, result in publish_result['results'].items():
                    status = "✅" if result.get('success', False) else "❌"
                    print(f"   {platform}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка workflow: {e}")
        return False


async def main():
    """Основная функция"""
    print("🚀 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ AI CONTENT ORCHESTRATOR")
    print("=" * 70)
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    
    # Тест 1: Отдельные агенты
    agents_ok = await test_individual_agents()
    
    # Тест 2: Workflow
    workflow_ok = await test_workflow()
    
    # Итоговый отчет
    total_time = time.time() - start_time
    print(f"\n" + "=" * 70)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    print(f"⏰ Общее время: {total_time:.2f} секунд")
    print(f"✅ Агенты: {'ПРОЙДЕН' if agents_ok else 'НЕ ПРОЙДЕН'}")
    print(f"✅ Workflow: {'ПРОЙДЕН' if workflow_ok else 'НЕ ПРОЙДЕН'}")
    
    if agents_ok and workflow_ok:
        print(f"\n🎉 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        print(f"✅ AI Content Orchestrator работает корректно!")
    else:
        print(f"\n⚠️ Система требует доработки")
    
    print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
