"""
WorkflowEngine - Система управления задачами и workflow
Управляет выполнением задач, приоритизацией и зависимостями между агентами
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from uuid import uuid4

# Настройка логирования
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Статусы задач в workflow"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Приоритеты задач"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskType(Enum):
    """Типы задач"""
    REAL_TIME = "real_time"      # Реакция на тренды (SLA: 15 мин)
    PLANNED = "planned"          # Плановый контент (SLA: 240 мин)
    COMPLEX = "complex"          # Комплексные задачи (SLA: 1440 мин)


@dataclass
class Task:
    """Модель задачи в workflow"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    task_type: TaskType = TaskType.PLANNED
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Устанавливаем дедлайн на основе типа задачи"""
        if not self.deadline:
            sla_minutes = {
                TaskType.REAL_TIME: 15,
                TaskType.PLANNED: 240,
                TaskType.COMPLEX: 1440
            }
            self.deadline = self.created_at + timedelta(minutes=sla_minutes[self.task_type])


@dataclass
class Workflow:
    """Модель workflow"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """Движок управления workflow и задачами"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        
        # Конфигурация приоритизации
        self.task_priorities = {
            TaskType.REAL_TIME: {"sla": 15, "weight": 10},
            TaskType.PLANNED: {"sla": 240, "weight": 5},
            TaskType.COMPLEX: {"sla": 1440, "weight": 3}
        }
        
        logger.info("WorkflowEngine инициализирован")
    
    def create_workflow(self, name: str, task_type: TaskType, 
                       context: Dict[str, Any] = None) -> Workflow:
        """Создает новый workflow"""
        workflow = Workflow(
            name=name,
            context=context or {}
        )
        
        self.workflows[workflow.id] = workflow
        logger.info(f"Создан workflow: {workflow.id} - {name}")
        
        return workflow
    
    def add_task(self, workflow_id: str, task_name: str, 
                task_type: TaskType, priority: TaskPriority = TaskPriority.MEDIUM,
                dependencies: List[str] = None, context: Dict[str, Any] = None) -> Task:
        """Добавляет задачу в workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} не найден")
        
        task = Task(
            name=task_name,
            task_type=task_type,
            priority=priority,
            dependencies=dependencies or [],
            context=context or {}
        )
        
        workflow = self.workflows[workflow_id]
        workflow.tasks.append(task)
        
        # Добавляем в очередь задач
        self.task_queue.append(task)
        self._sort_task_queue()
        
        logger.info(f"Добавлена задача: {task.id} - {task_name} в workflow {workflow_id}")
        
        return task
    
    def _sort_task_queue(self):
        """Сортирует очередь задач по приоритету"""
        def task_priority_score(task: Task) -> float:
            # Базовый приоритет
            priority_score = task.priority.value
            
            # Множитель типа задачи
            type_multiplier = self.task_priorities[task.task_type]["weight"]
            
            # Штраф за приближающийся дедлайн
            time_penalty = 0
            if task.deadline:
                time_left = (task.deadline - datetime.now()).total_seconds() / 60
                if time_left < 60:  # Меньше часа
                    time_penalty = 10
                elif time_left < 240:  # Меньше 4 часов
                    time_penalty = 5
            
            return priority_score * type_multiplier - time_penalty
        
        self.task_queue.sort(key=task_priority_score, reverse=True)
    
    def get_next_task(self, agent_id: str) -> Optional[Task]:
        """Возвращает следующую задачу для агента"""
        for task in self.task_queue:
            if (task.status == TaskStatus.PENDING and 
                self._can_execute_task(task, agent_id)):
                return task
        return None
    
    def _can_execute_task(self, task: Task, agent_id: str) -> bool:
        """Проверяет, может ли агент выполнить задачу"""
        # Проверяем зависимости
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        
        # Проверяем, не назначена ли уже другому агенту
        if task.assigned_agent and task.assigned_agent != agent_id:
            return False
        
        return True
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Назначает задачу агенту"""
        task = self._find_task(task_id)
        if not task:
            return False
        
        if task.status != TaskStatus.PENDING:
            return False
        
        task.assigned_agent = agent_id
        task.status = TaskStatus.IN_PROGRESS
        
        # Перемещаем в выполняемые
        if task in self.task_queue:
            self.task_queue.remove(task)
        self.running_tasks[task_id] = task
        
        logger.info(f"Задача {task_id} назначена агенту {agent_id}")
        return True
    
    def complete_task(self, task_id: str, result: Dict[str, Any] = None) -> bool:
        """Отмечает задачу как выполненную"""
        task = self._find_task(task_id)
        if not task:
            return False
        
        task.status = TaskStatus.COMPLETED
        task.result = result or {}
        
        # Перемещаем в выполненные
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        self.completed_tasks[task_id] = task
        
        logger.info(f"Задача {task_id} выполнена")
        return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Отмечает задачу как неудачную"""
        task = self._find_task(task_id)
        if not task:
            return False
        
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        
        # Возвращаем в очередь или помечаем как неудачную
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        logger.error(f"Задача {task_id} провалена: {error_message}")
        return True
    
    def _find_task(self, task_id: str) -> Optional[Task]:
        """Находит задачу по ID"""
        # Ищем в очереди
        for task in self.task_queue:
            if task.id == task_id:
                return task
        
        # Ищем в выполняемых
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]
        
        # Ищем в выполненных
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        return None
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает статус workflow"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        # Подсчитываем статистику
        total_tasks = len(workflow.tasks)
        completed_tasks = sum(1 for task in workflow.tasks if task.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for task in workflow.tasks if task.status == TaskStatus.FAILED)
        in_progress_tasks = sum(1 for task in workflow.tasks if task.status == TaskStatus.IN_PROGRESS)
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "progress_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Возвращает статус очереди задач"""
        return {
            "pending_tasks": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "total_workflows": len(self.workflows)
        }
