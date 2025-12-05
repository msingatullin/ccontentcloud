"""
DraftingAgent - Писатель-верстальщик
Генерирует контент под разные платформы и форматы
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..orchestrator.agent_manager import BaseAgent, AgentCapability
from ..orchestrator.workflow_engine import Task, TaskType, TaskPriority
from ..models.content import ContentBrief, ContentPiece, Platform, ContentType, ContentStatus
from ..mcp.integrations.huggingface import HuggingFaceMCP
from ..mcp.integrations.openai import OpenAIMCP
from ..mcp.config import get_mcp_config, is_mcp_enabled

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class ContentTemplate:
    """Шаблон контента для платформы"""
    platform: str
    content_type: str
    structure: List[str]
    max_length: int
    required_elements: List[str]
    optional_elements: List[str]


@dataclass
class ContentPrompt:
    """Промпт для AI генерации контента"""
    platform: str
    content_type: str
    prompt_template: str
    max_tokens: int
    temperature: float
    system_message: str
    examples: List[str]


@dataclass
class GeneratedContent:
    """Сгенерированный контент"""
    content_piece: ContentPiece
    platform_optimized: bool
    seo_score: float
    engagement_potential: float
    readability_score: float


class DraftingAgent(BaseAgent):
    """Агент для создания и форматирования контента"""
    
    def __init__(self, agent_id: str = "drafting_agent"):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED, TaskType.REAL_TIME],
            max_concurrent_tasks=5,
            specializations=["content_creation", "copywriting", "seo", "formatting"],
            performance_score=1.1
        )
        super().__init__(agent_id, "Drafting Agent", capability)
        
        # Шаблоны контента для разных платформ
        self.content_templates = self._load_content_templates()
        self.platform_guidelines = self._load_platform_guidelines()
        self.tone_guides = self._load_tone_guides()
        
        # AI интеграции
        self.huggingface_mcp = None
        self.vertex_ai_mcp = None
        self.openai_mcp = None
        self.ai_prompts = self._load_ai_prompts()
        self._initialize_ai_integrations()
        
        logger.info(f"DraftingAgent {agent_id} инициализирован")
    
    def _load_content_templates(self) -> Dict[str, ContentTemplate]:
        """Загружает шаблоны контента для платформ"""
        return {
            "telegram_post": ContentTemplate(
                platform="telegram",
                content_type="post",
                structure=["hook", "main_content", "call_to_action"],
                max_length=500,
                required_elements=["hook", "main_content"],
                optional_elements=["hashtags", "call_to_action", "link"]
            ),
            "vk_post": ContentTemplate(
                platform="vk",
                content_type="post",
                structure=["hook", "main_content", "call_to_action"],
                max_length=300,
                required_elements=["hook", "main_content"],
                optional_elements=["hashtags", "call_to_action", "poll"]
            ),
            "instagram_post": ContentTemplate(
                platform="instagram",
                content_type="post",
                structure=["hook", "main_content", "hashtags"],
                max_length=150,
                required_elements=["hook", "main_content"],
                optional_elements=["hashtags", "call_to_action", "location"]
            ),
            "twitter_post": ContentTemplate(
                platform="twitter",
                content_type="post",
                structure=["hook", "main_content"],
                max_length=100,
                required_elements=["hook", "main_content"],
                optional_elements=["hashtags", "mention", "link"]
            ),
            "thread": ContentTemplate(
                platform="twitter",
                content_type="thread",
                structure=["intro_tweet", "main_tweets", "conclusion_tweet"],
                max_length=1000,
                required_elements=["intro_tweet", "main_tweets"],
                optional_elements=["hashtags", "call_to_action"]
            )
        }
    
    def _load_platform_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """Загружает гайдлайны для платформ"""
        return {
            "telegram": {
                "tone": "informal",
                "emoji_usage": "moderate",
                "hashtag_style": "minimal",
                "link_placement": "end",
                "call_to_action": "direct"
            },
            "vk": {
                "tone": "casual",
                "emoji_usage": "frequent",
                "hashtag_style": "moderate",
                "link_placement": "middle",
                "call_to_action": "engaging"
            },
            "instagram": {
                "tone": "inspirational",
                "emoji_usage": "frequent",
                "hashtag_style": "extensive",
                "link_placement": "bio",
                "call_to_action": "soft"
            },
            "twitter": {
                "tone": "conversational",
                "emoji_usage": "minimal",
                "hashtag_style": "strategic",
                "link_placement": "end",
                "call_to_action": "urgent"
            }
        }
    
    def _load_tone_guides(self) -> Dict[str, Dict[str, Any]]:
        """Загружает гайды по тону"""
        return {
            "professional": {
                "vocabulary": "formal",
                "sentence_structure": "complex",
                "emoji_usage": "none",
                "contractions": "avoid",
                "examples": ["Мы предлагаем", "Наша компания", "Профессиональные решения"]
            },
            "casual": {
                "vocabulary": "informal",
                "sentence_structure": "simple",
                "emoji_usage": "moderate",
                "contractions": "use",
                "examples": ["Привет!", "Круто!", "Давайте разберем"]
            },
            "friendly": {
                "vocabulary": "warm",
                "sentence_structure": "medium",
                "emoji_usage": "frequent",
                "contractions": "use",
                "examples": ["Друзья!", "Отлично!", "Поделимся секретом"]
            },
            "authoritative": {
                "vocabulary": "expert",
                "sentence_structure": "complex",
                "emoji_usage": "none",
                "contractions": "avoid",
                "examples": ["Исследования показывают", "Эксперты рекомендуют", "Доказано"]
            }
        }
    
    def _load_ai_prompts(self) -> Dict[str, ContentPrompt]:
        """Загружает промпты для AI генерации контента"""
        return {
            "telegram_post": ContentPrompt(
                platform="telegram",
                content_type="post",
                prompt_template="""Создай пост для Telegram на тему: {topic}

Пиши естественно, как автор, который видит проблему изнутри. Без официоза, без штампов, без "это реальность", "узнайте в статье", "инструменты помогают". Только живая мысль, настоящая польза и ощущение опыта.

{tone_profile_instruction}
{insights_instruction}

Структура:

1) Зацепка — наблюдение, честная мысль или неожиданный факт.

2) Суть — 2–3 предложения пользы: объяснение, пример, вывод.

3) Действие — одна строка без навязчивых продаж.

Правила:

- 1–2 эмодзи максимум.

- 250–450 символов.

- Пиши плотным языком, каждое предложение несёт смысл.

- Не используй сухие формулировки аналитики.

- Не дублируй тему или ключевые слова как явный список.

Теперь создай пост на тему: {topic}""",
                max_tokens=250,
                temperature=0.8,
                system_message="Ты автор, который пишет посты для Telegram. Видишь проблему изнутри, пишешь естественно, без официоза. Каждое предложение несёт смысл и пользу. Плотный, понятный, человеческий стиль.",
                examples=[
                    "Когда цена падает — новички паникуют, а опытные докупают. Почему? Потому что работают с вероятностями, а не эмоциями. Разбираем логику на примерах.",
                    "Большинство ошибок в инвестициях — это не про деньги, а про психологию. Страх упустить выгоду заставляет покупать на пике. Жадность не даёт продать вовремя.",
                    "Пассивный доход — это не про лень, а про систему. Пока вы спите, ваши активы работают. Но сначала нужно эту систему построить."
                ]
            ),
            "vk_post": ContentPrompt(
                platform="vk",
                content_type="post",
                prompt_template="""Создай пост для VK на тему: {topic}

Целевая аудитория: {target_audience}
Тон: {tone}
Ключевые слова: {keywords}

Требования:
- Живой, разговорный стиль
- Вопросы для вовлечения аудитории
- Релевантные хештеги
- Длина: до 300 символов
- НЕ добавляй блоки "Похожие события", "Similar events", исторические данные или события за последние годы

Структура:
1. Зацепка с вопросом
2. Основная информация
3. Призыв к обсуждению""",
                max_tokens=150,
                temperature=0.8,
                system_message="Ты создаешь контент для VK - социальной сети с живым общением. Пиши в разговорном стиле, задавай вопросы. НЕ добавляй блоки с похожими событиями, историческими данными или событиями за последние годы.",
                examples=[
                    "А что думаете об этом?",
                    "Кто-нибудь сталкивался с подобным?",
                    "Поделитесь опытом в комментариях!"
                ]
            ),
            "instagram_post": ContentPrompt(
                platform="instagram",
                content_type="post",
                prompt_template="""Создай пост для Instagram на тему: {topic}

Целевая аудитория: {target_audience}
Тон: {tone}
Ключевые слова: {keywords}

Требования:
- Визуально привлекательный текст
- Много эмодзи
- Хештеги для охвата
- Длина: до 150 символов
- НЕ добавляй блоки "Похожие события", "Similar events", исторические данные или события за последние годы

Структура:
1. Эмодзи + зацепка
2. Краткая информация
3. Хештеги""",
                max_tokens=100,
                temperature=0.9,
                system_message="Ты создаешь контент для Instagram - визуальной платформы. Используй эмодзи, создавай атмосферу. НЕ добавляй блоки с похожими событиями, историческими данными или событиями за последние годы.",
                examples=[
                    "✨ Вдохновение на каждый день",
                    "🌟 Новые возможности ждут",
                    "💫 Момент для изменений"
                ]
            ),
            "twitter_post": ContentPrompt(
                platform="twitter",
                content_type="post",
                prompt_template="""Создай твит на тему: {topic}

Целевая аудитория: {target_audience}
Тон: {tone}
Ключевые слова: {keywords}

Требования:
- Остроумно и лаконично
- Используй хештеги
- Длина: до 280 символов
- Можешь использовать тред
- НЕ добавляй блоки "Похожие события", "Similar events", исторические данные или события за последние годы

Структура:
1. Зацепка
2. Основная мысль
3. Хештеги""",
                max_tokens=100,
                temperature=0.8,
                system_message="Ты создаешь твиты - короткие, остроумные сообщения. Будь лаконичным и запоминающимся. НЕ добавляй блоки с похожими событиями, историческими данными или событиями за последние годы.",
                examples=[
                    "💡 Идея дня:",
                    "🔥 Горячая тема:",
                    "⚡ Быстрый факт:"
                ]
            )
        }
    
    def _initialize_ai_integrations(self):
        """Инициализирует AI интеграции"""
        try:
            # Инициализируем HuggingFaceMCP если доступен
            if is_mcp_enabled('huggingface'):
                self.huggingface_mcp = HuggingFaceMCP()
                logger.info("HuggingFaceMCP инициализирован в DraftingAgent")
            else:
                logger.warning("HuggingFaceMCP недоступен - будет использоваться fallback")
            
            # Инициализируем Vertex AI (приоритет) если доступен
            if is_mcp_enabled('vertex_ai'):
                from ..mcp.integrations.vertex_ai import VertexAIMCP
                self.vertex_ai_mcp = VertexAIMCP()
                logger.info("VertexAIMCP (Gemini) инициализирован в DraftingAgent")
            else:
                logger.warning("VertexAIMCP недоступен - будет использоваться fallback")
            
            # Инициализируем OpenAIMCP как fallback если доступен
            if is_mcp_enabled('openai'):
                self.openai_mcp = OpenAIMCP()
                logger.info("OpenAIMCP инициализирован в DraftingAgent (fallback)")
            else:
                logger.warning("OpenAIMCP недоступен - будет использоваться fallback")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации AI интеграций: {e}")
            self.huggingface_mcp = None
            self.vertex_ai_mcp = None
            self.openai_mcp = None
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу создания контента"""
        try:
            logger.info(f"DraftingAgent выполняет задачу: {task.name}")
            
            # Извлекаем данные из контекста задачи
            brief_data = task.context.get("brief_data", {})
            platform = task.context.get("platform", "telegram")
            content_type = task.context.get("content_type", "post")
            strategy_data = task.context.get("strategy", {})
            variants_count = task.context.get("variants_count", 1)  # Количество вариантов (по умолчанию 1)
            
            # Генерируем варианты контента
            variants = []
            for variant_num in range(1, variants_count + 1):
                logger.info(f"Генерация варианта {variant_num} из {variants_count}")
                
                # Создаем контент с небольшими вариациями для каждого варианта
                generated_content = await self._generate_content(
                    brief_data, platform, content_type, strategy_data, variant_num=variant_num
                )
                
                # Оптимизируем для платформы
                optimized_content = await self._optimize_for_platform(
                    generated_content, platform
                )
                
                # Проверяем качество
                quality_metrics = await self._assess_content_quality(optimized_content)
                
                variant_data = {
                    "variant_number": variant_num,
                    "content": {
                        "id": optimized_content.content_piece.id,
                        "title": optimized_content.content_piece.title,
                        "text": optimized_content.content_piece.text,
                        "hashtags": optimized_content.content_piece.hashtags,
                        "call_to_action": optimized_content.content_piece.call_to_action,
                        "platform": platform,
                        "content_type": content_type
                    },
                    "quality_metrics": {
                        "seo_score": optimized_content.seo_score,
                        "engagement_potential": optimized_content.engagement_potential,
                        "readability_score": optimized_content.readability_score,
                        "platform_optimized": optimized_content.platform_optimized
                    },
                    "recommendations": await self._generate_improvement_recommendations(
                        optimized_content, quality_metrics
                    )
                }
                variants.append(variant_data)
            
            # Если только один вариант - возвращаем старый формат для совместимости
            if variants_count == 1:
                result = {
                    "task_id": task.id,
                    "agent_id": self.agent_id,
                    "content": variants[0]["content"],
                    "quality_metrics": variants[0]["quality_metrics"],
                    "recommendations": variants[0]["recommendations"],
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Возвращаем все варианты
                result = {
                    "task_id": task.id,
                    "agent_id": self.agent_id,
                    "variants": variants,
                    "variants_count": len(variants),
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"DraftingAgent завершил задачу {task.id}, создано вариантов: {len(variants)}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в DraftingAgent: {e}")
            raise
    
    async def _generate_content(self, brief_data: Dict[str, Any], 
                              platform: str, content_type: str,
                              strategy_data: Dict[str, Any],
                              variant_num: int = 1) -> GeneratedContent:
        """Генерирует контент на основе брифа"""
        
        # Получаем шаблон для платформы
        template_key = f"{platform}_{content_type}"
        template = self.content_templates.get(template_key, 
                                            self.content_templates["telegram_post"])
        
        # Создаем контент-пис
        content_piece = ContentPiece(
            brief_id=brief_data.get("brief_id", ""),
            content_type=ContentType(content_type),
            platform=Platform(platform),
            title=brief_data.get("title", ""),
            status=ContentStatus.DRAFT,
            created_by_agent=self.agent_id
        )
        
        # Генерируем текст по шаблону
        text_parts = []
        
        # Hook (зацепка) - добавляем вариативность для разных вариантов
        if "hook" in template.required_elements:
            hook = await self._generate_hook(brief_data, strategy_data, platform, variant_num=variant_num)
            text_parts.append(hook)
        
        # Основной контент - добавляем вариативность для разных вариантов
        if "main_content" in template.required_elements:
            main_content = await self._generate_main_content(brief_data, strategy_data, platform, variant_num=variant_num)
            text_parts.append(main_content)
        
        # Call to action
        if "call_to_action" in template.optional_elements:
            cta = await self._generate_call_to_action(brief_data, platform)
            content_piece.call_to_action = cta
        
        # Объединяем части
        content_piece.text = "\n\n".join(text_parts)
        
        # Генерируем хештеги
        if "hashtags" in template.optional_elements:
            content_piece.hashtags = await self._generate_hashtags(brief_data, platform)
        
        # Ограничиваем длину
        if len(content_piece.text) > template.max_length:
            content_piece.text = await self._truncate_content(
                content_piece.text, template.max_length
            )
        
        return GeneratedContent(
            content_piece=content_piece,
            platform_optimized=False,  # Будет оптимизировано позже
            seo_score=0.0,  # Будет рассчитано позже
            engagement_potential=0.0,  # Будет рассчитано позже
            readability_score=0.0  # Будет рассчитано позже
        )
    
    async def _generate_hook(self, brief_data: Dict[str, Any],
                           strategy_data: Dict[str, Any], platform: str, variant_num: int = 1) -> str:
        """Генерирует зацепку для контента"""
        tone = brief_data.get("tone", "professional")
        target_audience = brief_data.get("target_audience", "")
        title = brief_data.get("title", "")
        description = brief_data.get("description", "")
        keywords = brief_data.get("keywords", [])

        # Извлекаем КОРОТКУЮ тему из title или keywords
        # НЕ используем полное предложение!
        topic = None

        # Если есть keywords - используем первый
        if keywords and len(keywords) > 0:
            topic = keywords[0].lower()
        # Иначе пытаемся извлечь тему из title (первые 2-3 слова)
        elif title:
            # Берём только первые несколько слов из title
            words = title.split()
            if len(words) <= 3:
                topic = title.lower()
            else:
                # Ищем ключевые существительные
                for word in words:
                    word_lower = word.lower().strip(',.!?')
                    if len(word_lower) > 4 and word_lower not in ['канал', 'предлагая', 'посвящен']:
                        topic = word_lower
                        break

        # Fallback на общую тему
        if not topic:
            topic = "эту тему"

        # Простые, универсальные зацепки
        hook_templates = {
            "professional": [
                f"Разбираем тему: {topic}",
                f"Важно знать про {topic}",
                f"Коротко о главном: {topic}"
            ],
            "casual": [
                f"Поговорим про {topic}?",
                f"Что нужно знать про {topic}",
                f"Разбираемся с {topic}"
            ],
            "benefit": [
                f"Как использовать {topic} для роста",
                f"Польза от {topic}",
                f"Что даёт {topic}"
            ]
        }

        # Выбираем тип зацепки
        template_key = tone if tone in hook_templates else "professional"

        import random
        hook = random.choice(hook_templates[template_key])

        # Добавляем эмодзи в зависимости от платформы
        platform_guidelines = self.platform_guidelines.get(platform, {})
        if platform_guidelines.get("emoji_usage") == "frequent":
            hook = f"🚀 {hook}"
        elif platform_guidelines.get("emoji_usage") == "moderate":
            hook = f"💡 {hook}"
        
        return hook
    
    async def _generate_main_content(self, brief_data: Dict[str, Any],
                                   strategy_data: Dict[str, Any], platform: str, variant_num: int = 1) -> str:
        """Генерирует основной контент через AI или fallback на шаблоны"""
        logger.info(f"🤖 Попытка AI генерации контента для {platform}, вариант {variant_num}")

        try:
            # Пытаемся использовать AI генерацию
            ai_content = await self._generate_content_with_ai(brief_data, strategy_data, platform, variant_num=variant_num)
            if ai_content:
                logger.info(f"✅ Основной контент сгенерирован через AI для {platform}: {ai_content[:100]}...")
                return ai_content
            else:
                logger.warning(f"⚠️ AI вернул пустой контент, используем fallback")
        except Exception as e:
            logger.error(f"❌ Ошибка AI генерации, используем fallback: {e}", exc_info=True)

        # Fallback на шаблонную генерацию
        logger.warning(f"⚠️ Используем FALLBACK генерацию вместо AI")
        return await self._generate_main_content_fallback(brief_data, strategy_data, platform, variant_num=variant_num)
    
    def _clean_generated_text(self, text: str) -> str:
        """Очищает сгенерированный текст от мусора, markdown и лишних символов"""
        if not text:
            return ""
        
        # Удаляем markdown разметку
        text = re.sub(r'#+\s*', '', text)  # Заголовки
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Жирный текст
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Курсив
        text = re.sub(r'`(.*?)`', r'\1', text)  # Код
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Ссылки
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Изображения
        
        # Удаляем мусор (строки с непонятными символами)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Пропускаем пустые строки
            if not line:
                continue
            # Пропускаем строки с мусором (много повторяющихся символов)
            if len(line) > 5 and len(set(line)) < 3:
                continue
            # Пропускаем строки только с символами без букв (кроме эмодзи)
            if not re.search(r'[а-яА-Яa-zA-Z]', line) and not re.search(r'[\U0001F300-\U0001F9FF]', line):
                continue
            # Пропускаем строки с техническими метаданными
            if any(meta in line.lower() for meta in ['subscription', 'подписк', 'business_goals', 'creating_posts']):
                continue
            cleaned_lines.append(line)
        
        # Объединяем обратно
        text = '\n'.join(cleaned_lines).strip()
        
        # Удаляем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)  # Множественные переносы
        
        return text.strip()
    
    async def _generate_content_with_ai(self, brief_data: Dict[str, Any], 
                                      strategy_data: Dict[str, Any], platform: str, variant_num: int = 1) -> Optional[str]:
        """Генерирует контент через AI модели"""
        try:
            # Получаем промпт для платформы
            prompt_key = f"{platform}_post"
            prompt = self.ai_prompts.get(prompt_key)
            
            if not prompt:
                logger.warning(f"Промпт для {platform} не найден")
                return None
            
            # Подготавливаем данные для промпта
            # ВАЖНО: используем title как основную тему, description только как fallback
            topic = brief_data.get("title", "").strip()
            
            # Если title пустой или слишком короткий, пытаемся извлечь тему из description
            if not topic or len(topic) < 3:
                description = brief_data.get("description", "").strip()
                if description:
                    # Очищаем description от инструкций типа "Напиши пост на тему..."
                    description_clean = description
                    # Удаляем инструкции
                    description_clean = re.sub(r'Напиши пост на тему\s*["\']?([^"\']+)["\']?', r'\1', description_clean, flags=re.IGNORECASE)
                    description_clean = re.sub(r'Создай пост про\s*', '', description_clean, flags=re.IGNORECASE)
                    description_clean = re.sub(r'Цель:\s*[^.]*\.?', '', description_clean, flags=re.IGNORECASE)
                    description_clean = re.sub(r'Напиши пост\s*', '', description_clean, flags=re.IGNORECASE)
                    # Берем первую часть до точки или запятой
                    topic = description_clean.split('.')[0].split(',')[0].strip()
                    # Если слишком длинное, берем первые слова
                    if len(topic) > 100:
                        topic = ' '.join(topic.split()[:10])
            
            # Если все еще пусто - используем дефолт
            if not topic or len(topic.strip()) < 3:
                topic = "контент"
            
            logger.info(f"🎯 Генерируем контент по теме: '{topic}'")
            logger.info(f"📋 Исходные данные: title='{brief_data.get('title', '')}', description='{brief_data.get('description', '')[:100]}...'")
            
            target_audience = brief_data.get("target_audience", "пользователи")
            tone = brief_data.get("tone", "professional")
            keywords = ", ".join(brief_data.get("keywords", []))
            
            # Извлекаем tone_profile (гибридный тон) если есть
            tone_profile = brief_data.get("tone_profile", {})
            tone_profile_instruction = ""
            if tone_profile and isinstance(tone_profile, dict):
                base = tone_profile.get("base", tone)
                flavor = tone_profile.get("flavor", "")
                rhythm = tone_profile.get("rhythm", "short")
                energy = tone_profile.get("energy", "medium")
                
                if base and flavor:
                    tone_profile_instruction = f"""
Используй tone_profile:
- base: {base} (основная тональность)
- flavor: {flavor} (дополнительный оттенок)
- rhythm: {rhythm} (ритм текста - для Telegram рекомендуется short/medium)
- energy: {energy} (энергия текста)

Создай пост, который сочетает {base} с оттенком {flavor}, ритмом {rhythm} и энергией {energy}.
"""
            
            # Извлекаем insights (инсайты из аналитики) если есть
            insights = brief_data.get("insights", [])
            insights_instruction = ""
            if insights and isinstance(insights, list) and len(insights) > 0:
                # Фильтруем пустые инсайты
                valid_insights = [insight for insight in insights[:4] if insight and isinstance(insight, str) and len(insight.strip()) > 0]
                if valid_insights:
                    insights_text = "\n".join([f"- {insight}" for insight in valid_insights])
                    insights_instruction = f"""
Используй эти инсайты для создания живого текста:
{insights_text}

Опирайся на эти наблюдения, но не копируй их дословно. Используй для создания естественной речи.
"""
            
            # Добавляем вариативность для разных вариантов
            variant_instruction = ""
            if variant_num > 1:
                variant_styles = [
                    "Создай более эмоциональный и живой вариант",
                    "Создай более структурированный и информативный вариант",
                    "Создай более креативный и нестандартный вариант"
                ]
                variant_instruction = f"\n\nВАЖНО: {variant_styles[min(variant_num - 1, len(variant_styles) - 1)]}. Вариант должен отличаться от предыдущих."
            
            # Формируем финальный промпт
            final_prompt = prompt.prompt_template.format(
                topic=topic,
                target_audience=target_audience,
                tone=tone,
                keywords=keywords,
                tone_profile_instruction=tone_profile_instruction,
                insights_instruction=insights_instruction
            ) + variant_instruction
            
            # ВАЖНО: Логируем финальный промпт для отладки
            logger.info(f"📝 Финальный промпт для AI (первые 500 символов): {final_prompt[:500]}...")
            
            # Увеличиваем temperature для большей вариативности при генерации нескольких вариантов
            adjusted_temperature = prompt.temperature + (variant_num - 1) * 0.1
            adjusted_temperature = min(adjusted_temperature, 1.0)  # Максимум 1.0
            
            # Приоритет 1: Vertex AI Gemini
            if hasattr(self, 'vertex_ai_mcp') and self.vertex_ai_mcp is not None:
                result = await self.vertex_ai_mcp.execute_with_retry(
                    'generate_content',
                    prompt=final_prompt,
                    max_tokens=prompt.max_tokens,
                    temperature=adjusted_temperature
                )
                
                if result.success and result.data:
                    generated_text = result.data.get('generated_text', '')
                    if generated_text:
                        # Очищаем текст от мусора и markdown
                        generated_text = self._clean_generated_text(generated_text)
                        return generated_text if generated_text else None
            
            # Приоритет 2: HuggingFace
            if self.huggingface_mcp is not None:
                result = await self.huggingface_mcp.execute_with_retry(
                    'generate_text',
                    prompt=final_prompt,
                    max_tokens=prompt.max_tokens,
                    temperature=adjusted_temperature
                )
                
                if result.success and result.data:
                    generated_text = result.data.get('generated_text', '')
                    if generated_text:
                        # Очищаем текст от мусора и markdown
                        generated_text = self._clean_generated_text(generated_text)
                        return generated_text if generated_text else None
            
            # Fallback на OpenAI если доступен
            if self.openai_mcp is not None:
                result = await self.openai_mcp.execute_with_retry(
                    'generate_content',
                    prompt=final_prompt,
                    max_tokens=prompt.max_tokens,
                    temperature=adjusted_temperature
                )
                
                if result.success and result.data:
                    generated_text = result.data.get('content', '')
                    if generated_text:
                        logger.info(f"✅ OpenAI сгенерировал текст (первые 200 символов): {generated_text[:200]}...")
                        # Очищаем текст от мусора и markdown
                        generated_text = self._clean_generated_text(generated_text)
                        logger.info(f"✅ После очистки (первые 200 символов): {generated_text[:200]}...")
                        return generated_text if generated_text else None
                    else:
                        logger.warning(f"⚠️ OpenAI вернул пустой content")
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка AI генерации контента: {e}")
            return None
    
    async def _generate_main_content_fallback(self, brief_data: Dict[str, Any],
                                            strategy_data: Dict[str, Any], platform: str, variant_num: int = 1) -> str:
        """Fallback метод для генерации основного контента (шаблонная логика)"""
        title = brief_data.get("title", "")
        description = brief_data.get("description", "")
        target_audience = brief_data.get("target_audience", "")
        keywords = brief_data.get("keywords", [])
        business_goals = brief_data.get("business_goals", [])

        logger.warning(f"⚠️ ИСПОЛЬЗУЕТСЯ FALLBACK ГЕНЕРАЦИЯ! AI не работает. Brief: title='{title}', keywords={keywords}")

        # Создаем основной контент БЕЗ технических фраз
        content_parts = []

        # 1. Основное описание (ТОЛЬКО суть, без "Пост о...")
        if description:
            # Берём первое предложение и очищаем от технических фраз
            sentences = description.split('.')
            if sentences:
                main_sentence = sentences[0].strip()
                # Убираем технические фразы
                main_sentence = main_sentence.replace("Канал посвящен", "Здесь вы найдёте информацию о")
                main_sentence = main_sentence.replace("предлагая", "—")
                content_parts.append(main_sentence + ".")

        # 2. Что получит читатель (на основе business_goals)
        if business_goals:
            # Маппинг технических целей на понятный язык
            goal_mapping = {
                "охват": "широкий охват",
                "вовлечение": "высокое вовлечение",
                "creating_posts": "создание полезного контента",
                "engagement": "взаимодействие с аудиторией",
                "growth": "рост канала",
                "sales": "увеличение продаж",
                "awareness": "узнаваемость бренда",
                "retention": "удержание аудитории"
            }

            readable_goals = []
            for goal in business_goals[:3]:
                readable = goal_mapping.get(goal.lower(), goal)
                readable_goals.append(readable)

            if readable_goals:
                if len(readable_goals) == 1:
                    content_parts.append(f"\nФокус на {readable_goals[0]}.")
                else:
                    content_parts.append(f"\nФокус: {', '.join(readable_goals)}.")

        # 3. Призыв или ценность для аудитории
        if keywords and len(keywords) > 0:
            # Используем keywords для описания ценности
            main_keyword = keywords[0].lower()
            content_parts.append(f"\nПолезная информация про {main_keyword}.")

        # Если контент всё ещё пустой - добавляем универсальную фразу
        if not content_parts:
            content_parts.append("Полезный контент для вас.")

        result = "\n".join(content_parts)
        logger.info(f"Fallback generated content: {result[:100]}...")
        return result
    
    async def _generate_call_to_action(self, brief_data: Dict[str, Any], platform: str) -> str:
        """Генерирует призыв к действию"""
        cta_data = brief_data.get("call_to_action", "")
        platform_guidelines = self.platform_guidelines.get(platform, {})

        # Обработка CTA: может быть строкой, списком или пустым
        cta_text = ""
        if isinstance(cta_data, list) and cta_data:
            # Если список - берём первый элемент и форматируем
            primary_cta = cta_data[0]

            # Маппинг типовых CTA на красивые фразы
            cta_mapping = {
                "подписаться на канал": "👉 Подписывайтесь на канал",
                "подписаться": "👉 Подписывайтесь на канал",
                "subscribe": "👉 Подписывайтесь на канал",
                "subscription": "👉 Подписывайтесь на канал",
                "подписка": "👉 Подписывайтесь на канал",
                "purchase": "🛒 Заказать",
                "купить": "🛒 Купить",
                "узнать больше": "ℹ️ Узнать больше",
                "learn more": "ℹ️ Узнать больше",
                "читать": "📖 Читать полностью",
                "регистрация": "✍️ Зарегистрироваться",
                "заявка на консультацию": "📞 Заявка на консультацию",
                "консультация": "📞 Заявка на консультацию"
            }

            # Ищем совпадение (case-insensitive)
            primary_cta_lower = primary_cta.lower().strip()
            
            # Специальная обработка для "subscription" и похожих
            if 'subscription' in primary_cta_lower or 'подписк' in primary_cta_lower:
                cta_text = "👉 Подписывайтесь на канал"
            elif primary_cta_lower in cta_mapping:
                cta_text = cta_mapping[primary_cta_lower]
            else:
                # Проверяем частичное совпадение
                for key, value in cta_mapping.items():
                    if key in primary_cta_lower:
                        cta_text = value
                        break
                if not cta_text:
                    cta_text = f"👉 {primary_cta}"

        elif isinstance(cta_data, str) and cta_data:
            cta_data_lower = cta_data.lower().strip()
            # Специальная обработка для "subscription"
            if 'subscription' in cta_data_lower or 'подписк' in cta_data_lower:
                cta_text = "👉 Подписывайтесь на канал"
            elif cta_data.startswith("👉") or cta_data.startswith("🛒"):
                cta_text = cta_data
            else:
                cta_text = f"👉 {cta_data}"

        if not cta_text:
            # Генерируем CTA по умолчанию в зависимости от платформы
            cta_style = platform_guidelines.get("call_to_action", "direct")

            if cta_style == "direct":
                cta_text = "👉 Подписывайтесь на наш канал"
            elif cta_style == "engaging":
                cta_text = "💬 Что думаете? Пишите в комментариях"
            elif cta_style == "soft":
                cta_text = "❤️ Понравилось? Сохраните пост"
            else:
                cta_text = "ℹ️ Узнать больше"

        return cta_text
    
    async def _generate_hashtags(self, brief_data: Dict[str, Any], platform: str) -> List[str]:
        """Генерирует хештеги (БЕЗ символа #, он будет добавлен при форматировании)"""
        keywords = brief_data.get("keywords", [])
        title = brief_data.get("title", "")
        description = brief_data.get("description", "")
        platform_guidelines = self.platform_guidelines.get(platform, {})
        hashtag_style = platform_guidelines.get("hashtag_style", "minimal")

        hashtags = []

        # Умная генерация хештегов на основе контекста контента
        # Определяем тематику по ключевым словам и описанию
        content_lower = (title + " " + description).lower()

        # Тематические категории хештегов
        topic_hashtags = {
            "инвест": ["инвестиции", "финансы", "фондовыйрынок"],
            "бизнес": ["бизнес", "предприниматель", "стартап"],
            "маркет": ["маркетинг", "smm", "реклама"],
            "технолог": ["технологии", "инновации", "it"],
            "AI": ["ai", "искусственныйинтеллект", "нейросети"],
            "крипто": ["крипто", "blockchain", "bitcoin"],
            "образован": ["образование", "обучение", "курсы"],
            "здоров": ["здоровье", "фитнес", "зож"]
        }

        # Находим подходящую тематику
        matched_topics = []
        for key, tags in topic_hashtags.items():
            if key in content_lower:
                matched_topics.extend(tags[:2])  # Берём первые 2 тега из категории

        # Добавляем хештеги из ключевых слов (без #)
        for keyword in keywords[:3]:  # Максимум 3 хештега из keywords
            # Убираем спецсимволы и пробелы
            clean_keyword = keyword.replace(' ', '_').replace('-', '_').lower()
            # Фильтруем слишком длинные или короткие
            if 3 <= len(clean_keyword) <= 30 and clean_keyword not in hashtags:
                hashtags.append(clean_keyword)

        # Добавляем тематические хештеги если нашли
        for topic_tag in matched_topics:
            if topic_tag not in hashtags:
                hashtags.append(topic_tag)

        # Если хештегов мало, добавляем универсальные
        if len(hashtags) < 2:
            universal_hashtags = {
                "telegram": ["полезно", "контент"],
                "vk": ["полезное", "интересное"],
                "instagram": ["instagood", "motivation"],
                "twitter": ["content", "useful"]
            }
            for tag in universal_hashtags.get(platform, ["контент", "полезно"]):
                if tag not in hashtags:
                    hashtags.append(tag)
                if len(hashtags) >= 3:
                    break

        # Ограничиваем количество в зависимости от стиля
        max_hashtags = 3 if hashtag_style == "minimal" else (5 if hashtag_style == "moderate" else 8)
        return hashtags[:max_hashtags]
    
    async def _truncate_content(self, content: str, max_length: int) -> str:
        """Обрезает контент до максимальной длины"""
        if len(content) <= max_length:
            return content
        
        # Обрезаем по предложениям
        sentences = content.split('. ')
        truncated = ""
        
        for sentence in sentences:
            if len(truncated + sentence + '. ') <= max_length:
                truncated += sentence + '. '
            else:
                break
        
        return truncated.strip()
    
    async def _optimize_for_platform(self, content: GeneratedContent, platform: str) -> GeneratedContent:
        """Оптимизирует контент для конкретной платформы"""
        platform_guidelines = self.platform_guidelines.get(platform, {})
        content_piece = content.content_piece
        
        # Оптимизируем тон
        tone = platform_guidelines.get("tone", "casual")
        if tone == "informal":
            content_piece.text = await self._make_informal(content_piece.text)
        elif tone == "inspirational":
            content_piece.text = await self._make_inspirational(content_piece.text)
        
        # Оптимизируем эмодзи
        emoji_usage = platform_guidelines.get("emoji_usage", "moderate")
        if emoji_usage == "frequent":
            content_piece.text = await self._add_emojis(content_piece.text, 3)
        elif emoji_usage == "minimal":
            content_piece.text = await self._remove_emojis(content_piece.text)
        
        # Оптимизируем хештеги
        hashtag_style = platform_guidelines.get("hashtag_style", "minimal")
        if hashtag_style == "minimal":
            content_piece.hashtags = content_piece.hashtags[:3]
        elif hashtag_style == "extensive":
            content_piece.hashtags.extend(["#viral", "#trending"])
        
        content.platform_optimized = True
        return content
    
    async def _make_informal(self, text: str) -> str:
        """Делает текст более неформальным"""
        replacements = {
            "мы предлагаем": "мы делаем",
            "наша компания": "мы",
            "профессиональные": "крутые",
            "решения": "фишки"
        }
        
        for formal, informal in replacements.items():
            text = text.replace(formal, informal)
        
        return text
    
    async def _make_inspirational(self, text: str) -> str:
        """Делает текст более вдохновляющим"""
        inspirational_words = ["вдохновляющий", "мотивирующий", "преображающий"]
        import random
        
        if "важно" in text:
            text = text.replace("важно", random.choice(inspirational_words))
        
        return text
    
    async def _add_emojis(self, text: str, count: int) -> str:
        """Добавляет эмодзи в текст"""
        emojis = ["✨", "🚀", "💡", "🎯", "🔥", "⭐", "💪", "🎉"]
        import random
        
        words = text.split()
        for _ in range(min(count, len(words) // 5)):
            if words:
                pos = random.randint(0, len(words) - 1)
                words.insert(pos, random.choice(emojis))
        
        return " ".join(words)
    
    async def _remove_emojis(self, text: str) -> str:
        """Удаляет эмодзи из текста"""
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                 u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                 "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    
    async def _assess_content_quality(self, content: GeneratedContent) -> Dict[str, float]:
        """Оценивает качество контента"""
        text = content.content_piece.text
        
        # SEO оценка
        seo_score = await self._calculate_seo_score(text, content.content_piece.hashtags)
        
        # Потенциал вовлеченности
        engagement_potential = await self._calculate_engagement_potential(text)
        
        # Читаемость
        readability_score = await self._calculate_readability_score(text)
        
        return {
            "seo_score": seo_score,
            "engagement_potential": engagement_potential,
            "readability_score": readability_score
        }
    
    async def _calculate_seo_score(self, text: str, hashtags: List[str]) -> float:
        """Рассчитывает SEO оценку"""
        score = 0.0
        
        # Длина текста
        if 100 <= len(text) <= 500:
            score += 0.3
        elif 50 <= len(text) < 100:
            score += 0.2
        
        # Наличие хештегов
        if hashtags:
            score += 0.2
        
        # Наличие ключевых слов
        keywords = ["решение", "проблема", "успех", "результат", "эффект"]
        for keyword in keywords:
            if keyword in text.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    async def _calculate_engagement_potential(self, text: str) -> float:
        """Рассчитывает потенциал вовлеченности"""
        score = 0.0
        
        # Вопросы
        if "?" in text:
            score += 0.3
        
        # Эмодзи
        emoji_count = len(re.findall(r'[^\w\s]', text))
        if emoji_count > 0:
            score += 0.2
        
        # Призывы к действию
        cta_words = ["подписывайтесь", "комментируйте", "делитесь", "сохраняйте"]
        for word in cta_words:
            if word in text.lower():
                score += 0.2
        
        # Эмоциональные слова
        emotional_words = ["круто", "отлично", "потрясающе", "невероятно"]
        for word in emotional_words:
            if word in text.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    async def _calculate_readability_score(self, text: str) -> float:
        """Рассчитывает оценку читаемости"""
        sentences = text.split('.')
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        # Средняя длина предложения
        avg_sentence_length = len(words) / len(sentences)
        
        # Оценка читаемости (простая формула)
        if avg_sentence_length <= 10:
            return 1.0
        elif avg_sentence_length <= 15:
            return 0.8
        elif avg_sentence_length <= 20:
            return 0.6
        else:
            return 0.4
    
    async def _generate_improvement_recommendations(self, content: GeneratedContent, 
                                                  quality_metrics: Dict[str, float]) -> List[str]:
        """Генерирует рекомендации по улучшению"""
        recommendations = []
        
        if quality_metrics["seo_score"] < 0.5:
            recommendations.append("Добавить больше ключевых слов и хештегов")
        
        if quality_metrics["engagement_potential"] < 0.5:
            recommendations.append("Добавить вопросы или призывы к действию")
        
        if quality_metrics["readability_score"] < 0.6:
            recommendations.append("Упростить предложения для лучшей читаемости")
        
        if not content.platform_optimized:
            recommendations.append("Оптимизировать контент для целевой платформы")
        
        if not recommendations:
            recommendations.append("Контент готов к публикации!")
        
        return recommendations
