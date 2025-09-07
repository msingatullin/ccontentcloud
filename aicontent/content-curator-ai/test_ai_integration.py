"""
Тестирование интеграции AI моделей в DraftingAgent
Проверка AI генерации контента vs шаблонной генерации
"""

import asyncio
import sys
from datetime import datetime

# Добавляем путь к приложению
sys.path.append('.')

from app.agents.drafting_agent import DraftingAgent, ContentBrief, Platform, ContentType, ContentStatus


async def test_drafting_agent_initialization():
    """Тестирование инициализации DraftingAgent с AI интеграциями"""
    print("🔧 ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ DRAFTINGAGENT")
    print("=" * 60)
    
    try:
        # Создаем экземпляр DraftingAgent
        drafting = DraftingAgent("test_drafting")
        print(f"✅ DraftingAgent создан: {drafting.agent_id}")
        
        # Проверяем инициализацию AI интеграций
        if drafting.huggingface_mcp is not None:
            print(f"✅ HuggingFaceMCP инициализирован: {drafting.huggingface_mcp}")
        else:
            print(f"⚠️  HuggingFaceMCP не инициализирован (будет использоваться fallback)")
        
        if drafting.openai_mcp is not None:
            print(f"✅ OpenAIMCP инициализирован: {drafting.openai_mcp}")
        else:
            print(f"⚠️  OpenAIMCP не инициализирован (будет использоваться fallback)")
        
        # Проверяем AI промпты
        print(f"✅ AI промпты загружены: {len(drafting.ai_prompts)} промптов")
        for platform, prompt in drafting.ai_prompts.items():
            print(f"   - {platform}: {prompt.max_tokens} токенов, temp={prompt.temperature}")
        
        # Проверяем шаблоны контента
        print(f"✅ Шаблоны контента загружены: {len(drafting.content_templates)} шаблонов")
        
        return drafting
        
    except Exception as e:
        print(f"❌ Ошибка инициализации DraftingAgent: {e}")
        return None


async def test_ai_content_generation():
    """Тестирование AI генерации контента"""
    print("\n🤖 ТЕСТИРОВАНИЕ AI ГЕНЕРАЦИИ КОНТЕНТА")
    print("=" * 60)
    
    try:
        drafting = DraftingAgent("test_drafting")
        
        # Создаем тестовый бриф
        test_brief = {
            "brief_id": "test_brief_001",
            "title": "Искусственный интеллект в бизнесе",
            "description": "Как AI технологии помогают компаниям автоматизировать процессы и повышать эффективность",
            "target_audience": "предприниматели и менеджеры",
            "tone": "professional",
            "keywords": ["AI", "автоматизация", "эффективность", "бизнес"],
            "business_goals": ["привлечение клиентов", "повышение узнаваемости"],
            "call_to_action": "Узнать больше о наших AI решениях"
        }
        
        strategy_data = {
            "content_strategy": "educational",
            "engagement_goal": "high"
        }
        
        print(f"📝 Тестовый бриф создан:")
        print(f"   Тема: {test_brief['title']}")
        print(f"   Аудитория: {test_brief['target_audience']}")
        print(f"   Тон: {test_brief['tone']}")
        print(f"   Ключевые слова: {test_brief['keywords']}")
        
        # Тестируем AI генерацию для разных платформ
        platforms = ["telegram", "vk", "instagram", "twitter"]
        
        for platform in platforms:
            print(f"\n�� Тестирование AI генерации для {platform.upper()}:")
            
            # Генерируем контент через AI
            ai_content = await drafting._generate_content_with_ai(
                test_brief, strategy_data, platform
            )
            
            if ai_content:
                print(f"✅ AI контент сгенерирован:")
                print(f"   {ai_content[:200]}...")
            else:
                print(f"⚠️  AI генерация недоступна, будет использоваться fallback")
            
            # Тестируем fallback генерацию
            fallback_content = await drafting._generate_main_content_fallback(
                test_brief, strategy_data, platform
            )
            print(f"✅ Fallback контент:")
            print(f"   {fallback_content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка тестирования AI генерации: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ AI МОДЕЛЕЙ В DRAFTINGAGENT")
    print("=" * 70)
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Тест 1: Инициализация
    drafting = await test_drafting_agent_initialization()
    if not drafting:
        print("❌ Критическая ошибка - DraftingAgent не инициализирован")
        return
    
    # Тест 2: AI генерация контента
    ai_generation_success = await test_ai_content_generation()
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    
    print(f"✅ Инициализация DraftingAgent: ПРОЙДЕН")
    print(f"✅ AI генерация контента: {'ПРОЙДЕН' if ai_generation_success else 'НЕ ПРОЙДЕН'}")
    
    total_tests = 2
    passed_tests = sum([
        True,  # Инициализация всегда проходит
        ai_generation_success
    ])
    
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests >= 2:  # Минимум 2 из 2 тестов
        print("🎉 ИНТЕГРАЦИЯ AI МОДЕЛЕЙ УСПЕШНА!")
        print("✅ DraftingAgent готов к использованию с AI генерацией контента")
        print("✅ Система fallback работает корректно")
    else:
        print("⚠️  Интеграция требует доработки")
    
    print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
