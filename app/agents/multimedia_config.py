"""
Конфигурация для Multimedia Producer Agent
Содержит настройки для генерации изображений, оптимизации и интеграций
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ImageGenerationConfig:
    """Конфигурация генерации изображений"""
    
    # DALL-E настройки
    dalle_model: str = "dall-e-3"
    dalle_quality: str = "standard"  # standard, hd
    dalle_style: str = "vivid"       # vivid, natural
    dalle_max_retries: int = 3
    
    # Stable Diffusion настройки
    sd_model: str = "stable-diffusion-xl-base-1.0"
    sd_steps: int = 20
    sd_guidance_scale: float = 7.5
    sd_scheduler: str = "DPMSolverMultistepScheduler"
    
    # Общие настройки
    max_image_size: int = 1920
    default_format: str = "square"
    fallback_enabled: bool = True


@dataclass
class CacheConfig:
    """Конфигурация кэширования"""
    
    enabled: bool = True
    ttl_hours: int = 24
    max_cache_size_mb: int = 1024  # 1GB
    cache_dir: str = "cache/multimedia"
    cleanup_interval_hours: int = 6


@dataclass
class OptimizationConfig:
    """Конфигурация оптимизации изображений"""
    
    # Настройки для веб
    web_quality: int = 85
    web_max_width: int = 1920
    web_max_height: int = 1920
    web_format: str = "jpeg"
    
    # Настройки для социальных сетей
    social_quality: int = 90
    social_max_width: int = 1080
    social_max_height: int = 1080
    social_format: str = "jpeg"
    
    # Настройки для печати
    print_quality: int = 95
    print_max_width: int = 3000
    print_max_height: int = 3000
    print_format: str = "png"
    
    # Дополнительные настройки
    progressive_jpeg: bool = True
    optimize_png: bool = True
    strip_metadata: bool = True


@dataclass
class PlatformConfig:
    """Конфигурация платформ"""
    
    instagram: Dict[str, Any] = field(default_factory=lambda: {
        "formats": ["square", "vertical"],
        "max_file_size_mb": 30,
        "preferred_format": "jpeg"
    })
    
    facebook: Dict[str, Any] = field(default_factory=lambda: {
        "formats": ["square", "horizontal", "banner"],
        "max_file_size_mb": 10,
        "preferred_format": "jpeg"
    })
    
    youtube: Dict[str, Any] = field(default_factory=lambda: {
        "formats": ["horizontal"],
        "max_file_size_mb": 2,
        "preferred_format": "jpeg"
    })
    
    tiktok: Dict[str, Any] = field(default_factory=lambda: {
        "formats": ["vertical"],
        "max_file_size_mb": 10,
        "preferred_format": "jpeg"
    })
    
    twitter: Dict[str, Any] = field(default_factory=lambda: {
        "formats": ["horizontal", "banner"],
        "max_file_size_mb": 5,
        "preferred_format": "jpeg"
    })
    
    linkedin: Dict[str, Any] = field(default_factory=lambda: {
        "formats": ["horizontal"],
        "max_file_size_mb": 5,
        "preferred_format": "jpeg"
    })


@dataclass
class TemplateConfig:
    """Конфигурация шаблонов"""
    
    # Статистический шаблон
    stats_template: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "default_colors": ["#007bff", "#28a745", "#ffc107", "#dc3545"],
        "font_family": "DejaVu Sans",
        "max_text_length": 100
    })
    
    # Шаблон временной шкалы
    timeline_template: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "max_events": 6,
        "default_colors": ["#6c757d", "#007bff", "#28a745"],
        "font_family": "DejaVu Sans"
    })
    
    # Карусельный шаблон
    carousel_template: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "max_slides": 10,
        "default_format": "square",
        "transition_style": "fade"
    })


@dataclass
class APIConfig:
    """Конфигурация API интеграций"""
    
    # OpenAI (DALL-E)
    openai_api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout: int = 60
    
    # Stability AI (Stable Diffusion)
    stability_api_key: str = field(default_factory=lambda: os.getenv('STABLE_DIFFUSION_API_KEY', ''))
    stability_base_url: str = "https://api.stability.ai"
    stability_timeout: int = 120
    
    # Unsplash
    unsplash_api_key: str = field(default_factory=lambda: os.getenv('UNSPLASH_API_KEY', ''))
    unsplash_base_url: str = "https://api.unsplash.com"
    unsplash_timeout: int = 30
    
    # Общие настройки
    max_retries: int = 3
    retry_delay: int = 1
    rate_limit_delay: float = 0.1


@dataclass
class MultimediaAgentConfig:
    """Основная конфигурация Multimedia Producer Agent"""
    
    # Основные настройки
    agent_id: str = "multimedia_producer_agent"
    agent_name: str = "Multimedia Producer Agent"
    max_concurrent_tasks: int = 2
    performance_score: float = 0.8
    
    # Конфигурации компонентов
    image_generation: ImageGenerationConfig = field(default_factory=ImageGenerationConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    platforms: PlatformConfig = field(default_factory=PlatformConfig)
    templates: TemplateConfig = field(default_factory=TemplateConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Дополнительные настройки
    enable_logging: bool = True
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_port: int = 8080
    
    # Безопасность
    allowed_domains: List[str] = field(default_factory=lambda: [
        "api.openai.com",
        "api.stability.ai", 
        "api.unsplash.com"
    ])
    
    max_file_size_mb: int = 50
    allowed_formats: List[str] = field(default_factory=lambda: [
        "png", "jpeg", "jpg", "webp", "gif"
    ])


def load_config_from_env() -> MultimediaAgentConfig:
    """Загружает конфигурацию из переменных окружения"""
    
    config = MultimediaAgentConfig()
    
    # Переопределяем настройки из переменных окружения
    if os.getenv('MULTIMEDIA_CACHE_TTL_HOURS'):
        config.cache.ttl_hours = int(os.getenv('MULTIMEDIA_CACHE_TTL_HOURS'))
    
    if os.getenv('MULTIMEDIA_MAX_CONCURRENT_TASKS'):
        config.max_concurrent_tasks = int(os.getenv('MULTIMEDIA_MAX_CONCURRENT_TASKS'))
    
    if os.getenv('MULTIMEDIA_PERFORMANCE_SCORE'):
        config.performance_score = float(os.getenv('MULTIMEDIA_PERFORMANCE_SCORE'))
    
    if os.getenv('MULTIMEDIA_CACHE_DIR'):
        config.cache.cache_dir = os.getenv('MULTIMEDIA_CACHE_DIR')
    
    if os.getenv('MULTIMEDIA_LOG_LEVEL'):
        config.log_level = os.getenv('MULTIMEDIA_LOG_LEVEL')
    
    return config


def validate_config(config: MultimediaAgentConfig) -> bool:
    """Валидирует конфигурацию"""
    
    errors = []
    
    # Проверяем API ключи
    if not config.api.openai_api_key and not config.api.stability_api_key:
        errors.append("Необходим хотя бы один API ключ для генерации изображений")
    
    # Проверяем настройки кэша
    if config.cache.max_cache_size_mb <= 0:
        errors.append("Размер кэша должен быть больше 0")
    
    # Проверяем настройки оптимизации
    if not (1 <= config.optimization.web_quality <= 100):
        errors.append("Качество для веб должно быть от 1 до 100")
    
    # Проверяем настройки агента
    if config.max_concurrent_tasks <= 0:
        errors.append("Количество одновременных задач должно быть больше 0")
    
    if not (0.1 <= config.performance_score <= 2.0):
        errors.append("Performance score должен быть от 0.1 до 2.0")
    
    if errors:
        for error in errors:
            print(f"❌ Ошибка конфигурации: {error}")
        return False
    
    return True


# Глобальная конфигурация
DEFAULT_CONFIG = load_config_from_env()

# Валидируем конфигурацию при импорте
if not validate_config(DEFAULT_CONFIG):
    print("⚠️ Обнаружены ошибки в конфигурации Multimedia Producer Agent")
