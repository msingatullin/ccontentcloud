"""
Сервис для работы с запланированными постами
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.scheduled_posts import ScheduledPostDB
from app.models.content import ContentPieceDB

logger = logging.getLogger(__name__)


class ScheduledPostService:
    """Сервис управления запланированными постами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_scheduled_post(
        self,
        user_id: int,
        content_id: str,
        platform: str,
        scheduled_time: datetime,
        account_id: Optional[int] = None,
        account_type: Optional[str] = None,
        publish_options: Optional[Dict[str, Any]] = None
    ) -> ScheduledPostDB:
        """Создать запланированный пост"""
        # Проверяем что контент существует и принадлежит пользователю
        content = self.db.query(ContentPieceDB).filter(
            and_(
                ContentPieceDB.id == content_id,
                ContentPieceDB.user_id == user_id
            )
        ).first()
        
        if not content:
            raise ValueError(f"Контент {content_id} не найден или не принадлежит пользователю")
        
        # Определяем account_type если не указан
        if not account_type:
            if platform == 'telegram':
                account_type = 'telegram_channel'
            elif platform == 'instagram':
                account_type = 'instagram_account'
            elif platform == 'twitter':
                account_type = 'twitter_account'
        
        scheduled_post = ScheduledPostDB(
            user_id=user_id,
            content_id=content_id,
            platform=platform,
            account_id=account_id,
            account_type=account_type,
            scheduled_time=scheduled_time,
            status='scheduled',
            publish_options=publish_options or {}
        )
        
        self.db.add(scheduled_post)
        self.db.commit()
        self.db.refresh(scheduled_post)
        
        logger.info(f"Создан запланированный пост {scheduled_post.id} для user_id={user_id}")
        return scheduled_post
    
    def get_scheduled_post(self, user_id: int, post_id: int) -> Optional[ScheduledPostDB]:
        """Получить запланированный пост"""
        return self.db.query(ScheduledPostDB).filter(
            and_(
                ScheduledPostDB.id == post_id,
                ScheduledPostDB.user_id == user_id
            )
        ).first()
    
    def list_scheduled_posts(
        self,
        user_id: int,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ScheduledPostDB]:
        """Список запланированных постов"""
        query = self.db.query(ScheduledPostDB).filter(
            ScheduledPostDB.user_id == user_id
        )
        
        if status:
            query = query.filter(ScheduledPostDB.status == status)
        if platform:
            query = query.filter(ScheduledPostDB.platform == platform)
        
        return query.order_by(ScheduledPostDB.scheduled_time.asc()).limit(limit).offset(offset).all()
    
    def update_scheduled_post(
        self,
        user_id: int,
        post_id: int,
        scheduled_time: Optional[datetime] = None,
        status: Optional[str] = None,
        publish_options: Optional[Dict[str, Any]] = None
    ) -> Optional[ScheduledPostDB]:
        """Обновить запланированный пост"""
        post = self.get_scheduled_post(user_id, post_id)
        if not post:
            return None
        
        if scheduled_time:
            post.scheduled_time = scheduled_time
        if status:
            post.status = status
        if publish_options is not None:
            post.publish_options = publish_options
        
        post.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(post)
        
        logger.info(f"Обновлен запланированный пост {post_id}")
        return post
    
    def cancel_scheduled_post(self, user_id: int, post_id: int) -> bool:
        """Отменить запланированный пост"""
        post = self.get_scheduled_post(user_id, post_id)
        if not post:
            return False
        
        if post.status == 'published':
            raise ValueError("Нельзя отменить уже опубликованный пост")
        
        post.status = 'cancelled'
        post.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Отменен запланированный пост {post_id}")
        return True
    
    def delete_scheduled_post(self, user_id: int, post_id: int) -> bool:
        """Удалить запланированный пост"""
        post = self.get_scheduled_post(user_id, post_id)
        if not post:
            return False
        
        if post.status == 'published':
            raise ValueError("Нельзя удалить уже опубликованный пост")
        
        self.db.delete(post)
        self.db.commit()
        
        logger.info(f"Удален запланированный пост {post_id}")
        return True
    
    def get_posts_to_publish(self, limit: int = 100) -> List[ScheduledPostDB]:
        """Получить посты готовые к публикации (для scheduler)"""
        now = datetime.utcnow()
        return self.db.query(ScheduledPostDB).filter(
            and_(
                ScheduledPostDB.status == 'scheduled',
                ScheduledPostDB.scheduled_time <= now
            )
        ).order_by(ScheduledPostDB.scheduled_time.asc()).limit(limit).all()
    
    def mark_as_published(
        self,
        post_id: int,
        platform_post_id: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Отметить пост как опубликованный"""
        post = self.db.query(ScheduledPostDB).filter(
            ScheduledPostDB.id == post_id
        ).first()
        
        if not post:
            return False
        
        if error_message:
            post.status = 'failed'
            post.error_message = error_message
        else:
            post.status = 'published'
            post.platform_post_id = platform_post_id
            post.published_at = datetime.utcnow()
        
        post.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True

