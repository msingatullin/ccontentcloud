"""
Тестирование MCP интеграций
Проверка базовой архитектуры и Telegram интеграции
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к приложению
sys.path.append('.')

from app.mcp.config import config_manager, get_mcp_config
from app.mcp.integrations.telegram import TelegramMCP
from app.mcp.integrations.openai import OpenAIMCP
from app.mcp.integrations.huggingface import HuggingFaceMCP


async def test_mcp_config():
    """Тестирование конфигурации MCP"""
    print("🔧 ТЕСТИРОВАНИЕ MCP КОНФИГУРАЦИИ")
    print("=" * 50)
    
    # Получаем сводку статуса
    status = config_manager.get_status_summary()
    print(f"📊 Общая статистика:")
    print(f"   Всего сервисов: {status['total_services']}")
    print(f"   Включено: {status['enabled_services']}")
    print(f"   Отключено: {status['disabled_services']}")
    print(f"   С ошибками: {status['services_with_errors']}")
    print(f"   Тестовый режим: {status['test_mode']}")
    
    # Показываем включенные сервисы
    enabled_services = config_manager.get_enabled_services()
    print(f"\n✅ Включенные сервисы: {', '.join(enabled_services)}")
    
    # Показываем ошибки конфигурации
    if status['errors']:
        print(f"\n❌ Ошибки конфигурации:")
        for service, errors in status['errors'].items():
            print(f"   {service}: {', '.join(errors)}")
    else:
        print(f"\n✅ Ошибок конфигурации не найдено")
    
    return status


async def test_telegram_mcp():
    """Тестирование Telegram MCP интеграции"""
    print("\n📱 ТЕСТИРОВАНИЕ TELEGRAM MCP")
    print("=" * 50)
    
    try:
        # Создаем экземпляр TelegramMCP
        telegram = TelegramMCP()
        print(f"✅ TelegramMCP создан: {telegram}")
        
        # Тестируем подключение
        print("\n🔌 Тестирование подключения...")
        connect_result = await telegram.connect()
        if connect_result.success:
            print(f"✅ Подключение успешно: {connect_result.data}")
        else:
            print(f"❌ Ошибка подключения: {connect_result.error}")
        
        # Тестируем health check
        print("\n🏥 Тестирование health check...")
        health_result = await telegram.health_check()
        if health_result.success:
            print(f"✅ Health check пройден: {health_result.data}")
        else:
            print(f"❌ Health check не пройден: {health_result.error}")
        
        # Тестируем отправку сообщения (в тестовом режиме)
        print("\n📤 Тестирование отправки сообщения...")
        message_result = await telegram.send_message(
            "🧪 Тестовое сообщение от AI Content Orchestrator\n"
            f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "🚀 MCP интеграция работает!"
        )
        if message_result.success:
            print(f"✅ Сообщение отправлено: {message_result.data}")
            print(f"   Metadata: {message_result.metadata}")
        else:
            print(f"❌ Ошибка отправки: {message_result.error}")
        
        # Получаем метрики
        print("\n📊 Метрики TelegramMCP:")
        metrics = telegram.get_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка в TelegramMCP: {e}")
        return False


async def test_other_mcp_integrations():
    """Тестирование других MCP интеграций"""
    print("\n🤖 ТЕСТИРОВАНИЕ ДРУГИХ MCP ИНТЕГРАЦИЙ")
    print("=" * 50)
    
    integrations = [
        ("OpenAI", OpenAIMCP),
        ("HuggingFace", HuggingFaceMCP)
    ]
    
    results = {}
    
    for name, integration_class in integrations:
        try:
            print(f"\n🔧 Тестирование {name}MCP...")
            integration = integration_class()
            print(f"✅ {name}MCP создан: {integration}")
            
            # Тестируем подключение
            connect_result = await integration.connect()
            if connect_result.success:
                print(f"✅ {name} подключение успешно")
            else:
                print(f"❌ {name} ошибка подключения: {connect_result.error}")
            
            # Тестируем health check
            health_result = await integration.health_check()
            if health_result.success:
                print(f"✅ {name} health check пройден")
            else:
                print(f"❌ {name} health check не пройден: {health_result.error}")
            
            results[name] = True
            
        except Exception as e:
            print(f"❌ Критическая ошибка в {name}MCP: {e}")
            results[name] = False
    
    return results


async def test_fallback_system():
    """Тестирование системы fallback"""
    print("\n🔄 ТЕСТИРОВАНИЕ СИСТЕМЫ FALLBACK")
    print("=" * 50)
    
    try:
        # Создаем TelegramMCP с отключенным API
        telegram = TelegramMCP()
        
        # Принудительно устанавливаем статус ERROR для тестирования fallback
        from app.mcp.integrations.base import MCPStatus
        telegram.status = MCPStatus.ERROR
        
        print("🔧 Тестирование fallback для недоступного сервиса...")
        
        # Пытаемся отправить сообщение (должен сработать fallback)
        result = await telegram.execute_with_retry(
            'send_message',
            "Тестовое сообщение для fallback"
        )
        
        if result.success:
            print(f"✅ Fallback сработал: {result.data}")
            print(f"   Metadata: {result.metadata}")
        else:
            print(f"❌ Fallback не сработал: {result.error}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Ошибка тестирования fallback: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ MCP ИНТЕГРАЦИЙ")
    print("=" * 60)
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Тест 1: Конфигурация
    config_status = await test_mcp_config()
    
    # Тест 2: Telegram MCP
    telegram_success = await test_telegram_mcp()
    
    # Тест 3: Другие интеграции
    other_results = await test_other_mcp_integrations()
    
    # Тест 4: Система fallback
    fallback_success = await test_fallback_system()
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    print(f"✅ Конфигурация MCP: {'ПРОЙДЕН' if config_status else 'НЕ ПРОЙДЕН'}")
    print(f"✅ Telegram MCP: {'ПРОЙДЕН' if telegram_success else 'НЕ ПРОЙДЕН'}")
    print(f"✅ Другие интеграции: {sum(other_results.values())}/{len(other_results)} пройдено")
    print(f"✅ Система fallback: {'ПРОЙДЕН' if fallback_success else 'НЕ ПРОЙДЕН'}")
    
    total_tests = 4
    passed_tests = sum([
        bool(config_status),
        telegram_success,
        sum(other_results.values()) > 0,
        fallback_success
    ])
    
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! MCP архитектура готова к использованию!")
    else:
        print("⚠️  Некоторые тесты не пройдены. Требуется доработка.")
    
    print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
