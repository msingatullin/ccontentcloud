"""
Конфигурация MCP серверов
Централизованное управление настройками всех интеграций
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


@dataclass
class MCPConfig:
    """Конфигурация для MCP интеграции"""
    enabled: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: Optional[int] = None
    fallback_enabled: bool = True
    test_mode: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


class MCPConfigManager:
    """Менеджер конфигурации MCP серверов"""
    
    def __init__(self):
        self.configs: Dict[str, MCPConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Загружает конфигурации всех MCP серверов"""
        
        # Telegram Bot API
        self.configs['telegram'] = MCPConfig(
            enabled=bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            api_key=os.getenv('TELEGRAM_BOT_TOKEN'),
            base_url='https://api.telegram.org/bot',
            timeout=30,
            max_retries=3,
            retry_delay=1.0,
            rate_limit=30,  # 30 сообщений в секунду
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
                'chat_id': os.getenv('TELEGRAM_CHAT_ID', '@your_channel')
            }
        )
        
        # OpenAI API
        self.configs['openai'] = MCPConfig(
            enabled=bool(os.getenv('OPENAI_API_KEY')),
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url='https://api.openai.com/v1',
            timeout=60,
            max_retries=2,
            retry_delay=2.0,
            rate_limit=60,  # 60 запросов в минуту
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'model': 'gpt-5-mini',  # Обновлено на GPT-5-mini
                'temperature': 0.7,
                'max_tokens': 2000
            }
        )
        
        # HuggingFace API
        self.configs['huggingface'] = MCPConfig(
            enabled=bool(os.getenv('HUGGINGFACE_API_KEY')),
            api_key=os.getenv('HUGGINGFACE_API_KEY'),
            base_url='https://api-inference.huggingface.co',
            timeout=45,
            max_retries=2,
            retry_delay=1.5,
            rate_limit=1000,  # 1000 запросов в час
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'wait_for_model': True,
                'use_cache': True
            }
        )
        
        # VK API
        self.configs['vk'] = MCPConfig(
            enabled=bool(os.getenv('VK_API_TOKEN')),
            api_key=os.getenv('VK_API_TOKEN'),
            base_url='https://api.vk.com/method',
            timeout=30,
            max_retries=3,
            retry_delay=1.0,
            rate_limit=20,  # 20 запросов в секунду
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'v': '5.131',
                'lang': 'ru'
            }
        )
        
        # Instagram API
        self.configs['instagram'] = MCPConfig(
            enabled=bool(os.getenv('INSTAGRAM_ACCESS_TOKEN')),
            api_key=os.getenv('INSTAGRAM_ACCESS_TOKEN'),
            base_url='https://graph.instagram.com',
            timeout=30,
            max_retries=2,
            retry_delay=2.0,
            rate_limit=200,  # 200 запросов в час
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'fields': 'id,caption,media_type,media_url,permalink'
            }
        )
        
        # Twitter API
        self.configs['twitter'] = MCPConfig(
            enabled=bool(os.getenv('TWITTER_API_KEY')),
            api_key=os.getenv('TWITTER_API_KEY'),
            base_url='https://api.twitter.com/2',
            timeout=30,
            max_retries=2,
            retry_delay=2.0,
            rate_limit=300,  # 300 твитов в 15 минут
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'api_secret': os.getenv('TWITTER_API_SECRET'),
                'tweet.fields': 'created_at,public_metrics'
            }
        )
        
        # News API
        self.configs['news'] = MCPConfig(
            enabled=bool(os.getenv('NEWS_API_KEY')),
            api_key=os.getenv('NEWS_API_KEY'),
            base_url='https://newsapi.org/v2',
            timeout=20,
            max_retries=2,
            retry_delay=1.0,
            rate_limit=1000,  # 1000 запросов в день
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'language': 'ru',
                'sortBy': 'publishedAt'
            }
        )
        
        # Analytics API (Google Analytics)
        self.configs['analytics'] = MCPConfig(
            enabled=bool(os.getenv('GOOGLE_ANALYTICS_KEY')),
            api_key=os.getenv('GOOGLE_ANALYTICS_KEY'),
            base_url='https://analyticsdata.googleapis.com/v1beta',
            timeout=30,
            max_retries=2,
            retry_delay=2.0,
            rate_limit=100,  # 100 запросов в 100 секунд
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'metrics': 'sessions,pageviews,users'
            }
        )
        
        # Wikipedia API (бесплатный)
        self.configs['wikipedia'] = MCPConfig(
            enabled=True,  # Wikipedia API бесплатный
            api_key=None,
            base_url='https://ru.wikipedia.org/api/rest_v1',
            timeout=20,
            max_retries=2,
            retry_delay=1.0,
            rate_limit=500,  # 500 запросов в час
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'language': 'ru',
                'format': 'json'
            }
        )
        
        # Google Trends API (бесплатный)
        self.configs['google_trends'] = MCPConfig(
            enabled=True,
            api_key=None,
            base_url='https://trends.google.com/trends/api',
            timeout=30,
            max_retries=2,
            retry_delay=2.0,
            rate_limit=100,  # 100 запросов в час
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'True').lower() == 'true',
            custom_params={
                'language': 'ru',
                'region': 'RU'
            }
        )
        
        # Google Vertex AI (Gemini + Imagen)
        # Использует Application Default Credentials в Cloud Run
        self.configs['vertex_ai'] = MCPConfig(
            enabled=bool(os.getenv('GOOGLE_CLOUD_PROJECT')),
            api_key=None,  # Не нужен - используем ADC
            base_url=None,  # SDK сам определяет URL
            timeout=60,
            max_retries=3,
            retry_delay=2.0,
            rate_limit=60,  # 60 запросов в минуту
            fallback_enabled=True,
            test_mode=os.getenv('TEST_MODE', 'False').lower() == 'true',
            custom_params={
                'project_id': os.getenv('GOOGLE_CLOUD_PROJECT', os.getenv('GCP_PROJECT_ID')),
                'location': os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1'),
                'text_model': os.getenv('VERTEX_AI_TEXT_MODEL', 'gemini-1.5-flash-001'),
                'image_model': os.getenv('VERTEX_AI_IMAGE_MODEL', 'imagegeneration@006'),
                'grounding_enabled': os.getenv('VERTEX_AI_GROUNDING', 'true').lower() == 'true'
            }
        )
    
    def get_config(self, service_name: str) -> Optional[MCPConfig]:
        """Получает конфигурацию для сервиса"""
        return self.configs.get(service_name)
    
    def is_enabled(self, service_name: str) -> bool:
        """Проверяет, включен ли сервис"""
        config = self.get_config(service_name)
        return config is not None and config.enabled
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """Получает API ключ для сервиса"""
        config = self.get_config(service_name)
        return config.api_key if config else None
    
    def get_all_configs(self) -> Dict[str, MCPConfig]:
        """Возвращает все конфигурации"""
        return self.configs.copy()
    
    def get_enabled_services(self) -> list[str]:
        """Возвращает список включенных сервисов"""
        return [name for name, config in self.configs.items() if config.enabled]
    
    def update_config(self, service_name: str, **kwargs) -> bool:
        """Обновляет конфигурацию сервиса"""
        if service_name not in self.configs:
            return False
        
        config = self.configs[service_name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return True
    
    def validate_configs(self) -> Dict[str, list[str]]:
        """Валидирует все конфигурации и возвращает ошибки"""
        errors = {}
        
        for service_name, config in self.configs.items():
            service_errors = []
            
            if config.enabled:
                if not config.api_key:
                    service_errors.append("API ключ не установлен")
                
                if not config.base_url:
                    service_errors.append("Base URL не установлен")
                
                if config.timeout <= 0:
                    service_errors.append("Timeout должен быть больше 0")
                
                if config.max_retries < 0:
                    service_errors.append("Max retries не может быть отрицательным")
            
            if service_errors:
                errors[service_name] = service_errors
        
        return errors
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Возвращает сводку статуса всех сервисов"""
        enabled_count = len(self.get_enabled_services())
        total_count = len(self.configs)
        errors = self.validate_configs()
        
        return {
            "total_services": total_count,
            "enabled_services": enabled_count,
            "disabled_services": total_count - enabled_count,
            "services_with_errors": len(errors),
            "errors": errors,
            "test_mode": any(config.test_mode for config in self.configs.values())
        }


# Глобальный экземпляр менеджера конфигурации
config_manager = MCPConfigManager()


def get_mcp_config(service_name: str) -> Optional[MCPConfig]:
    """Удобная функция для получения конфигурации"""
    return config_manager.get_config(service_name)


def is_mcp_enabled(service_name: str) -> bool:
    """Удобная функция для проверки включения сервиса"""
    return config_manager.is_enabled(service_name)


def get_mcp_api_key(service_name: str) -> Optional[str]:
    """Удобная функция для получения API ключа"""
    return config_manager.get_api_key(service_name)
