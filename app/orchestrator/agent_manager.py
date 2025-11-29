"""
AgentManager - Координация и управление AI агентами
Управляет жизненным циклом агентов, их взаимодействием и распределением задач
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from uuid import uuid4

from .workflow_engine import WorkflowEngine, Task, TaskStatus, TaskType, TaskPriority

# Настройка логирования
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Статусы агентов"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    """Возможности агента"""
    task_types: List[TaskType]
    max_concurrent_tasks: int = 1
    specializations: List[str] = field(default_factory=list)
    performance_score: float = 1.0  # Коэффициент производительности


class BaseAgent(ABC):
    """Базовый класс для всех AI агентов"""
    
    def __init__(self, agent_id: str, name: str, capabilities: AgentCapability):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.status = AgentStatus.IDLE
        self.current_tasks: List[str] = []
        self.completed_tasks: List[str] = []
        self.error_count = 0
        self.last_activity = datetime.now()
        
        logger.info(f"Агент {self.name} ({self.agent_id}) инициализирован")
    
    @abstractmethod
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу - должен быть реализован в наследниках"""
        pass
    
    def can_handle_task(self, task: Task) -> bool:
        """Проверяет, может ли агент выполнить задачу"""
        # Проверяем тип задачи
        if task.task_type not in self.capabilities.task_types:
            return False
        
        # Проверяем загрузку
        if len(self.current_tasks) >= self.capabilities.max_concurrent_tasks:
            return False
        
        # Проверяем статус
        if self.status == AgentStatus.ERROR:
            return False
        
        return True
    
    def assign_task(self, task_id: str) -> bool:
        """Назначает задачу агенту"""
        if len(self.current_tasks) >= self.capabilities.max_concurrent_tasks:
            return False
        
        self.current_tasks.append(task_id)
        self.status = AgentStatus.BUSY
        self.last_activity = datetime.now()
        
        logger.info(f"Агент {self.name} получил задачу {task_id}")
        return True
    
    def complete_task(self, task_id: str) -> bool:
        """Отмечает задачу как выполненную"""
        if task_id in self.current_tasks:
            self.current_tasks.remove(task_id)
            self.completed_tasks.append(task_id)
            
            # Если нет активных задач, переводим в IDLE
            if not self.current_tasks:
                self.status = AgentStatus.IDLE
            
            self.last_activity = datetime.now()
            logger.info(f"Агент {self.name} завершил задачу {task_id}")
            return True
        
        return False
    
    def fail_task(self, task_id: str) -> bool:
        """Отмечает задачу как неудачную"""
        if task_id in self.current_tasks:
            self.current_tasks.remove(task_id)
            self.error_count += 1
            self.status = AgentStatus.ERROR
            self.last_activity = datetime.now()
            
            logger.error(f"Агент {self.name} провалил задачу {task_id}")
            return True
        
        return False
    
    def reset_error_status(self):
        """Сбрасывает статус ошибки"""
        if self.status == AgentStatus.ERROR:
            self.status = AgentStatus.IDLE
            logger.info(f"Агент {self.name} восстановлен после ошибки")


class AgentManager:
    """Менеджер агентов - координация и управление"""
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow_engine = workflow_engine
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        
        logger.info("AgentManager инициализирован")
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """Регистрирует агента в системе"""
        if agent.agent_id in self.agents:
            logger.warning(f"Агент {agent.agent_id} уже зарегистрирован")
            return False
        
        self.agents[agent.agent_id] = agent
        self.agent_capabilities[agent.agent_id] = agent.capabilities
        
        logger.info(f"Агент {agent.name} ({agent.agent_id}) зарегистрирован")
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Отменяет регистрацию агента"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Переназначаем активные задачи
        for task_id in agent.current_tasks.copy():
            self._reassign_task(task_id, agent_id)
        
        # Удаляем агента
        del self.agents[agent_id]
        del self.agent_capabilities[agent_id]
        
        logger.info(f"Агент {agent.name} ({agent_id}) отключен")
        return True
    
    def get_available_agents(self, task_type: TaskType) -> List[BaseAgent]:
        """Возвращает доступных агентов для типа задачи"""
        available_agents = []
        
        for agent in self.agents.values():
            if (agent.status == AgentStatus.IDLE and 
                task_type in agent.capabilities.task_types):
                available_agents.append(agent)
        
        # Сортируем по производительности
        available_agents.sort(
            key=lambda a: a.capabilities.performance_score, 
            reverse=True
        )
        
        return available_agents
    
    def assign_task_to_agent(self, task: Task) -> Optional[str]:
        """Назначает задачу подходящему агенту"""
        available_agents = self.get_available_agents(task.task_type)
        
        if not available_agents:
            logger.warning(f"Нет доступных агентов для задачи {task.id}")
            return None
        
        # Фильтруем агентов которые могут обработать эту конкретную задачу
        capable_agents = [agent for agent in available_agents if agent.can_handle_task(task)]
        
        if not capable_agents:
            logger.warning(f"Нет агентов способных обработать задачу {task.id} ({task.name})")
            return None
        
        # Выбираем лучшего агента из способных
        best_agent = capable_agents[0]
        
        # Назначаем задачу
        if best_agent.assign_task(task.id):
            self.task_assignments[task.id] = best_agent.agent_id
            self.workflow_engine.assign_task(task.id, best_agent.agent_id)
            
            logger.info(f"Задача {task.id} ({task.name}) назначена агенту {best_agent.name}")
            return best_agent.agent_id
        
        return None
    
    def _reassign_task(self, task_id: str, old_agent_id: str):
        """Переназначает задачу другому агенту"""
        task = self.workflow_engine._find_task(task_id)
        if not task:
            return
        
        # Убираем из старого агента
        if old_agent_id in self.agents:
            self.agents[old_agent_id].current_tasks.remove(task_id)
        
        # Назначаем новому агенту
        new_agent_id = self.assign_task_to_agent(task)
        if new_agent_id:
            logger.info(f"Задача {task_id} переназначена с {old_agent_id} на {new_agent_id}")
        else:
            # Если не можем переназначить, возвращаем в очередь
            task.status = TaskStatus.PENDING
            task.assigned_agent = None
            self.workflow_engine.task_queue.append(task)
            logger.warning(f"Задача {task_id} возвращена в очередь")
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Выполняет задачу через назначенного агента"""
        if task_id not in self.task_assignments:
            raise ValueError(f"Задача {task_id} не назначена агенту")
        
        agent_id = self.task_assignments[task_id]
        agent = self.agents.get(agent_id)
        
        if not agent:
            raise ValueError(f"Агент {agent_id} не найден")
        
        task = self.workflow_engine._find_task(task_id)
        if not task:
            raise ValueError(f"Задача {task_id} не найдена")
        
        try:
            logger.info(f"Выполнение задачи {task_id} агентом {agent.name}")
            
            # Выполняем задачу
            result = await agent.execute_task(task)
            
            # Отмечаем как выполненную
            agent.complete_task(task_id)
            self.workflow_engine.complete_task(task_id, result)
            
            # Убираем из назначений
            del self.task_assignments[task_id]
            
            logger.info(f"Задача {task_id} успешно выполнена")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка выполнения задачи {task_id}: {str(e)}")
            
            # Отмечаем как неудачную
            agent.fail_task(task_id)
            self.workflow_engine.fail_task(task_id, str(e))
            
            # Убираем из назначений
            if task_id in self.task_assignments:
                del self.task_assignments[task_id]
            
            raise
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает статус агента"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "status": agent.status.value,
            "current_tasks": len(agent.current_tasks),
            "completed_tasks": len(agent.completed_tasks),
            "error_count": agent.error_count,
            "last_activity": agent.last_activity.isoformat(),
            "capabilities": {
                "task_types": [t.value for t in agent.capabilities.task_types],
                "max_concurrent_tasks": agent.capabilities.max_concurrent_tasks,
                "specializations": agent.capabilities.specializations,
                "performance_score": agent.capabilities.performance_score
            }
        }
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает статус всех агентов"""
        return {
            agent_id: self.get_agent_status(agent_id)
            for agent_id in self.agents.keys()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Возвращает общий статус системы агентов"""
        total_agents = len(self.agents)
        idle_agents = sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE)
        busy_agents = sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY)
        error_agents = sum(1 for a in self.agents.values() if a.status == AgentStatus.ERROR)
        
        total_tasks = sum(len(a.current_tasks) for a in self.agents.values())
        total_completed = sum(len(a.completed_tasks) for a in self.agents.values())
        
        return {
            "total_agents": total_agents,
            "idle_agents": idle_agents,
            "busy_agents": busy_agents,
            "error_agents": error_agents,
            "active_tasks": total_tasks,
            "completed_tasks": total_completed,
            "task_assignments": len(self.task_assignments)
        }
    
    async def auto_assign_tasks(self):
        """Автоматически назначает задачи доступным агентам"""
        # Получаем задачи из очереди
        pending_tasks = [
            task for task in self.workflow_engine.task_queue
            if task.status == TaskStatus.PENDING
        ]
        
        assigned_count = 0
        for task in pending_tasks:
            if self.assign_task_to_agent(task):
                assigned_count += 1
        
        if assigned_count > 0:
            logger.info(f"Автоматически назначено {assigned_count} задач")
        
        return assigned_count
    
    def restart_all_agents(self) -> Dict[str, Any]:
        """Перезапускает все агенты (сбрасывает ошибки и освобождает задачи)"""
        logger.info("🔄 Запуск перезагрузки всех агентов...")
        
        restarted_count = 0
        error_count = 0
        freed_tasks = []
        
        for agent_id, agent in self.agents.items():
            try:
                # Сбрасываем статус ошибки
                if agent.status == AgentStatus.ERROR:
                    agent.reset_error_status()
                    restarted_count += 1
                    logger.info(f"✅ Агент {agent.name} восстановлен из ERROR статуса")
                
                # Освобождаем зависшие задачи (опционально - можно раскомментировать при необходимости)
                # if agent.current_tasks:
                #     for task_id in agent.current_tasks.copy():
                #         freed_tasks.append(task_id)
                #         agent.current_tasks.remove(task_id)
                #     agent.status = AgentStatus.IDLE
                #     logger.info(f"🔓 Агент {agent.name} освободил задачи: {freed_tasks}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Ошибка при перезапуске агента {agent.name}: {e}")
        
        result = {
            "success": True,
            "message": f"Перезапущено {restarted_count} агентов",
            "restarted_agents": restarted_count,
            "total_agents": len(self.agents),
            "errors": error_count,
            "freed_tasks": len(freed_tasks),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Перезапуск завершен: {result}")
        return result