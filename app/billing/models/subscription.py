"""
Модели для системы подписок и billing
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SubscriptionStatus(Enum):
    """Статусы подписки"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"
    TRIAL = "trial"


class PlanType(Enum):
    """Типы тарифных планов"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentStatus(Enum):
    """Статусы платежей"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


@dataclass
class PlanLimits:
    """Лимиты тарифного плана"""
    posts_per_month: int
    max_agents: int
    platforms: list
    api_calls_per_day: int
    storage_gb: int
    support_level: str
    features: list = field(default_factory=list)


@dataclass
class SubscriptionPlan:
    """Тарифный план"""
    id: str
    name: str
    description: str
    price_monthly: int  # в копейках
    price_yearly: int  # в копейках
    plan_type: PlanType
    limits: PlanLimits
    features: list
    is_popular: bool = False
    trial_days: int = 0


class Subscription(Base):
    """Модель подписки"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    plan_id = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default=SubscriptionStatus.ACTIVE.value)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Платежная информация
    payment_method = Column(String(50), nullable=True)
    auto_renew = Column(Boolean, default=True)
    last_payment_at = Column(DateTime, nullable=True)
    next_payment_at = Column(DateTime, nullable=True)
    
    # Метаданные
    meta_data = Column(JSON, default=dict)
    
    # Связи
    payments = relationship("Payment", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")


class Payment(Base):
    """Модель платежа"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    
    # ЮКасса данные
    yookassa_payment_id = Column(String(255), nullable=True, unique=True)
    yookassa_payment_url = Column(Text, nullable=True)
    
    # Сумма и валюта
    amount = Column(Integer, nullable=False)  # в копейках
    currency = Column(String(3), default='RUB')
    
    # Статус
    status = Column(String(20), nullable=False, default=PaymentStatus.PENDING.value)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    
    # Описание
    description = Column(Text, nullable=True)
    meta_data = Column(JSON, default=dict)
    
    # Связи
    subscription = relationship("Subscription", back_populates="payments")


class UsageRecord(Base):
    """Модель записи использования"""
    __tablename__ = 'usage_records'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Тип использования
    resource_type = Column(String(50), nullable=False)  # posts, api_calls, storage
    resource_id = Column(String(255), nullable=True)
    
    # Количество
    quantity = Column(Integer, nullable=False, default=1)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Метаданные
    meta_data = Column(JSON, default=dict)
    
    # Связи
    subscription = relationship("Subscription", back_populates="usage_records")


class BillingEvent(Base):
    """Модель событий billing системы"""
    __tablename__ = 'billing_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=True)
    
    # Тип события
    event_type = Column(String(50), nullable=False)  # subscription_created, payment_succeeded, etc.
    
    # Данные события
    event_data = Column(JSON, nullable=False)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Статус обработки
    is_processed = Column(Boolean, default=False)


# Предопределенные тарифные планы
PLANS = {
    "free": SubscriptionPlan(
        id="free",
        name="Free",
        description="Базовый план для начала работы",
        price_monthly=0,
        price_yearly=0,
        plan_type=PlanType.FREE,
        limits=PlanLimits(
            posts_per_month=50,
            max_agents=3,
            platforms=["telegram", "vk"],
            api_calls_per_day=100,
            storage_gb=1,
            support_level="community",
            features=[
                "Базовые AI агенты",
                "Ограниченные платформы",
                "Сообщество поддержка"
            ]
        ),
        features=[
            "50 постов в месяц",
            "3 AI агента",
            "Telegram и VK",
            "Базовые шаблоны",
            "Сообщество поддержка"
        ],
        trial_days=7
    ),
    
    "pro": SubscriptionPlan(
        id="pro",
        name="Pro",
        description="Для профессионалов и малого бизнеса",
        price_monthly=299000,  # 2990₽
        price_yearly=2990000,  # 29900₽ (скидка ~17%)
        plan_type=PlanType.PRO,
        limits=PlanLimits(
            posts_per_month=-1,  # unlimited
            max_agents=10,
            platforms=["telegram", "vk", "facebook", "instagram", "youtube", "tiktok", "google_ads", "yandex_direct"],
            api_calls_per_day=10000,
            storage_gb=100,
            support_level="priority",
            features=[
                "Все AI агенты",
                "Все платформы",
                "Приоритетная поддержка",
                "Расширенная аналитика"
            ]
        ),
        features=[
            "Неограниченные посты",
            "Все 10 AI агентов",
            "Все платформы",
            "Расширенные шаблоны",
            "Приоритетная поддержка",
            "Аналитика и отчеты",
            "A/B тестирование",
            "API доступ"
        ],
        is_popular=True,
        trial_days=14
    ),
    
    "enterprise": SubscriptionPlan(
        id="enterprise",
        name="Enterprise",
        description="Для крупных компаний и команд",
        price_monthly=0,  # договорная
        price_yearly=0,
        plan_type=PlanType.ENTERPRISE,
        limits=PlanLimits(
            posts_per_month=-1,
            max_agents=-1,
            platforms=["all"],
            api_calls_per_day=-1,
            storage_gb=-1,
            support_level="dedicated",
            features=[
                "Белый лейбл",
                "Выделенная поддержка",
                "Кастомные интеграции",
                "SLA гарантии"
            ]
        ),
        features=[
            "Неограниченные ресурсы",
            "Белый лейбл решение",
            "Выделенная поддержка 24/7",
            "Кастомные интеграции",
            "SLA гарантии",
            "Персональный менеджер",
            "Обучение команды",
            "Приоритетная разработка"
        ],
        trial_days=30
    )
}


def get_plan_by_id(plan_id: str) -> Optional[SubscriptionPlan]:
    """Получить план по ID"""
    return PLANS.get(plan_id)


def get_all_plans() -> Dict[str, SubscriptionPlan]:
    """Получить все доступные планы"""
    return PLANS


def is_plan_available(plan_id: str) -> bool:
    """Проверить доступность плана"""
    return plan_id in PLANS


def get_plan_limits(plan_id: str) -> Optional[PlanLimits]:
    """Получить лимиты плана"""
    plan = get_plan_by_id(plan_id)
    return plan.limits if plan else None
