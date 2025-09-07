"""
MainOrchestrator - Главный оркестратор системы
Объединяет WorkflowEngine и AgentManager для управления всей системой
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .workflow_engine import WorkflowEngine, Task, TaskType, TaskPriority, TaskStatus
from .agent_manager import AgentManager, BaseAgent, AgentCapability, AgentStatus
from ..models.content import ContentBrief, ContentPiece, Platform, ContentType
from ..models.workflow import WorkflowInstance, WorkflowStatus

# Настройка логирования
logger = logging.getLogger(__name__)


class ContentOrchestrator:
    """Главный оркестратор системы AI агентов"""
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.agent_manager = AgentManager(self.workflow_engine)
        self.is_running = False
        self.auto_assign_enabled = True
        
        logger.info("ContentOrchestrator инициализирован")
    
    async def start(self):
        """Запускает оркестратор"""
        if self.is_running:
            logger.warning("Оркестратор уже запущен")
            return
        
        self.is_running = True
        logger.info("ContentOrchestrator запущен")
        
        # Запускаем фоновые задачи
        if self.auto_assign_enabled:
            asyncio.create_task(self._auto_assign_loop())
    
    async def stop(self):
        """Останавливает оркестратор"""
        self.is_running = False
        logger.info("ContentOrchestrator остановлен")
    
    async def _auto_assign_loop(self):
        """Фоновый цикл автоматического назначения задач"""
        while self.is_running:
            try:
                await self.agent_manager.auto_assign_tasks()
                await asyncio.sleep(5)  # Проверяем каждые 5 секунд
            except Exception as e:
                logger.error(f"Ошибка в auto_assign_loop: {e}")
                await asyncio.sleep(10)  # При ошибке ждем дольше
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """Регистрирует агента в системе"""
        return self.agent_manager.register_agent(agent)
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Отменяет регистрацию агента"""
        return self.agent_manager.unregister_agent(agent_id)
    
    async def create_content_workflow(self, brief: ContentBrief, 
                                    platforms: List[Platform] = None,
                                    content_types: List[ContentType] = None) -> str:
        """Создает workflow для создания контента"""
        platforms = platforms or [Platform.TELEGRAM, Platform.VK]
        content_types = content_types or [ContentType.POST]
        
        # Создаем workflow
        workflow = self.workflow_engine.create_workflow(
            name=f"Content Creation: {brief.title}",
            task_type=TaskType.PLANNED,
            context={
                "brief_id": brief.id,
                "platforms": [p.value for p in platforms],
                "content_types": [ct.value for ct in content_types]
            }
        )
        
        # Добавляем задачи для каждого платформы и типа контента
        for platform in platforms:
            for content_type in content_types:
                task_name = f"Create {content_type.value} for {platform.value}"
                
                self.workflow_engine.add_task(
                    workflow_id=workflow.id,
                    task_name=task_name,
                    task_type=TaskType.PLANNED,
                    priority=TaskPriority.MEDIUM,
                    context={
                        "brief_id": brief.id,
                        "platform": platform.value,
                        "content_type": content_type.value
                    }
                )
        
        logger.info(f"Создан workflow {workflow.id} для бриф {brief.id}")
        return workflow.id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Выполняет workflow"""
        if workflow_id not in self.workflow_engine.workflows:
            raise ValueError(f"Workflow {workflow_id} не найден")
        
        workflow = self.workflow_engine.workflows[workflow_id]
        workflow.status = TaskStatus.IN_PROGRESS
        
        results = {}
        
        try:
            # Выполняем задачи по порядку
            for task in workflow.tasks:
                if task.status == TaskStatus.PENDING:
                    # Назначаем задачу агенту
                    agent_id = self.agent_manager.assign_task_to_agent(task)
                    if agent_id:
                        # Выполняем задачу
                        result = await self.agent_manager.execute_task(task.id)
                        results[task.id] = result
                    else:
                        logger.warning(f"Не удалось назначить задачу {task.id}")
                        task.status = TaskStatus.FAILED
                        task.error_message = "No available agent"
            
            # Проверяем статус workflow
            completed_tasks = sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED)
            failed_tasks = sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED)
            
            if failed_tasks == 0:
                workflow.status = TaskStatus.COMPLETED
            elif completed_tasks > 0:
                workflow.status = TaskStatus.FAILED
            else:
                workflow.status = TaskStatus.FAILED
            
            logger.info(f"Workflow {workflow_id} завершен со статусом {workflow.status.value}")
            
        except Exception as e:
            workflow.status = TaskStatus.FAILED
            logger.error(f"Ошибка выполнения workflow {workflow_id}: {e}")
            raise
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "results": results,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "total_tasks": len(workflow.tasks)
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает статус workflow"""
        return self.workflow_engine.get_workflow_status(workflow_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Возвращает общий статус системы"""
        workflow_status = self.workflow_engine.get_queue_status()
        agent_status = self.agent_manager.get_system_status()
        
        return {
            "orchestrator": {
                "is_running": self.is_running,
                "auto_assign_enabled": self.auto_assign_enabled
            },
            "workflows": workflow_status,
            "agents": agent_status,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает статус агента"""
        return self.agent_manager.get_agent_status(agent_id)
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает статус всех агентов"""
        return self.agent_manager.get_all_agents_status()
    
    async def process_content_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает запрос на создание контента"""
        try:
            # Создаем бриф из запроса
            brief = ContentBrief(
                title=request.get("title", ""),
                description=request.get("description", ""),
                target_audience=request.get("target_audience", ""),
                business_goals=request.get("business_goals", []),
                call_to_action=request.get("call_to_action", ""),
                tone=request.get("tone", "professional"),
                keywords=request.get("keywords", []),
                constraints=request.get("constraints", {})
            )
            
            # Определяем платформы и типы контента
            platforms = [Platform(p) for p in request.get("platforms", ["telegram", "vk"])]
            content_types = [ContentType(ct) for ct in request.get("content_types", ["post"])]
            
            # Создаем workflow
            workflow_id = await self.create_content_workflow(brief, platforms, content_types)
            
            # Проверяем нужен ли фактчекинг
            constraints = request.get("constraints", {})
            if constraints.get("fact_checking", False):
                # Добавляем задачу фактчекинга
                self.workflow_engine.add_task(
                    workflow_id=workflow_id,
                    task_name="Fact Check Content",
                    task_type=TaskType.PLANNED,
                    priority=TaskPriority.MEDIUM,
                    context={
                        "content": {
                            "id": brief.id,
                            "text": f"{brief.title} {brief.description}",
                            "type": "content_brief"
                        },
                        "check_type": "comprehensive"
                    }
                )
                logger.info(f"Добавлена задача фактчекинга в workflow {workflow_id}")
            
            # Выполняем workflow
            result = await self.execute_workflow(workflow_id)
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "brief_id": brief.id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def enable_auto_assign(self):
        """Включает автоматическое назначение задач"""
        self.auto_assign_enabled = True
        logger.info("Автоматическое назначение задач включено")
    
    def disable_auto_assign(self):
        """Отключает автоматическое назначение задач"""
        self.auto_assign_enabled = False
        logger.info("Автоматическое назначение задач отключено")


# Глобальный экземпляр оркестратора
orchestrator = ContentOrchestrator()
