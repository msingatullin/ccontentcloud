"""
Схемы валидации для API запросов и ответов
Использует Pydantic для валидации данных
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class PlatformEnum(str, Enum):
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


class ContentTypeEnum(str, Enum):
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


class ToneEnum(str, Enum):
    """Тоны контента"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"


class TaskTypeEnum(str, Enum):
    """Типы задач"""
    REAL_TIME = "real_time"
    PLANNED = "planned"
    COMPLEX = "complex"


class TaskPriorityEnum(str, Enum):
    """Приоритеты задач"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatusEnum(str, Enum):
    """Статусы агентов"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class WorkflowStatusEnum(str, Enum):
    """Статусы workflow"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== REQUEST SCHEMAS ====================

class ContentRequestSchema(BaseModel):
    """Схема запроса на создание контента"""
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок контента")
    description: str = Field(..., min_length=10, max_length=1000, description="Описание контента")
    target_audience: str = Field(..., min_length=1, max_length=200, description="Целевая аудитория")
    business_goals: List[str] = Field(..., min_items=1, max_items=10, description="Бизнес-цели")
    call_to_action: List[str] = Field(default=[], max_items=10, description="Призывы к действию (текст, ссылки, действия)")
    tone: ToneEnum = Field(default=ToneEnum.PROFESSIONAL, description="Тон контента")
    keywords: List[str] = Field(default=[], max_items=20, description="Ключевые слова")
    platforms: List[PlatformEnum] = Field(default=[], max_items=5, description="Платформы для публикации (опционально)")
    content_types: List[ContentTypeEnum] = Field(default=[ContentTypeEnum.POST], description="Типы контента")
    constraints: Dict[str, Any] = Field(default={}, description="Дополнительные ограничения")
    test_mode: bool = Field(default=False, description="Тестовый режим (без реальной публикации). По умолчанию False - публикация реальная")
    channel_id: Optional[int] = Field(default=None, description="ID конкретного канала/аккаунта для публикации (если не указан - используется дефолтный)")
    
    # Медиа и документы
    uploaded_files: List[str] = Field(default=[], max_items=10, description="IDs загруженных файлов для использования в контенте")
    reference_urls: List[str] = Field(default=[], max_items=5, description="URLs референсных материалов")
    
    @validator('keywords')
    def validate_keywords(cls, v):
        """Валидация ключевых слов"""
        for keyword in v:
            if len(keyword.strip()) == 0:
                raise ValueError("Ключевые слова не могут быть пустыми")
            if len(keyword) > 50:
                raise ValueError("Ключевые слова не могут быть длиннее 50 символов")
        return v
    
    @validator('business_goals')
    def validate_business_goals(cls, v):
        """Валидация бизнес-целей"""
        for goal in v:
            if len(goal.strip()) == 0:
                raise ValueError("Бизнес-цели не могут быть пустыми")
            if len(goal) > 100:
                raise ValueError("Бизнес-цели не могут быть длиннее 100 символов")
        return v


class WorkflowStatusRequestSchema(BaseModel):
    """Схема запроса статуса workflow"""
    workflow_id: str = Field(..., description="ID workflow")


class AgentStatusRequestSchema(BaseModel):
    """Схема запроса статуса агента"""
    agent_id: Optional[str] = Field(None, description="ID конкретного агента (опционально)")


class ContentModificationSchema(BaseModel):
    """Схема модификации контента"""
    text: Optional[str] = Field(None, max_length=5000, description="Новый текст")
    hashtags: Optional[List[str]] = Field(None, max_items=20, description="Новые хештеги")
    call_to_action: Optional[str] = Field(None, max_length=200, description="Новый призыв к действию")
    title: Optional[str] = Field(None, max_length=200, description="Новый заголовок")


# ==================== RESPONSE SCHEMAS ====================

class ContentQualityMetricsSchema(BaseModel):
    """Схема метрик качества контента"""
    seo_score: float = Field(..., ge=0.0, le=1.0, description="SEO оценка")
    engagement_potential: float = Field(..., ge=0.0, le=1.0, description="Потенциал вовлеченности")
    readability_score: float = Field(..., ge=0.0, le=1.0, description="Оценка читаемости")
    platform_optimized: bool = Field(..., description="Оптимизирован для платформы")


class ContentSchema(BaseModel):
    """Схема контента"""
    id: str = Field(..., description="ID контента")
    title: str = Field(..., description="Заголовок")
    text: str = Field(..., description="Текст контента")
    hashtags: List[str] = Field(..., description="Хештеги")
    call_to_action: str = Field(..., description="Призыв к действию")
    platform: str = Field(..., description="Платформа")
    content_type: str = Field(..., description="Тип контента")


class PublicationSchema(BaseModel):
    """Схема публикации"""
    success: bool = Field(..., description="Успешность публикации")
    platform_post_id: Optional[str] = Field(None, description="ID поста на платформе")
    published_at: Optional[str] = Field(None, description="Время публикации")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class ScheduleSchema(BaseModel):
    """Схема расписания"""
    id: str = Field(..., description="ID расписания")
    scheduled_time: str = Field(..., description="Запланированное время")
    status: str = Field(..., description="Статус")


class StrategySchema(BaseModel):
    """Схема стратегии"""
    target_audience: str = Field(..., description="Целевая аудитория")
    key_messages: List[str] = Field(..., description="Ключевые сообщения")
    content_themes: List[str] = Field(..., description="Темы контента")
    platform_strategy: Dict[str, Any] = Field(..., description="Стратегия по платформам")


class ContentPlanSchema(BaseModel):
    """Схема плана контента"""
    calendar_id: str = Field(..., description="ID календаря")
    estimated_reach: int = Field(..., description="Ожидаемый охват")
    content_briefs_count: int = Field(..., description="Количество брифов")


class TaskResultSchema(BaseModel):
    """Схема результата задачи"""
    task_id: str = Field(..., description="ID задачи")
    agent_id: str = Field(..., description="ID агента")
    status: str = Field(..., description="Статус выполнения")
    timestamp: str = Field(..., description="Время выполнения")
    content: Optional[ContentSchema] = Field(None, description="Созданный контент")
    publication: Optional[PublicationSchema] = Field(None, description="Результат публикации")
    strategy: Optional[StrategySchema] = Field(None, description="Созданная стратегия")
    quality_metrics: Optional[ContentQualityMetricsSchema] = Field(None, description="Метрики качества")
    recommendations: Optional[List[str]] = Field(None, description="Рекомендации")


class WorkflowResultSchema(BaseModel):
    """Схема результата workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    status: str = Field(..., description="Статус workflow")
    results: Dict[str, TaskResultSchema] = Field(..., description="Результаты задач")
    completed_tasks: int = Field(..., description="Количество выполненных задач")
    failed_tasks: int = Field(..., description="Количество проваленных задач")
    total_tasks: int = Field(..., description="Общее количество задач")


class ContentResponseSchema(BaseModel):
    """Схема ответа на создание контента"""
    success: bool = Field(..., description="Успешность операции")
    workflow_id: str = Field(..., description="ID созданного workflow")
    brief_id: str = Field(..., description="ID созданного брифа")
    result: WorkflowResultSchema = Field(..., description="Результат выполнения")
    timestamp: str = Field(..., description="Время создания")


class AgentCapabilitySchema(BaseModel):
    """Схема возможностей агента"""
    task_types: List[str] = Field(..., description="Типы задач")
    max_concurrent_tasks: int = Field(..., description="Максимум одновременных задач")
    specializations: List[str] = Field(..., description="Специализации")
    performance_score: float = Field(..., description="Оценка производительности")


class AgentStatusSchema(BaseModel):
    """Схема статуса агента"""
    agent_id: str = Field(..., description="ID агента")
    name: str = Field(..., description="Название агента")
    status: AgentStatusEnum = Field(..., description="Статус агента")
    current_tasks: int = Field(..., description="Текущие задачи")
    completed_tasks: int = Field(..., description="Выполненные задачи")
    error_count: int = Field(..., description="Количество ошибок")
    last_activity: str = Field(..., description="Последняя активность")
    capabilities: AgentCapabilitySchema = Field(..., description="Возможности агента")


class SystemStatusSchema(BaseModel):
    """Схема статуса системы"""
    orchestrator: Dict[str, Any] = Field(..., description="Статус оркестратора")
    workflows: Dict[str, Any] = Field(..., description="Статус workflow")
    agents: Dict[str, Any] = Field(..., description="Статус агентов")
    timestamp: str = Field(..., description="Время получения статуса")


class WorkflowStatusSchema(BaseModel):
    """Схема статуса workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    name: str = Field(..., description="Название workflow")
    status: WorkflowStatusEnum = Field(..., description="Статус")
    created_at: str = Field(..., description="Время создания")
    total_tasks: int = Field(..., description="Общее количество задач")
    completed_tasks: int = Field(..., description="Выполненные задачи")
    failed_tasks: int = Field(..., description="Проваленные задачи")
    in_progress_tasks: int = Field(..., description="Задачи в процессе")
    progress_percentage: float = Field(..., description="Процент выполнения")


class ErrorResponseSchema(BaseModel):
    """Схема ответа с ошибкой"""
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    status_code: int = Field(..., description="HTTP статус код")
    timestamp: str = Field(..., description="Время ошибки")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали")


class HealthCheckSchema(BaseModel):
    """Схема health check"""
    status: str = Field(..., description="Статус сервиса")
    timestamp: str = Field(..., description="Время проверки")
    version: str = Field(..., description="Версия сервиса")
    service: str = Field(..., description="Название сервиса")


class PlatformConfigSchema(BaseModel):
    """Схема конфигурации платформы"""
    platform: str = Field(..., description="Название платформы")
    supported: bool = Field(..., description="Поддерживается ли платформа")
    max_text_length: int = Field(..., description="Максимальная длина текста")
    rate_limits: Dict[str, int] = Field(..., description="Лимиты API")
    supported_formats: List[str] = Field(..., description="Поддерживаемые форматы")


class PlatformStatsSchema(BaseModel):
    """Схема статистики платформ"""
    platforms: Dict[str, PlatformConfigSchema] = Field(..., description="Конфигурации платформ")


# ==================== UTILITY SCHEMAS ====================

class PaginationSchema(BaseModel):
    """Схема пагинации"""
    page: int = Field(default=1, ge=1, description="Номер страницы")
    per_page: int = Field(default=10, ge=1, le=100, description="Элементов на странице")
    total: int = Field(..., description="Общее количество элементов")
    pages: int = Field(..., description="Общее количество страниц")


class FilterSchema(BaseModel):
    """Схема фильтрации"""
    platform: Optional[PlatformEnum] = Field(None, description="Фильтр по платформе")
    content_type: Optional[ContentTypeEnum] = Field(None, description="Фильтр по типу контента")
    status: Optional[str] = Field(None, description="Фильтр по статусу")
    date_from: Optional[str] = Field(None, description="Дата начала (ISO format)")
    date_to: Optional[str] = Field(None, description="Дата окончания (ISO format)")


class SearchSchema(BaseModel):
    """Схема поиска"""
    query: str = Field(..., min_length=1, max_length=100, description="Поисковый запрос")
    filters: Optional[FilterSchema] = Field(None, description="Фильтры")
    pagination: Optional[PaginationSchema] = Field(None, description="Пагинация")


# ==================== VALIDATION HELPERS ====================

def validate_platforms(platforms: List[str]) -> List[PlatformEnum]:
    """Валидирует список платформ"""
    try:
        return [PlatformEnum(platform) for platform in platforms]
    except ValueError as e:
        raise ValueError(f"Неподдерживаемая платформа: {e}")


def validate_content_types(content_types: List[str]) -> List[ContentTypeEnum]:
    """Валидирует список типов контента"""
    try:
        return [ContentTypeEnum(content_type) for content_type in content_types]
    except ValueError as e:
        raise ValueError(f"Неподдерживаемый тип контента: {e}")


def validate_tone(tone: str) -> ToneEnum:
    """Валидирует тон контента"""
    try:
        return ToneEnum(tone)
    except ValueError:
        raise ValueError(f"Неподдерживаемый тон: {tone}")


# ==================== EXAMPLE DATA ====================

class ExampleData:
    """Примеры данных для документации API"""
    
    CONTENT_REQUEST_EXAMPLE = {
        "title": "Революция в AI: как искусственный интеллект меняет бизнес",
        "description": "Глубокий анализ влияния AI на современный бизнес и перспективы развития",
        "target_audience": "IT-специалисты и бизнес-лидеры",
        "business_goals": [
            "привлечение внимания к инновациям",
            "образование аудитории о возможностях AI",
            "установление экспертного авторитета"
        ],
        "call_to_action": [
            "Подписывайтесь на наш Telegram канал",
            "https://t.me/ai_business_channel",
            "Переходите на сайт за полной статьей",
            "https://example.com/ai-revolution?utm_source=post"
        ],
        "tone": "professional",
        "keywords": ["AI", "искусственный интеллект", "бизнес", "инновации"],
        "platforms": ["telegram", "vk", "twitter"],
        "content_types": ["post", "thread"],
        "test_mode": True
    }
    
    CONTENT_RESPONSE_EXAMPLE = {
        "success": True,
        "workflow_id": "47fa6a19-6050-4707-a716-0f2260700b4e",
        "brief_id": "8aa7317b-548a-45dd-871a-f0c130fbc7e3",
        "result": {
            "workflow_id": "47fa6a19-6050-4707-a716-0f2260700b4e",
            "status": "completed",
            "completed_tasks": 6,
            "failed_tasks": 0,
            "total_tasks": 6,
            "results": {
                "task_1": {
                    "task_id": "task_1",
                    "agent_id": "chief_001",
                    "status": "completed",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "strategy": {
                        "target_audience": "IT-специалисты и бизнес-лидеры",
                        "key_messages": ["Мы предлагаем уникальные решения"],
                        "content_themes": ["технологии", "инновации"],
                        "platform_strategy": {}
                    }
                }
            }
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    ERROR_RESPONSE_EXAMPLE = {
        "error": "Validation Error",
        "message": "Некорректные данные запроса",
        "status_code": 400,
        "timestamp": "2024-01-01T12:00:00Z",
        "details": {
            "field": "title",
            "issue": "Поле обязательно для заполнения"
        }
    }
