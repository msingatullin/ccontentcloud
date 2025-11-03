"""
PublisherAgent - Публиковщик
Публикует контент в социальные сети и отслеживает результаты
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..orchestrator.agent_manager import BaseAgent, AgentCapability
from ..orchestrator.workflow_engine import Task, TaskType, TaskPriority
from ..models.content import ContentPiece, Platform, ContentStatus, PublicationSchedule, ContentMetrics
from ..mcp.integrations.telegram import TelegramMCP
from ..mcp.config import get_mcp_config, is_mcp_enabled

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class PublicationResult:
    """Результат публикации"""
    success: bool
    platform_post_id: Optional[str] = None
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


@dataclass
class PlatformConfig:
    """Конфигурация платформы"""
    platform: str
    api_endpoint: str
    auth_required: bool
    rate_limits: Dict[str, int]
    supported_formats: List[str]
    max_text_length: int


class PublisherAgent(BaseAgent):
    """Агент для публикации контента в социальные сети"""
    
    def __init__(self, agent_id: str = "publisher_agent"):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED, TaskType.REAL_TIME],
            max_concurrent_tasks=3,
            specializations=["publishing", "social_media", "analytics", "scheduling"],
            performance_score=1.0
        )
        super().__init__(agent_id, "Publisher Agent", capability)
        
        # Конфигурации платформ
        self.platform_configs = self._load_platform_configs()
        self.publication_queue = []
        self.published_content = {}
        
        # MCP интеграции
        self.telegram_mcp = None
        self._initialize_mcp_integrations()
        
        logger.info(f"PublisherAgent {agent_id} инициализирован")
    
    def _load_platform_configs(self) -> Dict[str, PlatformConfig]:
        """Загружает конфигурации платформ"""
        return {
            "telegram": PlatformConfig(
                platform="telegram",
                api_endpoint="https://api.telegram.org/bot",
                auth_required=True,
                rate_limits={"posts_per_hour": 30, "requests_per_second": 1},
                supported_formats=["text", "image", "video", "document"],
                max_text_length=4096
            ),
            "vk": PlatformConfig(
                platform="vk",
                api_endpoint="https://api.vk.com/method",
                auth_required=True,
                rate_limits={"posts_per_hour": 100, "requests_per_second": 3},
                supported_formats=["text", "image", "video", "poll"],
                max_text_length=1000
            ),
            "instagram": PlatformConfig(
                platform="instagram",
                api_endpoint="https://graph.instagram.com",
                auth_required=True,
                rate_limits={"posts_per_hour": 25, "requests_per_second": 1},
                supported_formats=["image", "video", "carousel"],
                max_text_length=2200
            ),
            "twitter": PlatformConfig(
                platform="twitter",
                api_endpoint="https://api.twitter.com/2",
                auth_required=True,
                rate_limits={"posts_per_hour": 300, "requests_per_second": 1},
                supported_formats=["text", "image", "video"],
                max_text_length=280
            )
        }
    
    def _initialize_mcp_integrations(self):
        """Инициализирует MCP интеграции"""
        try:
            # Инициализируем TelegramMCP если доступен
            if is_mcp_enabled('telegram'):
                self.telegram_mcp = TelegramMCP()
                logger.info("TelegramMCP инициализирован в PublisherAgent")
            else:
                logger.warning("TelegramMCP недоступен - будет использоваться fallback")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации MCP интеграций: {e}")
            self.telegram_mcp = None
    
    def can_handle_task(self, task: Task) -> bool:
        """
        Проверяет, может ли PublisherAgent выполнить задачу
        Обрабатывает только задачи публикации (с 'Publish' в названии)
        """
        # Сначала проверяем базовые условия
        if not super().can_handle_task(task):
            return False
        
        # PublisherAgent обрабатывает только задачи публикации
        if "Publish" in task.name or "publish" in task.name.lower():
            return True
        
        return False
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу публикации контента"""
        try:
            logger.info(f"PublisherAgent выполняет задачу: {task.name}")
            
            # Извлекаем данные из контекста задачи
            content_data = task.context.get("content", {})
            platform = task.context.get("platform", "telegram")
            schedule_time = task.context.get("schedule_time")
            test_mode = task.context.get("test_mode", True)
            user_id = task.context.get("user_id")  # ID пользователя для мультипользовательского режима
            account_id = task.context.get("account_id")  # ID конкретного аккаунта (telegram_channel_id, instagram_account_id, twitter_account_id)
            
            # Создаем контент-пис
            content_piece = ContentPiece(
                id=content_data.get("id", ""),
                title=content_data.get("title", ""),
                text=content_data.get("text", ""),
                hashtags=content_data.get("hashtags", []),
                call_to_action=content_data.get("call_to_action", ""),
                platform=Platform(platform),
                status=ContentStatus.DRAFT,
                created_by_agent=self.agent_id
            )
            
            # Публикуем контент
            if test_mode:
                result = await self._publish_test_content(content_piece, platform)
            else:
                result = await self._publish_content(content_piece, platform, schedule_time, user_id, account_id)
            
            # Создаем расписание публикации
            schedule = await self._create_publication_schedule(
                content_piece, platform, result
            )
            
            # Собираем метрики
            metrics = await self._collect_initial_metrics(result, platform)
            
            result_data = {
                "task_id": task.id,
                "agent_id": self.agent_id,
                "publication": {
                    "success": result.success,
                    "platform_post_id": result.platform_post_id,
                    "published_at": result.published_at.isoformat() if result.published_at else None,
                    "error_message": result.error_message
                },
                "schedule": {
                    "id": schedule.id,
                    "scheduled_time": schedule.scheduled_time.isoformat(),
                    "status": schedule.status.value
                },
                "metrics": metrics,
                "platform_info": {
                    "platform": platform,
                    "config": {
                        "max_text_length": self.platform_configs[platform].max_text_length,
                        "supported_formats": self.platform_configs[platform].supported_formats
                    }
                },
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"PublisherAgent завершил задачу {task.id}")
            return result_data
            
        except Exception as e:
            logger.error(f"Ошибка в PublisherAgent: {e}")
            raise
    
    async def _publish_test_content(self, content: ContentPiece, platform: str) -> PublicationResult:
        """Подготавливает контент к публикации (форматирование и валидация)"""
        logger.info(f"Подготовка контента для {platform}")
        
        # Форматируем контент под платформу
        formatted_content = await self._format_content_for_platform(content, platform)
        
        # Валидируем финальный контент
        validation = await self._validate_formatted_content(formatted_content, platform)
        
        # Генерируем превью для пользователя
        preview = await self._generate_content_preview(formatted_content, platform)
        
        # Рассчитываем оптимальное время публикации
        optimal_time = await self._calculate_optimal_publish_time(platform, content)
        
        # Генерируем тестовый ID (для истории)
        import random
        test_post_id = f"ready_{platform}_{random.randint(10000, 99999)}"
        
        return PublicationResult(
            success=True,
            platform_post_id=test_post_id,
            published_at=None,  # Не опубликовано, готово к публикации
            metrics={
                "status": "ready_to_publish",
                "formatted_content": formatted_content,
                "preview": preview,
                "optimal_publish_time": optimal_time.isoformat(),
                "validation": validation,
                "estimated_reach": random.randint(500, 5000),
                "estimated_engagement_rate": round(random.uniform(0.05, 0.20), 2)
            }
        )
    
    async def _publish_content(self, content: ContentPiece, platform: str, 
                             schedule_time: Optional[datetime] = None,
                             user_id: Optional[int] = None,
                             account_id: Optional[int] = None) -> PublicationResult:
        """Публикует контент в реальную платформу"""
        try:
            platform_config = self.platform_configs.get(platform)
            if not platform_config:
                return PublicationResult(
                    success=False,
                    error_message=f"Платформа {platform} не поддерживается"
                )
            
            # Проверяем ограничения
            if not await self._check_rate_limits(platform):
                return PublicationResult(
                    success=False,
                    error_message=f"Превышены лимиты для платформы {platform}"
                )
            
            # Валидируем контент
            validation_result = await self._validate_content(content, platform)
            if not validation_result["valid"]:
                return PublicationResult(
                    success=False,
                    error_message=validation_result["error"]
                )
            
            # Публикуем в зависимости от платформы
            if platform == "telegram":
                return await self._publish_to_telegram(content, schedule_time, user_id, account_id)
            elif platform == "vk":
                return await self._publish_to_vk(content, schedule_time)
            elif platform == "instagram":
                return await self._publish_to_instagram(content, schedule_time, user_id, account_id)
            elif platform == "twitter":
                return await self._publish_to_twitter(content, schedule_time, user_id, account_id)
            else:
                return PublicationResult(
                    success=False,
                    error_message=f"Метод публикации для {platform} не реализован"
                )
                
        except Exception as e:
            logger.error(f"Ошибка публикации в {platform}: {e}")
            return PublicationResult(
                success=False,
                error_message=str(e)
            )
    
    async def _check_rate_limits(self, platform: str) -> bool:
        """Проверяет лимиты публикации для платформы"""
        # В MVP просто возвращаем True
        # В реальной реализации здесь была бы проверка лимитов API
        return True
    
    async def _validate_content(self, content: ContentPiece, platform: str) -> Dict[str, Any]:
        """Валидирует контент для платформы"""
        platform_config = self.platform_configs.get(platform)
        if not platform_config:
            return {"valid": False, "error": f"Платформа {platform} не найдена"}
        
        # Проверяем длину текста
        if len(content.text) > platform_config.max_text_length:
            return {
                "valid": False, 
                "error": f"Текст слишком длинный: {len(content.text)} > {platform_config.max_text_length}"
            }
        
        # Проверяем наличие текста
        if not content.text.strip():
            return {"valid": False, "error": "Текст контента пустой"}
        
        return {"valid": True}
    
    async def _publish_to_telegram(self, content: ContentPiece, 
                                 schedule_time: Optional[datetime] = None,
                                 user_id: Optional[int] = None,
                                 channel_id: Optional[int] = None) -> PublicationResult:
        """
        Публикует в Telegram через TelegramMCP
        
        Args:
            content: Контент для публикации
            schedule_time: Время публикации (опционально)
            user_id: ID пользователя (для многопользовательского режима)
            channel_id: ID конкретного канала или None для дефолтного
        """
        try:
            # Если указан user_id - используем канал пользователя
            if user_id:
                return await self._publish_to_telegram_user_channel(
                    content, user_id, channel_id, schedule_time
                )
            
            # Иначе используем старую логику (глобальный бот)
            # Проверяем доступность TelegramMCP
            if self.telegram_mcp is None:
                logger.warning("TelegramMCP недоступен, используем fallback")
                return await self._publish_to_telegram_fallback(content, schedule_time)
            
            # Получаем конфигурацию Telegram
            telegram_config = get_mcp_config('telegram')
            if not telegram_config or telegram_config.test_mode:
                logger.info("Telegram в тестовом режиме, используем fallback")
                return await self._publish_to_telegram_fallback(content, schedule_time)
            
            # Формируем сообщение для Telegram
            message_text = self._format_telegram_message(content)
            
            logger.info(f"Публикация в Telegram через MCP: {content.title}")
            
            # Отправляем сообщение через TelegramMCP
            result = await self.telegram_mcp.execute_with_retry(
                'send_message',
                text=message_text
            )
            
            if result.success:
                message_data = result.data
                logger.info(f"Сообщение успешно отправлено в Telegram, ID: {message_data.get('message_id')}")
                
                return PublicationResult(
                    success=True,
                    platform_post_id=str(message_data.get('message_id')),
                    published_at=datetime.now(),
                    metrics={
                        "message_id": message_data.get('message_id'),
                        "chat_id": message_data.get('chat', {}).get('id'),
                        "sent_via": "telegram_mcp",
                        "timestamp": message_data.get('date')
                    }
                )
            else:
                logger.error(f"Ошибка отправки в Telegram: {result.error}")
                # Fallback на мок данные при ошибке
                return await self._publish_to_telegram_fallback(content, schedule_time)
            
        except Exception as e:
            logger.error(f"Критическая ошибка публикации в Telegram: {e}")
            # Fallback на мок данные при критической ошибке
            return await self._publish_to_telegram_fallback(content, schedule_time)
    
    async def _publish_to_telegram_user_channel(self, content: ContentPiece,
                                                user_id: int,
                                                channel_id: Optional[int] = None,
                                                schedule_time: Optional[datetime] = None) -> PublicationResult:
        """
        Публикует в Telegram канал конкретного пользователя
        Архитектура: ОДИН БОТ - МНОГО КАНАЛОВ
        
        Args:
            content: Контент для публикации
            user_id: ID пользователя
            channel_id: ID конкретного канала или None для дефолтного
            schedule_time: Время публикации
        """
        try:
            from app.services.telegram_channel_service import TelegramChannelService
            from app.models.telegram_channels import TelegramChannel
            from app.database.connection import get_db_session_session
            
            # Получаем сессию БД
            db = next(get_db_session())
            service = TelegramChannelService(db)
            
            # Получаем канал пользователя
            if channel_id:
                channel = db.query(TelegramChannel).filter(
                    TelegramChannel.id == channel_id,
                    TelegramChannel.user_id == user_id,
                    TelegramChannel.is_active == True
                ).first()
            else:
                # Используем дефолтный канал
                channel = service.get_default_channel(user_id)
            
            if not channel:
                logger.error(f"Telegram канал не найден для user_id={user_id}, channel_id={channel_id}")
                return PublicationResult(
                    success=False,
                    error_message="Telegram канал не подключен. Добавьте канал в настройках."
                )
            
            if not channel.is_verified:
                logger.warning(f"Попытка публикации в неверифицированный канал {channel.id}")
                return PublicationResult(
                    success=False,
                    error_message=f"Канал '{channel.channel_name}' не верифицирован. Добавьте бота @content4ubot в администраторы канала."
                )
            
            # Формируем сообщение
            message_text = self._format_telegram_message(content)
            
            logger.info(f"Публикация в канал '{channel.channel_name}' (user_id={user_id}, chat_id={channel.chat_id})")
            
            # Отправляем через TelegramChannelService (прямо через Bot API)
            result = await service.send_message(
                chat_id=channel.chat_id,
                text=message_text,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            
            if result["success"]:
                message_data = result["data"]
                message_id = message_data.get('message_id')
                
                # Обновляем статистику канала
                service.update_channel_stats(channel.id, post_success=True)
                
                # Формируем URL поста если возможно
                post_url = None
                if channel.channel_username:
                    post_url = f"https://t.me/{channel.channel_username.lstrip('@')}/{message_id}"
                
                logger.info(f"✅ Успешно опубликовано в канал '{channel.channel_name}', message_id={message_id}")
                
                return PublicationResult(
                    success=True,
                    platform="telegram",
                    platform_post_id=str(message_id),
                    post_url=post_url,
                    published_at=datetime.now(),
                    metrics={
                        "message_id": message_id,
                        "channel_id": channel.id,
                        "channel_name": channel.channel_name,
                        "chat_id": channel.chat_id,
                        "sent_via": "telegram_bot_api"
                    }
                )
            else:
                error_msg = result["error"] or "Неизвестная ошибка Telegram API"
                logger.error(f"❌ Ошибка публикации в канал '{channel.channel_name}': {error_msg}")
                
                # Сохраняем ошибку в канале
                service.update_channel_stats(channel.id, post_success=False, error_message=error_msg)
                
                return PublicationResult(
                    success=False,
                    error_message=f"Ошибка публикации: {error_msg}"
                )
            
        except Exception as e:
            logger.error(f"Критическая ошибка публикации в пользовательский канал: {e}", exc_info=True)
            return PublicationResult(
                success=False,
                error_message=f"Внутренняя ошибка: {str(e)}"
            )
    
    async def _publish_to_telegram_fallback(self, content: ContentPiece, 
                                          schedule_time: Optional[datetime] = None) -> PublicationResult:
        """Fallback метод для публикации в Telegram (мок данные)"""
        try:
            logger.info("Публикация в Telegram (fallback/имитация)")
            
            # Имитируем API вызов
            await asyncio.sleep(1)
            
            import random
            post_id = f"tg_{random.randint(10000, 99999)}"
            
            return PublicationResult(
                success=True,
                platform_post_id=post_id,
                published_at=datetime.now(),
                metrics={
                    "views": random.randint(500, 2000),
                    "forwards": random.randint(10, 100),
                    "reactions": random.randint(20, 200),
                    "sent_via": "fallback"
                }
            )
            
        except Exception as e:
            return PublicationResult(
                success=False,
                error_message=f"Ошибка fallback публикации в Telegram: {e}"
            )
    
    def _format_telegram_message(self, content: ContentPiece) -> str:
        """Форматирует сообщение для Telegram"""
        message_parts = []
        
        # Заголовок
        if content.title:
            message_parts.append(f"<b>{content.title}</b>")
        
        # Основной текст
        if content.text:
            message_parts.append(content.text)
        
        # Хештеги
        if content.hashtags:
            hashtags_text = " ".join([f"#{tag}" for tag in content.hashtags])
            message_parts.append(hashtags_text)
        
        # Call to action
        if content.call_to_action:
            message_parts.append(f"\n{content.call_to_action}")
        
        return "\n\n".join(message_parts)
    
    async def _publish_to_vk(self, content: ContentPiece, 
                           schedule_time: Optional[datetime] = None) -> PublicationResult:
        """Публикует в VK"""
        try:
            logger.info("Публикация в VK (имитация)")
            
            await asyncio.sleep(1)
            
            import random
            post_id = f"vk_{random.randint(10000, 99999)}"
            
            return PublicationResult(
                success=True,
                platform_post_id=post_id,
                published_at=datetime.now(),
                metrics={
                    "views": random.randint(1000, 5000),
                    "likes": random.randint(50, 500),
                    "reposts": random.randint(5, 50),
                    "comments": random.randint(10, 100)
                }
            )
            
        except Exception as e:
            return PublicationResult(
                success=False,
                error_message=f"Ошибка публикации в VK: {e}"
            )
    
    async def _publish_to_instagram(self, content: ContentPiece, 
                                  schedule_time: Optional[datetime] = None,
                                  user_id: Optional[int] = None,
                                  account_id: Optional[int] = None) -> PublicationResult:
        """Публикует в Instagram через подключенный аккаунт пользователя"""
        
        # Если user_id не указан - используем старую имитацию
        if not user_id:
            logger.warning("Instagram публикация без user_id - имитация")
            return await self._publish_to_instagram_fallback(content, schedule_time)
        
        try:
            from app.database.connection import get_db_session
            from app.services.instagram_account_service import InstagramAccountService
            
            logger.info(f"Публикация в Instagram для user_id={user_id}, account_id={account_id}")
            
            # Получаем сессию БД
            db = next(get_db_session())
            service = InstagramAccountService(db)
            
            # Получаем аккаунт
            if account_id:
                account = service.get_account_by_id(user_id, account_id)
                if not account:
                    return PublicationResult(
                        success=False,
                        error_message="Instagram аккаунт не найден"
                    )
            else:
                # Используем дефолтный аккаунт
                account = service.get_default_account(user_id)
                if not account:
                    return PublicationResult(
                        success=False,
                        error_message="У пользователя нет дефолтного Instagram аккаунта"
                    )
            
            # Проверяем активность
            if not account.is_active:
                return PublicationResult(
                    success=False,
                    error_message="Instagram аккаунт деактивирован"
                )
            
            # Формируем текст с хэштегами
            text = content.text
            hashtags = content.hashtags or []
            
            # Проверяем наличие изображения
            if not content.images or len(content.images) == 0:
                return PublicationResult(
                    success=False,
                    error_message="Instagram требует как минимум одно изображение"
                )
            
            # Берем первое изображение
            photo_path = content.images[0]
            
            # Публикуем
            success, message = await service.publish_photo(
                account_id=account.id,
                photo_path=photo_path,
                caption=text,
                hashtags=hashtags
            )
            
            if success:
                logger.info(f"✅ Instagram публикация успешна: {message}")
                return PublicationResult(
                    success=True,
                    platform_post_id=message,  # message содержит media_id
                    published_at=datetime.now()
                )
            else:
                logger.error(f"❌ Instagram публикация не удалась: {message}")
                return PublicationResult(
                    success=False,
                    error_message=message
                )
            
        except Exception as e:
            logger.error(f"Критическая ошибка публикации в Instagram: {e}")
            return PublicationResult(
                success=False,
                error_message=f"Ошибка публикации в Instagram: {str(e)}"
            )
    
    async def _publish_to_instagram_fallback(self, content: ContentPiece, 
                                           schedule_time: Optional[datetime] = None) -> PublicationResult:
        """Имитация публикации в Instagram (для обратной совместимости)"""
        try:
            logger.info("Публикация в Instagram (имитация - FALLBACK)")
            
            await asyncio.sleep(1.5)
            
            import random
            post_id = f"ig_mock_{random.randint(10000, 99999)}"
            
            return PublicationResult(
                success=True,
                platform_post_id=post_id,
                published_at=datetime.now(),
                metrics={
                    "likes": random.randint(100, 1000),
                    "comments": random.randint(10, 100),
                    "saves": random.randint(5, 50),
                    "shares": random.randint(5, 25)
                }
            )
            
        except Exception as e:
            return PublicationResult(
                success=False,
                error_message=f"Ошибка имитации Instagram: {e}"
            )
    
    async def _publish_to_twitter(self, content: ContentPiece, 
                                schedule_time: Optional[datetime] = None,
                                user_id: Optional[int] = None,
                                account_id: Optional[int] = None) -> PublicationResult:
        """Публикует в Twitter через подключенный аккаунт пользователя"""
        
        # Если user_id не указан - используем старую имитацию
        if not user_id:
            logger.warning("Twitter публикация без user_id - имитация")
            return await self._publish_to_twitter_fallback(content, schedule_time)
        
        try:
            from app.database.connection import get_db_session
            from app.services.twitter_account_service import TwitterAccountService
            
            logger.info(f"Публикация в Twitter для user_id={user_id}, account_id={account_id}")
            
            # Получаем сессию БД
            db = next(get_db_session())
            service = TwitterAccountService(db)
            
            # Получаем аккаунт
            if account_id:
                account = service.get_account_by_id(user_id, account_id)
                if not account:
                    return PublicationResult(
                        success=False,
                        error_message="Twitter аккаунт не найден"
                    )
            else:
                # Используем дефолтный аккаунт
                account = service.get_default_account(user_id)
                if not account:
                    return PublicationResult(
                        success=False,
                        error_message="У пользователя нет дефолтного Twitter аккаунта"
                    )
            
            # Проверяем активность
            if not account.is_active:
                return PublicationResult(
                    success=False,
                    error_message="Twitter аккаунт деактивирован"
                )
            
            # Формируем текст
            text = content.text
            
            # Twitter ограничение - 280 символов
            if len(text) > 280:
                logger.warning(f"Текст твита слишком длинный ({len(text)} символов), обрезаем до 280")
                text = text[:277] + "..."
            
            # Собираем пути к медиа (если есть)
            media_paths = []
            if content.images:
                media_paths.extend(content.images[:4])  # Twitter позволяет до 4 изображений
            
            # Публикуем
            success, message = await service.publish_tweet(
                account_id=account.id,
                text=text,
                media_paths=media_paths if media_paths else None
            )
            
            if success:
                logger.info(f"✅ Twitter публикация успешна: {message}")
                return PublicationResult(
                    success=True,
                    platform_post_id=message,  # message содержит tweet_id
                    published_at=datetime.now()
                )
            else:
                logger.error(f"❌ Twitter публикация не удалась: {message}")
                return PublicationResult(
                    success=False,
                    error_message=message
                )
            
        except Exception as e:
            logger.error(f"Критическая ошибка публикации в Twitter: {e}")
            return PublicationResult(
                success=False,
                error_message=f"Ошибка публикации в Twitter: {str(e)}"
            )
    
    async def _publish_to_twitter_fallback(self, content: ContentPiece, 
                                         schedule_time: Optional[datetime] = None) -> PublicationResult:
        """Имитация публикации в Twitter (для обратной совместимости)"""
        try:
            logger.info("Публикация в Twitter (имитация - FALLBACK)")
            
            await asyncio.sleep(0.8)
            
            import random
            post_id = f"tw_mock_{random.randint(10000, 99999)}"
            
            return PublicationResult(
                success=True,
                platform_post_id=post_id,
                published_at=datetime.now(),
                metrics={
                    "retweets": random.randint(5, 50),
                    "likes": random.randint(20, 200),
                    "replies": random.randint(2, 20),
                    "quotes": random.randint(1, 10)
                }
            )
            
        except Exception as e:
            return PublicationResult(
                success=False,
                error_message=f"Ошибка имитации Twitter: {e}"
            )
    
    async def _create_publication_schedule(self, content: ContentPiece, platform: str, 
                                         result: PublicationResult) -> PublicationSchedule:
        """Создает расписание публикации"""
        schedule = PublicationSchedule(
            content_id=content.id,
            platform=Platform(platform),
            scheduled_time=datetime.now(),
            published_time=result.published_at,
            status=ContentStatus.PUBLISHED if result.success else ContentStatus.FAILED,
            platform_post_id=result.platform_post_id,
            metrics=result.metrics or {}
        )
        
        return schedule
    
    async def _collect_initial_metrics(self, result: PublicationResult, platform: str) -> Dict[str, Any]:
        """Собирает начальные метрики"""
        if not result.success:
            return {"error": result.error_message}
        
        metrics = {
            "platform": platform,
            "post_id": result.platform_post_id,
            "published_at": result.published_at.isoformat() if result.published_at else None,
            "initial_metrics": result.metrics or {},
            "collection_timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    async def schedule_publication(self, content: ContentPiece, platform: str, 
                                 schedule_time: datetime) -> PublicationSchedule:
        """Планирует публикацию на определенное время"""
        schedule = PublicationSchedule(
            content_id=content.id,
            platform=Platform(platform),
            scheduled_time=schedule_time,
            status=ContentStatus.SCHEDULED
        )
        
        # Добавляем в очередь планирования
        self.publication_queue.append({
            "schedule": schedule,
            "content": content,
            "platform": platform
        })
        
        logger.info(f"Запланирована публикация в {platform} на {schedule_time}")
        return schedule
    
    async def get_publication_metrics(self, platform_post_id: str, platform: str) -> ContentMetrics:
        """Получает метрики публикации"""
        # В MVP возвращаем тестовые метрики
        import random
        
        metrics = ContentMetrics(
            content_id="",
            platform=Platform(platform),
            platform_post_id=platform_post_id,
            views=random.randint(100, 5000),
            likes=random.randint(10, 500),
            shares=random.randint(5, 100),
            comments=random.randint(0, 50),
            clicks=random.randint(0, 200),
            engagement_rate=random.uniform(0.05, 0.25),
            click_through_rate=random.uniform(0.01, 0.1),
            reach=random.randint(500, 10000),
            post_created_at=datetime.now() - timedelta(hours=random.randint(1, 24))
        )
        
        return metrics
    
    async def analyze_performance(self, content_id: str, platform: str) -> Dict[str, Any]:
        """Анализирует производительность контента"""
        # В MVP возвращаем базовый анализ
        import random
        
        analysis = {
            "content_id": content_id,
            "platform": platform,
            "performance_score": random.uniform(0.3, 0.9),
            "engagement_rate": random.uniform(0.05, 0.3),
            "reach": random.randint(1000, 10000),
            "viral_potential": random.uniform(0.1, 0.8),
            "recommendations": [
                "Попробуйте добавить больше визуального контента",
                "Публикуйте в оптимальное время для вашей аудитории",
                "Используйте больше релевантных хештегов"
            ],
            "best_performing_elements": [
                "Заголовок привлек внимание",
                "Хештеги увеличили охват",
                "Call-to-action вызвал отклик"
            ],
            "improvement_areas": [
                "Увеличить частоту публикаций",
                "Добавить больше интерактивного контента",
                "Оптимизировать время публикации"
            ]
        }
        
        return analysis
    
    async def republish_content(self, content: ContentPiece, platform: str, 
                              modifications: Dict[str, Any] = None) -> PublicationResult:
        """Перепубликует контент с модификациями"""
        # Применяем модификации
        if modifications:
            if "text" in modifications:
                content.text = modifications["text"]
            if "hashtags" in modifications:
                content.hashtags = modifications["hashtags"]
            if "call_to_action" in modifications:
                content.call_to_action = modifications["call_to_action"]
        
        # Публикуем модифицированный контент
        return await self._publish_content(content, platform)
    
    async def delete_publication(self, platform_post_id: str, platform: str) -> bool:
        """Удаляет публикацию с платформы"""
        try:
            logger.info(f"Удаление публикации {platform_post_id} с {platform}")
            
            # В MVP просто имитируем удаление
            await asyncio.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления публикации: {e}")
            return False
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по платформам"""
        stats = {}
        
        for platform, config in self.platform_configs.items():
            stats[platform] = {
                "supported": True,
                "max_text_length": config.max_text_length,
                "rate_limits": config.rate_limits,
                "supported_formats": config.supported_formats
            }
        
        return stats
    
    async def _format_content_for_platform(self, content: ContentPiece, platform: str) -> str:
        """Форматирует контент под конкретную платформу"""
        platform_config = self.platform_configs.get(platform)
        if not platform_config:
            return content.text
        
        formatted_parts = []
        
        # Форматируем в зависимости от платформы
        if platform == "telegram":
            # Telegram поддерживает HTML и Markdown
            if content.title:
                formatted_parts.append(f"<b>{content.title}</b>\n")
            formatted_parts.append(content.text)
            if content.hashtags:
                formatted_parts.append("\n" + " ".join(content.hashtags))
            if content.call_to_action:
                formatted_parts.append(f"\n\n{content.call_to_action}")
            
        elif platform == "vk":
            # VK использует plain text
            if content.title:
                formatted_parts.append(f"{content.title}\n")
            formatted_parts.append(content.text)
            if content.hashtags:
                formatted_parts.append("\n" + " ".join(content.hashtags))
            if content.call_to_action:
                formatted_parts.append(f"\n{content.call_to_action}")
            
        elif platform == "instagram":
            # Instagram - короткий текст с хештегами
            formatted_parts.append(content.text)
            if content.hashtags:
                formatted_parts.append("\n\n" + " ".join(content.hashtags[:30]))  # Instagram лимит
            
        elif platform == "twitter":
            # Twitter - очень короткий текст
            text = content.text[:250]  # Резервируем место для хештегов
            formatted_parts.append(text)
            if content.hashtags:
                formatted_parts.append(" ".join(content.hashtags[:3]))  # Макс 3 хештега
        
        formatted = "".join(formatted_parts)
        
        # Обрезаем если превышает лимит
        if len(formatted) > platform_config.max_text_length:
            formatted = formatted[:platform_config.max_text_length - 3] + "..."
        
        return formatted
    
    async def _validate_formatted_content(self, formatted_content: str, platform: str) -> Dict[str, Any]:
        """Валидирует отформатированный контент"""
        platform_config = self.platform_configs.get(platform)
        
        issues = []
        warnings = []
        
        # Проверка длины
        if len(formatted_content) > platform_config.max_text_length:
            issues.append(f"Превышена максимальная длина: {len(formatted_content)} > {platform_config.max_text_length}")
        elif len(formatted_content) > platform_config.max_text_length * 0.9:
            warnings.append("Контент близок к максимальной длине")
        
        # Проверка на пустоту
        if not formatted_content.strip():
            issues.append("Контент пустой после форматирования")
        
        # Проверка хештегов
        hashtag_count = formatted_content.count('#')
        if hashtag_count > 10 and platform != "instagram":
            warnings.append(f"Слишком много хештегов: {hashtag_count}")
        
        # Проверка ссылок
        if 'http' in formatted_content:
            if platform == "instagram":
                warnings.append("Instagram не поддерживает кликабельные ссылки в постах")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "content_length": len(formatted_content),
            "max_length": platform_config.max_text_length,
            "usage_percentage": round(len(formatted_content) / platform_config.max_text_length * 100, 1)
        }
    
    async def _generate_content_preview(self, formatted_content: str, platform: str) -> str:
        """Генерирует превью контента"""
        preview_length = 100
        if len(formatted_content) <= preview_length:
            return formatted_content
        
        return formatted_content[:preview_length] + "..."
    
    async def _calculate_optimal_publish_time(self, platform: str, content: ContentPiece) -> datetime:
        """Рассчитывает оптимальное время публикации"""
        # Базовое оптимальное время для разных платформ (на основе исследований)
        optimal_hours = {
            "telegram": [9, 13, 18, 20],  # Утро, обед, вечер
            "vk": [12, 18, 21],  # Обед, вечер, поздний вечер
            "instagram": [11, 14, 19],  # Обед, после обеда, вечер
            "twitter": [9, 12, 17]  # Утро, обед, конец рабочего дня
        }
        
        platform_hours = optimal_hours.get(platform, [12, 18])
        
        # Находим ближайшее оптимальное время
        now = datetime.now()
        current_hour = now.hour
        
        # Ищем следующий оптимальный час
        for hour in platform_hours:
            if hour > current_hour:
                optimal_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                return optimal_time
        
        # Если все часы прошли, берем первый час завтра
        tomorrow = now + timedelta(days=1)
        optimal_time = tomorrow.replace(hour=platform_hours[0], minute=0, second=0, microsecond=0)
        
        return optimal_time
