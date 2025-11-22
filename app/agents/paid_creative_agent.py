"""
PaidCreativeAgent - Агент для создания рекламных креативов
Создание рекламных текстов, оптимизация под платформы, A/B тестирование
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.orchestrator.agent_manager import BaseAgent, AgentCapability, AgentStatus
from app.orchestrator.workflow_engine import TaskType, Task

# Настройка логирования
logger = logging.getLogger(__name__)


class AdPlatform(Enum):
    """Рекламные платформы"""
    TELEGRAM_ADS = "telegram_ads"
    VK_ADS = "vk_ads"
    GOOGLE_ADS = "google_ads"
    YANDEX_DIRECT = "yandex_direct"
    FACEBOOK_ADS = "facebook_ads"
    INSTAGRAM_ADS = "instagram_ads"
    YOUTUBE_ADS = "youtube_ads"
    TIKTOK_ADS = "tiktok_ads"


class AdFormat(Enum):
    """Форматы рекламы"""
    TEXT_AD = "text_ad"
    IMAGE_AD = "image_ad"
    VIDEO_AD = "video_ad"
    CAROUSEL_AD = "carousel_ad"
    STORY_AD = "story_ad"
    BANNER_AD = "banner_ad"
    NATIVE_AD = "native_ad"
    DISPLAY_AD = "display_ad"


class AdObjective(Enum):
    """Цели рекламы"""
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEADS = "leads"
    SALES = "sales"
    APP_INSTALLS = "app_installs"
    VIDEO_VIEWS = "video_views"
    CONVERSIONS = "conversions"


class ComplianceStatus(Enum):
    """Статус соответствия политикам"""
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


@dataclass
class AdCreative:
    """Рекламный креатив"""
    creative_id: str
    platform: AdPlatform
    format: AdFormat
    objective: AdObjective
    headline: str
    description: str
    call_to_action: str
    target_audience: str
    budget: Optional[float] = None
    bid_strategy: Optional[str] = None
    landing_page: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    compliance_status: ComplianceStatus = ComplianceStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTestVariant:
    """Вариант A/B теста"""
    variant_id: str
    creative: AdCreative
    traffic_percentage: float
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    is_control: bool = False


@dataclass
class ABTest:
    """A/B тест рекламных креативов"""
    test_id: str
    name: str
    variants: List[ABTestVariant]
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "active"
    winner_variant_id: Optional[str] = None
    confidence_level: float = 0.0
    test_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    cost: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    cpm: float = 0.0
    conversion_rate: float = 0.0
    cost_per_conversion: float = 0.0
    roi: float = 0.0
    roas: float = 0.0


@dataclass
class ComplianceReport:
    """Отчет о соответствии политикам"""
    creative_id: str
    platform: AdPlatform
    compliance_status: ComplianceStatus
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)


class PaidCreativeAgent(BaseAgent):
    """Агент для создания рекламных креативов"""
    
    def __init__(self, agent_id: str = "paid_creative_agent"):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED, TaskType.COMPLEX],  # Требует времени на творческий процесс
            max_concurrent_tasks=2,                           # Ограниченная пропускная способность
            specializations=["paid_advertising", "ad_copy", "creative_optimization", "performance_marketing"],
            performance_score=0.9                           # Требует времени на творческий процесс
        )
        super().__init__(agent_id, "Paid Creative Agent", capability)
        
        # Система создания креативов
        self.creative_templates = self._load_creative_templates()
        self.platform_guidelines = self._load_platform_guidelines()
        self.compliance_rules = self._load_compliance_rules()
        
        # A/B тестирование
        self.ab_tests = {}
        self.test_results = {}
        self.performance_tracker = {}
        
        # Кэш креативов
        self.creative_cache = {}
        self.cache_ttl = timedelta(hours=24)  # Кэш на 24 часа
        
        # Статистика производительности
        self.performance_stats = {
            'total_creatives': 0,
            'successful_creatives': 0,
            'failed_creatives': 0,
            'avg_ctr': 0.0,
            'avg_conversion_rate': 0.0,
            'avg_roi': 0.0,
            'total_spend': 0.0,
            'total_revenue': 0.0
        }
        
        # Настройки оптимизации
        self.optimization_settings = {
            'max_headline_length': 30,
            'max_description_length': 90,
            'min_ctr_threshold': 0.02,
            'min_conversion_rate_threshold': 0.01,
            'max_cpc_threshold': 10.0,
            'target_roi': 3.0
        }
        
        logger.info(f"PaidCreativeAgent {agent_id} инициализирован")
    
    def _load_creative_templates(self) -> Dict[str, Dict[str, Any]]:
        """Загружает шаблоны рекламных креативов"""
        return {
            'awareness': {
                'headline_templates': [
                    "Узнайте о {product}",
                    "Откройте для себя {product}",
                    "Новинка: {product}",
                    "Популярный {product}",
                    "Тренд: {product}"
                ],
                'description_templates': [
                    "Познакомьтесь с {product} и его преимуществами",
                    "Узнайте, почему {product} выбирают тысячи",
                    "Откройте новые возможности с {product}",
                    "Популярный выбор среди пользователей"
                ],
                'cta_templates': [
                    "Узнать больше",
                    "Познакомиться",
                    "Изучить",
                    "Открыть"
                ]
            },
            'traffic': {
                'headline_templates': [
                    "Переходите на {product}",
                    "Посетите {product}",
                    "Заходите на {product}",
                    "Изучите {product}",
                    "Проверьте {product}"
                ],
                'description_templates': [
                    "Переходите на наш сайт и узнайте больше",
                    "Посетите страницу и получите подробную информацию",
                    "Заходите и изучайте все возможности",
                    "Проверьте актуальные предложения"
                ],
                'cta_templates': [
                    "Перейти",
                    "Посетить",
                    "Зайти",
                    "Изучить"
                ]
            },
            'engagement': {
                'headline_templates': [
                    "Присоединяйтесь к {product}",
                    "Станьте частью {product}",
                    "Подключайтесь к {product}",
                    "Участвуйте в {product}",
                    "Взаимодействуйте с {product}"
                ],
                'description_templates': [
                    "Присоединяйтесь к нашему сообществу",
                    "Станьте частью активного сообщества",
                    "Подключайтесь и участвуйте в обсуждениях",
                    "Взаимодействуйте с другими пользователями"
                ],
                'cta_templates': [
                    "Присоединиться",
                    "Подписаться",
                    "Участвовать",
                    "Взаимодействовать"
                ]
            },
            'leads': {
                'headline_templates': [
                    "Получите {offer}",
                    "Закажите {offer}",
                    "Запросите {offer}",
                    "Скачайте {offer}",
                    "Зарегистрируйтесь для {offer}"
                ],
                'description_templates': [
                    "Получите бесплатную консультацию",
                    "Закажите обратный звонок",
                    "Запросите персональное предложение",
                    "Скачайте полезные материалы"
                ],
                'cta_templates': [
                    "Получить",
                    "Заказать",
                    "Запросить",
                    "Скачать"
                ]
            },
            'sales': {
                'headline_templates': [
                    "Купите {product}",
                    "Закажите {product}",
                    "Приобретите {product}",
                    "Получите {product}",
                    "Закажите {product} со скидкой"
                ],
                'description_templates': [
                    "Купите сейчас и получите скидку",
                    "Закажите с доставкой на дом",
                    "Приобретите по выгодной цене",
                    "Получите качественный продукт"
                ],
                'cta_templates': [
                    "Купить",
                    "Заказать",
                    "Приобрести",
                    "Получить"
                ]
            }
        }
    
    def _load_platform_guidelines(self) -> Dict[AdPlatform, Dict[str, Any]]:
        """Загружает руководящие принципы платформ"""
        return {
            AdPlatform.TELEGRAM_ADS: {
                'max_headline_length': 30,
                'max_description_length': 90,
                'max_cta_length': 20,
                'allowed_formats': [AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь'],
                'required_elements': ['headline', 'description', 'cta'],
                'targeting_options': ['age', 'gender', 'location', 'interests']
            },
            AdPlatform.VK_ADS: {
                'max_headline_length': 25,
                'max_description_length': 80,
                'max_cta_length': 15,
                'allowed_formats': [AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.CAROUSEL_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь', 'табак'],
                'required_elements': ['headline', 'description', 'cta'],
                'targeting_options': ['age', 'gender', 'location', 'interests', 'education']
            },
            AdPlatform.GOOGLE_ADS: {
                'max_headline_length': 30,
                'max_description_length': 90,
                'max_cta_length': 25,
                'allowed_formats': [AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.DISPLAY_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь', 'табак', 'наркотики'],
                'required_elements': ['headline', 'description', 'cta', 'landing_page'],
                'targeting_options': ['age', 'gender', 'location', 'interests', 'keywords']
            },
            AdPlatform.YANDEX_DIRECT: {
                'max_headline_length': 33,
                'max_description_length': 75,
                'max_cta_length': 20,
                'allowed_formats': [AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь', 'табак'],
                'required_elements': ['headline', 'description', 'cta', 'landing_page'],
                'targeting_options': ['age', 'gender', 'location', 'interests', 'keywords']
            },
            AdPlatform.FACEBOOK_ADS: {
                'max_headline_length': 40,
                'max_description_length': 125,
                'max_cta_length': 20,
                'allowed_formats': [AdFormat.TEXT_AD, AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.CAROUSEL_AD, AdFormat.STORY_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь', 'табак', 'наркотики'],
                'required_elements': ['headline', 'description', 'cta'],
                'targeting_options': ['age', 'gender', 'location', 'interests', 'behavior']
            },
            AdPlatform.INSTAGRAM_ADS: {
                'max_headline_length': 40,
                'max_description_length': 125,
                'max_cta_length': 20,
                'allowed_formats': [AdFormat.IMAGE_AD, AdFormat.VIDEO_AD, AdFormat.CAROUSEL_AD, AdFormat.STORY_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь', 'табак', 'наркотики'],
                'required_elements': ['headline', 'description', 'cta'],
                'targeting_options': ['age', 'gender', 'location', 'interests', 'behavior']
            },
            AdPlatform.YOUTUBE_ADS: {
                'max_headline_length': 30,
                'max_description_length': 90,
                'max_cta_length': 25,
                'allowed_formats': [AdFormat.VIDEO_AD, AdFormat.DISPLAY_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь', 'табак', 'наркотики'],
                'required_elements': ['headline', 'description', 'cta'],
                'targeting_options': ['age', 'gender', 'location', 'interests', 'keywords']
            },
            AdPlatform.TIKTOK_ADS: {
                'max_headline_length': 35,
                'max_description_length': 100,
                'max_cta_length': 20,
                'allowed_formats': [AdFormat.VIDEO_AD, AdFormat.IMAGE_AD, AdFormat.CAROUSEL_AD],
                'prohibited_content': ['криптовалюта', 'азартные игры', 'алкоголь', 'табак', 'наркотики'],
                'required_elements': ['headline', 'description', 'cta'],
                'targeting_options': ['age', 'gender', 'location', 'interests', 'behavior']
            }
        }
    
    def _load_compliance_rules(self) -> Dict[str, List[str]]:
        """Загружает правила соответствия политикам"""
        return {
            'prohibited_keywords': [
                'криптовалюта', 'биткоин', 'эфириум', 'майнинг',
                'азартные игры', 'казино', 'ставки', 'лотерея',
                'алкоголь', 'пиво', 'водка', 'вино',
                'табак', 'сигареты', 'курить',
                'наркотики', 'марихуана', 'кокаин',
                'оружие', 'пистолет', 'автомат',
                'взрывчатка', 'бомба', 'терроризм'
            ],
            'restricted_keywords': [
                'бесплатно', 'скидка', 'акция', 'распродажа',
                'лучший', 'номер один', 'лидер',
                'гарантия', 'обещание', 'результат'
            ],
            'required_disclaimers': [
                'результат может отличаться',
                'индивидуальные результаты',
                'консультация специалиста',
                'условия применения'
            ],
            'age_restrictions': [
                '18+', '21+', 'только для взрослых'
            ]
        }
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу по созданию рекламного креатива"""
        try:
            self.status = AgentStatus.BUSY
            self.last_activity = datetime.now()
            
            task_data = task.context
            task_type = task_data.get("task_type", "create_creative")
            
            if task_type == "create_creative":
                result = await self._create_ad_creative(task_data)
            elif task_type == "ab_test":
                result = await self._create_ab_test(task_data)
            elif task_type == "optimize_creative":
                result = await self._optimize_creative(task_data)
            elif task_type == "check_compliance":
                result = await self._check_compliance(task_data)
            else:
                raise ValueError(f"Неизвестный тип задачи: {task_type}")
            
            self.status = AgentStatus.IDLE
            self.completed_tasks.append(task.id)
            
            logger.info(f"Задача {task_type} завершена для {task.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении задачи: {e}")
            self.status = AgentStatus.ERROR
            self.error_count += 1
            raise
    
    async def _create_ad_creative(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает рекламный креатив"""
        platform = AdPlatform(task_data.get("platform", "telegram_ads"))
        objective = AdObjective(task_data.get("objective", "awareness"))
        product = task_data.get("product", "продукт")
        target_audience = task_data.get("target_audience", "общая аудитория")
        budget = task_data.get("budget")
        
        # Получаем шаблоны для цели
        templates = self.creative_templates.get(objective.value, self.creative_templates['awareness'])
        
        # Генерируем креатив
        headline = self._generate_headline(templates['headline_templates'], product)
        description = self._generate_description(templates['description_templates'], product)
        cta = self._generate_cta(templates['cta_templates'])
        
        # Создаем креатив
        creative = AdCreative(
            creative_id=f"creative_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            platform=platform,
            format=AdFormat.TEXT_AD,
            objective=objective,
            headline=headline,
            description=description,
            call_to_action=cta,
            target_audience=target_audience,
            budget=budget,
            landing_page=task_data.get("landing_page"),
            keywords=task_data.get("keywords", []),
            hashtags=task_data.get("hashtags", [])
        )
        
        # Проверяем соответствие политикам
        compliance_report = await self._check_creative_compliance(creative)
        creative.compliance_status = compliance_report.compliance_status
        
        # Сохраняем в кэш
        self.creative_cache[creative.creative_id] = {
            'creative': creative,
            'timestamp': datetime.now()
        }
        
        # Обновляем статистику
        self._update_performance_stats(creative)
        
        return {
            "creative_id": creative.creative_id,
            "platform": creative.platform.value,
            "objective": creative.objective.value,
            "headline": creative.headline,
            "description": creative.description,
            "call_to_action": creative.call_to_action,
            "target_audience": creative.target_audience,
            "budget": creative.budget,
            "compliance_status": creative.compliance_status.value,
            "compliance_report": {
                "violations": compliance_report.violations,
                "recommendations": compliance_report.recommendations,
                "risk_score": compliance_report.risk_score
            },
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_headline(self, templates: List[str], product: str) -> str:
        """Генерирует заголовок"""
        import random
        template = random.choice(templates)
        return template.format(product=product)
    
    def _generate_description(self, templates: List[str], product: str) -> str:
        """Генерирует описание"""
        import random
        template = random.choice(templates)
        return template.format(product=product)
    
    def _generate_cta(self, templates: List[str]) -> str:
        """Генерирует призыв к действию"""
        import random
        return random.choice(templates)
    
    async def _check_creative_compliance(self, creative: AdCreative) -> ComplianceReport:
        """Проверяет соответствие креатива политикам платформы"""
        violations = []
        recommendations = []
        risk_score = 0.0
        
        # Проверяем запрещенные ключевые слова
        content = f"{creative.headline} {creative.description} {creative.call_to_action}".lower()
        
        for keyword in self.compliance_rules['prohibited_keywords']:
            if keyword in content:
                violations.append(f"Запрещенное ключевое слово: {keyword}")
                risk_score += 0.3
        
        # Проверяем ограниченные ключевые слова
        for keyword in self.compliance_rules['restricted_keywords']:
            if keyword in content:
                recommendations.append(f"Ограниченное ключевое слово: {keyword}")
                risk_score += 0.1
        
        # Проверяем длину заголовка
        platform_guidelines = self.platform_guidelines.get(creative.platform, {})
        max_headline_length = platform_guidelines.get('max_headline_length', 30)
        
        if len(creative.headline) > max_headline_length:
            violations.append(f"Заголовок слишком длинный: {len(creative.headline)} > {max_headline_length}")
            risk_score += 0.2
        
        # Проверяем длину описания
        max_description_length = platform_guidelines.get('max_description_length', 90)
        
        if len(creative.description) > max_description_length:
            violations.append(f"Описание слишком длинное: {len(creative.description)} > {max_description_length}")
            risk_score += 0.2
        
        # Определяем статус соответствия
        if risk_score >= 0.5:
            compliance_status = ComplianceStatus.REJECTED
        elif risk_score >= 0.2:
            compliance_status = ComplianceStatus.NEEDS_REVIEW
        else:
            compliance_status = ComplianceStatus.APPROVED
        
        return ComplianceReport(
            creative_id=creative.creative_id,
            platform=creative.platform,
            compliance_status=compliance_status,
            violations=violations,
            recommendations=recommendations,
            risk_score=risk_score
        )
    
    async def _create_ab_test(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает A/B тест рекламных креативов"""
        test_name = task_data.get("test_name", f"AB Test {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        variants_data = task_data.get("variants", [])
        
        # Создаем варианты
        variants = []
        for i, variant_data in enumerate(variants_data):
            creative_data = variant_data.get("creative", {})
            traffic_percentage = variant_data.get("traffic_percentage", 50.0)
            is_control = variant_data.get("is_control", i == 0)
            
            # Создаем креатив для варианта
            creative = await self._create_ad_creative(creative_data)
            
            variant = ABTestVariant(
                variant_id=f"variant_{i+1}",
                creative=creative,
                traffic_percentage=traffic_percentage,
                is_control=is_control
            )
            variants.append(variant)
        
        # Создаем A/B тест
        ab_test = ABTest(
            test_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=test_name,
            variants=variants,
            start_date=datetime.now()
        )
        
        # Сохраняем тест
        self.ab_tests[ab_test.test_id] = ab_test
        
        return {
            "test_id": ab_test.test_id,
            "test_name": ab_test.name,
            "variants": [
                {
                    "variant_id": variant.variant_id,
                    "creative_id": variant.creative.creative_id,
                    "traffic_percentage": variant.traffic_percentage,
                    "is_control": variant.is_control
                }
                for variant in variants
            ],
            "start_date": ab_test.start_date.isoformat(),
            "status": ab_test.status
        }
    
    async def _optimize_creative(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Оптимизирует рекламный креатив"""
        creative_id = task_data.get("creative_id")
        performance_data = task_data.get("performance_data", {})
        
        if creative_id not in self.creative_cache:
            raise ValueError(f"Креатив {creative_id} не найден")
        
        creative = self.creative_cache[creative_id]['creative']
        
        # Анализируем производительность
        metrics = PerformanceMetrics(**performance_data)
        
        # Определяем области для оптимизации
        optimizations = []
        
        if metrics.ctr < self.optimization_settings['min_ctr_threshold']:
            optimizations.append("Низкий CTR - оптимизировать заголовок")
        
        if metrics.conversion_rate < self.optimization_settings['min_conversion_rate_threshold']:
            optimizations.append("Низкая конверсия - оптимизировать описание")
        
        if metrics.cpc > self.optimization_settings['max_cpc_threshold']:
            optimizations.append("Высокий CPC - оптимизировать таргетинг")
        
        if metrics.roi < self.optimization_settings['target_roi']:
            optimizations.append("Низкий ROI - оптимизировать креатив")
        
        # Генерируем рекомендации
        recommendations = self._generate_optimization_recommendations(creative, metrics)
        
        return {
            "creative_id": creative_id,
            "current_metrics": {
                "ctr": metrics.ctr,
                "conversion_rate": metrics.conversion_rate,
                "cpc": metrics.cpc,
                "roi": metrics.roi
            },
            "optimizations": optimizations,
            "recommendations": recommendations,
            "optimized_at": datetime.now().isoformat()
        }
    
    def _generate_optimization_recommendations(self, creative: AdCreative, metrics: PerformanceMetrics) -> List[str]:
        """Генерирует рекомендации по оптимизации"""
        recommendations = []
        
        if metrics.ctr < 0.02:
            recommendations.append("Добавить эмоциональные слова в заголовок")
            recommendations.append("Использовать числа и проценты")
            recommendations.append("Добавить срочность")
        
        if metrics.conversion_rate < 0.01:
            recommendations.append("Улучшить описание продукта")
            recommendations.append("Добавить социальные доказательства")
            recommendations.append("Усилить призыв к действию")
        
        if metrics.cpc > 5.0:
            recommendations.append("Уточнить таргетинг аудитории")
            recommendations.append("Использовать длинные ключевые слова")
            recommendations.append("Оптимизировать ставки")
        
        if metrics.roi < 2.0:
            recommendations.append("Пересмотреть ценовую стратегию")
            recommendations.append("Улучшить посадочную страницу")
            recommendations.append("Оптимизировать воронку конверсии")
        
        return recommendations
    
    async def _check_compliance(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверяет соответствие политикам"""
        creative_id = task_data.get("creative_id")
        
        if creative_id not in self.creative_cache:
            raise ValueError(f"Креатив {creative_id} не найден")
        
        creative = self.creative_cache[creative_id]['creative']
        compliance_report = await self._check_creative_compliance(creative)
        
        return {
            "creative_id": creative_id,
            "compliance_status": compliance_report.compliance_status.value,
            "violations": compliance_report.violations,
            "recommendations": compliance_report.recommendations,
            "risk_score": compliance_report.risk_score,
            "checked_at": compliance_report.generated_at.isoformat()
        }
    
    def _update_performance_stats(self, creative: AdCreative):
        """Обновляет статистику производительности"""
        self.performance_stats['total_creatives'] += 1
        
        if creative.compliance_status == ComplianceStatus.APPROVED:
            self.performance_stats['successful_creatives'] += 1
        else:
            self.performance_stats['failed_creatives'] += 1
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику производительности"""
        return {
            "total_creatives": self.performance_stats['total_creatives'],
            "successful_creatives": self.performance_stats['successful_creatives'],
            "failed_creatives": self.performance_stats['failed_creatives'],
            "success_rate": (
                self.performance_stats['successful_creatives'] / 
                max(self.performance_stats['total_creatives'], 1) * 100
            ),
            "avg_ctr": self.performance_stats['avg_ctr'],
            "avg_conversion_rate": self.performance_stats['avg_conversion_rate'],
            "avg_roi": self.performance_stats['avg_roi'],
            "total_spend": self.performance_stats['total_spend'],
            "total_revenue": self.performance_stats['total_revenue'],
            "active_ab_tests": len([test for test in self.ab_tests.values() if test.status == "active"]),
            "cache_size": len(self.creative_cache),
            "last_activity": self.last_activity.isoformat()
        }
