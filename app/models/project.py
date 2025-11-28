"""
Модель проекта для группировки социальных сетей и контента
Проект = контекст для бизнеса/бренда (как в SMMplanner)
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime


class Project(Base):
    """
    Проект - контейнер для группировки соц.сетей и контента.
    Пользователь может иметь несколько проектов (разные бренды/бизнесы).
    """
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Основная информация
    name = Column(String(255), nullable=False)  # "Мой интернет-магазин", "Личный бренд"
    description = Column(Text, nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Проект по умолчанию
    
    # Настройки проекта (tone of voice, целевая аудитория и т.д.)
    settings = Column(JSON, default=dict, nullable=False)
    # Пример settings:
    # {
    #     "tone_of_voice": "professional",
    #     "target_audience": "владельцы малого бизнеса 25-45 лет",
    #     "brand_name": "TechStore",
    #     "brand_description": "Интернет-магазин электроники",
    #     "keywords": ["электроника", "гаджеты", "техника"],
    #     "hashtags": ["#techstore", "#электроника"],
    #     "default_cta": "Переходите на сайт!",
    #     "color_scheme": {"primary": "#3B82F6", "secondary": "#10B981"}
    # }
    
    # AI настройки для проекта
    ai_settings = Column(JSON, default=dict, nullable=False)
    # Пример ai_settings:
    # {
    #     "preferred_style": "informative",
    #     "content_length": "medium",
    #     "emoji_usage": "moderate",
    #     "formality_level": "semi-formal"
    # }
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="projects")
    telegram_channels = relationship("TelegramChannel", back_populates="project", lazy="dynamic")
    content_pieces = relationship("ContentPieceDB", back_populates="project", lazy="dynamic")
    scheduled_posts = relationship("ScheduledPostDB", back_populates="project", lazy="dynamic")
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'settings': self.settings or {},
            'ai_settings': self.ai_settings or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Статистика
            'channels_count': self.telegram_channels.count() if self.telegram_channels else 0,
            'content_count': self.content_pieces.count() if self.content_pieces else 0,
        }
    
    def __repr__(self):
        return f"<Project(id={self.id}, user_id={self.user_id}, name='{self.name}')>"


