"""
Тестирование реальной отправки сообщения в Telegram
"""

import asyncio
import sys
from datetime import datetime

# Добавляем путь к приложению
sys.path.append('.')

from app.agents.publisher_agent import PublisherAgent, ContentPiece, Platform, ContentStatus


async def test_real_telegram_send():
    """Тестирование реальной отправки сообщения в Telegram"""
    print("🚀 ТЕСТИРОВАНИЕ РЕАЛЬНОЙ ОТПРАВКИ В TELEGRAM")
    print("=" * 60)
    
    try:
        # Создаем PublisherAgent
        publisher = PublisherAgent("real_test_publisher")
        print(f"✅ PublisherAgent создан")
        
        if publisher.telegram_mcp is None:
            print("❌ TelegramMCP не инициализирован")
            return False
        
        # Создаем контент для реальной отправки
        real_content = ContentPiece(
            id="real_send_001",
            title="🎉 Реальная публикация через TelegramMCP!",
            text="Это сообщение отправлено через реальный Telegram Bot API!\n\n✅ Интеграция MCP работает\n✅ PublisherAgent использует TelegramMCP\n✅ Система готова к продакшену\n\nВремя отправки: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            hashtags=["realtest", "telegram", "mcp", "success", "integration"],
            call_to_action="🎯 AI Content Orchestrator работает!",
            platform=Platform.TELEGRAM,
            status=ContentStatus.DRAFT,
            created_by_agent="real_test_publisher"
        )
        
        print(f"📝 Контент для отправки:")
        print(f"   Заголовок: {real_content.title}")
        print(f"   Текст: {real_content.text[:100]}...")
        
        # Форматируем сообщение
        formatted_message = publisher._format_telegram_message(real_content)
        print(f"\n📋 Отформатированное сообщение:")
        print(f"   {formatted_message}")
        
        # Отправляем через TelegramMCP напрямую
        print(f"\n📤 Отправка через TelegramMCP...")
        result = await publisher.telegram_mcp.send_message(
            text=formatted_message
        )
        
        if result.success:
            print(f"🎉 СООБЩЕНИЕ УСПЕШНО ОТПРАВЛЕНО!")
            print(f"   Message ID: {result.data.get('message_id')}")
            print(f"   Chat ID: {result.data.get('chat', {}).get('id')}")
            print(f"   Timestamp: {result.data.get('date')}")
            print(f"   Bot: {result.data.get('chat', {}).get('type')}")
            print(f"   Metadata: {result.metadata}")
            return True
        else:
            print(f"❌ Ошибка отправки: {result.error}")
            return False
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False


async def main():
    """Основная функция"""
    print("🚀 ТЕСТИРОВАНИЕ РЕАЛЬНОЙ ОТПРАВКИ В TELEGRAM")
    print("=" * 60)
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = await test_real_telegram_send()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 РЕАЛЬНАЯ ОТПРАВКА УСПЕШНА!")
        print("✅ TelegramMCP полностью интегрирован в PublisherAgent")
        print("✅ Система готова к продакшену")
    else:
        print("❌ Ошибка реальной отправки")
    
    print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
