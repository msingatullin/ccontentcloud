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
                prompt_template="""Создай пост для Telegram канала на тему: {topic}

Целевая аудитория: {target_audience}
Тон: {tone}
Ключевые слова: {keywords}

Требования:
- Захватывающая зацепка в начале
- Информативный основной контент
- Призыв к действию в конце
- Используй эмодзи для привлечения внимания
- Длина: до 500 символов
- НЕ добавляй блоки "Похожие события", "Similar events", исторические данные или события за последние годы

Структура:
1. Зацепка (1-2 предложения)
2. Основной контент (2-3 предложения)
3. Призыв к действию (1 предложение)""",
                max_tokens=200,
                temperature=0.7,
                system_message="Ты профессиональный копирайтер, специализирующийся на создании контента для социальных сетей. Создавай увлекательный и информативный контент. НЕ добавляй блоки с похожими событиями, историческими данными или событиями за последние годы.",
                examples=[
                    "🚀 Новые технологии меняют мир!",
                    "💡 Знаете ли вы, что...",
                    "🎯 Хотите узнать секрет успеха?"
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
            
            # Инициализируем OpenAIMCP если доступен
            if is_mcp_enabled('openai'):
                self.openai_mcp = OpenAIMCP()
                logger.info("OpenAIMCP инициализирован в DraftingAgent")
            else:
                logger.warning("OpenAIMCP недоступен - будет использоваться fallback")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации AI интеграций: {e}")
            self.huggingface_mcp = None
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
            
            # Создаем контент
            generated_content = await self._generate_content(
                brief_data, platform, content_type, strategy_data
            )
            
            # Оптимизируем для платформы
            optimized_content = await self._optimize_for_platform(
                generated_content, platform
            )
            
            # Проверяем качество
            quality_metrics = await self._assess_content_quality(optimized_content)
            
            result = {
                "task_id": task.id,
                "agent_id": self.agent_id,
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
                ),
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"DraftingAgent завершил задачу {task.id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в DraftingAgent: {e}")
            raise
    
    async def _generate_content(self, brief_data: Dict[str, Any], 
                              platform: str, content_type: str,
                              strategy_data: Dict[str, Any]) -> GeneratedContent:
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
        
        # Hook (зацепка)
        if "hook" in template.required_elements:
            hook = await self._generate_hook(brief_data, strategy_data, platform)
            text_parts.append(hook)
        
        # Основной контент
        if "main_content" in template.required_elements:
            main_content = await self._generate_main_content(brief_data, strategy_data, platform)
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
                           strategy_data: Dict[str, Any], platform: str) -> str:
        """Генерирует зацепку для контента"""
        tone = brief_data.get("tone", "professional")
        target_audience = brief_data.get("target_audience", "")
        keywords = brief_data.get("keywords", [])
        
        # Получаем гайд по тону
        tone_guide = self.tone_guides.get(tone, self.tone_guides["professional"])
        
        # Шаблоны зацепок
        hook_templates = {
            "question": [
                f"Знаете ли вы, что {keywords[0] if keywords else 'новые технологии'} могут...",
                f"Хотите узнать секрет {keywords[0] if keywords else 'успеха'}?",
                f"Почему {target_audience} выбирают именно это решение?"
            ],
            "statement": [
                f"Сегодня поговорим о {keywords[0] if keywords else 'важной теме'}",
                f"Открываем секреты {keywords[0] if keywords else 'эффективности'}",
                f"Новый подход к {keywords[0] if keywords else 'решению задач'}"
            ],
            "statistic": [
                f"90% {target_audience} не знают об этом",
                f"Всего 1 шаг до {keywords[0] if keywords else 'результата'}",
                f"Проверенный способ {keywords[0] if keywords else 'достижения цели'}"
            ]
        }
        
        # Выбираем тип зацепки в зависимости от тона
        if tone == "professional":
            hook_type = "statement"
        elif tone == "casual":
            hook_type = "question"
        else:
            hook_type = "statistic"
        
        import random
        hook = random.choice(hook_templates[hook_type])
        
        # Добавляем эмодзи в зависимости от платформы
        platform_guidelines = self.platform_guidelines.get(platform, {})
        if platform_guidelines.get("emoji_usage") == "frequent":
            hook = f"🚀 {hook}"
        elif platform_guidelines.get("emoji_usage") == "moderate":
            hook = f"💡 {hook}"
        
        return hook
    
    async def _generate_main_content(self, brief_data: Dict[str, Any], 
                                   strategy_data: Dict[str, Any], platform: str) -> str:
        """Генерирует основной контент через AI или fallback на шаблоны"""
        try:
            # Пытаемся использовать AI генерацию
            ai_content = await self._generate_content_with_ai(brief_data, strategy_data, platform)
            if ai_content:
                logger.info(f"Основной контент сгенерирован через AI для {platform}")
                return ai_content
        except Exception as e:
            logger.warning(f"Ошибка AI генерации, используем fallback: {e}")
        
        # Fallback на шаблонную генерацию
        return await self._generate_main_content_fallback(brief_data, strategy_data, platform)
    
    async def _generate_content_with_ai(self, brief_data: Dict[str, Any], 
                                      strategy_data: Dict[str, Any], platform: str) -> Optional[str]:
        """Генерирует контент через AI модели"""
        try:
            import os
            import openai
            
            # Проверяем наличие OpenAI API ключа
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY не установлен, используем fallback")
                return None
            
            # Получаем промпт для платформы
            prompt_key = f"{platform}_post"
            prompt = self.ai_prompts.get(prompt_key)
            
            if not prompt:
                logger.warning(f"Промпт для {platform} не найден")
                return None
            
            # Подготавливаем данные для промпта
            topic = brief_data.get("title", brief_data.get("description", "контент"))
            target_audience = brief_data.get("target_audience", "пользователи")
            tone = brief_data.get("tone", "professional")
            keywords = ", ".join(brief_data.get("keywords", []))
            
            # Формируем финальный промпт
            final_prompt = prompt.prompt_template.format(
                topic=topic,
                target_audience=target_audience,
                tone=tone,
                keywords=keywords
            )
            
            # Вызываем OpenAI API напрямую
            try:
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": prompt.system_message},
                        {"role": "user", "content": final_prompt}
                    ],
                    max_tokens=prompt.max_tokens,
                    temperature=prompt.temperature,
                    n=1
                )
                
                if response.choices and len(response.choices) > 0:
                    generated_text = response.choices[0].message.content.strip()
                    logger.info(f"✅ Контент успешно сгенерирован через OpenAI для {platform}")
                    return generated_text
                
            except openai.APIError as e:
                logger.error(f"OpenAI API Error: {e}")
                return None
            except openai.RateLimitError as e:
                logger.error(f"OpenAI Rate Limit: {e}")
                return None
            except Exception as e:
                logger.error(f"OpenAI Error: {e}")
                return None
            
            # Fallback на MCP интеграции если OpenAI не сработал
            if self.huggingface_mcp is not None:
                result = await self.huggingface_mcp.execute_with_retry(
                    'generate_text',
                    prompt=final_prompt,
                    max_tokens=prompt.max_tokens,
                    temperature=prompt.temperature
                )
                
                if result.success and result.data:
                    return result.data.get('generated_text', '')
            
            if self.openai_mcp is not None:
                result = await self.openai_mcp.execute_with_retry(
                    'generate_content',
                    prompt=final_prompt,
                    max_tokens=prompt.max_tokens,
                    temperature=prompt.temperature
                )
                
                if result.success and result.data:
                    return result.data.get('content', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка AI генерации контента: {e}")
            return None
    
    async def _generate_main_content_fallback(self, brief_data: Dict[str, Any], 
                                            strategy_data: Dict[str, Any], platform: str) -> str:
        """Fallback метод для генерации основного контента (шаблонная логика)"""
        description = brief_data.get("description", "")
        target_audience = brief_data.get("target_audience", "")
        tone = brief_data.get("tone", "professional")
        keywords = brief_data.get("keywords", [])
        
        # Получаем гайд по тону
        tone_guide = self.tone_guides.get(tone, self.tone_guides["professional"])
        
        # Создаем основной контент
        content_parts = []
        
        # Введение
        intro = f"Для {target_audience} важно понимать, что {description.lower()}"
        content_parts.append(intro)
        
        # Основные пункты
        if keywords:
            for keyword in keywords[:3]:  # Максимум 3 пункта
                point = f"• {keyword} - ключевой элемент успеха"
                content_parts.append(point)
        
        # Дополнительная информация
        if brief_data.get("business_goals"):
            goals_text = f"Наши цели: {', '.join(brief_data['business_goals'][:2])}"
            content_parts.append(goals_text)
        
        return "\n".join(content_parts)
    
    async def _generate_call_to_action(self, brief_data: Dict[str, Any], platform: str) -> str:
        """Генерирует призыв к действию"""
        cta_text = brief_data.get("call_to_action", "")
        platform_guidelines = self.platform_guidelines.get(platform, {})
        
        if not cta_text:
            # Генерируем CTA в зависимости от платформы
            cta_style = platform_guidelines.get("call_to_action", "direct")
            
            if cta_style == "direct":
                cta_text = "Подписывайтесь на наш канал!"
            elif cta_style == "engaging":
                cta_text = "Что думаете? Пишите в комментариях!"
            elif cta_style == "soft":
                cta_text = "Понравилось? Сохраните пост!"
            else:
                cta_text = "Узнать больше"
        
        return cta_text
    
    async def _generate_hashtags(self, brief_data: Dict[str, Any], platform: str) -> List[str]:
        """Генерирует хештеги"""
        keywords = brief_data.get("keywords", [])
        platform_guidelines = self.platform_guidelines.get(platform, {})
        hashtag_style = platform_guidelines.get("hashtag_style", "minimal")
        
        hashtags = []
        
        # Добавляем хештеги из ключевых слов
        for keyword in keywords[:5]:  # Максимум 5 хештегов
            hashtag = f"#{keyword.replace(' ', '_').lower()}"
            hashtags.append(hashtag)
        
        # Добавляем платформо-специфичные хештеги
        platform_hashtags = {
            "telegram": ["#новости", "#полезно"],
            "vk": ["#вконтакте", "#полезное"],
            "instagram": ["#instagood", "#lifestyle", "#motivation"],
            "twitter": ["#trending", "#news"]
        }
        
        if hashtag_style == "extensive":
            hashtags.extend(platform_hashtags.get(platform, [])[:3])
        elif hashtag_style == "moderate":
            hashtags.extend(platform_hashtags.get(platform, [])[:1])
        
        return hashtags[:10]  # Максимум 10 хештегов
    
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
        content.seo_score = seo_score
        
        # Потенциал вовлеченности
        engagement_potential = await self._calculate_engagement_potential(text)
        content.engagement_potential = engagement_potential
        
        # Читаемость
        readability_score = await self._calculate_readability_score(text)
        content.readability_score = readability_score
        
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
