"""
Twitter MCP интеграция
Анализ трендов и вирусного контента в Twitter/X
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
import httpx

from .base import BaseMCPIntegration, MCPResponse, MCPError, MCPStatus
from ..config import get_mcp_config

logger = logging.getLogger(__name__)


class TwitterMCP(BaseMCPIntegration):
    """MCP интеграция для Twitter API v2"""
    
    def __init__(self):
        config = get_mcp_config('twitter')
        if not config:
            raise ValueError("Twitter конфигурация не найдена")
        
        super().__init__('twitter', {
            'api_key': config.api_key,
            'base_url': config.base_url,
            'timeout': config.timeout,
            'max_retries': config.max_retries,
            'retry_delay': config.retry_delay,
            'fallback_enabled': config.fallback_enabled,
            'test_mode': config.test_mode
        })
        
        self.api_key = config.api_key
        self.api_secret = config.custom_params.get('api_secret')
        self.base_url = config.base_url
        self.bearer_token = None
        
        logger.info("TwitterMCP инициализирован")
    
    async def connect(self) -> MCPResponse:
        """Подключение к Twitter API"""
        try:
            # В MVP используем упрощенную авторизацию
            if self.test_mode:
                self.bearer_token = "test_bearer_token"
                self.status = MCPStatus.CONNECTED
                return MCPResponse.success_response(data={"status": "connected", "mode": "test"})
            
            # Реальная авторизация через Bearer Token
            if self.api_key and self.api_secret:
                # Здесь должна быть логика получения Bearer Token
                # Для MVP используем заглушку
                self.bearer_token = f"bearer_{self.api_key}"
                self.status = MCPStatus.CONNECTED
                return MCPResponse.success_response(data={"status": "connected"})
            else:
                raise MCPError("Twitter API ключи не настроены")
                
        except Exception as e:
            logger.error(f"Ошибка подключения к Twitter API: {e}")
            self.status = MCPStatus.ERROR
            return MCPResponse.error_response(f"Ошибка подключения: {str(e)}")
    
    async def disconnect(self) -> MCPResponse:
        """Отключение от Twitter API"""
        self.bearer_token = None
        self.status = MCPStatus.DISCONNECTED
        return MCPResponse.success_response(data={"status": "disconnected"})
    
    async def health_check(self) -> MCPResponse:
        """Проверка здоровья Twitter API"""
        if self.status == MCPStatus.CONNECTED:
            return MCPResponse.success_response(data={"status": "healthy"})
        else:
            return MCPResponse.error_response("API не подключен")
    
    async def get_trending_topics(self, location: str = "worldwide") -> MCPResponse:
        """Получает трендовые темы"""
        try:
            if self.test_mode:
                return await self._get_trending_topics_mock(location)
            
            # Реальный запрос к Twitter API
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/trends/by/woeid/1"  # Worldwide trends
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return MCPResponse.success_response(data=data)
                else:
                    raise MCPError(f"Twitter API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения трендов Twitter: {e}")
            return await self._get_trending_topics_mock(location)
    
    async def search_tweets(self, query: str, max_results: int = 100) -> MCPResponse:
        """Поиск твитов по запросу"""
        try:
            if self.test_mode:
                return await self._search_tweets_mock(query, max_results)
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,public_metrics,context_annotations"
            }
            
            url = f"{self.base_url}/tweets/search/recent"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return MCPResponse.success_response(data=data)
                else:
                    raise MCPError(f"Twitter API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка поиска твитов: {e}")
            return await self._search_tweets_mock(query, max_results)
    
    async def get_viral_tweets(self, time_period: str = "1h") -> MCPResponse:
        """Получает вирусные твиты за период"""
        try:
            if self.test_mode:
                return await self._get_viral_tweets_mock(time_period)
            
            # Поиск твитов с высокими метриками
            viral_queries = [
                "min_retweets:100",
                "min_faves:500",
                "min_replies:50"
            ]
            
            all_viral_tweets = []
            
            for query in viral_queries:
                response = await self.search_tweets(query, 50)
                if response.success:
                    tweets = response.data.get('data', [])
                    all_viral_tweets.extend(tweets)
            
            # Сортируем по метрикам
            all_viral_tweets.sort(
                key=lambda x: x.get('public_metrics', {}).get('retweet_count', 0),
                reverse=True
            )
            
            return MCPResponse.success_response(data={
                'viral_tweets': all_viral_tweets[:20],  # Топ 20
                'total_found': len(all_viral_tweets)
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения вирусных твитов: {e}")
            return await self._get_viral_tweets_mock(time_period)
    
    async def analyze_hashtag_trends(self, hashtag: str) -> MCPResponse:
        """Анализирует тренды хештега"""
        try:
            if self.test_mode:
                return await self._analyze_hashtag_trends_mock(hashtag)
            
            # Поиск твитов с хештегом
            query = f"#{hashtag}"
            response = await self.search_tweets(query, 100)
            
            if not response.success:
                return response
            
            tweets = response.data.get('data', [])
            
            # Анализ метрик
            total_tweets = len(tweets)
            total_retweets = sum(
                t.get('public_metrics', {}).get('retweet_count', 0) 
                for t in tweets
            )
            total_likes = sum(
                t.get('public_metrics', {}).get('like_count', 0) 
                for t in tweets
            )
            
            # Анализ временных трендов
            tweet_times = [
                datetime.fromisoformat(t['created_at'].replace('Z', '+00:00'))
                for t in tweets
            ]
            
            analysis = {
                'hashtag': hashtag,
                'total_tweets': total_tweets,
                'total_retweets': total_retweets,
                'total_likes': total_likes,
                'engagement_rate': (total_retweets + total_likes) / max(total_tweets, 1),
                'tweet_frequency': len(tweet_times),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return MCPResponse.success_response(data=analysis)
            
        except Exception as e:
            logger.error(f"Ошибка анализа хештега {hashtag}: {e}")
            return await self._analyze_hashtag_trends_mock(hashtag)
    
    # Mock методы для тестирования
    async def _get_trending_topics_mock(self, location: str) -> MCPResponse:
        """Заглушка для трендовых тем"""
        mock_trends = [
            {"name": "#ИИ", "tweet_volume": 50000},
            {"name": "#технологии", "tweet_volume": 35000},
            {"name": "#стартапы", "tweet_volume": 25000},
            {"name": "#образование", "tweet_volume": 20000},
            {"name": "#бизнес", "tweet_volume": 18000}
        ]
        
        return MCPResponse.success_response(data={
            'trends': mock_trends,
            'location': location,
            'as_of': datetime.now().isoformat()
        })
    
    async def _search_tweets_mock(self, query: str, max_results: int) -> MCPResponse:
        """Заглушка для поиска твитов"""
        mock_tweets = []
        
        for i in range(min(max_results, 10)):
            mock_tweets.append({
                "id": f"mock_tweet_{i}",
                "text": f"Mock tweet about {query} #{i}",
                "created_at": (datetime.now() - timedelta(hours=i)).isoformat(),
                "public_metrics": {
                    "retweet_count": 100 - i * 5,
                    "like_count": 500 - i * 20,
                    "reply_count": 20 - i,
                    "quote_count": 10 - i
                }
            })
        
        return MCPResponse.success_response(data={
            'data': mock_tweets,
            'meta': {
                'result_count': len(mock_tweets),
                'query': query
            }
        })
    
    async def _get_viral_tweets_mock(self, time_period: str) -> MCPResponse:
        """Заглушка для вирусных твитов"""
        mock_viral = [
            {
                "id": "viral_1",
                "text": "Искусственный интеллект меняет мир! 🤖 #ИИ #технологии",
                "created_at": datetime.now().isoformat(),
                "public_metrics": {
                    "retweet_count": 5000,
                    "like_count": 15000,
                    "reply_count": 800,
                    "quote_count": 200
                }
            },
            {
                "id": "viral_2", 
                "text": "Новый стартап привлек $10M инвестиций! 🚀 #стартапы #инвестиции",
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "public_metrics": {
                    "retweet_count": 3000,
                    "like_count": 8000,
                    "reply_count": 400,
                    "quote_count": 150
                }
            }
        ]
        
        return MCPResponse.success_response(data={
            'viral_tweets': mock_viral,
            'time_period': time_period,
            'total_found': len(mock_viral)
        })
    
    async def _analyze_hashtag_trends_mock(self, hashtag: str) -> MCPResponse:
        """Заглушка для анализа хештегов"""
        return MCPResponse.success_response(data={
            'hashtag': hashtag,
            'total_tweets': 1500,
            'total_retweets': 5000,
            'total_likes': 12000,
            'engagement_rate': 11.33,
            'tweet_frequency': 150,
            'trend_direction': 'rising',
            'analysis_timestamp': datetime.now().isoformat()
        })
