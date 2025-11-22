"""
CommunityConciergeAgent - Агент для управления сообществом и модерации
Модерация комментариев, автоматические ответы, эскалация запросов
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


class CommentType(Enum):
    """Типы комментариев"""
    QUESTION = "question"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    SUPPORT_REQUEST = "support_request"
    FEEDBACK = "feedback"
    GENERAL = "general"


class SentimentType(Enum):
    """Типы тональности"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class EscalationLevel(Enum):
    """Уровни эскалации"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseType(Enum):
    """Типы ответов"""
    AUTO_REPLY = "auto_reply"
    TEMPLATE_REPLY = "template_reply"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    MODERATE = "moderate"
    IGNORE = "ignore"


@dataclass
class Comment:
    """Комментарий пользователя"""
    comment_id: str
    user_id: str
    username: str
    content: str
    platform: str
    post_id: str
    timestamp: datetime
    comment_type: CommentType
    sentiment: SentimentType
    language: str = "ru"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModerationResult:
    """Результат модерации"""
    comment_id: str
    action: ResponseType
    confidence: float
    reason: str
    auto_reply: Optional[str] = None
    escalation_level: EscalationLevel = EscalationLevel.NONE
    moderation_notes: str = ""
    requires_human_review: bool = False


@dataclass
class CommunityInsight:
    """Инсайт сообщества"""
    insight_id: str
    type: str
    title: str
    description: str
    data: Dict[str, Any]
    confidence: float
    generated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class CommunityStats:
    """Статистика сообщества"""
    total_comments: int
    positive_comments: int
    negative_comments: int
    neutral_comments: int
    auto_replies_sent: int
    escalations: int
    response_time_avg: float
    satisfaction_score: float
    top_questions: List[str] = field(default_factory=list)
    top_complaints: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


class CommunityConciergeAgent(BaseAgent):
    """Агент для управления сообществом и модерации"""
    
    def __init__(self, agent_id: str = "community_concierge_agent"):
        capability = AgentCapability(
            task_types=[TaskType.REAL_TIME],  # Быстрая реакция на комментарии
            max_concurrent_tasks=10,          # Высокая пропускная способность
            specializations=["community_management", "comment_moderation", "customer_support", "sentiment_analysis"],
            performance_score=1.3            # Высокая скорость для real-time
        )
        super().__init__(agent_id, "Community Concierge Agent", capability)
        
        # Система модерации
        self.moderation_rules = self._load_moderation_rules()
        self.auto_reply_templates = self._load_auto_reply_templates()
        self.escalation_triggers = self._load_escalation_triggers()
        
        # Анализ тональности
        self.sentiment_analyzer = self._load_sentiment_analyzer()
        self.language_detector = self._load_language_detector()
        
        # Кэш для быстрого доступа
        self.comment_cache = {}
        self.user_history = {}
        self.response_cache = {}
        self.cache_ttl = timedelta(minutes=30)
        
        # Статистика и инсайты
        self.community_stats = CommunityStats(
            total_comments=0,
            positive_comments=0,
            negative_comments=0,
            neutral_comments=0,
            auto_replies_sent=0,
            escalations=0,
            response_time_avg=0.0,
            satisfaction_score=0.0
        )
        
        # Настройки модерации
        self.moderation_settings = {
            'auto_reply_threshold': 0.8,
            'escalation_threshold': 0.7,
            'spam_detection_threshold': 0.9,
            'inappropriate_threshold': 0.8,
            'response_time_target': 5.0,  # секунд
            'max_auto_replies_per_user': 3
        }
        
        # Очередь обработки
        self.processing_queue = asyncio.Queue()
        self.escalation_queue = asyncio.Queue()
        
        logger.info(f"CommunityConciergeAgent {agent_id} инициализирован")
    
    def can_handle_task(self, task: Task) -> bool:
        """
        Проверяет, может ли CommunityConciergeAgent выполнить задачу
        НЕ обрабатывает задачи публикации и задачи с изображениями
        """
        # Сначала проверяем базовые условия
        if not super().can_handle_task(task):
            return False
        
        # CommunityConciergeAgent НЕ обрабатывает задачи публикации
        if "Publish" in task.name or "publish" in task.name.lower():
            return False
        
        # CommunityConciergeAgent НЕ обрабатывает задачи генерации/поиска изображений
        image_keywords = ["Image", "image", "Stock", "stock", "Generate", "generate", "multimedia"]
        if any(keyword in task.name for keyword in image_keywords):
            return False
        
        # Также проверяем контекст задачи
        task_context = task.context if hasattr(task, 'context') else {}
        if task_context.get("image_source") or task_context.get("content_type") in ["post_image", "image"]:
            return False
        
        return True
    
    def _load_moderation_rules(self) -> Dict[str, Any]:
        """Загружает правила модерации"""
        return {
            'spam_keywords': [
                'купить', 'продать', 'заработок', 'криптовалюта', 'инвестиции',
                'реклама', 'промо', 'скидка', 'акция', 'бесплатно'
            ],
            'inappropriate_keywords': [
                'ругательство', 'оскорбление', 'дискриминация', 'экстремизм'
            ],
            'question_patterns': [
                r'как\s+.*\?', r'что\s+.*\?', r'где\s+.*\?', r'когда\s+.*\?',
                r'почему\s+.*\?', r'зачем\s+.*\?', r'сколько\s+.*\?'
            ],
            'complaint_patterns': [
                r'проблема', r'ошибка', r'не\s+работает', r'плохо', r'ужасно',
                r'разочарован', r'недоволен', r'жалоба'
            ],
            'compliment_patterns': [
                r'спасибо', r'отлично', r'супер', r'классно', r'круто',
                r'молодцы', r'хорошо', r'понравилось'
            ]
        }
    
    def _load_auto_reply_templates(self) -> Dict[str, Dict[str, str]]:
        """Загружает шаблоны автоматических ответов"""
        return {
            'greeting': {
                'template': 'Привет, {username}! 👋 Спасибо за комментарий!',
                'conditions': ['positive_sentiment', 'general_comment']
            },
            'question_general': {
                'template': 'Спасибо за вопрос! 🤔 Наша команда скоро ответит. А пока можете посмотреть FAQ: {faq_link}',
                'conditions': ['question_type', 'general_question']
            },
            'question_specific': {
                'template': 'Отличный вопрос! 💡 {specific_answer}',
                'conditions': ['question_type', 'specific_question']
            },
            'complaint': {
                'template': 'Извините за неудобства! 😔 Мы разберемся с проблемой. Напишите нам в личные сообщения для быстрого решения.',
                'conditions': ['complaint_type', 'negative_sentiment']
            },
            'compliment': {
                'template': 'Спасибо за отзыв! ❤️ Это мотивирует нас работать еще лучше!',
                'conditions': ['compliment_type', 'positive_sentiment']
            },
            'spam': {
                'template': 'Спасибо за интерес к нашему контенту! 📝 Для рекламы обращайтесь в личные сообщения.',
                'conditions': ['spam_type', 'advertisement']
            },
            'escalation': {
                'template': 'Спасибо за обращение! 🔄 Мы передали ваш запрос специалисту. Ответим в ближайшее время.',
                'conditions': ['escalation_required', 'complex_issue']
            }
        }
    
    def _load_escalation_triggers(self) -> Dict[str, Any]:
        """Загружает триггеры для эскалации"""
        return {
            'critical_keywords': [
                'юридический', 'суд', 'жалоба', 'претензия', 'возврат',
                'компенсация', 'ущерб', 'нарушение', 'закон'
            ],
            'complex_questions': [
                'техническая поддержка', 'настройка', 'интеграция',
                'кастомизация', 'разработка'
            ],
            'negative_escalation_threshold': 0.8,
            'complaint_escalation_threshold': 0.7,
            'multiple_complaints_threshold': 3
        }
    
    def _load_sentiment_analyzer(self) -> Dict[str, Any]:
        """Загружает анализатор тональности"""
        return {
            'positive_words': [
                'отлично', 'супер', 'классно', 'круто', 'молодцы', 'хорошо',
                'понравилось', 'спасибо', 'благодарю', 'восхищен', 'впечатлен'
            ],
            'negative_words': [
                'плохо', 'ужасно', 'отвратительно', 'недоволен', 'разочарован',
                'злой', 'бесит', 'ненавижу', 'отвращение', 'проблема'
            ],
            'neutral_words': [
                'нормально', 'обычно', 'стандартно', 'типично', 'средне'
            ],
            'intensity_modifiers': {
                'very': 1.5, 'очень': 1.5, 'крайне': 2.0, 'чрезвычайно': 2.0,
                'слегка': 0.5, 'немного': 0.5, 'чуть': 0.5
            }
        }
    
    def _load_language_detector(self) -> Dict[str, Any]:
        """Загружает детектор языка"""
        return {
            'russian_patterns': [
                r'[а-яё]', r'[А-ЯЁ]', r'[0-9]+\s+[а-яё]+', r'[а-яё]+\s+[0-9]+'
            ],
            'english_patterns': [
                r'[a-z]', r'[A-Z]', r'[0-9]+\s+[a-z]+', r'[a-z]+\s+[0-9]+'
            ],
            'default_language': 'ru'
        }
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу по модерации комментария"""
        try:
            self.status = AgentStatus.BUSY
            self.last_activity = datetime.now()
            
            task_data = task.context
            comment_data = task_data.get("comment", {})
            moderation_type = task_data.get("moderation_type", "auto")
            
            # Создаем объект комментария
            comment = Comment(
                comment_id=comment_data.get("id", task.id),
                user_id=comment_data.get("user_id", ""),
                username=comment_data.get("username", ""),
                content=comment_data.get("content", ""),
                platform=comment_data.get("platform", ""),
                post_id=comment_data.get("post_id", ""),
                timestamp=datetime.fromisoformat(comment_data.get("timestamp", datetime.now().isoformat())),
                comment_type=CommentType.GENERAL,
                sentiment=SentimentType.NEUTRAL
            )
            
            # Анализируем комментарий
            analysis_result = await self._analyze_comment(comment)
            
            # Принимаем решение о модерации
            moderation_result = await self._moderate_comment(comment, analysis_result)
            
            # Обновляем статистику
            self._update_community_stats(comment, moderation_result)
            
            # Генерируем инсайты
            insights = await self._generate_insights(comment, analysis_result)
            
            self.status = AgentStatus.IDLE
            self.completed_tasks.append(task.id)
            
            result = {
                "comment_id": comment.comment_id,
                "moderation_result": {
                    "action": moderation_result.action.value,
                    "confidence": moderation_result.confidence,
                    "reason": moderation_result.reason,
                    "auto_reply": moderation_result.auto_reply,
                    "escalation_level": moderation_result.escalation_level.value,
                    "requires_human_review": moderation_result.requires_human_review
                },
                "analysis": {
                    "comment_type": analysis_result["comment_type"].value,
                    "sentiment": analysis_result["sentiment"].value,
                    "language": analysis_result["language"],
                    "confidence": analysis_result["confidence"]
                },
                "insights": [
                    {
                        "type": insight.type,
                        "title": insight.title,
                        "description": insight.description,
                        "confidence": insight.confidence
                    }
                    for insight in insights
                ],
                "community_stats": {
                    "total_comments": self.community_stats.total_comments,
                    "positive_comments": self.community_stats.positive_comments,
                    "negative_comments": self.community_stats.negative_comments,
                    "auto_replies_sent": self.community_stats.auto_replies_sent,
                    "escalations": self.community_stats.escalations
                },
                "processing_time": (datetime.now() - self.last_activity).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Модерация комментария {comment.comment_id} завершена. Действие: {moderation_result.action.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при модерации комментария: {e}")
            self.status = AgentStatus.ERROR
            self.error_count += 1
            raise
    
    async def _analyze_comment(self, comment: Comment) -> Dict[str, Any]:
        """Анализирует комментарий"""
        # Определяем тип комментария
        comment_type = self._classify_comment_type(comment.content)
        
        # Анализируем тональность
        sentiment = self._analyze_sentiment(comment.content)
        
        # Определяем язык
        language = self._detect_language(comment.content)
        
        # Проверяем на спам
        is_spam = self._detect_spam(comment.content)
        
        # Проверяем на неподходящий контент
        is_inappropriate = self._detect_inappropriate(comment.content)
        
        # Вычисляем общую уверенность
        confidence = self._calculate_confidence(comment_type, sentiment, is_spam, is_inappropriate)
        
        return {
            "comment_type": comment_type,
            "sentiment": sentiment,
            "language": language,
            "is_spam": is_spam,
            "is_inappropriate": is_inappropriate,
            "confidence": confidence
        }
    
    def _classify_comment_type(self, content: str) -> CommentType:
        """Классифицирует тип комментария"""
        content_lower = content.lower()
        
        # Проверяем на вопросы
        for pattern in self.moderation_rules['question_patterns']:
            if re.search(pattern, content_lower):
                return CommentType.QUESTION
        
        # Проверяем на жалобы
        for pattern in self.moderation_rules['complaint_patterns']:
            if re.search(pattern, content_lower):
                return CommentType.COMPLAINT
        
        # Проверяем на комплименты
        for pattern in self.moderation_rules['compliment_patterns']:
            if re.search(pattern, content_lower):
                return CommentType.COMPLIMENT
        
        # Проверяем на спам
        for keyword in self.moderation_rules['spam_keywords']:
            if keyword in content_lower:
                return CommentType.SPAM
        
        # Проверяем на неподходящий контент
        for keyword in self.moderation_rules['inappropriate_keywords']:
            if keyword in content_lower:
                return CommentType.INAPPROPRIATE
        
        return CommentType.GENERAL
    
    def _analyze_sentiment(self, content: str) -> SentimentType:
        """Анализирует тональность комментария"""
        content_lower = content.lower()
        
        positive_score = 0
        negative_score = 0
        
        # Анализируем положительные слова
        for word in self.sentiment_analyzer['positive_words']:
            if word in content_lower:
                positive_score += 1
        
        # Анализируем отрицательные слова
        for word in self.sentiment_analyzer['negative_words']:
            if word in content_lower:
                negative_score += 1
        
        # Применяем модификаторы интенсивности
        for modifier, multiplier in self.sentiment_analyzer['intensity_modifiers'].items():
            if modifier in content_lower:
                positive_score *= multiplier
                negative_score *= multiplier
        
        # Определяем тональность
        if positive_score > negative_score * 1.5:
            return SentimentType.POSITIVE
        elif negative_score > positive_score * 1.5:
            return SentimentType.NEGATIVE
        elif positive_score > 0 and negative_score > 0:
            return SentimentType.MIXED
        else:
            return SentimentType.NEUTRAL
    
    def _detect_language(self, content: str) -> str:
        """Определяет язык комментария"""
        # Простое определение языка по символам
        russian_chars = len(re.findall(r'[а-яё]', content, re.IGNORECASE))
        english_chars = len(re.findall(r'[a-z]', content, re.IGNORECASE))
        
        if russian_chars > english_chars:
            return 'ru'
        elif english_chars > russian_chars:
            return 'en'
        else:
            return self.language_detector['default_language']
    
    def _detect_spam(self, content: str) -> bool:
        """Определяет спам"""
        content_lower = content.lower()
        
        # Проверяем ключевые слова спама
        spam_count = sum(1 for keyword in self.moderation_rules['spam_keywords'] 
                        if keyword in content_lower)
        
        # Проверяем длину (слишком короткие или длинные сообщения)
        if len(content) < 10 or len(content) > 500:
            spam_count += 1
        
        # Проверяем на повторяющиеся символы
        if re.search(r'(.)\1{4,}', content):
            spam_count += 1
        
        return spam_count >= 2
    
    def _detect_inappropriate(self, content: str) -> bool:
        """Определяет неподходящий контент"""
        content_lower = content.lower()
        
        # Проверяем ключевые слова
        for keyword in self.moderation_rules['inappropriate_keywords']:
            if keyword in content_lower:
                return True
        
        # Проверяем на избыточное использование заглавных букв
        if len(re.findall(r'[А-ЯЁ]', content)) > len(content) * 0.7:
            return True
        
        return False
    
    def _calculate_confidence(self, comment_type: CommentType, sentiment: SentimentType, 
                            is_spam: bool, is_inappropriate: bool) -> float:
        """Вычисляет уверенность в анализе"""
        confidence = 0.5  # Базовая уверенность
        
        # Увеличиваем уверенность для четких типов
        if comment_type in [CommentType.SPAM, CommentType.INAPPROPRIATE]:
            confidence += 0.3
        
        if sentiment in [SentimentType.POSITIVE, SentimentType.NEGATIVE]:
            confidence += 0.2
        
        if is_spam or is_inappropriate:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    async def _moderate_comment(self, comment: Comment, analysis: Dict[str, Any]) -> ModerationResult:
        """Принимает решение о модерации комментария"""
        comment_type = analysis["comment_type"]
        sentiment = analysis["sentiment"]
        is_spam = analysis["is_spam"]
        is_inappropriate = analysis["is_inappropriate"]
        confidence = analysis["confidence"]
        
        # Определяем действие
        if is_spam:
            action = ResponseType.TEMPLATE_REPLY
            reason = "Обнаружен спам"
            auto_reply = self.auto_reply_templates['spam']['template']
            escalation_level = EscalationLevel.NONE
            
        elif is_inappropriate:
            action = ResponseType.MODERATE
            reason = "Неподходящий контент"
            auto_reply = None
            escalation_level = EscalationLevel.MEDIUM
            
        elif comment_type == CommentType.COMPLAINT and sentiment == SentimentType.NEGATIVE:
            action = ResponseType.ESCALATE_TO_HUMAN
            reason = "Жалоба требует внимания"
            auto_reply = self.auto_reply_templates['complaint']['template']
            escalation_level = EscalationLevel.HIGH
            
        elif comment_type == CommentType.QUESTION:
            action = ResponseType.AUTO_REPLY
            reason = "Типовой вопрос"
            auto_reply = self._generate_question_reply(comment.content)
            escalation_level = EscalationLevel.NONE
            
        elif comment_type == CommentType.COMPLIMENT:
            action = ResponseType.AUTO_REPLY
            reason = "Положительный отзыв"
            auto_reply = self.auto_reply_templates['compliment']['template']
            escalation_level = EscalationLevel.NONE
            
        else:
            action = ResponseType.AUTO_REPLY
            reason = "Общий комментарий"
            auto_reply = self.auto_reply_templates['greeting']['template']
            escalation_level = EscalationLevel.NONE
        
        # Проверяем необходимость эскалации
        if self._should_escalate(comment, analysis):
            action = ResponseType.ESCALATE_TO_HUMAN
            escalation_level = EscalationLevel.HIGH
            reason = "Требуется эскалация"
        
        return ModerationResult(
            comment_id=comment.comment_id,
            action=action,
            confidence=confidence,
            reason=reason,
            auto_reply=auto_reply,
            escalation_level=escalation_level,
            requires_human_review=escalation_level in [EscalationLevel.HIGH, EscalationLevel.CRITICAL]
        )
    
    def _generate_question_reply(self, content: str) -> str:
        """Генерирует ответ на вопрос"""
        content_lower = content.lower()
        
        # Простые ответы на типовые вопросы
        if 'как' in content_lower and 'зарегистрироваться' in content_lower:
            return "Для регистрации перейдите по ссылке: {registration_link} 📝"
        elif 'сколько' in content_lower and 'стоит' in content_lower:
            return "Цены указаны в разделе 'Тарифы': {pricing_link} 💰"
        elif 'когда' in content_lower and 'обновление' in content_lower:
            return "Обновления выходят еженедельно! Следите за новостями 📢"
        elif 'где' in content_lower and 'скачать' in content_lower:
            return "Скачать можно здесь: {download_link} 📱"
        else:
            return self.auto_reply_templates['question_general']['template']
    
    def _should_escalate(self, comment: Comment, analysis: Dict[str, Any]) -> bool:
        """Определяет необходимость эскалации"""
        content_lower = comment.content.lower()
        
        # Проверяем критические ключевые слова
        for keyword in self.escalation_triggers['critical_keywords']:
            if keyword in content_lower:
                return True
        
        # Проверяем сложные вопросы
        for keyword in self.escalation_triggers['complex_questions']:
            if keyword in content_lower:
                return True
        
        # Проверяем пороги
        if (analysis["sentiment"] == SentimentType.NEGATIVE and 
            analysis["confidence"] > self.escalation_triggers['negative_escalation_threshold']):
            return True
        
        if (analysis["comment_type"] == CommentType.COMPLAINT and 
            analysis["confidence"] > self.escalation_triggers['complaint_escalation_threshold']):
            return True
        
        return False
    
    def _update_community_stats(self, comment: Comment, moderation_result: ModerationResult):
        """Обновляет статистику сообщества"""
        self.community_stats.total_comments += 1
        
        # Обновляем статистику тональности
        if comment.sentiment == SentimentType.POSITIVE:
            self.community_stats.positive_comments += 1
        elif comment.sentiment == SentimentType.NEGATIVE:
            self.community_stats.negative_comments += 1
        else:
            self.community_stats.neutral_comments += 1
        
        # Обновляем статистику ответов
        if moderation_result.action == ResponseType.AUTO_REPLY:
            self.community_stats.auto_replies_sent += 1
        
        if moderation_result.escalation_level != EscalationLevel.NONE:
            self.community_stats.escalations += 1
        
        # Обновляем среднее время ответа
        response_time = (datetime.now() - comment.timestamp).total_seconds()
        current_avg = self.community_stats.response_time_avg
        total_comments = self.community_stats.total_comments
        
        self.community_stats.response_time_avg = (
            (current_avg * (total_comments - 1) + response_time) / total_comments
        )
    
    async def _generate_insights(self, comment: Comment, analysis: Dict[str, Any]) -> List[CommunityInsight]:
        """Генерирует инсайты сообщества"""
        insights = []
        
        # Инсайт о тональности
        if comment.sentiment == SentimentType.NEGATIVE:
            insights.append(CommunityInsight(
                insight_id=f"negative_sentiment_{comment.comment_id}",
                type="sentiment_analysis",
                title="Негативная тональность",
                description=f"Обнаружен негативный комментарий от {comment.username}",
                data={"sentiment": comment.sentiment.value, "confidence": analysis["confidence"]},
                confidence=analysis["confidence"],
                tags=["sentiment", "negative", "attention_required"]
            ))
        
        # Инсайт о типе комментария
        if analysis["comment_type"] == CommentType.QUESTION:
            insights.append(CommunityInsight(
                insight_id=f"question_{comment.comment_id}",
                type="content_analysis",
                title="Частый вопрос",
                description=f"Пользователь {comment.username} задал вопрос",
                data={"question_type": "general", "content": comment.content[:100]},
                confidence=0.8,
                tags=["question", "faq", "content_improvement"]
            ))
        
        # Инсайт о спаме
        if analysis["is_spam"]:
            insights.append(CommunityInsight(
                insight_id=f"spam_{comment.comment_id}",
                type="moderation",
                title="Обнаружен спам",
                description=f"Спам-комментарий от {comment.username}",
                data={"spam_type": "advertisement", "content": comment.content[:50]},
                confidence=0.9,
                tags=["spam", "moderation", "security"]
            ))
        
        return insights
    
    def get_community_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику сообщества"""
        return {
            "total_comments": self.community_stats.total_comments,
            "positive_comments": self.community_stats.positive_comments,
            "negative_comments": self.community_stats.negative_comments,
            "neutral_comments": self.community_stats.neutral_comments,
            "auto_replies_sent": self.community_stats.auto_replies_sent,
            "escalations": self.community_stats.escalations,
            "response_time_avg": self.community_stats.response_time_avg,
            "satisfaction_score": self.community_stats.satisfaction_score,
            "positive_ratio": (
                self.community_stats.positive_comments / 
                max(self.community_stats.total_comments, 1) * 100
            ),
            "escalation_rate": (
                self.community_stats.escalations / 
                max(self.community_stats.total_comments, 1) * 100
            ),
            "cache_size": len(self.comment_cache),
            "last_activity": self.last_activity.isoformat()
        }
