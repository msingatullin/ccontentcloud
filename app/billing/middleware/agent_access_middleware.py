"""
Middleware для проверки доступа пользователей к AI агентам
Обеспечивает соблюдение подписок и лимитов
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AgentAccessMiddleware:
    """Проверка доступа к агентам перед выполнением"""
    
    @staticmethod
    def check_agent_access(user_id: int, agent_id: str, db_session) -> bool:
        """
        Проверяет есть ли у пользователя активная подписка на агента
        
        Args:
            user_id: ID пользователя
            agent_id: ID агента
            db_session: Сессия БД
        
        Returns:
            True - доступ разрешен, False - доступ запрещен
        """
        from app.billing.models.agent_subscription import AgentSubscription
        
        subscription = db_session.query(AgentSubscription).filter(
            AgentSubscription.user_id == user_id,
            AgentSubscription.agent_id == agent_id,
            AgentSubscription.status == 'active',
            AgentSubscription.expires_at > datetime.utcnow()
        ).first()
        
        if not subscription:
            logger.warning(f"User {user_id} has no active subscription for agent {agent_id}")
            return False
        
        # Проверяем можно ли использовать (с учетом лимитов)
        if not subscription.can_use():
            logger.warning(f"User {user_id} reached limits for agent {agent_id}")
            return False
        
        logger.info(f"Access granted for user {user_id} to agent {agent_id}")
        return True
    
    @staticmethod
    def get_user_agents(user_id: int, db_session) -> List[str]:
        """
        Получить список агентов доступных пользователю
        
        Args:
            user_id: ID пользователя
            db_session: Сессия БД
        
        Returns:
            Список agent_id доступных агентов
        """
        from app.billing.models.agent_subscription import AgentSubscription
        
        subscriptions = db_session.query(AgentSubscription).filter(
            AgentSubscription.user_id == user_id,
            AgentSubscription.status == 'active',
            AgentSubscription.expires_at > datetime.utcnow()
        ).all()
        
        # Фильтруем только те, которые можно использовать (с учетом лимитов)
        available_agents = [
            sub.agent_id for sub in subscriptions if sub.can_use()
        ]
        
        logger.info(f"User {user_id} has access to {len(available_agents)} agents")
        return available_agents
    
    @staticmethod
    def get_user_subscriptions(user_id: int, db_session) -> List[Dict[str, Any]]:
        """
        Получить детальную информацию о подписках пользователя
        
        Args:
            user_id: ID пользователя
            db_session: Сессия БД
        
        Returns:
            Список словарей с информацией о подписках
        """
        from app.billing.models.agent_subscription import AgentSubscription
        
        subscriptions = db_session.query(AgentSubscription).filter(
            AgentSubscription.user_id == user_id
        ).order_by(AgentSubscription.created_at.desc()).all()
        
        return [sub.to_dict() for sub in subscriptions]
    
    @staticmethod
    def check_workflow_access(
        user_id: int,
        required_agents: List[str],
        db_session
    ) -> Dict[str, Any]:
        """
        Проверяет какие агенты из workflow доступны пользователю
        
        Args:
            user_id: ID пользователя
            required_agents: Список agent_id нужных для workflow
            db_session: Сессия БД
        
        Returns:
            Dict с информацией о доступе:
            {
                "can_proceed": bool,
                "allowed_agents": List[str],
                "blocked_agents": List[str],
                "missing_subscriptions": List[dict]
            }
        """
        user_agents = AgentAccessMiddleware.get_user_agents(user_id, db_session)
        
        allowed = [agent for agent in required_agents if agent in user_agents]
        blocked = [agent for agent in required_agents if agent not in user_agents]
        
        # Формируем информацию о недостающих подписках
        missing_subscriptions = []
        if blocked:
            from app.billing.models.agent_pricing import AGENT_PRICING
            
            for agent_id in blocked:
                agent_info = AGENT_PRICING.get(agent_id, {})
                missing_subscriptions.append({
                    "agent_id": agent_id,
                    "agent_name": agent_info.get('name', agent_id),
                    "price_monthly": agent_info.get('price_monthly', 0) / 100,  # В рублях
                    "description": agent_info.get('description', '')
                })
        
        result = {
            "can_proceed": len(blocked) == 0,
            "allowed_agents": allowed,
            "blocked_agents": blocked,
            "missing_subscriptions": missing_subscriptions
        }
        
        if not result["can_proceed"]:
            logger.warning(
                f"User {user_id} missing subscriptions for agents: {blocked}"
            )
        
        return result
    
    @staticmethod
    def increment_agent_usage(
        user_id: int,
        agent_id: str,
        tokens_used: int,
        cost_kopeks: int,
        db_session
    ):
        """
        Увеличивает счетчики использования агента
        
        Args:
            user_id: ID пользователя
            agent_id: ID агента
            tokens_used: Количество использованных токенов
            cost_kopeks: Стоимость в копейках
            db_session: Сессия БД
        """
        from app.billing.models.agent_subscription import AgentSubscription
        
        subscription = db_session.query(AgentSubscription).filter(
            AgentSubscription.user_id == user_id,
            AgentSubscription.agent_id == agent_id,
            AgentSubscription.status == 'active'
        ).first()
        
        if subscription:
            subscription.increment_usage(tokens_used, cost_kopeks)
            db_session.commit()
            
            logger.info(
                f"Updated usage for user {user_id}, agent {agent_id}: "
                f"+{tokens_used} tokens, +{cost_kopeks/100:.2f}₽"
            )
        else:
            logger.warning(
                f"Cannot update usage - no subscription found for user {user_id}, agent {agent_id}"
            )
    
    @staticmethod
    def get_usage_stats(user_id: int, db_session) -> Dict[str, Any]:
        """
        Получить статистику использования агентов за текущий месяц
        
        Args:
            user_id: ID пользователя
            db_session: Сессия БД
        
        Returns:
            Dict со статистикой использования
        """
        from app.billing.models.agent_subscription import AgentSubscription
        
        subscriptions = db_session.query(AgentSubscription).filter(
            AgentSubscription.user_id == user_id,
            AgentSubscription.status == 'active'
        ).all()
        
        total_requests = 0
        total_tokens = 0
        total_cost = 0
        
        by_agent = []
        
        for sub in subscriptions:
            total_requests += sub.requests_this_month
            total_tokens += sub.tokens_this_month
            total_cost += sub.cost_this_month
            
            by_agent.append({
                "agent_id": sub.agent_id,
                "agent_name": sub.agent_name,
                "requests": sub.requests_this_month,
                "tokens": sub.tokens_this_month,
                "cost_rub": sub.cost_this_month / 100,
                "avg_tokens_per_request": (
                    sub.tokens_this_month / sub.requests_this_month 
                    if sub.requests_this_month > 0 else 0
                )
            })
        
        return {
            "period": "current_month",
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost_rub": total_cost / 100,
            "by_agent": sorted(by_agent, key=lambda x: x['tokens'], reverse=True)
        }
    
    @staticmethod
    def recommend_agents(user_id: int, db_session) -> Dict[str, Any]:
        """
        Рекомендовать агентов на основе использования
        
        Args:
            user_id: ID пользователя
            db_session: Сессия БД
        
        Returns:
            Dict с рекомендациями
        """
        from app.billing.models.agent_pricing import AGENT_PRICING, recommend_bundle
        
        # Получаем текущие подписки
        current_agents = AgentAccessMiddleware.get_user_agents(user_id, db_session)
        
        # Проверяем есть ли выгодный bundle
        bundle_recommendation = recommend_bundle(current_agents)
        
        # Рекомендуемые агенты (на основе категорий)
        recommended = []
        
        if "drafting_agent" in current_agents and "publisher_agent" not in current_agents:
            recommended.append({
                "agent_id": "publisher_agent",
                "reason": "Дополняет Drafting Agent для полного цикла контента",
                **AGENT_PRICING.get("publisher_agent", {})
            })
        
        if "chief_content_agent" in current_agents and "trends_scout_agent" not in current_agents:
            recommended.append({
                "agent_id": "trends_scout_agent",
                "reason": "Усилит стратегию актуальными трендами",
                **AGENT_PRICING.get("trends_scout_agent", {})
            })
        
        return {
            "bundle_recommendation": bundle_recommendation,
            "recommended_agents": recommended
        }

