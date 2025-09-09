"""
TrendAnalyzer - Система анализа и скоринга трендов
Специализированные алгоритмы для оценки потенциала трендов
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

logger = logging.getLogger(__name__)


class TrendScore(Enum):
    """Уровни оценки трендов"""
    LOW = "low"          # 0-30
    MEDIUM = "medium"    # 31-60
    HIGH = "high"        # 61-80
    VIRAL = "viral"      # 81-100


@dataclass
class TrendMetrics:
    """Метрики тренда"""
    popularity_score: float = 0.0      # Популярность (0-100)
    engagement_rate: float = 0.0       # Вовлеченность (0-100)
    growth_rate: float = 0.0           # Скорость роста (%)
    virality_potential: float = 0.0    # Потенциал вирусности (0-100)
    audience_relevance: float = 0.0    # Релевантность аудитории (0-100)
    content_potential: float = 0.0     # Потенциал для контента (0-100)
    trend_lifetime: float = 0.0        # Ожидаемое время жизни (часы)
    competition_level: float = 0.0     # Уровень конкуренции (0-100)


@dataclass
class TrendAnalysis:
    """Результат анализа тренда"""
    trend_id: str
    overall_score: float               # Общий балл (0-100)
    trend_level: TrendScore            # Уровень тренда
    metrics: TrendMetrics              # Детальные метрики
    strengths: List[str]               # Сильные стороны
    weaknesses: List[str]              # Слабые стороны
    opportunities: List[str]           # Возможности
    risks: List[str]                   # Риски
    recommendations: List[str]         # Рекомендации
    confidence_level: float = 0.0      # Уровень уверенности (0-100)
    analyzed_at: datetime = field(default_factory=datetime.now)


class TrendAnalyzer:
    """Система анализа и скоринга трендов"""
    
    def __init__(self):
        # Веса для расчета общего балла
        self.score_weights = {
            'popularity': 0.25,
            'engagement': 0.20,
            'growth_rate': 0.20,
            'virality_potential': 0.15,
            'audience_relevance': 0.10,
            'content_potential': 0.10
        }
        
        # Пороги для классификации
        self.trend_thresholds = {
            'viral_min': 80.0,
            'high_min': 60.0,
            'medium_min': 30.0
        }
        
        # Ключевые слова для анализа
        self.viral_indicators = [
            'вирусный', 'тренд', 'хайп', 'бум', 'взрыв', 'сенсация',
            'viral', 'trending', 'boom', 'sensation', 'breaking',
            'шок', 'невероятно', 'удивительно', 'потрясающе'
        ]
        
        self.engagement_boosters = [
            'вопрос', 'опрос', 'голосование', 'выбор', 'мнение',
            'question', 'poll', 'vote', 'choice', 'opinion',
            'как думаете', 'что скажете', 'ваше мнение'
        ]
        
        self.content_keywords = [
            'обучение', 'образование', 'советы', 'руководство', 'инструкция',
            'learning', 'education', 'tips', 'guide', 'tutorial',
            'как сделать', 'пошагово', 'простое объяснение'
        ]
        
        logger.info("TrendAnalyzer инициализирован")
    
    def analyze_trend(self, trend_data: Dict[str, Any], target_audience: str = "general") -> TrendAnalysis:
        """Анализирует тренд и возвращает детальную оценку"""
        try:
            logger.info(f"Анализ тренда: {trend_data.get('title', 'Unknown')}")
            
            # Извлекаем базовые метрики
            metrics = self._calculate_metrics(trend_data, target_audience)
            
            # Рассчитываем общий балл
            overall_score = self._calculate_overall_score(metrics)
            
            # Определяем уровень тренда
            trend_level = self._determine_trend_level(overall_score)
            
            # Анализируем сильные и слабые стороны
            strengths, weaknesses = self._analyze_strengths_weaknesses(metrics, trend_data)
            
            # Выявляем возможности и риски
            opportunities, risks = self._identify_opportunities_risks(metrics, trend_data)
            
            # Генерируем рекомендации
            recommendations = self._generate_recommendations(metrics, trend_level, target_audience)
            
            # Рассчитываем уровень уверенности
            confidence_level = self._calculate_confidence_level(trend_data, metrics)
            
            return TrendAnalysis(
                trend_id=trend_data.get('trend_id', 'unknown'),
                overall_score=overall_score,
                trend_level=trend_level,
                metrics=metrics,
                strengths=strengths,
                weaknesses=weaknesses,
                opportunities=opportunities,
                risks=risks,
                recommendations=recommendations,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.error(f"Ошибка анализа тренда: {e}")
            return self._create_error_analysis(trend_data, str(e))
    
    def _calculate_metrics(self, trend_data: Dict[str, Any], target_audience: str) -> TrendMetrics:
        """Рассчитывает метрики тренда"""
        title = trend_data.get('title', '').lower()
        description = trend_data.get('description', '').lower()
        text_content = f"{title} {description}"
        
        # Популярность
        popularity_score = min(trend_data.get('popularity_score', 0), 100)
        
        # Вовлеченность
        engagement_rate = min(trend_data.get('engagement_rate', 0), 100)
        
        # Скорость роста
        growth_rate = max(trend_data.get('growth_rate', 0), 0)
        
        # Потенциал вирусности
        virality_potential = self._calculate_virality_potential(text_content, popularity_score, engagement_rate)
        
        # Релевантность аудитории
        audience_relevance = self._calculate_audience_relevance(text_content, target_audience)
        
        # Потенциал для контента
        content_potential = self._calculate_content_potential(text_content, trend_data)
        
        # Время жизни тренда
        trend_lifetime = self._estimate_trend_lifetime(popularity_score, growth_rate, virality_potential)
        
        # Уровень конкуренции
        competition_level = self._estimate_competition_level(popularity_score, text_content)
        
        return TrendMetrics(
            popularity_score=popularity_score,
            engagement_rate=engagement_rate,
            growth_rate=growth_rate,
            virality_potential=virality_potential,
            audience_relevance=audience_relevance,
            content_potential=content_potential,
            trend_lifetime=trend_lifetime,
            competition_level=competition_level
        )
    
    def _calculate_virality_potential(self, text: str, popularity: float, engagement: float) -> float:
        """Рассчитывает потенциал вирусности"""
        virality_score = 0.0
        
        # Проверяем вирусные индикаторы
        viral_indicators_found = sum(1 for indicator in self.viral_indicators if indicator in text)
        virality_score += min(viral_indicators_found * 10, 30)
        
        # Проверяем бустеры вовлеченности
        engagement_boosters_found = sum(1 for booster in self.engagement_boosters if booster in text)
        virality_score += min(engagement_boosters_found * 8, 20)
        
        # Учитываем популярность и вовлеченность
        virality_score += (popularity * 0.3) + (engagement * 0.2)
        
        # Бонус за хештеги и упоминания
        hashtag_count = text.count('#')
        mention_count = text.count('@')
        virality_score += min((hashtag_count + mention_count) * 2, 10)
        
        return min(virality_score, 100)
    
    def _calculate_audience_relevance(self, text: str, target_audience: str) -> float:
        """Рассчитывает релевантность для целевой аудитории"""
        audience_keywords = {
            'tech_audience': ['технологии', 'it', 'программирование', 'стартапы', 'ии', 'искусственный интеллект'],
            'business_audience': ['бизнес', 'маркетинг', 'финансы', 'предпринимательство', 'инвестиции'],
            'general_audience': ['новости', 'развлечения', 'образование', 'здоровье', 'спорт']
        }
        
        keywords = audience_keywords.get(target_audience, audience_keywords['general_audience'])
        
        relevance_score = 0.0
        for keyword in keywords:
            if keyword in text:
                relevance_score += 15
        
        # Базовый балл для общей аудитории
        if target_audience == 'general_audience':
            relevance_score += 20
        
        return min(relevance_score, 100)
    
    def _calculate_content_potential(self, text: str, trend_data: Dict[str, Any]) -> float:
        """Рассчитывает потенциал для создания контента"""
        content_score = 0.0
        
        # Проверяем ключевые слова для контента
        content_keywords_found = sum(1 for keyword in self.content_keywords if keyword in text)
        content_score += min(content_keywords_found * 12, 40)
        
        # Учитываем длину и информативность
        text_length = len(text)
        if 50 <= text_length <= 200:
            content_score += 20  # Оптимальная длина для контента
        elif text_length > 200:
            content_score += 10  # Слишком длинный, но информативный
        
        # Проверяем наличие вопросов (хорошо для контента)
        if '?' in text or any(q in text for q in ['как', 'что', 'почему', 'когда', 'где']):
            content_score += 15
        
        # Учитываем тип тренда
        trend_type = trend_data.get('trend_type', '')
        if trend_type in ['news', 'educational']:
            content_score += 20
        elif trend_type == 'viral':
            content_score += 15
        
        return min(content_score, 100)
    
    def _estimate_trend_lifetime(self, popularity: float, growth_rate: float, virality: float) -> float:
        """Оценивает время жизни тренда в часах"""
        # Базовое время жизни
        base_lifetime = 24.0
        
        # Корректировки
        if popularity > 80:
            base_lifetime *= 1.5  # Популярные тренды живут дольше
        elif popularity < 30:
            base_lifetime *= 0.5  # Непопулярные тренды быстро угасают
        
        if growth_rate > 50:
            base_lifetime *= 1.3  # Быстро растущие тренды
        elif growth_rate < 10:
            base_lifetime *= 0.7  # Медленно растущие тренды
        
        if virality > 70:
            base_lifetime *= 1.2  # Вирусные тренды
        elif virality < 30:
            base_lifetime *= 0.8  # Невирусные тренды
        
        return max(base_lifetime, 2.0)  # Минимум 2 часа
    
    def _estimate_competition_level(self, popularity: float, text: str) -> float:
        """Оценивает уровень конкуренции"""
        competition_score = popularity * 0.6  # Базовый уровень на основе популярности
        
        # Популярные темы = больше конкуренции
        popular_topics = ['ии', 'искусственный интеллект', 'криптовалюты', 'блокчейн', 'стартапы']
        for topic in popular_topics:
            if topic in text:
                competition_score += 20
        
        return min(competition_score, 100)
    
    def _calculate_overall_score(self, metrics: TrendMetrics) -> float:
        """Рассчитывает общий балл тренда"""
        score = 0.0
        
        score += metrics.popularity_score * self.score_weights['popularity']
        score += metrics.engagement_rate * self.score_weights['engagement']
        score += min(metrics.growth_rate, 100) * self.score_weights['growth_rate'] / 100
        score += metrics.virality_potential * self.score_weights['virality_potential']
        score += metrics.audience_relevance * self.score_weights['audience_relevance']
        score += metrics.content_potential * self.score_weights['content_potential']
        
        return min(score, 100)
    
    def _determine_trend_level(self, overall_score: float) -> TrendScore:
        """Определяет уровень тренда"""
        if overall_score >= self.trend_thresholds['viral_min']:
            return TrendScore.VIRAL
        elif overall_score >= self.trend_thresholds['high_min']:
            return TrendScore.HIGH
        elif overall_score >= self.trend_thresholds['medium_min']:
            return TrendScore.MEDIUM
        else:
            return TrendScore.LOW
    
    def _analyze_strengths_weaknesses(self, metrics: TrendMetrics, trend_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Анализирует сильные и слабые стороны тренда"""
        strengths = []
        weaknesses = []
        
        # Анализ сильных сторон
        if metrics.popularity_score > 70:
            strengths.append("Высокая популярность")
        if metrics.engagement_rate > 70:
            strengths.append("Высокий уровень вовлеченности")
        if metrics.growth_rate > 30:
            strengths.append("Быстрый рост")
        if metrics.virality_potential > 70:
            strengths.append("Высокий потенциал вирусности")
        if metrics.audience_relevance > 70:
            strengths.append("Высокая релевантность для аудитории")
        if metrics.content_potential > 70:
            strengths.append("Отличный потенциал для контента")
        
        # Анализ слабых сторон
        if metrics.popularity_score < 40:
            weaknesses.append("Низкая популярность")
        if metrics.engagement_rate < 40:
            weaknesses.append("Низкий уровень вовлеченности")
        if metrics.growth_rate < 10:
            weaknesses.append("Медленный рост")
        if metrics.virality_potential < 40:
            weaknesses.append("Низкий потенциал вирусности")
        if metrics.audience_relevance < 40:
            weaknesses.append("Низкая релевантность для аудитории")
        if metrics.content_potential < 40:
            weaknesses.append("Ограниченный потенциал для контента")
        if metrics.competition_level > 80:
            weaknesses.append("Высокая конкуренция")
        
        return strengths, weaknesses
    
    def _identify_opportunities_risks(self, metrics: TrendMetrics, trend_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Выявляет возможности и риски"""
        opportunities = []
        risks = []
        
        # Возможности
        if metrics.trend_lifetime > 48:
            opportunities.append("Длительный жизненный цикл тренда")
        if metrics.competition_level < 50:
            opportunities.append("Низкая конкуренция")
        if metrics.growth_rate > 20 and metrics.popularity_score < 60:
            opportunities.append("Растущий тренд с потенциалом")
        if metrics.virality_potential > 60:
            opportunities.append("Возможность создать вирусный контент")
        
        # Риски
        if metrics.trend_lifetime < 12:
            risks.append("Короткий жизненный цикл тренда")
        if metrics.competition_level > 80:
            risks.append("Высокая конкуренция")
        if metrics.growth_rate < 0:
            risks.append("Снижающийся тренд")
        if metrics.popularity_score > 90:
            risks.append("Тренд на пике популярности")
        
        return opportunities, risks
    
    def _generate_recommendations(self, metrics: TrendMetrics, trend_level: TrendScore, target_audience: str) -> List[str]:
        """Генерирует рекомендации на основе анализа"""
        recommendations = []
        
        # Рекомендации по уровню тренда
        if trend_level == TrendScore.VIRAL:
            recommendations.append("Срочно создавать контент - тренд вирусный")
            recommendations.append("Использовать все доступные каналы распространения")
        elif trend_level == TrendScore.HIGH:
            recommendations.append("Приоритетный тренд для контент-плана")
            recommendations.append("Создать серию материалов по теме")
        elif trend_level == TrendScore.MEDIUM:
            recommendations.append("Рассмотреть для включения в контент-план")
            recommendations.append("Мониторить развитие тренда")
        else:
            recommendations.append("Низкий приоритет - тренд слабый")
            recommendations.append("Рассмотреть альтернативные темы")
        
        # Рекомендации по метрикам
        if metrics.content_potential > 70:
            recommendations.append("Отличная тема для образовательного контента")
        if metrics.virality_potential > 70:
            recommendations.append("Создать интерактивный контент для вирусности")
        if metrics.audience_relevance > 70:
            recommendations.append("Тема идеально подходит для целевой аудитории")
        if metrics.competition_level < 50:
            recommendations.append("Возможность стать первым в теме")
        
        # Рекомендации по времени
        if metrics.trend_lifetime < 24:
            recommendations.append("Действовать быстро - тренд краткосрочный")
        elif metrics.trend_lifetime > 72:
            recommendations.append("Есть время для качественной проработки")
        
        return recommendations
    
    def _calculate_confidence_level(self, trend_data: Dict[str, Any], metrics: TrendMetrics) -> float:
        """Рассчитывает уровень уверенности в анализе"""
        confidence = 50.0  # Базовый уровень
        
        # Увеличиваем уверенность при наличии данных
        if trend_data.get('popularity_score', 0) > 0:
            confidence += 10
        if trend_data.get('engagement_rate', 0) > 0:
            confidence += 10
        if trend_data.get('growth_rate', 0) > 0:
            confidence += 10
        if trend_data.get('keywords') and len(trend_data['keywords']) > 0:
            confidence += 10
        if trend_data.get('hashtags') and len(trend_data['hashtags']) > 0:
            confidence += 5
        
        # Уменьшаем уверенность при недостатке данных
        if not trend_data.get('description'):
            confidence -= 15
        if not trend_data.get('source'):
            confidence -= 10
        
        return max(min(confidence, 100), 0)
    
    def _create_error_analysis(self, trend_data: Dict[str, Any], error_message: str) -> TrendAnalysis:
        """Создает анализ ошибки"""
        return TrendAnalysis(
            trend_id=trend_data.get('trend_id', 'error'),
            overall_score=0.0,
            trend_level=TrendScore.LOW,
            metrics=TrendMetrics(),
            strengths=[],
            weaknesses=[f"Ошибка анализа: {error_message}"],
            opportunities=[],
            risks=["Недостаточно данных для анализа"],
            recommendations=["Повторить анализ с корректными данными"],
            confidence_level=0.0
        )
    
    def compare_trends(self, trends: List[Dict[str, Any]], target_audience: str = "general") -> List[TrendAnalysis]:
        """Сравнивает несколько трендов"""
        analyses = []
        
        for trend_data in trends:
            analysis = self.analyze_trend(trend_data, target_audience)
            analyses.append(analysis)
        
        # Сортируем по общему баллу
        analyses.sort(key=lambda x: x.overall_score, reverse=True)
        
        return analyses
    
    def get_trend_ranking(self, analyses: List[TrendAnalysis]) -> Dict[str, Any]:
        """Создает рейтинг трендов"""
        if not analyses:
            return {"ranking": [], "summary": "Нет данных для ранжирования"}
        
        ranking = []
        for i, analysis in enumerate(analyses, 1):
            ranking.append({
                "rank": i,
                "trend_id": analysis.trend_id,
                "score": round(analysis.overall_score, 2),
                "level": analysis.trend_level.value,
                "confidence": round(analysis.confidence_level, 2)
            })
        
        # Статистика
        total_trends = len(analyses)
        viral_count = len([a for a in analyses if a.trend_level == TrendScore.VIRAL])
        high_count = len([a for a in analyses if a.trend_level == TrendScore.HIGH])
        avg_score = sum(a.overall_score for a in analyses) / total_trends
        
        summary = {
            "total_trends": total_trends,
            "viral_trends": viral_count,
            "high_priority_trends": high_count,
            "average_score": round(avg_score, 2),
            "top_trend": ranking[0] if ranking else None
        }
        
        return {
            "ranking": ranking,
            "summary": summary
        }
