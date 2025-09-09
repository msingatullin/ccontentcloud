"""
Wikipedia MCP интеграция
Доступ к Wikipedia API для проверки фактов
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
import httpx

from .base import BaseMCPIntegration, MCPResponse, MCPError, MCPStatus
from ..config import get_mcp_config

logger = logging.getLogger(__name__)


class WikipediaMCP(BaseMCPIntegration):
    """MCP интеграция для Wikipedia API"""
    
    def __init__(self):
        config = get_mcp_config('wikipedia')
        if not config:
            # Создаем базовую конфигурацию для Wikipedia (бесплатный API)
            config = type('Config', (), {
                'enabled': True,
                'api_key': None,
                'base_url': 'https://ru.wikipedia.org/api/rest_v1',
                'timeout': 20,
                'max_retries': 2,
                'retry_delay': 1.0,
                'fallback_enabled': True,
                'test_mode': True,
                'custom_params': {
                    'language': 'ru',
                    'format': 'json'
                }
            })()
        
        super().__init__('wikipedia', {
            'api_key': config.api_key,
            'base_url': config.base_url,
            'timeout': config.timeout,
            'max_retries': config.max_retries,
            'retry_delay': config.retry_delay,
            'fallback_enabled': config.fallback_enabled,
            'test_mode': config.test_mode
        })
        
        self.base_url = config.base_url
        self.language = config.custom_params.get('language', 'ru')
        self.format = config.custom_params.get('format', 'json')
        
        logger.info(f"WikipediaMCP инициализирован для языка: {self.language}")
    
    async def connect(self) -> MCPResponse:
        """Подключение к Wikipedia API"""
        try:
            self.status = MCPStatus.CONNECTING
            
            # Проверяем доступность API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/page/summary/Россия")
                
                if response.status_code == 200:
                    self.status = MCPStatus.CONNECTED
                    logger.info("Подключен к Wikipedia API")
                    return MCPResponse.success_response(
                        data={"status": "connected", "language": self.language}
                    )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="api_error",
                        message=f"Wikipedia API недоступен: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            self.status = MCPStatus.ERROR
            error = MCPError(
                service=self.service_name,
                error_type="connection_error",
                message=f"Ошибка подключения к Wikipedia: {str(e)}"
            )
            return MCPResponse.error_response(error)
    
    async def disconnect(self) -> MCPResponse:
        """Отключение от Wikipedia API"""
        self.status = MCPStatus.DISCONNECTED
        logger.info("Отключен от Wikipedia API")
        return MCPResponse.success_response(data={"status": "disconnected"})
    
    async def health_check(self) -> MCPResponse:
        """Проверка здоровья Wikipedia API"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/page/summary/Тест")
                
                if response.status_code == 200:
                    return MCPResponse.success_response(
                        data={"status": "healthy", "language": self.language}
                    )
                else:
                    return MCPResponse.error_response(
                        MCPError(
                            service=self.service_name,
                            error_type="health_check_failed",
                            message=f"Wikipedia API недоступен: HTTP {response.status_code}"
                        )
                    )
                    
        except Exception as e:
            return MCPResponse.error_response(
                MCPError(
                    service=self.service_name,
                    error_type="health_check_error",
                    message=str(e)
                )
            )
    
    async def search_general(self, query: str) -> MCPResponse:
        """Общий поиск в Wikipedia"""
        try:
            # Используем Wikipedia Search API
            search_url = f"https://{self.language}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 5,
                'srprop': 'snippet|timestamp'
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(search_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    search_results = data.get('query', {}).get('search', [])
                    
                    sources = []
                    evidence = []
                    
                    for result in search_results:
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        
                        sources.append(f"wikipedia:{title}")
                        evidence.append(f"Wikipedia: {title} - {snippet[:200]}...")
                    
                    return MCPResponse.success_response(
                        data={
                            'sources': sources,
                            'evidence': evidence,
                            'query': query,
                            'results_count': len(search_results)
                        },
                        metadata={
                            'language': self.language,
                            'search_type': 'general'
                        }
                    )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="search_failed",
                        message=f"Ошибка поиска в Wikipedia: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="search_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def search_historical(self, query: str) -> MCPResponse:
        """Поиск исторических данных в Wikipedia"""
        try:
            # Добавляем исторические ключевые слова к запросу
            historical_query = f"{query} история исторический"
            
            # Используем общий поиск с историческим контекстом
            result = await self.search_general(historical_query)
            
            if result.success:
                # Дополняем метаданные
                result.metadata['search_type'] = 'historical'
                result.metadata['original_query'] = query
                
                return result
            else:
                return result
                
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="historical_search_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def search_statistics(self, query: str) -> MCPResponse:
        """Поиск статистических данных в Wikipedia"""
        try:
            # Добавляем статистические ключевые слова к запросу
            stats_query = f"{query} статистика данные цифры"
            
            # Используем общий поиск со статистическим контекстом
            result = await self.search_general(stats_query)
            
            if result.success:
                # Дополняем метаданные
                result.metadata['search_type'] = 'statistical'
                result.metadata['original_query'] = query
                
                return result
            else:
                return result
                
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="statistical_search_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def search_scientific(self, query: str) -> MCPResponse:
        """Поиск научных данных в Wikipedia"""
        try:
            # Добавляем научные ключевые слова к запросу
            scientific_query = f"{query} наука исследование ученые"
            
            # Используем общий поиск с научным контекстом
            result = await self.search_general(scientific_query)
            
            if result.success:
                # Дополняем метаданные
                result.metadata['search_type'] = 'scientific'
                result.metadata['original_query'] = query
                
                return result
            else:
                return result
                
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="scientific_search_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def get_page_summary(self, title: str) -> MCPResponse:
        """Получение краткого описания страницы Wikipedia"""
        try:
            # Используем Wikipedia REST API для получения summary
            summary_url = f"{self.base_url}/page/summary/{title}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(summary_url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return MCPResponse.success_response(
                        data={
                            'title': data.get('title', ''),
                            'extract': data.get('extract', ''),
                            'description': data.get('description', ''),
                            'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            'thumbnail': data.get('thumbnail', {}).get('source', '') if data.get('thumbnail') else None
                        },
                        metadata={
                            'language': self.language,
                            'page_title': title
                        }
                    )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="page_summary_failed",
                        message=f"Ошибка получения summary страницы: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="page_summary_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def get_page_sources(self, title: str) -> MCPResponse:
        """Получение источников страницы Wikipedia"""
        try:
            # Используем Wikipedia API для получения ссылок
            sources_url = f"https://{self.language}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'prop': 'extlinks',
                'titles': title,
                'ellimit': 20
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(sources_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    pages = data.get('query', {}).get('pages', {})
                    
                    sources = []
                    for page_id, page_data in pages.items():
                        extlinks = page_data.get('extlinks', [])
                        for link in extlinks:
                            url = link.get('*', '')
                            if url:
                                sources.append(url)
                    
                    return MCPResponse.success_response(
                        data={
                            'sources': sources,
                            'sources_count': len(sources),
                            'page_title': title
                        },
                        metadata={
                            'language': self.language,
                            'search_type': 'sources'
                        }
                    )
                else:
                    raise MCPError(
                        service=self.service_name,
                        error_type="sources_failed",
                        message=f"Ошибка получения источников: HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            error = MCPError(
                service=self.service_name,
                error_type="sources_error",
                message=str(e)
            )
            return MCPResponse.error_response(error)
    
    async def _fallback_operation(self, operation: str, *args, **kwargs) -> MCPResponse:
        """Fallback для Wikipedia операций"""
        logger.info(f"Выполняем fallback для Wikipedia операции: {operation}")
        
        # Для тестового режима возвращаем мок данные
        if self.config.get('test_mode', True):
            if operation == 'search_general':
                query = args[0] if args else 'test query'
                return MCPResponse.success_response(
                    data={
                        'sources': [f'wikipedia:test_article_{i}' for i in range(3)],
                        'evidence': [
                            f'Wikipedia: Тестовая статья 1 - информация о {query}',
                            f'Wikipedia: Тестовая статья 2 - дополнительные данные о {query}',
                            f'Wikipedia: Тестовая статья 3 - подробности о {query}'
                        ],
                        'query': query,
                        'results_count': 3
                    },
                    metadata={
                        'fallback': True,
                        'test_mode': True,
                        'operation': operation,
                        'language': self.language
                    }
                )
            elif operation == 'search_historical':
                query = args[0] if args else 'test historical query'
                return MCPResponse.success_response(
                    data={
                        'sources': [f'wikipedia:historical_{i}' for i in range(2)],
                        'evidence': [
                            f'Wikipedia: Историческая статья 1 - {query} в истории',
                            f'Wikipedia: Историческая статья 2 - исторические данные о {query}'
                        ],
                        'query': query,
                        'results_count': 2
                    },
                    metadata={
                        'fallback': True,
                        'test_mode': True,
                        'operation': operation,
                        'language': self.language
                    }
                )
            elif operation == 'search_statistics':
                query = args[0] if args else 'test statistical query'
                return MCPResponse.success_response(
                    data={
                        'sources': [f'wikipedia:stats_{i}' for i in range(2)],
                        'evidence': [
                            f'Wikipedia: Статистическая статья 1 - данные о {query}',
                            f'Wikipedia: Статистическая статья 2 - статистика по {query}'
                        ],
                        'query': query,
                        'results_count': 2
                    },
                    metadata={
                        'fallback': True,
                        'test_mode': True,
                        'operation': operation,
                        'language': self.language
                    }
                )
            elif operation == 'search_scientific':
                query = args[0] if args else 'test scientific query'
                return MCPResponse.success_response(
                    data={
                        'sources': [f'wikipedia:scientific_{i}' for i in range(2)],
                        'evidence': [
                            f'Wikipedia: Научная статья 1 - исследования {query}',
                            f'Wikipedia: Научная статья 2 - научные данные о {query}'
                        ],
                        'query': query,
                        'results_count': 2
                    },
                    metadata={
                        'fallback': True,
                        'test_mode': True,
                        'operation': operation,
                        'language': self.language
                    }
                )
        
        # Если не тестовый режим, возвращаем ошибку
        return MCPResponse.error_response(
            MCPError(
                service=self.service_name,
                error_type="fallback_used",
                message=f"Wikipedia API недоступен, fallback для {operation}",
                details={
                    'original_operation': operation,
                    'fallback_reason': 'service_unavailable'
                }
            )
        )
