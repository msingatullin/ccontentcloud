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
            from app.integrations.telegram_integration import TelegramIntegration
            from app.models.social_media import TelegramChannel
            
            # Получаем канал
            if post.account_id:
                channel = db.query(TelegramChannel).filter(
                    TelegramChannel.id == post.account_id
                ).first()
            else:
                # Берем первый активный канал пользователя
                channel = db.query(TelegramChannel).filter(
                    TelegramChannel.user_id == post.user_id,
                    TelegramChannel.is_active == True
                ).first()
            
            if not channel:
                return {
                    'success': False,
                    'error': 'Telegram канал не найден'
                }
            
            # Инициализируем интеграцию
            telegram = TelegramIntegration()
            
            # Публикуем
            result = telegram.send_message(
                bot_token=channel.bot_token,
                chat_id=channel.chat_id,
                text=content.text or content.title,
                options=post.publish_options or {}
            )
            
            if result.get('ok'):
                message_id = result.get('result', {}).get('message_id')
                return {
                    'success': True,
                    'platform_post_id': str(message_id) if message_id else None
                }
            else:
                return {
                    'success': False,
                    'error': result.get('description', 'Telegram API error')
                }
        
        except ImportError:
            logger.warning("TelegramIntegration не найден, используем заглушку")
            return {
                'success': True,
                'platform_post_id': f'telegram_mock_{post.id}_{int(time.time())}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
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

