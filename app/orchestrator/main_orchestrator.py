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
                                    content_types: List[ContentType] = None,
                                    variants_count: int = 1,
                                    image_source: str = None) -> str:
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
                "content_types": [ct.value for ct in content_types],
                "image_source": image_source  # Сохраняем image_source в контексте workflow
            }
        )
        
        # Добавляем задачи для каждого платформы и типа контента
        for platform in platforms:
            for content_type in content_types:
                task_name = f"Create {content_type.value} for {platform.value}"
                
                content_task = self.workflow_engine.add_task(
                    workflow_id=workflow.id,
                    task_name=task_name,
                    task_type=TaskType.PLANNED,
                    priority=TaskPriority.MEDIUM,
                    context={
                        "brief_id": brief.id,
                        "brief_data": {
                            "brief_id": brief.id,
                            "title": brief.title,
                            "description": brief.description,
                            "target_audience": brief.target_audience,
                            "business_goals": brief.business_goals,
                            "call_to_action": brief.call_to_action,
                            "tone": brief.tone,
                            "keywords": brief.keywords,
                            # Добавляем tone_profile и insights из project_context если есть
                            "tone_profile": request.get("tone_profile"),
                            "insights": request.get("insights", [])
                        },
                        "platform": platform.value,
                        "content_type": content_type.value,
                        "variants_count": variants_count  # Передаем количество вариантов
                    }
                )
                
                # Для постов добавляем задачу генерации изображения (если указан image_source)
                if content_type == ContentType.POST and image_source:
                    image_task_name = f"Generate image for {content_type.value} on {platform.value}"
                    image_task = self.workflow_engine.add_task(
                        workflow_id=workflow.id,
                        task_name=image_task_name,
                        task_type=TaskType.PLANNED,
                        priority=TaskPriority.MEDIUM,
                        context={
                            "brief_id": brief.id,
                            "platform": platform.value,
                            "content_type": "image",
                            "image_source": image_source,  # Передаем image_source в контекст задачи
                            "format": "square",  # По умолчанию квадратный формат
                            "style": brief.tone or "professional",
                            "prompt": f"{brief.title}. {brief.description[:200]}",
                            "parent_task_id": content_task.id  # Связь с задачей создания контента
                        },
                        dependencies=[content_task.id]  # Изображение генерируется после создания текста
                    )
                    logger.info(f"🖼️ Добавлена задача генерации изображения {image_task.id} для поста на {platform.value} (image_source={image_source})")
        
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
                # Проверяем, нужно ли обновить контекст задачи из parent task
                parent_task_id = task.context.get("parent_task_id")
                if parent_task_id and parent_task_id in results:
                    # Получаем результат родительской задачи
                    parent_result = results[parent_task_id]

                    # Если это задача публикации и у parent есть content, добавляем его в context
                    if "Publish" in task.name and "content" in parent_result:
                        task.context["content"] = parent_result["content"]
                        logger.info(f"Обновлен контекст задачи {task.id} контентом из parent task {parent_task_id}")
                        logger.info(f"Content keys: {list(parent_result['content'].keys())}")

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
                elif task.status == TaskStatus.IN_PROGRESS:
                    # Задача уже назначена, выполняем её
                    result = await self.agent_manager.execute_task(task.id)
                    results[task.id] = result

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
            # ВАЖНО: Логируем входящие данные для отладки
            logger.info(f"📝 Создание контента: title='{request.get('title', '')}', description='{request.get('description', '')[:100]}...'")
            logger.info(f"📝 Параметры изображения: generate_image={request.get('generate_image', False)}, image_source={request.get('image_source', 'не указан')}")
            
            # Создаем бриф из запроса (НЕ перезаписываем title и description!)
            brief = ContentBrief(
                title=request.get("title", ""),  # Используем title из запроса
                description=request.get("description", ""),  # Используем description из запроса
                target_audience=request.get("target_audience", ""),
                business_goals=request.get("business_goals", []),
                call_to_action=request.get("call_to_action", ""),
                tone=request.get("tone", "professional"),
                keywords=request.get("keywords", []),
                constraints=request.get("constraints", {})
            )
            
            logger.info(f"✅ Бриф создан: title='{brief.title}', description='{brief.description[:100]}...'")

            # Определяем платформы и типы контента
            platforms = [Platform(p) for p in request.get("platforms", ["telegram", "vk"])]
            content_types = [ContentType(ct) for ct in request.get("content_types", ["post"])]
            variants_count = request.get("variants_count", 1)  # Количество вариантов (по умолчанию 1)
            
            # ВАЖНО: Проверяем оба поля для генерации изображений
            generate_image = request.get("generate_image", False)  # Флаг генерации изображения
            image_source = request.get("image_source")  # Источник изображения (ai, stock, или None)
            
            # Если generate_image=True и image_source='ai', то генерируем изображение через AI
            # Если generate_image=True и image_source='stock', то используем стоковые изображения
            # Если generate_image=False или image_source не указан, то изображение не генерируется
            final_image_source = None
            if generate_image and image_source:
                final_image_source = image_source
                logger.info(f"🖼️ Генерация изображения включена: generate_image={generate_image}, image_source={image_source}")
            elif generate_image and not image_source:
                logger.warning(f"⚠️ generate_image=True, но image_source не указан. Изображение не будет сгенерировано.")
            else:
                logger.info(f"📝 Генерация изображения отключена: generate_image={generate_image}")

            # Создаем workflow с передачей image_source
            workflow_id = await self.create_content_workflow(
                brief, 
                platforms, 
                content_types, 
                variants_count=variants_count,
                image_source=final_image_source  # Передаем только если generate_image=True и image_source указан
            )

            # Получаем workflow для добавления дополнительных задач
            workflow = self.workflow_engine.workflows[workflow_id]

            # Проверяем нужен ли фактчекинг
            constraints = request.get("constraints", {})
            if constraints.get("fact_checking", False):
                # Добавляем задачу фактчекинга
                factcheck_task = self.workflow_engine.add_task(
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

                # Принудительно назначаем задачу ResearchFactCheckAgent
                if "research_factcheck_agent" in self.agent_manager.agents:
                    factcheck_agent = self.agent_manager.agents["research_factcheck_agent"]
                    if factcheck_agent.assign_task(factcheck_task.id):
                        self.agent_manager.task_assignments[factcheck_task.id] = "research_factcheck_agent"
                        self.workflow_engine.assign_task(factcheck_task.id, "research_factcheck_agent")
                        # Устанавливаем статус IN_PROGRESS для выполнения
                        factcheck_task.status = TaskStatus.IN_PROGRESS
                        # Добавляем задачу в workflow для выполнения
                        workflow.tasks.append(factcheck_task)
                        logger.info(f"Задача фактчекинга {factcheck_task.id} назначена ResearchFactCheckAgent и добавлена в workflow")
                    else:
                        logger.warning("ResearchFactCheckAgent недоступен для фактчекинга")
                else:
                    logger.warning("ResearchFactCheckAgent не найден в системе")

            # Проверяем нужно ли публиковать сразу
            publish_immediately = request.get("publish_immediately", True)
            if publish_immediately:
                # Добавляем задачи публикации для каждой платформы
                channel_id = request.get("channel_id")
                test_mode = request.get("test_mode", False)
                user_id = request.get("user_id")  # ID пользователя (из JWT токена)

                logger.info(f"Добавление задач публикации: publish_immediately={publish_immediately}, channel_id={channel_id}, test_mode={test_mode}, user_id={user_id}")

                # Находим задачи создания контента, чтобы привязать к ним публикацию
                content_tasks = [t for t in workflow.tasks if "Create" in t.name and "image" not in t.name.lower()]

                for content_task in content_tasks:
                    platform = content_task.context.get("platform", "telegram")

                    # Создаем задачу публикации с зависимостью от контента
                    publish_task = self.workflow_engine.add_task(
                        workflow_id=workflow_id,
                        task_name=f"Publish {platform} content",
                        task_type=TaskType.PLANNED,
                        priority=TaskPriority.HIGH,  # Высокий приоритет для публикации
                        context={
                            "platform": platform,
                            "account_id": channel_id,  # ID канала/аккаунта для публикации
                            "user_id": user_id,
                            "test_mode": test_mode,
                            "parent_task_id": content_task.id,  # Связь с задачей создания контента
                            # content будет добавлен из результата parent task при выполнении
                        },
                        dependencies=[content_task.id]  # Публикация после создания контента
                    )
                    logger.info(f"Добавлена задача публикации {publish_task.id} для {platform} (зависит от {content_task.id})")

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
