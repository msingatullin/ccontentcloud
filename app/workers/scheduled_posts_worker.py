"""
Worker для публикации запланированных постов
Проверяет таблицу scheduled_posts и публикует посты по расписанию
"""

import logging
import time
import threading
import re
import asyncio
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
            
            if not message_text or not message_text.strip():
                # Fallback: если после форматирования ничего не осталось, используем базовый текст
                logger.warning(f"Formatted message is empty for content {content.id}, using fallback")
                message_text = content.text or content.title or ""
            
            # Проверяем наличие изображений
            image_url = None
            if content.media_urls:
                if isinstance(content.media_urls, list) and len(content.media_urls) > 0:
                    image_url = content.media_urls[0]  # Берем первое изображение
                    logger.info(f"📸 Найдено изображение для публикации: {image_url}")
                elif isinstance(content.media_urls, str):
                    # Если media_urls - это строка (JSON)
                    import json
                    try:
                        media_list = json.loads(content.media_urls)
                        if isinstance(media_list, list) and len(media_list) > 0:
                            image_url = media_list[0]
                            logger.info(f"📸 Найдено изображение для публикации (из JSON строки): {image_url}")
                    except:
                        logger.warning(f"⚠️ Не удалось распарсить media_urls как JSON: {content.media_urls}")
                else:
                    logger.info(f"ℹ️ media_urls имеет неожиданный тип: {type(content.media_urls)}, значение: {content.media_urls}")
            else:
                logger.info(f"ℹ️ media_urls пуст для контента {content.id}")
            
            # Публикуем через TelegramChannelService (async метод)
            logger.info(f"Публикация в канал '{channel.channel_name}' (chat_id={channel.chat_id})")
            
            # Если есть изображение - отправляем фото с подписью, иначе - просто текст
            if image_url:
                result = asyncio.run(service.send_photo(
                    chat_id=channel.chat_id,
                    photo_url=image_url,
                    caption=message_text,
                    parse_mode="HTML"
                ))
            else:
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
        
        # Основной текст (очищаем от метаданных)
        text = ""
        if content.text:
            # Убираем строки с метаданными
            lines = content.text.split('\n')
            cleaned_lines = []
            for line in lines:
                # Пропускаем строки с метаданными
                if any(meta in line.lower() for meta in ['наши цели:', 'бизнес-цели:', 'business_goals', 'creating_posts', 'publishing_social']):
                    continue
                cleaned_lines.append(line)
            text = '\n'.join(cleaned_lines).strip()
        
        # Проверяем, не начинается ли текст уже с заголовка
        title_in_text = False
        if content.title and text:
            # Проверяем, есть ли заголовок в начале текста (с небольшой вариативностью)
            title_clean = content.title.strip()
            # Убираем HTML теги если есть
            text_clean = text.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').strip()
            # Проверяем первые 150 символов текста (больше для учета вариаций)
            text_start = text_clean[:150].strip()
            
            # Извлекаем ключевые слова из заголовка (первые 2-3 значимых слова)
            title_words = [w.lower().strip() for w in title_clean.split() if len(w) > 3][:3]
            text_start_lower = text_start.lower()
            
            # Проверяем, есть ли ключевые слова заголовка в начале текста
            # Если хотя бы 2 из 3 первых слов заголовка встречаются в начале текста - это дубликат
            matches = sum(1 for word in title_words if word in text_start_lower[:100])
            
            # Также проверяем формальные начала, которые могут содержать тему из заголовка
            formal_beginnings = ['предлагает', 'компания', 'сервис', 'служба', 'сервис по']
            has_formal_beginning = any(beginning in text_start_lower[:50] for beginning in formal_beginnings)
            
            if matches >= 2 or (has_formal_beginning and matches >= 1) or title_clean.lower() in text_start_lower[:len(title_clean) + 20]:
                title_in_text = True
                logger.info(f"Заголовок '{title_clean}' найден в начале текста (совпадений: {matches}), не добавляем дубликат")
                # Убираем формальное начало из текста, если оно есть
                if has_formal_beginning:
                    # Пытаемся удалить первое предложение, если оно содержит формальное начало
                    sentences = text.split('.')
                    if len(sentences) > 1 and any(beginning in sentences[0].lower() for beginning in formal_beginnings):
                        text = '. '.join(sentences[1:]).strip()
                        logger.info(f"Удалено формальное начало из текста")
        
        # Заголовок (если есть и не дублируется в тексте)
        if content.title and not title_in_text:
            message_parts.append(f"<b>{content.title}</b>")
        
        # Добавляем основной текст (если есть)
        if text:
            message_parts.append(text)
        
        # Хештеги (если есть) - логируем для отладки
        if content.hashtags:
            logger.info(f"Hashtags found: {content.hashtags}, type: {type(content.hashtags)}")
            if isinstance(content.hashtags, list) and len(content.hashtags) > 0:
                # Очищаем хештеги от всех # (могут быть двойные или множественные)
                clean_hashtags = []
                for tag in content.hashtags[:10]:
                    if tag and tag.strip():
                        # Убираем ВСЕ # из начала строки (может быть ## или ###)
                        clean_tag = re.sub(r'^#+', '', tag.strip()).strip()
                        if clean_tag:
                            clean_hashtags.append(f"#{clean_tag}")
                
                if clean_hashtags:
                    hashtags_text = " ".join(clean_hashtags)
                    message_parts.append(hashtags_text)
                    logger.info(f"Hashtags added to message: {hashtags_text}")
            elif isinstance(content.hashtags, str):
                # Если хештеги пришли как строка, пытаемся распарсить
                hashtags_list = [tag.strip() for tag in content.hashtags.split(',') if tag.strip()]
                if hashtags_list:
                    clean_hashtags = []
                    for tag in hashtags_list[:10]:
                        # Убираем ВСЕ # из начала строки (может быть ## или ###)
                        clean_tag = re.sub(r'^#+', '', tag.strip()).strip()
                        if clean_tag:
                            clean_hashtags.append(f"#{clean_tag}")
                    if clean_hashtags:
                        hashtags_text = " ".join(clean_hashtags)
                        message_parts.append(hashtags_text)
                        logger.info(f"Hashtags (from string) added to message: {hashtags_text}")
        else:
            logger.warning(f"No hashtags found for content {content.id}")
        
        # Call to action (если есть)
        if content.call_to_action:
            message_parts.append(f"{content.call_to_action}")
        
        return "\n\n".join([part for part in message_parts if part.strip()])
    
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

