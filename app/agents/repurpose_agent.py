"""
RepurposeAgent - Агент для адаптации контента под разные форматы
Преобразует один материал в 8+ форматов для различных платформ
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


class ContentFormat(Enum):
    """Форматы контента"""
    TELEGRAM_POST = "telegram_post"
    TWITTER_THREAD = "twitter_thread"
    INSTAGRAM_CAROUSEL = "instagram_carousel"
    INSTAGRAM_STORY = "instagram_story"
    LINKEDIN_ARTICLE = "linkedin_article"
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK_VIDEO = "tiktok_video"
    PODCAST_SCRIPT = "podcast_script"
    BLOG_POST = "blog_post"
    NEWSLETTER = "newsletter"
    PRESENTATION = "presentation"
    INFOGRAPHIC = "infographic"


class ContentType(Enum):
    """Типы исходного контента"""
    LONG_ARTICLE = "long_article"
    VIDEO_SCRIPT = "video_script"
    PODCAST_EPISODE = "podcast_episode"
    PRESENTATION_SLIDES = "presentation_slides"
    SOCIAL_MEDIA_POST = "social_media_post"
    NEWSLETTER_CONTENT = "newsletter_content"
    BLOG_POST = "blog_post"
    INTERVIEW_TRANSCRIPT = "interview_transcript"


class AdaptationStrategy(Enum):
    """Стратегии адаптации"""
    EXTRACT_KEY_POINTS = "extract_key_points"
    SUMMARIZE = "summarize"
    EXPAND = "expand"
    RESTRUCTURE = "restructure"
    VISUALIZE = "visualize"
    CONVERSATIONAL = "conversational"


@dataclass
class ContentPiece:
    """Фрагмент контента"""
    content_id: str
    format: ContentFormat
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    word_count: int = 0
    character_count: int = 0
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    call_to_action: Optional[str] = None


@dataclass
class RepurposeResult:
    """Результат адаптации контента"""
    source_content_id: str
    source_format: ContentFormat
    adapted_pieces: List[ContentPiece]
    adaptation_strategy: AdaptationStrategy
    success_rate: float
    total_pieces: int
    processing_time: float
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PlatformGuidelines:
    """Руководящие принципы платформы"""
    max_length: int
    min_length: int
    preferred_tone: str
    hashtag_limit: int
    mention_style: str
    call_to_action_required: bool
    visual_elements: List[str] = field(default_factory=list)
    formatting_rules: List[str] = field(default_factory=list)


class RepurposeAgent(BaseAgent):
    """Агент для адаптации контента под разные форматы"""
    
    def __init__(self, agent_id: str = "repurpose_agent"):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED],  # Требует анализа исходного контента
            max_concurrent_tasks=3,         # Эффективный для массовой обработки
            specializations=["content_repurposing", "format_adaptation", "cross_platform", "content_optimization"],
            performance_score=1.1          # Эффективный для массовой обработки
        )
        super().__init__(agent_id, "Repurpose Agent", capability)
        
        # Шаблоны адаптации для разных форматов
        self.adaptation_templates = self._load_adaptation_templates()
        self.platform_guidelines = self._load_platform_guidelines()
        self.content_analyzers = self._load_content_analyzers()
        
        # Кэш адаптированного контента
        self.repurpose_cache = {}
        self.cache_ttl = timedelta(hours=12)  # Кэш на 12 часов
        
        # Статистика адаптации
        self.adaptation_stats = {
            'total_adaptations': 0,
            'successful_adaptations': 0,
            'failed_adaptations': 0,
            'formats_created': {},
            'average_processing_time': 0.0
        }
        
        # Настройки качества
        self.quality_thresholds = {
            'min_word_count': 50,
            'max_word_count': 2000,
            'readability_score': 0.7,
            'engagement_potential': 0.6
        }
        
        logger.info(f"RepurposeAgent {agent_id} инициализирован")
    
    def can_handle_task(self, task: Task) -> bool:
        """
        Проверяет, может ли RepurposeAgent выполнить задачу
        НЕ обрабатывает задачи публикации (с 'Publish' в названии) и задачи с изображениями
        """
        # Сначала проверяем базовые условия
        if not super().can_handle_task(task):
            return False
        
        # RepurposeAgent НЕ обрабатывает задачи публикации
        if "Publish" in task.name or "publish" in task.name.lower():
            return False
        
        # RepurposeAgent НЕ обрабатывает задачи генерации/поиска изображений
        # Это должны делать MultimediaProducerAgent
        image_related_keywords = ["Image", "image", "stock", "Stock", "Generate", "generate", "multimedia"]
        if any(keyword in task.name for keyword in image_related_keywords):
            return False  # MultimediaProducerAgent должен обрабатывать
        
        # Также проверяем контекст задачи
        if task.context.get("content_type") in ["post_image", "image"] or task.context.get("image_source"):
            return False  # MultimediaProducerAgent должен обрабатывать
        
        return True
    
    def _load_adaptation_templates(self) -> Dict[ContentFormat, Dict[str, Any]]:
        """Загружает шаблоны адаптации для разных форматов"""
        return {
            ContentFormat.TELEGRAM_POST: {
                "max_length": 4096,
                "structure": "hook + main_content + cta",
                "tone": "conversational",
                "hashtags": 3,
                "formatting": ["bold", "italic", "links"]
            },
            ContentFormat.TWITTER_THREAD: {
                "max_length": 280,
                "structure": "thread_intro + points + conclusion",
                "tone": "engaging",
                "hashtags": 2,
                "formatting": ["thread_numbering", "mentions"]
            },
            ContentFormat.INSTAGRAM_CAROUSEL: {
                "max_length": 2200,
                "structure": "hook + slides + cta",
                "tone": "visual_storytelling",
                "hashtags": 30,
                "formatting": ["line_breaks", "emojis"]
            },
            ContentFormat.INSTAGRAM_STORY: {
                "max_length": 100,
                "structure": "quick_hook + value + swipe_up",
                "tone": "casual",
                "hashtags": 5,
                "formatting": ["stories_text", "polls", "questions"]
            },
            ContentFormat.LINKEDIN_ARTICLE: {
                "max_length": 3000,
                "structure": "headline + intro + body + conclusion",
                "tone": "professional",
                "hashtags": 5,
                "formatting": ["headings", "bullet_points", "calls_to_action"]
            },
            ContentFormat.YOUTUBE_SHORTS: {
                "max_length": 500,
                "structure": "hook + value + subscribe",
                "tone": "energetic",
                "hashtags": 3,
                "formatting": ["timestamps", "subscribe_reminder"]
            },
            ContentFormat.TIKTOK_VIDEO: {
                "max_length": 300,
                "structure": "trending_hook + content + follow",
                "tone": "trendy",
                "hashtags": 5,
                "formatting": ["trending_sounds", "effects"]
            },
            ContentFormat.PODCAST_SCRIPT: {
                "max_length": 2000,
                "structure": "intro + segments + outro",
                "tone": "conversational",
                "hashtags": 0,
                "formatting": ["speaker_notes", "timing"]
            },
            ContentFormat.BLOG_POST: {
                "max_length": 2500,
                "structure": "title + intro + sections + conclusion",
                "tone": "informative",
                "hashtags": 10,
                "formatting": ["headings", "subheadings", "links"]
            },
            ContentFormat.NEWSLETTER: {
                "max_length": 1500,
                "structure": "subject + preview + content + footer",
                "tone": "personal",
                "hashtags": 0,
                "formatting": ["personal_greeting", "unsubscribe"]
            },
            ContentFormat.PRESENTATION: {
                "max_length": 1000,
                "structure": "title + agenda + slides + conclusion",
                "tone": "presentation",
                "hashtags": 0,
                "formatting": ["slide_titles", "bullet_points"]
            },
            ContentFormat.INFOGRAPHIC: {
                "max_length": 200,
                "structure": "title + key_points + visual_elements",
                "tone": "visual",
                "hashtags": 5,
                "formatting": ["statistics", "icons", "charts"]
            }
        }
    
    def _load_platform_guidelines(self) -> Dict[ContentFormat, PlatformGuidelines]:
        """Загружает руководящие принципы для платформ"""
        return {
            ContentFormat.TELEGRAM_POST: PlatformGuidelines(
                max_length=4096,
                min_length=100,
                preferred_tone="conversational",
                hashtag_limit=5,
                mention_style="@username",
                call_to_action_required=True,
                visual_elements=["images", "videos", "polls"],
                formatting_rules=["Use markdown", "Bold for emphasis", "Links for references"]
            ),
            ContentFormat.TWITTER_THREAD: PlatformGuidelines(
                max_length=280,
                min_length=50,
                preferred_tone="engaging",
                hashtag_limit=3,
                mention_style="@username",
                call_to_action_required=True,
                visual_elements=["images", "videos", "polls"],
                formatting_rules=["Number threads", "Use line breaks", "Engage with questions"]
            ),
            ContentFormat.INSTAGRAM_CAROUSEL: PlatformGuidelines(
                max_length=2200,
                min_length=200,
                preferred_tone="visual_storytelling",
                hashtag_limit=30,
                mention_style="@username",
                call_to_action_required=True,
                visual_elements=["carousel_images", "stories", "reels"],
                formatting_rules=["Use emojis", "Line breaks for readability", "Hashtags at end"]
            ),
            ContentFormat.INSTAGRAM_STORY: PlatformGuidelines(
                max_length=100,
                min_length=20,
                preferred_tone="casual",
                hashtag_limit=5,
                mention_style="@username",
                call_to_action_required=True,
                visual_elements=["stories", "polls", "questions", "swipe_up"],
                formatting_rules=["Short and punchy", "Use story features", "Engage with stickers"]
            ),
            ContentFormat.LINKEDIN_ARTICLE: PlatformGuidelines(
                max_length=3000,
                min_length=500,
                preferred_tone="professional",
                hashtag_limit=5,
                mention_style="@username",
                call_to_action_required=True,
                visual_elements=["images", "videos", "documents"],
                formatting_rules=["Professional tone", "Use headings", "Include insights"]
            ),
            ContentFormat.YOUTUBE_SHORTS: PlatformGuidelines(
                max_length=500,
                min_length=100,
                preferred_tone="energetic",
                hashtag_limit=3,
                mention_style="@channel",
                call_to_action_required=True,
                visual_elements=["shorts_video", "thumbnails", "end_screens"],
                formatting_rules=["Hook in first 3 seconds", "Subscribe reminder", "Trending topics"]
            ),
            ContentFormat.TIKTOK_VIDEO: PlatformGuidelines(
                max_length=300,
                min_length=50,
                preferred_tone="trendy",
                hashtag_limit=5,
                mention_style="@username",
                call_to_action_required=True,
                visual_elements=["trending_sounds", "effects", "filters"],
                formatting_rules=["Follow trends", "Use trending sounds", "Engage with comments"]
            ),
            ContentFormat.PODCAST_SCRIPT: PlatformGuidelines(
                max_length=2000,
                min_length=500,
                preferred_tone="conversational",
                hashtag_limit=0,
                mention_style="natural",
                call_to_action_required=True,
                visual_elements=["intro_music", "outro_music", "ad_breaks"],
                formatting_rules=["Natural speech", "Include timing", "Speaker notes"]
            ),
            ContentFormat.BLOG_POST: PlatformGuidelines(
                max_length=2500,
                min_length=800,
                preferred_tone="informative",
                hashtag_limit=10,
                mention_style="natural",
                call_to_action_required=True,
                visual_elements=["featured_images", "infographics", "videos"],
                formatting_rules=["SEO optimized", "Use headings", "Include links"]
            ),
            ContentFormat.NEWSLETTER: PlatformGuidelines(
                max_length=1500,
                min_length=300,
                preferred_tone="personal",
                hashtag_limit=0,
                mention_style="natural",
                call_to_action_required=True,
                visual_elements=["images", "gifs", "buttons"],
                formatting_rules=["Personal greeting", "Unsubscribe link", "Mobile friendly"]
            ),
            ContentFormat.PRESENTATION: PlatformGuidelines(
                max_length=1000,
                min_length=200,
                preferred_tone="presentation",
                hashtag_limit=0,
                mention_style="natural",
                call_to_action_required=True,
                visual_elements=["slides", "charts", "diagrams"],
                formatting_rules=["Clear structure", "Visual elements", "Speaker notes"]
            ),
            ContentFormat.INFOGRAPHIC: PlatformGuidelines(
                max_length=200,
                min_length=50,
                preferred_tone="visual",
                hashtag_limit=5,
                mention_style="@username",
                call_to_action_required=True,
                visual_elements=["charts", "icons", "statistics"],
                formatting_rules=["Visual focus", "Key statistics", "Clear data"]
            )
        }
    
    def _load_content_analyzers(self) -> Dict[ContentType, Dict[str, Any]]:
        """Загружает анализаторы для разных типов контента"""
        return {
            ContentType.LONG_ARTICLE: {
                "extract_method": "key_points_extraction",
                "structure_analysis": True,
                "summary_generation": True,
                "quote_extraction": True
            },
            ContentType.VIDEO_SCRIPT: {
                "extract_method": "scene_analysis",
                "structure_analysis": True,
                "summary_generation": True,
                "quote_extraction": True
            },
            ContentType.PODCAST_EPISODE: {
                "extract_method": "transcript_analysis",
                "structure_analysis": True,
                "summary_generation": True,
                "quote_extraction": True
            },
            ContentType.PRESENTATION_SLIDES: {
                "extract_method": "slide_analysis",
                "structure_analysis": True,
                "summary_generation": True,
                "quote_extraction": False
            },
            ContentType.SOCIAL_MEDIA_POST: {
                "extract_method": "post_analysis",
                "structure_analysis": False,
                "summary_generation": False,
                "quote_extraction": True
            },
            ContentType.NEWSLETTER_CONTENT: {
                "extract_method": "section_analysis",
                "structure_analysis": True,
                "summary_generation": True,
                "quote_extraction": True
            },
            ContentType.BLOG_POST: {
                "extract_method": "paragraph_analysis",
                "structure_analysis": True,
                "summary_generation": True,
                "quote_extraction": True
            },
            ContentType.INTERVIEW_TRANSCRIPT: {
                "extract_method": "qa_analysis",
                "structure_analysis": True,
                "summary_generation": True,
                "quote_extraction": True
            }
        }
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу по адаптации контента"""
        try:
            self.status = AgentStatus.BUSY
            self.last_activity = datetime.now()
            
            task_data = task.context
            source_content = task_data.get("content", "")
            source_format = task_data.get("source_format", "long_article")
            target_formats = task_data.get("target_formats", [])
            content_id = task_data.get("content_id", task.id)
            
            # Проверяем кэш
            cache_key = f"{content_id}_{hash(source_content)}_{'-'.join(target_formats)}"
            if cache_key in self.repurpose_cache:
                cached_result = self.repurpose_cache[cache_key]
                if datetime.now() - cached_result['timestamp'] < self.cache_ttl:
                    logger.info(f"Используем кэшированный результат для {content_id}")
                    return cached_result['result']
            
            # Выполняем адаптацию контента
            result = await self._repurpose_content(
                source_content, source_format, target_formats, content_id
            )
            
            # Сохраняем в кэш
            self.repurpose_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            
            # Обновляем статистику
            self._update_adaptation_stats(result)
            
            self.status = AgentStatus.IDLE
            self.completed_tasks.append(task.id)
            
            logger.info(f"Адаптация контента завершена для {content_id}. Создано {result['total_pieces']} форматов")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при адаптации контента: {e}")
            self.status = AgentStatus.ERROR
            self.error_count += 1
            raise
    
    async def _repurpose_content(self, source_content: str, source_format: str, target_formats: List[str], content_id: str) -> Dict[str, Any]:
        """Адаптирует контент под разные форматы"""
        start_time = datetime.now()
        
        # Анализируем исходный контент
        content_analysis = await self._analyze_source_content(source_content, source_format)
        
        # Определяем стратегию адаптации
        adaptation_strategy = self._determine_adaptation_strategy(source_format, target_formats)
        
        # Создаем адаптированные версии
        adapted_pieces = []
        successful_adaptations = 0
        
        for target_format_str in target_formats:
            try:
                target_format = ContentFormat(target_format_str)
                adapted_piece = await self._adapt_to_format(
                    source_content, content_analysis, target_format, adaptation_strategy
                )
                if adapted_piece:
                    adapted_pieces.append(adapted_piece)
                    successful_adaptations += 1
            except Exception as e:
                logger.warning(f"Ошибка адаптации в формат {target_format_str}: {e}")
        
        # Вычисляем время обработки
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Вычисляем успешность
        success_rate = successful_adaptations / len(target_formats) if target_formats else 0
        
        result = {
            "source_content_id": content_id,
            "source_format": source_format,
            "adapted_pieces": [
                {
                    "content_id": piece.content_id,
                    "format": piece.format.value,
                    "title": piece.title,
                    "content": piece.content,
                    "metadata": piece.metadata,
                    "word_count": piece.word_count,
                    "character_count": piece.character_count,
                    "hashtags": piece.hashtags,
                    "mentions": piece.mentions,
                    "call_to_action": piece.call_to_action
                }
                for piece in adapted_pieces
            ],
            "adaptation_strategy": adaptation_strategy.value,
            "success_rate": success_rate,
            "total_pieces": len(adapted_pieces),
            "processing_time": processing_time,
            "generated_at": datetime.now().isoformat()
        }
        
        return result
    
    async def _analyze_source_content(self, content: str, source_format: str) -> Dict[str, Any]:
        """Анализирует исходный контент"""
        # Извлекаем ключевые точки
        key_points = self._extract_key_points(content)
        
        # Анализируем структуру
        structure = self._analyze_content_structure(content)
        
        # Извлекаем цитаты
        quotes = self._extract_quotes(content)
        
        # Определяем тон
        tone = self._analyze_tone(content)
        
        # Извлекаем статистику
        stats = self._extract_statistics(content)
        
        return {
            "key_points": key_points,
            "structure": structure,
            "quotes": quotes,
            "tone": tone,
            "statistics": stats,
            "word_count": len(content.split()),
            "character_count": len(content)
        }
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Извлекает ключевые точки из контента"""
        # Простое извлечение ключевых точек по абзацам
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        key_points = []
        
        for paragraph in paragraphs:
            if len(paragraph) > 50:  # Игнорируем слишком короткие абзацы
                # Берем первое предложение как ключевую точку
                sentences = paragraph.split('. ')
                if sentences:
                    key_point = sentences[0].strip()
                    if key_point and not key_point.endswith('.'):
                        key_point += '.'
                    key_points.append(key_point)
        
        return key_points[:10]  # Ограничиваем 10 ключевыми точками
    
    def _analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Анализирует структуру контента"""
        # Подсчитываем заголовки
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        
        # Подсчитываем абзацы
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Подсчитываем списки
        lists = re.findall(r'^[\*\-\+]\s+(.+)$', content, re.MULTILINE)
        
        return {
            "headings": headings,
            "paragraphs_count": len(paragraphs),
            "lists_count": len(lists),
            "has_intro": len(paragraphs) > 0,
            "has_conclusion": len(paragraphs) > 2
        }
    
    def _extract_quotes(self, content: str) -> List[str]:
        """Извлекает цитаты из контента"""
        # Ищем текст в кавычках
        quotes = re.findall(r'"([^"]+)"', content)
        
        # Ищем выделенный текст
        bold_text = re.findall(r'\*\*([^*]+)\*\*', content)
        
        # Объединяем и ограничиваем
        all_quotes = quotes + bold_text
        return all_quotes[:5]  # Ограничиваем 5 цитатами
    
    def _analyze_tone(self, content: str) -> str:
        """Анализирует тон контента"""
        # Простой анализ тона по ключевым словам
        professional_words = ['анализ', 'исследование', 'данные', 'результаты', 'методология']
        casual_words = ['круто', 'классно', 'вау', 'супер', 'отлично']
        technical_words = ['алгоритм', 'система', 'технология', 'процесс', 'функция']
        
        content_lower = content.lower()
        
        professional_count = sum(1 for word in professional_words if word in content_lower)
        casual_count = sum(1 for word in casual_words if word in content_lower)
        technical_count = sum(1 for word in technical_words if word in content_lower)
        
        if professional_count > casual_count and professional_count > technical_count:
            return "professional"
        elif casual_count > professional_count and casual_count > technical_count:
            return "casual"
        elif technical_count > professional_count and technical_count > casual_count:
            return "technical"
        else:
            return "neutral"
    
    def _extract_statistics(self, content: str) -> List[str]:
        """Извлекает статистику из контента"""
        # Ищем числа с процентами
        percentages = re.findall(r'(\d+(?:\.\d+)?%)', content)
        
        # Ищем числа с единицами измерения
        numbers_with_units = re.findall(r'(\d+(?:\.\d+)?\s*(?:тыс|млн|млрд|руб|долл|евро|кг|г|м|км))', content)
        
        # Ищем простые числа
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', content)
        
        return percentages + numbers_with_units + numbers[:5]  # Ограничиваем 10 статистиками
    
    def _determine_adaptation_strategy(self, source_format: str, target_formats: List[str]) -> AdaptationStrategy:
        """Определяет стратегию адаптации"""
        # Простая логика определения стратегии
        if len(target_formats) > 5:
            return AdaptationStrategy.EXTRACT_KEY_POINTS
        elif any('thread' in fmt for fmt in target_formats):
            return AdaptationStrategy.RESTRUCTURE
        elif any('story' in fmt for fmt in target_formats):
            return AdaptationStrategy.SUMMARIZE
        elif any('infographic' in fmt for fmt in target_formats):
            return AdaptationStrategy.VISUALIZE
        else:
            return AdaptationStrategy.EXTRACT_KEY_POINTS
    
    async def _adapt_to_format(self, source_content: str, content_analysis: Dict[str, Any], target_format: ContentFormat, strategy: AdaptationStrategy) -> Optional[ContentPiece]:
        """Адаптирует контент под конкретный формат"""
        try:
            # Получаем шаблон для формата
            template = self.adaptation_templates.get(target_format, {})
            guidelines = self.platform_guidelines.get(target_format)
            
            if not template or not guidelines:
                logger.warning(f"Нет шаблона для формата {target_format}")
                return None
            
            # Адаптируем контент в зависимости от стратегии
            if strategy == AdaptationStrategy.EXTRACT_KEY_POINTS:
                adapted_content = self._extract_key_points_adaptation(source_content, content_analysis, template)
            elif strategy == AdaptationStrategy.SUMMARIZE:
                adapted_content = self._summarize_adaptation(source_content, content_analysis, template)
            elif strategy == AdaptationStrategy.EXPAND:
                adapted_content = self._expand_adaptation(source_content, content_analysis, template)
            elif strategy == AdaptationStrategy.RESTRUCTURE:
                adapted_content = self._restructure_adaptation(source_content, content_analysis, template)
            elif strategy == AdaptationStrategy.VISUALIZE:
                adapted_content = self._visualize_adaptation(source_content, content_analysis, template)
            else:
                adapted_content = self._conversational_adaptation(source_content, content_analysis, template)
            
            # Проверяем длину
            if len(adapted_content) > guidelines.max_length:
                adapted_content = adapted_content[:guidelines.max_length-3] + "..."
            elif len(adapted_content) < guidelines.min_length:
                adapted_content = self._expand_content(adapted_content, guidelines.min_length)
            
            # Создаем заголовок
            title = self._generate_title(content_analysis, target_format)
            
            # Извлекаем хештеги
            hashtags = self._generate_hashtags(content_analysis, guidelines.hashtag_limit)
            
            # Создаем призыв к действию
            call_to_action = self._generate_call_to_action(target_format)
            
            # Создаем метаданные
            metadata = {
                "strategy": strategy.value,
                "tone": content_analysis.get("tone", "neutral"),
                "word_count": len(adapted_content.split()),
                "character_count": len(adapted_content),
                "has_statistics": len(content_analysis.get("statistics", [])) > 0,
                "has_quotes": len(content_analysis.get("quotes", [])) > 0
            }
            
            return ContentPiece(
                content_id=f"{target_format.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                format=target_format,
                title=title,
                content=adapted_content,
                metadata=metadata,
                word_count=len(adapted_content.split()),
                character_count=len(adapted_content),
                hashtags=hashtags,
                mentions=[],
                call_to_action=call_to_action
            )
            
        except Exception as e:
            logger.error(f"Ошибка адаптации в формат {target_format}: {e}")
            return None
    
    def _extract_key_points_adaptation(self, content: str, analysis: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Адаптация через извлечение ключевых точек"""
        key_points = analysis.get("key_points", [])
        if not key_points:
            return content[:500] + "..." if len(content) > 500 else content
        
        # Берем первые 3-5 ключевых точек
        selected_points = key_points[:5]
        
        # Форматируем в зависимости от тона
        tone = analysis.get("tone", "neutral")
        if tone == "professional":
            formatted_content = "Ключевые моменты:\n\n" + "\n".join(f"• {point}" for point in selected_points)
        else:
            formatted_content = "Главное:\n\n" + "\n".join(f"🔥 {point}" for point in selected_points)
        
        return formatted_content
    
    def _summarize_adaptation(self, content: str, analysis: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Адаптация через суммирование"""
        # Берем первые и последние абзацы
        paragraphs = content.split('\n\n')
        if len(paragraphs) <= 2:
            return content
        
        intro = paragraphs[0]
        conclusion = paragraphs[-1] if len(paragraphs) > 1 else ""
        
        summary = intro
        if conclusion and conclusion != intro:
            summary += f"\n\n{conclusion}"
        
        return summary
    
    def _expand_adaptation(self, content: str, analysis: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Адаптация через расширение"""
        # Добавляем контекст и примеры
        expanded = content
        
        # Добавляем статистику если есть
        statistics = analysis.get("statistics", [])
        if statistics:
            expanded += f"\n\n📊 Статистика: {', '.join(statistics[:3])}"
        
        # Добавляем цитаты если есть
        quotes = analysis.get("quotes", [])
        if quotes:
            expanded += f"\n\n💬 Цитата: \"{quotes[0]}\""
        
        return expanded
    
    def _restructure_adaptation(self, content: str, analysis: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Адаптация через реструктуризацию"""
        key_points = analysis.get("key_points", [])
        if not key_points:
            return content
        
        # Создаем структурированный контент
        restructured = "🧵 Thread:\n\n"
        
        for i, point in enumerate(key_points[:5], 1):
            restructured += f"{i}/5 {point}\n\n"
        
        return restructured
    
    def _visualize_adaptation(self, content: str, analysis: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Адаптация для визуального формата"""
        key_points = analysis.get("key_points", [])
        statistics = analysis.get("statistics", [])
        
        visual_content = "📊 Инфографика:\n\n"
        
        if statistics:
            visual_content += f"📈 {statistics[0]}\n"
        
        if key_points:
            visual_content += f"💡 {key_points[0]}\n"
        
        if len(key_points) > 1:
            visual_content += f"🔍 {key_points[1]}\n"
        
        return visual_content
    
    def _conversational_adaptation(self, content: str, analysis: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Адаптация в разговорный стиль"""
        key_points = analysis.get("key_points", [])
        if not key_points:
            return content
        
        conversational = "Привет! 👋\n\n"
        conversational += f"Хочу поделиться с тобой: {key_points[0]}\n\n"
        
        if len(key_points) > 1:
            conversational += f"А еще: {key_points[1]}\n\n"
        
        conversational += "Что думаешь? 💭"
        
        return conversational
    
    def _generate_title(self, analysis: Dict[str, Any], target_format: ContentFormat) -> str:
        """Генерирует заголовок для формата"""
        key_points = analysis.get("key_points", [])
        
        if key_points:
            # Берем первое предложение как основу для заголовка
            first_point = key_points[0]
            # Убираем знаки препинания в конце
            title = first_point.rstrip('.,!?')
            # Ограничиваем длину
            if len(title) > 60:
                title = title[:57] + "..."
            return title
        
        return f"Контент для {target_format.value}"
    
    def _generate_hashtags(self, analysis: Dict[str, Any], limit: int) -> List[str]:
        """Генерирует хештеги"""
        # Простые хештеги на основе анализа
        hashtags = []
        
        tone = analysis.get("tone", "neutral")
        if tone == "professional":
            hashtags.extend(["#бизнес", "#анализ", "#инсайты"])
        elif tone == "technical":
            hashtags.extend(["#технологии", "#разработка", "#инновации"])
        elif tone == "casual":
            hashtags.extend(["#лайфхак", "#советы", "#мотивация"])
        
        # Добавляем общие хештеги
        hashtags.extend(["#контент", "#полезное"])
        
        return hashtags[:limit]
    
    def _generate_call_to_action(self, target_format: ContentFormat) -> str:
        """Генерирует призыв к действию"""
        cta_templates = {
            ContentFormat.TELEGRAM_POST: "Что думаешь? Пиши в комментариях! 💬",
            ContentFormat.TWITTER_THREAD: "Согласен? Ретвитни если полезно! 🔄",
            ContentFormat.INSTAGRAM_CAROUSEL: "Сохрани пост, чтобы не потерять! 💾",
            ContentFormat.INSTAGRAM_STORY: "Свайп вверх для подробностей! ⬆️",
            ContentFormat.LINKEDIN_ARTICLE: "Поделись своим мнением в комментариях! 💼",
            ContentFormat.YOUTUBE_SHORTS: "Подписывайся на канал! 🔔",
            ContentFormat.TIKTOK_VIDEO: "Ставь лайк и подписывайся! ❤️",
            ContentFormat.PODCAST_SCRIPT: "Слушай полный выпуск в подкасте! 🎧",
            ContentFormat.BLOG_POST: "Читай больше на нашем сайте! 🌐",
            ContentFormat.NEWSLETTER: "Подписывайся на рассылку! 📧",
            ContentFormat.PRESENTATION: "Скачивай презентацию! 📥",
            ContentFormat.INFOGRAPHIC: "Сохрани инфографику! 📊"
        }
        
        return cta_templates.get(target_format, "Поделись с друзьями! 👥")
    
    def _expand_content(self, content: str, min_length: int) -> str:
        """Расширяет контент до минимальной длины"""
        if len(content) >= min_length:
            return content
        
        # Добавляем дополнительные элементы
        expanded = content
        
        if len(expanded) < min_length:
            expanded += "\n\n💡 Полезный совет: сохрани этот пост, чтобы не потерять!"
        
        if len(expanded) < min_length:
            expanded += "\n\n🤔 Что думаешь об этом? Пиши в комментариях!"
        
        return expanded
    
    def _update_adaptation_stats(self, result: Dict[str, Any]):
        """Обновляет статистику адаптации"""
        self.adaptation_stats['total_adaptations'] += 1
        
        if result['success_rate'] > 0.8:
            self.adaptation_stats['successful_adaptations'] += 1
        else:
            self.adaptation_stats['failed_adaptations'] += 1
        
        # Обновляем статистику по форматам
        for piece in result['adapted_pieces']:
            format_name = piece['format']
            if format_name not in self.adaptation_stats['formats_created']:
                self.adaptation_stats['formats_created'][format_name] = 0
            self.adaptation_stats['formats_created'][format_name] += 1
        
        # Обновляем среднее время обработки
        current_avg = self.adaptation_stats['average_processing_time']
        total_adaptations = self.adaptation_stats['total_adaptations']
        new_time = result['processing_time']
        
        self.adaptation_stats['average_processing_time'] = (
            (current_avg * (total_adaptations - 1) + new_time) / total_adaptations
        )
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику адаптации"""
        return {
            "total_adaptations": self.adaptation_stats['total_adaptations'],
            "successful_adaptations": self.adaptation_stats['successful_adaptations'],
            "failed_adaptations": self.adaptation_stats['failed_adaptations'],
            "success_rate": (
                self.adaptation_stats['successful_adaptations'] / 
                self.adaptation_stats['total_adaptations'] * 100
                if self.adaptation_stats['total_adaptations'] > 0 else 0
            ),
            "formats_created": self.adaptation_stats['formats_created'],
            "average_processing_time": self.adaptation_stats['average_processing_time'],
            "cache_size": len(self.repurpose_cache),
            "last_activity": self.last_activity.isoformat()
        }
