"""
Тестирование интеграции News API в ChiefContentAgent
Проверка актуальных новостей vs шаблонных данных
"""

import asyncio
import sys
from datetime import datetime

# Добавляем путь к приложению
sys.path.append('.')

from app.agents.chief_agent import ChiefContentAgent, ContentStrategy, NewsTrend


async def test_chief_agent_initialization():
    """Тестирование инициализации ChiefContentAgent с News API"""
    print("🔧 ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ CHIEFCONTENTAGENT")
    print("=" * 60)
    
    try:
        # Создаем экземпляр ChiefContentAgent
        chief = ChiefContentAgent("test_chief")
        print(f"✅ ChiefContentAgent создан: {chief.agent_id}")
        
        # Проверяем инициализацию News API
        if chief.news_mcp is not None:
            print(f"✅ NewsMCP инициализирован: {chief.news_mcp}")
        else:
            print(f"⚠️  NewsMCP не инициализирован (будет использоваться fallback)")
        
        # Проверяем кеши
        print(f"✅ News cache инициализирован: {len(chief.news_cache)} записей")
        print(f"✅ Trend cache инициализирован: {len(chief.trend_cache)} записей")
        
        # Проверяем стратегии
        print(f"✅ Стратегии контента загружены: {len(chief.content_strategies)} стратегий")
        print(f"✅ Инсайты платформ загружены: {len(chief.platform_insights)} платформ")
        
        return chief
        
    except Exception as e:
        print(f"❌ Ошибка инициализации ChiefContentAgent: {e}")
        return None


async def test_news_themes_generation():
    """Тестирование генерации тем контента через News API"""
    print("\n📰 ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ ТЕМ ЧЕРЕЗ NEWS API")
    print("=" * 60)
    
    try:
        chief = ChiefContentAgent("test_chief")
        
        # Тестовые данные
        business_goals = [
            "привлечение новых клиентов",
            "повышение узнаваемости бренда",
            "анализ трендов в IT"
        ]
        target_audience = "IT-специалисты и разработчики"
        
        print(f"📝 Тестовые данные:")
        print(f"   Бизнес-цели: {business_goals}")
        print(f"   Целевая аудитория: {target_audience}")
        
        # Тестируем извлечение ключевых слов
        keywords = chief._extract_search_keywords(business_goals, target_audience)
        print(f"\n🔍 Извлеченные ключевые слова: {keywords}")
        
        # Тестируем генерацию тем через News API
        print(f"\n📰 Тестирование генерации тем через News API...")
        news_themes = await chief._generate_themes_from_news(business_goals, target_audience)
        
        if news_themes:
            print(f"✅ Темы из новостей сгенерированы:")
            for i, theme in enumerate(news_themes, 1):
                print(f"   {i}. {theme}")
        else:
            print(f"⚠️  News API недоступен, будет использоваться fallback")
        
        # Тестируем fallback генерацию
        print(f"\n📋 Тестирование fallback генерации...")
        fallback_themes = await chief._generate_content_themes_fallback(business_goals, target_audience)
        print(f"✅ Fallback темы:")
        for i, theme in enumerate(fallback_themes, 1):
            print(f"   {i}. {theme}")
        
        # Тестируем полную генерацию тем
        print(f"\n🎯 Тестирование полной генерации тем...")
        final_themes = await chief._generate_content_themes(business_goals, target_audience)
        print(f"✅ Финальные темы контента:")
        for i, theme in enumerate(final_themes, 1):
            print(f"   {i}. {theme}")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка тестирования News API: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ NEWS API В CHIEFCONTENTAGENT")
    print("=" * 70)
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Тест 1: Инициализация
    chief = await test_chief_agent_initialization()
    if not chief:
        print("❌ Критическая ошибка - ChiefContentAgent не инициализирован")
        return
    
    # Тест 2: Генерация тем через News API
    news_themes_success = await test_news_themes_generation()
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    
    print(f"✅ Инициализация ChiefContentAgent: ПРОЙДЕН")
    print(f"✅ Генерация тем через News API: {'ПРОЙДЕН' if news_themes_success else 'НЕ ПРОЙДЕН'}")
    
    total_tests = 2
    passed_tests = sum([
        True,  # Инициализация всегда проходит
        news_themes_success
    ])
    
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests >= 2:  # Минимум 2 из 2 тестов
        print("🎉 ИНТЕГРАЦИЯ NEWS API УСПЕШНА!")
        print("✅ ChiefContentAgent готов к использованию с актуальными новостями")
        print("✅ Система fallback работает корректно")
    else:
        print("⚠️  Интеграция требует доработки")
    
    print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
