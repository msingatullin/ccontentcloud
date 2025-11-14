"""
Сервис для работы с правилами автопостинга
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.auto_posting_rules import AutoPostingRuleDB

logger = logging.getLogger(__name__)


class AutoPostingService:
    """Сервис управления правилами автопостинга"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_rule(
        self,
        user_id: int,
        name: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        content_config: Dict[str, Any],
        platforms: List[str],
        accounts: Optional[Dict[str, List[int]]] = None,
        content_types: Optional[List[str]] = None,
        description: Optional[str] = None,
        max_posts_per_day: Optional[int] = None,
        max_posts_per_week: Optional[int] = None
    ) -> AutoPostingRuleDB:
        """Создать правило автопостинга"""
        # Вычисляем next_execution_at на основе расписания
        next_execution_at = self._calculate_next_execution(schedule_type, schedule_config)
        
        rule = AutoPostingRuleDB(
            user_id=user_id,
            name=name,
            description=description,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            content_config=content_config,
            platforms=platforms,
            accounts=accounts or {},
            content_types=content_types or [],
            is_active=True,
            is_paused=False,
            max_posts_per_day=max_posts_per_day,
            max_posts_per_week=max_posts_per_week,
            next_execution_at=next_execution_at
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"Создано правило автопостинга {rule.id} для user_id={user_id}")
        return rule
    
    def get_rule(self, user_id: int, rule_id: int) -> Optional[AutoPostingRuleDB]:
        """Получить правило"""
        return self.db.query(AutoPostingRuleDB).filter(
            and_(
                AutoPostingRuleDB.id == rule_id,
                AutoPostingRuleDB.user_id == user_id
            )
        ).first()
    
    def list_rules(
        self,
        user_id: int,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AutoPostingRuleDB]:
        """Список правил"""
        query = self.db.query(AutoPostingRuleDB).filter(
            AutoPostingRuleDB.user_id == user_id
        )
        
        if is_active is not None:
            query = query.filter(AutoPostingRuleDB.is_active == is_active)
        
        return query.order_by(AutoPostingRuleDB.created_at.desc()).limit(limit).offset(offset).all()
    
    def update_rule(
        self,
        user_id: int,
        rule_id: int,
        **kwargs
    ) -> Optional[AutoPostingRuleDB]:
        """Обновить правило"""
        rule = self.get_rule(user_id, rule_id)
        if not rule:
            return None
        
        # Обновляем поля
        for key, value in kwargs.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)
        
        # Пересчитываем next_execution_at если изменилось расписание
        if 'schedule_type' in kwargs or 'schedule_config' in kwargs:
            rule.next_execution_at = self._calculate_next_execution(
                rule.schedule_type,
                rule.schedule_config
            )
        
        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"Обновлено правило автопостинга {rule_id}")
        return rule
    
    def delete_rule(self, user_id: int, rule_id: int) -> bool:
        """Удалить правило"""
        rule = self.get_rule(user_id, rule_id)
        if not rule:
            return False
        
        self.db.delete(rule)
        self.db.commit()
        
        logger.info(f"Удалено правило автопостинга {rule_id}")
        return True
    
    def toggle_active(self, user_id: int, rule_id: int, is_active: bool) -> bool:
        """Включить/выключить правило"""
        rule = self.get_rule(user_id, rule_id)
        if not rule:
            return False
        
        rule.is_active = is_active
        rule.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def get_rules_to_execute(self, limit: int = 100) -> List[AutoPostingRuleDB]:
        """Получить правила готовые к выполнению (для scheduler)"""
        now = datetime.utcnow()
        return self.db.query(AutoPostingRuleDB).filter(
            and_(
                AutoPostingRuleDB.is_active == True,
                AutoPostingRuleDB.is_paused == False,
                AutoPostingRuleDB.next_execution_at <= now
            )
        ).order_by(AutoPostingRuleDB.next_execution_at.asc()).limit(limit).all()
    
    def mark_execution(
        self,
        rule_id: int,
        success: bool,
        next_execution_at: Optional[datetime] = None
    ) -> bool:
        """Отметить выполнение правила"""
        rule = self.db.query(AutoPostingRuleDB).filter(
            AutoPostingRuleDB.id == rule_id
        ).first()
        
        if not rule:
            return False
        
        rule.total_executions += 1
        if success:
            rule.successful_executions += 1
        else:
            rule.failed_executions += 1
        
        rule.last_execution_at = datetime.utcnow()
        
        if next_execution_at:
            rule.next_execution_at = next_execution_at
        else:
            # Пересчитываем следующее выполнение
            rule.next_execution_at = self._calculate_next_execution(
                rule.schedule_type,
                rule.schedule_config
            )
        
        rule.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def _calculate_next_execution(
        self,
        schedule_type: str,
        schedule_config: Dict[str, Any]
    ) -> Optional[datetime]:
        """Вычислить следующее время выполнения"""
        now = datetime.utcnow()
        
        if schedule_type == 'daily':
            times = schedule_config.get('times', [])
            days_of_week = schedule_config.get('days_of_week', list(range(1, 8)))
            
            if not times:
                return None
            
            # Находим ближайшее время сегодня или в ближайшие дни
            for day_offset in range(7):
                check_date = now + timedelta(days=day_offset)
                day_of_week = check_date.weekday() + 1  # 1=Пн, 7=Вс
                
                if day_of_week not in days_of_week:
                    continue
                
                for time_str in times:
                    hour, minute = map(int, time_str.split(':'))
                    execution_time = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if execution_time > now:
                        return execution_time
        
        elif schedule_type == 'weekly':
            day_of_week = schedule_config.get('day_of_week', 1)
            time_str = schedule_config.get('time', '10:00')
            hour, minute = map(int, time_str.split(':'))
            
            # Находим следующий день недели
            current_day = now.weekday() + 1
            days_ahead = (day_of_week - current_day) % 7
            if days_ahead == 0:
                # Если сегодня этот день, проверяем время
                execution_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if execution_time > now:
                    return execution_time
                days_ahead = 7
            
            next_date = now + timedelta(days=days_ahead)
            return next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        elif schedule_type == 'custom':
            dates = schedule_config.get('dates', [])
            if not dates:
                return None
            
            for date_str in sorted(dates):
                try:
                    execution_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if execution_time > now:
                        return execution_time
                except:
                    continue
        
        elif schedule_type == 'cron':
            # Для cron нужна библиотека, пока возвращаем None
            # Можно использовать croniter
            return None
        
        return None

