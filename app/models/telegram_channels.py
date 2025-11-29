"""
Модели для управления Telegram каналами пользователей
Архитектура: ОДИН БОТ - МНОГО КАНАЛОВ
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime
from typing import Optional


class TelegramChannel(Base):
    """Telegram каналы пользователей для публикации"""
    __tablename__ = 'telegram_channels'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Информация о канале
    channel_name = Column(String(255), nullable=False)  # "Мой канал о финансах"
    channel_username = Column(String(255), nullable=True)  # @mychannel (если публичный)
    chat_id = Column(String(255), nullable=False, index=True)  # -1001234567890 или @username
    
    # Статус подключения
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Проверили что бот есть в админах
    is_default = Column(Boolean, default=False, nullable=False)  # Канал по умолчанию для публикаций
    
    # Метаданные канала (получаем от Telegram API)
    channel_title = Column(String(500), nullable=True)  # Название из Telegram
    channel_type = Column(String(50), nullable=True)  # channel, group, supergroup
    members_count = Column(Integer, nullable=True)
    
    # Статистика использования
    posts_count = Column(Integer, default=0, nullable=False)
    last_post_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="telegram_channels")
    project = relationship("Project", back_populates="telegram_channels")
    
    # Индексы для оптимизации запросов
    __table_args__ = (
        Index('ix_telegram_user_active', 'user_id', 'is_active'),
        Index('ix_telegram_user_chat', 'user_id', 'chat_id', unique=True),  # Один канал на юзера
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API ответов"""
        # Формируем ссылку на канал
        channel_link = None
        if self.channel_username:
            # Убираем @ если есть
            username = self.channel_username.lstrip('@')
            channel_link = f"https://t.me/{username}"
        
        return {
            'id': self.id,
            'project_id': self.project_id,
            'channel_name': self.channel_name,
            'channel_username': self.channel_username,
            'channel_link': channel_link,
            'chat_id': self.chat_id,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_default': self.is_default,
            'channel_title': self.channel_title,
            'channel_type': self.channel_type,
            'members_count': self.members_count,
            'posts_count': self.posts_count,
            'last_post_at': self.last_post_at.isoformat() if self.last_post_at else None,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<TelegramChannel(id={self.id}, user_id={self.user_id}, name='{self.channel_name}', chat_id='{self.chat_id}')>"


