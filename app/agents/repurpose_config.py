"""
Конфигурация для Repurpose Agent
Настройки адаптации контента и форматов
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .repurpose_agent import ContentFormat, ContentType, AdaptationStrategy


@dataclass
class FormatConfig:
    """Конфигурация для формата контента"""
    enabled: bool = True
    priority: int = 1
    custom_template: Optional[str] = None
    quality_threshold: float = 0.7
    max_retries: int = 3


@dataclass
class AdaptationConfig:
    """Конфигурация адаптации"""
    enabled: bool = True
    strategy: AdaptationStrategy = AdaptationStrategy.EXTRACT_KEY_POINTS
    preserve_tone: bool = True
    preserve_brand_voice: bool = True
    add_hashtags: bool = True
    add_call_to_action: bool = True


@dataclass
class QualityConfig:
    """Конфигурация качества"""
    min_word_count: int = 50
    max_word_count: int = 2000
    readability_score: float = 0.7
    engagement_potential: float = 0.6
    plagiarism_check: bool = False
    grammar_check: bool = True


@dataclass
class CacheConfig:
    """Конфигурация кэширования"""
    enabled: bool = True
    ttl_hours: int = 12
    max_size: int = 500
    cleanup_interval_hours: int = 24


@dataclass
class RepurposeAgentConfig:
    """Основная конфигурация Repurpose Agent"""
    agent_name: str = "Repurpose Agent"
    max_concurrent_tasks: int = 3
    performance_score: float = 1.1
    
    # Настройки адаптации
    enable_auto_adaptation: bool = True
    enable_quality_checks: bool = True
    enable_brand_consistency: bool = True
    
    # Конфигурация форматов
    format_configs: Dict[ContentFormat, FormatConfig] = field(default_factory=dict)
    
    # Конфигурация адаптации
    adaptation_config: AdaptationConfig = field(default_factory=AdaptationConfig)
    
    # Конфигурация качества
    quality_config: QualityConfig = field(default_factory=QualityConfig)
    
    # Кэширование
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Дополнительные настройки
    enable_statistics: bool = True
    log_detailed_reports: bool = False
    enable_ai_enhancement: bool = True


def load_config_from_env() -> RepurposeAgentConfig:
    """Загружает конфигурацию из переменных окружения"""
    
    # Создаем конфигурации для форматов
    format_configs = {
        ContentFormat.TELEGRAM_POST: FormatConfig(
            enabled=os.getenv("REPURPOSE_TELEGRAM_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_TELEGRAM_PRIORITY", "1")),
            quality_threshold=float(os.getenv("REPURPOSE_TELEGRAM_QUALITY", "0.7"))
        ),
        ContentFormat.TWITTER_THREAD: FormatConfig(
            enabled=os.getenv("REPURPOSE_TWITTER_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_TWITTER_PRIORITY", "1")),
            quality_threshold=float(os.getenv("REPURPOSE_TWITTER_QUALITY", "0.8"))
        ),
        ContentFormat.INSTAGRAM_CAROUSEL: FormatConfig(
            enabled=os.getenv("REPURPOSE_INSTAGRAM_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_INSTAGRAM_PRIORITY", "2")),
            quality_threshold=float(os.getenv("REPURPOSE_INSTAGRAM_QUALITY", "0.7"))
        ),
        ContentFormat.INSTAGRAM_STORY: FormatConfig(
            enabled=os.getenv("REPURPOSE_STORY_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_STORY_PRIORITY", "3")),
            quality_threshold=float(os.getenv("REPURPOSE_STORY_QUALITY", "0.6"))
        ),
        ContentFormat.LINKEDIN_ARTICLE: FormatConfig(
            enabled=os.getenv("REPURPOSE_LINKEDIN_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_LINKEDIN_PRIORITY", "1")),
            quality_threshold=float(os.getenv("REPURPOSE_LINKEDIN_QUALITY", "0.8"))
        ),
        ContentFormat.YOUTUBE_SHORTS: FormatConfig(
            enabled=os.getenv("REPURPOSE_YOUTUBE_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_YOUTUBE_PRIORITY", "2")),
            quality_threshold=float(os.getenv("REPURPOSE_YOUTUBE_QUALITY", "0.7"))
        ),
        ContentFormat.TIKTOK_VIDEO: FormatConfig(
            enabled=os.getenv("REPURPOSE_TIKTOK_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_TIKTOK_PRIORITY", "3")),
            quality_threshold=float(os.getenv("REPURPOSE_TIKTOK_QUALITY", "0.6"))
        ),
        ContentFormat.PODCAST_SCRIPT: FormatConfig(
            enabled=os.getenv("REPURPOSE_PODCAST_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_PODCAST_PRIORITY", "2")),
            quality_threshold=float(os.getenv("REPURPOSE_PODCAST_QUALITY", "0.8"))
        ),
        ContentFormat.BLOG_POST: FormatConfig(
            enabled=os.getenv("REPURPOSE_BLOG_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_BLOG_PRIORITY", "1")),
            quality_threshold=float(os.getenv("REPURPOSE_BLOG_QUALITY", "0.8"))
        ),
        ContentFormat.NEWSLETTER: FormatConfig(
            enabled=os.getenv("REPURPOSE_NEWSLETTER_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_NEWSLETTER_PRIORITY", "2")),
            quality_threshold=float(os.getenv("REPURPOSE_NEWSLETTER_QUALITY", "0.7"))
        ),
        ContentFormat.PRESENTATION: FormatConfig(
            enabled=os.getenv("REPURPOSE_PRESENTATION_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_PRESENTATION_PRIORITY", "3")),
            quality_threshold=float(os.getenv("REPURPOSE_PRESENTATION_QUALITY", "0.7"))
        ),
        ContentFormat.INFOGRAPHIC: FormatConfig(
            enabled=os.getenv("REPURPOSE_INFOGRAPHIC_ENABLED", "true").lower() == "true",
            priority=int(os.getenv("REPURPOSE_INFOGRAPHIC_PRIORITY", "2")),
            quality_threshold=float(os.getenv("REPURPOSE_INFOGRAPHIC_QUALITY", "0.7"))
        )
    }
    
    # Определяем стратегию адаптации
    strategy_str = os.getenv("REPURPOSE_STRATEGY", "extract_key_points")
    try:
        strategy = AdaptationStrategy(strategy_str)
    except ValueError:
        strategy = AdaptationStrategy.EXTRACT_KEY_POINTS
    
    return RepurposeAgentConfig(
        agent_name=os.getenv("REPURPOSE_AGENT_NAME", "Repurpose Agent"),
        max_concurrent_tasks=int(os.getenv("REPURPOSE_MAX_CONCURRENT_TASKS", "3")),
        performance_score=float(os.getenv("REPURPOSE_PERFORMANCE_SCORE", "1.1")),
        
        enable_auto_adaptation=os.getenv("REPURPOSE_AUTO_ADAPTATION", "true").lower() == "true",
        enable_quality_checks=os.getenv("REPURPOSE_QUALITY_CHECKS", "true").lower() == "true",
        enable_brand_consistency=os.getenv("REPURPOSE_BRAND_CONSISTENCY", "true").lower() == "true",
        
        format_configs=format_configs,
        
        adaptation_config=AdaptationConfig(
            enabled=os.getenv("REPURPOSE_ADAPTATION_ENABLED", "true").lower() == "true",
            strategy=strategy,
            preserve_tone=os.getenv("REPURPOSE_PRESERVE_TONE", "true").lower() == "true",
            preserve_brand_voice=os.getenv("REPURPOSE_PRESERVE_BRAND", "true").lower() == "true",
            add_hashtags=os.getenv("REPURPOSE_ADD_HASHTAGS", "true").lower() == "true",
            add_call_to_action=os.getenv("REPURPOSE_ADD_CTA", "true").lower() == "true"
        ),
        
        quality_config=QualityConfig(
            min_word_count=int(os.getenv("REPURPOSE_MIN_WORDS", "50")),
            max_word_count=int(os.getenv("REPURPOSE_MAX_WORDS", "2000")),
            readability_score=float(os.getenv("REPURPOSE_READABILITY", "0.7")),
            engagement_potential=float(os.getenv("REPURPOSE_ENGAGEMENT", "0.6")),
            plagiarism_check=os.getenv("REPURPOSE_PLAGIARISM_CHECK", "false").lower() == "true",
            grammar_check=os.getenv("REPURPOSE_GRAMMAR_CHECK", "true").lower() == "true"
        ),
        
        cache=CacheConfig(
            enabled=os.getenv("REPURPOSE_CACHE_ENABLED", "true").lower() == "true",
            ttl_hours=int(os.getenv("REPURPOSE_CACHE_TTL_HOURS", "12")),
            max_size=int(os.getenv("REPURPOSE_CACHE_MAX_SIZE", "500")),
            cleanup_interval_hours=int(os.getenv("REPURPOSE_CACHE_CLEANUP_HOURS", "24"))
        ),
        
        enable_statistics=os.getenv("REPURPOSE_STATISTICS", "true").lower() == "true",
        log_detailed_reports=os.getenv("REPURPOSE_DETAILED_LOGS", "false").lower() == "true",
        enable_ai_enhancement=os.getenv("REPURPOSE_AI_ENHANCEMENT", "true").lower() == "true"
    )


# Предустановленные конфигурации
SOCIAL_MEDIA_FOCUS_CONFIG = RepurposeAgentConfig(
    agent_name="Repurpose Agent (Social Media Focus)",
    format_configs={
        ContentFormat.TELEGRAM_POST: FormatConfig(enabled=True, priority=1),
        ContentFormat.TWITTER_THREAD: FormatConfig(enabled=True, priority=1),
        ContentFormat.INSTAGRAM_CAROUSEL: FormatConfig(enabled=True, priority=1),
        ContentFormat.INSTAGRAM_STORY: FormatConfig(enabled=True, priority=2),
        ContentFormat.TIKTOK_VIDEO: FormatConfig(enabled=True, priority=2),
        ContentFormat.YOUTUBE_SHORTS: FormatConfig(enabled=True, priority=2),
        ContentFormat.LINKEDIN_ARTICLE: FormatConfig(enabled=False),
        ContentFormat.BLOG_POST: FormatConfig(enabled=False),
        ContentFormat.PODCAST_SCRIPT: FormatConfig(enabled=False),
        ContentFormat.NEWSLETTER: FormatConfig(enabled=False),
        ContentFormat.PRESENTATION: FormatConfig(enabled=False),
        ContentFormat.INFOGRAPHIC: FormatConfig(enabled=True, priority=3)
    },
    adaptation_config=AdaptationConfig(
        strategy=AdaptationStrategy.EXTRACT_KEY_POINTS,
        add_hashtags=True,
        add_call_to_action=True
    )
)

PROFESSIONAL_FOCUS_CONFIG = RepurposeAgentConfig(
    agent_name="Repurpose Agent (Professional Focus)",
    format_configs={
        ContentFormat.LINKEDIN_ARTICLE: FormatConfig(enabled=True, priority=1),
        ContentFormat.BLOG_POST: FormatConfig(enabled=True, priority=1),
        ContentFormat.NEWSLETTER: FormatConfig(enabled=True, priority=1),
        ContentFormat.PRESENTATION: FormatConfig(enabled=True, priority=2),
        ContentFormat.PODCAST_SCRIPT: FormatConfig(enabled=True, priority=2),
        ContentFormat.TELEGRAM_POST: FormatConfig(enabled=False),
        ContentFormat.TWITTER_THREAD: FormatConfig(enabled=False),
        ContentFormat.INSTAGRAM_CAROUSEL: FormatConfig(enabled=False),
        ContentFormat.INSTAGRAM_STORY: FormatConfig(enabled=False),
        ContentFormat.TIKTOK_VIDEO: FormatConfig(enabled=False),
        ContentFormat.YOUTUBE_SHORTS: FormatConfig(enabled=False),
        ContentFormat.INFOGRAPHIC: FormatConfig(enabled=True, priority=3)
    },
    adaptation_config=AdaptationConfig(
        strategy=AdaptationStrategy.EXPAND,
        preserve_tone=True,
        preserve_brand_voice=True
    )
)

VIDEO_FOCUS_CONFIG = RepurposeAgentConfig(
    agent_name="Repurpose Agent (Video Focus)",
    format_configs={
        ContentFormat.YOUTUBE_SHORTS: FormatConfig(enabled=True, priority=1),
        ContentFormat.TIKTOK_VIDEO: FormatConfig(enabled=True, priority=1),
        ContentFormat.INSTAGRAM_STORY: FormatConfig(enabled=True, priority=1),
        ContentFormat.PODCAST_SCRIPT: FormatConfig(enabled=True, priority=2),
        ContentFormat.TELEGRAM_POST: FormatConfig(enabled=True, priority=2),
        ContentFormat.TWITTER_THREAD: FormatConfig(enabled=True, priority=2),
        ContentFormat.INSTAGRAM_CAROUSEL: FormatConfig(enabled=True, priority=3),
        ContentFormat.LINKEDIN_ARTICLE: FormatConfig(enabled=False),
        ContentFormat.BLOG_POST: FormatConfig(enabled=False),
        ContentFormat.NEWSLETTER: FormatConfig(enabled=False),
        ContentFormat.PRESENTATION: FormatConfig(enabled=False),
        ContentFormat.INFOGRAPHIC: FormatConfig(enabled=True, priority=3)
    },
    adaptation_config=AdaptationConfig(
        strategy=AdaptationStrategy.SUMMARIZE,
        add_call_to_action=True
    )
)

ALL_FORMATS_CONFIG = RepurposeAgentConfig(
    agent_name="Repurpose Agent (All Formats)",
    max_concurrent_tasks=5,
    format_configs={
        format_type: FormatConfig(enabled=True, priority=1)
        for format_type in ContentFormat
    },
    adaptation_config=AdaptationConfig(
        strategy=AdaptationStrategy.EXTRACT_KEY_POINTS,
        preserve_tone=True,
        preserve_brand_voice=True,
        add_hashtags=True,
        add_call_to_action=True
    )
)
