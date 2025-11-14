"""
Модели для правил автопостинга
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime


class AutoPostingRuleDB(Base):
    """Правила автопостинга - настройки пользователя для автоматического создания и публикации контента"""
    __tablename__ = 'auto_posting_rules'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Основная информация
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Расписание публикации
    schedule_type = Column(String(50), nullable=False)  # daily, weekly, custom, cron
    schedule_config = Column(JSON, nullable=False)  # Конфигурация расписания
    
    # Параметры создания контента (информация от пользователя)
    content_config = Column(JSON, nullable=False)  # Параметры для /api/v1/content/create
    
    # Платформы и аккаунты для публикации
    platforms = Column(JSON, nullable=False)  # ["telegram", "instagram"]
    accounts = Column(JSON, nullable=True)  # {"telegram": [1, 2], "instagram": [3]}
    
    # Типы контента
    content_types = Column(JSON, nullable=True)  # ["post", "story", "reel"]
    
    # Статус правила
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_paused = Column(Boolean, default=False, nullable=False)
    
    # Лимиты и ограничения
    max_posts_per_day = Column(Integer, nullable=True)
    max_posts_per_week = Column(Integer, nullable=True)
    
    # Статистика выполнения
    total_executions = Column(Integer, default=0, nullable=False)
    successful_executions = Column(Integer, default=0, nullable=False)
    failed_executions = Column(Integer, default=0, nullable=False)
    last_execution_at = Column(DateTime, nullable=True)
    next_execution_at = Column(DateTime, nullable=True, index=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="auto_posting_rules")
    
    # Индексы
    __table_args__ = (
        Index('ix_auto_posting_user_active', 'user_id', 'is_active'),
        Index('ix_auto_posting_next_execution', 'next_execution_at', 'is_active'),
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config or {},
            'content_config': self.content_config or {},
            'platforms': self.platforms or [],
            'accounts': self.accounts or {},
            'content_types': self.content_types or [],
            'is_active': self.is_active,
            'is_paused': self.is_paused,
            'max_posts_per_day': self.max_posts_per_day,
            'max_posts_per_week': self.max_posts_per_week,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'last_execution_at': self.last_execution_at.isoformat() if self.last_execution_at else None,
            'next_execution_at': self.next_execution_at.isoformat() if self.next_execution_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<AutoPostingRuleDB(id={self.id}, user_id={self.user_id}, name='{self.name}', is_active={self.is_active})>"

