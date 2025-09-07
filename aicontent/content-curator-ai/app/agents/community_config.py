"""
Конфигурация для Community Concierge Agent
Настройки модерации, автоматических ответов и анализа сообщества
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .community_concierge_agent import CommentType, SentimentType, EscalationLevel, ResponseType


@dataclass
class ModerationConfig:
    """Конфигурация модерации"""
    enabled: bool = True
    auto_reply_enabled: bool = True
    escalation_enabled: bool = True
    spam_detection_enabled: bool = True
    inappropriate_detection_enabled: bool = True
    sentiment_analysis_enabled: bool = True


@dataclass
class AutoReplyConfig:
    """Конфигурация автоматических ответов"""
    enabled: bool = True
    max_replies_per_user: int = 3
    response_time_target: float = 5.0  # секунд
    template_customization: bool = True
    personalization: bool = True


@dataclass
class EscalationConfig:
    """Конфигурация эскалации"""
    enabled: bool = True
    critical_keywords: List[str] = field(default_factory=list)
    complex_questions: List[str] = field(default_factory=list)
    negative_threshold: float = 0.8
    complaint_threshold: float = 0.7
    multiple_complaints_threshold: int = 3


@dataclass
class SentimentConfig:
    """Конфигурация анализа тональности"""
    enabled: bool = True
    positive_words: List[str] = field(default_factory=list)
    negative_words: List[str] = field(default_factory=list)
    neutral_words: List[str] = field(default_factory=list)
    intensity_modifiers: Dict[str, float] = field(default_factory=dict)


@dataclass
class CommunityInsightsConfig:
    """Конфигурация инсайтов сообщества"""
    enabled: bool = True
    generate_sentiment_insights: bool = True
    generate_question_insights: bool = True
    generate_spam_insights: bool = True
    generate_trend_insights: bool = True
    insight_retention_days: int = 30


@dataclass
class CommunityConciergeConfig:
    """Основная конфигурация Community Concierge Agent"""
    agent_name: str = "Community Concierge Agent"
    max_concurrent_tasks: int = 10
    performance_score: float = 1.3
    
    # Настройки модерации
    moderation: ModerationConfig = field(default_factory=ModerationConfig)
    
    # Автоматические ответы
    auto_reply: AutoReplyConfig = field(default_factory=AutoReplyConfig)
    
    # Эскалация
    escalation: EscalationConfig = field(default_factory=EscalationConfig)
    
    # Анализ тональности
    sentiment: SentimentConfig = field(default_factory=SentimentConfig)
    
    # Инсайты сообщества
    insights: CommunityInsightsConfig = field(default_factory=CommunityInsightsConfig)
    
    # Дополнительные настройки
    enable_statistics: bool = True
    log_detailed_reports: bool = False
    enable_ai_enhancement: bool = True
    cache_ttl_minutes: int = 30


def load_config_from_env() -> CommunityConciergeConfig:
    """Загружает конфигурацию из переменных окружения"""
    
    return CommunityConciergeConfig(
        agent_name=os.getenv("COMMUNITY_AGENT_NAME", "Community Concierge Agent"),
        max_concurrent_tasks=int(os.getenv("COMMUNITY_MAX_CONCURRENT_TASKS", "10")),
        performance_score=float(os.getenv("COMMUNITY_PERFORMANCE_SCORE", "1.3")),
        
        moderation=ModerationConfig(
            enabled=os.getenv("COMMUNITY_MODERATION_ENABLED", "true").lower() == "true",
            auto_reply_enabled=os.getenv("COMMUNITY_AUTO_REPLY_ENABLED", "true").lower() == "true",
            escalation_enabled=os.getenv("COMMUNITY_ESCALATION_ENABLED", "true").lower() == "true",
            spam_detection_enabled=os.getenv("COMMUNITY_SPAM_DETECTION_ENABLED", "true").lower() == "true",
            inappropriate_detection_enabled=os.getenv("COMMUNITY_INAPPROPRIATE_DETECTION_ENABLED", "true").lower() == "true",
            sentiment_analysis_enabled=os.getenv("COMMUNITY_SENTIMENT_ANALYSIS_ENABLED", "true").lower() == "true"
        ),
        
        auto_reply=AutoReplyConfig(
            enabled=os.getenv("COMMUNITY_AUTO_REPLY_ENABLED", "true").lower() == "true",
            max_replies_per_user=int(os.getenv("COMMUNITY_MAX_REPLIES_PER_USER", "3")),
            response_time_target=float(os.getenv("COMMUNITY_RESPONSE_TIME_TARGET", "5.0")),
            template_customization=os.getenv("COMMUNITY_TEMPLATE_CUSTOMIZATION", "true").lower() == "true",
            personalization=os.getenv("COMMUNITY_PERSONALIZATION", "true").lower() == "true"
        ),
        
        escalation=EscalationConfig(
            enabled=os.getenv("COMMUNITY_ESCALATION_ENABLED", "true").lower() == "true",
            critical_keywords=os.getenv("COMMUNITY_CRITICAL_KEYWORDS", "юридический,суд,жалоба,претензия,возврат").split(","),
            complex_questions=os.getenv("COMMUNITY_COMPLEX_QUESTIONS", "техническая поддержка,настройка,интеграция").split(","),
            negative_threshold=float(os.getenv("COMMUNITY_NEGATIVE_THRESHOLD", "0.8")),
            complaint_threshold=float(os.getenv("COMMUNITY_COMPLAINT_THRESHOLD", "0.7")),
            multiple_complaints_threshold=int(os.getenv("COMMUNITY_MULTIPLE_COMPLAINTS_THRESHOLD", "3"))
        ),
        
        sentiment=SentimentConfig(
            enabled=os.getenv("COMMUNITY_SENTIMENT_ENABLED", "true").lower() == "true",
            positive_words=os.getenv("COMMUNITY_POSITIVE_WORDS", "отлично,супер,классно,круто,молодцы,хорошо,понравилось,спасибо").split(","),
            negative_words=os.getenv("COMMUNITY_NEGATIVE_WORDS", "плохо,ужасно,отвратительно,недоволен,разочарован,злой,бесит").split(","),
            neutral_words=os.getenv("COMMUNITY_NEUTRAL_WORDS", "нормально,обычно,стандартно,типично,средне").split(","),
            intensity_modifiers={
                "очень": float(os.getenv("COMMUNITY_INTENSITY_VERY", "1.5")),
                "крайне": float(os.getenv("COMMUNITY_INTENSITY_EXTREME", "2.0")),
                "слегка": float(os.getenv("COMMUNITY_INTENSITY_SLIGHT", "0.5"))
            }
        ),
        
        insights=CommunityInsightsConfig(
            enabled=os.getenv("COMMUNITY_INSIGHTS_ENABLED", "true").lower() == "true",
            generate_sentiment_insights=os.getenv("COMMUNITY_SENTIMENT_INSIGHTS", "true").lower() == "true",
            generate_question_insights=os.getenv("COMMUNITY_QUESTION_INSIGHTS", "true").lower() == "true",
            generate_spam_insights=os.getenv("COMMUNITY_SPAM_INSIGHTS", "true").lower() == "true",
            generate_trend_insights=os.getenv("COMMUNITY_TREND_INSIGHTS", "true").lower() == "true",
            insight_retention_days=int(os.getenv("COMMUNITY_INSIGHT_RETENTION_DAYS", "30"))
        ),
        
        enable_statistics=os.getenv("COMMUNITY_STATISTICS", "true").lower() == "true",
        log_detailed_reports=os.getenv("COMMUNITY_DETAILED_LOGS", "false").lower() == "true",
        enable_ai_enhancement=os.getenv("COMMUNITY_AI_ENHANCEMENT", "true").lower() == "true",
        cache_ttl_minutes=int(os.getenv("COMMUNITY_CACHE_TTL_MINUTES", "30"))
    )


# Предустановленные конфигурации
STRICT_MODERATION_CONFIG = CommunityConciergeConfig(
    agent_name="Community Concierge Agent (Strict Moderation)",
    moderation=ModerationConfig(
        enabled=True,
        auto_reply_enabled=True,
        escalation_enabled=True,
        spam_detection_enabled=True,
        inappropriate_detection_enabled=True,
        sentiment_analysis_enabled=True
    ),
    auto_reply=AutoReplyConfig(
        enabled=True,
        max_replies_per_user=2,
        response_time_target=3.0,
        template_customization=True,
        personalization=False
    ),
    escalation=EscalationConfig(
        enabled=True,
        critical_keywords=["юридический", "суд", "жалоба", "претензия", "возврат", "компенсация"],
        complex_questions=["техническая поддержка", "настройка", "интеграция", "кастомизация"],
        negative_threshold=0.7,
        complaint_threshold=0.6,
        multiple_complaints_threshold=2
    ),
    sentiment=SentimentConfig(
        enabled=True,
        positive_words=["отлично", "супер", "классно", "круто", "молодцы", "хорошо", "понравилось", "спасибо"],
        negative_words=["плохо", "ужасно", "отвратительно", "недоволен", "разочарован", "злой", "бесит", "ненавижу"],
        neutral_words=["нормально", "обычно", "стандартно", "типично", "средне"],
        intensity_modifiers={"очень": 1.5, "крайне": 2.0, "слегка": 0.5}
    )
)

FRIENDLY_MODERATION_CONFIG = CommunityConciergeConfig(
    agent_name="Community Concierge Agent (Friendly Moderation)",
    moderation=ModerationConfig(
        enabled=True,
        auto_reply_enabled=True,
        escalation_enabled=True,
        spam_detection_enabled=True,
        inappropriate_detection_enabled=False,
        sentiment_analysis_enabled=True
    ),
    auto_reply=AutoReplyConfig(
        enabled=True,
        max_replies_per_user=5,
        response_time_target=10.0,
        template_customization=True,
        personalization=True
    ),
    escalation=EscalationConfig(
        enabled=True,
        critical_keywords=["юридический", "суд", "жалоба", "претензия"],
        complex_questions=["техническая поддержка", "настройка", "интеграция"],
        negative_threshold=0.9,
        complaint_threshold=0.8,
        multiple_complaints_threshold=5
    ),
    sentiment=SentimentConfig(
        enabled=True,
        positive_words=["отлично", "супер", "классно", "круто", "молодцы", "хорошо", "понравилось", "спасибо", "благодарю"],
        negative_words=["плохо", "ужасно", "недоволен", "разочарован"],
        neutral_words=["нормально", "обычно", "стандартно", "типично", "средне", "приемлемо"],
        intensity_modifiers={"очень": 1.3, "крайне": 1.8, "слегка": 0.7}
    )
)

AUTOMATED_CONFIG = CommunityConciergeConfig(
    agent_name="Community Concierge Agent (Automated)",
    max_concurrent_tasks=20,
    moderation=ModerationConfig(
        enabled=True,
        auto_reply_enabled=True,
        escalation_enabled=False,
        spam_detection_enabled=True,
        inappropriate_detection_enabled=True,
        sentiment_analysis_enabled=True
    ),
    auto_reply=AutoReplyConfig(
        enabled=True,
        max_replies_per_user=10,
        response_time_target=2.0,
        template_customization=False,
        personalization=False
    ),
    escalation=EscalationConfig(
        enabled=False,
        critical_keywords=[],
        complex_questions=[],
        negative_threshold=1.0,
        complaint_threshold=1.0,
        multiple_complaints_threshold=100
    ),
    sentiment=SentimentConfig(
        enabled=True,
        positive_words=["отлично", "супер", "классно", "круто", "молодцы", "хорошо", "понравилось", "спасибо"],
        negative_words=["плохо", "ужасно", "недоволен", "разочарован"],
        neutral_words=["нормально", "обычно", "стандартно", "типично", "средне"],
        intensity_modifiers={"очень": 1.5, "крайне": 2.0, "слегка": 0.5}
    )
)

HUMAN_FOCUSED_CONFIG = CommunityConciergeConfig(
    agent_name="Community Concierge Agent (Human Focused)",
    max_concurrent_tasks=5,
    moderation=ModerationConfig(
        enabled=True,
        auto_reply_enabled=False,
        escalation_enabled=True,
        spam_detection_enabled=True,
        inappropriate_detection_enabled=True,
        sentiment_analysis_enabled=True
    ),
    auto_reply=AutoReplyConfig(
        enabled=False,
        max_replies_per_user=0,
        response_time_target=60.0,
        template_customization=False,
        personalization=False
    ),
    escalation=EscalationConfig(
        enabled=True,
        critical_keywords=["юридический", "суд", "жалоба", "претензия", "возврат", "компенсация", "ущерб"],
        complex_questions=["техническая поддержка", "настройка", "интеграция", "кастомизация", "разработка"],
        negative_threshold=0.5,
        complaint_threshold=0.4,
        multiple_complaints_threshold=1
    ),
    sentiment=SentimentConfig(
        enabled=True,
        positive_words=["отлично", "супер", "классно", "круто", "молодцы", "хорошо", "понравилось", "спасибо"],
        negative_words=["плохо", "ужасно", "отвратительно", "недоволен", "разочарован", "злой", "бесит"],
        neutral_words=["нормально", "обычно", "стандартно", "типично", "средне"],
        intensity_modifiers={"очень": 1.5, "крайне": 2.0, "слегка": 0.5}
    )
)
