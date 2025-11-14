"""
Модели для запланированных постов
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime


class ScheduledPostDB(Base):
    """Запланированные посты для публикации"""
    __tablename__ = 'scheduled_posts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Связь с контентом
    content_id = Column(String(36), ForeignKey('content_pieces.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Платформа и аккаунт
    platform = Column(String(50), nullable=False, index=True)  # telegram, instagram, twitter
    account_id = Column(Integer, nullable=True)  # ID аккаунта
    account_type = Column(String(50), nullable=True)  # telegram_channel, instagram_account, twitter_account
    
    # Время публикации
    scheduled_time = Column(DateTime, nullable=False, index=True)
    published_at = Column(DateTime, nullable=True)
    
    # Статус
    status = Column(String(50), default='scheduled', nullable=False, index=True)  # scheduled, published, failed, cancelled
    
    # Результат публикации
    platform_post_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Дополнительные параметры публикации
    publish_options = Column(JSON, default=dict)  # геопозиция, опросы, первый комментарий, UTM и т.д.
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="scheduled_posts")
    content = relationship("ContentPieceDB", back_populates="scheduled_posts")
    
    # Индексы
    __table_args__ = (
        Index('ix_scheduled_user_status', 'user_id', 'status'),
        Index('ix_scheduled_time_status', 'scheduled_time', 'status'),
        Index('ix_scheduled_platform', 'platform', 'status'),
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_id': self.content_id,
            'platform': self.platform,
            'account_id': self.account_id,
            'account_type': self.account_type,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'status': self.status,
            'platform_post_id': self.platform_post_id,
            'error_message': self.error_message,
            'publish_options': self.publish_options or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<ScheduledPostDB(id={self.id}, user_id={self.user_id}, content_id='{self.content_id}', scheduled_time='{self.scheduled_time}')>"

