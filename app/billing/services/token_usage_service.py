"""
Сервис для работы со статистикой использования AI токенов
Используется для отображения расхода токенов в ЛК клиентов
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.content import TokenUsageDB

logger = logging.getLogger(__name__)


class TokenUsageService:
    """Сервис для агрегации и отображения статистики токенов"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_user_token_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Получить сводку по токенам для пользователя
        Показывает: сегодня, этот месяц, всего
        """
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Сегодня
            today_stats = self.db.query(
                func.sum(TokenUsageDB.total_tokens).label('total_tokens'),
                func.sum(TokenUsageDB.cost_rub).label('cost_rub'),
                func.count(TokenUsageDB.id).label('requests_count')
            ).filter(
                and_(
                    TokenUsageDB.user_id == user_id,
                    TokenUsageDB.created_at >= today_start
                )
            ).first()
            
            # Этот месяц
            month_stats = self.db.query(
                func.sum(TokenUsageDB.total_tokens).label('total_tokens'),
                func.sum(TokenUsageDB.cost_rub).label('cost_rub'),
                func.count(TokenUsageDB.id).label('requests_count')
            ).filter(
                and_(
                    TokenUsageDB.user_id == user_id,
                    TokenUsageDB.created_at >= month_start
                )
            ).first()
            
            # Всего
            total_stats = self.db.query(
                func.sum(TokenUsageDB.total_tokens).label('total_tokens'),
                func.sum(TokenUsageDB.cost_rub).label('cost_rub'),
                func.count(TokenUsageDB.id).label('requests_count')
            ).filter(
                TokenUsageDB.user_id == user_id
            ).first()
            
            return {
                "today": {
                    "total_tokens": int(today_stats.total_tokens or 0),
                    "cost_rub": float(today_stats.cost_rub or 0),
                    "requests_count": int(today_stats.requests_count or 0)
                },
                "this_month": {
                    "total_tokens": int(month_stats.total_tokens or 0),
                    "cost_rub": float(month_stats.cost_rub or 0),
                    "requests_count": int(month_stats.requests_count or 0)
                },
                "all_time": {
                    "total_tokens": int(total_stats.total_tokens or 0),
                    "cost_rub": float(total_stats.cost_rub or 0),
                    "requests_count": int(total_stats.requests_count or 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting token summary for user {user_id}: {e}")
            return {
                "today": {"total_tokens": 0, "cost_rub": 0, "requests_count": 0},
                "this_month": {"total_tokens": 0, "cost_rub": 0, "requests_count": 0},
                "all_time": {"total_tokens": 0, "cost_rub": 0, "requests_count": 0}
            }
    
    def get_token_history(
        self, 
        user_id: int, 
        days: int = 30,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить историю использования токенов по дням
        Для графиков в frontend
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = self.db.query(
                func.date(TokenUsageDB.created_at).label('date'),
                func.sum(TokenUsageDB.total_tokens).label('total_tokens'),
                func.sum(TokenUsageDB.prompt_tokens).label('prompt_tokens'),
                func.sum(TokenUsageDB.completion_tokens).label('completion_tokens'),
                func.sum(TokenUsageDB.cost_rub).label('cost_rub'),
                func.count(TokenUsageDB.id).label('requests_count')
            ).filter(
                and_(
                    TokenUsageDB.user_id == user_id,
                    TokenUsageDB.created_at >= start_date,
                    TokenUsageDB.created_at <= end_date
                )
            )
            
            if agent_id:
                query = query.filter(TokenUsageDB.agent_id == agent_id)
            
            query = query.group_by(func.date(TokenUsageDB.created_at))
            query = query.order_by(func.date(TokenUsageDB.created_at))
            
            results = query.all()
            
            history = []
            for row in results:
                history.append({
                    "date": row.date.isoformat(),
                    "total_tokens": int(row.total_tokens or 0),
                    "prompt_tokens": int(row.prompt_tokens or 0),
                    "completion_tokens": int(row.completion_tokens or 0),
                    "cost_rub": float(row.cost_rub or 0),
                    "requests_count": int(row.requests_count or 0)
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting token history for user {user_id}: {e}")
            return []
    
    def get_usage_by_agent(
        self, 
        user_id: int, 
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Получить статистику по агентам
        Показывает какой агент сколько токенов расходует
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            results = self.db.query(
                TokenUsageDB.agent_id,
                func.sum(TokenUsageDB.total_tokens).label('total_tokens'),
                func.sum(TokenUsageDB.cost_rub).label('cost_rub'),
                func.count(TokenUsageDB.id).label('requests_count'),
                func.avg(TokenUsageDB.execution_time_ms).label('avg_execution_time_ms')
            ).filter(
                and_(
                    TokenUsageDB.user_id == user_id,
                    TokenUsageDB.created_at >= start_date
                )
            ).group_by(
                TokenUsageDB.agent_id
            ).order_by(
                func.sum(TokenUsageDB.total_tokens).desc()
            ).all()
            
            agents_stats = []
            for row in results:
                agents_stats.append({
                    "agent_id": row.agent_id,
                    "total_tokens": int(row.total_tokens or 0),
                    "cost_rub": float(row.cost_rub or 0),
                    "requests_count": int(row.requests_count or 0),
                    "avg_execution_time_ms": int(row.avg_execution_time_ms or 0)
                })
            
            return agents_stats
            
        except Exception as e:
            logger.error(f"Error getting agent usage for user {user_id}: {e}")
            return []
    
    def get_usage_by_model(
        self, 
        user_id: int, 
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Получить статистику по AI моделям
        Показывает расход по OpenAI, Anthropic и конкретным моделям
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            results = self.db.query(
                TokenUsageDB.ai_provider,
                TokenUsageDB.ai_model,
                func.sum(TokenUsageDB.total_tokens).label('total_tokens'),
                func.sum(TokenUsageDB.cost_rub).label('cost_rub'),
                func.count(TokenUsageDB.id).label('requests_count')
            ).filter(
                and_(
                    TokenUsageDB.user_id == user_id,
                    TokenUsageDB.created_at >= start_date
                )
            ).group_by(
                TokenUsageDB.ai_provider,
                TokenUsageDB.ai_model
            ).order_by(
                func.sum(TokenUsageDB.cost_rub).desc()
            ).all()
            
            models_stats = []
            for row in results:
                models_stats.append({
                    "ai_provider": row.ai_provider,
                    "ai_model": row.ai_model,
                    "total_tokens": int(row.total_tokens or 0),
                    "cost_rub": float(row.cost_rub or 0),
                    "requests_count": int(row.requests_count or 0)
                })
            
            return models_stats
            
        except Exception as e:
            logger.error(f"Error getting model usage for user {user_id}: {e}")
            return []
    
    def get_detailed_usage(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Получить детальную историю использования токенов
        Для таблицы с пагинацией в ЛК
        """
        try:
            query = self.db.query(TokenUsageDB).filter(
                TokenUsageDB.user_id == user_id
            )
            
            if agent_id:
                query = query.filter(TokenUsageDB.agent_id == agent_id)
            
            if start_date:
                query = query.filter(TokenUsageDB.created_at >= start_date)
            
            if end_date:
                query = query.filter(TokenUsageDB.created_at <= end_date)
            
            total_count = query.count()
            
            results = query.order_by(
                TokenUsageDB.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            items = []
            for record in results:
                items.append({
                    "id": record.id,
                    "agent_id": record.agent_id,
                    "ai_provider": record.ai_provider,
                    "ai_model": record.ai_model,
                    "total_tokens": record.total_tokens,
                    "prompt_tokens": record.prompt_tokens,
                    "completion_tokens": record.completion_tokens,
                    "cost_rub": record.cost_rub,
                    "execution_time_ms": record.execution_time_ms,
                    "created_at": record.created_at.isoformat(),
                    "content_type": record.content_type,
                    "platform": record.platform
                })
            
            return {
                "items": items,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed usage for user {user_id}: {e}")
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False
            }
    
    def record_token_usage(
        self,
        user_id: int,
        agent_id: str,
        ai_provider: str,
        ai_model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        cost_rub: float,
        execution_time_ms: Optional[int] = None,
        content_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        platform: Optional[str] = None,
        content_type: Optional[str] = None,
        task_type: Optional[str] = None,
        request_metadata: Optional[Dict] = None,
        response_metadata: Optional[Dict] = None
    ) -> Optional[TokenUsageDB]:
        """
        Записать использование токенов
        Вызывается после каждого запроса к AI
        """
        try:
            usage_record = TokenUsageDB(
                user_id=user_id,
                content_id=content_id,
                workflow_id=workflow_id,
                agent_id=agent_id,
                request_id=request_id or f"{user_id}_{datetime.utcnow().timestamp()}",
                endpoint=endpoint,
                ai_provider=ai_provider,
                ai_model=ai_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=cost_usd,
                cost_rub=cost_rub,
                platform=platform,
                content_type=content_type,
                task_type=task_type,
                execution_time_ms=execution_time_ms,
                request_metadata=request_metadata or {},
                response_metadata=response_metadata or {}
            )
            
            self.db.add(usage_record)
            self.db.commit()
            
            logger.info(f"Recorded token usage for user {user_id}: {prompt_tokens + completion_tokens} tokens")
            
            return usage_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording token usage for user {user_id}: {e}")
            return None

