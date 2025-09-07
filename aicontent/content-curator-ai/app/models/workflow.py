"""
Модели данных для workflow и системы управления задачами
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from uuid import uuid4


class WorkflowStatus(Enum):
    """Статусы workflow"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


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
class WorkflowDefinition:
    """Определение workflow"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0"
    
    # Шаги workflow
    steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # Параметры
    max_retries: int = 3
    timeout_minutes: int = 60
    parallel_execution: bool = False
    
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    is_active: bool = True


@dataclass
class WorkflowInstance:
    """Экземпляр workflow"""
    id: str = field(default_factory=lambda: str(uuid4()))
    definition_id: str = ""
    name: str = ""
    status: WorkflowStatus = WorkflowStatus.CREATED
    
    # Контекст выполнения
    context: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # Временные метки
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Задачи
    task_ids: List[str] = field(default_factory=list)
    
    # Метаданные
    created_by: str = ""
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class TaskDefinition:
    """Определение задачи"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.PLANNED
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Агент и выполнение
    required_agent_type: str = ""
    estimated_duration_minutes: int = 30
    max_retries: int = 3
    
    # Зависимости
    dependencies: List[str] = field(default_factory=list)
    
    # Параметры
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class TaskInstance:
    """Экземпляр задачи"""
    id: str = field(default_factory=lambda: str(uuid4()))
    definition_id: str = ""
    workflow_instance_id: str = ""
    name: str = ""
    
    # Статус и приоритет
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.PLANNED
    
    # Выполнение
    assigned_agent_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Зависимости
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # Данные
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # Ошибки и повторы
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Временные метки
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    
    # Метаданные
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    """Возможности агента"""
    agent_type: str = ""
    supported_task_types: List[TaskType] = field(default_factory=list)
    max_concurrent_tasks: int = 1
    specializations: List[str] = field(default_factory=list)
    performance_score: float = 1.0
    availability_schedule: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStatus:
    """Статус агента"""
    agent_id: str = ""
    agent_type: str = ""
    status: str = "idle"  # idle, busy, error, offline
    current_tasks: List[str] = field(default_factory=list)
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutionLog:
    """Лог выполнения workflow"""
    id: str = field(default_factory=lambda: str(uuid4()))
    workflow_instance_id: str = ""
    task_instance_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # Событие
    event_type: str = ""  # started, completed, failed, retry, etc.
    message: str = ""
    level: str = "info"  # debug, info, warning, error
    
    # Данные
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Временная метка
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowMetrics:
    """Метрики workflow"""
    id: str = field(default_factory=lambda: str(uuid4()))
    workflow_definition_id: str = ""
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    # Статистика выполнения
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    
    # Временные метрики
    avg_execution_time_minutes: float = 0.0
    min_execution_time_minutes: float = 0.0
    max_execution_time_minutes: float = 0.0
    
    # Метрики задач
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration_minutes: float = 0.0
    
    # Метрики агентов
    agents_used: List[str] = field(default_factory=list)
    avg_agent_utilization: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)
