"""
Фабрика для создания изолированных оркестраторов для каждого пользователя
Реализует Per-User Agent Clusters архитектуру
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Type, Optional
from dataclasses import dataclass

from .main_orchestrator import ContentOrchestrator
from .agent_manager import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class UserOrchestratorInstance:
    """Экземпляр оркестратора для конкретного пользователя"""
    orchestrator: ContentOrchestrator
    user_id: int
    created_at: datetime
    last_used: datetime
    agent_ids: list  # Список ID агентов, зарегистрированных для пользователя


class UserOrchestratorFactory:
    """
    Фабрика для создания и управления оркестраторами по пользователям
    
    Каждый пользователь получает свой изолированный оркестратор
    с только теми агентами, на которые у него есть подписка
    """
    
    # Хранилище оркестраторов по пользователям
    _user_orchestrators: Dict[int, UserOrchestratorInstance] = {}
    
    # Настройки управления lifecycle
    _cleanup_interval = 3600  # Очистка каждый час (секунды)
    _max_idle_time = 7200  # Максимальное время неактивности - 2 часа
    
    @classmethod
    def get_orchestrator(cls, user_id: int, db_session) -> ContentOrchestrator:
        """
        Получить или создать оркестратор для пользователя
        
        Args:
            user_id: ID пользователя
            db_session: Сессия БД для загрузки подписок
        
        Returns:
            ContentOrchestrator с зарегистрированными агентами пользователя
        """
        # Проверяем есть ли уже оркестратор для этого пользователя
        if user_id not in cls._user_orchestrators:
            logger.info(f"Creating new orchestrator for user {user_id}")
            # Создаем новый оркестратор для пользователя
            orchestrator = cls._create_user_orchestrator(user_id, db_session)
            
            # Получаем список зарегистрированных агентов
            agent_ids = [agent_id for agent_id in orchestrator.agent_manager.agents.keys()]
            
            cls._user_orchestrators[user_id] = UserOrchestratorInstance(
                orchestrator=orchestrator,
                user_id=user_id,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                agent_ids=agent_ids
            )
            
            logger.info(f"Orchestrator created for user {user_id} with {len(agent_ids)} agents: {agent_ids}")
        
        # Обновляем время последнего использования
        cls._user_orchestrators[user_id].last_used = datetime.utcnow()
        
        return cls._user_orchestrators[user_id].orchestrator
    
    @classmethod
    def _create_user_orchestrator(cls, user_id: int, db_session) -> ContentOrchestrator:
        """
        Создает оркестратор и регистрирует только купленных агентов
        
        Args:
            user_id: ID пользователя
            db_session: Сессия БД
        
        Returns:
            ContentOrchestrator с зарегистрированными агентами
        """
        from ..billing.models.agent_subscription import AgentSubscription
        
        # Создаем новый оркестратор
        orchestrator = ContentOrchestrator()
        
        # Получаем активные подписки пользователя на агентов
        subscriptions = db_session.query(AgentSubscription).filter(
            AgentSubscription.user_id == user_id,
            AgentSubscription.status == 'active',
            AgentSubscription.expires_at > datetime.utcnow()
        ).all()
        
        logger.info(f"Found {len(subscriptions)} active agent subscriptions for user {user_id}")
        
        # Получаем маппинг агентов
        agent_classes = cls._get_agent_classes()
        
        # Регистрируем только купленных агентов
        registered_count = 0
        for subscription in subscriptions:
            agent_class = agent_classes.get(subscription.agent_id)
            
            if agent_class:
                try:
                    # Создаем экземпляр агента
                    agent = agent_class()
                    
                    # Регистрируем в оркестраторе
                    if orchestrator.register_agent(agent):
                        registered_count += 1
                        logger.info(f"Registered {subscription.agent_id} for user {user_id}")
                    else:
                        logger.warning(f"Failed to register {subscription.agent_id} for user {user_id}")
                        
                except Exception as e:
                    logger.error(f"Error creating agent {subscription.agent_id}: {e}")
            else:
                logger.warning(f"Unknown agent_id: {subscription.agent_id}")
        
        logger.info(f"Successfully registered {registered_count} agents for user {user_id}")
        
        return orchestrator
    
    @classmethod
    def _get_agent_classes(cls) -> Dict[str, Type[BaseAgent]]:
        """
        Маппинг ID агентов на их классы
        
        Returns:
            Dict с agent_id -> Agent Class
        """
        from ..agents.chief_agent import ChiefContentAgent
        from ..agents.drafting_agent import DraftingAgent
        from ..agents.publisher_agent import PublisherAgent
        from ..agents.research_factcheck_agent import ResearchFactCheckAgent
        from ..agents.trends_scout_agent import TrendsScoutAgent
        from ..agents.multimedia_producer_agent import MultimediaProducerAgent
        from ..agents.legal_guard_agent import LegalGuardAgent
        from ..agents.repurpose_agent import RepurposeAgent
        from ..agents.community_concierge_agent import CommunityConciergeAgent
        from ..agents.paid_creative_agent import PaidCreativeAgent
        
        return {
            "chief_content_agent": ChiefContentAgent,
            "drafting_agent": DraftingAgent,
            "publisher_agent": PublisherAgent,
            "research_factcheck_agent": ResearchFactCheckAgent,
            "trends_scout_agent": TrendsScoutAgent,
            "multimedia_producer_agent": MultimediaProducerAgent,
            "legal_guard_agent": LegalGuardAgent,
            "repurpose_agent": RepurposeAgent,
            "community_concierge_agent": CommunityConciergeAgent,
            "paid_creative_agent": PaidCreativeAgent
        }
    
    @classmethod
    def refresh_user_agents(cls, user_id: int, db_session):
        """
        Обновить список агентов для пользователя
        Вызывается когда пользователь купил/отменил подписку на агента
        
        Args:
            user_id: ID пользователя
            db_session: Сессия БД
        """
        logger.info(f"Refreshing agents for user {user_id}")
        
        if user_id in cls._user_orchestrators:
            # Удаляем старый оркестратор
            old_instance = cls._user_orchestrators[user_id]
            logger.info(f"Removing old orchestrator for user {user_id} (had {len(old_instance.agent_ids)} agents)")
            del cls._user_orchestrators[user_id]
        
        # При следующем запросе создастся новый с актуальными подписками
        logger.info(f"User {user_id} orchestrator will be recreated on next request")
    
    @classmethod
    async def cleanup_idle_orchestrators(cls):
        """
        Очистка неактивных оркестраторов для освобождения памяти
        Вызывается периодически фоновой задачей
        """
        now = datetime.utcnow()
        to_remove = []
        
        for user_id, instance in cls._user_orchestrators.items():
            idle_time = (now - instance.last_used).total_seconds()
            
            if idle_time > cls._max_idle_time:
                to_remove.append(user_id)
                logger.info(f"Marking orchestrator for user {user_id} for removal (idle for {idle_time:.0f}s)")
        
        # Удаляем неактивные оркестраторы
        for user_id in to_remove:
            instance = cls._user_orchestrators[user_id]
            logger.info(f"Removing idle orchestrator for user {user_id} (last used: {instance.last_used})")
            del cls._user_orchestrators[user_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} idle orchestrators")
        else:
            logger.debug(f"No idle orchestrators to clean (total active: {len(cls._user_orchestrators)})")
    
    @classmethod
    def get_active_users_count(cls) -> int:
        """Получить количество активных пользователей с оркестраторами"""
        return len(cls._user_orchestrators)
    
    @classmethod
    def get_user_agents(cls, user_id: int) -> list:
        """
        Получить список агентов пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Список ID агентов или пустой список
        """
        if user_id in cls._user_orchestrators:
            return cls._user_orchestrators[user_id].agent_ids.copy()
        return []
    
    @classmethod
    def get_stats(cls) -> Dict:
        """
        Получить статистику по оркестраторам
        
        Returns:
            Dict со статистикой
        """
        now = datetime.utcnow()
        total_agents = 0
        
        for instance in cls._user_orchestrators.values():
            total_agents += len(instance.agent_ids)
        
        return {
            "active_users": len(cls._user_orchestrators),
            "total_agents_registered": total_agents,
            "avg_agents_per_user": total_agents / len(cls._user_orchestrators) if cls._user_orchestrators else 0,
            "cleanup_interval": cls._cleanup_interval,
            "max_idle_time": cls._max_idle_time
        }


# Фоновая задача для очистки
async def orchestrator_cleanup_task():
    """
    Фоновая задача для периодической очистки неактивных оркестраторов
    Должна запускаться при старте приложения
    """
    logger.info("Orchestrator cleanup task started")
    
    while True:
        try:
            await asyncio.sleep(UserOrchestratorFactory._cleanup_interval)
            await UserOrchestratorFactory.cleanup_idle_orchestrators()
        except Exception as e:
            logger.error(f"Error in orchestrator cleanup task: {e}")
            await asyncio.sleep(60)  # При ошибке ждем минуту и пробуем снова

