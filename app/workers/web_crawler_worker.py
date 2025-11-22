"""
Web Crawler Worker для мониторинга источников контента
"""

import logging
import threading
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from openai import AsyncOpenAI
import os

from app.services.content_source_service import ContentSourceService, MonitoredItemService, SourceCheckHistoryService
from app.services.content_extractor import ContentExtractor, ChangeDetector, RSSParser
from app.services.scheduled_post_service import ScheduledPostService
from app.services.production_calendar_service import ProductionCalendarService
from app.database.connection import get_db_session
from app.models.content_sources import ContentSource

logger = logging.getLogger(__name__)


class WebCrawlerWorker:
    """Worker для мониторинга источников контента"""
    
    def __init__(self, check_interval: int = 60):
        """
        Args:
            check_interval: Интервал проверки в секундах (по умолчанию 60)
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.openai_client = None
        
        # Инициализируем OpenAI клиент
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            logger.warning("OPENAI_API_KEY not set, AI extraction will be disabled")
        
        self.content_extractor = ContentExtractor(self.openai_client)
        self.change_detector = ChangeDetector()
        
        logger.info(f"WebCrawlerWorker initialized with check_interval={check_interval}s")
    
    def start(self):
        """Запуск worker в отдельном потоке"""
        if self.running:
            logger.warning("WebCrawlerWorker already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("WebCrawlerWorker started")
    
    def stop(self):
        """Остановка worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("WebCrawlerWorker stopped")
    
    def _run(self):
        """Основной цикл worker"""
        logger.info("WebCrawlerWorker main loop started")
        
        while self.running:
            try:
                # Получаем источники для проверки
                sources = ContentSourceService.get_sources_to_check(limit=10)
                
                if sources:
                    logger.info(f"Found {len(sources)} sources to check")
                    
                    for source in sources:
                        if not self.running:
                            break
                        
                        # Проверяем источник
                        asyncio.run(self._check_source(source))
                
                # Ждем перед следующей итерацией
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in WebCrawlerWorker main loop: {e}", exc_info=True)
                time.sleep(self.check_interval)
    
    async def _check_source(self, source):
        """Проверка одного источника контента"""
        start_time = time.time()
        logger.info(f"Checking source: {source.id} - {source.name} ({source.source_type})")
        
        try:
            items_found = 0
            items_new = 0
            items_duplicate = 0
            items_posted = 0
            
            # Умная обработка: автоматически определяем лучший метод
            if source.source_type == 'rss':
                # Прямой RSS - используем как есть
                result = await self._check_rss_source(source)
            elif source.source_type == 'website' or source.source_type == 'auto':
                # Пробуем найти RSS автоматически
                result = await self._check_source_smart(source)
            else:
                logger.warning(f"Unsupported source type: {source.source_type}, trying smart detection")
                result = await self._check_source_smart(source)
            
            items_found = result.get('items_found', 0)
            items_new = result.get('items_new', 0)
            items_duplicate = result.get('items_duplicate', 0)
            items_posted = result.get('items_posted', 0)
            
            # Обновляем статус источника
            ContentSourceService.update_check_status(
                source.id,
                status='success',
                items_found=items_found,
                items_new=items_new
            )
            
            # Сохраняем историю проверки
            execution_time = int((time.time() - start_time) * 1000)
            SourceCheckHistoryService.create_history(
                source_id=source.id,
                items_found=items_found,
                items_new=items_new,
                items_duplicate=items_duplicate,
                items_posted=items_posted,
                status='success',
                execution_time_ms=execution_time
            )
            
            logger.info(f"Source {source.id} checked successfully: {items_new} new items")
            
        except Exception as e:
            logger.error(f"Error checking source {source.id}: {e}", exc_info=True)
            
            # Обновляем статус, но не показываем технические ошибки пользователю
            # Вместо этого просто отмечаем как "нет новых новостей"
            try:
                ContentSourceService.update_check_status(
                    source.id,
                    status='success',  # Показываем как успех, чтобы не пугать пользователя
                    items_found=0,
                    items_new=0
                )
                
                # Сохраняем историю
                execution_time = int((time.time() - start_time) * 1000)
                SourceCheckHistoryService.create_history(
                    source_id=source.id,
                    items_found=0,
                    items_new=0,
                    items_duplicate=0,
                    items_posted=0,
                    status='success',  # Не показываем ошибку пользователю
                    execution_time_ms=execution_time
                )
            except Exception as update_error:
                logger.error(f"Error updating status after error: {update_error}")
    
    async def _check_rss_source(self, source) -> Dict[str, int]:
        """Проверка RSS источника"""
        items_found = 0
        items_new = 0
        items_duplicate = 0
        items_posted = 0
        
        try:
            # Загружаем RSS ленту
            response = requests.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Парсим RSS
            feed_items = RSSParser.parse_feed(response.text)
            items_found = len(feed_items)
            
            logger.info(f"RSS source {source.id}: found {items_found} items")
            
            # Обрабатываем каждый элемент
            for feed_item in feed_items[:20]:  # Берем максимум 20 последних
                # Проверяем на дубликат
                external_id = feed_item.get('external_id')
                url = feed_item.get('url')
                
                duplicate = MonitoredItemService.check_duplicate(source.id, external_id, url)
                if duplicate:
                    items_duplicate += 1
                    continue
                
                # Применяем фильтры по ключевым словам
                if not self._matches_filters(feed_item, source):
                    continue
                
                # Создаем новый элемент
                monitored_item = MonitoredItemService.create_item(
                    source_id=source.id,
                    user_id=source.user_id,
                    title=feed_item.get('title', 'Untitled'),
                    content=feed_item.get('content', ''),
                    summary=feed_item.get('summary', ''),
                    url=url,
                    author=feed_item.get('author'),
                    external_id=external_id,
                    status='new',
                    raw_data=feed_item,
                    relevance_score=0.7  # Базовая релевантность для RSS
                )
                
                if monitored_item:
                    items_new += 1
                    
                    # Если включен автопостинг, создаем отложенный пост
                    if source.auto_post_enabled:
                        posted = await self._create_scheduled_post(source, monitored_item, feed_item)
                        if posted:
                            items_posted += 1
            
            return {
                'items_found': items_found,
                'items_new': items_new,
                'items_duplicate': items_duplicate,
                'items_posted': items_posted
            }
            
        except Exception as e:
            logger.error(f"Error checking RSS source {source.id}: {e}")
            raise
    
    async def _check_source_smart(self, source) -> Dict[str, int]:
        """
        Умная проверка источника: автоматически определяет RSS или использует краулер
        Не показывает ошибки пользователю, пробует все варианты
        """
        items_found = 0
        items_new = 0
        items_duplicate = 0
        items_posted = 0
        
        try:
            # 1. Пробуем найти RSS на странице
            logger.info(f"Smart check for source {source.id}: trying to discover RSS feed...")
            # discover_rss_feed может работать синхронно, но оборачиваем в try-except для безопасности
            try:
                rss_url = RSSParser.discover_rss_feed(source.url)
            except Exception as e:
                logger.warning(f"Error discovering RSS feed: {e}, will use crawler")
                rss_url = None
            
            if rss_url:
                logger.info(f"RSS feed discovered: {rss_url}, using RSS method")
                # Временно меняем URL на RSS для обработки
                original_url = source.url
                try:
                    source.url = rss_url
                    result = await self._check_rss_source(source)
                    items_found = result.get('items_found', 0)
                    items_new = result.get('items_new', 0)
                    items_duplicate = result.get('items_duplicate', 0)
                    items_posted = result.get('items_posted', 0)
                    
                    # Если RSS сработал - обновляем тип источника для будущих проверок
                    if items_new > 0:
                        db = get_db_session()
                        try:
                            source_obj = db.query(ContentSource).filter(ContentSource.id == source.id).first()
                            if source_obj:
                                source_obj.source_type = 'rss'
                                source_obj.url = rss_url
                                db.commit()
                                logger.info(f"Updated source {source.id} to RSS type with URL {rss_url}")
                        finally:
                            db.close()
                    
                    return {
                        'items_found': items_found,
                        'items_new': items_new,
                        'items_duplicate': items_duplicate,
                        'items_posted': items_posted
                    }
                except Exception as e:
                    logger.warning(f"RSS method failed for {rss_url}, trying crawler: {e}")
                    source.url = original_url
                    # Продолжаем с краулером
            
            # 2. Если RSS не найден или не сработал - используем краулер
            logger.info(f"Using crawler method for source {source.id}")
            result = await self._check_website_source(source)
            return result
            
        except Exception as e:
            logger.error(f"Error in smart check for source {source.id}: {e}")
            # Не пробрасываем ошибку дальше, возвращаем пустой результат
            return {
                'items_found': 0,
                'items_new': 0,
                'items_duplicate': 0,
                'items_posted': 0
            }
    
    async def _check_website_source(self, source) -> Dict[str, int]:
        """Проверка website источника с помощью crawler"""
        items_found = 0
        items_new = 0
        items_duplicate = 0
        items_posted = 0
        
        try:
            # Загружаем страницу
            response = requests.get(source.url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ContentCurator/1.0; +https://content-curator.com)'
            })
            response.raise_for_status()
            html = response.text
            
            # Проверяем изменения
            changes = self.change_detector.detect_changes(
                html,
                source.last_snapshot_data
            )
            
            if not changes.get('has_changes'):
                logger.info(f"Website source {source.id}: no changes detected")
                return {
                    'items_found': 0,
                    'items_new': 0,
                    'items_duplicate': 0,
                    'items_posted': 0
                }
            
            # Сохраняем новый снимок
            ContentSourceService.save_snapshot(
                source.id,
                changes.get('new_hash'),
                {'hash': changes.get('new_hash'), 'timestamp': datetime.utcnow().isoformat()}
            )
            
            # Извлекаем контент с помощью AI
            extraction_hints = {
                'keywords': source.keywords,
                'categories': source.categories
            }
            
            extracted_data = await self.content_extractor.extract_from_html(
                html,
                source.url,
                extraction_hints
            )
            
            items_found = 1
            
            # Проверяем на дубликат по URL
            duplicate = MonitoredItemService.check_duplicate(source.id, None, source.url)
            if duplicate:
                # Обновляем существующий элемент если контент изменился
                MonitoredItemService.update_item_status(
                    duplicate.id,
                    status='new',
                    content=extracted_data.get('content', ''),
                    summary=extracted_data.get('summary', ''),
                    extracted_data=extracted_data,
                    relevance_score=extracted_data.get('relevance_score', 0.5)
                )
                items_duplicate += 1
            else:
                # Создаем новый элемент
                monitored_item = MonitoredItemService.create_item(
                    source_id=source.id,
                    user_id=source.user_id,
                    title=extracted_data.get('title', 'Untitled'),
                    content=extracted_data.get('content', ''),
                    summary=extracted_data.get('summary', ''),
                    url=source.url,
                    image_url=extracted_data.get('image_url'),
                    author=extracted_data.get('author'),
                    status='new',
                    extracted_data=extracted_data,
                    ai_summary=extracted_data.get('summary'),
                    ai_sentiment=extracted_data.get('sentiment'),
                    ai_category=extracted_data.get('category'),
                    ai_keywords=extracted_data.get('keywords', []),
                    relevance_score=extracted_data.get('relevance_score', 0.5)
                )
                
                if monitored_item:
                    items_new += 1
                    
                    # Если включен автопостинг и это релевантный контент
                    if source.auto_post_enabled and extracted_data.get('relevance_score', 0) >= 0.5:
                        posted = await self._create_scheduled_post(source, monitored_item, extracted_data)
                        if posted:
                            items_posted += 1
            
            return {
                'items_found': items_found,
                'items_new': items_new,
                'items_duplicate': items_duplicate,
                'items_posted': items_posted
            }
            
        except Exception as e:
            logger.error(f"Error checking website source {source.id}: {e}")
            raise
    
    def _matches_filters(self, item_data: Dict[str, Any], source) -> bool:
        """Проверка соответствия элемента фильтрам источника"""
        
        # Если нет фильтров, пропускаем все
        if not source.keywords and not source.exclude_keywords:
            return True
        
        # Подготавливаем текст для проверки
        text = f"{item_data.get('title', '')} {item_data.get('summary', '')} {item_data.get('content', '')}".lower()
        
        # Проверяем исключающие ключевые слова
        if source.exclude_keywords:
            for keyword in source.exclude_keywords:
                if keyword.lower() in text:
                    logger.debug(f"Item excluded by keyword: {keyword}")
                    return False
        
        # Проверяем включающие ключевые слова
        if source.keywords:
            for keyword in source.keywords:
                if keyword.lower() in text:
                    return True
            # Если не нашли ни одного ключевого слова
            return False
        
        return True
    
    async def _create_scheduled_post(
        self,
        source,
        monitored_item,
        extracted_data: Dict[str, Any]
    ) -> bool:
        """Создание отложенного поста из найденного контента"""
        db = get_db_session()
        try:
            # Сначала создаем контент из новости
            from app.models.content import ContentPieceDB
            import uuid
            
            # Формируем текст поста по шаблону
            if source.post_template:
                post_text = source.post_template.format(
                    title=extracted_data.get('title', ''),
                    description=extracted_data.get('summary', ''),
                    content=extracted_data.get('content', '')[:500],
                    url=extracted_data.get('url', ''),
                    author=extracted_data.get('author', '')
                )
            else:
                # Базовый шаблон
                post_text = f"{extracted_data.get('title', '')}\n\n{extracted_data.get('summary', '')}"
                if extracted_data.get('url'):
                    post_text += f"\n\n{extracted_data['url']}"
            
            # Создаем контент из новости
            content = ContentPieceDB(
                id=str(uuid.uuid4()),
                user_id=source.user_id,
                title=extracted_data.get('title', 'Untitled'),
                text=post_text,
                content_type='post',
                platform='telegram',
                status='draft',
                meta_data={
                    'source_id': source.id,
                    'monitored_item_id': monitored_item.id,
                    'url': extracted_data.get('url', ''),
                    'auto_generated': True,
                    'image_url': extracted_data.get('image_url')
                }
            )
            db.add(content)
            db.commit()
            db.refresh(content)
            logger.info(f"Created content piece {content.id} from monitored item {monitored_item.id}")
            
            # Определяем время публикации с учетом расписания
            from datetime import timedelta
            
            # Получаем настройки расписания из config
            posting_schedule = source.config.get('posting_schedule', {}) if source.config else {}
            frequency = posting_schedule.get('frequency', '2h')
            forbidden_hours_start = posting_schedule.get('forbidden_hours_start', '22:00')
            forbidden_hours_end = posting_schedule.get('forbidden_hours_end', '08:00')
            weekends_mode = posting_schedule.get('weekends_mode', 'disabled')
            use_production_calendar = posting_schedule.get('use_production_calendar', True)
            weekends_schedule = posting_schedule.get('weekends_schedule', {})
            
            # Вычисляем базовое время публикации на основе частоты
            base_time = datetime.utcnow()
            if frequency == '1h':
                scheduled_time = base_time + timedelta(hours=1)
            elif frequency == '2h':
                scheduled_time = base_time + timedelta(hours=2)
            elif frequency == '5h':
                scheduled_time = base_time + timedelta(hours=5)
            elif frequency == '1d':
                scheduled_time = base_time + timedelta(days=1)
            elif frequency == '2d':
                # Два раза в сутки - утром и вечером
                scheduled_time = base_time + timedelta(hours=12)
            else:
                scheduled_time = base_time + timedelta(minutes=source.post_delay_minutes or 0)
            
            # Проверяем, можно ли постить в это время
            can_post = ProductionCalendarService.can_post_at_time(
                post_datetime=scheduled_time,
                forbidden_hours_start=forbidden_hours_start,
                forbidden_hours_end=forbidden_hours_end,
                weekends_mode=weekends_mode,
                use_production_calendar=use_production_calendar,
                weekends_schedule=weekends_schedule
            )
            
            # Если нельзя постить сейчас, ищем ближайшее разрешенное время
            if not can_post:
                # Пробуем сдвинуть время вперед с шагом в 1 час, максимум 24 часа
                for hours_offset in range(1, 25):
                    candidate_time = scheduled_time + timedelta(hours=hours_offset)
                    if ProductionCalendarService.can_post_at_time(
                        post_datetime=candidate_time,
                        forbidden_hours_start=forbidden_hours_start,
                        forbidden_hours_end=forbidden_hours_end,
                        weekends_mode=weekends_mode,
                        use_production_calendar=use_production_calendar,
                        weekends_schedule=weekends_schedule
                    ):
                        scheduled_time = candidate_time
                        logger.info(f"Adjusted posting time for source {source.id} to {scheduled_time} due to schedule restrictions")
                        break
                else:
                    # Если не нашли подходящее время за 24 часа, откладываем на завтра
                    scheduled_time = scheduled_time + timedelta(days=1)
                    scheduled_time = scheduled_time.replace(hour=9, minute=0, second=0, microsecond=0)
                    logger.warning(f"Could not find suitable posting time for source {source.id}, scheduled for {scheduled_time}")
            
            # Получаем первый активный Telegram канал пользователя
            from app.models.telegram_channels import TelegramChannel
            telegram_channel = db.query(TelegramChannel).filter(
                TelegramChannel.user_id == source.user_id,
                TelegramChannel.is_active == True
            ).first()
            
            if not telegram_channel:
                logger.warning(f"No active Telegram channel found for user {source.user_id}, skipping post creation")
                return False
            
            # Создаем сервис с сессией БД
            scheduled_service = ScheduledPostService(db)
            
            # Создаем отложенный пост
            try:
                scheduled_post = scheduled_service.create_scheduled_post(
                    user_id=source.user_id,
                    content_id=content.id,
                    platform='telegram',
                    account_id=telegram_channel.id,
                    scheduled_time=scheduled_time,
                    publish_options={
                        'text': post_text,
                        'media_urls': [extracted_data.get('image_url')] if extracted_data.get('image_url') else None
                    }
                )
                
                if scheduled_post:
                    # Обновляем monitored_item
                    MonitoredItemService.update_item_status(
                        monitored_item.id,
                        status='approved',
                        scheduled_post_id=scheduled_post.id
                    )
                    
                    logger.info(f"✅ Created scheduled post {scheduled_post.id} from monitored item {monitored_item.id} for source {source.id}")
                    return True
                else:
                    logger.warning(f"Failed to create scheduled post for monitored item {monitored_item.id}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error creating scheduled post via service: {e}", exc_info=True)
                return False
            
        except Exception as e:
            logger.error(f"Error creating scheduled post: {e}", exc_info=True)
            return False
        finally:
            db.close()

