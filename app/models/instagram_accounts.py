"""
Модели для управления Instagram аккаунтами пользователей
Архитектура: Логин/пароль через instagrapi
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime, date
from typing import Optional


class InstagramAccount(Base):
    """Instagram аккаунты пользователей для публикации"""
    __tablename__ = 'instagram_accounts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Учетные данные (ЗАШИФРОВАНЫ!)
    instagram_username = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    
    # Название для UI
    account_name = Column(String(255), nullable=False)  # "Мой бизнес Instagram"
    
    # Информация о профиле из Instagram API
    instagram_user_id = Column(String(255), nullable=True)  # ID пользователя в Instagram
    profile_pic_url = Column(Text, nullable=True)
    followers_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    biography = Column(Text, nullable=True)
    
    # Статус подключения
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Проверили логин
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Session data (для сохранения сессии Instagram между запросами)
    session_data = Column(Text, nullable=True)  # JSON с session_id и cookies
    last_login = Column(DateTime, nullable=True)
    
    # Статистика использования
    posts_count = Column(Integer, default=0, nullable=False)
    last_post_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Ограничения безопасности (защита от блокировки Instagram)
    daily_posts_limit = Column(Integer, default=10, nullable=False)  # Макс постов в день
    posts_today = Column(Integer, default=0, nullable=False)
    posts_reset_date = Column(Date, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="instagram_accounts")
    
    # Индексы для оптимизации
    __table_args__ = (
        Index('ix_instagram_user_active', 'user_id', 'is_active'),
        Index('ix_instagram_user_username', 'user_id', 'instagram_username', unique=True),
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API ответов"""
        return {
            'id': self.id,
            'account_name': self.account_name,
            'instagram_username': self.instagram_username,
            'instagram_user_id': self.instagram_user_id,
            'profile_pic_url': self.profile_pic_url,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'biography': self.biography,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_default': self.is_default,
            'posts_count': self.posts_count,
            'last_post_at': self.last_post_at.isoformat() if self.last_post_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_error': self.last_error,
            'daily_posts_limit': self.daily_posts_limit,
            'posts_today': self.posts_today,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<InstagramAccount(id={self.id}, user_id={self.user_id}, username='{self.instagram_username}')>"


