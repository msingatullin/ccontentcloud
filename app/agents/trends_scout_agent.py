"""
TrendsScoutAgent - MVP версия агента анализа трендов
Специализируется на мониторинге трендов в реальном времени
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ..orchestrator.agent_manager import BaseAgent, AgentCapability
from ..orchestrator.workflow_engine import Task, TaskType, TaskPriority
from ..mcp.integrations.news import NewsMCP
from ..mcp.integrations.twitter import TwitterMCP
from ..mcp.integrations.google_trends import GoogleTrendsMCP
from ..mcp.config import get_mcp_config, is_mcp_enabled
from .trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class TrendType(Enum):
    """Типы трендов"""
    VIRAL = "viral"              # Вирусный контент
    NEWS = "news"                # Новостные события
    SOCIAL = "social"            # Социальные тренды
    SEARCH = "search"            # Поисковые тренды
    HASHTAG = "hashtag"          # Хештеги


class TrendStatus(Enum):
    """Статусы трендов"""
    RISING = "rising"            # Растущий тренд
    PEAK = "peak"                # Пик популярности
    DECLINING = "declining"      # Снижающийся тренд
    STABLE = "stable"            # Стабильный тренд


@dataclass
class TrendData:
    """Данные о тренде"""
    trend_id: str
    title: str
    description: str
    trend_type: TrendType
    status: TrendStatus
    popularity_score: float      # 0-100
    engagement_rate: float       # 0-100
    growth_rate: float          # % изменения за период
    source: str                 # Источник тренда
    keywords: List[str]
    hashtags: List[str]
    target_audience: List[str]  # Целевые аудитории
    content_ideas: List[str]    # Идеи для контента
    discovered_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class TrendAnalysisReport:
    """Отчет анализа трендов"""
    report_id: str
    analysis_period: str
    total_trends: int
    trending_topics: List[TrendData]
    viral_content: List[TrendData]
    content_recommendations: List[str]
    audience_insights: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)


class TrendsScoutAgent(BaseAgent):
    """MVP агент для анализа трендов в реальном времени"""
    
    def __init__(self, agent_id: str = "trends_scout_agent"):
        capability = AgentCapability(
            task_types=[TaskType.REAL_TIME],  # Специализация на real-time
            max_concurrent_tasks=3,           # Быстрая обработка
            specializations=["trend_analysis", "viral_content", "social_monitoring"],
            performance_score=1.2            # Высокая скорость для real-time
        )
        super().__init__(agent_id, "Trends Scout Agent (MVP)", capability)
        
        # MCP интеграции
        self.news_mcp = None
        self.twitter_mcp = None
        self.google_trends_mcp = None
        
        # Кэш трендов (в памяти для MVP)
        self.trends_cache = {}
        self.cache_ttl = timedelta(minutes=15)  # Кэш на 15 минут
        
        # Настройки анализа
        self.trend_keywords = self._load_trend_keywords()
        self.audience_profiles = self._load_audience_profiles()
        self.content_templates = self._load_content_templates()
        
        # Метрики трендов
        self.trend_thresholds = {
            'viral_min_score': 70.0,
            'trending_min_score': 50.0,
            'growth_min_rate': 20.0
        }
        
        # Система анализа трендов
        self.trend_analyzer = TrendAnalyzer()
        
        self._initialize_mcp_integrations()
        logger.info(f"TrendsScoutAgent MVP {agent_id} инициализирован")
    
    def _load_trend_keywords(self) -> Dict[str, List[str]]:
        """Загружает ключевые слова для анализа трендов"""
        return {
            'viral_keywords': [
                'вирусный', 'тренд', 'хайп', 'бум', 'взрыв', 'сенсация',
                'viral', 'trending', 'boom', 'sensation', 'breaking'
            ],
            'social_keywords': [
                'социальные сети', 'instagram', 'tiktok', 'youtube', 'telegram',
                'social media', 'influencer', 'блогер', 'подписчик'
            ],
            'news_keywords': [
                'новости', 'события', 'происшествия', 'политика', 'экономика',
                'news', 'breaking news', 'events', 'politics'
            ]
        }
    
    def _load_audience_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Загружает профили целевых аудиторий"""
        return {
            'tech_audience': {
                'interests': ['технологии', 'IT', 'программирование', 'стартапы'],
                'platforms': ['telegram', 'youtube', 'habr'],
                'age_range': '18-35'
            },
            'business_audience': {
                'interests': ['бизнес', 'маркетинг', 'финансы', 'предпринимательство'],
                'platforms': ['linkedin', 'telegram', 'youtube'],
                'age_range': '25-45'
            },
            'general_audience': {
                'interests': ['развлечения', 'новости', 'образование'],
                'platforms': ['instagram', 'tiktok', 'youtube', 'telegram'],
                'age_range': '16-50'
            }
        }
    
    def _load_content_templates(self) -> Dict[str, str]:
        """Загружает шаблоны для генерации контент-идей"""
        return {
            'viral_template': "Создать контент на тему '{trend}' с акцентом на вирусность",
            'news_template': "Осветить тренд '{trend}' в контексте новостей",
            'educational_template': "Объяснить тренд '{trend}' простым языком",
            'analytical_template': "Проанализировать влияние тренда '{trend}' на индустрию"
        }
    
    def _initialize_mcp_integrations(self):
        """Инициализирует MCP интеграции"""
        try:
            # News MCP
            if is_mcp_enabled('news'):
                self.news_mcp = NewsMCP()
                logger.info("News MCP интеграция инициализирована")
            else:
                logger.warning("News MCP отключен - работа в режиме заглушек")
            
            # Twitter MCP
            if is_mcp_enabled('twitter'):
                self.twitter_mcp = TwitterMCP()
                logger.info("Twitter MCP интеграция инициализирована")
            else:
                logger.warning("Twitter MCP отключен - работа в режиме заглушек")
            
            # Google Trends MCP
            if is_mcp_enabled('google_trends'):
                self.google_trends_mcp = GoogleTrendsMCP()
                logger.info("Google Trends MCP интеграция инициализирована")
            else:
                logger.warning("Google Trends MCP отключен - работа в режиме заглушек")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации MCP: {e}")
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу анализа трендов"""
        try:
            logger.info(f"TrendsScoutAgent выполняет задачу: {task.id}")
            
            # Анализируем параметры задачи
            analysis_type = task.context.get('analysis_type', 'general')
            time_period = task.context.get('time_period', '1h')
            target_audience = task.context.get('target_audience', 'general_audience')
            
            # Выполняем анализ трендов
            if analysis_type == 'viral_content':
                result = await self._analyze_viral_content(time_period, target_audience)
            elif analysis_type == 'news_trends':
                result = await self._analyze_news_trends(time_period, target_audience)
            elif analysis_type == 'social_trends':
                result = await self._analyze_social_trends(time_period, target_audience)
            else:
                result = await self._analyze_general_trends(time_period, target_audience)
            
            # Отмечаем задачу как выполненную
            self.complete_task(task.id)
            
            return {
                'status': 'success',
                'task_id': task.id,
                'agent_id': self.agent_id,
                'result': result,
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка выполнения задачи {task.id}: {e}")
            self.increment_error_count()
            return {
                'status': 'error',
                'task_id': task.id,
                'agent_id': self.agent_id,
                'error': str(e),
                'execution_time': datetime.now().isoformat()
            }
    
    async def _analyze_general_trends(self, time_period: str, target_audience: str) -> TrendAnalysisReport:
        """Анализ общих трендов"""
        logger.info(f"Анализ общих трендов за период: {time_period}")
        
        # Получаем данные из различных источников
        trends_data = []
        
        # Анализ новостных трендов
        if self.news_mcp:
            news_trends = await self._get_news_trends(time_period)
            trends_data.extend(news_trends)
        
        # Анализ социальных трендов
        if self.twitter_mcp:
            twitter_trends = await self._get_twitter_trends(time_period)
            trends_data.extend(twitter_trends)
        else:
            social_trends = await self._get_social_trends_mock(time_period)
            trends_data.extend(social_trends)
        
        # Анализ поисковых трендов
        if self.google_trends_mcp:
            search_trends = await self._get_search_trends(time_period)
            trends_data.extend(search_trends)
        
        # Фильтруем тренды по целевой аудитории
        filtered_trends = self._filter_trends_by_audience(trends_data, target_audience)
        
        # Анализируем тренды с помощью TrendAnalyzer
        analyzed_trends = []
        for trend in filtered_trends:
            trend_dict = self._trend_data_to_dict(trend)
            analysis = self.trend_analyzer.analyze_trend(trend_dict, target_audience)
            analyzed_trends.append(analysis)
        
        # Сортируем по общему баллу
        analyzed_trends.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Генерируем контент-рекомендации на основе анализа
        content_recommendations = self._generate_enhanced_recommendations(analyzed_trends)
        
        # Создаем отчет
        report = TrendAnalysisReport(
            report_id=f"trends_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis_period=time_period,
            total_trends=len(filtered_trends),
            trending_topics=filtered_trends,
            viral_content=[t for t in filtered_trends if t.popularity_score >= 70],
            content_recommendations=content_recommendations,
            audience_insights=self._analyze_audience_insights(filtered_trends, target_audience)
        )
        
        return report
    
    async def _analyze_viral_content(self, time_period: str, target_audience: str) -> TrendAnalysisReport:
        """Анализ вирусного контента"""
        logger.info(f"Анализ вирусного контента за период: {time_period}")
        
        # Получаем все тренды
        general_report = await self._analyze_general_trends(time_period, target_audience)
        
        # Фильтруем только вирусный контент
        viral_trends = [
            trend for trend in general_report.trending_topics 
            if trend.popularity_score >= self.trend_thresholds['viral_min_score']
        ]
        
        # Обновляем отчет
        general_report.trending_topics = viral_trends
        general_report.viral_content = viral_trends
        general_report.total_trends = len(viral_trends)
        
        return general_report
    
    async def _analyze_news_trends(self, time_period: str, target_audience: str) -> TrendAnalysisReport:
        """Анализ новостных трендов"""
        logger.info(f"Анализ новостных трендов за период: {time_period}")
        
        trends_data = []
        
        if self.news_mcp:
            news_trends = await self._get_news_trends(time_period)
            trends_data.extend(news_trends)
        
        # Фильтруем по аудитории
        filtered_trends = self._filter_trends_by_audience(trends_data, target_audience)
        
        # Генерируем рекомендации
        content_recommendations = self._generate_content_recommendations(filtered_trends)
        
        return TrendAnalysisReport(
            report_id=f"news_trends_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis_period=time_period,
            total_trends=len(filtered_trends),
            trending_topics=filtered_trends,
            viral_content=[],
            content_recommendations=content_recommendations,
            audience_insights=self._analyze_audience_insights(filtered_trends, target_audience)
        )
    
    async def _analyze_social_trends(self, time_period: str, target_audience: str) -> TrendAnalysisReport:
        """Анализ социальных трендов"""
        logger.info(f"Анализ социальных трендов за период: {time_period}")
        
        # Получаем социальные тренды (заглушка для MVP)
        social_trends = await self._get_social_trends_mock(time_period)
        
        # Фильтруем по аудитории
        filtered_trends = self._filter_trends_by_audience(social_trends, target_audience)
        
        # Генерируем рекомендации
        content_recommendations = self._generate_content_recommendations(filtered_trends)
        
        return TrendAnalysisReport(
            report_id=f"social_trends_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis_period=time_period,
            total_trends=len(filtered_trends),
            trending_topics=filtered_trends,
            viral_content=[t for t in filtered_trends if t.popularity_score >= 70],
            content_recommendations=content_recommendations,
            audience_insights=self._analyze_audience_insights(filtered_trends, target_audience)
        )
    
    async def _get_news_trends(self, time_period: str) -> List[TrendData]:
        """Получает новостные тренды через News MCP"""
        trends = []
        
        try:
            if not self.news_mcp:
                logger.warning("News MCP недоступен - используем заглушки")
                return await self._get_news_trends_mock(time_period)
            
            # Получаем топ новости
            response = await self.news_mcp.get_news("trending", "ru")
            
            if response.success and response.data:
                articles = response.data.get('articles', [])
                
                for i, article in enumerate(articles[:10]):  # Топ 10
                    trend = TrendData(
                        trend_id=f"news_trend_{i}",
                        title=article.get('title', ''),
                        description=article.get('description', ''),
                        trend_type=TrendType.NEWS,
                        status=TrendStatus.RISING,
                        popularity_score=min(90 - i * 5, 100),  # Убывающая популярность
                        engagement_rate=min(85 - i * 3, 100),
                        growth_rate=20.0 + i * 2,
                        source=article.get('source', {}).get('name', 'News'),
                        keywords=self._extract_keywords(article.get('title', '')),
                        hashtags=self._extract_hashtags(article.get('title', '')),
                        target_audience=['general_audience'],
                        content_ideas=self._generate_trend_content_ideas(article.get('title', ''))
                    )
                    trends.append(trend)
            
        except Exception as e:
            logger.error(f"Ошибка получения новостных трендов: {e}")
            # Возвращаем заглушки при ошибке
            trends = await self._get_news_trends_mock(time_period)
        
        return trends
    
    async def _get_twitter_trends(self, time_period: str) -> List[TrendData]:
        """Получает тренды из Twitter"""
        trends = []
        
        try:
            if not self.twitter_mcp:
                logger.warning("Twitter MCP недоступен - используем заглушки")
                return await self._get_social_trends_mock(time_period)
            
            # Получаем трендовые темы
            trending_response = await self.twitter_mcp.get_trending_topics()
            
            if trending_response.success and trending_response.data:
                trending_data = trending_response.data.get('trends', [])
                
                for i, trend_item in enumerate(trending_data[:5]):  # Топ 5
                    trend = TrendData(
                        trend_id=f"twitter_trend_{i}",
                        title=trend_item.get('name', ''),
                        description=f"Трендовая тема в Twitter: {trend_item.get('name', '')}",
                        trend_type=TrendType.SOCIAL,
                        status=TrendStatus.RISING,
                        popularity_score=min(95 - i * 10, 100),
                        engagement_rate=min(90 - i * 5, 100),
                        growth_rate=30.0 + i * 5,
                        source="Twitter",
                        keywords=self._extract_keywords(trend_item.get('name', '')),
                        hashtags=[trend_item.get('name', '')],
                        target_audience=['general_audience'],
                        content_ideas=self._generate_trend_content_ideas(trend_item.get('name', ''))
                    )
                    trends.append(trend)
            
            # Получаем вирусные твиты
            viral_response = await self.twitter_mcp.get_viral_tweets(time_period)
            
            if viral_response.success and viral_response.data:
                viral_tweets = viral_response.data.get('viral_tweets', [])
                
                for i, tweet in enumerate(viral_tweets[:3]):  # Топ 3 вирусных
                    trend = TrendData(
                        trend_id=f"viral_tweet_{i}",
                        title=tweet.get('text', '')[:100] + "...",
                        description=f"Вирусный твит: {tweet.get('text', '')[:200]}",
                        trend_type=TrendType.VIRAL,
                        status=TrendStatus.PEAK,
                        popularity_score=95.0,
                        engagement_rate=98.0,
                        growth_rate=50.0,
                        source="Twitter Viral",
                        keywords=self._extract_keywords(tweet.get('text', '')),
                        hashtags=self._extract_hashtags(tweet.get('text', '')),
                        target_audience=['general_audience'],
                        content_ideas=[
                            f"Создать контент на тему вирусного твита: {tweet.get('text', '')[:50]}",
                            "Проанализировать почему этот твит стал вирусным"
                        ]
                    )
                    trends.append(trend)
            
        except Exception as e:
            logger.error(f"Ошибка получения трендов Twitter: {e}")
            trends = await self._get_social_trends_mock(time_period)
        
        return trends
    
    async def _get_search_trends(self, time_period: str) -> List[TrendData]:
        """Получает поисковые тренды из Google Trends"""
        trends = []
        
        try:
            if not self.google_trends_mcp:
                logger.warning("Google Trends MCP недоступен - используем заглушки")
                return []
            
            # Получаем трендовые поиски
            trending_response = await self.google_trends_mcp.get_trending_searches(time_period)
            
            if trending_response.success and trending_response.data:
                trending_data = trending_response.data.get('default', {}).get('trendingSearchesDays', [])
                
                for day_data in trending_data:
                    for i, search_item in enumerate(day_data.get('trendingSearches', [])[:5]):
                        trend = TrendData(
                            trend_id=f"search_trend_{i}",
                            title=search_item.get('title', {}).get('query', ''),
                            description=f"Трендовый поиск: {search_item.get('title', {}).get('query', '')}",
                            trend_type=TrendType.SEARCH,
                            status=TrendStatus.RISING,
                            popularity_score=min(85 - i * 8, 100),
                            engagement_rate=min(75 - i * 5, 100),
                            growth_rate=20.0 + i * 3,
                            source="Google Trends",
                            keywords=[search_item.get('title', {}).get('query', '')],
                            hashtags=[],
                            target_audience=['general_audience'],
                            content_ideas=self._generate_trend_content_ideas(search_item.get('title', {}).get('query', ''))
                        )
                        trends.append(trend)
            
            # Получаем растущие поиски
            rising_response = await self.google_trends_mcp.get_rising_searches(time_period)
            
            if rising_response.success and rising_response.data:
                rising_searches = rising_response.data.get('rising_searches', [])
                
                for i, search_item in enumerate(rising_searches[:3]):
                    trend = TrendData(
                        trend_id=f"rising_search_{i}",
                        title=search_item.get('title', {}).get('query', ''),
                        description=f"Растущий поиск: {search_item.get('title', {}).get('query', '')}",
                        trend_type=TrendType.SEARCH,
                        status=TrendStatus.RISING,
                        popularity_score=90.0,
                        engagement_rate=85.0,
                        growth_rate=40.0,
                        source="Google Trends Rising",
                        keywords=[search_item.get('title', {}).get('query', '')],
                        hashtags=[],
                        target_audience=['general_audience'],
                        content_ideas=[
                            f"Создать контент на растущую тему: {search_item.get('title', {}).get('query', '')}",
                            "Объяснить почему эта тема набирает популярность"
                        ]
                    )
                    trends.append(trend)
            
        except Exception as e:
            logger.error(f"Ошибка получения поисковых трендов: {e}")
        
        return trends
    
    async def _get_news_trends_mock(self, time_period: str) -> List[TrendData]:
        """Заглушка для новостных трендов"""
        return [
            TrendData(
                trend_id="mock_news_1",
                title="Искусственный интеллект в образовании",
                description="Новые технологии ИИ меняют подход к обучению",
                trend_type=TrendType.NEWS,
                status=TrendStatus.RISING,
                popularity_score=85.0,
                engagement_rate=78.0,
                growth_rate=25.0,
                source="TechNews",
                keywords=["ИИ", "образование", "технологии"],
                hashtags=["#ИИ", "#образование", "#технологии"],
                target_audience=["tech_audience", "general_audience"],
                content_ideas=[
                    "Объяснить как ИИ помогает в обучении",
                    "Показать примеры использования ИИ в школах"
                ]
            ),
            TrendData(
                trend_id="mock_news_2",
                title="Устойчивое развитие в бизнесе",
                description="Компании переходят на экологичные практики",
                trend_type=TrendType.NEWS,
                status=TrendStatus.PEAK,
                popularity_score=72.0,
                engagement_rate=65.0,
                growth_rate=18.0,
                source="BusinessNews",
                keywords=["устойчивое развитие", "экология", "бизнес"],
                hashtags=["#экология", "#бизнес", "#устойчивость"],
                target_audience=["business_audience"],
                content_ideas=[
                    "Кейсы успешных экологических инициатив",
                    "Как внедрить устойчивые практики в компании"
                ]
            )
        ]
    
    async def _get_social_trends_mock(self, time_period: str) -> List[TrendData]:
        """Заглушка для социальных трендов"""
        return [
            TrendData(
                trend_id="mock_social_1",
                title="Короткие видео в образовании",
                description="TikTok и Reels меняют способ подачи знаний",
                trend_type=TrendType.SOCIAL,
                status=TrendStatus.RISING,
                popularity_score=88.0,
                engagement_rate=92.0,
                growth_rate=35.0,
                source="SocialMedia",
                keywords=["короткие видео", "образование", "TikTok"],
                hashtags=["#короткиевидео", "#образование", "#TikTok"],
                target_audience=["general_audience", "tech_audience"],
                content_ideas=[
                    "Создать серию образовательных коротких видео",
                    "Показать как делать эффективный образовательный контент"
                ]
            ),
            TrendData(
                trend_id="mock_social_2",
                title="Подкасты в бизнесе",
                description="Растущая популярность бизнес-подкастов",
                trend_type=TrendType.SOCIAL,
                status=TrendStatus.STABLE,
                popularity_score=65.0,
                engagement_rate=58.0,
                growth_rate=12.0,
                source="PodcastPlatform",
                keywords=["подкасты", "бизнес", "аудио"],
                hashtags=["#подкасты", "#бизнес", "#аудио"],
                target_audience=["business_audience"],
                content_ideas=[
                    "Запустить бизнес-подкаст",
                    "Пригласить экспертов для интервью"
                ]
            )
        ]
    
    def _filter_trends_by_audience(self, trends: List[TrendData], target_audience: str) -> List[TrendData]:
        """Фильтрует тренды по целевой аудитории"""
        if target_audience not in self.audience_profiles:
            return trends
        
        audience_profile = self.audience_profiles[target_audience]
        filtered_trends = []
        
        for trend in trends:
            # Проверяем соответствие интересам аудитории
            if any(keyword in trend.keywords for keyword in audience_profile['interests']):
                trend.target_audience = [target_audience]
                filtered_trends.append(trend)
        
        return filtered_trends
    
    def _generate_content_recommendations(self, trends: List[TrendData]) -> List[str]:
        """Генерирует рекомендации по контенту на основе трендов"""
        recommendations = []
        
        for trend in trends:
            if trend.trend_type == TrendType.VIRAL:
                template = self.content_templates['viral_template']
            elif trend.trend_type == TrendType.NEWS:
                template = self.content_templates['news_template']
            else:
                template = self.content_templates['educational_template']
            
            recommendation = template.format(trend=trend.title)
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_trend_content_ideas(self, trend_title: str) -> List[str]:
        """Генерирует идеи контента для тренда"""
        return [
            f"Подробный разбор тренда: {trend_title}",
            f"Как использовать тренд '{trend_title}' в контенте",
            f"Экспертное мнение о тренде: {trend_title}"
        ]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлекает ключевые слова из текста"""
        # Простая реализация для MVP
        keywords = []
        text_lower = text.lower()
        
        for category, words in self.trend_keywords.items():
            for word in words:
                if word.lower() in text_lower:
                    keywords.append(word)
        
        return list(set(keywords))  # Убираем дубликаты
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Извлекает хештеги из текста"""
        import re
        hashtags = re.findall(r'#\w+', text)
        return hashtags
    
    def _analyze_audience_insights(self, trends: List[TrendData], target_audience: str) -> Dict[str, Any]:
        """Анализирует инсайты для целевой аудитории"""
        if not trends:
            return {}
        
        # Подсчитываем статистику
        total_trends = len(trends)
        viral_trends = len([t for t in trends if t.popularity_score >= 70])
        avg_engagement = sum(t.engagement_rate for t in trends) / total_trends
        avg_growth = sum(t.growth_rate for t in trends) / total_trends
        
        # Топ ключевые слова
        all_keywords = []
        for trend in trends:
            all_keywords.extend(trend.keywords)
        
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_trends': total_trends,
            'viral_trends_count': viral_trends,
            'viral_percentage': (viral_trends / total_trends) * 100,
            'average_engagement': round(avg_engagement, 2),
            'average_growth_rate': round(avg_growth, 2),
            'top_keywords': [kw[0] for kw in top_keywords],
            'target_audience': target_audience,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _trend_data_to_dict(self, trend: TrendData) -> Dict[str, Any]:
        """Конвертирует TrendData в словарь для анализа"""
        return {
            'trend_id': trend.trend_id,
            'title': trend.title,
            'description': trend.description,
            'trend_type': trend.trend_type.value,
            'status': trend.status.value,
            'popularity_score': trend.popularity_score,
            'engagement_rate': trend.engagement_rate,
            'growth_rate': trend.growth_rate,
            'source': trend.source,
            'keywords': trend.keywords,
            'hashtags': trend.hashtags,
            'target_audience': trend.target_audience,
            'content_ideas': trend.content_ideas,
            'discovered_at': trend.discovered_at.isoformat(),
            'last_updated': trend.last_updated.isoformat()
        }
    
    def _generate_enhanced_recommendations(self, analyzed_trends: List) -> List[str]:
        """Генерирует улучшенные рекомендации на основе анализа трендов"""
        recommendations = []
        
        # Рекомендации от топ трендов
        for i, analysis in enumerate(analyzed_trends[:3]):  # Топ 3
            if analysis.overall_score > 70:
                recommendations.extend(analysis.recommendations[:2])  # Топ 2 рекомендации
        
        # Общие рекомендации
        viral_trends = [a for a in analyzed_trends if a.trend_level.value == 'viral']
        if viral_trends:
            recommendations.append("Обнаружены вирусные тренды - приоритет на создание контента")
        
        high_trends = [a for a in analyzed_trends if a.trend_level.value == 'high']
        if high_trends:
            recommendations.append("Множество высокоприоритетных трендов - планировать серию контента")
        
        # Рекомендации по времени
        short_lived_trends = [a for a in analyzed_trends if a.metrics.trend_lifetime < 24]
        if short_lived_trends:
            recommendations.append("Есть краткосрочные тренды - действовать быстро")
        
        return list(set(recommendations))  # Убираем дубликаты
