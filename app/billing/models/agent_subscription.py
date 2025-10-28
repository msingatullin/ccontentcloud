"""
Модель подписок на отдельных AI агентов
Поддерживает Pay-Per-Agent биллинг модель
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database.connection import Base


class AgentSubscription(Base):
    """Подписка пользователя на конкретного AI агента"""
    __tablename__ = 'agent_subscriptions'
    
    # Идентификаторы
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Агент
    agent_id = Column(String(100), nullable=False, index=True)  # "drafting_agent", "chief_content_agent"
    agent_name = Column(String(200))  # "Drafting Agent" - для отображения
    
    # Подписка
    status = Column(String(20), default='active', index=True, nullable=False)  # active, paused, cancelled, expired
    price_monthly = Column(Integer, nullable=False)  # Цена в копейках (990₽ = 99000)
    
    # Период действия
    starts_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    auto_renew = Column(Boolean, default=True, nullable=False)  # Автопродление
    
    # Статистика использования за текущий месяц
    requests_this_month = Column(Integer, default=0, nullable=False)  # Количество запросов
    tokens_this_month = Column(Integer, default=0, nullable=False)  # Использовано токенов
    cost_this_month = Column(Integer, default=0, nullable=False)  # Фактическая стоимость токенов в копейках
    
    # Лимиты (опционально для некоторых планов)
    max_requests_per_month = Column(Integer)  # Максимум запросов в месяц (если есть лимит)
    max_tokens_per_month = Column(Integer)  # Максимум токенов в месяц
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime)  # Когда отменена
    last_used_at = Column(DateTime)  # Последнее использование
    
    # Источник подписки (для аналитики)
    source = Column(String(50))  # direct, bundle, trial, promotion
    bundle_id = Column(String(100))  # Если часть bundle
    
    # Связи
    user = relationship("User", back_populates="agent_subscriptions")
    
    def __repr__(self):
        return f"<AgentSubscription user={self.user_id} agent={self.agent_id} status={self.status}>"
    
    def is_active(self) -> bool:
        """Проверяет активна ли подписка"""
        if self.status != 'active':
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def can_use(self) -> bool:
        """
        Проверяет можно ли использовать агента
        Учитывает и статус, и лимиты
        """
        if not self.is_active():
            return False
        
        # Проверка лимитов запросов
        if self.max_requests_per_month and self.requests_this_month >= self.max_requests_per_month:
            return False
        
        # Проверка лимитов токенов
        if self.max_tokens_per_month and self.tokens_this_month >= self.max_tokens_per_month:
            return False
        
        return True
    
    def increment_usage(self, tokens_used: int, cost_kopeks: int):
        """
        Увеличивает счетчики использования
        
        Args:
            tokens_used: Количество использованных токенов
            cost_kopeks: Стоимость в копейках
        """
        self.requests_this_month += 1
        self.tokens_this_month += tokens_used
        self.cost_this_month += cost_kopeks
        self.last_used_at = datetime.utcnow()
    
    def reset_monthly_counters(self):
        """Сбрасывает месячные счетчики (вызывается в начале месяца)"""
        self.requests_this_month = 0
        self.tokens_this_month = 0
        self.cost_this_month = 0
    
    def renew(self, months: int = 1):
        """
        Продлевает подписку
        
        Args:
            months: На сколько месяцев продлить
        """
        if not self.expires_at or self.expires_at < datetime.utcnow():
            # Если истекла, продляем от текущего момента
            self.starts_at = datetime.utcnow()
            self.expires_at = datetime.utcnow() + timedelta(days=30 * months)
        else:
            # Если активна, продляем от даты истечения
            self.expires_at = self.expires_at + timedelta(days=30 * months)
        
        self.status = 'active'
        self.cancelled_at = None
    
    def cancel(self):
        """Отменяет подписку (доступ сохраняется до expires_at)"""
        self.status = 'cancelled'
        self.auto_renew = False
        self.cancelled_at = datetime.utcnow()
    
    def pause(self):
        """Приостанавливает подписку"""
        self.status = 'paused'
    
    def resume(self):
        """Возобновляет приостановленную подписку"""
        if self.status == 'paused':
            self.status = 'active'
    
    def to_dict(self):
        """Преобразует в словарь для API"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "price_monthly_rub": self.price_monthly / 100,  # В рублях
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auto_renew": self.auto_renew,
            "usage": {
                "requests_this_month": self.requests_this_month,
                "tokens_this_month": self.tokens_this_month,
                "cost_this_month_rub": self.cost_this_month / 100
            },
            "limits": {
                "max_requests": self.max_requests_per_month,
                "max_tokens": self.max_tokens_per_month
            },
            "is_active": self.is_active(),
            "can_use": self.can_use(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }

