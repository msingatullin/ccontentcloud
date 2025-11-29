"""
Модели данных для контента и контент-планов
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from uuid import uuid4


class ContentType(Enum):
    """Типы контента"""
    POST = "post"
    STORY = "story"
    REEL = "reel"
    THREAD = "thread"
    LONGREAD = "longread"
    CAROUSEL = "carousel"
    VIDEO = "video"
    IMAGE = "image"
    POLL = "poll"
    QUIZ = "quiz"


class ContentStatus(Enum):
    """Статусы контента"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Platform(Enum):
    """Поддерживаемые платформы"""
    TELEGRAM = "telegram"
    VK = "vk"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    BLOG = "blog"


@dataclass
class ContentBrief:
    """Бриф для создания контента"""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    target_audience: str = ""
    business_goals: List[str] = field(default_factory=list)
    call_to_action: str = ""
    tone: str = "professional"  # professional, casual, friendly, authoritative
    keywords: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class ContentPiece:
    """Отдельный кусок контента"""
    id: str = field(default_factory=lambda: str(uuid4()))
    brief_id: str = ""
    content_type: ContentType = ContentType.POST
    platform: Platform = Platform.TELEGRAM
    title: str = ""
    text: str = ""
    media_urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    call_to_action: str = ""
    status: ContentStatus = ContentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by_agent: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentCalendar:
    """Календарь контента"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    content_pieces: List[str] = field(default_factory=list)  # IDs контента
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class PublicationSchedule:
    """Расписание публикаций"""
    id: str = field(default_factory=lambda: str(uuid4()))
    content_id: str = ""
    platform: Platform = Platform.TELEGRAM
    scheduled_time: datetime = field(default_factory=datetime.now)
    published_time: Optional[datetime] = None
    status: ContentStatus = ContentStatus.SCHEDULED
    platform_post_id: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContentMetrics:
    """Метрики контента"""
    id: str = field(default_factory=lambda: str(uuid4()))
    content_id: str = ""
    platform: Platform = Platform.TELEGRAM
    platform_post_id: str = ""
    
    # Основные метрики
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    clicks: int = 0
    
    # Расчетные метрики
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0
    reach: int = 0
    
    # Временные метрики
    collected_at: datetime = field(default_factory=datetime.now)
    post_created_at: Optional[datetime] = None
    
    # Дополнительные данные
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentTemplate:
    """Шаблон контента"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    content_type: ContentType = ContentType.POST
    platform: Platform = Platform.TELEGRAM
    template_text: str = ""
    variables: List[str] = field(default_factory=list)  # Переменные в шаблоне
    example_values: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    usage_count: int = 0


@dataclass
class BrandVoice:
    """Голос бренда"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    
    # Характеристики голоса
    tone: str = "professional"
    personality_traits: List[str] = field(default_factory=list)
    communication_style: str = ""
    do_not_use: List[str] = field(default_factory=list)
    preferred_words: List[str] = field(default_factory=list)
    
    # Примеры
    examples: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContentCampaign:
    """Кампания контента"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    brief_id: str = ""
    brand_voice_id: str = ""
    
    # Параметры кампании
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    target_platforms: List[Platform] = field(default_factory=list)
    content_types: List[ContentType] = field(default_factory=list)
    
    # Контент кампании
    content_pieces: List[str] = field(default_factory=list)
    calendar_id: Optional[str] = None
    
    # Статус и метрики
    status: ContentStatus = ContentStatus.DRAFT
    total_budget: Optional[float] = None
    spent_budget: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


# ==================== SQLAlchemy МОДЕЛИ ДЛЯ БД ====================

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database.connection import Base


class ContentPieceDB(Base):
    """SQLAlchemy модель для сохранения готового контента"""
    __tablename__ = 'content_pieces'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=True, index=True)
    brief_id = Column(String(36), nullable=True)
    
    # Основные поля
    title = Column(String(500), nullable=False)
    text = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    
    # Дополнительные элементы
    hashtags = Column(JSON, default=list)
    mentions = Column(JSON, default=list)
    media_urls = Column(JSON, default=list)
    call_to_action = Column(String(500), nullable=True)
    
    # Статус и метаданные
    status = Column(String(50), default='draft', index=True)
    created_by_agent = Column(String(100), nullable=True)
    
    # AI метрики качества
    seo_score = Column(Float, default=0.0)
    engagement_potential = Column(Float, default=0.0)
    readability_score = Column(Float, default=0.0)
    
    # Публикация
    published_at = Column(DateTime, nullable=True)
    platform_post_id = Column(String(255), nullable=True)
    
    # Метрики производительности
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    
    # Метаданные (переименовано из metadata - зарезервированное слово в SQLAlchemy)
    meta_data = Column(JSON, default=dict)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="content_pieces")
    project = relationship("Project", back_populates="content_pieces")
    token_usage_records = relationship("TokenUsageDB", back_populates="content_piece")
    history_records = relationship("ContentHistoryDB", back_populates="content_piece")
    scheduled_posts = relationship("ScheduledPostDB", back_populates="content", cascade="all, delete-orphan")


class ContentHistoryDB(Base):
    """История изменений контента"""
    __tablename__ = 'content_history'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(String(36), ForeignKey('content_pieces.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Изменения
    action = Column(String(50), nullable=False)  # created, updated, published, archived
    changed_fields = Column(JSON, default=dict)
    changed_by_agent = Column(String(100), nullable=True)
    
    # Снапшот контента
    content_snapshot = Column(JSON, nullable=False)
    
    # Дата
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = relationship("User")
    content_piece = relationship("ContentPieceDB", back_populates="history_records")


class TokenUsageDB(Base):
    """Детальный учет использования AI токенов"""
    __tablename__ = 'token_usage'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    content_id = Column(String(36), ForeignKey('content_pieces.id'), nullable=True)
    workflow_id = Column(String(36), nullable=True, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    
    # Запрос
    request_id = Column(String(255), unique=True, index=True)
    endpoint = Column(String(100), nullable=True)
    
    # AI Модель
    ai_provider = Column(String(50), nullable=False)  # openai, anthropic, huggingface
    ai_model = Column(String(100), nullable=False)  # gpt-5-mini, gpt-5, gpt-4, dall-e-3
    
    # Токены
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Стоимость
    cost_usd = Column(Float, nullable=False, default=0.0)
    cost_rub = Column(Float, nullable=False, default=0.0)
    
    # Детали запроса
    platform = Column(String(50), nullable=True)
    content_type = Column(String(50), nullable=True)
    task_type = Column(String(50), nullable=True)
    
    # Время выполнения
    execution_time_ms = Column(Integer, nullable=True)
    
    # Метаданные
    request_metadata = Column(JSON, default=dict)
    response_metadata = Column(JSON, default=dict)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = relationship("User", back_populates="token_usage_records")
    content_piece = relationship("ContentPieceDB", back_populates="token_usage_records")
