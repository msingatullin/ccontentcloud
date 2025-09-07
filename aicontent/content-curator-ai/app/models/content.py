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
