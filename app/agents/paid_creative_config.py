"""
Конфигурация для Paid Creative Agent
Настройки создания рекламных креативов и оптимизации
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .paid_creative_agent import AdPlatform, AdFormat, AdObjective, ComplianceStatus


@dataclass
class CreativeConfig:
    """Конфигурация создания креативов"""
    enabled: bool = True
    max_headline_length: int = 30
    max_description_length: int = 90
    max_cta_length: int = 20
    template_customization: bool = True
    personalization: bool = True


@dataclass
class PlatformConfig:
    """Конфигурация платформы"""
    enabled: bool = True
    max_headline_length: int = 30
    max_description_length: int = 90
    max_cta_length: int = 20
    allowed_formats: List[AdFormat] = field(default_factory=list)
    prohibited_content: List[str] = field(default_factory=list)
    required_elements: List[str] = field(default_factory=list)
    targeting_options: List[str] = field(default_factory=list)


@dataclass
class ComplianceConfig:
    """Конфигурация соответствия политикам"""
    enabled: bool = True
    prohibited_keywords: List[str] = field(default_factory=list)
    restricted_keywords: List[str] = field(default_factory=list)
    required_disclaimers: List[str] = field(default_factory=list)
    age_restrictions: List[str] = field(default_factory=list)
    auto_review_threshold: float = 0.2
    auto_reject_threshold: float = 0.5


@dataclass
class ABTestConfig:
    """Конфигурация A/B тестирования"""
    enabled: bool = True
    max_variants: int = 5
    min_traffic_percentage: float = 10.0
    max_test_duration_days: int = 30
    confidence_level: float = 0.95
    statistical_significance_threshold: float = 0.05


@dataclass
class OptimizationConfig:
    """Конфигурация оптимизации"""
    enabled: bool = True
    min_ctr_threshold: float = 0.02
    min_conversion_rate_threshold: float = 0.01
    max_cpc_threshold: float = 10.0
    target_roi: float = 3.0
    optimization_frequency_hours: int = 24


@dataclass
class PaidCreativeAgentConfig:
    """Основная конфигурация Paid Creative Agent"""
    agent_name: str = "Paid Creative Agent"
    max_concurrent_tasks: int = 2
    performance_score: float = 0.9
    
    # Настройки создания креативов
    creative: CreativeConfig = field(default_factory=CreativeConfig)
    
    # Конфигурация платформ
    platforms: Dict[AdPlatform, PlatformConfig] = field(default_factory=dict)
    
    # Соответствие политикам
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    
    # A/B тестирование
    ab_testing: ABTestConfig = field(default_factory=ABTestConfig)
    
    # Оптимизация
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    
    # Дополнительные настройки
    enable_statistics: bool = True
    log_detailed_reports: bool = False
    enable_ai_enhancement: bool = True
    cache_ttl_hours: int = 24


def load_config_from_env() -> PaidCreativeAgentConfig:
    """Загружает конфигурацию из переменных окружения"""
    
    # Создаем конфигурации для платформ
    platform_configs = {
        AdPlatform.TELEGRAM_ADS: PlatformConfig(
            enabled=os.getenv("PAID_TELEGRAM_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_TELEGRAM_HEADLINE_LENGTH", "30")),
            max_description_length=int(os.getenv("PAID_TELEGRAM_DESCRIPTION_LENGTH", "90")),
            max_cta_length=int(os.getenv("PAID_TELEGRAM_CTA_LENGTH", "20")),
            allowed_formats=[AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD],
            prohibited_content=os.getenv("PAID_TELEGRAM_PROHIBITED", "криптовалюта,азартные игры,алкоголь").split(","),
            required_elements=["headline", "description", "cta"],
            targeting_options=["age", "gender", "location", "interests"]
        ),
        AdPlatform.VK_ADS: PlatformConfig(
            enabled=os.getenv("PAID_VK_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_VK_HEADLINE_LENGTH", "25")),
            max_description_length=int(os.getenv("PAID_VK_DESCRIPTION_LENGTH", "80")),
            max_cta_length=int(os.getenv("PAID_VK_CTA_LENGTH", "15")),
            allowed_formats=[AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.CAROUSEL_AD],
            prohibited_content=os.getenv("PAID_VK_PROHIBITED", "криптовалюта,азартные игры,алкоголь,табак").split(","),
            required_elements=["headline", "description", "cta"],
            targeting_options=["age", "gender", "location", "interests", "education"]
        ),
        AdPlatform.GOOGLE_ADS: PlatformConfig(
            enabled=os.getenv("PAID_GOOGLE_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_GOOGLE_HEADLINE_LENGTH", "30")),
            max_description_length=int(os.getenv("PAID_GOOGLE_DESCRIPTION_LENGTH", "90")),
            max_cta_length=int(os.getenv("PAID_GOOGLE_CTA_LENGTH", "25")),
            allowed_formats=[AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.DISPLAY_AD],
            prohibited_content=os.getenv("PAID_GOOGLE_PROHIBITED", "криптовалюта,азартные игры,алкоголь,табак,наркотики").split(","),
            required_elements=["headline", "description", "cta", "landing_page"],
            targeting_options=["age", "gender", "location", "interests", "keywords"]
        ),
        AdPlatform.YANDEX_DIRECT: PlatformConfig(
            enabled=os.getenv("PAID_YANDEX_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_YANDEX_HEADLINE_LENGTH", "33")),
            max_description_length=int(os.getenv("PAID_YANDEX_DESCRIPTION_LENGTH", "75")),
            max_cta_length=int(os.getenv("PAID_YANDEX_CTA_LENGTH", "20")),
            allowed_formats=[AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD],
            prohibited_content=os.getenv("PAID_YANDEX_PROHIBITED", "криптовалюта,азартные игры,алкоголь,табак").split(","),
            required_elements=["headline", "description", "cta", "landing_page"],
            targeting_options=["age", "gender", "location", "interests", "keywords"]
        ),
        AdPlatform.FACEBOOK_ADS: PlatformConfig(
            enabled=os.getenv("PAID_FACEBOOK_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_FACEBOOK_HEADLINE_LENGTH", "40")),
            max_description_length=int(os.getenv("PAID_FACEBOOK_DESCRIPTION_LENGTH", "125")),
            max_cta_length=int(os.getenv("PAID_FACEBOOK_CTA_LENGTH", "20")),
            allowed_formats=[AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.CAROUSEL_AD, AdFormat.STORY_AD],
            prohibited_content=os.getenv("PAID_FACEBOOK_PROHIBITED", "криптовалюта,азартные игры,алкоголь,табак,наркотики").split(","),
            required_elements=["headline", "description", "cta"],
            targeting_options=["age", "gender", "location", "interests", "behavior"]
        ),
        AdPlatform.INSTAGRAM_ADS: PlatformConfig(
            enabled=os.getenv("PAID_INSTAGRAM_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_INSTAGRAM_HEADLINE_LENGTH", "40")),
            max_description_length=int(os.getenv("PAID_INSTAGRAM_DESCRIPTION_LENGTH", "125")),
            max_cta_length=int(os.getenv("PAID_INSTAGRAM_CTA_LENGTH", "20")),
            allowed_formats=[AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.CAROUSEL_AD, AdFormat.STORY_AD],
            prohibited_content=os.getenv("PAID_INSTAGRAM_PROHIBITED", "криптовалюта,азартные игры,алкоголь,табак,наркотики").split(","),
            required_elements=["headline", "description", "cta"],
            targeting_options=["age", "gender", "location", "interests", "behavior"]
        ),
        AdPlatform.YOUTUBE_ADS: PlatformConfig(
            enabled=os.getenv("PAID_YOUTUBE_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_YOUTUBE_HEADLINE_LENGTH", "30")),
            max_description_length=int(os.getenv("PAID_YOUTUBE_DESCRIPTION_LENGTH", "90")),
            max_cta_length=int(os.getenv("PAID_YOUTUBE_CTA_LENGTH", "25")),
            allowed_formats=[AdFormat.VIDEO_AD, AdFormat.DISPLAY_AD],
            prohibited_content=os.getenv("PAID_YOUTUBE_PROHIBITED", "криптовалюта,азартные игры,алкоголь,табак,наркотики").split(","),
            required_elements=["headline", "description", "cta"],
            targeting_options=["age", "gender", "location", "interests", "keywords"]
        ),
        AdPlatform.TIKTOK_ADS: PlatformConfig(
            enabled=os.getenv("PAID_TIKTOK_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_TIKTOK_HEADLINE_LENGTH", "35")),
            max_description_length=int(os.getenv("PAID_TIKTOK_DESCRIPTION_LENGTH", "100")),
            max_cta_length=int(os.getenv("PAID_TIKTOK_CTA_LENGTH", "20")),
            allowed_formats=[AdFormat.VIDEO_AD, AdFormat.IMAGE_AD, AdFormat.CAROUSEL_AD],
            prohibited_content=os.getenv("PAID_TIKTOK_PROHIBITED", "криптовалюта,азартные игры,алкоголь,табак,наркотики").split(","),
            required_elements=["headline", "description", "cta"],
            targeting_options=["age", "gender", "location", "interests", "behavior"]
        )
    }
    
    return PaidCreativeAgentConfig(
        agent_name=os.getenv("PAID_AGENT_NAME", "Paid Creative Agent"),
        max_concurrent_tasks=int(os.getenv("PAID_MAX_CONCURRENT_TASKS", "2")),
        performance_score=float(os.getenv("PAID_PERFORMANCE_SCORE", "0.9")),
        
        creative=CreativeConfig(
            enabled=os.getenv("PAID_CREATIVE_ENABLED", "true").lower() == "true",
            max_headline_length=int(os.getenv("PAID_MAX_HEADLINE_LENGTH", "30")),
            max_description_length=int(os.getenv("PAID_MAX_DESCRIPTION_LENGTH", "90")),
            max_cta_length=int(os.getenv("PAID_MAX_CTA_LENGTH", "20")),
            template_customization=os.getenv("PAID_TEMPLATE_CUSTOMIZATION", "true").lower() == "true",
            personalization=os.getenv("PAID_PERSONALIZATION", "true").lower() == "true"
        ),
        
        platforms=platform_configs,
        
        compliance=ComplianceConfig(
            enabled=os.getenv("PAID_COMPLIANCE_ENABLED", "true").lower() == "true",
            prohibited_keywords=os.getenv("PAID_PROHIBITED_KEYWORDS", "криптовалюта,азартные игры,алкоголь,табак,наркотики").split(","),
            restricted_keywords=os.getenv("PAID_RESTRICTED_KEYWORDS", "бесплатно,скидка,акция,лучший,гарантия").split(","),
            required_disclaimers=os.getenv("PAID_REQUIRED_DISCLAIMERS", "результат может отличаться,индивидуальные результаты").split(","),
            age_restrictions=os.getenv("PAID_AGE_RESTRICTIONS", "18+,21+,только для взрослых").split(","),
            auto_review_threshold=float(os.getenv("PAID_AUTO_REVIEW_THRESHOLD", "0.2")),
            auto_reject_threshold=float(os.getenv("PAID_AUTO_REJECT_THRESHOLD", "0.5"))
        ),
        
        ab_testing=ABTestConfig(
            enabled=os.getenv("PAID_AB_TESTING_ENABLED", "true").lower() == "true",
            max_variants=int(os.getenv("PAID_MAX_VARIANTS", "5")),
            min_traffic_percentage=float(os.getenv("PAID_MIN_TRAFFIC_PERCENTAGE", "10.0")),
            max_test_duration_days=int(os.getenv("PAID_MAX_TEST_DURATION_DAYS", "30")),
            confidence_level=float(os.getenv("PAID_CONFIDENCE_LEVEL", "0.95")),
            statistical_significance_threshold=float(os.getenv("PAID_SIGNIFICANCE_THRESHOLD", "0.05"))
        ),
        
        optimization=OptimizationConfig(
            enabled=os.getenv("PAID_OPTIMIZATION_ENABLED", "true").lower() == "true",
            min_ctr_threshold=float(os.getenv("PAID_MIN_CTR_THRESHOLD", "0.02")),
            min_conversion_rate_threshold=float(os.getenv("PAID_MIN_CONVERSION_RATE_THRESHOLD", "0.01")),
            max_cpc_threshold=float(os.getenv("PAID_MAX_CPC_THRESHOLD", "10.0")),
            target_roi=float(os.getenv("PAID_TARGET_ROI", "3.0")),
            optimization_frequency_hours=int(os.getenv("PAID_OPTIMIZATION_FREQUENCY_HOURS", "24"))
        ),
        
        enable_statistics=os.getenv("PAID_STATISTICS", "true").lower() == "true",
        log_detailed_reports=os.getenv("PAID_DETAILED_LOGS", "false").lower() == "true",
        enable_ai_enhancement=os.getenv("PAID_AI_ENHANCEMENT", "true").lower() == "true",
        cache_ttl_hours=int(os.getenv("PAID_CACHE_TTL_HOURS", "24"))
    )


# Предустановленные конфигурации
SOCIAL_MEDIA_FOCUS_CONFIG = PaidCreativeAgentConfig(
    agent_name="Paid Creative Agent (Social Media Focus)",
    platforms={
        AdPlatform.TELEGRAM_ADS: PlatformConfig(enabled=True),
        AdPlatform.VK_ADS: PlatformConfig(enabled=True),
        AdPlatform.FACEBOOK_ADS: PlatformConfig(enabled=True),
        AdPlatform.INSTAGRAM_ADS: PlatformConfig(enabled=True),
        AdPlatform.TIKTOK_ADS: PlatformConfig(enabled=True),
        AdPlatform.GOOGLE_ADS: PlatformConfig(enabled=False),
        AdPlatform.YANDEX_DIRECT: PlatformConfig(enabled=False),
        AdPlatform.YOUTUBE_ADS: PlatformConfig(enabled=False)
    },
    creative=CreativeConfig(
        max_headline_length=35,
        max_description_length=100,
        template_customization=True,
        personalization=True
    ),
    compliance=ComplianceConfig(
        auto_review_threshold=0.3,
        auto_reject_threshold=0.6
    )
)

SEARCH_ENGINE_FOCUS_CONFIG = PaidCreativeAgentConfig(
    agent_name="Paid Creative Agent (Search Engine Focus)",
    platforms={
        AdPlatform.GOOGLE_ADS: PlatformConfig(enabled=True),
        AdPlatform.YANDEX_DIRECT: PlatformConfig(enabled=True),
        AdPlatform.TELEGRAM_ADS: PlatformConfig(enabled=False),
        AdPlatform.VK_ADS: PlatformConfig(enabled=False),
        AdPlatform.FACEBOOK_ADS: PlatformConfig(enabled=False),
        AdPlatform.INSTAGRAM_ADS: PlatformConfig(enabled=False),
        AdPlatform.TIKTOK_ADS: PlatformConfig(enabled=False),
        AdPlatform.YOUTUBE_ADS: PlatformConfig(enabled=False)
    },
    creative=CreativeConfig(
        max_headline_length=30,
        max_description_length=90,
        template_customization=True,
        personalization=False
    ),
    compliance=ComplianceConfig(
        auto_review_threshold=0.1,
        auto_reject_threshold=0.4
    )
)

VIDEO_FOCUS_CONFIG = PaidCreativeAgentConfig(
    agent_name="Paid Creative Agent (Video Focus)",
    platforms={
        AdPlatform.YOUTUBE_ADS: PlatformConfig(enabled=True),
        AdPlatform.TIKTOK_ADS: PlatformConfig(enabled=True),
        AdPlatform.INSTAGRAM_ADS: PlatformConfig(enabled=True),
        AdPlatform.FACEBOOK_ADS: PlatformConfig(enabled=True),
        AdPlatform.TELEGRAM_ADS: PlatformConfig(enabled=False),
        AdPlatform.VK_ADS: PlatformConfig(enabled=False),
        AdPlatform.GOOGLE_ADS: PlatformConfig(enabled=False),
        AdPlatform.YANDEX_DIRECT: PlatformConfig(enabled=False)
    },
    creative=CreativeConfig(
        max_headline_length=40,
        max_description_length=125,
        template_customization=True,
        personalization=True
    ),
    compliance=ComplianceConfig(
        auto_review_threshold=0.2,
        auto_reject_threshold=0.5
    )
)

ALL_PLATFORMS_CONFIG = PaidCreativeAgentConfig(
    agent_name="Paid Creative Agent (All Platforms)",
    max_concurrent_tasks=5,
    platforms={
        platform: PlatformConfig(enabled=True)
        for platform in AdPlatform
    },
    creative=CreativeConfig(
        max_headline_length=40,
        max_description_length=125,
        template_customization=True,
        personalization=True
    ),
    compliance=ComplianceConfig(
        auto_review_threshold=0.2,
        auto_reject_threshold=0.5
    ),
    ab_testing=ABTestConfig(
        max_variants=10,
        max_test_duration_days=60
    )
)
