"""
Модели для управления Twitter аккаунтами пользователей
Архитектура: OAuth 1.0a через официальный Twitter API
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime
from typing import Optional


class TwitterAccount(Base):
    """Twitter аккаунты пользователей для публикации"""
    __tablename__ = 'twitter_accounts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # OAuth токены (ЗАШИФРОВАНЫ!)
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_access_token_secret = Column(Text, nullable=False)
    
    # Информация о Twitter аккаунте
    twitter_user_id = Column(String(255), nullable=False)  # ID пользователя в Twitter
    twitter_username = Column(String(255), nullable=False)  # @username
    twitter_display_name = Column(String(255), nullable=True)  # Display name
    profile_image_url = Column(Text, nullable=True)
    followers_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    tweet_count = Column(Integer, nullable=True)
    
    # Название для UI
    account_name = Column(String(255), nullable=False)  # "Мой Twitter бизнес"
    
    # Статус подключения
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # OAuth завершен успешно
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Статистика использования
    tweets_count = Column(Integer, default=0, nullable=False)  # Опубликовано через систему
    last_tweet_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="twitter_accounts")
    
    # Индексы для оптимизации
    __table_args__ = (
        Index('ix_twitter_user_active', 'user_id', 'is_active'),
        Index('ix_twitter_user_twitter_id', 'user_id', 'twitter_user_id', unique=True),
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API ответов"""
        return {
            'id': self.id,
            'account_name': self.account_name,
            'twitter_username': self.twitter_username,
            'twitter_display_name': self.twitter_display_name,
            'twitter_user_id': self.twitter_user_id,
            'profile_image_url': self.profile_image_url,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'tweet_count': self.tweet_count,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_default': self.is_default,
            'tweets_count': self.tweets_count,
            'last_tweet_at': self.last_tweet_at.isoformat() if self.last_tweet_at else None,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<TwitterAccount(id={self.id}, user_id={self.user_id}, username='{self.twitter_username}')>"


