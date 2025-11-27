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
from ..models.content import ContentBrief, ContentPiece, Platform, ContentType, ContentPieceDB, TokenUsageDB, ContentHistoryDB
from ..models.workflow import WorkflowInstance, WorkflowStatus
from ..database.connection import get_db_session

# Настройка логирования
logger = logging.getLogger(__name__)


class ContentOrchestrator:
    """Главный оркестратор системы AI агентов"""
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.agent_manager = AgentManager(self.workflow_engine)
        self.is_running = False
        self.auto_assign_enabled = True
        self.db_session = get_db_session()
        
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
                                    user_id: Optional[int] = None,
                                    test_mode: bool = False,
                                    channel_id: Optional[int] = None,
                                    publish_immediately: bool = True,
                                    generate_image: bool = False,
                                    image_source: Optional[str] = None) -> str:
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
                "user_id": user_id,  # Добавляем user_id для сохранения в БД
                "test_mode": test_mode,  # Добавляем test_mode для передачи в задачи
                "channel_id": channel_id,  # ID конкретного канала для публикации
                "image_source": image_source or "stock"  # Источник изображения
            }
        )
        
        # Преобразуем brief в словарь для передачи в контекст задачи
        brief_data = {
            "brief_id": brief.id,
            "title": brief.title,
            "description": brief.description,
            "target_audience": brief.target_audience,
            "business_goals": brief.business_goals,
            "call_to_action": brief.call_to_action,
            "tone": brief.tone,
            "keywords": brief.keywords,
            "constraints": brief.constraints
        }
        
        # Добавляем задачу добавления изображения если запрошено (ПЕРЕД созданием контента)
        if generate_image:
            logger.info(f"🖼️ Создание задачи генерации изображения для бриф {brief.id}, generate_image={generate_image}")
            # Получаем источник изображения из контекста workflow
            image_source = workflow.context.get('image_source', 'stock')  # По умолчанию стоковые
            logger.info(f"🖼️ Источник изображения: {image_source}")
            
            if image_source == 'ai':
                # Генерация через ИИ
                image_task_name = "Generate Image with AI"
                image_prompt = f"{brief.title}. {brief.description[:200]}"
                image_context = {
                    "brief_id": brief.id,
                    "prompt": image_prompt,
                    "content_type": "post_image",
                    "user_id": user_id,
                    "platform": "telegram",
                    "style": "realistic",
                    "image_format": "square",
                    "image_source": "ai"
                }
            else:
                # Поиск стокового изображения (по умолчанию)
                image_task_name = "Find Stock Image"
                # Формируем запрос для поиска изображения на основе заголовка и ключевых слов
                search_query = brief.title
                if brief.keywords:
                    search_query += f" {' '.join(brief.keywords[:3])}"  # Добавляем первые 3 ключевых слова
                
                image_context = {
                    "brief_id": brief.id,
                    "search_query": search_query,
                    "content_type": "post_image",
                    "user_id": user_id,
                    "platform": "telegram",
                    "image_format": "square",
                    "image_source": "stock",
                    "task_type": "find_stock_image"  # Указываем тип задачи для агента
                }
            
            self.workflow_engine.add_task(
                workflow_id=workflow.id,
                task_name=image_task_name,
                task_type=TaskType.PLANNED,
                priority=TaskPriority.MEDIUM,
                context=image_context
            )
            
            logger.info(f"Добавлена задача добавления изображения ({image_source}) для бриф {brief.id}")

        # Добавляем задачи для каждого платформы и типа контента
        for platform in platforms:
            for content_type in content_types:
                # Задача создания контента
                task_name = f"Create {content_type.value} for {platform.value}"
                
                self.workflow_engine.add_task(
                    workflow_id=workflow.id,
                    task_name=task_name,
                    task_type=TaskType.PLANNED,
                    priority=TaskPriority.MEDIUM,
                    context={
                        "brief_id": brief.id,
                        "brief_data": brief_data,  # Передаем полные данные брифа
                        "platform": platform.value,
                        "content_type": content_type.value,
                        "user_id": user_id,
                        "test_mode": test_mode  # Передаем test_mode в каждую задачу
                    }
                )
                
                # Задача публикации контента - создаем только если publish_immediately = True
                if publish_immediately:
                    publish_task_name = f"Publish {content_type.value} to {platform.value}"
                    
                    # Формируем контекст публикации с account_id
                    publish_context = {
                        "brief_id": brief.id,
                        "platform": platform.value,
                        "content_type": content_type.value,
                        "user_id": user_id,
                        "test_mode": test_mode,
                        # content будет добавлен после создания контента
                    }
                    
                    # Добавляем account_id если указан channel_id
                    if channel_id:
                        publish_context["account_id"] = channel_id
                    
                    self.workflow_engine.add_task(
                        workflow_id=workflow.id,
                        task_name=publish_task_name,
                        task_type=TaskType.PLANNED,
                        priority=TaskPriority.HIGH,
                        context=publish_context
                    )
                else:
                    logger.info(f"Пропущена задача публикации для {content_type.value} на {platform.value} (publish_immediately=False)")
        
        logger.info(f"Создан workflow {workflow.id} для бриф {brief.id} с задачами создания и публикации")
        return workflow.id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Выполняет workflow"""
        if workflow_id not in self.workflow_engine.workflows:
            raise ValueError(f"Workflow {workflow_id} не найден")
        
        workflow = self.workflow_engine.workflows[workflow_id]
        workflow.status = TaskStatus.IN_PROGRESS
        
        results = {}
        
        try:
            # Получаем user_id из контекста workflow
            user_id = workflow.context.get('user_id')
            
            # Выполняем задачи по порядку
            logger.info(f"🔄 Начинаем выполнение workflow {workflow_id}, всего задач: {len(workflow.tasks)}")
            for task in workflow.tasks:
                logger.info(f"📋 Задача: {task.name} (id={task.id}), статус: {task.status.value}, тип: {task.task_type.value}")
                if task.status == TaskStatus.PENDING:
                    # Назначаем задачу агенту
                    logger.info(f"🔍 Пытаемся назначить задачу {task.id} ({task.name}) агенту...")
                    agent_id = self.agent_manager.assign_task_to_agent(task)
                    if agent_id:
                        logger.info(f"✅ Задача {task.id} назначена агенту {agent_id}, начинаем выполнение...")
                        # Выполняем задачу
                        result = await self.agent_manager.execute_task(task.id)
                        results[task.id] = result
                        logger.info(f"✅ Задача {task.id} выполнена, результат: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                        
                        # Сохраняем результат в БД если это контент
                        if user_id and 'content' in result:
                            await self._save_task_result_to_db(result, user_id, workflow_id, agent_id, task)
                        
                        # Если это задача создания контента, передаем результат в задачу публикации
                        if 'content' in result and 'Create' in task.name:
                            platform = task.context.get('platform')
                            content_type = task.context.get('content_type')
                            # Ищем соответствующую задачу публикации
                            for pub_task in workflow.tasks:
                                if (pub_task.status == TaskStatus.PENDING and 
                                    'Publish' in pub_task.name and 
                                    pub_task.context.get('platform') == platform and
                                    pub_task.context.get('content_type') == content_type):
                                    # Добавляем контент в контекст задачи публикации
                                    pub_task.context['content'] = result.get('content', {})
                                    logger.info(f"Передан контент из задачи {task.id} в задачу публикации {pub_task.id}")
                                    break
                    else:
                        logger.warning(f"Не удалось назначить задачу {task.id}")
                        task.status = TaskStatus.FAILED
                        task.error_message = "No available agent"
                elif task.status == TaskStatus.IN_PROGRESS:
                    # Задача уже назначена, выполняем её
                    result = await self.agent_manager.execute_task(task.id)
                    results[task.id] = result
                    
                    # Сохраняем результат в БД если это контент
                    agent_id = self.agent_manager.task_assignments.get(task.id)
                    if user_id and agent_id and 'content' in result:
                        await self._save_task_result_to_db(result, user_id, workflow_id, agent_id, task)
                    
                    # Если это задача генерации/поиска изображения, добавляем image_url в media_urls существующего контента
                    logger.info(f"🔍 Проверка задачи {task.id}: name='{task.name}', user_id={user_id}, image_source={task.context.get('image_source')}, 'Image' in name={'Image' in task.name}")
                    if user_id and ('Image' in task.name or task.context.get('image_source')):
                        image_url = None
                        
                        logger.info(f"🖼️ Обработка результата задачи с изображением: {task.id} ({task.name})")
                        logger.info(f"🖼️ Результат: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                        
                        # Результат возвращается в формате {"success": True, "result": GeneratedImage, ...}
                        task_result = result.get('result')
                        
                        if task_result:
                            logger.info(f"🖼️ task_result type: {type(task_result)}")
                            # Если result - это объект GeneratedImage, извлекаем image_url
                            if hasattr(task_result, 'image_url'):
                                image_url = task_result.image_url
                                logger.info(f"🖼️ image_url из объекта GeneratedImage: {image_url}")
                            # Если result - это словарь, проверяем ключи
                            elif isinstance(task_result, dict):
                                image_url = task_result.get('image_url') or task_result.get('url')
                                logger.info(f"🖼️ image_url из словаря: {image_url}, keys: {list(task_result.keys())}")
                        
                        # Также проверяем прямые ключи в результате (для обратной совместимости)
                        if not image_url:
                            logger.info(f"🖼️ Пробуем найти image_url в прямых ключах результата...")
                            if 'image' in result:
                                image_data = result.get('image', {})
                                if isinstance(image_data, dict):
                                    image_url = image_data.get('image_url')
                                elif isinstance(image_data, str):
                                    image_url = image_data
                            elif 'image_url' in result:
                                image_url = result.get('image_url')
                        
                        if image_url:
                            brief_id = task.context.get('brief_id')
                            if brief_id:
                                await self._add_image_to_content(brief_id, image_url, user_id)
                                logger.info(f"✅ Добавлено изображение {image_url} в контент для brief_id {brief_id}")
                                
                                # Inject image_url into pending Publish tasks
                                for pub_task in workflow.tasks:
                                    if (pub_task.status == TaskStatus.PENDING and 
                                        'Publish' in pub_task.name):
                                        
                                        # Initialize content dict if missing
                                        if 'content' not in pub_task.context:
                                            pub_task.context['content'] = {}
                                        
                                        # Initialize media_urls list if missing
                                        if 'media_urls' not in pub_task.context['content']:
                                            pub_task.context['content']['media_urls'] = []
                                            
                                        # Add image_url if not present
                                        current_media = pub_task.context['content']['media_urls']
                                        if image_url not in current_media:
                                            current_media.append(image_url)
                                            logger.info(f"📸 Image URL injected into Publish task {pub_task.id}")
                            else:
                                logger.warning(f"⚠️ brief_id не найден в контексте задачи {task.id} ({task.name})")
                        else:
                            logger.warning(f"⚠️ image_url не найден в результате задачи {task.id} ({task.name}). "
                                         f"Результат keys: {list(result.keys()) if isinstance(result, dict) else type(result)}, "
                                         f"task_result type: {type(result.get('result')) if isinstance(result, dict) else 'N/A'}, "
                                         f"task_result value: {result.get('result') if isinstance(result, dict) else 'N/A'}")
                    
                    # Если это задача создания контента, передаем результат в задачу публикации
                    if 'content' in result and 'Create' in task.name:
                        platform = task.context.get('platform')
                        content_type = task.context.get('content_type')
                        new_content = result.get('content', {})
                        
                        # Ищем соответствующую задачу публикации
                        for pub_task in workflow.tasks:
                            if (pub_task.status == TaskStatus.PENDING and 
                                'Publish' in pub_task.name and 
                                pub_task.context.get('platform') == platform and
                                pub_task.context.get('content_type') == content_type):
                                
                                # ВАЖНО: Сохраняем существующие media_urls перед обновлением
                                existing_content = pub_task.context.get('content', {})
                                existing_media_urls = existing_content.get('media_urls', [])
                                
                                # Обновляем контент, а не перезаписываем полностью
                                if 'content' not in pub_task.context:
                                    pub_task.context['content'] = {}
                                
                                pub_task.context['content'].update(new_content)
                                
                                # Восстанавливаем media_urls если они были
                                if existing_media_urls:
                                    pub_task.context['content']['media_urls'] = existing_media_urls
                                    logger.info(f"📸 Сохранены media_urls при обновлении контента: {existing_media_urls}")
                                
                                logger.info(f"Передан контент из задачи {task.id} в задачу публикации {pub_task.id}, "
                                           f"media_urls: {pub_task.context['content'].get('media_urls', [])}")
                                break
            
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
    
    def restart_all_agents(self) -> Dict[str, Any]:
        """Перезапускает все агенты в системе"""
        logger.info("🔄 ContentOrchestrator: перезапуск всех агентов")
        return self.agent_manager.restart_all_agents()
    
    def save_content_to_db(self, content_piece: ContentPiece, user_id: int, 
                          workflow_id: str, agent_id: str) -> Optional[str]:
        """Сохраняет созданный контент в БД"""
        try:
            # Создаем запись в БД
            content_db = ContentPieceDB(
                id=content_piece.id,
                user_id=user_id,
                workflow_id=workflow_id,
                brief_id=content_piece.brief_id,
                title=content_piece.title,
                text=content_piece.text,
                content_type=content_piece.content_type.value,
                platform=content_piece.platform.value,
                hashtags=content_piece.hashtags,
                mentions=content_piece.mentions,
                media_urls=content_piece.media_urls,
                call_to_action=content_piece.call_to_action,
                status=content_piece.status.value,
                created_by_agent=agent_id,
                meta_data=content_piece.metadata
            )
            
            # Сохраняем в БД
            self.db_session.add(content_db)
            self.db_session.commit()
            
            # Создаем запись в истории
            history_record = ContentHistoryDB(
                content_id=content_piece.id,
                user_id=user_id,
                action='created',
                changed_by_agent=agent_id,
                content_snapshot={
                    "title": content_piece.title,
                    "text": content_piece.text,
                    "platform": content_piece.platform.value,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            self.db_session.add(history_record)
            self.db_session.commit()
            
            logger.info(f"✅ Контент {content_piece.id} сохранен в БД для пользователя {user_id}")
            return content_piece.id
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения контента в БД: {e}")
            self.db_session.rollback()
            return None
    
    def save_token_usage(self, user_id: int, agent_id: str, workflow_id: str,
                        content_id: Optional[str], ai_model: str, 
                        prompt_tokens: int, completion_tokens: int,
                        cost_usd: float, platform: str, content_type: str) -> None:
        """Сохраняет информацию об использовании токенов"""
        try:
            import uuid
            
            # Конвертируем USD в RUB (примерный курс)
            usd_to_rub_rate = 95.0  # обновлять из API ЦБ РФ
            cost_rub = cost_usd * usd_to_rub_rate
            cost_kopeks = int(cost_rub * 100)  # В копейках для AgentSubscription
            
            token_usage = TokenUsageDB(
                user_id=user_id,
                content_id=content_id,
                workflow_id=workflow_id,
                agent_id=agent_id,
                request_id=str(uuid.uuid4()),
                endpoint='/content/create',
                ai_provider='openai',
                ai_model=ai_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=cost_usd,
                cost_rub=cost_rub,
                platform=platform,
                content_type=content_type,
                task_type='content_generation'
            )
            
            self.db_session.add(token_usage)
            self.db_session.commit()
            
            logger.info(f"✅ Использование токенов сохранено: {prompt_tokens + completion_tokens} токенов, {cost_rub:.2f}₽")
            
            # Обновляем счетчики в AgentSubscription
            try:
                from ..billing.middleware.agent_access_middleware import AgentAccessMiddleware
                
                total_tokens = prompt_tokens + completion_tokens
                AgentAccessMiddleware.increment_agent_usage(
                    user_id=user_id,
                    agent_id=agent_id,
                    tokens_used=total_tokens,
                    cost_kopeks=cost_kopeks,
                    db_session=self.db_session
                )
                logger.info(f"✅ Счетчики AgentSubscription обновлены для {agent_id}")
            except Exception as sub_e:
                logger.warning(f"⚠️ Не удалось обновить AgentSubscription: {sub_e}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения token usage: {e}")
            self.db_session.rollback()
    
    async def _save_task_result_to_db(self, result: Dict[str, Any], user_id: int, 
                                     workflow_id: str, agent_id: str, task: Task) -> None:
        """Сохраняет результат выполнения задачи в БД"""
        try:
            content_data = result.get('content', {})
            
            # Создаем ContentPiece из результата
            content_piece = ContentPiece(
                id=content_data.get('id', ''),
                brief_id=task.context.get('brief_id', ''),
                content_type=ContentType(content_data.get('content_type', 'post')),
                platform=Platform(content_data.get('platform', 'telegram')),
                title=content_data.get('title', ''),
                text=content_data.get('text', ''),
                hashtags=content_data.get('hashtags', []),
                call_to_action=content_data.get('call_to_action', ''),
                created_by_agent=agent_id
            )
            
            # Сохраняем контент
            self.save_content_to_db(content_piece, user_id, workflow_id, agent_id)
            
            # Сохраняем использование токенов если есть информация
            quality_metrics = result.get('quality_metrics', {})
            if quality_metrics:
                # Примерный расчет токенов (для точного нужно получать из OpenAI response)
                estimated_prompt_tokens = len(content_piece.title + content_piece.text) // 4  # примерно 4 символа = 1 токен
                estimated_completion_tokens = len(content_piece.text) // 4
                
                # Расчет стоимости для gpt-5-mini
                # GPT-5-mini: Input $0.00025/1K, Output $0.002/1K
                cost_usd = (estimated_prompt_tokens / 1000 * 0.00025) + (estimated_completion_tokens / 1000 * 0.002)
                
                self.save_token_usage(
                    user_id=user_id,
                    agent_id=agent_id,
                    workflow_id=workflow_id,
                    content_id=content_piece.id,
                    ai_model='gpt-5-mini',
                    prompt_tokens=estimated_prompt_tokens,
                    completion_tokens=estimated_completion_tokens,
                    cost_usd=cost_usd,
                    platform=content_piece.platform.value,
                    content_type=content_piece.content_type.value
                )
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результата задачи: {e}")
    
    async def _add_image_to_content(self, brief_id: str, image_url: str, user_id: int) -> None:
        """Добавляет URL изображения в media_urls существующего контента"""
        try:
            from app.models.content import ContentPieceDB
            from app.database.connection import get_db_session
            
            db_session = get_db_session()
            
            # Находим контент по brief_id
            content = db_session.query(ContentPieceDB).filter(
                ContentPieceDB.brief_id == brief_id,
                ContentPieceDB.user_id == user_id
            ).first()
            
            if content:
                # Получаем текущие media_urls
                if not content.media_urls:
                    content.media_urls = []
                elif isinstance(content.media_urls, str):
                    # Если это строка, парсим её
                    import json
                    try:
                        content.media_urls = json.loads(content.media_urls)
                    except:
                        content.media_urls = [content.media_urls]
                
                # Добавляем новый URL, если его еще нет
                if image_url not in content.media_urls:
                    content.media_urls.append(image_url)
                    db_session.commit()
                    logger.info(f"✅ URL изображения добавлен в media_urls контента {content.id}")
                else:
                    logger.info(f"URL изображения уже есть в media_urls контента {content.id}")
            else:
                logger.warning(f"Контент для brief_id {brief_id} не найден, невозможно добавить изображение")
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления изображения в контент: {e}")
    
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
            
            # Получаем user_id, test_mode, channel_id, publish_immediately, generate_image и image_source из запроса
            user_id = request.get("user_id")
            test_mode = request.get("test_mode", False)
            channel_id = request.get("channel_id")  # ID конкретного канала для публикации
            publish_immediately = request.get("publish_immediately", True)  # По умолчанию публикуем сразу
            generate_image = request.get("generate_image", False)  # Добавление изображения
            image_source = request.get("image_source", "stock")  # Источник изображения: 'stock' или 'ai'
            
            # Логируем параметры для отладки
            logger.info(f"📝 Параметры создания контента: generate_image={generate_image}, image_source={image_source}, publish_immediately={publish_immediately}")
            
            # Создаем workflow с передачей всех параметров
            workflow_id = await self.create_content_workflow(brief, platforms, content_types, user_id, test_mode, channel_id, publish_immediately, generate_image, image_source)
            
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
                        workflow = self.workflow_engine.workflows[workflow_id]
                        workflow.tasks.append(factcheck_task)
                        logger.info(f"Задача фактчекинга {factcheck_task.id} назначена ResearchFactCheckAgent и добавлена в workflow")
                    else:
                        logger.warning("ResearchFactCheckAgent недоступен для фактчекинга")
                else:
                    logger.warning("ResearchFactCheckAgent не найден в системе")
            
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
