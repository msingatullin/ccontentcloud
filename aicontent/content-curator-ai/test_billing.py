#!/usr/bin/env python3
"""
Скрипт для тестирования billing системы с реальными ключами ЮКассы
"""

import os
import sys
import logging
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Установка переменных окружения
os.environ['YOOKASSA_SHOP_ID'] = '1134145'
os.environ['YOOKASSA_SECRET_KEY'] = 'live_144m9a57yZytkuyh90IAiM0sQoF-L3SAyfB4hZMSDFk'
os.environ['YOOKASSA_WEBHOOK_SECRET'] = 'test_webhook_secret'
os.environ['YOOKASSA_RETURN_URL'] = 'https://content-curator-1046574462613.us-central1.run.app/billing/success'
os.environ['YOOKASSA_CANCEL_URL'] = 'https://content-curator-1046574462613.us-central1.run.app/billing/cancel'
os.environ['YOOKASSA_TEST_MODE'] = 'false'

def test_yookassa_connection():
    """Тест подключения к ЮКассе"""
    try:
        from app.billing.services.yookassa_service import YooKassaService
        
        logger.info("🔗 Тестирование подключения к ЮКассе...")
        
        yookassa_service = YooKassaService()
        
        logger.info(f"✅ Shop ID: {yookassa_service.shop_id}")
        logger.info(f"✅ Test Mode: {yookassa_service.is_test_mode()}")
        logger.info(f"✅ Return URL: {yookassa_service.return_url}")
        logger.info(f"✅ Cancel URL: {yookassa_service.cancel_url}")
        
        # Получаем способы оплаты
        payment_methods = yookassa_service.get_payment_methods()
        logger.info(f"✅ Доступно способов оплаты: {len(payment_methods)}")
        
        for method in payment_methods:
            logger.info(f"   - {method['icon']} {method['name']}: {method['description']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к ЮКассе: {e}")
        return False


def test_plans():
    """Тест тарифных планов"""
    try:
        from app.billing.models.subscription import get_all_plans, get_plan_by_id
        
        logger.info("📋 Тестирование тарифных планов...")
        
        plans = get_all_plans()
        logger.info(f"✅ Найдено планов: {len(plans)}")
        
        for plan_id, plan in plans.items():
            logger.info(f"\n📦 План: {plan.name}")
            logger.info(f"   ID: {plan.id}")
            logger.info(f"   Описание: {plan.description}")
            logger.info(f"   Цена в месяц: {plan.price_monthly / 100:.2f} ₽")
            logger.info(f"   Цена в год: {plan.price_yearly / 100:.2f} ₽")
            logger.info(f"   Тип: {plan.plan_type.value}")
            logger.info(f"   Лимиты:")
            logger.info(f"     - Постов в месяц: {plan.limits.posts_per_month}")
            logger.info(f"     - Максимум агентов: {plan.limits.max_agents}")
            logger.info(f"     - Платформы: {', '.join(plan.limits.platforms)}")
            logger.info(f"     - API вызовов в день: {plan.limits.api_calls_per_day}")
            logger.info(f"     - Хранилище: {plan.limits.storage_gb} GB")
            logger.info(f"     - Поддержка: {plan.limits.support_level}")
            logger.info(f"   Пробный период: {plan.trial_days} дней")
            logger.info(f"   Популярный: {'Да' if plan.is_popular else 'Нет'}")
        
        # Тест получения конкретного плана
        pro_plan = get_plan_by_id('pro')
        if pro_plan:
            logger.info(f"✅ План Pro найден: {pro_plan.name}")
        else:
            logger.error("❌ План Pro не найден")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования планов: {e}")
        return False


def test_payment_creation():
    """Тест создания платежа (без реальной оплаты)"""
    try:
        from app.billing.services.yookassa_service import YooKassaService, PaymentRequest
        
        logger.info("💳 Тестирование создания платежа...")
        
        yookassa_service = YooKassaService()
        
        # Создаем тестовый платеж на 1 копейку
        payment_request = PaymentRequest(
            amount=1,  # 1 копейка для теста
            currency="RUB",
            description="Тестовый платеж для проверки интеграции",
            metadata={
                "test": True,
                "user_id": "test_user_123",
                "plan_id": "pro",
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info("🔄 Создание тестового платежа...")
        payment_response = yookassa_service.create_payment(
            payment_request=payment_request,
            user_id="test_user_123"
        )
        
        logger.info(f"✅ Платеж создан успешно!")
        logger.info(f"   ID: {payment_response.payment_id}")
        logger.info(f"   URL: {payment_response.payment_url}")
        logger.info(f"   Сумма: {yookassa_service.format_amount(payment_response.amount)}")
        logger.info(f"   Статус: {payment_response.status}")
        logger.info(f"   Создан: {payment_response.created_at}")
        logger.info(f"   Истекает: {payment_response.expires_at}")
        
        # Получаем информацию о платеже
        payment_info = yookassa_service.get_payment(payment_response.payment_id)
        if payment_info:
            logger.info(f"✅ Информация о платеже получена")
            logger.info(f"   Статус: {payment_info['status']}")
            logger.info(f"   Сумма: {payment_info['amount']} копеек")
            logger.info(f"   Валюта: {payment_info['currency']}")
        else:
            logger.warning("⚠️ Не удалось получить информацию о платеже")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return False


def test_config():
    """Тест конфигурации"""
    try:
        from app.billing.config import get_billing_config, validate_billing_config
        
        logger.info("⚙️ Тестирование конфигурации...")
        
        config = get_billing_config()
        
        logger.info(f"✅ Shop ID: {config.yookassa_shop_id}")
        logger.info(f"✅ Secret Key: {config.yookassa_secret_key[:10]}...")
        logger.info(f"✅ Test Mode: {config.yookassa_test_mode}")
        logger.info(f"✅ Return URL: {config.return_url}")
        logger.info(f"✅ Cancel URL: {config.cancel_url}")
        logger.info(f"✅ Default Trial Days: {config.default_trial_days}")
        logger.info(f"✅ Auto Renew: {config.auto_renew_enabled}")
        logger.info(f"✅ Notifications: {config.notifications_enabled}")
        logger.info(f"✅ Webhook Signature Required: {config.webhook_signature_required}")
        logger.info(f"✅ Payment Timeout: {config.payment_timeout_minutes} минут")
        
        # Валидация конфигурации
        try:
            validate_billing_config(config)
            logger.info("✅ Конфигурация валидна")
        except ValueError as e:
            logger.error(f"❌ Ошибка валидации конфигурации: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования конфигурации: {e}")
        return False


def main():
    """Основная функция тестирования"""
    logger.info("🚀 Запуск тестирования billing системы")
    logger.info("=" * 60)
    
    tests = [
        ("Конфигурация", test_config),
        ("Подключение к ЮКассе", test_yookassa_connection),
        ("Тарифные планы", test_plans),
        ("Создание платежа", test_payment_creation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Тест: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: ПРОЙДЕН")
            else:
                logger.error(f"❌ {test_name}: ПРОВАЛЕН")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ОШИБКА - {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    logger.info("\n" + "=" * 60)
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 Все тесты пройдены успешно!")
        logger.info("💡 Billing система готова к использованию")
    else:
        logger.warning("⚠️ Некоторые тесты провалены")
        logger.info("🔧 Проверьте настройки и исправьте ошибки")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
