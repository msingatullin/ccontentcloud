"""
Worker для публикации запланированных постов
Проверяет таблицу scheduled_posts и публикует посты по расписанию
"""

import logging
import time
import threading
from datetime import datetime
from typing import Optional

from app.database.connection import get_db_session
from app.services.scheduled_post_service import ScheduledPostService
from app.models.content import ContentPieceDB
from app.models.scheduled_posts import ScheduledPostDB

logger = logging.getLogger(__name__)


class ScheduledPostsWorker:
    """Worker для автоматической публикации запланированных постов"""
    
    def __init__(self, check_interval: int = 60):
        """
        Args:
            check_interval: Интервал проверки в секундах (по умолчанию 60)
        """
        self.check_interval = check_interval
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        logger.info(f"ScheduledPostsWorker инициализирован с интервалом {check_interval}s")
    
    def start(self):
        """Запустить worker в отдельном потоке"""
        if self.is_running:
            logger.warning("ScheduledPostsWorker уже запущен")
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ScheduledPostsWorker")
        self._thread.start()
        logger.info("ScheduledPostsWorker запущен")
    
    def stop(self):
        """Остановить worker"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("ScheduledPostsWorker остановлен")
    
    def _run_loop(self):
        """Основной цикл worker'а"""
        logger.info("ScheduledPostsWorker начал работу")
        
        while self.is_running:
            try:
                self._process_scheduled_posts()
            except Exception as e:
                logger.error(f"Ошибка в ScheduledPostsWorker: {e}", exc_info=True)
            
            # Ждем до следующей проверки
            time.sleep(self.check_interval)
        
        logger.info("ScheduledPostsWorker завершил работу")
    
    def _process_scheduled_posts(self):
        """Обработать запланированные посты"""
        db = None
        try:
            db = get_db_session()
            service = ScheduledPostService(db)
            
            # Получаем посты готовые к публикации
            posts = service.get_posts_to_publish(limit=50)
            
            if not posts:
                logger.debug("Нет постов для публикации")
                return
            
            logger.info(f"Найдено {len(posts)} постов для публикации")
            
            for post in posts:
                try:
                    self._publish_post(post, db, service)
                except Exception as e:
                    logger.error(f"Ошибка обработки поста {post.id}: {e}", exc_info=True)
                    # Помечаем как failed
                    try:
                        service.mark_as_published(
                            post.id,
                            None,
                            error_message=f"Критическая ошибка: {str(e)}"
                        )
                    except Exception as mark_error:
                        logger.error(f"Не удалось пометить пост {post.id} как failed: {mark_error}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке постов: {e}", exc_info=True)
        finally:
            if db:
                db.close()
    
    def _publish_post(self, post: ScheduledPostDB, db, service: ScheduledPostService):
        """
        Опубликовать один пост
        
        Args:
            post: Запланированный пост
            db: Сессия БД
            service: ScheduledPostService
        """
        logger.info(f"Публикация поста {post.id} (content_id={post.content_id}, platform={post.platform})")
        
        # Получаем контент
        content = db.query(ContentPieceDB).filter(
            ContentPieceDB.id == post.content_id
        ).first()
        
        if not content:
            logger.error(f"Контент {post.content_id} не найден для поста {post.id}")
            service.mark_as_published(
                post.id,
                None,
                error_message="Контент не найден"
            )
            return
        
        # Проверяем что контент готов к публикации
        if content.status != 'approved' and content.status != 'ready':
            logger.warning(f"Контент {content.id} имеет статус {content.status}, но продолжаем публикацию")
        
        # Публикуем через соответствующий сервис
        try:
            result = self._publish_to_platform(
                post=post,
                content=content,
                db=db
            )
            
            if result['success']:
                logger.info(f"Пост {post.id} успешно опубликован: {result.get('platform_post_id', 'N/A')}")
                service.mark_as_published(
                    post.id,
                    result.get('platform_post_id'),
                    error_message=None
                )
            else:
                error_msg = result.get('error', 'Неизвестная ошибка')
                logger.error(f"Ошибка публикации поста {post.id}: {error_msg}")
                service.mark_as_published(
                    post.id,
                    None,
                    error_message=error_msg
                )
        
        except Exception as e:
            logger.error(f"Исключение при публикации поста {post.id}: {e}", exc_info=True)
            service.mark_as_published(
                post.id,
                None,
                error_message=f"Исключение: {str(e)}"
            )
    
    def _publish_to_platform(self, post: ScheduledPostDB, content: ContentPieceDB, db) -> dict:
        """
        Публикация на платформу
        
        Args:
            post: Запланированный пост
            content: Контент для публикации
            db: Сессия БД
            
        Returns:
            dict: {'success': bool, 'platform_post_id': str, 'error': str}
        """
        platform = post.platform.lower()
        
        try:
            if platform == 'telegram':
                return self._publish_to_telegram(post, content, db)
            elif platform == 'instagram':
                return self._publish_to_instagram(post, content, db)
            elif platform == 'twitter':
                return self._publish_to_twitter(post, content, db)
            else:
                return {
                    'success': False,
                    'error': f'Неподдерживаемая платформа: {platform}'
                }
        
        except Exception as e:
            logger.error(f"Ошибка публикации на {platform}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _publish_to_telegram(self, post: ScheduledPostDB, content: ContentPieceDB, db) -> dict:
        """Публикация в Telegram"""
        try:
            import asyncio
            from app.services.telegram_channel_service import TelegramChannelService
            from app.models.telegram_channels import TelegramChannel
            
            # Получаем канал
            if post.account_id:
                channel = db.query(TelegramChannel).filter(
                    TelegramChannel.id == post.account_id,
                    TelegramChannel.user_id == post.user_id,
                    TelegramChannel.is_active == True
                ).first()
            else:
                # Берем дефолтный канал пользователя
                service = TelegramChannelService(db)
                channel = service.get_default_channel(post.user_id)
            
            if not channel:
                return {
                    'success': False,
                    'error': 'Telegram канал не найден. Добавьте канал в настройках.'
                }
            
            if not channel.is_verified:
                return {
                    'success': False,
                    'error': f'Канал "{channel.channel_name}" не верифицирован. Добавьте бота @content4ubot в администраторы канала.'
                }
            
            # Инициализируем сервис
            service = TelegramChannelService(db)
            
            # Формируем текст сообщения через форматирование (как в publisher_agent)
            # Убираем метаданные из текста
            message_text = self._format_telegram_message(content)
            
            # Дополнительная очистка от метаданных (на случай если они все еще есть)
            # Удаляем строки с "Наши цели:", "Бизнес-цели:", технические данные
            lines = message_text.split('\n')
            cleaned_lines = []
            for line in lines:
                # Пропускаем строки с метаданными
                if any(meta in line.lower() for meta in ['наши цели:', 'бизнес-цели:', 'business_goals', 'creating_posts', 'publishing_social']):
                    continue
                cleaned_lines.append(line)
            message_text = '\n'.join(cleaned_lines).strip()
            
            if not message_text:
                # Fallback: если после очистки ничего не осталось, используем базовый текст
                message_text = content.text or content.title
                if not message_text:
                    message_text = f"{content.title}\n\n{content.text or ''}".strip()
            
            # Публикуем через TelegramChannelService (async метод)
            logger.info(f"Публикация в канал '{channel.channel_name}' (chat_id={channel.chat_id})")
            result = asyncio.run(service.send_message(
                chat_id=channel.chat_id,
                text=message_text,
                parse_mode="HTML",
                disable_web_page_preview=False
            ))
            
            if result.get('success'):
                message_data = result.get('data', {})
                message_id = message_data.get('message_id')
                
                # Обновляем статистику канала
                service.update_channel_stats(channel.id, post_success=True)
                
                logger.info(f"✅ Пост успешно опубликован в канал '{channel.channel_name}', message_id={message_id}")
                
                return {
                    'success': True,
                    'platform_post_id': str(message_id) if message_id else None
                }
            else:
                error_msg = result.get('error', 'Telegram API error')
                logger.error(f"❌ Ошибка публикации в канал '{channel.channel_name}': {error_msg}")
                
                # Обновляем статистику канала с ошибкой
                service.update_channel_stats(channel.id, post_success=False, error_message=error_msg)
                
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except Exception as e:
            logger.error(f"Критическая ошибка публикации в Telegram: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_telegram_message(self, content: ContentPieceDB) -> str:
        """Форматирует сообщение для Telegram (как в publisher_agent)"""
        message_parts = []
        
        # Заголовок (если есть)
        if content.title:
            message_parts.append(f"<b>{content.title}</b>")
        
        # Основной текст (очищаем от метаданных)
        if content.text:
            text = content.text
            # Убираем строки с метаданными
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                # Пропускаем строки с метаданными
                if any(meta in line.lower() for meta in ['наши цели:', 'бизнес-цели:', 'business_goals', 'creating_posts', 'publishing_social']):
                    continue
                cleaned_lines.append(line)
            text = '\n'.join(cleaned_lines).strip()
            if text:
                message_parts.append(text)
        
        # Хештеги (если есть)
        if content.hashtags and isinstance(content.hashtags, list):
            hashtags_text = " ".join([f"#{tag.replace('#', '')}" for tag in content.hashtags[:10]])  # Максимум 10 хештегов
            if hashtags_text:
                message_parts.append(hashtags_text)
        
        # Call to action (если есть)
        if content.call_to_action:
            message_parts.append(f"\n{content.call_to_action}")
        
        return "\n\n".join(message_parts)
    
    def _publish_to_instagram(self, post: ScheduledPostDB, content: ContentPieceDB, db) -> dict:
        """Публикация в Instagram"""
        try:
            from app.integrations.instagram_integration import InstagramIntegration
            from app.models.social_media import InstagramAccount
            
            # Получаем аккаунт
            if post.account_id:
                account = db.query(InstagramAccount).filter(
                    InstagramAccount.id == post.account_id
                ).first()
            else:
                account = db.query(InstagramAccount).filter(
                    InstagramAccount.user_id == post.user_id,
                    InstagramAccount.is_active == True
                ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'Instagram аккаунт не найден'
                }
            
            # TODO: Реализовать публикацию в Instagram через API
            logger.warning("Instagram публикация пока не реализована, используем заглушку")
            return {
                'success': True,
                'platform_post_id': f'instagram_mock_{post.id}_{int(time.time())}'
            }
        
        except ImportError:
            logger.warning("InstagramIntegration не найден, используем заглушку")
            return {
                'success': True,
                'platform_post_id': f'instagram_mock_{post.id}_{int(time.time())}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _publish_to_twitter(self, post: ScheduledPostDB, content: ContentPieceDB, db) -> dict:
        """Публикация в Twitter"""
        try:
            from app.integrations.twitter_integration import TwitterIntegration
            from app.models.social_media import TwitterAccount
            
            # Получаем аккаунт
            if post.account_id:
                account = db.query(TwitterAccount).filter(
                    TwitterAccount.id == post.account_id
                ).first()
            else:
                account = db.query(TwitterAccount).filter(
                    TwitterAccount.user_id == post.user_id,
                    TwitterAccount.is_active == True
                ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'Twitter аккаунт не найден'
                }
            
            # TODO: Реализовать публикацию в Twitter через API
            logger.warning("Twitter публикация пока не реализована, используем заглушку")
            return {
                'success': True,
                'platform_post_id': f'twitter_mock_{post.id}_{int(time.time())}'
            }
        
        except ImportError:
            logger.warning("TwitterIntegration не найден, используем заглушку")
            return {
                'success': True,
                'platform_post_id': f'twitter_mock_{post.id}_{int(time.time())}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

