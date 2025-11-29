"""
Worker для выполнения правил автопостинга
Проверяет таблицу auto_posting_rules и создает/публикует контент
"""

import logging
import time
import threading
import requests
from datetime import datetime
from typing import Optional

from app.database.connection import get_db_session
from app.services.auto_posting_service import AutoPostingService
from app.services.scheduled_post_service import ScheduledPostService
from app.models.auto_posting_rules import AutoPostingRuleDB

logger = logging.getLogger(__name__)


class AutoPostingWorker:
    """Worker для автоматического создания и публикации контента по правилам"""
    
    def __init__(self, check_interval: int = 300, api_base_url: str = None):
        """
        Args:
            check_interval: Интервал проверки в секундах (по умолчанию 300 = 5 минут)
            api_base_url: Базовый URL API для создания контента
        """
        self.check_interval = check_interval
        self.api_base_url = api_base_url or "http://localhost:8080"
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        logger.info(f"AutoPostingWorker инициализирован с интервалом {check_interval}s")
    
    def start(self):
        """Запустить worker в отдельном потоке"""
        if self.is_running:
            logger.warning("AutoPostingWorker уже запущен")
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="AutoPostingWorker")
        self._thread.start()
        logger.info("AutoPostingWorker запущен")
    
    def stop(self):
        """Остановить worker"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("AutoPostingWorker остановлен")
    
    def _run_loop(self):
        """Основной цикл worker'а"""
        logger.info("AutoPostingWorker начал работу")
        
        while self.is_running:
            try:
                self._process_auto_posting_rules()
            except Exception as e:
                logger.error(f"Ошибка в AutoPostingWorker: {e}", exc_info=True)
            
            # Ждем до следующей проверки
            time.sleep(self.check_interval)
        
        logger.info("AutoPostingWorker завершил работу")
    
    def _process_auto_posting_rules(self):
        """Обработать правила автопостинга"""
        db = None
        try:
            db = get_db_session()
            service = AutoPostingService(db)
            
            # Получаем правила готовые к выполнению
            rules = service.get_rules_to_execute(limit=50)
            
            if not rules:
                logger.debug("Нет правил для выполнения")
                return
            
            logger.info(f"Найдено {len(rules)} правил для выполнения")
            
            for rule in rules:
                try:
                    self._execute_rule(rule, db, service)
                except Exception as e:
                    logger.error(f"Ошибка выполнения правила {rule.id}: {e}", exc_info=True)
                    # Помечаем как failed execution
                    try:
                        service.mark_execution(rule.id, success=False)
                    except Exception as mark_error:
                        logger.error(f"Не удалось пометить правило {rule.id}: {mark_error}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке правил: {e}", exc_info=True)
        finally:
            if db:
                db.close()
    
    def _execute_rule(self, rule: AutoPostingRuleDB, db, service: AutoPostingService):
        """
        Выполнить правило автопостинга
        
        Args:
            rule: Правило автопостинга
            db: Сессия БД
            service: AutoPostingService
        """
        logger.info(f"Выполнение правила {rule.id} '{rule.name}' (user_id={rule.user_id})")
        
        # Проверяем лимиты
        if not self._check_limits(rule, db):
            logger.warning(f"Правило {rule.id} превысило лимиты, пропускаем")
            # Всё равно отмечаем выполнение чтобы обновить next_execution_at
            service.mark_execution(rule.id, success=True)
            return
        
        try:
            # 1. Создаем контент через API
            content_id = self._create_content(rule)
            
            if not content_id:
                logger.error(f"Не удалось создать контент для правила {rule.id}")
                service.mark_execution(rule.id, success=False)
                return
            
            logger.info(f"Создан контент {content_id} для правила {rule.id}")
            
            # 2. Создаем запланированные посты для каждой платформы
            scheduled_service = ScheduledPostService(db)
            posts_created = 0
            
            for platform in rule.platforms:
                # Получаем список аккаунтов для платформы
                account_ids = rule.accounts.get(platform, []) if rule.accounts else []
                
                if not account_ids:
                    # Если аккаунты не указаны, создаем пост без account_id
                    # (будет использован первый активный аккаунт при публикации)
                    account_ids = [None]
                
                for account_id in account_ids:
                    try:
                        # Создаем запланированный пост (сразу или через небольшую задержку)
                        scheduled_time = datetime.utcnow()  # Публикуем сразу
                        
                        post = scheduled_service.create_scheduled_post(
                            user_id=rule.user_id,
                            content_id=content_id,
                            platform=platform,
                            scheduled_time=scheduled_time,
                            account_id=account_id,
                            publish_options={}
                        )
                        
                        posts_created += 1
                        logger.info(f"Создан запланированный пост {post.id} для {platform}")
                    
                    except Exception as e:
                        logger.error(f"Ошибка создания поста для {platform}: {e}")
            
            # Помечаем выполнение как успешное
            service.mark_execution(rule.id, success=True)
            logger.info(f"Правило {rule.id} успешно выполнено, создано {posts_created} постов")
        
        except Exception as e:
            logger.error(f"Исключение при выполнении правила {rule.id}: {e}", exc_info=True)
            service.mark_execution(rule.id, success=False)
    
    def _check_limits(self, rule: AutoPostingRuleDB, db) -> bool:
        """
        Проверить лимиты публикаций
        
        Args:
            rule: Правило автопостинга
            db: Сессия БД
            
        Returns:
            bool: True если лимиты не превышены
        """
        from app.models.scheduled_posts import ScheduledPostDB
        from datetime import timedelta
        
        now = datetime.utcnow()
        
        # Проверяем дневной лимит
        if rule.max_posts_per_day:
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            posts_today = db.query(ScheduledPostDB).filter(
                ScheduledPostDB.user_id == rule.user_id,
                ScheduledPostDB.created_at >= day_start
            ).count()
            
            if posts_today >= rule.max_posts_per_day:
                logger.warning(f"Правило {rule.id}: достигнут дневной лимит {rule.max_posts_per_day}")
                return False
        
        # Проверяем недельный лимит
        if rule.max_posts_per_week:
            week_start = now - timedelta(days=7)
            posts_this_week = db.query(ScheduledPostDB).filter(
                ScheduledPostDB.user_id == rule.user_id,
                ScheduledPostDB.created_at >= week_start
            ).count()
            
            if posts_this_week >= rule.max_posts_per_week:
                logger.warning(f"Правило {rule.id}: достигнут недельный лимит {rule.max_posts_per_week}")
                return False
        
        return True
    
    def _create_content(self, rule: AutoPostingRuleDB) -> Optional[str]:
        """
        Создать контент через API
        
        Args:
            rule: Правило автопостинга
            
        Returns:
            str: ID созданного контента или None
        """
        try:
            # TODO: Получить JWT token пользователя для авторизации
            # Пока используем внутренний вызов без токена
            
            url = f"{self.api_base_url}/api/v1/content/create"
            
            # Подготавливаем данные из content_config
            data = rule.content_config.copy()
            
            # Добавляем platforms если не указаны
            if 'platforms' not in data:
                data['platforms'] = rule.platforms
            
            # Добавляем content_types если не указаны
            if 'content_types' not in data and rule.content_types:
                data['content_types'] = rule.content_types
            
            logger.info(f"Создание контента для правила {rule.id}: {url}")
            
            # Вызываем API (внутренний вызов без авторизации для worker'а)
            # TODO: Нужно реализовать внутренний API или использовать service напрямую
            
            # ВРЕМЕННО: используем заглушку
            logger.warning("Прямой вызов API /content/create из worker'а не реализован")
            logger.warning("Используйте прямой вызов сервиса ContentOrchestrator")
            
            # Генерируем mock content_id
            content_id = f"mock_content_{rule.id}_{int(time.time())}"
            logger.info(f"Mock контент создан: {content_id}")
            
            return content_id
        
        except Exception as e:
            logger.error(f"Ошибка создания контента: {e}", exc_info=True)
            return None

