"""
Пример использования billing системы
"""

import os
import logging
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Установка переменных окружения для примера
os.environ['YOOKASSA_SHOP_ID'] = '1134145'
os.environ['YOOKASSA_SECRET_KEY'] = 'live_144m9a57yZytkuyh90IAiM0sQoF-L3SAyfB4hZMSDFk'
os.environ['YOOKASSA_WEBHOOK_SECRET'] = 'your_webhook_secret_here'
os.environ['YOOKASSA_RETURN_URL'] = 'https://content-curator-1046574462613.us-central1.run.app/billing/success'
os.environ['YOOKASSA_CANCEL_URL'] = 'https://content-curator-1046574462613.us-central1.run.app/billing/cancel'

from app.billing.services.yookassa_service import YooKassaService, PaymentRequest
from app.billing.services.subscription_service import SubscriptionService
from app.billing.models.subscription import get_all_plans, get_plan_by_id


def example_create_payment():
    """Пример создания платежа"""
    try:
        # Инициализируем сервис ЮКассы
        yookassa_service = YooKassaService()
        
        # Создаем запрос на платеж
        payment_request = PaymentRequest(
            amount=299000,  # 2990₽ в копейках
            currency="RUB",
            description="Подписка Pro на месяц",
            metadata={
                "plan_id": "pro",
                "billing_period": "monthly",
                "user_id": "user_123"
            }
        )
        
        # Создаем платеж
        payment_response = yookassa_service.create_payment(
            payment_request=payment_request,
            user_id="user_123"
        )
        
        logger.info(f"Создан платеж: {payment_response.payment_id}")
        logger.info(f"URL для оплаты: {payment_response.payment_url}")
        logger.info(f"Сумма: {yookassa_service.format_amount(payment_response.amount)}")
        logger.info(f"Истекает: {payment_response.expires_at}")
        
        return payment_response
        
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return None


def example_get_plans():
    """Пример получения тарифных планов"""
    try:
        plans = get_all_plans()
        
        logger.info("Доступные тарифные планы:")
        for plan_id, plan in plans.items():
            logger.info(f"\nПлан: {plan.name}")
            logger.info(f"Описание: {plan.description}")
            logger.info(f"Цена в месяц: {plan.price_monthly / 100:.2f} ₽")
            logger.info(f"Цена в год: {plan.price_yearly / 100:.2f} ₽")
            logger.info(f"Лимиты:")
            logger.info(f"  - Постов в месяц: {plan.limits.posts_per_month}")
            logger.info(f"  - Максимум агентов: {plan.limits.max_agents}")
            logger.info(f"  - Платформы: {', '.join(plan.limits.platforms)}")
            logger.info(f"  - API вызовов в день: {plan.limits.api_calls_per_day}")
            logger.info(f"  - Хранилище: {plan.limits.storage_gb} GB")
            logger.info(f"  - Поддержка: {plan.limits.support_level}")
            logger.info(f"Пробный период: {plan.trial_days} дней")
        
        return plans
        
    except Exception as e:
        logger.error(f"Ошибка получения планов: {e}")
        return None


def example_check_usage_limits():
    """Пример проверки лимитов использования"""
    try:
        # TODO: Инициализировать с реальной сессией БД
        # db_session = get_db_session()
        # subscription_service = SubscriptionService(db_session)
        
        user_id = "user_123"
        
        # Получаем статистику использования
        # usage_stats = subscription_service.get_usage_stats(user_id)
        # if not usage_stats:
        #     logger.error("Не удалось получить статистику использования")
        #     return
        
        # Временная заглушка
        usage_stats = {
            "posts_used": 15,
            "posts_limit": 50,
            "api_calls_used": 250,
            "api_calls_limit": 100,
            "storage_used_gb": 0.5,
            "storage_limit_gb": 1,
            "agents_used": 2,
            "agents_limit": 3
        }
        
        logger.info(f"Статистика использования для пользователя {user_id}:")
        logger.info(f"Посты: {usage_stats['posts_used']}/{usage_stats['posts_limit']}")
        logger.info(f"API вызовы: {usage_stats['api_calls_used']}/{usage_stats['api_calls_limit']}")
        logger.info(f"Хранилище: {usage_stats['storage_used_gb']}/{usage_stats['storage_limit_gb']} GB")
        logger.info(f"Агенты: {usage_stats['agents_used']}/{usage_stats['agents_limit']}")
        
        # Проверяем лимиты
        # posts_available = subscription_service.check_usage_limit(user_id, "posts", 1)
        # api_calls_available = subscription_service.check_usage_limit(user_id, "api_calls", 1)
        # agents_available = subscription_service.check_usage_limit(user_id, "agents", 1)
        
        posts_available = usage_stats['posts_used'] < usage_stats['posts_limit']
        api_calls_available = usage_stats['api_calls_used'] < usage_stats['api_calls_limit']
        agents_available = usage_stats['agents_used'] < usage_stats['agents_limit']
        
        logger.info(f"\nДоступность ресурсов:")
        logger.info(f"Посты: {'✅ Доступно' if posts_available else '❌ Лимит исчерпан'}")
        logger.info(f"API вызовы: {'✅ Доступно' if api_calls_available else '❌ Лимит исчерпан'}")
        logger.info(f"Агенты: {'✅ Доступно' if agents_available else '❌ Лимит исчерпан'}")
        
        return usage_stats
        
    except Exception as e:
        logger.error(f"Ошибка проверки лимитов: {e}")
        return None


def example_payment_methods():
    """Пример получения способов оплаты"""
    try:
        yookassa_service = YooKassaService()
        payment_methods = yookassa_service.get_payment_methods()
        
        logger.info("Доступные способы оплаты:")
        for method in payment_methods:
            logger.info(f"{method['icon']} {method['name']} - {method['description']}")
        
        return payment_methods
        
    except Exception as e:
        logger.error(f"Ошибка получения способов оплаты: {e}")
        return None


def example_webhook_processing():
    """Пример обработки webhook от ЮКассы"""
    try:
        yookassa_service = YooKassaService()
        
        # Пример webhook данных (в реальности приходят от ЮКассы)
        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "test_payment_123",
                "status": "succeeded",
                "amount": {
                    "value": "2990.00",
                    "currency": "RUB"
                },
                "metadata": {
                    "user_id": "user_123",
                    "plan_id": "pro"
                },
                "created_at": datetime.utcnow().isoformat(),
                "paid_at": datetime.utcnow().isoformat()
            }
        }
        
        # Парсим webhook
        parsed_data = yookassa_service.parse_webhook(str(webhook_data))
        
        if parsed_data:
            logger.info(f"Обработан webhook: {parsed_data['event_type']}")
            logger.info(f"Платеж: {parsed_data['payment_id']}")
            logger.info(f"Сумма: {parsed_data['amount']} копеек")
            logger.info(f"Пользователь: {parsed_data['metadata']['user_id']}")
        else:
            logger.warning("Не удалось распарсить webhook")
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return None


def main():
    """Основная функция с примерами"""
    logger.info("=== Примеры использования billing системы ===\n")
    
    # 1. Получение тарифных планов
    logger.info("1. Получение тарифных планов:")
    example_get_plans()
    
    # 2. Создание платежа
    logger.info("\n2. Создание платежа:")
    example_create_payment()
    
    # 3. Проверка лимитов использования
    logger.info("\n3. Проверка лимитов использования:")
    example_check_usage_limits()
    
    # 4. Способы оплаты
    logger.info("\n4. Способы оплаты:")
    example_payment_methods()
    
    # 5. Обработка webhook
    logger.info("\n5. Обработка webhook:")
    example_webhook_processing()
    
    logger.info("\n=== Примеры завершены ===")


if __name__ == "__main__":
    main()
