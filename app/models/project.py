"""
Модели для управления проектами
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class ProjectStatus(str, Enum):
    """Статусы проекта"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PAUSED = "paused"
    DELETED = "deleted"


class Project(Base):
    """Модель проекта"""
    __tablename__ = 'projects'
    
    # Основные поля
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Владелец проекта
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Статус
    status = Column(String(20), default=ProjectStatus.ACTIVE.value, nullable=False)
    
    # Настройки проекта
    settings = Column(JSON, default=dict, nullable=True)  # Дополнительные настройки
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="projects")
    scheduled_posts = relationship("ScheduledPostDB", back_populates="project", cascade="all, delete-orphan")
    telegram_channels = relationship("TelegramChannel", back_populates="project", cascade="all, delete-orphan")
    content_pieces = relationship("ContentPieceDB", back_populates="project", cascade="all, delete-orphan")
    instagram_accounts = relationship("InstagramAccount", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует проект в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_id": self.user_id,
            "status": self.status,
            "settings": self.settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"

