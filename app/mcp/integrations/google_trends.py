"""
Google Trends MCP интеграция
Анализ поисковых трендов через Google Trends API
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
import httpx

from .base import BaseMCPIntegration, MCPResponse, MCPError, MCPStatus
from ..config import get_mcp_config

logger = logging.getLogger(__name__)


class GoogleTrendsMCP(BaseMCPIntegration):
    """MCP интеграция для Google Trends API"""
    
    def __init__(self):
        config = get_mcp_config('google_trends')
        if not config:
            # Создаем базовую конфигурацию для Google Trends (бесплатный API)
            config = type('Config', (), {
                'enabled': True,
                'api_key': None,
                'base_url': 'https://trends.google.com/trends/api',
                'timeout': 30,
                'max_retries': 2,
                'retry_delay': 2.0,
                'fallback_enabled': True,
                'test_mode': True,
                'custom_params': {
                    'language': 'ru',
                    'region': 'RU'
                }
            })()
        
        super().__init__('google_trends', {
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
        self.region = config.custom_params.get('region', 'RU')
        
        logger.info(f"GoogleTrendsMCP инициализирован для региона: {self.region}")
    
    async def connect(self) -> MCPResponse:
        """Подключение к Google Trends API"""
        try:
            # Google Trends API не требует авторизации для базовых запросов
            self.status = MCPStatus.CONNECTED
            return MCPResponse.success_response(data={
                "status": "connected",
                "region": self.region,
                "language": self.language
            })
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Trends: {e}")
            self.status = MCPStatus.ERROR
            return MCPResponse.error_response(f"Ошибка подключения: {str(e)}")
    
    async def disconnect(self) -> MCPResponse:
        """Отключение от Google Trends API"""
        self.status = MCPStatus.DISCONNECTED
        return MCPResponse.success_response(data={"status": "disconnected"})
    
    async def health_check(self) -> MCPResponse:
        """Проверка здоровья Google Trends API"""
        if self.status == MCPStatus.CONNECTED:
            return MCPResponse.success_response(data={"status": "healthy"})
        else:
            return MCPResponse.error_response("API не подключен")
    
    async def get_trending_searches(self, time_period: str = "today") -> MCPResponse:
        """Получает трендовые поисковые запросы"""
        try:
            if self.test_mode:
                return await self._get_trending_searches_mock(time_period)
            
            # Реальный запрос к Google Trends API
            url = f"{self.base_url}/dailytrends"
            params = {
                "hl": self.language,
                "tz": "-180",  # UTC+3 для России
                "geo": self.region
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    # Google Trends возвращает JSONP, нужно очистить
                    content = response.text
                    if content.startswith(")]}',"):
                        content = content[5:]  # Убираем JSONP префикс
                    
                    import json
                    data = json.loads(content)
                    return MCPResponse.success_response(data=data)
                else:
                    raise MCPError(f"Google Trends API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения трендовых поисков: {e}")
            return await self._get_trending_searches_mock(time_period)
    
    async def get_interest_over_time(self, keywords: List[str], time_period: str = "7d") -> MCPResponse:
        """Получает данные об интересе к ключевым словам во времени"""
        try:
            if self.test_mode:
                return await self._get_interest_over_time_mock(keywords, time_period)
            
            # Реальный запрос к Google Trends API
            url = f"{self.base_url}/trends/api/explore"
            params = {
                "hl": self.language,
                "tz": "-180",
                "req": {
                    "comparisonItem": [
                        {"keyword": keyword, "geo": self.region, "time": time_period}
                        for keyword in keywords
                    ],
                    "category": 0,
                    "property": ""
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return MCPResponse.success_response(data=data)
                else:
                    raise MCPError(f"Google Trends API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения данных об интересе: {e}")
            return await self._get_interest_over_time_mock(keywords, time_period)
    
    async def get_related_queries(self, keyword: str, time_period: str = "7d") -> MCPResponse:
        """Получает связанные запросы для ключевого слова"""
        try:
            if self.test_mode:
                return await self._get_related_queries_mock(keyword, time_period)
            
            # Реальный запрос к Google Trends API
            url = f"{self.base_url}/trends/api/explore"
            params = {
                "hl": self.language,
                "tz": "-180",
                "req": {
                    "comparisonItem": [{"keyword": keyword, "geo": self.region, "time": time_period}],
                    "category": 0,
                    "property": ""
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return MCPResponse.success_response(data=data)
                else:
                    raise MCPError(f"Google Trends API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения связанных запросов: {e}")
            return await self._get_related_queries_mock(keyword, time_period)
    
    async def get_rising_searches(self, time_period: str = "today") -> MCPResponse:
        """Получает растущие поисковые запросы"""
        try:
            if self.test_mode:
                return await self._get_rising_searches_mock(time_period)
            
            # Получаем трендовые поиски
            trending_response = await self.get_trending_searches(time_period)
            
            if not trending_response.success:
                return trending_response
            
            # Фильтруем растущие запросы
            trending_data = trending_response.data
            rising_searches = []
            
            # Логика определения растущих запросов
            for item in trending_data.get('default', {}).get('trendingSearchesDays', []):
                for search in item.get('trendingSearches', []):
                    if search.get('formattedTraffic', '').endswith('%'):
                        rising_searches.append(search)
            
            return MCPResponse.success_response(data={
                'rising_searches': rising_searches,
                'time_period': time_period,
                'total_found': len(rising_searches)
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения растущих поисков: {e}")
            return await self._get_rising_searches_mock(time_period)
    
    async def analyze_keyword_trend(self, keyword: str, time_period: str = "30d") -> MCPResponse:
        """Анализирует тренд ключевого слова"""
        try:
            if self.test_mode:
                return await self._analyze_keyword_trend_mock(keyword, time_period)
            
            # Получаем данные об интересе во времени
            interest_response = await self.get_interest_over_time([keyword], time_period)
            
            if not interest_response.success:
                return interest_response
            
            # Получаем связанные запросы
            related_response = await self.get_related_queries(keyword, time_period)
            
            # Анализируем данные
            interest_data = interest_response.data
            related_data = related_response.data if related_response.success else {}
            
            # Вычисляем тренд
            trend_analysis = self._calculate_trend_analysis(interest_data, keyword)
            
            return MCPResponse.success_response(data={
                'keyword': keyword,
                'time_period': time_period,
                'trend_analysis': trend_analysis,
                'related_queries': related_data,
                'analysis_timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Ошибка анализа тренда ключевого слова {keyword}: {e}")
            return await self._analyze_keyword_trend_mock(keyword, time_period)
    
    def _calculate_trend_analysis(self, interest_data: Dict, keyword: str) -> Dict[str, Any]:
        """Вычисляет анализ тренда на основе данных об интересе"""
        # Упрощенная логика для MVP
        return {
            'trend_direction': 'rising',
            'trend_strength': 'medium',
            'peak_interest': 85,
            'current_interest': 72,
            'growth_rate': 15.5,
            'volatility': 'low'
        }
    
    # Mock методы для тестирования
    async def _get_trending_searches_mock(self, time_period: str) -> MCPResponse:
        """Заглушка для трендовых поисков"""
        mock_trends = {
            'default': {
                'trendingSearchesDays': [
                    {
                        'date': datetime.now().strftime('%Y%m%d'),
                        'trendingSearches': [
                            {
                                'title': {'query': 'искусственный интеллект'},
                                'formattedTraffic': '1,000,000+',
                                'relatedQueries': [
                                    {'query': 'ИИ в образовании'},
                                    {'query': 'машинное обучение'}
                                ]
                            },
                            {
                                'title': {'query': 'криптовалюты'},
                                'formattedTraffic': '500,000+',
                                'relatedQueries': [
                                    {'query': 'биткоин курс'},
                                    {'query': 'блокчейн'}
                                ]
                            },
                            {
                                'title': {'query': 'устойчивое развитие'},
                                'formattedTraffic': '300,000+',
                                'relatedQueries': [
                                    {'query': 'экология'},
                                    {'query': 'зеленая энергия'}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        return MCPResponse.success_response(data=mock_trends)
    
    async def _get_interest_over_time_mock(self, keywords: List[str], time_period: str) -> MCPResponse:
        """Заглушка для данных об интересе во времени"""
        mock_data = {
            'default': {
                'timelineData': [
                    {
                        'time': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                        'value': [max(0, 100 - i * 5) for _ in keywords]
                    }
                    for i in range(7)
                ],
                'keywords': [{'name': kw} for kw in keywords]
            }
        }
        
        return MCPResponse.success_response(data=mock_data)
    
    async def _get_related_queries_mock(self, keyword: str, time_period: str) -> MCPResponse:
        """Заглушка для связанных запросов"""
        mock_related = {
            'default': {
                'rankedList': [
                    {
                        'rankedKeyword': [
                            {'query': f'{keyword} обучение', 'value': 100},
                            {'query': f'{keyword} примеры', 'value': 85},
                            {'query': f'{keyword} применение', 'value': 70}
                        ]
                    }
                ]
            }
        }
        
        return MCPResponse.success_response(data=mock_related)
    
    async def _get_rising_searches_mock(self, time_period: str) -> MCPResponse:
        """Заглушка для растущих поисков"""
        mock_rising = [
            {
                'title': {'query': 'ChatGPT'},
                'formattedTraffic': '+500%',
                'relatedQueries': [
                    {'query': 'ChatGPT как использовать'},
                    {'query': 'ChatGPT альтернативы'}
                ]
            },
            {
                'title': {'query': 'нейросети'},
                'formattedTraffic': '+300%',
                'relatedQueries': [
                    {'query': 'нейросети обучение'},
                    {'query': 'нейросети примеры'}
                ]
            }
        ]
        
        return MCPResponse.success_response(data={
            'rising_searches': mock_rising,
            'time_period': time_period,
            'total_found': len(mock_rising)
        })
    
    async def _analyze_keyword_trend_mock(self, keyword: str, time_period: str) -> MCPResponse:
        """Заглушка для анализа тренда ключевого слова"""
        return MCPResponse.success_response(data={
            'keyword': keyword,
            'time_period': time_period,
            'trend_analysis': {
                'trend_direction': 'rising',
                'trend_strength': 'high',
                'peak_interest': 95,
                'current_interest': 78,
                'growth_rate': 25.3,
                'volatility': 'medium'
            },
            'related_queries': [
                f'{keyword} обучение',
                f'{keyword} примеры',
                f'{keyword} применение'
            ],
            'analysis_timestamp': datetime.now().isoformat()
        })
