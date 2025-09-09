"""
Конфигурация для billing системы
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class BillingConfig:
    """Конфигурация billing системы"""
    
    # ЮКасса настройки
    yookassa_shop_id: str
    yookassa_secret_key: str
    return_url: str
    cancel_url: str
    yookassa_webhook_secret: Optional[str] = None
    yookassa_test_mode: bool = False
    
    # Настройки подписок
    default_trial_days: int = 7
    auto_renew_enabled: bool = True
    
    # Настройки уведомлений
    notifications_enabled: bool = True
    email_notifications: bool = True
    
    # Настройки лимитов
    max_posts_per_month_free: int = 50
    max_agents_free: int = 3
    max_api_calls_per_day_free: int = 100
    max_storage_gb_free: int = 1
    
    # Настройки безопасности
    webhook_signature_required: bool = True
    payment_timeout_minutes: int = 30
    
    # Настройки базы данных
    database_url: Optional[str] = None
    
    # Настройки логирования
    log_level: str = "INFO"
    log_webhooks: bool = True


def load_billing_config() -> BillingConfig:
    """Загрузить конфигурацию billing системы из переменных окружения"""
    
    return BillingConfig(
        # ЮКасса настройки
        yookassa_shop_id=os.getenv('YOOKASSA_SHOP_ID', ''),
        yookassa_secret_key=os.getenv('YOOKASSA_SECRET_KEY', ''),
        yookassa_webhook_secret=os.getenv('YOOKASSA_WEBHOOK_SECRET'),
        yookassa_test_mode=os.getenv('YOOKASSA_TEST_MODE', 'false').lower() == 'true',
        
        # URL для возврата
        return_url=os.getenv('YOOKASSA_RETURN_URL', 'https://content-curator-1046574462613.us-central1.run.app/billing/success'),
        cancel_url=os.getenv('YOOKASSA_CANCEL_URL', 'https://content-curator-1046574462613.us-central1.run.app/billing/cancel'),
        
        # Настройки подписок
        default_trial_days=int(os.getenv('BILLING_DEFAULT_TRIAL_DAYS', '7')),
        auto_renew_enabled=os.getenv('BILLING_AUTO_RENEW_ENABLED', 'true').lower() == 'true',
        
        # Настройки уведомлений
        notifications_enabled=os.getenv('BILLING_NOTIFICATIONS_ENABLED', 'true').lower() == 'true',
        email_notifications=os.getenv('BILLING_EMAIL_NOTIFICATIONS', 'true').lower() == 'true',
        
        # Настройки лимитов
        max_posts_per_month_free=int(os.getenv('BILLING_MAX_POSTS_FREE', '50')),
        max_agents_free=int(os.getenv('BILLING_MAX_AGENTS_FREE', '3')),
        max_api_calls_per_day_free=int(os.getenv('BILLING_MAX_API_CALLS_FREE', '100')),
        max_storage_gb_free=int(os.getenv('BILLING_MAX_STORAGE_FREE', '1')),
        
        # Настройки безопасности
        webhook_signature_required=os.getenv('BILLING_WEBHOOK_SIGNATURE_REQUIRED', 'true').lower() == 'true',
        payment_timeout_minutes=int(os.getenv('BILLING_PAYMENT_TIMEOUT_MINUTES', '30')),
        
        # Настройки базы данных
        database_url=os.getenv('DATABASE_URL'),
        
        # Настройки логирования
        log_level=os.getenv('BILLING_LOG_LEVEL', 'INFO'),
        log_webhooks=os.getenv('BILLING_LOG_WEBHOOKS', 'true').lower() == 'true'
    )


# Глобальная конфигурация
billing_config = load_billing_config()


def get_billing_config() -> BillingConfig:
    """Получить текущую конфигурацию billing системы"""
    return billing_config


def update_billing_config(**kwargs) -> None:
    """Обновить конфигурацию billing системы"""
    global billing_config
    
    for key, value in kwargs.items():
        if hasattr(billing_config, key):
            setattr(billing_config, key, value)


# Валидация конфигурации
def validate_billing_config(config: BillingConfig) -> bool:
    """Проверить корректность конфигурации"""
    
    errors = []
    
    # Проверяем обязательные поля
    if not config.yookassa_shop_id:
        errors.append("YOOKASSA_SHOP_ID не установлен")
    
    if not config.yookassa_secret_key:
        errors.append("YOOKASSA_SECRET_KEY не установлен")
    
    if not config.return_url:
        errors.append("YOOKASSA_RETURN_URL не установлен")
    
    if not config.cancel_url:
        errors.append("YOOKASSA_CANCEL_URL не установлен")
    
    # Проверяем корректность значений
    if config.default_trial_days < 0:
        errors.append("BILLING_DEFAULT_TRIAL_DAYS должен быть >= 0")
    
    if config.max_posts_per_month_free < 0:
        errors.append("BILLING_MAX_POSTS_FREE должен быть >= 0")
    
    if config.max_agents_free < 0:
        errors.append("BILLING_MAX_AGENTS_FREE должен быть >= 0")
    
    if config.max_api_calls_per_day_free < 0:
        errors.append("BILLING_MAX_API_CALLS_FREE должен быть >= 0")
    
    if config.max_storage_gb_free < 0:
        errors.append("BILLING_MAX_STORAGE_FREE должен быть >= 0")
    
    if config.payment_timeout_minutes < 1:
        errors.append("BILLING_PAYMENT_TIMEOUT_MINUTES должен быть >= 1")
    
    if errors:
        raise ValueError(f"Ошибки конфигурации billing системы: {', '.join(errors)}")
    
    return True


# Инициализация конфигурации при импорте
try:
    validate_billing_config(billing_config)
except ValueError as e:
    print(f"Предупреждение: {e}")
