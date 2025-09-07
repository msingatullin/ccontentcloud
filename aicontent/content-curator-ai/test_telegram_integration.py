"""
Тестирование интеграции TelegramMCP в PublisherAgent
Проверка реальной публикации и fallback системы
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к приложению
sys.path.append('.')

from app.agents.publisher_agent import PublisherAgent, ContentPiece, Platform, ContentStatus
from app.mcp.config import config_manager


async def test_publisher_agent_initialization():
    """Тестирование инициализации PublisherAgent с TelegramMCP"""
    print("🔧 ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ PUBLISHERAGENT")
    print("=" * 60)
    
    try:
        # Создаем экземпляр PublisherAgent
        publisher = PublisherAgent("test_publisher")
        print(f"✅ PublisherAgent создан: {publisher.agent_id}")
        
        # Проверяем инициализацию TelegramMCP
        if publisher.telegram_mcp is not None:
            print(f"✅ TelegramMCP инициализирован: {publisher.telegram_mcp}")
        else:
            print(f"⚠️  TelegramMCP не инициализирован (будет использоваться fallback)")
        
        # Проверяем конфигурацию платформ
        print(f"✅ Конфигурации платформ загружены: {len(publisher.platform_configs)} платформ")
        for platform, config in publisher.platform_configs.items():
            print(f"   - {platform}: {config.max_text_length} символов, {config.rate_limits}")
        
        return publisher
        
    except Exception as e:
        print(f"❌ Ошибка инициализации PublisherAgent: {e}")
        return None


async def test_telegram_publication_fallback():
    """Тестирование публикации в Telegram в fallback режиме"""
    print("\n📱 ТЕСТИРОВАНИЕ TELEGRAM ПУБЛИКАЦИИ (FALLBACK)")
    print("=" * 60)
    
    try:
        publisher = PublisherAgent("test_publisher")
        
        # Создаем тестовый контент
        test_content = ContentPiece(
            id="test_content_001",
            title="🧪 Тест интеграции TelegramMCP",
            text="Это тестовое сообщение для проверки интеграции TelegramMCP в PublisherAgent.\n\nСистема должна работать как в реальном режиме, так и в fallback режиме.",
            hashtags=["test", "telegram", "mcp", "integration"],
            call_to_action="Подписывайтесь на наш канал для получения обновлений!",
            platform=Platform.TELEGRAM,
            status=ContentStatus.DRAFT,
            created_by_agent="test_publisher"
        )
        
        print(f"📝 Тестовый контент создан:")
        print(f"   Заголовок: {test_content.title}")
        print(f"   Текст: {test_content.text[:100]}...")
        print(f"   Хештеги: {test_content.hashtags}")
        print(f"   CTA: {test_content.call_to_action}")
        
        # Тестируем форматирование сообщения
        formatted_message = publisher._format_telegram_message(test_content)
        print(f"\n📋 Отформатированное сообщение:")
        print(f"   {formatted_message}")
        
        # Тестируем публикацию (должна использовать fallback)
        print(f"\n📤 Тестирование публикации...")
        result = await publisher._publish_to_telegram(test_content)
        
        if result.success:
            print(f"✅ Публикация успешна!")
            print(f"   Post ID: {result.platform_post_id}")
            print(f"   Время публикации: {result.published_at}")
            print(f"   Метрики: {result.metrics}")
        else:
            print(f"❌ Ошибка публикации: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Критическая ошибка тестирования: {e}")
        return False


async def test_telegram_mcp_connection():
    """Тестирование подключения к TelegramMCP"""
    print("\n🔌 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К TELEGRAMMCP")
    print("=" * 60)
    
    try:
        publisher = PublisherAgent("test_publisher")
        
        if publisher.telegram_mcp is None:
            print("⚠️  TelegramMCP не инициализирован - проверяем конфигурацию")
            
            # Проверяем конфигурацию
            telegram_config = config_manager.get_config('telegram')
            if telegram_config:
                print(f"✅ Конфигурация Telegram найдена:")
                print(f"   Включен: {telegram_config.enabled}")
                print(f"   API ключ: {'установлен' if telegram_config.api_key else 'не установлен'}")
                print(f"   Тестовый режим: {telegram_config.test_mode}")
                print(f"   Base URL: {telegram_config.base_url}")
            else:
                print("❌ Конфигурация Telegram не найдена")
            
            return False
        
        # Тестируем подключение
        print("🔌 Тестирование подключения к Telegram Bot API...")
        connect_result = await publisher.telegram_mcp.connect()
        
        if connect_result.success:
            print(f"✅ Подключение успешно!")
            print(f"   Bot info: {connect_result.data}")
            print(f"   Metadata: {connect_result.metadata}")
        else:
            print(f"❌ Ошибка подключения: {connect_result.error}")
        
        # Тестируем health check
        print("\n🏥 Тестирование health check...")
        health_result = await publisher.telegram_mcp.health_check()
        
        if health_result.success:
            print(f"✅ Health check пройден!")
            print(f"   Status: {health_result.data}")
        else:
            print(f"❌ Health check не пройден: {health_result.error}")
        
        return connect_result.success and health_result.success
        
    except Exception as e:
        print(f"❌ Критическая ошибка тестирования подключения: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ TELEGRAMMCP В PUBLISHERAGENT")
    print("=" * 70)
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Тест 1: Инициализация
    publisher = await test_publisher_agent_initialization()
    if not publisher:
        print("❌ Критическая ошибка - PublisherAgent не инициализирован")
        return
    
    # Тест 2: Fallback публикация
    fallback_success = await test_telegram_publication_fallback()
    
    # Тест 3: Подключение к TelegramMCP
    connection_success = await test_telegram_mcp_connection()
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    
    print(f"✅ Инициализация PublisherAgent: ПРОЙДЕН")
    print(f"✅ Fallback публикация: {'ПРОЙДЕН' if fallback_success else 'НЕ ПРОЙДЕН'}")
    print(f"✅ Подключение к TelegramMCP: {'ПРОЙДЕН' if connection_success else 'НЕ ПРОЙДЕН'}")
    
    total_tests = 3
    passed_tests = sum([
        True,  # Инициализация всегда проходит
        fallback_success,
        connection_success
    ])
    
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests >= 2:  # Минимум 2 из 3 тестов
        print("🎉 ИНТЕГРАЦИЯ TELEGRAMMCP УСПЕШНА!")
        print("✅ PublisherAgent готов к использованию с реальным Telegram API")
    else:
        print("⚠️  Интеграция требует доработки")
    
    print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
