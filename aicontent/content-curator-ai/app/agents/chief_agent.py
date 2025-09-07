"""
ChiefContentAgent - Стратег-редактор
Превращает бизнес-цели в контент-план и стратегию
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..orchestrator.agent_manager import BaseAgent, AgentCapability
from ..orchestrator.workflow_engine import Task, TaskType, TaskPriority
from ..models.content import ContentBrief, ContentCalendar, Platform, ContentType
from ..mcp.integrations.news import NewsMCP
from ..mcp.config import get_mcp_config, is_mcp_enabled

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class NewsTrend:
    """Тренд новостей"""
    topic: str
    relevance_score: float
    source_count: int
    recent_articles: List[Dict[str, Any]]
    trend_direction: str  # "rising", "stable", "declining"
    keywords: List[str]


@dataclass
class ContentStrategy:
    """Стратегия контента"""
    target_audience: str
    key_messages: List[str]
    content_themes: List[str]
    posting_schedule: Dict[str, Any]
    platform_strategy: Dict[str, Dict[str, Any]]
    success_metrics: List[str]
    news_trends: List[NewsTrend] = None


@dataclass
class ContentPlan:
    """План контента"""
    strategy: ContentStrategy
    content_calendar: ContentCalendar
    content_briefs: List[ContentBrief]
    estimated_reach: int
    budget_estimate: Optional[float]


class ChiefContentAgent(BaseAgent):
    """Агент-стратег для создания контент-планов"""
    
    def __init__(self, agent_id: str = "chief_content_agent"):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED, TaskType.COMPLEX],
            max_concurrent_tasks=3,
            specializations=["strategy", "planning", "content_analysis"],
            performance_score=1.2
        )
        super().__init__(agent_id, "Chief Content Agent", capability)
        
        # База знаний стратегий
        self.content_strategies = self._load_content_strategies()
        self.platform_insights = self._load_platform_insights()
        
        # News API интеграции
        self.news_mcp = None
        self.news_cache = {}
        self.trend_cache = {}
        self._initialize_news_integrations()
        
        logger.info(f"ChiefContentAgent {agent_id} инициализирован")
    
    def _load_content_strategies(self) -> Dict[str, Any]:
        """Загружает базовые стратегии контента"""
        return {
            "awareness": {
                "goal": "Повышение узнаваемости бренда",
                "content_types": ["educational", "entertainment", "trending"],
                "posting_frequency": "daily",
                "engagement_focus": "shares_and_comments"
            },
            "engagement": {
                "goal": "Увеличение вовлеченности аудитории",
                "content_types": ["interactive", "polls", "user_generated"],
                "posting_frequency": "2-3_per_day",
                "engagement_focus": "comments_and_reactions"
            },
            "conversion": {
                "goal": "Конверсия в клиентов",
                "content_types": ["product_showcase", "testimonials", "offers"],
                "posting_frequency": "3-4_per_week",
                "engagement_focus": "clicks_and_conversions"
            },
            "retention": {
                "goal": "Удержание существующих клиентов",
                "content_types": ["tips", "behind_scenes", "community"],
                "posting_frequency": "daily",
                "engagement_focus": "loyalty_and_retention"
            }
        }
    
    def _load_platform_insights(self) -> Dict[str, Dict[str, Any]]:
        """Загружает инсайты по платформам"""
        return {
            "telegram": {
                "best_times": ["09:00-11:00", "18:00-21:00"],
                "optimal_length": "200-500 символов",
                "content_preferences": ["news", "tips", "announcements"],
                "engagement_rate": 0.15
            },
            "vk": {
                "best_times": ["12:00-14:00", "19:00-22:00"],
                "optimal_length": "100-300 символов",
                "content_preferences": ["entertainment", "memes", "discussions"],
                "engagement_rate": 0.08
            },
            "instagram": {
                "best_times": ["11:00-13:00", "17:00-19:00"],
                "optimal_length": "125-150 символов",
                "content_preferences": ["visual", "stories", "reels"],
                "engagement_rate": 0.12
            },
            "twitter": {
                "best_times": ["09:00-10:00", "15:00-16:00"],
                "optimal_length": "50-100 символов",
                "content_preferences": ["news", "opinions", "trends"],
                "engagement_rate": 0.06
            }
        }
    
    def _initialize_news_integrations(self):
        """Инициализирует News API интеграции"""
        try:
            # Инициализируем NewsMCP если доступен
            if is_mcp_enabled('news'):
                self.news_mcp = NewsMCP()
                logger.info("NewsMCP инициализирован в ChiefContentAgent")
            else:
                logger.warning("NewsMCP недоступен - будет использоваться fallback")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации News интеграций: {e}")
            self.news_mcp = None
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу создания контент-стратегии"""
        try:
            logger.info(f"ChiefContentAgent выполняет задачу: {task.name}")
            
            # Извлекаем данные из контекста задачи
            brief_data = task.context.get("brief_data", {})
            business_goals = task.context.get("business_goals", [])
            target_audience = task.context.get("target_audience", "")
            platforms = task.context.get("platforms", ["telegram", "vk"])
            
            # Создаем контент-стратегию
            strategy = await self._create_content_strategy(
                business_goals, target_audience, platforms
            )
            
            # Создаем контент-план
            content_plan = await self._create_content_plan(
                strategy, brief_data, platforms
            )
            
            # Генерируем календарь контента
            calendar = await self._generate_content_calendar(
                content_plan, platforms
            )
            
            result = {
                "task_id": task.id,
                "agent_id": self.agent_id,
                "strategy": {
                    "target_audience": strategy.target_audience,
                    "key_messages": strategy.key_messages,
                    "content_themes": strategy.content_themes,
                    "platform_strategy": strategy.platform_strategy
                },
                "content_plan": {
                    "calendar_id": calendar.id,
                    "estimated_reach": content_plan.estimated_reach,
                    "content_briefs_count": len(content_plan.content_briefs)
                },
                "recommendations": await self._generate_recommendations(
                    strategy, platforms
                ),
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"ChiefContentAgent завершил задачу {task.id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в ChiefContentAgent: {e}")
            raise
    
    async def _create_content_strategy(self, business_goals: List[str], 
                                     target_audience: str, 
                                     platforms: List[str]) -> ContentStrategy:
        """Создает стратегию контента на основе бизнес-целей"""
        
        # Определяем основную цель
        primary_goal = self._identify_primary_goal(business_goals)
        strategy_template = self.content_strategies.get(primary_goal, 
                                                      self.content_strategies["awareness"])
        
        # Создаем ключевые сообщения
        key_messages = await self._generate_key_messages(business_goals, target_audience)
        
        # Определяем темы контента
        content_themes = await self._generate_content_themes(business_goals, target_audience)
        
        # Создаем стратегию для каждой платформы
        platform_strategy = {}
        for platform in platforms:
            platform_strategy[platform] = await self._create_platform_strategy(
                platform, strategy_template, target_audience
            )
        
        # Определяем расписание публикаций
        posting_schedule = await self._create_posting_schedule(platforms)
        
        # Определяем метрики успеха
        success_metrics = await self._define_success_metrics(primary_goal, platforms)
        
        return ContentStrategy(
            target_audience=target_audience,
            key_messages=key_messages,
            content_themes=content_themes,
            posting_schedule=posting_schedule,
            platform_strategy=platform_strategy,
            success_metrics=success_metrics
        )
    
    def _identify_primary_goal(self, business_goals: List[str]) -> str:
        """Определяет основную бизнес-цель"""
        goal_keywords = {
            "awareness": ["узнаваемость", "осведомленность", "популярность", "известность"],
            "engagement": ["вовлеченность", "активность", "взаимодействие", "участие"],
            "conversion": ["продажи", "конверсия", "клиенты", "заказы", "покупки"],
            "retention": ["удержание", "лояльность", "повторные", "постоянные"]
        }
        
        for goal, keywords in goal_keywords.items():
            for business_goal in business_goals:
                if any(keyword in business_goal.lower() for keyword in keywords):
                    return goal
        
        return "awareness"  # По умолчанию
    
    async def _generate_key_messages(self, business_goals: List[str], 
                                   target_audience: str) -> List[str]:
        """Генерирует ключевые сообщения"""
        messages = []
        
        # Базовые сообщения на основе целей
        for goal in business_goals:
            if "привлечение" in goal.lower():
                messages.append("Мы предлагаем уникальные решения для ваших задач")
            elif "образование" in goal.lower():
                messages.append("Получайте экспертные знания и практические советы")
            elif "доверие" in goal.lower():
                messages.append("Мы - надежный партнер с проверенной репутацией")
            elif "инновации" in goal.lower():
                messages.append("Открываем новые возможности с передовыми технологиями")
        
        # Добавляем сообщения для целевой аудитории
        if "специалист" in target_audience.lower():
            messages.append("Профессиональные решения для экспертов")
        elif "начинающий" in target_audience.lower():
            messages.append("Простые и понятные решения для старта")
        
        return messages[:5]  # Максимум 5 ключевых сообщений
    
    async def _generate_content_themes(self, business_goals: List[str], 
                                     target_audience: str) -> List[str]:
        """Генерирует темы контента через News API или fallback на шаблоны"""
        try:
            # Пытаемся использовать News API для актуальных тем
            news_themes = await self._generate_themes_from_news(business_goals, target_audience)
            if news_themes:
                logger.info(f"Темы контента сгенерированы через News API")
                return news_themes
        except Exception as e:
            logger.warning(f"Ошибка News API генерации тем, используем fallback: {e}")
        
        # Fallback на шаблонную генерацию
        return await self._generate_content_themes_fallback(business_goals, target_audience)
    
    async def _generate_themes_from_news(self, business_goals: List[str], 
                                       target_audience: str) -> Optional[List[str]]:
        """Генерирует темы контента на основе актуальных новостей"""
        try:
            if self.news_mcp is None:
                return None
            
            # Формируем ключевые слова для поиска
            search_keywords = self._extract_search_keywords(business_goals, target_audience)
            
            themes = []
            
            # Ищем новости по каждому ключевому слову
            for keyword in search_keywords[:3]:  # Максимум 3 запроса
                # Проверяем кеш
                cache_key = f"themes_{keyword}_{target_audience}"
                if cache_key in self.news_cache:
                    cached_data = self.news_cache[cache_key]
                    if datetime.now() - cached_data['timestamp'] < timedelta(hours=1):
                        themes.extend(cached_data['themes'])
                        continue
                
                # Ищем новости через News API
                result = await self.news_mcp.execute_with_retry(
                    'get_news',
                    query=keyword,
                    language='ru'
                )
                
                if result.success and result.data:
                    # Анализируем новости и извлекаем темы
                    news_themes = self._extract_themes_from_news(result.data, keyword)
                    themes.extend(news_themes)
                    
                    # Кешируем результат
                    self.news_cache[cache_key] = {
                        'themes': news_themes,
                        'timestamp': datetime.now()
                    }
            
            # Убираем дубли и возвращаем топ тем
            unique_themes = list(set(themes))
            return unique_themes[:8] if unique_themes else None
            
        except Exception as e:
            logger.error(f"Ошибка генерации тем из новостей: {e}")
            return None
    
    def _extract_search_keywords(self, business_goals: List[str], target_audience: str) -> List[str]:
        """Извлекает ключевые слова для поиска новостей"""
        keywords = []
        
        # Ключевые слова из бизнес-целей
        for goal in business_goals:
            if "привлечение" in goal.lower():
                keywords.extend(["маркетинг", "реклама", "продвижение"])
            elif "образование" in goal.lower():
                keywords.extend(["обучение", "образование", "развитие"])
            elif "тренды" in goal.lower():
                keywords.extend(["тренды", "новости", "инновации"])
            elif "технологии" in goal.lower():
                keywords.extend(["технологии", "IT", "цифровизация"])
        
        # Ключевые слова из целевой аудитории
        if "IT" in target_audience.upper():
            keywords.extend(["программирование", "разработка", "автоматизация"])
        elif "бизнес" in target_audience.lower():
            keywords.extend(["управление", "эффективность", "стартапы"])
        elif "образование" in target_audience.lower():
            keywords.extend(["образование", "учеба", "навыки"])
        
        return list(set(keywords))
    
    def _extract_themes_from_news(self, news_data: Dict[str, Any], keyword: str) -> List[str]:
        """Извлекает темы контента из новостных данных"""
        themes = []
        
        try:
            articles = news_data.get('articles', [])
            
            for article in articles[:5]:  # Анализируем топ 5 статей
                title = article.get('title', '')
                description = article.get('description', '')
                
                # Извлекаем ключевые темы из заголовка и описания
                text = f"{title} {description}".lower()
                
                # Определяем темы на основе ключевых слов
                if any(word in text for word in ["новости", "события", "происшествия"]):
                    themes.append("актуальные новости")
                if any(word in text for word in ["тренды", "тенденции", "развитие"]):
                    themes.append("анализ трендов")
                if any(word in text for word in ["технологии", "инновации", "цифровизация"]):
                    themes.append("технологические инновации")
                if any(word in text for word in ["бизнес", "экономика", "рынок"]):
                    themes.append("бизнес-аналитика")
                if any(word in text for word in ["образование", "обучение", "навыки"]):
                    themes.append("образовательный контент")
                if any(word in text for word in ["советы", "рекомендации", "гайды"]):
                    themes.append("практические советы")
        
        except Exception as e:
            logger.error(f"Ошибка извлечения тем из новостей: {e}")
        
        return themes
    
    async def _generate_content_themes_fallback(self, business_goals: List[str], 
                                              target_audience: str) -> List[str]:
        """Fallback метод для генерации тем контента (шаблонная логика)"""
        themes = []
        
        # Темы на основе целей
        for goal in business_goals:
            if "привлечение" in goal.lower():
                themes.extend(["успешные кейсы", "отзывы клиентов", "преимущества"])
            elif "образование" in goal.lower():
                themes.extend(["обучающие материалы", "советы экспертов", "практические гайды"])
            elif "тренды" in goal.lower():
                themes.extend(["новости индустрии", "анализ трендов", "прогнозы"])
        
        # Темы для аудитории
        if "IT" in target_audience.upper():
            themes.extend(["технологии", "разработка", "автоматизация"])
        elif "бизнес" in target_audience.lower():
            themes.extend(["управление", "эффективность", "рост"])
        
        return list(set(themes))[:8]  # Убираем дубли, максимум 8 тем
    
    async def _create_platform_strategy(self, platform: str, 
                                      strategy_template: Dict[str, Any],
                                      target_audience: str) -> Dict[str, Any]:
        """Создает стратегию для конкретной платформы"""
        platform_insights = self.platform_insights.get(platform, {})
        
        return {
            "content_focus": strategy_template["content_types"],
            "posting_frequency": strategy_template["posting_frequency"],
            "optimal_times": platform_insights.get("best_times", ["09:00-18:00"]),
            "content_length": platform_insights.get("optimal_length", "200-300 символов"),
            "engagement_goal": strategy_template["engagement_focus"],
            "expected_engagement_rate": platform_insights.get("engagement_rate", 0.1)
        }
    
    async def _create_posting_schedule(self, platforms: List[str]) -> Dict[str, Any]:
        """Создает расписание публикаций"""
        schedule = {}
        
        for platform in platforms:
            platform_insights = self.platform_insights.get(platform, {})
            best_times = platform_insights.get("best_times", ["09:00-11:00", "18:00-21:00"])
            
            schedule[platform] = {
                "frequency": "daily",
                "best_times": best_times,
                "content_mix": {
                    "educational": 40,
                    "entertainment": 30,
                    "promotional": 20,
                    "user_generated": 10
                }
            }
        
        return schedule
    
    async def _define_success_metrics(self, primary_goal: str, 
                                    platforms: List[str]) -> List[str]:
        """Определяет метрики успеха"""
        metrics = {
            "awareness": ["reach", "impressions", "brand_mentions"],
            "engagement": ["likes", "comments", "shares", "engagement_rate"],
            "conversion": ["clicks", "conversions", "cost_per_acquisition"],
            "retention": ["return_visitors", "subscription_rate", "lifetime_value"]
        }
        
        base_metrics = metrics.get(primary_goal, metrics["awareness"])
        
        # Добавляем платформо-специфичные метрики
        platform_metrics = {
            "telegram": ["subscribers_growth", "message_views"],
            "vk": ["group_members", "post_reach"],
            "instagram": ["followers_growth", "story_views"],
            "twitter": ["followers", "retweets"]
        }
        
        for platform in platforms:
            if platform in platform_metrics:
                base_metrics.extend(platform_metrics[platform])
        
        return list(set(base_metrics))  # Убираем дубли
    
    async def _create_content_plan(self, strategy: ContentStrategy, 
                                 brief_data: Dict[str, Any],
                                 platforms: List[str]) -> ContentPlan:
        """Создает детальный план контента"""
        
        # Создаем брифы для контента
        content_briefs = await self._generate_content_briefs(strategy, brief_data)
        
        # Оцениваем охват
        estimated_reach = await self._estimate_reach(platforms, len(content_briefs))
        
        # Оцениваем бюджет (если нужен)
        budget_estimate = await self._estimate_budget(platforms, len(content_briefs))
        
        # Создаем календарь
        calendar = ContentCalendar(
            name=f"Content Calendar - {strategy.target_audience}",
            description=f"План контента для {', '.join(platforms)}",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        return ContentPlan(
            strategy=strategy,
            content_calendar=calendar,
            content_briefs=content_briefs,
            estimated_reach=estimated_reach,
            budget_estimate=budget_estimate
        )
    
    async def _generate_content_briefs(self, strategy: ContentStrategy, 
                                     brief_data: Dict[str, Any]) -> List[ContentBrief]:
        """Генерирует брифы для контента"""
        briefs = []
        
        # Создаем брифы для каждой темы
        for theme in strategy.content_themes[:5]:  # Максимум 5 брифов
            brief = ContentBrief(
                title=f"Контент: {theme}",
                description=f"Создание контента на тему '{theme}' для {strategy.target_audience}",
                target_audience=strategy.target_audience,
                business_goals=brief_data.get("business_goals", []),
                call_to_action=brief_data.get("call_to_action", ""),
                tone=brief_data.get("tone", "professional"),
                keywords=[theme] + brief_data.get("keywords", []),
                constraints=brief_data.get("constraints", {})
            )
            briefs.append(brief)
        
        return briefs
    
    async def _estimate_reach(self, platforms: List[str], content_count: int) -> int:
        """Оценивает потенциальный охват"""
        base_reach = {
            "telegram": 1000,
            "vk": 2000,
            "instagram": 1500,
            "twitter": 800
        }
        
        total_reach = 0
        for platform in platforms:
            platform_reach = base_reach.get(platform, 1000)
            total_reach += platform_reach * content_count
        
        return total_reach
    
    async def _estimate_budget(self, platforms: List[str], content_count: int) -> Optional[float]:
        """Оценивает бюджет на продвижение"""
        # Для MVP пока не используем платное продвижение
        return None
    
    async def _generate_content_calendar(self, content_plan: ContentPlan, 
                                       platforms: List[str]) -> ContentCalendar:
        """Генерирует календарь контента"""
        calendar = content_plan.content_calendar
        
        # Добавляем ID брифов в календарь
        calendar.content_pieces = [brief.id for brief in content_plan.content_briefs]
        
        return calendar
    
    async def _generate_recommendations(self, strategy: ContentStrategy, 
                                      platforms: List[str]) -> List[str]:
        """Генерирует рекомендации по улучшению"""
        recommendations = []
        
        # Рекомендации по платформам
        for platform in platforms:
            platform_insights = self.platform_insights.get(platform, {})
            engagement_rate = platform_insights.get("engagement_rate", 0.1)
            
            if engagement_rate < 0.1:
                recommendations.append(f"Улучшить контент для {platform} - низкий engagement rate")
        
        # Рекомендации по расписанию
        recommendations.append("Публиковать контент в оптимальное время для каждой платформы")
        
        # Рекомендации по контенту
        recommendations.append("Создавать разнообразный контент: образовательный, развлекательный, промо")
        
        # Рекомендации по метрикам
        recommendations.append(f"Отслеживать метрики: {', '.join(strategy.success_metrics[:3])}")
        
        return recommendations
