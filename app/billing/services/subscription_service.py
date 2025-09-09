"""
Сервис для управления подписками
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.billing.models.subscription import (
    Subscription, Payment, UsageRecord, BillingEvent,
    SubscriptionStatus, PaymentStatus, PlanType,
    get_plan_by_id, PLANS
)

logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """Статистика использования"""
    posts_used: int
    posts_limit: int
    api_calls_used: int
    api_calls_limit: int
    storage_used_gb: float
    storage_limit_gb: int
    agents_used: int
    agents_limit: int
    period_start: datetime
    period_end: datetime


class SubscriptionService:
    """Сервис для управления подписками"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        payment_method: str = "yookassa",
        trial_days: Optional[int] = None
    ) -> Optional[Subscription]:
        """Создать новую подписку"""
        try:
            plan = get_plan_by_id(plan_id)
            if not plan:
                logger.error(f"План {plan_id} не найден")
                return None
            
            # Определяем даты
            now = datetime.utcnow()
            starts_at = now
            
            # Если это пробный период
            if trial_days and trial_days > 0:
                trial_ends_at = now + timedelta(days=trial_days)
                expires_at = trial_ends_at
                status = SubscriptionStatus.TRIAL
            else:
                trial_ends_at = None
                # Для бесплатного плана - подписка на год
                if plan.plan_type == PlanType.FREE:
                    expires_at = now + timedelta(days=365)
                else:
                    expires_at = now + timedelta(days=30)  # Месячная подписка
                status = SubscriptionStatus.ACTIVE
            
            # Создаем подписку
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                status=status.value,
                starts_at=starts_at,
                expires_at=expires_at,
                trial_ends_at=trial_ends_at,
                payment_method=payment_method,
                auto_renew=plan.plan_type != PlanType.FREE
            )
            
            self.db.add(subscription)
            self.db.commit()
            
            # Создаем событие
            self._create_billing_event(
                user_id=user_id,
                subscription_id=subscription.id,
                event_type="subscription_created",
                event_data={
                    "plan_id": plan_id,
                    "trial_days": trial_days,
                    "expires_at": expires_at.isoformat()
                }
            )
            
            logger.info(f"Создана подписка {subscription.id} для пользователя {user_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Ошибка создания подписки: {e}")
            self.db.rollback()
            return None
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получить активную подписку пользователя"""
        try:
            return self.db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE.value,
                    SubscriptionStatus.TRIAL.value
                ])
            ).order_by(Subscription.created_at.desc()).first()
            
        except Exception as e:
            logger.error(f"Ошибка получения подписки пользователя {user_id}: {e}")
            return None
    
    def update_subscription_status(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Обновить статус подписки"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"Подписка {subscription_id} не найдена")
                return False
            
            old_status = subscription.status
            subscription.status = status.value
            subscription.updated_at = datetime.utcnow()
            
            if expires_at:
                subscription.expires_at = expires_at
            
            self.db.commit()
            
            # Создаем событие
            self._create_billing_event(
                user_id=subscription.user_id,
                subscription_id=subscription_id,
                event_type="subscription_status_changed",
                event_data={
                    "old_status": old_status,
                    "new_status": status.value,
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )
            
            logger.info(f"Статус подписки {subscription_id} изменен на {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса подписки: {e}")
            self.db.rollback()
            return False
    
    def renew_subscription(
        self,
        subscription_id: int,
        payment_id: Optional[str] = None
    ) -> bool:
        """Продлить подписку"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"Подписка {subscription_id} не найдена")
                return False
            
            plan = get_plan_by_id(subscription.plan_id)
            if not plan:
                logger.error(f"План {subscription.plan_id} не найден")
                return False
            
            # Продлеваем подписку
            if plan.plan_type == PlanType.FREE:
                # Бесплатный план продлеваем на год
                new_expires_at = subscription.expires_at + timedelta(days=365)
            else:
                # Платные планы продлеваем на месяц
                new_expires_at = subscription.expires_at + timedelta(days=30)
            
            subscription.expires_at = new_expires_at
            subscription.status = SubscriptionStatus.ACTIVE.value
            subscription.last_payment_at = datetime.utcnow()
            subscription.next_payment_at = new_expires_at
            subscription.updated_at = datetime.utcnow()
            
            # Если есть payment_id, обновляем последний платеж
            if payment_id:
                payment = self.db.query(Payment).filter(
                    Payment.yookassa_payment_id == payment_id
                ).first()
                if payment:
                    payment.status = PaymentStatus.SUCCEEDED.value
                    payment.paid_at = datetime.utcnow()
            
            self.db.commit()
            
            # Создаем событие
            self._create_billing_event(
                user_id=subscription.user_id,
                subscription_id=subscription_id,
                event_type="subscription_renewed",
                event_data={
                    "new_expires_at": new_expires_at.isoformat(),
                    "payment_id": payment_id
                }
            )
            
            logger.info(f"Подписка {subscription_id} продлена до {new_expires_at}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка продления подписки: {e}")
            self.db.rollback()
            return False
    
    def cancel_subscription(
        self,
        subscription_id: int,
        reason: str = "user_request"
    ) -> bool:
        """Отменить подписку"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"Подписка {subscription_id} не найдена")
                return False
            
            subscription.status = SubscriptionStatus.CANCELLED.value
            subscription.auto_renew = False
            subscription.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Создаем событие
            self._create_billing_event(
                user_id=subscription.user_id,
                subscription_id=subscription_id,
                event_type="subscription_cancelled",
                event_data={
                    "reason": reason,
                    "cancelled_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Подписка {subscription_id} отменена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отмены подписки: {e}")
            self.db.rollback()
            return False
    
    def get_usage_stats(self, user_id: str, period_start: Optional[datetime] = None) -> Optional[UsageStats]:
        """Получить статистику использования"""
        try:
            subscription = self.get_user_subscription(user_id)
            if not subscription:
                return None
            
            plan = get_plan_by_id(subscription.plan_id)
            if not plan:
                return None
            
            # Определяем период
            if not period_start:
                period_start = subscription.starts_at
            
            period_end = subscription.expires_at
            
            # Получаем статистику использования
            usage_records = self.db.query(UsageRecord).filter(
                UsageRecord.user_id == user_id,
                UsageRecord.period_start >= period_start,
                UsageRecord.period_end <= period_end
            ).all()
            
            # Подсчитываем использование
            posts_used = sum(
                record.quantity for record in usage_records 
                if record.resource_type == "posts"
            )
            
            api_calls_used = sum(
                record.quantity for record in usage_records 
                if record.resource_type == "api_calls"
            )
            
            storage_used = sum(
                record.quantity for record in usage_records 
                if record.resource_type == "storage"
            ) / 1024 / 1024 / 1024  # Конвертируем в GB
            
            # TODO: Получить количество используемых агентов из системы агентов
            
            return UsageStats(
                posts_used=posts_used,
                posts_limit=plan.limits.posts_per_month,
                api_calls_used=api_calls_used,
                api_calls_limit=plan.limits.api_calls_per_day,
                storage_used_gb=storage_used,
                storage_limit_gb=plan.limits.storage_gb,
                agents_used=0,  # TODO: Получить из системы агентов
                agents_limit=plan.limits.max_agents,
                period_start=period_start,
                period_end=period_end
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики использования: {e}")
            return None
    
    def record_usage(
        self,
        user_id: str,
        resource_type: str,
        quantity: int = 1,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Записать использование ресурса"""
        try:
            subscription = self.get_user_subscription(user_id)
            if not subscription:
                logger.error(f"Активная подписка для пользователя {user_id} не найдена")
                return False
            
            # Создаем запись использования
            usage_record = UsageRecord(
                subscription_id=subscription.id,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                quantity=quantity,
                period_start=subscription.starts_at,
                period_end=subscription.expires_at,
                metadata=metadata or {}
            )
            
            self.db.add(usage_record)
            self.db.commit()
            
            logger.info(f"Записано использование {resource_type} для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи использования: {e}")
            self.db.rollback()
            return False
    
    def check_usage_limit(
        self,
        user_id: str,
        resource_type: str,
        requested_quantity: int = 1
    ) -> bool:
        """Проверить лимит использования"""
        try:
            usage_stats = self.get_usage_stats(user_id)
            if not usage_stats:
                return False
            
            # Проверяем лимиты в зависимости от типа ресурса
            if resource_type == "posts":
                return usage_stats.posts_used + requested_quantity <= usage_stats.posts_limit
            elif resource_type == "api_calls":
                return usage_stats.api_calls_used + requested_quantity <= usage_stats.api_calls_limit
            elif resource_type == "storage":
                return usage_stats.storage_used_gb + (requested_quantity / 1024 / 1024 / 1024) <= usage_stats.storage_limit_gb
            elif resource_type == "agents":
                return usage_stats.agents_used + requested_quantity <= usage_stats.agents_limit
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимита использования: {e}")
            return False
    
    def _create_billing_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        subscription_id: Optional[int] = None
    ):
        """Создать событие billing системы"""
        try:
            event = BillingEvent(
                user_id=user_id,
                subscription_id=subscription_id,
                event_type=event_type,
                event_data=event_data
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка создания billing события: {e}")
    
    def get_billing_events(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[BillingEvent]:
        """Получить события billing системы для пользователя"""
        try:
            return self.db.query(BillingEvent).filter(
                BillingEvent.user_id == user_id
            ).order_by(BillingEvent.created_at.desc()).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Ошибка получения billing событий: {e}")
            return []
