"""
Сервис для управления источниками контента
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.content_sources import ContentSource, MonitoredItem, SourceCheckHistory
from app.database.connection import SessionLocal

logger = logging.getLogger(__name__)


class ContentSourceService:
    """Сервис для работы с источниками контента"""
    
    @staticmethod
    def create_source(
        user_id: int,
        name: str,
        source_type: str,
        url: str,
        **kwargs
    ) -> Optional[ContentSource]:
        """Создание нового источника контента"""
        db = SessionLocal()
        try:
            # Вычисляем первую проверку
            check_interval = kwargs.get('check_interval_minutes', 60)
            next_check = datetime.utcnow() + timedelta(minutes=check_interval)
            
            source = ContentSource(
                user_id=user_id,
                name=name,
                source_type=source_type,
                url=url,
                next_check_at=next_check,
                **kwargs
            )
            
            db.add(source)
            db.commit()
            db.refresh(source)
            
            logger.info(f"Created content source: {source.id} for user {user_id}")
            return source
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating content source: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_source(source_id: int, user_id: int) -> Optional[ContentSource]:
        """Получение источника по ID"""
        db = SessionLocal()
        try:
            return db.query(ContentSource).filter(
                and_(
                    ContentSource.id == source_id,
                    ContentSource.user_id == user_id
                )
            ).first()
        finally:
            db.close()
    
    @staticmethod
    def get_user_sources(
        user_id: int,
        source_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[ContentSource]:
        """Получение всех источников пользователя"""
        db = SessionLocal()
        try:
            query = db.query(ContentSource).filter(ContentSource.user_id == user_id)
            
            if source_type:
                query = query.filter(ContentSource.source_type == source_type)
            
            if is_active is not None:
                query = query.filter(ContentSource.is_active == is_active)
            
            return query.order_by(ContentSource.created_at.desc()).all()
        finally:
            db.close()
    
    @staticmethod
    def update_source(
        source_id: int,
        user_id: int,
        **updates
    ) -> Optional[ContentSource]:
        """Обновление источника"""
        db = SessionLocal()
        try:
            source = db.query(ContentSource).filter(
                and_(
                    ContentSource.id == source_id,
                    ContentSource.user_id == user_id
                )
            ).first()
            
            if not source:
                return None
            
            # Обновляем поля
            for key, value in updates.items():
                if hasattr(source, key):
                    setattr(source, key, value)
            
            source.updated_at = datetime.utcnow()
            
            # Если изменился интервал проверки, пересчитываем next_check_at
            if 'check_interval_minutes' in updates:
                source.next_check_at = datetime.utcnow() + timedelta(minutes=updates['check_interval_minutes'])
            
            db.commit()
            db.refresh(source)
            
            logger.info(f"Updated content source: {source_id}")
            return source
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating content source {source_id}: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def delete_source(source_id: int, user_id: int) -> bool:
        """Удаление источника"""
        db = SessionLocal()
        try:
            source = db.query(ContentSource).filter(
                and_(
                    ContentSource.id == source_id,
                    ContentSource.user_id == user_id
                )
            ).first()
            
            if not source:
                return False
            
            db.delete(source)
            db.commit()
            
            logger.info(f"Deleted content source: {source_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting content source {source_id}: {e}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_sources_to_check(limit: int = 50) -> List[ContentSource]:
        """Получение источников, которые нужно проверить"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            return db.query(ContentSource).filter(
                and_(
                    ContentSource.is_active == True,
                    ContentSource.next_check_at <= now
                )
            ).order_by(ContentSource.next_check_at).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def update_check_status(
        source_id: int,
        status: str,
        items_found: int = 0,
        items_new: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Обновление статуса проверки источника"""
        db = SessionLocal()
        try:
            source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
            
            if not source:
                return False
            
            source.last_check_at = datetime.utcnow()
            source.last_check_status = status
            source.last_error_message = error_message
            source.total_checks += 1
            source.total_items_found += items_found
            source.total_items_new += items_new
            
            # Планируем следующую проверку
            source.next_check_at = datetime.utcnow() + timedelta(minutes=source.check_interval_minutes)
            
            db.commit()
            
            logger.info(f"Updated check status for source {source_id}: {status}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating check status for source {source_id}: {e}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def save_snapshot(source_id: int, snapshot_hash: str, snapshot_data: Dict[str, Any]) -> bool:
        """Сохранение снимка контента для diff"""
        db = SessionLocal()
        try:
            source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
            
            if not source:
                return False
            
            source.last_snapshot_hash = snapshot_hash
            source.last_snapshot_data = snapshot_data
            
            db.commit()
            
            logger.info(f"Saved snapshot for source {source_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving snapshot for source {source_id}: {e}")
            return False
        finally:
            db.close()


class MonitoredItemService:
    """Сервис для работы с найденными элементами контента"""
    
    @staticmethod
    def create_item(
        source_id: int,
        user_id: int,
        title: str,
        **kwargs
    ) -> Optional[MonitoredItem]:
        """Создание нового найденного элемента"""
        db = SessionLocal()
        try:
            item = MonitoredItem(
                source_id=source_id,
                user_id=user_id,
                title=title,
                **kwargs
            )
            
            db.add(item)
            db.commit()
            db.refresh(item)
            
            logger.info(f"Created monitored item: {item.id} for source {source_id}")
            return item
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating monitored item: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_item(item_id: int, user_id: int) -> Optional[MonitoredItem]:
        """Получение элемента по ID"""
        db = SessionLocal()
        try:
            return db.query(MonitoredItem).filter(
                and_(
                    MonitoredItem.id == item_id,
                    MonitoredItem.user_id == user_id
                )
            ).first()
        finally:
            db.close()
    
    @staticmethod
    def get_items_by_source(
        source_id: int,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[MonitoredItem]:
        """Получение элементов по источнику"""
        db = SessionLocal()
        try:
            query = db.query(MonitoredItem).filter(
                and_(
                    MonitoredItem.source_id == source_id,
                    MonitoredItem.user_id == user_id
                )
            )
            
            if status:
                query = query.filter(MonitoredItem.status == status)
            
            return query.order_by(MonitoredItem.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def get_new_items(user_id: int, limit: int = 50) -> List[MonitoredItem]:
        """Получение новых необработанных элементов"""
        db = SessionLocal()
        try:
            return db.query(MonitoredItem).filter(
                and_(
                    MonitoredItem.user_id == user_id,
                    MonitoredItem.status == 'new'
                )
            ).order_by(
                MonitoredItem.relevance_score.desc(),
                MonitoredItem.created_at.desc()
            ).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def update_item_status(
        item_id: int,
        status: str,
        **kwargs
    ) -> Optional[MonitoredItem]:
        """Обновление статуса элемента"""
        db = SessionLocal()
        try:
            item = db.query(MonitoredItem).filter(MonitoredItem.id == item_id).first()
            
            if not item:
                return None
            
            item.status = status
            
            # Обновляем дополнительные поля
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            if status in ['posted', 'ignored', 'approved']:
                item.processed_at = datetime.utcnow()
            
            if status == 'posted':
                item.posted_at = datetime.utcnow()
            
            db.commit()
            db.refresh(item)
            
            logger.info(f"Updated monitored item {item_id} status to {status}")
            return item
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating monitored item {item_id}: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def check_duplicate(source_id: int, external_id: Optional[str], url: Optional[str]) -> Optional[MonitoredItem]:
        """Проверка на дубликат"""
        db = SessionLocal()
        try:
            conditions = [MonitoredItem.source_id == source_id]
            
            if external_id:
                conditions.append(MonitoredItem.external_id == external_id)
            elif url:
                conditions.append(MonitoredItem.url == url)
            else:
                return None
            
            return db.query(MonitoredItem).filter(and_(*conditions)).first()
        finally:
            db.close()


class SourceCheckHistoryService:
    """Сервис для истории проверок источников"""
    
    @staticmethod
    def create_history(
        source_id: int,
        items_found: int,
        items_new: int,
        items_duplicate: int,
        items_posted: int,
        status: str,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> Optional[SourceCheckHistory]:
        """Создание записи истории проверки"""
        db = SessionLocal()
        try:
            history = SourceCheckHistory(
                source_id=source_id,
                items_found=items_found,
                items_new=items_new,
                items_duplicate=items_duplicate,
                items_posted=items_posted,
                status=status,
                error_message=error_message,
                execution_time_ms=execution_time_ms
            )
            
            db.add(history)
            db.commit()
            db.refresh(history)
            
            logger.info(f"Created check history for source {source_id}")
            return history
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating check history: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_source_history(source_id: int, limit: int = 50) -> List[SourceCheckHistory]:
        """Получение истории проверок источника"""
        db = SessionLocal()
        try:
            return db.query(SourceCheckHistory).filter(
                SourceCheckHistory.source_id == source_id
            ).order_by(SourceCheckHistory.checked_at.desc()).limit(limit).all()
        finally:
            db.close()

